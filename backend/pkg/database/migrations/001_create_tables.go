package migrations

import (
	"fmt"

	"gorm.io/gorm"
	"scraper/pkg/database"
)

// CreateTables runs the first migration to create all database tables
func CreateTables(db *gorm.DB) error {
	fmt.Println("📋 Running migration 001: Create tables...")

	// Create cinema_companies table
	err := db.AutoMigrate(&database.CinemaCompany{})
	if err != nil {
		return fmt.Errorf("failed to create cinema_companies table: %w", err)
	}

	// Create cinemas table
	err = db.AutoMigrate(&database.Cinema{})
	if err != nil {
		return fmt.Errorf("failed to create cinemas table: %w", err)
	}

	// Create movies table
	err = db.AutoMigrate(&database.Movie{})
	if err != nil {
		return fmt.Errorf("failed to create movies table: %w", err)
	}

	// Create screening_times table
	err = db.AutoMigrate(&database.Screening{})
	if err != nil {
		return fmt.Errorf("failed to create screening_times table: %w", err)
	}

	fmt.Println("✅ Migration 001 completed: All tables created successfully!")
	return nil
}
