package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/bwmarrin/discordgo"
	"github.com/jltobler/go-rcon"
	"github.com/jonas747/dshardmanager"
	"github.com/nxadm/tail"
)

type Bot struct {
	dshardmanager.Manager
	config     *Config
	rconClient *rcon.Client
	session    *discordgo.Session
	state      State
}

// Create a new Bot using config.
func NewBot(config *Config) (bot *Bot, err error) {
	bot = &Bot{
		Manager:    *dshardmanager.New("Bot " + config.Token),
		config:     config,
		rconClient: rcon.NewClient(config.RconAddress, config.RconPass),
		session:    nil,
		state:      NewState(),
	}

	bot.AddHandler(bot.ready)
	bot.AddHandler(bot.onMessage)

	return bot, nil
}

func (b *Bot) Start(ctx context.Context) {
	err := b.Manager.Start()
	if err != nil {
		panic(err)
	}

	go b.pollStatusLoop(ctx)
	go b.pollMinecraftLogsLoop(ctx)
}

func (b *Bot) ready(s *discordgo.Session, event *discordgo.Ready) {
	log.Println("Connected!")

	b.session = s
	s.Identify.Intents = discordgo.IntentMessageContent |
		discordgo.IntentGuildMessages |
		discordgo.IntentDirectMessages |
		discordgo.IntentGuildWebhooks |
		discordgo.IntentGuilds

	s.AddHandler(func(_ *discordgo.Session, i *discordgo.InteractionCreate) {
		if h, ok := commandHandlers[i.ApplicationCommandData().Name]; ok {
			h(b, i)
		}
	})
	_, err := s.ApplicationCommandBulkOverwrite(s.State.User.ID, "", commands)
	if err != nil {
		panic("failed to apply commands")
	}
	log.Println("Applied commands")

	webhooks, err := s.ChannelWebhooks(b.config.Channel)
	if err != nil {
		panic(
			"Could not fetch webhooks for channel: " + err.Error() + "! Cannot continue")
	} else {
		for _, w := range webhooks {
			if w.Name == "fmcs-server" {
				b.state.Webhook = w
			}
		}

		if b.state.Webhook == nil {
			w, err := s.WebhookCreate(b.config.Channel, "fmcs-server", "")
			if err != nil {
				panic(
					"Could not find a webhook named 'fmcs-server' in the channel" +
						"(or create it: " + err.Error() + ")! Cannot continue")
			}

			b.state.Webhook = w
		}
	}
	log.Println("Acquired webhook")

	log.Println("Ready!")
}

func (b *Bot) Close() (err error) {
	return b.StopAll()
}

func (b *Bot) sendRcon(command string) (response string, err error) {
	res, err := b.rconClient.Send(command)
	return res, err
}

func (b *Bot) sendSystemMessage(message string) {
	_, err := b.session.ChannelMessageSendEmbed(
		b.config.Channel,
		&discordgo.MessageEmbed{
			Author: &discordgo.MessageEmbedAuthor{
				Name:    "System Message",
				IconURL: b.session.State.User.AvatarURL(""),
			},
			Description: message,
			Color:       colorSystem,
		},
	)
	if err != nil {
		log.Println("failed to send system message: ", err)
	}
}

func (b *Bot) getPlayerAvatar(ctx context.Context, username string) (url string, err error) {
	if !serverPlayerNameRe.MatchString(username) {
		return "", errors.New("invalid name")
	}

	// cached: return it
	url, ok := b.state.AvatarURLCache[username]
	if ok {
		return url, nil
	}

	// not cached: grab it
	requestUrl := fmt.Sprintf("https://playerdb.co/api/player/minecraft/%s", username)

	childCtx, cancel := context.WithTimeout(ctx, time.Second*10)
	defer cancel()

	req, err := http.NewRequestWithContext(childCtx, "GET", requestUrl, nil)
	if err != nil {
		return "", errors.New("failed to generate request")
	}
	req.Header.Add("User-Agent", "github.com/jack-avery/fmcs-server")

	client := &http.Client{}
	response, err := client.Do(req)
	if err != nil {
		return "", err
	}
	defer response.Body.Close()

	var playerData PlayerDBResponse
	if errDecode :=
		json.NewDecoder(response.Body).Decode(&playerData); errDecode != nil {
		return "", errDecode
	}

	if playerData.Code != "player.found" {
		return "", errors.New("player not found")
	}

	url = playerData.Data.Player.Avatar
	b.state.AvatarURLCache[username] = url
	return url, nil
}

func (b *Bot) updateStatus() {
	playerList, err := b.sendRcon("list")

	// assume server is offline
	if err != nil {
		err = b.session.UpdateWatchStatus(0, "for server restart...")
		if err != nil {
			log.Println("failed to update status: ", err)
		}
		b.state.ServerIsOnline = false
		return
	}

	if !b.state.ServerIsOnline {
		b.state.ServerIsOnline = true
		b.sendSystemMessage("Server is ready.")
	}

	// update player list
	result := serverListRe.FindStringSubmatch(playerList)
	players_current, _ := strconv.Atoi(result[1])
	players_maximum, _ := strconv.Atoi(result[2])
	players := []string{}
	if len(result) > 3 {
		players = result[3:]
	}

	b.state.Players = players
	b.state.MaxPlayers = players_maximum
	b.state.CurrentPlayerCount = players_current

	status := fmt.Sprintf("with %d player", players_current)
	if players_current != 1 {
		status += "s"
	}
	err = b.session.UpdateGameStatus(0, status)
	if err != nil {
		log.Println("failed to update status: ", err)
	}
}

func (b *Bot) updateDate() {
	dateQuery, err := b.sendRcon("time query day")

	// silently fail
	if err != nil {
		return
	}

	result := serverTimeRe.FindStringSubmatch(dateQuery)
	date, _ := strconv.Atoi(result[1])

	// not tracking yet
	if b.state.Day == -1 {
		b.state.Day = date
		return
	}

	if b.state.Day < date {
		b.state.Day = date

		// make the date look fancy
		date := strconv.Itoa(date)

		// stage 1: reverse once
		var s1 string
		for _, v := range date {
			s1 = string(v) + s1
		}

		// stage 2: reverse again, adding commas
		var date_text string
		for i, v := range s1 {
			if i != 0 && i%3 == 0 {
				date_text = "," + date_text
			}
			date_text = string(v) + date_text
		}

		if len(date) > 1 && date_text[len(date_text)-2] == '1' {
			date_text += "th"
		} else {
			switch date_text[:len(date_text)-1] {
			case "1":
				date_text += "st"
			case "2":
				date_text += "nd"
			case "3":
				date_text += "rd"
			default:
				date_text += "th"
			}
		}

		_, err = b.session.ChannelMessageSendEmbed(
			b.config.Channel,
			&discordgo.MessageEmbed{
				Title: fmt.Sprintf(":sunrise_over_mountains: Dawn of the %s day", date_text),
				Color: colorNewDay,
			},
		)
		if err != nil {
			log.Println("failed to announce new day: ", err)
		}
	}
}

func (b *Bot) pollStatusLoop(ctx context.Context) {
	pollRate := time.Second * 10
	ticker := time.NewTicker(pollRate)

	for {
		select {
		case <-ticker.C:
			b.updateStatus()

			if b.config.RelayDates {
				b.updateDate()
			}
		case <-ctx.Done():
			return
		}
	}
}

func (b *Bot) pollMinecraftLogsLoop(ctx context.Context) {
	t, err := tail.TailFile(
		"logs/latest.log",
		tail.Config{
			Follow: true,
			ReOpen: true,
			Location: &tail.SeekInfo{
				Offset: 0,
				Whence: io.SeekEnd,
			},
		})
	if err != nil {
		panic("could not tail logfile: " + err.Error())
	}

	for {
		select {
		case line := <-t.Lines:
			raw := line.Text

			if !serverInfoRe.MatchString(raw) {
				continue
			}

			if results := serverSystemMessageRe.FindStringSubmatch(raw); results != nil {
				msg := results[1]
				b.sendSystemMessage(msg)
				continue
			}

			if b.config.RelayMessages {
				if results := serverMessageRe.FindStringSubmatch(raw); results != nil {
					user := results[1]
					msg := results[2]
					avatar, _ := b.getPlayerAvatar(ctx, user)

					// is this enugh? it should stop @ing...
					msg = strings.ReplaceAll(msg, "@", "＠")
					msg = strings.ReplaceAll(msg, "\"", "'")

					_, err = b.session.WebhookExecute(
						b.state.Webhook.ID,
						b.state.Webhook.Token,
						false,
						&discordgo.WebhookParams{
							Username:  user,
							Content:   msg,
							AvatarURL: avatar,
						},
					)
					if err != nil {
						log.Println("failed to relay message: ", err)
					}
					continue
				}

				if results := serverActionRe.FindStringSubmatch(raw); results != nil {
					user := results[1]
					avatar, _ := b.getPlayerAvatar(ctx, user)

					// is this enugh? it should stop @ing...
					msg := strings.ReplaceAll(results[0], "@", "＠")
					msg = strings.ReplaceAll(msg, "\"", "'")

					_, err = b.session.ChannelMessageSendEmbed(
						b.config.Channel,
						&discordgo.MessageEmbed{
							Author: &discordgo.MessageEmbedAuthor{
								Name:    msg,
								IconURL: avatar,
							},
							Color: colorAction,
						},
					)
					if err != nil {
						log.Println("failed to relay action: ", err)
					}
					continue
				}
			}

			if b.config.RelayConnections {
				if results := serverJoinRe.FindStringSubmatch(raw); results != nil {
					avatar, _ := b.getPlayerAvatar(ctx, results[1])

					_, err = b.session.ChannelMessageSendEmbed(
						b.config.Channel,
						&discordgo.MessageEmbed{
							Author: &discordgo.MessageEmbedAuthor{
								Name:    fmt.Sprintf("📥 %s", results[0]),
								IconURL: avatar,
							},
							Color: colorJoin,
						},
					)
					if err != nil {
						log.Println("failed to relay join: ", err)
					}
					continue
				}

				if results := serverLeaveRe.FindStringSubmatch(raw); results != nil {
					avatar, _ := b.getPlayerAvatar(ctx, results[1])

					_, err = b.session.ChannelMessageSendEmbed(
						b.config.Channel,
						&discordgo.MessageEmbed{
							Author: &discordgo.MessageEmbedAuthor{
								Name:    fmt.Sprintf("📤 %s", results[0]),
								IconURL: avatar,
							},
							Color: colorLeave,
						},
					)
					if err != nil {
						log.Println("failed to relay leave: ", err)
					}
					continue
				}
			}

			if b.config.RelayAdvancements {
				if results := serverAdvancementRe.FindStringSubmatch(raw); results != nil {
					avatar, _ := b.getPlayerAvatar(ctx, results[1])

					_, err := b.session.ChannelMessageSendEmbed(
						b.config.Channel,
						&discordgo.MessageEmbed{
							Author: &discordgo.MessageEmbedAuthor{
								Name:    fmt.Sprintf("📖 %s", results[0]),
								IconURL: avatar,
							},
							Color: colorAdvancement,
						},
					)
					if err != nil {
						log.Println("failed to relay advancement: ", err)
					}
					continue
				}

				if results := serverChallengeRe.FindStringSubmatch(raw); results != nil {
					avatar, _ := b.getPlayerAvatar(ctx, results[1])

					_, err := b.session.ChannelMessageSendEmbed(
						b.config.Channel,
						&discordgo.MessageEmbed{
							Author: &discordgo.MessageEmbedAuthor{
								Name:    fmt.Sprintf("🏆 %s", results[0]),
								IconURL: avatar,
							},
							Color: colorChallenge,
						},
					)
					if err != nil {
						log.Println("failed to relay challenge: ", err)
					}
					continue
				}
			}

			if b.config.RelayDeaths {
				for i := range deathMessagesRe {
					if results := deathMessagesRe[i].FindStringSubmatch(raw); results != nil {
						user := results[1]
						avatar, _ := b.getPlayerAvatar(ctx, user)

						_, err := b.session.ChannelMessageSendEmbed(
							b.config.Channel,
							&discordgo.MessageEmbed{
								Author: &discordgo.MessageEmbedAuthor{
									Name:    fmt.Sprintf("💀 %s", results[0]),
									IconURL: avatar,
								},
								Color: colorDeath,
							},
						)
						if err != nil {
							log.Println("failed to relay death: ", err)
						}
						break
					}
				}
			}
		case <-ctx.Done():
			t.Cleanup()
			return
		}
	}
}

func (b *Bot) onMessage(s *discordgo.Session, m *discordgo.MessageCreate) {
	if m.Author.ID == s.State.User.ID ||
		!b.config.RelayMessages ||
		m.ChannelID != b.config.Channel ||
		m.Author.Bot {
		return
	}

	msg := m.Content

	// prettify user/emote/channel mentions
	mentions := discordMentionRe.FindAllStringSubmatch(msg, -1)
	for i := 0; i < len(m.Mentions); i++ {
		msg = strings.ReplaceAll(
			msg,
			mentions[i][0],
			fmt.Sprintf("@%s", m.Mentions[i].DisplayName()),
		)
	}

	// we don't use m.MentionChannels since it doesn't seem to work?
	channels := discordChannelRe.FindAllStringSubmatch(msg, -1)
	for i := range channels {
		channel, err := s.Channel(channels[i][1])
		if err != nil {
			msg = strings.ReplaceAll(
				msg,
				channels[i][0],
				"#unknown-channel",
			)
			continue
		}
		msg = strings.ReplaceAll(
			msg,
			channels[i][0],
			fmt.Sprintf("#%s", channel.Name),
		)
	}

	emotes := discordEmoteRe.FindAllStringSubmatch(msg, -1)
	for i := range emotes {
		msg = strings.ReplaceAll(
			msg,
			emotes[i][0],
			emotes[i][1],
		)
	}

	var reply_note string
	if m.ReferencedMessage != nil {
		reply_note = fmt.Sprintf(
			" (replying to %s)",
			m.ReferencedMessage.Author.DisplayName(),
		)
	}

	// sanitization
	msg = strings.ReplaceAll(msg, `"`, `'`)
	msg = strings.ReplaceAll(msg, `\`, ``)
	control := []string{"\n", "\r", "\t", "\f"}
	for i := range control {
		msg = strings.ReplaceAll(msg, control[i], " ")
	}

	msg = fmt.Sprintf(
		"<%s%s> %s",
		m.Author.DisplayName(),
		reply_note,
		msg,
	)

	// shorten to fit it into a single message
	// max minecraft message length is 256;
	// " [...] (attachment)" (19) on max length 236+19=255
	if len(msg) > 242 {
		msg = msg[:235] + " [...]"
	}

	if len(m.Attachments) != 0 {
		msg += " (attachment)"
	}

	_, err := b.sendRcon(
		fmt.Sprintf(`tellraw @a [{"text":"(Discord) ", "color":"blue"}, {"text":"%s", "color":"white"}]`, msg),
	)
	if err != nil {
		b.sendSystemMessage("Failed to send your message: " + err.Error())
	}
}
