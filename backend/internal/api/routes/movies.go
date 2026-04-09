package routes

import (
	"database/sql"
	"encoding/json"
	"log"
	"net/http"

	// SQLite driver import for database/sql
	_ "github.com/mattn/go-sqlite3"
)

// Screening represents a movie screening with date, time, language, and cinema information
// used in the API response
type Screening struct {
	Date     string `json:"date"`
	Time     string `json:"time"`
	Language string `json:"language"`
	Cinema   string `json:"cinema"`
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
	// Open database connection
	db, err := sql.Open("sqlite3", "./cine-uio.db")
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer func() {
		if err := db.Close(); err != nil {
			log.Printf("Error closing database: %v", err)
		}
	}()

	// Query to get movies with their screening times, cinema info, and TMDB data
	query := `
		SELECT m.scraped_title, m.spanish_title, m.duration, m.overview, m.poster_path, m.backdrop_path,
		       m.original_title, m.vote_average, st.date, st.time, st.language, c.name as cinema_name
		FROM movies m
		JOIN screening_times st ON m.id = st.movie_id
		JOIN cinemas c ON st.cinema_id = c.id
		ORDER BY m.scraped_title, st.date, st.time
	`

	rows, err := db.Query(query)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer func() {
		if err := rows.Close(); err != nil {
			log.Printf("Error closing rows: %v", err)
		}
	}()

	// Group screenings by movie
	moviesMap := make(map[string]*Movie)
	for rows.Next() {
		var scrapedTitle, date, time, language, cinemaName string
		var spanishTitle sql.NullString
		var duration sql.NullInt32
		var overview sql.NullString
		var posterPath sql.NullString
		var backdropPath sql.NullString
		var originalTitle sql.NullString
		var voteAverage sql.NullFloat64
		if err := rows.Scan(&scrapedTitle, &spanishTitle, &duration, &overview, &posterPath, &backdropPath, &originalTitle, &voteAverage, &date, &time, &language, &cinemaName); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		if _, exists := moviesMap[scrapedTitle]; !exists {
			var durationPtr *int
			if duration.Valid {
				durationValue := int(duration.Int32)
				durationPtr = &durationValue
			}

			var overviewPtr *string
			if overview.Valid {
				overviewPtr = &overview.String
			}

			var posterPathPtr *string
			if posterPath.Valid {
				posterPathPtr = &posterPath.String
			}

			var backdropPathPtr *string
			if backdropPath.Valid {
				backdropPathPtr = &backdropPath.String
			}

			var spanishTitlePtr *string
			if spanishTitle.Valid {
				spanishTitlePtr = &spanishTitle.String
			}

			var originalTitlePtr *string
			if originalTitle.Valid {
				originalTitlePtr = &originalTitle.String
			}

			var voteAveragePtr *float64
			if voteAverage.Valid {
				voteAvgValue := voteAverage.Float64
				voteAveragePtr = &voteAvgValue
			}

			moviesMap[scrapedTitle] = &Movie{
				ScrapedTitle:  scrapedTitle,
				SpanishTitle:  spanishTitlePtr,
				OriginalTitle: originalTitlePtr,
				Duration:      durationPtr,
				Overview:      overviewPtr,
				PosterPath:    posterPathPtr,
				BackdropPath:  backdropPathPtr,
				VoteAverage:   voteAveragePtr,
			}
		}
		moviesMap[scrapedTitle].Screenings = append(moviesMap[scrapedTitle].Screenings, Screening{
			Date:     date,
			Time:     time,
			Language: language,
			Cinema:   cinemaName,
		})
	}

	// Convert map to slice
	movies := make([]Movie, 0, len(moviesMap))
	for _, movie := range moviesMap {
		movies = append(movies, *movie)
	}

	// Set CORS headers
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "GET")

	// Return JSON response
	if err := json.NewEncoder(w).Encode(movies); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}
