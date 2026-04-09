package routes

import (
	"encoding/json"
	"net/http"

	"scraper/internal/scraper"
	"scraper/internal/shared/config"
)

// TMDBConfigResponse represents the TMDB configuration response
type TMDBConfigResponse struct {
	BaseURL       string   `json:"base_url"`
	SecureBaseURL string   `json:"secure_base_url"`
	BackdropSizes []string `json:"backdrop_sizes"`
	PosterSizes   []string `json:"poster_sizes"`
}

// TMDBConfigHandler handles requests for TMDB configuration
func TMDBConfigHandler(w http.ResponseWriter, _ *http.Request) {
	// Load configuration
	cfg := config.LoadConfig()
	tmdbService := scraper.NewTMDBService(cfg)

	// Get TMDB configuration
	config, err := tmdbService.GetTMDBConfiguration()
	if err != nil {
		http.Error(w, "Failed to get TMDB configuration", http.StatusInternalServerError)
		return
	}

	// Prepare response
	response := TMDBConfigResponse{
		BaseURL:       config.Images.BaseURL,
		SecureBaseURL: config.Images.SecureBaseURL,
		BackdropSizes: config.Images.BackdropSizes,
		PosterSizes:   config.Images.PosterSizes,
	}

	// Set headers and respond
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "GET")

	if err := json.NewEncoder(w).Encode(response); err != nil {
		http.Error(w, "Failed to encode response", http.StatusInternalServerError)
		return
	}
}
