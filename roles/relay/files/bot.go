package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"slices"
	"strconv"
	"strings"
	"time"

	"github.com/bwmarrin/discordgo"
	"github.com/icza/backscanner"
	"github.com/jltobler/go-rcon"
	"github.com/jonas747/dshardmanager"
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

	return bot, bot.Start()
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
	s.ApplicationCommandBulkOverwrite(s.State.User.ID, "", commands)
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

	go b.pollStatusLoop()
	go b.pollMinecraftLogsLoop()
}

func (b *Bot) Close() {
	b.StopAll()
}

func (b *Bot) sendRcon(command string) (response string, err error) {
	res, err := b.rconClient.Send(command)
	return res, err
}

func (b *Bot) systemMessage(message string) {
	b.session.ChannelMessageSendEmbed(
		b.config.Channel,
		&discordgo.MessageEmbed{
			Author: &discordgo.MessageEmbedAuthor{
				Name:    "System Message",
				IconURL: b.session.State.User.AvatarURL(""),
			},
			Description: message,
			Color:       0xFF00FF,
		},
	)
}

func (b *Bot) getPlayerAvatar(username string) (url string, err error) {
	if !serverPlayerNameRe.MatchString(username) {
		return "", errors.New("invalid name")
	}

	// cached: return it
	url, ok := b.state.AvatarURLCache[username]
	if ok {
		fmt.Println("cached")
		return url, nil
	}

	// not cached: grab it
	requestUrl := fmt.Sprintf("https://playerdb.co/api/player/minecraft/%s", username)

	req, err := http.NewRequest("GET", requestUrl, nil)
	if err != nil {
		return "", errors.New("failed to generate request")
	}
	req.Header.Add("User-Agent", "github.com/jack-avery/fmcs-server")

	client := &http.Client{}
	response, err := client.Do(req)
	if err != nil {
		return "", errors.New("failed to complete avatar request")
	}

	responseData, err := io.ReadAll(response.Body)
	if err != nil {
		return "", errors.New("failed to parse response body")
	}

	var playerData PlayerDBResponse
	json.Unmarshal(responseData, &playerData)

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
		b.session.UpdateWatchStatus(0, "for server restart...")
		b.state.ServerIsOnline = false
		return
	}

	if !b.state.ServerIsOnline {
		b.state.ServerIsOnline = true
		b.systemMessage("Server is ready.")
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
	b.session.UpdateGameStatus(0, status)
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

		b.session.ChannelMessageSendEmbed(
			b.config.Channel,
			&discordgo.MessageEmbed{
				Title: fmt.Sprintf(":sunrise_over_mountains: Dawn of the %s day", date_text),
				Color: 0xF1C40F,
			},
		)
	}
}

func (b *Bot) pollStatusLoop() {
	for {
		b.updateStatus()

		if b.config.RelayDates {
			b.updateDate()
		}

		time.Sleep(10 * time.Second)
	}
}

func (b *Bot) pollMinecraftLogsLoop() {
	var last_line []byte
	var last_line_new []byte
	pollRate := time.Second * time.Duration(b.config.PollRate)

	// grab first line
	for {
		file, err := os.Open("logs/latest.log")
		if err != nil {
			log.Println("failed to open latest.log: ", err)
			time.Sleep(pollRate)
			continue
		}

		fileStat, err := file.Stat()
		if err != nil {
			log.Println("failed to stat latest.log: ", err)
			time.Sleep(pollRate)
			continue
		}

		scanner := backscanner.New(file, int(fileStat.Size()))
		scanner.LineBytes() // discard first, otherwise byte array is empty (does logfile use CRLF??)
		line, _, err := scanner.LineBytes()
		if err != nil {
			if err == io.EOF {
				log.Println("retrying fetching first last_line: reached EOF?")
				time.Sleep(pollRate)
				continue
			} else {
				log.Println("failed to read last line: ", err)
				time.Sleep(pollRate)
				continue
			}
		}
		last_line = line
		break
	}

	for {
		file, err := os.Open("logs/latest.log")
		if err != nil {
			log.Println("failed to open latest.log: ", err)
			time.Sleep(pollRate)
			continue
		}

		fileStat, err := file.Stat()
		if err != nil {
			log.Println("failed to stat latest.log: ", err)
			time.Sleep(pollRate)
			continue
		}

		scanner := backscanner.New(file, int(fileStat.Size()))
		lines := make([]string, 0, 10)
		i := 0
		for {
			line, _, err := scanner.LineBytes()
			if err != nil {
				if err == io.EOF {
					log.Println("reached EOF while reading logs")
					break
				} else {
					log.Println("failed to read last line: ", err)
					time.Sleep(pollRate)
					break
				}
			}

			if i == 1 {
				last_line_new = line
			}

			if string(line) == string(last_line) {
				break
			}

			// grow slice if we're at capacity
			i += 1
			if i == cap(lines) {
				lines = slices.Grow(lines, int(cap(lines)/2))
			}

			lines = append(lines, string(line))
		}

		// nothing new, sit and wait
		if len(lines) == 0 {
			time.Sleep(pollRate)
			continue
		}

		last_line = last_line_new
		slices.Reverse(lines)

		for i := range lines {
			raw := lines[i]

			if !serverInfoRe.MatchString(raw) {
				continue
			}

			if results := serverSystemMessageRe.FindStringSubmatch(raw); results != nil {
				msg := results[1]
				b.systemMessage(msg)
				continue
			}

			if b.config.RelayMessages {
				if results := serverMessageRe.FindStringSubmatch(raw); results != nil {
					user := results[1]
					msg := results[2]
					avatar, _ := b.getPlayerAvatar(user)

					// is this enugh? it should stop @ing...
					msg = strings.ReplaceAll(msg, "@", "＠")
					msg = strings.ReplaceAll(msg, "\"", "'")

					b.session.WebhookExecute(
						b.state.Webhook.ID,
						b.state.Webhook.Token,
						false,
						&discordgo.WebhookParams{
							Username:  user,
							Content:   msg,
							AvatarURL: avatar,
						},
					)
					continue
				}

				if results := serverActionRe.FindStringSubmatch(raw); results != nil {
					user := results[1]
					avatar, _ := b.getPlayerAvatar(user)

					// is this enugh? it should stop @ing...
					msg := strings.ReplaceAll(results[0], "@", "＠")
					msg = strings.ReplaceAll(msg, "\"", "'")

					b.session.ChannelMessageSendEmbed(
						b.config.Channel,
						&discordgo.MessageEmbed{
							Author: &discordgo.MessageEmbedAuthor{
								Name:    msg,
								IconURL: avatar,
							},
							Color: 0x444444,
						},
					)
					continue
				}
			}

			if b.config.RelayConnections {
				if results := serverJoinRe.FindStringSubmatch(raw); results != nil {
					avatar, _ := b.getPlayerAvatar(results[1])

					b.session.ChannelMessageSendEmbed(
						b.config.Channel,
						&discordgo.MessageEmbed{
							Author: &discordgo.MessageEmbedAuthor{
								Name:    fmt.Sprintf("📥 %s", results[0]),
								IconURL: avatar,
							},
							Color: 0x00FF00,
						},
					)
					continue
				}

				if results := serverLeaveRe.FindStringSubmatch(raw); results != nil {
					avatar, _ := b.getPlayerAvatar(results[1])

					b.session.ChannelMessageSendEmbed(
						b.config.Channel,
						&discordgo.MessageEmbed{
							Author: &discordgo.MessageEmbedAuthor{
								Name:    fmt.Sprintf("📤 %s", results[0]),
								IconURL: avatar,
							},
							Color: 0xFF0000,
						},
					)
					continue
				}
			}

			if b.config.RelayAdvancements {
				if results := serverAdvancementRe.FindStringSubmatch(raw); results != nil {
					avatar, _ := b.getPlayerAvatar(results[1])

					b.session.ChannelMessageSendEmbed(
						b.config.Channel,
						&discordgo.MessageEmbed{
							Author: &discordgo.MessageEmbedAuthor{
								Name:    fmt.Sprintf("📖 %s", results[0]),
								IconURL: avatar,
							},
							Color: 0x8888FF,
						},
					)
					continue
				}

				if results := serverChallengeRe.FindStringSubmatch(raw); results != nil {
					avatar, _ := b.getPlayerAvatar(results[1])

					b.session.ChannelMessageSendEmbed(
						b.config.Channel,
						&discordgo.MessageEmbed{
							Author: &discordgo.MessageEmbedAuthor{
								Name:    fmt.Sprintf("🏆 %s", results[0]),
								IconURL: avatar,
							},
							Color: 0xF1C40F,
						},
					)
					continue
				}
			}

			if b.config.RelayDeaths {
				for i := range deathMessagesRe {
					if results := deathMessagesRe[i].FindStringSubmatch(raw); results != nil {
						user := results[1]
						avatar, _ := b.getPlayerAvatar(user)

						b.session.ChannelMessageSendEmbed(
							b.config.Channel,
							&discordgo.MessageEmbed{
								Author: &discordgo.MessageEmbedAuthor{
									Name:    fmt.Sprintf("💀 %s", results[0]),
									IconURL: avatar,
								},
								Color: 0xAA0000,
							},
						)
						break
					}
				}
			}
		}

		time.Sleep(pollRate)
	}
}

func (b *Bot) onMessage(s *discordgo.Session, m *discordgo.MessageCreate) {
	if m.Message.Author.ID == s.State.User.ID ||
		!b.config.RelayMessages ||
		m.ChannelID != b.config.Channel ||
		m.Message.Author.Bot {
		return
	}

	msg := m.Message.Content

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

	b.sendRcon(
		fmt.Sprintf(`tellraw @a [{"text":"(Discord) ", "color":"blue"}, {"text":"%s", "color":"white"}]`, msg),
	)
}
