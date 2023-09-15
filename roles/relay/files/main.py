# fmcs-server relay bot
# this is pretty haphazardly thrown together, rewrite eventually

import asyncio
import discord
import yaml
import logging
import sys
import re
import requests

from rcon.source import Client

with open("config.yml", "r") as f:
    CONFIG = yaml.safe_load(f.read())

log_handlers = []
formatter = logging.Formatter(
    "%(asctime)s | %(module)s [%(levelname)s] %(message)s",
)
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(formatter)
log_handlers.append(stdout_handler)
logging.basicConfig(handlers=log_handlers, level=logging.DEBUG)

SERVER_LIST_RE = re.compile(r"There are (\d+) of a max of (\d+) players online: (.+)?")
SERVER_MESSAGE_RE = re.compile(
    r"\[[0-9:]+\] \[Server thread/INFO\]: <([a-zA-Z0-9_]+)> (.+)"
)
SERVER_JOIN_RE = re.compile(
    r"\[[0-9:]+\] \[Server thread/INFO\]: ([a-zA-Z0-9_]+) joined the game"
)
SERVER_LEAVE_RE = re.compile(
    r"\[[0-9:]+\] \[Server thread/INFO\]: ([a-zA-Z0-9_]+) left the game"
)


class DiscordBot(discord.Client):
    def __init__(self):
        # I don't know which to use, so we just do this.
        discord.Client.__init__(self, intents=discord.Intents().all())
        self.tree = discord.app_commands.CommandTree(self)

    async def on_ready(self) -> None:
        # find relay channel
        self.CHANNEL = self.get_channel(CONFIG["channel"])
        self.AVATAR_CACHE = dict()

        # begin checking log file for changes
        asyncio.ensure_future(self.tick())

        logging.info("Ready!")

    async def setup_hook(self) -> None:
        self.tree.copy_global_to(guild=discord.Object(id=CONFIG["guild"]))
        await self.tree.sync()

    async def tick(self) -> None:
        with open("logs/latest.log", "r") as log:
            # consume existing lines
            log.readlines()

            while True:
                lines = log.readlines()

                for line in lines:
                    if SERVER_MESSAGE_RE.match(line):
                        info = SERVER_MESSAGE_RE.findall(line)[0]
                        user = info[0]
                        msg = info[1]

                        # No.
                        if ("@everyone" in msg) or ("@here" in msg):
                            msg = msg.replace("@", "")

                        embed = discord.embeds.Embed(
                            color=discord.Color.teal(), description=msg
                        )
                        embed.set_author(
                            name=user, icon_url=await self.get_player_avatar(user)
                        )

                        await self.CHANNEL.send(embed=embed)

                    elif SERVER_JOIN_RE.match(line):
                        user = SERVER_JOIN_RE.findall(line)[0]

                        embed = discord.embeds.Embed(color=discord.Color.green())
                        embed.set_author(
                            name=f"📥 {user} joined the server",
                            icon_url=await self.get_player_avatar(user),
                        )

                        await self.CHANNEL.send(embed=embed)

                    elif SERVER_LEAVE_RE.match(line):
                        user = SERVER_LEAVE_RE.findall(line)[0]

                        embed = discord.embeds.Embed(color=discord.Color.red())
                        embed.set_author(
                            name=f"📤 {user} left the server",
                            icon_url=await self.get_player_avatar(user),
                        )

                        await self.CHANNEL.send(embed=embed)

                await asyncio.sleep(CONFIG["poll_rate"])

    async def get_player_avatar(self, username: str) -> str:
        if username not in self.AVATAR_CACHE:
            r = requests.get(f"https://playerdb.co/api/player/minecraft/{username}")
            if r.status_code != 200:
                return False

            r = r.json()
            self.AVATAR_CACHE[username] = r["data"]["player"]["avatar"]

        return self.AVATAR_CACHE[username]

    async def on_message(self, message: discord.Message) -> None:
        if message.author == self.user:
            return

        msg = message.content

        if message.channel.id == CONFIG["channel"]:
            discord_to_server(message.author.name, msg, len(message.attachments) != 0)


def rcon(cmd: str):
    with Client(
        CONFIG["address"], CONFIG["rcon_port"], passwd=CONFIG["rcon_pass"]
    ) as client:
        response = client.run(cmd)
    return response


def discord_to_server(sender: str, msg: str, has_att: bool):
    # sanitize: remove \ and "
    msg = msg.replace('"', "''")
    msg = msg.replace("\\", "")

    # max minecraft message length is 256;
    # " [...] (attachment)" (19) on max length 236+19=255
    if len(msg) > 242:
        msg = msg[:235] + " [...]"

    if has_att:
        msg = msg + " (attachment)"

    rcon(
        'tellraw @a [{"text":"(Discord) ", "color":"blue"}, {"text":"'
        + f"<{sender}> {msg}"
        + '", "color":"white"}]',
    )


client = DiscordBot()


@client.tree.command(name="list", description="See online players")
async def _list(interaction: discord.Interaction) -> None:
    playerlist = rcon("list")

    info = SERVER_LIST_RE.findall(playerlist)[0]
    current = int(info[0])
    max = int(info[1])
    if current != 0:
        listing = info[2].split(", ")
        listing = "- " + "\n- ".join(listing)
    else:
        listing = "There are no players online..."

    embed = discord.embeds.Embed(
        color=discord.Color.og_blurple(),
        title=f"Players ({current}/{max})",
        description=listing,
    )
    await interaction.response.send_message(embed=embed)


@client.tree.command(name="help", description="See available commands")
async def _help(interaction: discord.Interaction) -> None:
    commands = await client.tree.fetch_commands()
    listing = "- " + "\n- ".join([c.name for c in commands])

    embed = discord.embeds.Embed(
        color=discord.Color.og_blurple(), title="Commands", description=listing
    )
    await interaction.response.send_message(embed=embed)


client.run(CONFIG["token"])
