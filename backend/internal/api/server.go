// Package api provides the HTTP API server for the cine-uio application
package api

import (
	"context"
	"log"
	"net/http"
	"time"

	"scraper/internal/api/routes"
)

// Server represents the API server
type Server struct {
	Addr string
}

// NewServer creates a new API server instance
func NewServer(addr string) *Server {
	return &Server{Addr: addr}
}

// Start starts the API server with proper timeout configuration
func (s *Server) Start() error {
	// Set up routes
	http.HandleFunc("/api/movies", routes.MoviesHandler)
	http.HandleFunc("/health", routes.HealthHandler)

	// Create HTTP server with timeout configuration
	server := &http.Server{
		Addr:         s.Addr,
		Handler:      nil,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	log.Printf("🚀 Starting cine-uio API server on %s", s.Addr)

	// Use context for graceful shutdown
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Start server in goroutine
	errChan := make(chan error, 1)
	go func() {
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			errChan <- err
		}
		close(errChan)
	}()

	// Wait for server error or cancellation
	select {
	case err := <-errChan:
		return err
	case <-ctx.Done():
		return nil
	}
}
