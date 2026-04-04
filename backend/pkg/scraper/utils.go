package scraper

import (
	"fmt"
	"scraper/pkg/database"
	"scraper/pkg/models"
)

// DeduplicateScreenings removes duplicate screenings based on movie, cinema, date, time, and language
func DeduplicateScreenings(screenings []models.ScrapedScreening) []models.ScrapedScreening {
	seen := make(map[string]bool)
	var unique []models.ScrapedScreening

	for _, s := range screenings {
		// Create a unique key for each screening
		// We need to get the movie title for deduplication
		// Since we don't have it in ScrapedScreening, we'll need to look it up
		var movie database.Movie
		result := database.DB.Where("id = ?", s.MovieID).First(&movie)
		if result.Error != nil {
			// If we can't find the movie, skip this screening
			continue
		}

		key := fmt.Sprintf("%s|%d|%s|%s|%s",
			movie.Title,
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
