// Package config provides configuration management for the application
package config

import (
	"log"
	"os"
	"strconv"

	"github.com/joho/godotenv"
)

// Config holds application configuration
type Config struct {
	DatabasePath string
	APIAddress   string
	LogLevel     string
	Scraper      ScraperConfig
	TMDBService  TMDBServiceConfig
}

// ScraperConfig holds scraper-specific configuration
type ScraperConfig struct {
	Concurrency int
	Timeout     int
}

// TMDBServiceConfig holds TMDB service configuration.
type TMDBServiceConfig struct {
	APIKey string
}

// LoadConfig loads configuration from .env file and environment variables with sensible defaults
func LoadConfig() *Config {
	// Load .env file from the current directory
	err := godotenv.Load()
	if err != nil {
		log.Printf("⚠️  No .env file found or error loading: %v", err)
		log.Println("📋 Using environment variables and defaults")
	}

	config := &Config{
		DatabasePath: getEnv("DATABASE_PATH", "cine-uio.db"),
		APIAddress:   getEnv("API_ADDRESS", ":8080"),
		LogLevel:     getEnv("LOG_LEVEL", "info"),
		Scraper: ScraperConfig{
			Concurrency: getEnvInt("SCRAPER_CONCURRENCY", 1),
			Timeout:     getEnvInt("SCRAPER_TIMEOUT", 30),
		},
		TMDBService: TMDBServiceConfig{
			APIKey: getEnv("TMDB_API_KEY", ""),
		},
	}

	log.Printf("📋 Configuration loaded: Database=%s, API=%s, LogLevel=%s",
		config.DatabasePath, config.APIAddress, config.LogLevel)

	return config
}

// getEnv gets an environment variable or returns a default value
func getEnv(key, defaultValue string) string {
	if value, exists := os.LookupEnv(key); exists {
		return value
	}
	return defaultValue
}

// getEnvInt gets an environment variable as integer or returns a default value
func getEnvInt(key string, defaultValue int) int {
	if value, exists := os.LookupEnv(key); exists {
		if intValue, err := strconv.Atoi(value); err == nil {
			return intValue
		}
	}
	return defaultValue
}
