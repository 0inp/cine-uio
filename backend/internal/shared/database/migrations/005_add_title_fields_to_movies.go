package migrations

import (
	"fmt"

	"gorm.io/gorm"

	"scraper/internal/shared/database"
)

// AddTitleFieldsToMovies renames title to scraped_title and adds spanish_title field to the movies table
func AddTitleFieldsToMovies(db *gorm.DB) error {
	// Check if the migration has already been applied
	if db.Migrator().HasColumn(&database.Movie{}, "scraped_title") &&
		db.Migrator().HasColumn(&database.Movie{}, "spanish_title") {
		return nil // Migration already applied
	}

	// First, check if we need to rename the existing title column to scraped_title
	if db.Migrator().HasColumn(&database.Movie{}, "title") &&
		!db.Migrator().HasColumn(&database.Movie{}, "scraped_title") {
		// Rename the title column to scraped_title
		err := db.Exec("ALTER TABLE movies RENAME COLUMN title TO scraped_title")
		if err != nil {
			return fmt.Errorf("failed to rename title column to scraped_title: %w", err.Error)
		}
	}

	// Add the spanish_title column if it doesn't exist
	if !db.Migrator().HasColumn(&database.Movie{}, "spanish_title") {
		err := db.Migrator().AddColumn(&database.Movie{}, "spanish_title")
		if err != nil {
			return err
		}
	}

	return nil
}
