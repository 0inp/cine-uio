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
	URL        string    // Actual URL to the cinema website for this screening
}

// ScrapedScreeningWithTMDB extends ScrapedScreening with TMDB data
type ScrapedScreeningWithTMDB struct {
	ScrapedScreening
	TMDBDetails *MovieDetails // TMDB data including duration
}

// MovieDetails represents the response structure from TMDB movie details endpoint
type MovieDetails struct {
	Title         string  `json:"title"` // Spanish title when language=es-ES
	OriginalTitle string  `json:"original_title"`
	Runtime       int     `json:"runtime"` // Duration in minutes
	Overview      string  `json:"overview"`
	PosterPath    string  `json:"poster_path"`
	BackdropPath  string  `json:"backdrop_path"`
	ReleaseDate   string  `json:"release_date"`
	VoteAverage   float64 `json:"vote_average"`
}

// TMDBConfiguration represents the response structure from TMDB configuration endpoint
type TMDBConfiguration struct {
	Images struct {
		BaseURL       string   `json:"base_url"`
		SecureBaseURL string   `json:"secure_base_url"`
		BackdropSizes []string `json:"backdrop_sizes"`
		PosterSizes   []string `json:"poster_sizes"`
	} `json:"images"`
}

// TMDBConfigCache represents cached TMDB configuration with expiry
type TMDBConfigCache struct {
	Config       *TMDBConfiguration
	LastFetched  time.Time
	ExpiresAfter time.Duration
}
