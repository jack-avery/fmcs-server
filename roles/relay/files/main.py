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

SERVER_INFO_RE = re.compile(r"\[[0-9:]+\] \[Server thread/INFO\]: (.+)")
SERVER_LIST_RE = re.compile(r"There are (\d+) of a max of (\d+) players online: (.+)?")
SERVER_MESSAGE_RE = re.compile(r"<([a-zA-Z0-9_]+)> (.+)")
SERVER_ADVANCEMENT_RE = re.compile(r"([a-zA-Z0-9_]+) has made the advancement \[.+\]")
SERVER_CHALLENGE_RE = re.compile(r"([a-zA-Z0-9_]+) has completed the challenge \[.+\]")
SERVER_JOIN_RE = re.compile(r"([a-zA-Z0-9_]+) joined the game")
SERVER_LEAVE_RE = re.compile(r"([a-zA-Z0-9_]+) left the game")

DISCORD_MENTION_RE = re.compile(r"<@\d+>")
DISCORD_CHANNEL_RE = re.compile(r"<#\d+>")
DISCORD_EMOTE_RE = re.compile(r"(<a?(:[a-zA-Z0-9_]+:)\d+>)")

# This should be ALL of them, sorted in order of which regex catches most or is most likely to show up
SERVER_DEATH_MESSAGES_RE = [
    re.compile(
        r"([a-zA-Z0-9_]+) was (?:shot|pummeled|blown up|killed|squashed|skewered|struck|slain|frozen to death|fireballed|stung|squashed|poked to death|impaled) by .+"
    ),
    re.compile(
        r"([a-zA-Z0-9_]+) (?:starved|burned|froze|was stung|was pricked) to death"
    ),
    re.compile(r"([a-zA-Z0-9_]+) .+ whilst trying to escape .+"),
    re.compile(r"([a-zA-Z0-9_]+) .+ whilst fighting .+"),
    re.compile(r"([a-zA-Z0-9_]+) drowned"),
    re.compile(r"([a-zA-Z0-9_]+) blew up"),
    re.compile(r"([a-zA-Z0-9_]+) hit the ground too hard"),
    re.compile(r"([a-zA-Z0-9_]+) fell from a high place"),
    re.compile(
        r"([a-zA-Z0-9_]+) fell off (?:a ladder|some vines|some weeping vines|some twisting vines|scaffolding)"
    ),
    re.compile(r"([a-zA-Z0-9_]+) fell while climbing"),
    re.compile(r"([a-zA-Z0-9_]+) experienced kinetic energy"),
    re.compile(r"([a-zA-Z0-9_]+) was impaled on a stalagmite"),
    re.compile(r"([a-zA-Z0-9_]+) went up in flames"),
    re.compile(r"([a-zA-Z0-9_]+) went off with a bang"),
    re.compile(r"([a-zA-Z0-9_]+) went off with a bang due to a firework fired from .+"),
    re.compile(r"([a-zA-Z0-9_]+) tried to swim in lava"),
    re.compile(r"([a-zA-Z0-9_]+) tried to swim in lava to escape .+"),
    re.compile(r"([a-zA-Z0-9_]+) was struck by lightning"),
    re.compile(r"([a-zA-Z0-9_]+) discovered the floor was lava"),
    re.compile(r"([a-zA-Z0-9_]+) walked into danger zone due to .+"),
    re.compile(r"([a-zA-Z0-9_]+) was shot by a skull from .+"),
    re.compile(r"([a-zA-Z0-9_]+) suffocated in a wall"),
    re.compile(r"([a-zA-Z0-9_]+) was squished too much"),
    re.compile(r"([a-zA-Z0-9_]+) was killed trying to hurt .+"),
    re.compile(r"([a-zA-Z0-9_]+) fell out of the world"),
    re.compile(r"([a-zA-Z0-9_]+) withered away"),
    re.compile(r"([a-zA-Z0-9_]+) was killed"),
]


def rcon(cmd: str) -> str:
    with Client(
        CONFIG["address"], CONFIG["rcon_port"], passwd=CONFIG["rcon_pass"]
    ) as client:
        response = client.run(cmd)
    return response


class DiscordBot(discord.Client):
    def __init__(self):
        # I don't know which to use, so we just do this.
        discord.Client.__init__(self, intents=discord.Intents().all())
        self.tree = discord.app_commands.CommandTree(self)
        self.SETUP = False

    async def on_ready(self) -> None:
        if not self.SETUP:
            # find relay channel
            self.CHANNEL = self.get_channel(CONFIG["channel"])
            self.AVATAR_CACHE = dict()

            # get guild from channel; add commands
            self.tree.copy_global_to(guild=discord.Object(id=self.CHANNEL.guild.id))
            await self.tree.sync()

            # begin checking log file for changes
            if "debug" not in sys.argv:
                asyncio.ensure_future(self.poll_logs())

            logging.info("Ready!")
            self.SETUP = True

    async def poll_logs(self) -> None:
        """
        Poll the logs every `CONFIG["poll_rate"]` seconds for new messages, connects, or disconnects.
        """
        # consume existing lines
        log = open("logs/latest.log", "r")
        log.readlines()

        while True:
            lines = log.readlines()

            for line in lines:
                raw = line

                if not SERVER_INFO_RE.match(line):
                    continue

                line = SERVER_INFO_RE.findall(line)[0]

                try:
                    if SERVER_MESSAGE_RE.match(line):
                        info = SERVER_MESSAGE_RE.findall(line)[0]
                        user = info[0]
                        msg = info[1]

                        embed = discord.embeds.Embed(
                            color=discord.Color.teal(), description=msg
                        )
                        embed.set_author(
                            name=user, icon_url=await self.get_player_avatar(user)
                        )

                        await self.CHANNEL.send(embed=embed)
                        continue

                    if SERVER_JOIN_RE.match(line):
                        user = SERVER_JOIN_RE.findall(line)[0]

                        embed = discord.embeds.Embed(color=discord.Color.green())
                        embed.set_author(
                            name=f"📥 {user} joined the server",
                            icon_url=await self.get_player_avatar(user),
                        )

                        await self.CHANNEL.send(embed=embed)

                    if SERVER_LEAVE_RE.match(line):
                        user = SERVER_LEAVE_RE.findall(line)[0]

                        embed = discord.embeds.Embed(color=discord.Color.red())
                        embed.set_author(
                            name=f"📤 {user} left the server",
                            icon_url=await self.get_player_avatar(user),
                        )

                        await self.CHANNEL.send(embed=embed)
                        continue

                    if SERVER_ADVANCEMENT_RE.match(line):
                        user = SERVER_ADVANCEMENT_RE.findall(line)[0]

                        embed = discord.embeds.Embed(color=discord.Color.teal())
                        embed.set_author(
                            name=f"📖 {line}",
                            icon_url=await self.get_player_avatar(user),
                        )

                        await self.CHANNEL.send(embed=embed)
                        continue

                    if SERVER_CHALLENGE_RE.match(line):
                        user = SERVER_CHALLENGE_RE.findall(line)[0]

                        embed = discord.embeds.Embed(color=discord.Color.gold())
                        embed.set_author(
                            name=f"🏆 {line}",
                            icon_url=await self.get_player_avatar(user),
                        )

                        await self.CHANNEL.send(embed=embed)
                        continue

                    for r in SERVER_DEATH_MESSAGES_RE:
                        if r.match(line):
                            user = r.findall(line)[0]

                            embed = discord.embeds.Embed(color=discord.Color.dark_red())
                            embed.set_author(
                                name=f"💀 {line}",
                                icon_url=await self.get_player_avatar(user),
                            )

                            await self.CHANNEL.send(embed=embed)
                            break

                except Exception as err:
                    embed = discord.embeds.Embed(
                        color=discord.Color.red(),
                        description=f"{raw}\n\n{err.with_traceback()}",
                    )
                    embed.set_author(
                        name=f"Failed to send message from server",
                        icon_url=self.application.icon.url,
                    )

            await asyncio.sleep(CONFIG["poll_rate"])

    async def get_player_avatar(self, username: str) -> str:
        """
        Get the URL for an icon of given user's Minecraft avatar.

        :param username: Minecraft username

        :returns: URL for icon of `username`
        """
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

        # send messages from configured channel ingame
        if message.channel.id == CONFIG["channel"]:
            msg = message.content

            # replace mentions with raw text
            if DISCORD_MENTION_RE.search(msg):
                for m, c in zip(DISCORD_MENTION_RE.findall(msg), message.mentions):
                    msg = msg.replace(m, f"@{c.display_name}")

            # replace channel mentions with raw text
            if DISCORD_CHANNEL_RE.search(msg):
                for m, c in zip(
                    DISCORD_CHANNEL_RE.findall(msg), message.channel_mentions
                ):
                    msg = msg.replace(m, f"#{c.name}")

            # replace emotes with raw text
            if DISCORD_EMOTE_RE.search(msg):
                for m, e in DISCORD_EMOTE_RE.findall(msg):
                    msg = msg.replace(m, e)

            # sanitize: remove \ and "
            msg = msg.replace('"', "''")
            msg = msg.replace("\\", "")

            msg = f"<{message.author.display_name}> {msg}"

            # max minecraft message length is 256;
            # " [...] (attachment)" (19) on max length 236+19=255
            if len(msg) > 242:
                msg = msg[:235] + " [...]"

            if len(message.attachments) != 0:
                msg = msg + " (attachment)"

            rcon(
                'tellraw @a [{"text":"(Discord) ", "color":"blue"}, {"text":"'
                + msg
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


@client.tree.command(
    name="rcon", description="Run a command on the server through rcon"
)
async def _rcon(interaction: discord.Interaction, command: str) -> None:
    if interaction.user.id not in CONFIG["rcon_users"]:
        embed = discord.embeds.Embed(
            color=discord.Color.red(),
            description="You do not have access to that command.",
        )
        await interaction.response.send_message(embed=embed)
        return

    response = rcon(command)
    if len(response) == 0:
        response = "*Command does not have a response*"

    embed = discord.embeds.Embed(
        color=discord.Color.og_blurple(), title="Command", description=response
    )
    await interaction.response.send_message(embed=embed)


client.run(CONFIG["token"])
