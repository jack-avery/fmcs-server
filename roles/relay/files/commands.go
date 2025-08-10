package main

import (
	"errors"
	"fmt"
	"log"
	"os"
	"slices"
	"strconv"
	"strings"

	"github.com/bwmarrin/discordgo"
)

func sendError(b *Bot, i *discordgo.InteractionCreate, context string, e error) {
	err := b.session.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
		Type: discordgo.InteractionResponseChannelMessageWithSource,
		Data: &discordgo.InteractionResponseData{
			Embeds: []*discordgo.MessageEmbed{
				{
					Title:       "Error",
					Description: fmt.Sprintf("Context: %s, Error: %s", context, e.Error()),
					Color:       colorError,
				},
			},
		},
	})
	if err != nil {
		log.Println("error sending error (", e, ") as response to interaction: ", err)
	}
}

var (
	colorBlurple = 0x7289da
	colorSystem  = 0xAD1456
	colorError   = 0xFF0000

	colorNewDay = 0xF1C40F

	colorAction      = 0x444444
	colorJoin        = 0x2ECC70
	colorLeave       = 0xE74D3C
	colorAdvancement = 0x1ABC9C
	colorChallenge   = 0xF1C40F
	colorDeath       = 0x992E22

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

			err := b.session.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
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
			if err != nil {
				log.Println("error responding to /help: ", err)
			}
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

			err = b.session.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
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
			if err != nil {
				log.Println("error responding to /info: ", err)
			}
		},

		"list": func(b *Bot, i *discordgo.InteractionCreate) {
			var listing string
			if b.state.CurrentPlayerCount != 0 {
				listing = "- " + strings.Join(b.state.Players, "\n- ")
			} else {
				listing = "There are no players online."
			}

			err := b.session.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
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
			if err != nil {
				log.Println("error responding to /list: ", err)
			}
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

			err = b.session.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
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
			if err != nil {
				log.Println("error responding to /rcon: ", err)
			}
		},
	}
)
