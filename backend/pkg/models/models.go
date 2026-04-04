package models

import "time"

// ScrapedScreening represents a screening found during scraping
// This is a simple DTO (Data Transfer Object) for the scraper
type ScrapedScreening struct {
	MovieID  uint      // ID of the movie (already looked up/created)
	CinemaID uint      // ID of the cinema (we already have this)
	Date     time.Time // Date of the screening
	Time     string    // Time of the screening
	Language string    // Language of the screening
}
