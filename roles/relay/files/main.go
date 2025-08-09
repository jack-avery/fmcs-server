package main

import (
	"context"
	"log"
	"os"
	"os/signal"
	"syscall"
)

func main() {
	ctx := context.Background()

	config, err := ParseConfig("config.yml")
	if err != nil {
		panic(err)
	}

	bot, err := NewBot(config)
	if err != nil {
		panic(err)
	}
	bot.Start(ctx)
	defer bot.Close()

	sc := make(chan os.Signal, 1)
	signal.Notify(sc, syscall.SIGINT, syscall.SIGTERM, os.Interrupt)
	<-sc

	log.Println("Exiting...")
}
