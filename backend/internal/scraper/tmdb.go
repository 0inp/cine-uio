package scraper

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/url"
	"os"

	"scraper/internal/shared/config"
	"scraper/internal/shared/models"
)

// TMDBService handles communication with The Movie Database API
type TMDBService struct {
	apiKey  string
	baseURL string
}

// NewTMDBService creates a new TMDB service instance
func NewTMDBService(cfg *config.Config) *TMDBService {
	apiKey := cfg.TMDBService.APIKey
	if apiKey == "" {
		// Fallback to environment variable if not in config
		apiKey = os.Getenv("TMDB_API_KEY")
		if apiKey == "" {
			log.Fatal("TMDB_API_KEY not set in config or environment")
		}
	}
	return &TMDBService{
		apiKey:  apiKey,
		baseURL: "https://api.themoviedb.org/3",
	}
}

// doRequest executes an HTTP request to TMDB API and handles the response
func (s *TMDBService) doRequest(method, url string, response interface{}) error {
	req, err := http.NewRequest(method, url, nil)
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	// Set Authorization header with Bearer token
	req.Header.Set("Authorization", "Bearer "+s.apiKey)
	req.Header.Set("Accept", "application/json")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return fmt.Errorf("failed to execute request: %w", err)
	}
	defer func() {
		if err := resp.Body.Close(); err != nil {
			log.Printf("Error closing response body: %v", err)
		}
	}()
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("TMDB request failed with status: %d", resp.StatusCode)
	}

	body, _ := io.ReadAll(resp.Body)
	if err := json.Unmarshal(body, response); err != nil {
		return fmt.Errorf("failed to parse response: %w", err)
	}

	return nil
}

// GetMovieTMDBID searches for a movie by its Spanish title
func (s *TMDBService) GetMovieTMDBID(spanishTitle string) (int, error) {
	// Search for the movie by Spanish title
	searchURL := fmt.Sprintf("%s/search/movie?query=%s&language=es-ES",
		s.baseURL, url.QueryEscape(spanishTitle))

	var searchResult struct {
		Results []struct {
			ID int `json:"id"`
		} `json:"results"`
	}

	if err := s.doRequest("GET", searchURL, &searchResult); err != nil {
		return 0, fmt.Errorf("failed to search TMDB: %w", err)
	}

	if len(searchResult.Results) == 0 {
		return 0, fmt.Errorf("no movie found with title: %s", spanishTitle)
	}

	// Get the first result and fetch full details
	movieID := searchResult.Results[0].ID
	return movieID, nil
}

// GetMovieTMDBDetailsFromID fetches detailed information about a specific movie by ID.
func (s *TMDBService) GetMovieTMDBDetailsFromID(movieID int) (*models.MovieDetails, error) {
	detailsURL := fmt.Sprintf("%s/movie/%d?language=es-ES",
		s.baseURL, movieID)

	var movieDetails models.MovieDetails
	if err := s.doRequest("GET", detailsURL, &movieDetails); err != nil {
		return nil, fmt.Errorf("failed to fetch movie details: %w", err)
	}

	return &movieDetails, nil
}

// GetMovieTMDBDetailsByScrapedTitle searches for a movie using the scraped Spanish title
// This is the main method used by the scraper - it searches using the exact title as scraped
func (s *TMDBService) GetMovieTMDBDetailsByScrapedTitle(spanishTitle string) (*models.MovieDetails, error) {
	movieTMDBID, _ := s.GetMovieTMDBID(spanishTitle)
	if movieTMDBID == 0 {
		return nil, nil
	}
	movieTMDBDetails, _ := s.GetMovieTMDBDetailsFromID(movieTMDBID)
	return movieTMDBDetails, nil

}
