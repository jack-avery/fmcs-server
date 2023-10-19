# fmcs-server relay bot
# this is pretty haphazardly thrown together, rewrite eventually

import asyncio
import discord
import logging
import requests
import sys
import yaml
from datetime import date

from rcon.source import Client

from src.regex import *

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


def rcon(cmd: str) -> str:
    try:
        with Client(
            CONFIG["rcon_addr"], CONFIG["port"] + 1, passwd=CONFIG["rcon_pass"]
        ) as client:
            response = client.run(cmd)
        return response
    except:
        return None


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

            # create webhook if it doesn't exist
            self.WEBHOOK = None
            for webhook in await self.CHANNEL.webhooks():
                if webhook.user == self.user:
                    self.WEBHOOK = webhook
            if self.WEBHOOK is None:
                self.WEBHOOK = await self.CHANNEL.create_webhook(name="fmcs-server")

            self.AVATAR_CACHE = dict()

            # get guild from channel; add commands
            self.tree.copy_global_to(guild=discord.Object(id=self.CHANNEL.guild.id))
            await self.tree.sync()

            # begin checking log file for changes
            if "debug" not in sys.argv:
                asyncio.ensure_future(self.poll_logs())

            logging.info("Ready!")
            self.SETUP = True

        asyncio.ensure_future(self.poll_status())

    async def update_status(self) -> None:
        playerlist = rcon("list")

        if not playerlist:
            await self.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name="for server restart...",
                )
            )
            return

        info = SERVER_LIST_RE.findall(playerlist)[0]
        current = int(info[0])

        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{current} player{'' if current == 1 else 's'}",
            )
        )

    async def poll_status(self, frequency: int = 60) -> None:
        while True:
            await self.update_status()
            await asyncio.sleep(frequency)

    async def poll_logs(self) -> None:
        """
        Poll the logs every `CONFIG["poll_rate"]` seconds for new messages, connects, or disconnects.
        """
        # consume existing lines
        log = open("logs/latest.log", "r")
        log.readlines()

        while True:
            last_poll_start_date = date.today()

            lines = log.readlines()
            for line in lines:
                raw = line

                if not SERVER_INFO_RE.match(line):
                    continue

                line = SERVER_INFO_RE.findall(line)[0]

                try:
                    if SERVER_SYSTEM_MESSAGE_RE.match(line):
                        info = SERVER_SYSTEM_MESSAGE_RE.findall(line)[0]

                        embed = discord.embeds.Embed(
                            color=discord.Color.dark_magenta(), description=info
                        )
                        embed.set_author(
                            name="System Message", icon_url=self.user.display_avatar.url
                        )

                        await self.CHANNEL.send(embed=embed)
                        continue

                    if CONFIG["relay_messages"]:
                        if SERVER_MESSAGE_RE.match(line):
                            info = SERVER_MESSAGE_RE.findall(line)[0]
                            user = info[0]
                            msg = info[1]

                            embed = discord.embeds.Embed(description=msg)

                            await self.WEBHOOK.send(
                                embed=embed,
                                username=user,
                                avatar_url=await self.get_player_avatar(user),
                            )
                            continue

                        if SERVER_ACTION_RE.match(line):
                            user = SERVER_ACTION_RE.findall(line)[0]

                            embed = discord.embeds.Embed(color=discord.Color.teal())
                            embed.set_author(
                                name=line, icon_url=await self.get_player_avatar(user)
                            )

                            await self.CHANNEL.send(embed=embed)
                            continue

                    if CONFIG["relay_connections"]:
                        if SERVER_JOIN_RE.match(line):
                            user = SERVER_JOIN_RE.findall(line)[0]

                            embed = discord.embeds.Embed(color=discord.Color.green())
                            embed.set_author(
                                name=f"📥 {line}",
                                icon_url=await self.get_player_avatar(user),
                            )

                            await self.CHANNEL.send(embed=embed)
                            await self.update_status()
                            continue

                        if SERVER_LEAVE_RE.match(line):
                            user = SERVER_LEAVE_RE.findall(line)[0]

                            embed = discord.embeds.Embed(color=discord.Color.red())
                            embed.set_author(
                                name=f"📤 {line}",
                                icon_url=await self.get_player_avatar(user),
                            )

                            await self.CHANNEL.send(embed=embed)
                            await self.update_status()
                            continue

                    if CONFIG["relay_advancements"]:
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

                    if CONFIG["relay_deaths"]:
                        for r in MINECRAFT_DEATH_MESSAGES_RE:
                            if r.match(line):
                                user = r.findall(line)[0]

                                if isinstance(user, tuple):
                                    user = user[0]

                                embed = discord.embeds.Embed(
                                    color=discord.Color.dark_red()
                                )
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
                    await self.CHANNEL.send(embed=embed)

            await asyncio.sleep(CONFIG["poll_rate"])

            # grab new log file if day changed
            if date.today() != last_poll_start_date:
                # force new file to be opened
                rcon("list")
                # wait 1 second to be sure
                await asyncio.sleep(1)
                # grab it
                log = open("logs/latest.log", "r")

    async def get_player_avatar(self, username: str) -> str:
        """
        Get the URL for an icon of given user's Minecraft avatar.

        :param username: Minecraft username

        :returns: URL for icon of `username`
        """
        if not SERVER_PLAYER_RE.match(username):
            return

        if username not in self.AVATAR_CACHE:
            HEADERS = {"User-Agent": "github.com/jack-avery/fmcs-server"}
            r = requests.get(
                f"https://playerdb.co/api/player/minecraft/{username}", headers=HEADERS
            )
            if r.status_code != 200:
                return False

            r = r.json()
            self.AVATAR_CACHE[username] = r["data"]["player"]["avatar"]

        return self.AVATAR_CACHE[username]

    async def on_message(self, message: discord.Message) -> None:
        if message.author == self.user or message.author.bot:
            return

        if not CONFIG["relay_messages"]:
            return

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

            reply_note = ""
            if message.reference:
                reply = await self.CHANNEL.fetch_message(message.reference.message_id)
                reply_note = f" (replying to {reply.author.display_name})"

            # sanitize
            msg = msg.replace("'", "'")
            for i in ['"', '"']:
                msg = msg.replace(i, "'")

            msg = msg.replace("\\", "")

            for i in ["\n", "\r", "\t", "\f"]:
                msg = msg.replace(i, " ")

            msg = f"<{message.author.display_name}{reply_note}> {msg}"

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

    if not playerlist:
        embed = discord.embeds.Embed(
            color=discord.Color.red(),
            description="The server is not online!",
        )
        await interaction.response.send_message(embed=embed)
        return

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


@client.tree.command(
    name="info", description="Get info for the server and the ATLauncher manifest"
)
async def _info(interaction: discord.Interaction) -> None:
    description = f"Connect at `{CONFIG['address']}:{CONFIG['port']}`"

    # Whitelist note
    description += f"\nThe server {'**is**' if CONFIG['is_whitelist'] else 'is **not**'} using a whitelist."

    # Link Dynmap
    if CONFIG["has_dynmap"]:
        description += f"\nThe server has Dynmap available at: http://{CONFIG['address']}:{CONFIG['port'] + 3}"

    description += "\n\n> *ATLauncher manifest with used mods is attached.*"

    embed = discord.embeds.Embed(
        color=discord.Color.og_blurple(), title=f"Server info", description=description
    )
    await interaction.response.send_message(
        embed=embed, file=discord.File(CONFIG["atl_manifest"])
    )


@client.tree.command(name="help", description="See available commands")
async def _help(interaction: discord.Interaction) -> None:
    commands = await client.tree.fetch_commands()
    listing = "- " + "\n- ".join(
        [f"</{c.name}:{c.id}>: {c.description}" for c in commands]
    )

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
