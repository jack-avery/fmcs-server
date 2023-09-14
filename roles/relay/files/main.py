# fmcs-server relay bot
# this is pretty haphazardly thrown together, rewrite eventually

import asyncio
import discord
import yaml
import logging
import sys
import re

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

    async def on_ready(self):
        # record no. lines in log to not send old messages
        with open("logs/latest.log", "r") as log:
            ln = len(log.readlines())

        # find relay channel
        self.CHANNEL = self.get_channel(CONFIG["channel"])

        # begin checking log file for changes
        asyncio.ensure_future(self.tick(ln))

        logging.info("Ready!")

    async def setup_hook(self) -> None:
        self.tree.copy_global_to(guild=discord.Object(id=CONFIG["guild"]))
        await self.tree.sync()

    async def tick(self, ln):
        with open("logs/latest.log", "r") as log:
            while True:
                lines = log.readlines()
                _ln = len(lines)
                lines = lines[ln:]
                ln = _ln

                for line in lines:
                    if SERVER_MESSAGE_RE.match(line):
                        info = SERVER_MESSAGE_RE.findall(line)[0]
                        user = info[0]
                        msg = info[1]

                        # No.
                        if ("@everyone" in msg) or ("@here" in msg):
                            msg = msg.replace("@", "")

                        await self.CHANNEL.send(f"💬 **<{user}>** {msg}")
                        continue

                    elif SERVER_JOIN_RE.match(line):
                        user = SERVER_JOIN_RE.findall(line)[0]

                        await self.CHANNEL.send(f"📥 **{user}** joined the server")
                        continue

                    elif SERVER_LEAVE_RE.match(line):
                        user = SERVER_LEAVE_RE.findall(line)[0]

                        await self.CHANNEL.send(f"📤 **{user}** left the server")
                        continue

                await asyncio.sleep(CONFIG["poll_rate"])

    ###
    #
    #   Command bootstrap
    #
    ##

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return

        msg = message.content

        if message.channel.id == CONFIG["channel"]:
            discord_to_server(message.author.name, msg)


def rcon(cmd: str):
    with Client(
        CONFIG["address"], CONFIG["rcon_port"], passwd=CONFIG["rcon_pass"]
    ) as client:
        response = client.run(cmd)
    return response


def discord_to_server(sender: str, msg: str):
    msg = msg.replace('"', "''")
    rcon(
        'tellraw @a [{"text":"(Discord) ", "color":"blue"}, {"text":"'
        + f"<{sender}> {msg}"
        + '", "color":"white"}]',
    )


client = DiscordBot()


@client.tree.command(name="list", description="See online players")
async def _list(interaction: discord.Interaction) -> None:
    playerlist = rcon("list")
    embed = discord.embeds.Embed(color=discord.Color.teal(), description=playerlist)
    await interaction.response.send_message(embed=embed)


@client.tree.command(name="help", description="See available commands")
async def _help(interaction: discord.Interaction) -> None:
    commands = await client.tree.fetch_commands()
    commands = f"Available commands are: {', '.join([c.name for c in commands])}"
    embed = discord.embeds.Embed(color=discord.Color.teal(), description=commands)
    await interaction.response.send_message(embed=embed)


client.run(CONFIG["token"])
