package main

import (
	"regexp"
)

var deathMessagesRe = []*regexp.Regexp{
	regexp.MustCompile(`([a-zA-Z0-9_]+) was squashed by a falling anvil`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was squashed by a falling anvil whilst fighting ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was shot by ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was shot by ([a-zA-Z0-9_]+) using (.+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was killed by ([a-zA-Z0-9_\[\]]+)`), // include [] on this for [Intentional Game Design]
	regexp.MustCompile(`([a-zA-Z0-9_]+) was pricked to death`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) walked into a cactus whilst trying to escape ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was squished too much`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was squashed by ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was roasted in dragon's breath`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was roasted in dragon's breath by ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) drowned`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) drowned whilst trying to escape ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) died from dehydration`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) died from dehydration whilst trying to escape ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was killed by even more magic`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) blew up`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was blown up by ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was blown up by ([a-zA-Z0-9_]+) using (.+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) hit the ground too hard`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) hit the ground too hard whilst trying to escape ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was squashed by a falling block`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was squashed by a falling block whilst fighting ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was skewered by a falling stalactite`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was skewered by a falling stalactite whilst fighting ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was fireballed by ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was fireballed by ([a-zA-Z0-9_]+) using (.+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) went off with a bang`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) went off with a bang due to a firework fired from (.+) by ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) went off with a bang whilst fighting ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) experienced kinetic energy`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) experienced kinetic energy whilst trying to escape ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) froze to death`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was frozen to death by ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) died`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was killed`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was killed whilst fighting ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) died because of ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) discovered the floor was lava`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) walked into the danger zone due to ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was killed by ([a-zA-Z0-9_]+) using magic`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was killed by ([a-zA-Z0-9_]+) using (.+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) went up in flames`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) walked into fire whilst fighting ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) suffocated in a wall`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) suffocated in a wall whilst fighting ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) tried to swim in lava`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) tried to swim in lava to escape ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was struck by lightning`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was struck by lightning whilst fighting ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was killed by magic`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was killed by magic whilst trying to escape ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was slain by ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was slain by ([a-zA-Z0-9_]+) using (.+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) burned to death`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was burnt to a crisp whilst fighting ([a-zA-Z0-9_]+) wielding (.+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was burnt to a crisp whilst fighting ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) left the confines of this world`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) left the confines of this world whilst fighting ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) fell out of the world`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) didn't want to live in the same world as ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was slain by ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was slain by ([a-zA-Z0-9_]+) using (.+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was obliterated by a sonically-charged shriek`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was obliterated by a sonically-charged shriek whilst trying to escape ([a-zA-Z0-9_]+) wielding (.+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was obliterated by a sonically-charged shriek whilst trying to escape ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was impaled on a stalagmite`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was impaled on a stalagmite whilst fighting ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) starved to death`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) starved to death whilst fighting ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was stung to death`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was stung to death by ([a-zA-Z0-9_]+) using (.+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was stung to death by ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was poked to death by a sweet berry bush`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was poked to death by a sweet berry bush whilst trying to escape ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was killed trying to hurt ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was killed by (.+) trying to hurt ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was pummeled by ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was pummeled by ([a-zA-Z0-9_]+) using (.+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was impaled by ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was impaled by ([a-zA-Z0-9_]+) with (.+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) withered away`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) withered away whilst fighting ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was shot by a skull from ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was shot by a skull from ([a-zA-Z0-9_]+) using (.+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) fell from a high place`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) fell off a ladder`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) fell while climbing`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) fell off scaffolding`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) fell off some twisting vines`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) fell off some vines`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) fell off some weeping vines`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was doomed to fall by ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was doomed to fall by ([a-zA-Z0-9_]+) using (.+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) fell too far and was finished by ([a-zA-Z0-9_]+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) fell too far and was finished by ([a-zA-Z0-9_]+) using (.+)`),
	regexp.MustCompile(`([a-zA-Z0-9_]+) was doomed to fall`),
}

var serverInfoRe = regexp.MustCompile(`\[(?:[a-zA-Z0-9]+ )?[0-9:.]+\] \[Server thread/INFO\](?: \[net.minecraft.server.MinecraftServer\/\])?: (.+)`)
var serverListRe = regexp.MustCompile(`There are (\d+) of a max of (\d+) players online: (.+)?`)
var serverTimeRe = regexp.MustCompile(`The time is (\d+)`)
var serverMessageRe = regexp.MustCompile(`<([a-zA-Z0-9_]+)> (.+)`)
var serverSystemMessageRe = regexp.MustCompile(`(?:\[Not Secure\] )?\[Rcon\] (.+)`)
var serverActionRe = regexp.MustCompile(`\* ([a-zA-Z0-9_]+) .+`)
var serverAdvancementRe = regexp.MustCompile(`([a-zA-Z0-9_]+) has made the advancement \[.+\]`)
var serverChallengeRe = regexp.MustCompile(`([a-zA-Z0-9_]+) has completed the challenge \[.+\]`)
var serverJoinRe = regexp.MustCompile(`([a-zA-Z0-9_]+) joined the game`)
var serverLeaveRe = regexp.MustCompile(`([a-zA-Z0-9_]+) left the game`)
var serverPlayerNameRe = regexp.MustCompile(`([a-zA-Z0-9_]+)`)

var discordMentionRe = regexp.MustCompile(`<@\d+>`)
var discordChannelRe = regexp.MustCompile(`<#(\d+)>`)
var discordEmoteRe = regexp.MustCompile(`<a?(:[a-zA-Z0-9_]+:)\d+>`)
