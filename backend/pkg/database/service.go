package database

import (
	"fmt"

	"gorm.io/gorm"
	"scraper/pkg/models"
)

// CinemaService provides database operations for cinemas
func GetAllCinemas() ([]Cinema, error) {
	var cinemas []Cinema
	result := DB.Find(&cinemas)
	if result.Error != nil {
		return nil, fmt.Errorf("failed to get cinemas from database: %w", result.Error)
	}

	return cinemas, nil
}

// ClearOldScreeningData clears movies and screening_times tables before new scrape
func ClearOldScreeningData() error {
	// Delete all screening times first (due to foreign key constraints)
	result := DB.Session(&gorm.Session{AllowGlobalUpdate: true}).
		Unscoped().
		Where("1 = 1").
		Delete(&Screening{})
	if result.Error != nil {
		return fmt.Errorf("failed to clear screening_times: %w", result.Error)
	}

	// Delete all movies
	result = DB.Session(&gorm.Session{AllowGlobalUpdate: true}).
		Unscoped().
		Where("1 = 1").
		Delete(&Movie{})
	if result.Error != nil {
		return fmt.Errorf("failed to clear movies: %w", result.Error)
	}

	return nil
}

// GetCinemaCompanyByName gets a cinema company by name
func GetCinemaCompanyByName(name string) (*CinemaCompany, error) {
	var company CinemaCompany
	result := DB.Where("name = ?", name).First(&company)
	if result.Error != nil {
		return nil, fmt.Errorf("failed to get cinema company: %w", result.Error)
	}
	return &company, nil
}

// SaveScrapedScreenings saves screenings from the scraper to the database
func SaveScrapedScreenings(screenings []models.ScrapedScreening) error {
	fmt.Printf("💾 Starting to save %d screenings to database...\n", len(screenings))

	if len(screenings) == 0 {
		fmt.Println("⚠️  No screenings to save - empty slice received")
		return nil
	}

	for i, screening := range screenings {
		// Get or create movie by title
		var movie Movie
		result := DB.Where("title = ?", screening.MovieTitle).FirstOrCreate(&movie, Movie{Title: screening.MovieTitle})
		if result.Error != nil {
			return fmt.Errorf("failed to get or create movie '%s': %w", screening.MovieTitle, result.Error)
		}

		// Update the screening with the actual movie ID
		screening.MovieID = movie.ID

		// Get cinema by ID (we already have this from scraping)
		var cinema Cinema
		result = DB.Where("id = ?", screening.CinemaID).First(&cinema)
		if result.Error != nil {
			return fmt.Errorf("failed to get cinema with ID %d: %w", screening.CinemaID, result.Error)
		}

		// Create screening record
		dbScreening := Screening{
			MovieID:  screening.MovieID,
			CinemaID: screening.CinemaID,
			Date:     screening.Date,
			Time:     screening.Time,
			Language: screening.Language,
		}

		result = DB.Create(&dbScreening)
		if result.Error != nil {
			return fmt.Errorf("failed to create screening for %s: %w", screening.MovieTitle, result.Error)
		}

		fmt.Printf("📝 Saved screening %d/%d: %s at %s\n", i+1, len(screenings), screening.MovieTitle, cinema.Name)
	}

	fmt.Printf("✅ Successfully saved %d screenings to database!\n", len(screenings))
	return nil
}
