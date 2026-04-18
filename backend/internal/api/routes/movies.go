package routes

import (
	"encoding/json"
	"fmt"
	"net/http"

	"scraper/internal/shared/database"
)

// Screening represents a movie screening with date, time, language, and cinema information
// used in the API response
type Screening struct {
	Date     string `json:"date"`
	Time     string `json:"time"`
	Language string `json:"language"`
	Cinema   string `json:"cinema"`
	URL      string `json:"url"`
}

// Movie represents a movie with its associated screenings
// used in the API response
type Movie struct {
	ScrapedTitle  string      `json:"scraped_title"`  // Title scraped from cinema websites
	SpanishTitle  *string     `json:"spanish_title"`  // Spanish title from TMDB
	OriginalTitle *string     `json:"original_title"` // Original title from TMDB
	Duration      *int        `json:"duration"`       // Duration in minutes, nullable
	Overview      *string     `json:"overview"`
	PosterPath    *string     `json:"poster_path"`
	BackdropPath  *string     `json:"backdrop_path"`
	VoteAverage   *float64    `json:"vote_average"`
	Screenings    []Screening `json:"screenings"`
}

// MoviesHandler handles HTTP requests to the /api/movies endpoint
// and returns a JSON response with all movies and their screenings
func MoviesHandler(w http.ResponseWriter, _ *http.Request) {
	// Set CORS headers
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "GET")

	// Get movies from service
	movies, err := database.GetAllMoviesWithScreenings()
	if err != nil {
		http.Error(w, fmt.Sprintf("Failed to get movies: %v", err), http.StatusInternalServerError)
		return
	}

	// Convert to API response format
	var responseMovies []Movie
	for _, movie := range movies {
		// Convert screenings
		var screenings []Screening
		for _, screening := range movie.Screenings {
			screenings = append(screenings, Screening{
				Date:     screening.Date.Format("2006-01-02"),
				Time:     screening.Time,
				Language: screening.Language,
				Cinema:   screening.Cinema,
				URL:      screening.URL,
			})
		}

		responseMovies = append(responseMovies, Movie{
			ScrapedTitle:  movie.ScrapedTitle,
			SpanishTitle:  movie.SpanishTitle,
			OriginalTitle: movie.OriginalTitle,
			Duration:      movie.Duration,
			Overview:      movie.Overview,
			PosterPath:    movie.PosterPath,
			BackdropPath:  movie.BackdropPath,
			VoteAverage:   movie.VoteAverage,
			Screenings:    screenings,
		})
	}

	// Return JSON response
	if err := json.NewEncoder(w).Encode(responseMovies); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}
