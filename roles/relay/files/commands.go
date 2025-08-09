package main

import (
	"errors"
	"fmt"
	"os"
	"slices"
	"strconv"
	"strings"

	"github.com/bwmarrin/discordgo"
)

func sendError(b *Bot, i *discordgo.InteractionCreate, context string, err error) {
	b.session.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
		Type: discordgo.InteractionResponseChannelMessageWithSource,
		Data: &discordgo.InteractionResponseData{
			Embeds: []*discordgo.MessageEmbed{
				{
					Title:       "Error",
					Description: fmt.Sprintf("Context: %s, Error: %s", context, err.Error()),
					Color:       0xFF0000,
				},
			},
		},
	})
}

var (
	colorBlurple = 0x7289da

	commands = []*discordgo.ApplicationCommand{
		{
			Name:        "help",
			Description: "See available commands",
		},
		{
			Name:        "info",
			Description: "Get info for the server and the .mrpack",
		},
		{
			Name:        "list",
			Description: "See online players",
		},
		{
			Name:        "rcon",
			Description: "Issue a command to the server",
			Options: []*discordgo.ApplicationCommandOption{
				{
					Type:        discordgo.ApplicationCommandOptionString,
					Name:        "command",
					Description: "The command to run",
					Required:    true,
				},
			},
		},
	}

	commandHandlers = map[string]func(b *Bot, i *discordgo.InteractionCreate){
		"help": func(b *Bot, i *discordgo.InteractionCreate) {
			listing := ""
			for _, v := range commands {
				listing += fmt.Sprintf("- %s: %s\n", v.Name, v.Description)
			}

			b.session.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
				Type: discordgo.InteractionResponseChannelMessageWithSource,
				Data: &discordgo.InteractionResponseData{
					Embeds: []*discordgo.MessageEmbed{
						{
							Title:       "Commands",
							Description: listing,
							Color:       colorBlurple,
						},
					},
				},
			})
		},

		"info": func(b *Bot, i *discordgo.InteractionCreate) {
			reader, err := os.Open(b.config.Manifest)
			if err != nil {
				sendError(b, i, "info, os.Open manifest", err)
				return
			}

			var description string
			description += fmt.Sprintf("Connect at `%s:%d`\n",
				b.config.Address,
				b.config.Port,
			)

			if b.config.IsWhitelist {
				description += "The server is using a whitelist.\n"
			}

			if b.config.HasDynmap {
				description += fmt.Sprintf(
					"The server has dynmap available at: http://%s:%d/\n",
					b.config.Address,
					b.config.Port+3,
				)
			}

			description += "\n> .mrpack for import into your preferred launcher is attached above.\n"
			description += "> Confused? See here: https://youtu.be/EqenOITGvis"

			b.session.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
				Type: discordgo.InteractionResponseChannelMessageWithSource,
				Data: &discordgo.InteractionResponseData{
					Files: []*discordgo.File{
						{
							Name:        b.config.Manifest,
							ContentType: "mrpack",
							Reader:      reader,
						},
					},
					Embeds: []*discordgo.MessageEmbed{
						{
							Title:       "Server Info",
							Description: description,
							Color:       colorBlurple,
						},
					},
				},
			})
		},

		"list": func(b *Bot, i *discordgo.InteractionCreate) {
			var listing string
			if b.state.CurrentPlayerCount != 0 {
				listing = "- " + strings.Join(b.state.Players, "\n- ")
			} else {
				listing = "There are no players online."
			}

			b.session.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
				Type: discordgo.InteractionResponseChannelMessageWithSource,
				Data: &discordgo.InteractionResponseData{
					Embeds: []*discordgo.MessageEmbed{
						{
							Title: fmt.Sprintf(
								"Players (%d/%d)",
								b.state.CurrentPlayerCount,
								b.state.MaxPlayers,
							),
							Description: listing,
							Color:       colorBlurple,
						},
					},
				},
			})
		},

		"rcon": func(b *Bot, i *discordgo.InteractionCreate) {
			uid, _ := strconv.Atoi(i.User.ID)
			if !slices.Contains(b.config.RconUsers, uid) {
				sendError(b, i, "rcon command", errors.New("action not permitted"))
				return
			}

			options := i.ApplicationCommandData().Options

			response, err := b.sendRcon(options[0].StringValue())
			if err != nil {
				sendError(b, i, "rcon command", err)
				return
			}

			if response == "" {
				response = "*Success; no response*"
			}

			b.session.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
				Type: discordgo.InteractionResponseChannelMessageWithSource,
				Data: &discordgo.InteractionResponseData{
					Embeds: []*discordgo.MessageEmbed{
						{
							Title:       "rcon response",
							Description: response,
							Color:       colorBlurple,
						},
					},
				},
			})
		},
	}
)
