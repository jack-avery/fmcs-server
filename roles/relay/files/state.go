package main

import "github.com/bwmarrin/discordgo"

type State struct {
	ServerIsOnline     bool
	Players            []string
	CurrentPlayerCount int
	MaxPlayers         int
	Day                int
	AvatarURLCache     map[string]string
	Webhook            *discordgo.Webhook
}

func NewState() State {
	return State{
		// assume server is online when bot starts, otherwise it will announce
		ServerIsOnline:     true,
		Players:            []string{},
		Day:                -1,
		CurrentPlayerCount: -1,
		MaxPlayers:         -1,
		AvatarURLCache:     make(map[string]string),
		Webhook:            nil,
	}
}
