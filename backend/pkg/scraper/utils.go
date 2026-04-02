package scraper

import (
	"fmt"
	"scraper/pkg/models"
)

// DeduplicateScreenings removes duplicate screenings based on movie, cinema, date, time, and language
func DeduplicateScreenings(screenings []models.Screening) []models.Screening {
	seen := make(map[string]bool)
	var unique []models.Screening

	for _, s := range screenings {
		// Create a unique key for each screening
		key := fmt.Sprintf("%s|%s|%s|%s|%s",
			s.Movie.Title,
			s.Cinema.Name,
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
