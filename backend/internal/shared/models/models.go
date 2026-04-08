// Package models contains data transfer objects and models used throughout the application.
package models

import "time"

// ScrapedScreening represents a screening found during scraping
// This is a simple DTO (Data Transfer Object) for the scraper
type ScrapedScreening struct {
	MovieTitle string    // Title of the movie (for lookup/creation)
	CinemaName string    // Name of the cinema (for lookup)
	StoreID    string    // Store ID for the cinema
	Date       time.Time // Date of the screening
	Time       string    // Time of the screening
	Language   string    // Language of the screening
}

// ScrapedScreeningWithTMDB extends ScrapedScreening with TMDB data
type ScrapedScreeningWithTMDB struct {
	ScrapedScreening
	TMDBDetails *MovieDetails // TMDB data including duration
}

// MovieDetails represents the response structure from TMDB movie details endpoint
type MovieDetails struct {
	Title         string  `json:"title"`
	OriginalTitle string  `json:"original_title"`
	Runtime       int     `json:"runtime"` // Duration in minutes
	Overview      string  `json:"overview"`
	PosterPath    string  `json:"poster_path"`
	ReleaseDate   string  `json:"release_date"`
	VoteAverage   float64 `json:"vote_average"`
}
