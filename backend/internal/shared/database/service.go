package database

import (
	"fmt"
	"log"

	"scraper/internal/shared/models"

	"gorm.io/gorm"
)

// GetAllCinemas returns all cinemas from the database.
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

// GetCinemaCompanyByID gets a cinema company by its ID
func GetCinemaCompanyByID(id uint) (*CinemaCompany, error) {
	var company CinemaCompany
	result := DB.Where("id = ?", id).First(&company)
	if result.Error != nil {
		return nil, fmt.Errorf("failed to get cinema company: %w", result.Error)
	}
	return &company, nil
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
func SaveScrapedScreenings(screenings interface{}) error {
	var screeningsSlice []models.ScrapedScreening
	var movieTMDBMap map[string]*models.MovieDetails

	// Handle different input types and extract TMDB data
	switch v := screenings.(type) {
	case []models.ScrapedScreening:
		screeningsSlice = v
	case []models.ScrapedScreeningWithTMDB:
		// Extract TMDB data and convert to ScrapedScreening
		for _, sw := range v {
			screeningsSlice = append(screeningsSlice, sw.ScrapedScreening)
			// Store TMDB data in a map for later use
			if sw.TMDBDetails != nil {
				if movieTMDBMap == nil {
					movieTMDBMap = make(map[string]*models.MovieDetails)
				}
				movieTMDBMap[sw.MovieTitle] = sw.TMDBDetails
			}
		}
	default:
		return fmt.Errorf("unsupported type for screenings: %T", screenings)
	}

	log.Printf("💾 Starting to save %d screenings to database...", len(screeningsSlice))

	if len(screeningsSlice) == 0 {
		fmt.Println("⚠️  No screenings to save - empty slice received")
		return nil
	}

	for _, screening := range screeningsSlice {
		var movie Movie
		var cinema Cinema

		// Get or create movie by title
		var duration *int
		if tmdbDetails, ok := movieTMDBMap[screening.MovieTitle]; ok && tmdbDetails.Runtime > 0 {
			runtime := tmdbDetails.Runtime
			duration = &runtime
		}
		result := DB.Where("title = ?", screening.MovieTitle).FirstOrCreate(&movie, Movie{Title: screening.MovieTitle, Duration: duration})
		if result.Error != nil {
			return fmt.Errorf("failed to get or create movie '%s': %w", screening.MovieTitle, result.Error)
		}

		// Get or create cinema by name and store ID
		result = DB.Where("name = ? AND store_id = ?", screening.CinemaName, screening.StoreID).First(&cinema)
		if result.Error != nil {
			// If not found, try to find by name only
			result = DB.Where("name = ?", screening.CinemaName).First(&cinema)
			if result.Error != nil {
				// If still not found, create new cinema with proper company info
				// Since we're scraping Multicines, we know the company
				cinema = Cinema{Name: screening.CinemaName, CompanyID: 1, StoreID: screening.StoreID}
				result = DB.Create(&cinema)
			}
		}
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

		// log.Printf("📝 Saved screening %d/%d: %s at %s", i+1, len(screeningsSlice), screening.MovieTitle, screening.CinemaName)
	}

	fmt.Printf("✅ Successfully saved %d screenings to database!\n", len(screeningsSlice))
	return nil
}
