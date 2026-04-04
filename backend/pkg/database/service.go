package database

import (
	"fmt"

	"scraper/pkg/models"
)

// CinemaService provides database operations for cinemas
func GetAllCinemas() ([]models.Cinema, error) {
	var dbCinemas []Cinema
	result := DB.Find(&dbCinemas)
	if result.Error != nil {
		return nil, fmt.Errorf("failed to get cinemas from database: %w", result.Error)
	}

	// Convert database cinemas to scraper models
	var cinemas []models.Cinema
	for _, dbCinema := range dbCinemas {
		cinemas = append(cinemas, models.Cinema{
			ID:          int(dbCinema.ID),
			Name:        dbCinema.Name,
			StoreID:     dbCinema.StoreID,
			CompanyName: dbCinema.CompanyName,
		})
	}

	return cinemas, nil
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

// SaveScreening saves a screening to the database
func SaveScreening(screening models.Screening) error {
	// Get or create movie
	var movie Movie
	result := DB.Where("title = ?", screening.Movie.Title).FirstOrCreate(&movie)
	if result.Error != nil {
		return fmt.Errorf("failed to get or create movie: %w", result.Error)
	}

	// Get cinema by name
	var cinema Cinema
	result = DB.Where("name = ?", screening.Cinema.Name).First(&cinema)
	if result.Error != nil {
		return fmt.Errorf("failed to get cinema: %w", result.Error)
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
		return fmt.Errorf("failed to create screening: %w", result.Error)
	}

	return nil
}

// SaveScreenings saves multiple screenings to the database
func SaveScreenings(screenings []models.Screening) error {
	for _, screening := range screenings {
		err := SaveScreening(screening)
		if err != nil {
			return fmt.Errorf("failed to save screening for %s: %w", screening.Movie.Title, err)
		}
	}
	return nil
}
