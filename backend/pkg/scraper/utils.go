package scraper

import (
	"fmt"
	"scraper/pkg/models"
)

// DeduplicateScreenings removes duplicate screenings based on movie, cinema, date, time, and language
func DeduplicateScreenings(screenings []models.ScrapedScreening) []models.ScrapedScreening {
	seen := make(map[string]bool)
	var unique []models.ScrapedScreening

	for _, s := range screenings {
		// Create a unique key for each screening
		// Note: We use CinemaID instead of CinemaName since that's what we have
		key := fmt.Sprintf("%s|%d|%s|%s|%s",
			s.MovieTitle,
			s.CinemaID,
			s.Date.Format("2006-01-02"),
			s.Time,
			s.Language)

		if !seen[key] {
			seen[key] = true
			unique = append(unique, s)
		}
	}

	return unique
}
