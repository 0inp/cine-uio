package migrations

import (
	"gorm.io/gorm"

	"scraper/internal/shared/database"
)

// AddTMDBFieldsToMovies adds additional TMDB fields to the movies table
func AddTMDBFieldsToMovies(db *gorm.DB) error {
	// Check if columns already exist
	if db.Migrator().HasColumn(&database.Movie{}, "overview") &&
		db.Migrator().HasColumn(&database.Movie{}, "poster_path") &&
		db.Migrator().HasColumn(&database.Movie{}, "backdrop_path") &&
		db.Migrator().HasColumn(&database.Movie{}, "original_title") &&
		db.Migrator().HasColumn(&database.Movie{}, "vote_average") {
		return nil // Columns already exist
	}

	// Add new columns
	err := db.Migrator().AddColumn(&database.Movie{}, "overview")
	if err != nil {
		return err
	}
	err = db.Migrator().AddColumn(&database.Movie{}, "poster_path")
	if err != nil {
		return err
	}
	err = db.Migrator().AddColumn(&database.Movie{}, "backdrop_path")
	if err != nil {
		return err
	}
	err = db.Migrator().AddColumn(&database.Movie{}, "original_title")
	if err != nil {
		return err
	}
	err = db.Migrator().AddColumn(&database.Movie{}, "vote_average")
	if err != nil {
		return err
	}

	return nil
}
