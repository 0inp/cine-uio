package models

import "time"

// ScrapedScreening represents a screening found during scraping
// This is a simple DTO (Data Transfer Object) for the scraper
type ScrapedScreening struct {
	MovieTitle string    // Title of the movie (for lookup/creation)
	CinemaName string    // Name of the cinema (for lookup)
	Date       time.Time // Date of the screening
	Time       string    // Time of the screening
	Language   string    // Language of the screening
}
