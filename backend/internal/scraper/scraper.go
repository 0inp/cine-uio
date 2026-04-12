// Package scraper provides web scraping functionality for cinema data.
package scraper

import (
	"context"
	"fmt"
	"strings"
	"time"

	"scraper/internal/shared/config"
	"scraper/internal/shared/database"
	"scraper/internal/shared/logger"
	"scraper/internal/shared/models"

	"github.com/PuerkitoBio/goquery"
	"github.com/chromedp/chromedp"
)

// Scraper is the main web scraper for cinema data.
type Scraper struct {
	Ctx         context.Context
	Logger      *logger.Logger
	TMDBService *TMDBService
}

// NewScraper creates a new scraper instance with the given logger.
func NewScraper(logger *logger.Logger, cfg *config.Config) (*Scraper, context.CancelFunc) {
	ctx, cancel := chromedp.NewContext(context.Background())
	return &Scraper{
		Ctx:         ctx,
		Logger:      logger,
		TMDBService: NewTMDBService(cfg),
	}, cancel
}

// scrapeScreeningTimesFromHTML scrapes the screening times from HTML for a specific date
func (s *Scraper) scrapeScreeningTimesFromHTML(doc *goquery.Document, movieTitle string, cinema database.Cinema, date time.Time, movieURL string) ([]models.ScrapedScreening, error) {
	var screenings []models.ScrapedScreening

	// Check for EmptyState (no screenings available)
	emptyState := doc.Find(".MovieDetail__content__session-type .EmptyState")
	if emptyState.Length() > 0 {
		s.Logger.Info("  ℹ No screening times available for this day (EmptyState detected)")
		return screenings, nil
	}

	// Find all session type containers
	sessionContainers := doc.Find(".MovieDetail__content__session-type")
	if sessionContainers.Length() == 0 {
		s.Logger.Warn("  ⚠ No session type containers found")
		return screenings, nil
	}

	// Use the provided date for all screenings on this day
	// Extract just the date part (without time) for storage
	dateOnly := time.Date(date.Year(), date.Month(), date.Day(), 0, 0, 0, 0, date.Location())
	s.Logger.Debug("  → Processing screenings for date: %s", dateOnly.Format("2006-01-02"))

	// Process session containers for this day
	if sessionContainers.Length() == 0 {
		s.Logger.Warn("  ⚠ No session type containers found")
		return screenings, nil
	}

	sessionContainers.Each(func(_ int, sessionContainer *goquery.Selection) {
		sessionTypes := sessionContainer.Find(".SessionType")
		if sessionTypes.Length() == 0 {
			sessionTypes = sessionContainer.Find(".sc-10d01b1b-0")
		}

		sessionTypes.Each(func(_ int, session *goquery.Selection) {
			// Extract language from the current session type
			language := session.Find(".SessionType__name").Text()
			if language == "" {
				language = session.Find(".sc-10d01b1b-0 .SessionType__name").Text()
			}
			if language == "" {
				language = "Unknown"
			}

			// Find all session times within this specific session type
			// Look for times in the current session's theater type list
			theaterTypes := session.Find(".TheaterType")
			if theaterTypes.Length() == 0 {
				theaterTypes = session.Find(".sc-ba5c4fe5-0")
			}

			theaterTypes.Each(func(_ int, theaterType *goquery.Selection) {
				// Find all session times within this theater type
				sessionTimes := theaterType.Find(".ScheduleSession .ScheduleSession__text")
				if sessionTimes.Length() == 0 {
					sessionTimes = theaterType.Find(".sc-870fb5d6-0 .ScheduleSession__text")
				}

				sessionTimes.Each(func(_ int, timeSel *goquery.Selection) {
					time := strings.TrimSpace(timeSel.Text())
					if time == "" {
						return
					}

					screening := models.ScrapedScreening{
						MovieTitle: movieTitle,  // For lookup in database service
						CinemaName: cinema.Name, // For lookup in database service
						StoreID:    cinema.StoreID,
						Date:       dateOnly, // Use date-only value
						Time:       time,
						Language:   language,
						URL:        movieURL, // Store the actual cinema website URL
					}
					screenings = append(screenings, screening)
					s.Logger.Debug("      ✅ Scraped: %s at %s on %s (Language: %s)", movieTitle, time, dateOnly.Format("2006-01-02"), language)
				})
			})
		})
	})

	return screenings, nil
}

// ScrapeMovieScreenings scrapes movie screening data from a specific movie page.
func (s *Scraper) ScrapeMovieScreenings(movieURL string, cinema database.Cinema) ([]models.ScrapedScreening, error) {
	var screenings []models.ScrapedScreening
	var err error

	s.Logger.Info("  → Starting to scrape movie page: %s", movieURL)

	// Navigate to the movie page
	err = chromedp.Run(s.Ctx,
		chromedp.Navigate(movieURL),
		chromedp.WaitVisible("body", chromedp.ByQuery),
		// Wait for the slick slider to be ready
		chromedp.WaitVisible(`.MovieDetail__content__days`, chromedp.ByQuery),
		chromedp.Sleep(2*time.Second), // Wait for initial content to load
	)
	if err != nil {
		return nil, fmt.Errorf("error navigating to movie page: %w", err)
	}

	// Get the movie title
	var movieTitle string
	err = chromedp.Run(s.Ctx,
		chromedp.Text(".MovieCard__title", &movieTitle, chromedp.ByQuery),
	)
	if err != nil || movieTitle == "" {
		err = chromedp.Run(s.Ctx,
			chromedp.Text("h1", &movieTitle, chromedp.ByQuery),
		)
		if err != nil || movieTitle == "" {
			return nil, fmt.Errorf("movie title not found")
		}
	}
	s.Logger.Debug("  → Movie: %s", movieTitle)

	// Check the data-index attribute of the active slick slide
	var activeIndexStr string
	err = chromedp.Run(s.Ctx,
		chromedp.Evaluate(`document.querySelector('.slick-slide.slick-active')?.getAttribute('data-index') || '-1'`, &activeIndexStr),
	)
	if err != nil {
		s.Logger.Warn("  ⚠ Error getting active slide index: %v", err)
		activeIndexStr = "-1"
	}

	// Convert string to int
	var activeIndex int
	if activeIndexStr != "-1" {
		_, err := fmt.Sscanf(activeIndexStr, "%d", &activeIndex)
		if err != nil {
			s.Logger.Warn("  ⚠ Error parsing active slide index '%s': %v", activeIndexStr, err)
			activeIndex = -1
		}
	} else {
		activeIndex = -1
	}

	s.Logger.Debug("  → Active slide data-index: %d", activeIndex)

	// If active index > 6, skip this movie entirely
	if activeIndex > 6 {
		s.Logger.Info("  → Skipping movie: active index %d > 6", activeIndex)
		return screenings, nil
	}

	// Determine the range of days to scrape: from activeIndex to 6
	startIndex := activeIndex
	endIndex := 6
	if activeIndex < 0 {
		// If we couldn't determine the active index, fall back to original behavior
		startIndex = 0
		endIndex = 6
	}

	s.Logger.Debug("  → Scraping days from index %d to %d", startIndex, endIndex)

	// Scrape screenings for each day in the determined range
	for dayIndex := startIndex; dayIndex <= endIndex; dayIndex++ {
		s.Logger.Debug("  → Processing day %d", dayIndex)

		if dayIndex > 0 {
			// Click on the day button for days 1-6
			s.Logger.Debug("  → Clicking on day %d (data-index=%d)", dayIndex, dayIndex)
			err = chromedp.Run(s.Ctx,
				chromedp.Click(fmt.Sprintf(`.slick-slide[data-index="%d"]`, dayIndex), chromedp.ByQuery),
				chromedp.Sleep(3*time.Second), // Wait for XHR to complete
			)
			if err != nil {
				s.Logger.Warn("    ⚠ Error clicking day %d: %v", dayIndex, err)
				continue
			}
		}

		// Get the current date for this day
		currentDate := time.Now().In(time.FixedZone("ECT", -5*60*60)) // Ecuador Time (UTC-5)
		if dayIndex > 0 {
			currentDate = currentDate.AddDate(0, 0, dayIndex)
		}

		// Parse the page to get screenings for this day
		var dayHTML string
		err = chromedp.Run(s.Ctx,
			chromedp.OuterHTML("body", &dayHTML, chromedp.ByQuery),
		)
		if err != nil {
			s.Logger.Warn("    ⚠ Error getting HTML for day %d: %v", dayIndex, err)
			continue
		}

		// Parse the HTML and scrape screenings for this day
		doc, err := goquery.NewDocumentFromReader(strings.NewReader(dayHTML))
		if err != nil {
			s.Logger.Warn("    ⚠ Error parsing HTML for day %d: %v", dayIndex, err)
			continue
		}

		// Check for EmptyState before processing
		emptyState := doc.Find(".MovieDetail__content__session-type .EmptyState")
		if emptyState.Length() > 0 {
			s.Logger.Info("    ℹ No screening times available for day %d (EmptyState detected)", dayIndex)
			continue
		}

		// Scrape screenings for this specific day
		dayScreenings, err := s.scrapeScreeningTimesFromHTML(doc, movieTitle, cinema, currentDate, movieURL)
		if err != nil {
			s.Logger.Warn("    ⚠ Error scraping screenings for day %d: %v", dayIndex, err)
			continue
		}

		screenings = append(screenings, dayScreenings...)
	}

	return screenings, nil
}

// fetchTMDBDataForScreenings fetches TMDB data for all unique movie titles in screenings
func (s *Scraper) fetchTMDBDataForScreenings(screenings []models.ScrapedScreening) []models.ScrapedScreeningWithTMDB {
	// Collect unique movie titles
	movieTitles := make(map[string]bool)
	for _, screening := range screenings {
		movieTitles[screening.MovieTitle] = true
	}

	// Fetch TMDB data for each unique movie
	movieTMDBMap := make(map[string]*models.MovieDetails)
	for title := range movieTitles {
		s.Logger.Info("🔍 Fetching TMDB data for: %s", title)

		details, err := s.TMDBService.GetMovieTMDBDetailsByScrapedTitle(title)
		if err != nil {
			s.Logger.Warn("⚠️  TMDB data not found for '%s': %v", title, err)
			continue
		}

		movieTMDBMap[title] = details
		s.Logger.Info("✅ Found TMDB data for '%s': %d minutes", title, details.Runtime)
	}

	// Create enhanced screenings with TMDB data
	var screeningsWithTMDB []models.ScrapedScreeningWithTMDB
	for _, screening := range screenings {
		details := movieTMDBMap[screening.MovieTitle]
		screeningsWithTMDB = append(screeningsWithTMDB, models.ScrapedScreeningWithTMDB{
			ScrapedScreening: screening,
			TMDBDetails:      details,
		})
	}

	return screeningsWithTMDB
}

// ScrapeMulticines scrapes data from all Multicines cinemas.
func (s *Scraper) ScrapeMulticines() ([]models.ScrapedScreeningWithTMDB, error) {
	var allScreenings []models.ScrapedScreening
	var cinemas []database.Cinema
	var err error

	// Get cinemas from database
	cinemas, err = database.GetAllCinemas()
	if err != nil {
		return nil, fmt.Errorf("failed to get cinemas from database: %w", err)
	}

	var company *database.CinemaCompany
	for _, cinema := range cinemas {
		s.Logger.Info("🎬 Starting to scrape cinema: %s", cinema.Name)

		// Get Multicines company to get base URL
		company, err = database.GetCinemaCompanyByName("Multicines")
		if err != nil {
			s.Logger.Error("❌ Error getting Multicines company: %v", err)
			continue
		}

		url := fmt.Sprintf("%s?cityId=19&storeId=%s", company.BaseURL, cinema.StoreID)

		// Navigate to the cinema page
		err = chromedp.Run(s.Ctx,
			chromedp.Navigate(url),
			chromedp.WaitVisible("body", chromedp.ByQuery),
			chromedp.Sleep(5*time.Second), // Wait for JS to load
		)
		if err != nil {
			s.Logger.Error("❌ Error navigating to %s: %v", cinema.Name, err)
			continue
		}

		// Get all movie card URLs first to avoid navigation issues
		// Since movie cards don't have direct href attributes, we need to click them and get the resulting URL
		var movieCount int
		err = chromedp.Run(s.Ctx,
			chromedp.Evaluate(`Array.from(document.querySelectorAll('.MovieCard')).length`, &movieCount),
		)
		if err != nil {
			s.Logger.Error("❌ Error counting movie cards for %s: %v", cinema.Name, err)
			continue
		}

		if movieCount == 0 {
			s.Logger.Warn("  ⚠ No movie cards found for cinema: %s", cinema.Name)
			continue
		}

		// Process each movie card by clicking and getting the URL
		for i := 0; i < movieCount; i++ {
			var screenings []models.ScrapedScreening
			s.Logger.Info("  🎥 Processing movie card %d/%d", i+1, movieCount)

			// Get the current URL before clicking
			var currentURL string
			err = chromedp.Run(s.Ctx,
				chromedp.Location(&currentURL),
			)
			if err != nil {
				s.Logger.Warn("    ⚠ Error getting current URL: %v", err)
				continue
			}

			// Click on the movie card using JavaScript
			var movieURL string
			err = chromedp.Run(s.Ctx,
				chromedp.Evaluate(fmt.Sprintf(`document.querySelectorAll('.MovieCard')[%d].click()`, i), nil),
				chromedp.Sleep(3*time.Second), // Wait for navigation
				chromedp.WaitVisible("body", chromedp.ByQuery),
				chromedp.Location(&movieURL),
			)
			if err != nil {
				s.Logger.Warn("    ⚠ Error clicking movie card %d: %v", i, err)
				// Navigate back to the cinema page
				err = chromedp.Run(s.Ctx,
					chromedp.Navigate(currentURL),
					chromedp.WaitVisible("body", chromedp.ByQuery),
				)
				if err != nil {
					s.Logger.Warn("    ⚠ Error navigating back to cinema page after click error: %v", err)
				}
				continue
			}

			s.Logger.Info("    🔗 Movie URL: %s", movieURL)

			// Scrape the screenings from the movie page
			screenings, err = s.ScrapeMovieScreenings(movieURL, cinema)
			if err != nil {
				s.Logger.Error("    ❌ Error scraping movie screenings: %v", err)
			} else {
				allScreenings = append(allScreenings, screenings...)
			}

			// Navigate back to the cinema page for the next movie
			err = chromedp.Run(s.Ctx,
				chromedp.Navigate(currentURL),
				chromedp.WaitVisible("body", chromedp.ByQuery),
			)
			if err != nil {
				s.Logger.Warn("    ⚠ Error navigating back to cinema page: %v", err)
			}
			// Add a small delay to ensure page is fully loaded
			if err := chromedp.Sleep(2 * time.Second).Do(s.Ctx); err != nil {
				s.Logger.Warn("    ⚠ Error during sleep: %v", err)
			}
		}
	}

	// Fetch TMDB data for all screenings
	screeningsWithTMDB := s.fetchTMDBDataForScreenings(allScreenings)

	return screeningsWithTMDB, nil
}
