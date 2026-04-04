package database

import (
	"fmt"
	"gorm.io/gorm"
	"log"
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
	log.Printf("💾 Starting to save %d screenings to database...", len(screenings))

	if len(screenings) == 0 {
		fmt.Println("⚠️  No screenings to save - empty slice received")
		return nil
	}

	for i, screening := range screenings {
		var movie Movie
		var cinema Cinema

		// Get or create movie by title
		result := DB.Where("title = ?", screening.MovieTitle).FirstOrCreate(&movie, Movie{Title: screening.MovieTitle})
		if result.Error != nil {
			return fmt.Errorf("failed to get or create movie '%s': %w", screening.MovieTitle, result.Error)
		}

		// Get or create cinema by name
		result = DB.Where("name = ?", screening.CinemaName).FirstOrCreate(&cinema, Cinema{Name: screening.CinemaName, CompanyID: 1, StoreID: "unknown", CompanyName: "Unknown"})
		if result.Error != nil {
			return fmt.Errorf("failed to get or create cinema '%s': %w", screening.CinemaName, result.Error)
		}

		// Create screening record
		dbScreening := Screening{
			MovieID:  movie.ID,
			CinemaID: cinema.ID,
			Date:     screening.Date,
			Time:     screening.Time,
			Language: screening.Language,
		}

		result = DB.Create(&dbScreening)
		if result.Error != nil {
			return fmt.Errorf("failed to create screening for %s: %w", screening.MovieTitle, result.Error)
		}

		log.Printf("📝 Saved screening %d/%d: %s at %s", i+1, len(screenings), screening.MovieTitle, screening.CinemaName)
	}

	fmt.Printf("✅ Successfully saved %d screenings to database!\n", len(screenings))
	return nil
}
