import re

# minecraft.jar/assets/minecraft/lang/en_us, death.* (except message_too_long)
# replace %1$s, %2$s -> ([a-zA-Z0-9_]+)
# replace %3$s -> (.+)
MINECRAFT_DEATH_MESSAGES_RE = [
    re.compile(r"([a-zA-Z0-9_]+) was squashed by a falling anvil"),
    re.compile(
        r"([a-zA-Z0-9_]+) was squashed by a falling anvil whilst fighting ([a-zA-Z0-9_]+)"
    ),
    re.compile(r"([a-zA-Z0-9_]+) was shot by ([a-zA-Z0-9_]+)"),
    re.compile(r"([a-zA-Z0-9_]+) was shot by ([a-zA-Z0-9_]+) using (.+)"),
    re.compile(
        r"([a-zA-Z0-9_]+) was killed by ([a-zA-Z0-9_\[\]]+)"
    ),  # include [] on this for [Intentional Game Design]
    re.compile(r"([a-zA-Z0-9_]+) was pricked to death"),
    re.compile(
        r"([a-zA-Z0-9_]+) walked into a cactus whilst trying to escape ([a-zA-Z0-9_]+)"
    ),
    re.compile(r"([a-zA-Z0-9_]+) was squished too much"),
    re.compile(r"([a-zA-Z0-9_]+) was squashed by ([a-zA-Z0-9_]+)"),
    re.compile(r"([a-zA-Z0-9_]+) was roasted in dragon's breath"),
    re.compile(r"([a-zA-Z0-9_]+) was roasted in dragon's breath by ([a-zA-Z0-9_]+)"),
    re.compile(r"([a-zA-Z0-9_]+) drowned"),
    re.compile(r"([a-zA-Z0-9_]+) drowned whilst trying to escape ([a-zA-Z0-9_]+)"),
    re.compile(r"([a-zA-Z0-9_]+) died from dehydration"),
    re.compile(
        r"([a-zA-Z0-9_]+) died from dehydration whilst trying to escape ([a-zA-Z0-9_]+)"
    ),
    re.compile(r"([a-zA-Z0-9_]+) was killed by even more magic"),
    re.compile(r"([a-zA-Z0-9_]+) blew up"),
    re.compile(r"([a-zA-Z0-9_]+) was blown up by ([a-zA-Z0-9_]+)"),
    re.compile(r"([a-zA-Z0-9_]+) was blown up by ([a-zA-Z0-9_]+) using (.+)"),
    re.compile(r"([a-zA-Z0-9_]+) hit the ground too hard"),
    re.compile(
        r"([a-zA-Z0-9_]+) hit the ground too hard whilst trying to escape ([a-zA-Z0-9_]+)"
    ),
    re.compile(r"([a-zA-Z0-9_]+) was squashed by a falling block"),
    re.compile(
        r"([a-zA-Z0-9_]+) was squashed by a falling block whilst fighting ([a-zA-Z0-9_]+)"
    ),
    re.compile(r"([a-zA-Z0-9_]+) was skewered by a falling stalactite"),
    re.compile(
        r"([a-zA-Z0-9_]+) was skewered by a falling stalactite whilst fighting ([a-zA-Z0-9_]+)"
    ),
    re.compile(r"([a-zA-Z0-9_]+) was fireballed by ([a-zA-Z0-9_]+)"),
    re.compile(r"([a-zA-Z0-9_]+) was fireballed by ([a-zA-Z0-9_]+) using (.+)"),
    re.compile(r"([a-zA-Z0-9_]+) went off with a bang"),
    re.compile(
        r"([a-zA-Z0-9_]+) went off with a bang due to a firework fired from (.+) by ([a-zA-Z0-9_]+)"
    ),
    re.compile(r"([a-zA-Z0-9_]+) went off with a bang whilst fighting ([a-zA-Z0-9_]+)"),
    re.compile(r"([a-zA-Z0-9_]+) experienced kinetic energy"),
    re.compile(
        r"([a-zA-Z0-9_]+) experienced kinetic energy whilst trying to escape ([a-zA-Z0-9_]+)"
    ),
    re.compile(r"([a-zA-Z0-9_]+) froze to death"),
    re.compile(r"([a-zA-Z0-9_]+) was frozen to death by ([a-zA-Z0-9_]+)"),
    re.compile(r"([a-zA-Z0-9_]+) died"),
    re.compile(r"([a-zA-Z0-9_]+) was killed"),
    re.compile(r"([a-zA-Z0-9_]+) was killed whilst fighting ([a-zA-Z0-9_]+)"),
    re.compile(r"([a-zA-Z0-9_]+) died because of ([a-zA-Z0-9_]+)"),
    re.compile(r"([a-zA-Z0-9_]+) discovered the floor was lava"),
    re.compile(r"([a-zA-Z0-9_]+) walked into the danger zone due to ([a-zA-Z0-9_]+)"),
    re.compile(r"([a-zA-Z0-9_]+) was killed by ([a-zA-Z0-9_]+) using magic"),
    re.compile(r"([a-zA-Z0-9_]+) was killed by ([a-zA-Z0-9_]+) using (.+)"),
    re.compile(r"([a-zA-Z0-9_]+) went up in flames"),
    re.compile(r"([a-zA-Z0-9_]+) walked into fire whilst fighting ([a-zA-Z0-9_]+)"),
    re.compile(r"([a-zA-Z0-9_]+) suffocated in a wall"),
    re.compile(r"([a-zA-Z0-9_]+) suffocated in a wall whilst fighting ([a-zA-Z0-9_]+)"),
    re.compile(r"([a-zA-Z0-9_]+) tried to swim in lava"),
    re.compile(r"([a-zA-Z0-9_]+) tried to swim in lava to escape ([a-zA-Z0-9_]+)"),
    re.compile(r"([a-zA-Z0-9_]+) was struck by lightning"),
    re.compile(
        r"([a-zA-Z0-9_]+) was struck by lightning whilst fighting ([a-zA-Z0-9_]+)"
    ),
    re.compile(r"([a-zA-Z0-9_]+) was killed by magic"),
    re.compile(
        r"([a-zA-Z0-9_]+) was killed by magic whilst trying to escape ([a-zA-Z0-9_]+)"
    ),
    re.compile(r"([a-zA-Z0-9_]+) was slain by ([a-zA-Z0-9_]+)"),
    re.compile(r"([a-zA-Z0-9_]+) was slain by ([a-zA-Z0-9_]+) using (.+)"),
    re.compile(r"([a-zA-Z0-9_]+) burned to death"),
    re.compile(
        r"([a-zA-Z0-9_]+) was burnt to a crisp whilst fighting ([a-zA-Z0-9_]+) wielding (.+)"
    ),
    re.compile(r"([a-zA-Z0-9_]+) was burnt to a crisp whilst fighting ([a-zA-Z0-9_]+)"),
    re.compile(r"([a-zA-Z0-9_]+) left the confines of this world"),
    re.compile(
        r"([a-zA-Z0-9_]+) left the confines of this world whilst fighting ([a-zA-Z0-9_]+)"
    ),
    re.compile(r"([a-zA-Z0-9_]+) fell out of the world"),
    re.compile(
        r"([a-zA-Z0-9_]+) didn't want to live in the same world as ([a-zA-Z0-9_]+)"
    ),
    re.compile(r"([a-zA-Z0-9_]+) was slain by ([a-zA-Z0-9_]+)"),
    re.compile(r"([a-zA-Z0-9_]+) was slain by ([a-zA-Z0-9_]+) using (.+)"),
    re.compile(r"([a-zA-Z0-9_]+) was obliterated by a sonically-charged shriek"),
    re.compile(
        r"([a-zA-Z0-9_]+) was obliterated by a sonically-charged shriek whilst trying to escape ([a-zA-Z0-9_]+) wielding (.+)"
    ),
    re.compile(
        r"([a-zA-Z0-9_]+) was obliterated by a sonically-charged shriek whilst trying to escape ([a-zA-Z0-9_]+)"
    ),
    re.compile(r"([a-zA-Z0-9_]+) was impaled on a stalagmite"),
    re.compile(
        r"([a-zA-Z0-9_]+) was impaled on a stalagmite whilst fighting ([a-zA-Z0-9_]+)"
    ),
    re.compile(r"([a-zA-Z0-9_]+) starved to death"),
    re.compile(r"([a-zA-Z0-9_]+) starved to death whilst fighting ([a-zA-Z0-9_]+)"),
    re.compile(r"([a-zA-Z0-9_]+) was stung to death"),
    re.compile(r"([a-zA-Z0-9_]+) was stung to death by ([a-zA-Z0-9_]+) using (.+)"),
    re.compile(r"([a-zA-Z0-9_]+) was stung to death by ([a-zA-Z0-9_]+)"),
    re.compile(r"([a-zA-Z0-9_]+) was poked to death by a sweet berry bush"),
    re.compile(
        r"([a-zA-Z0-9_]+) was poked to death by a sweet berry bush whilst trying to escape ([a-zA-Z0-9_]+)"
    ),
    re.compile(r"([a-zA-Z0-9_]+) was killed trying to hurt ([a-zA-Z0-9_]+)"),
    re.compile(r"([a-zA-Z0-9_]+) was killed by (.+) trying to hurt ([a-zA-Z0-9_]+)"),
    re.compile(r"([a-zA-Z0-9_]+) was pummeled by ([a-zA-Z0-9_]+)"),
    re.compile(r"([a-zA-Z0-9_]+) was pummeled by ([a-zA-Z0-9_]+) using (.+)"),
    re.compile(r"([a-zA-Z0-9_]+) was impaled by ([a-zA-Z0-9_]+)"),
    re.compile(r"([a-zA-Z0-9_]+) was impaled by ([a-zA-Z0-9_]+) with (.+)"),
    re.compile(r"([a-zA-Z0-9_]+) withered away"),
    re.compile(r"([a-zA-Z0-9_]+) withered away whilst fighting ([a-zA-Z0-9_]+)"),
    re.compile(r"([a-zA-Z0-9_]+) was shot by a skull from ([a-zA-Z0-9_]+)"),
    re.compile(r"([a-zA-Z0-9_]+) was shot by a skull from ([a-zA-Z0-9_]+) using (.+)"),
    re.compile(r"([a-zA-Z0-9_]+) fell from a high place"),
    re.compile(r"([a-zA-Z0-9_]+) fell off a ladder"),
    re.compile(r"([a-zA-Z0-9_]+) fell while climbing"),
    re.compile(r"([a-zA-Z0-9_]+) fell off scaffolding"),
    re.compile(r"([a-zA-Z0-9_]+) fell off some twisting vines"),
    re.compile(r"([a-zA-Z0-9_]+) fell off some vines"),
    re.compile(r"([a-zA-Z0-9_]+) fell off some weeping vines"),
    re.compile(r"([a-zA-Z0-9_]+) was doomed to fall by ([a-zA-Z0-9_]+)"),
    re.compile(r"([a-zA-Z0-9_]+) was doomed to fall by ([a-zA-Z0-9_]+) using (.+)"),
    re.compile(r"([a-zA-Z0-9_]+) fell too far and was finished by ([a-zA-Z0-9_]+)"),
    re.compile(
        r"([a-zA-Z0-9_]+) fell too far and was finished by ([a-zA-Z0-9_]+) using (.+)"
    ),
    re.compile(r"([a-zA-Z0-9_]+) was doomed to fall"),
]

SERVER_INFO_RE = re.compile(
    r"\[(?:[a-zA-Z0-9]+ )?[0-9:.]+\] \[Server thread/INFO\](?: \[net.minecraft.server.MinecraftServer\/\])?: (.+)"
)
SERVER_LIST_RE = re.compile(r"There are (\d+) of a max of (\d+) players online: (.+)?")
SERVER_TIME_RE = re.compile(r"The time is (\d+)")
SERVER_MESSAGE_RE = re.compile(r"<([a-zA-Z0-9_]+)> (.+)")
SERVER_SYSTEM_MESSAGE_RE = re.compile(r"(?:\[Not Secure\] )?\[Rcon\] (.+)")
SERVER_ACTION_RE = re.compile(r"\* ([a-zA-Z0-9_]+) .+")
SERVER_ADVANCEMENT_RE = re.compile(r"([a-zA-Z0-9_]+) has made the advancement \[.+\]")
SERVER_CHALLENGE_RE = re.compile(r"([a-zA-Z0-9_]+) has completed the challenge \[.+\]")
SERVER_JOIN_RE = re.compile(r"([a-zA-Z0-9_]+) joined the game")
SERVER_LEAVE_RE = re.compile(r"([a-zA-Z0-9_]+) left the game")
SERVER_PLAYER_RE = re.compile(r"([a-zA-Z0-9_]+)")

DISCORD_MENTION_RE = re.compile(r"<@\d+>")
DISCORD_CHANNEL_RE = re.compile(r"<#\d+>")
DISCORD_EMOTE_RE = re.compile(r"(<a?(:[a-zA-Z0-9_]+:)\d+>)")
