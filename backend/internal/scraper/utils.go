package scraper

import (
	"fmt"

	"scraper/internal/shared/models"
)

// DeduplicateScreenings removes duplicate screenings based on movie, cinema, date, time, and language
func DeduplicateScreenings(screenings interface{}) interface{} {
	seen := make(map[string]bool)

	switch v := screenings.(type) {
	case []models.ScrapedScreening:
		var unique []models.ScrapedScreening
		for _, s := range v {
			// Create a unique key for each screening
			key := fmt.Sprintf("%s|%s|%s|%s|%s",
				s.MovieTitle,
				s.CinemaName,
				s.Date.Format("2006-01-02"),
				s.Time,
				s.Language)

			if !seen[key] {
				seen[key] = true
				unique = append(unique, s)
			}
		}
		return unique

	case []models.ScrapedScreeningWithTMDB:
		var unique []models.ScrapedScreeningWithTMDB
		for _, s := range v {
			// Create a unique key for each screening
			key := fmt.Sprintf("%s|%s|%s|%s|%s",
				s.MovieTitle,
				s.CinemaName,
				s.Date.Format("2006-01-02"),
				s.Time,
				s.Language)

			if !seen[key] {
				seen[key] = true
				unique = append(unique, s)
			}
		}
		return unique

	default:
		return screenings
	}
}
