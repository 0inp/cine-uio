package migrations

import (
	"gorm.io/gorm"

	"scraper/internal/shared/database"
)

// AddDurationToMovies adds the duration column to the movies table
func AddDurationToMovies(db *gorm.DB) error {
	// Check if the column already exists
	if db.Migrator().HasColumn(&database.Movie{}, "duration") {
		return nil
	}

	// Add the duration column
	err := db.Migrator().AddColumn(&database.Movie{}, "duration")
	if err != nil {
		return err
	}

	return nil
}
