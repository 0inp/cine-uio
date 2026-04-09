package migrations

import (
	"fmt"

	"gorm.io/gorm"
)

// RunAllMigrations runs all database migrations in order
func RunAllMigrations(db *gorm.DB) error {
	fmt.Println("🚀 Starting database migrations...")

	// Run migration 001: Create tables
	err := CreateTables(db)
	if err != nil {
		return fmt.Errorf("migration 001 failed: %w", err)
	}

	// Run migration 002: Seed cinema data
	err = SeedCinemaData(db)
	if err != nil {
		return fmt.Errorf("migration 002 failed: %w", err)
	}

	// Run migration 003: Add duration to movies
	err = AddDurationToMovies(db)
	if err != nil {
		return fmt.Errorf("migration 003 failed: %w", err)
	}

	// Run migration 004: Add TMDB fields to movies
	err = AddTMDBFieldsToMovies(db)
	if err != nil {
		return fmt.Errorf("migration 004 failed: %w", err)
	}

	// Run migration 005: Add title fields to movies
	err = AddTitleFieldsToMovies(db)
	if err != nil {
		return fmt.Errorf("migration 005 failed: %w", err)
	}

	fmt.Println("🎉 All migrations completed successfully!")
	return nil
}
