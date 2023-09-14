# fmcs-server relay bot
# this is pretty haphazardly thrown together, rewrite eventually

import asyncio
import discord
import yaml
import logging
import sys
import re
import traceback

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

        self.PREFIX = "r!"
        self.COMMANDS = {
            "help": {
                "func": self.help,
                "help": "Show all commands, or help for a specific command.\nUsage: `help <command?>`",
            },
        }

        self.tree = discord.app_commands.CommandTree(self)

    async def on_ready(self):
        logging.info("Connected to Discord")

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
                        if "@everyone" or "@here" in msg:
                            msg.replace("@", "")

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

        if not msg.startswith(self.PREFIX):
            if message.channel.id == CONFIG["channel"]:
                discord_to_server(message.author.name, msg)

            return

        msg_cmd = msg[len(self.PREFIX) :].split(" ")
        args = msg_cmd[1:]
        cmd = msg_cmd[0]

        if cmd not in self.COMMANDS:
            return

        result = await self.run_command(cmd, message, args)
        if result:
            await message.channel.send(result)

    async def run_command(self, cmd, message: discord.Message, args):
        try:
            logging.info(f"Running command {cmd} (args:{args}) from {message.author}")
            return await self.COMMANDS[cmd]["func"](message, args)

        except ExitCommandWithMessage as msg:
            return msg

        except Exception:
            logging.error(traceback.format_exc())
            return f"Something went wrong! See logs for a stack trace. Raise an issue on the GitHub! <https://github.com/jack-avery/fmcs-server>"

    ###
    #
    #   Commands
    #
    ###

    async def help(self, message: discord.Message, args):
        if args:
            cmd = args[0]
            if cmd in self.COMMANDS:
                return self.COMMANDS[cmd]["help"]

        return (
            f"Available commands: {', '.join(self.COMMANDS)}"
            + f"\nYou can show help for a specific command using `help <command>`."
        )


class ExitCommandWithMessage(Exception):
    pass


def rcon(cmd: str):
    with Client(
        CONFIG["address"], CONFIG["rcon_port"], passwd=CONFIG["rcon_pass"]
    ) as client:
        response = client.run(cmd)
    return response


def discord_to_server(sender: str, msg: str):
    rcon(
        'tellraw @a [{"text":"(Discord) ", "color":"blue"}, {"text":"'
        + f"<{sender}> {msg}"
        + '", "color":"white"}]',
    )


client = DiscordBot()


@client.tree.command(name="list", description="See online players")
async def _list(interaction: discord.Interaction) -> None:
    playerlist = rcon("list")
    await interaction.response.send_message(playerlist)


client.run(CONFIG["token"])
