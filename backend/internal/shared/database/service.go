package database

import (
	"fmt"
	"log"
	"time"

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

// GetMovieByTitle finds a movie by its scraped title
func GetMovieByTitle(title string) (*Movie, error) {
	var movie Movie
	result := DB.Where("scraped_title = ?", title).First(&movie)
	if result.Error != nil {
		if result.Error == gorm.ErrRecordNotFound {
			return nil, nil
		}
		return nil, fmt.Errorf("failed to get movie by title: %w", result.Error)
	}
	return &movie, nil
}

// GetOrCreateMovie finds or creates a movie with TMDB data
func GetOrCreateMovie(title string, spanishTitle, originalTitle *string, duration *int,
	overview, posterPath, backdropPath *string, voteAverage *float64) (*Movie, error) {

	var movie Movie
	result := DB.Where("scraped_title = ?", title).First(&movie)

	if result.Error != nil && result.Error != gorm.ErrRecordNotFound {
		return nil, fmt.Errorf("failed to check existing movie: %w", result.Error)
	}

	// If movie exists, update with new TMDB data
	if result.RowsAffected > 0 {
		updates := make(map[string]interface{})
		if spanishTitle != nil {
			updates["spanish_title"] = spanishTitle
		}
		if originalTitle != nil {
			updates["original_title"] = originalTitle
		}
		if duration != nil {
			updates["duration"] = duration
		}
		if overview != nil {
			updates["overview"] = overview
		}
		if posterPath != nil {
			updates["poster_path"] = posterPath
		}
		if backdropPath != nil {
			updates["backdrop_path"] = backdropPath
		}
		if voteAverage != nil {
			updates["vote_average"] = voteAverage
		}

		if len(updates) > 0 {
			if err := DB.Model(&movie).Updates(updates).Error; err != nil {
				return nil, fmt.Errorf("failed to update movie: %w", err)
			}
		}
		return &movie, nil
	}

	// Create new movie
	movie = Movie{
		ScrapedTitle:  title,
		SpanishTitle:  spanishTitle,
		OriginalTitle: originalTitle,
		Duration:      duration,
		Overview:      overview,
		PosterPath:    posterPath,
		BackdropPath:  backdropPath,
		VoteAverage:   voteAverage,
	}

	if err := DB.Create(&movie).Error; err != nil {
		return nil, fmt.Errorf("failed to create movie: %w", err)
	}

	return &movie, nil
}

// GetCinemaByNameAndStoreID finds a cinema by name and store ID
func GetCinemaByNameAndStoreID(name, storeID string) (*Cinema, error) {
	var cinema Cinema
	result := DB.Where("name = ? AND store_id = ?", name, storeID).First(&cinema)
	if result.Error != nil {
		if result.Error == gorm.ErrRecordNotFound {
			return nil, nil
		}
		return nil, fmt.Errorf("failed to get cinema: %w", result.Error)
	}
	return &cinema, nil
}

// CreateCinema creates a new cinema record
func CreateCinema(name, storeID string, companyID uint) (*Cinema, error) {
	cinema := Cinema{
		Name:      name,
		StoreID:   storeID,
		CompanyID: companyID,
	}

	if err := DB.Create(&cinema).Error; err != nil {
		return nil, fmt.Errorf("failed to create cinema: %w", err)
	}

	return &cinema, nil
}

// CreateScreening creates a new screening record
func CreateScreening(movieID, cinemaID uint, date time.Time, time, language, url string) (*Screening, error) {
	screening := Screening{
		MovieID:  movieID,
		CinemaID: cinemaID,
		Date:     date,
		Time:     time,
		Language: language,
		URL:      url,
	}

	if err := DB.Create(&screening).Error; err != nil {
		return nil, fmt.Errorf("failed to create screening: %w", err)
	}

	return &screening, nil
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

// MovieWithScreenings represents a movie with its screenings for internal use
type MovieWithScreenings struct {
	ScrapedTitle  string
	SpanishTitle  *string
	OriginalTitle *string
	Duration      *int
	Overview      *string
	PosterPath    *string
	BackdropPath  *string
	VoteAverage   *float64
	Screenings    []ScreeningWithCinema
}

// ScreeningWithCinema represents a screening with cinema information
type ScreeningWithCinema struct {
	Date     time.Time
	Time     string
	Language string
	Cinema   string
	URL      string
}

// GetAllMoviesWithScreenings returns all movies with their screenings
func GetAllMoviesWithScreenings() ([]MovieWithScreenings, error) {
	var movies []Movie

	// Get all movies with their screenings
	result := DB.Preload("Screenings").
		Preload("Screenings.Cinema").
		Find(&movies)

	if result.Error != nil {
		return nil, fmt.Errorf("failed to get movies: %w", result.Error)
	}

	// Convert to internal format
	var responseMovies []MovieWithScreenings
	for _, movie := range movies {
		// Convert screenings
		var screenings []ScreeningWithCinema
		for _, screening := range movie.Screenings {
			// Get cinema name from the preloaded Cinema association
			var cinemaName string
			if screening.Cinema.ID > 0 {
				cinemaName = screening.Cinema.Name
			}
			screenings = append(screenings, ScreeningWithCinema{
				Date:     screening.Date,
				Time:     screening.Time,
				Language: screening.Language,
				Cinema:   cinemaName,
				URL:      screening.URL,
			})
		}

		responseMovies = append(responseMovies, MovieWithScreenings{
			ScrapedTitle:  movie.ScrapedTitle,
			SpanishTitle:  movie.SpanishTitle,
			OriginalTitle: movie.OriginalTitle,
			Duration:      movie.Duration,
			Overview:      movie.Overview,
			PosterPath:    movie.PosterPath,
			BackdropPath:  movie.BackdropPath,
			VoteAverage:   movie.VoteAverage,
			Screenings:    screenings,
		})
	}

	return responseMovies, nil
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
		// Get or create movie
		var duration *int
		var overview *string
		var posterPath *string
		var backdropPath *string
		var spanishTitle *string
		var originalTitle *string
		var voteAverage *float64

		if tmdbDetails, ok := movieTMDBMap[screening.MovieTitle]; ok {
			if tmdbDetails.Runtime > 0 {
				runtime := tmdbDetails.Runtime
				duration = &runtime
			}
			if tmdbDetails.Overview != "" {
				overview = &tmdbDetails.Overview
			}
			if tmdbDetails.PosterPath != "" {
				posterPath = &tmdbDetails.PosterPath
			}
			if tmdbDetails.BackdropPath != "" {
				backdropPath = &tmdbDetails.BackdropPath
			}
			if tmdbDetails.Title != "" {
				spanishTitle = &tmdbDetails.Title
			}
			if tmdbDetails.OriginalTitle != "" {
				originalTitle = &tmdbDetails.OriginalTitle
			}
			if tmdbDetails.VoteAverage > 0 {
				voteAvg := tmdbDetails.VoteAverage
				voteAverage = &voteAvg
			}
		}

		movie, err := GetOrCreateMovie(screening.MovieTitle, spanishTitle, originalTitle, duration,
			overview, posterPath, backdropPath, voteAverage)
		if err != nil {
			return fmt.Errorf("failed to get or create movie '%s': %w", screening.MovieTitle, err)
		}

		// Get or create cinema
		cinema, err := GetCinemaByNameAndStoreID(screening.CinemaName, screening.StoreID)
		if err != nil {
			return fmt.Errorf("failed to get cinema: %w", err)
		}

		if cinema == nil {
			// Create new cinema (Multicines company ID = 1)
			cinema, err = CreateCinema(screening.CinemaName, screening.StoreID, 1)
			if err != nil {
				return fmt.Errorf("failed to create cinema '%s': %w", screening.CinemaName, err)
			}
		}

		// Create screening
		_, err = CreateScreening(movie.ID, cinema.ID, screening.Date, screening.Time,
			screening.Language, screening.URL)
		if err != nil {
			return fmt.Errorf("failed to create screening for %s: %w", screening.MovieTitle, err)
		}
	}

	fmt.Printf("✅ Successfully saved %d screenings to database!\n", len(screeningsSlice))
	return nil
}
