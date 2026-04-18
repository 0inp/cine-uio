// Package main contains the API server for the cine-uio application
package main

import (
	"log"

	"scraper/internal/api"
	"scraper/internal/shared/config"
)

func main() {
	// Load configuration
	cfg := config.LoadConfig()

	// Create and start API server
	server, err := api.NewServer(cfg.APIAddress, cfg)
	if err != nil {
		log.Fatalf("Failed to create server: %v", err)
	}
	if err := server.Start(); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
