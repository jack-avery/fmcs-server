package main

import (
	"fmt"
	"os"

	yaml "gopkg.in/yaml.v2"
)

// Config is configuration of Bot
type Config struct {
	Token             string `yaml:"token"`
	Address           string `yaml:"address"`
	Port              int    `yaml:"port"`
	RconPass          string `yaml:"rcon_pass"`
	RconAddress       string
	Channel           string `yaml:"channel"`
	Manifest          string `yaml:"atl_manifest"`
	IsWhitelist       bool   `yaml:"is_whitelist"`
	RelayMessages     bool   `yaml:"relay_messages"`
	RelayDeaths       bool   `yaml:"relay_deaths"`
	RelayAdvancements bool   `yaml:"relay_advancements"`
	RelayConnections  bool   `yaml:"relay_connections"`
	RelayDates        bool   `yaml:"relay_dates"`
	PollRate          int    `yaml:"poll_rate"`
	HasDynmap         bool   `yaml:"has_dynmap"`
	RconUsers         []int  `yaml:"rcon_users"`
}

func ParseConfig(fname string) (config *Config, err error) {
	b, err := os.ReadFile(fname)
	if err != nil {
		return nil, err
	}

	err = yaml.Unmarshal(b, &config)
	config.RconAddress = fmt.Sprintf("rcon://%s:%d", config.Address, config.Port+1)

	return config, err
}
