package main

import (
	"flag"
	"fmt"

	"scraper/logger"
	"scraper/pkg/scraper"
)

func main() {
	// Parse command line flags for log level
	logLevel := flag.String("log-level", "info", "Log level (debug, info, warn, error, fatal)")
	flag.Parse()

	// Create logger with specified level
	level := logger.ParseLogLevel(*logLevel)
	log := logger.NewLogger(level)
	log.Info("🚀 Starting Multicines scraper with log level: %s", level)

	// Create scraper with logger
	scraperInstance, cancel := scraper.NewScraper(log)
	defer cancel()

	// Run the scraper
	screenings, err := scraperInstance.ScrapeMulticines()
	if err != nil {
		log.Fatal("Scraping failed: %v", err)
	}

	// Remove duplicate screenings
	screenings = scraper.DeduplicateScreenings(screenings)

	log.Info("✅ Scraping completed!")
	log.Info("📊 Total screenings (after deduplication): %d", len(screenings))

	log.Info("\n📋 Scraped Screenings:")
	for _, s := range screenings {
		fmt.Printf("🎬 %s at %s (%s): %s on %s\n",
			s.Movie.Title, s.Cinema.Name, s.Language, s.Time, s.Date.Format("2006-01-02"))
	}
}
