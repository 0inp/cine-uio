package scraper

import (
	"context"
	"fmt"
	"strings"
	"time"

	"scraper/logger"
	"scraper/pkg/database"
	"scraper/pkg/models"

	"github.com/KarpelesLab/strftime"
	"github.com/PuerkitoBio/goquery"
	"github.com/chromedp/chromedp"
	"golang.org/x/text/language"
)

type Scraper struct {
	Ctx    context.Context
	Logger *logger.Logger
}

func NewScraper(logger *logger.Logger) (*Scraper, context.CancelFunc) {
	ctx, cancel := chromedp.NewContext(context.Background())
	return &Scraper{
		Ctx:    ctx,
		Logger: logger,
	}, cancel
}

// scrapeScreeningTimes scrapes the screening times for a movie on specific dates
func (s *Scraper) scrapeScreeningTimes(doc *goquery.Document, movieTitle string, cinema database.Cinema) ([]models.ScrapedScreening, error) {
	var screenings []models.ScrapedScreening
	var err error
	var location *time.Location

	// Find all session type containers
	sessionContainers := doc.Find(".MovieDetail__content__session-type")
	if sessionContainers.Length() == 0 {
		s.Logger.Warn("  ⚠ No session type containers found")
		return screenings, nil
	}

	// Define the timezone for Quito, Ecuador (UTC-5)
	location, err = time.LoadLocation("America/Guayaquil")
	if err != nil {
		return nil, fmt.Errorf("failed to load timezone: %w", err)
	}

	// Start from today's date in Quito's timezone
	startDate := time.Now().In(location)
	expectedDates := make(map[string]time.Time)

	// Create a formatter for Spanish locale
	formatter := strftime.New(language.Make("es"))

	for i := 0; i < 7; i++ {
		currentDate := startDate.AddDate(0, 0, i)
		formatted := formatter.Format("%a. %d", currentDate)
		expectedDates[formatted] = currentDate
	}

	// Process each day element, but only those that match our expected dates
	doc.Find(".Day").Each(func(i int, day *goquery.Selection) {
		dayName := strings.TrimSpace(day.Find(".Day__name").Text())
		dayDate := strings.TrimSpace(day.Find(".Day__number").Text())
		dateStr := strings.ToLower(fmt.Sprintf("%s %s", dayName, dayDate))
		s.Logger.Debug("dateStr : %s", dateStr)

		if parsedDate, exists := expectedDates[dateStr]; exists {
			s.Logger.Info("    → Processing expected day: %s -> %s", dateStr, parsedDate.Format("2006-01-02"))

			// Process session containers for this day
			sessionContainers.Each(func(j int, sessionContainer *goquery.Selection) {
				sessionTypes := sessionContainer.Find(".SessionType")
				if sessionTypes.Length() == 0 {
					sessionTypes = sessionContainer.Find(".sc-10d01b1b-0")
				}

				sessionTypes.Each(func(k int, session *goquery.Selection) {
					sessionTimes := session.Find(".ScheduleSession .ScheduleSession__text")
					if sessionTimes.Length() == 0 {
						sessionTimes = session.Find(".sc-870fb5d6-0 .ScheduleSession__text")
					}

					sessionTimes.Each(func(l int, timeSel *goquery.Selection) {
						time := strings.TrimSpace(timeSel.Text())
						if time == "" {
							return
						}

						language := session.Find(".SessionType__name").Text()
						if language == "" {
							language = "Unknown"
						}

						screening := models.ScrapedScreening{
							MovieTitle: movieTitle,  // For lookup in database service
							CinemaName: cinema.Name, // For lookup in database service
							Date:       parsedDate,
							Time:       time,
							Language:   language,
						}
						screenings = append(screenings, screening)
						s.Logger.Info("      ✅ Scraped: %s at %s on %s (Language: %s)", movieTitle, time, parsedDate.Format("2006-01-02"), language)
					})
				})
			})
		}
	})

	return screenings, nil
}

func (s *Scraper) ScrapeMovieScreenings(movieURL string, cinema database.Cinema) ([]models.ScrapedScreening, error) {
	var screenings []models.ScrapedScreening
	var err error
	var doc *goquery.Document

	s.Logger.Info("  → Starting to scrape movie page: %s", movieURL)

	var movieHTML string
	err = chromedp.Run(s.Ctx,
		chromedp.Navigate(movieURL),
		chromedp.WaitVisible("body", chromedp.ByQuery),
		// Wait for the session type container to be visible (dynamic content)
		chromedp.WaitVisible(".MovieDetail__content__session-type", chromedp.ByQuery),
		chromedp.Sleep(3*time.Second), // Short additional wait for any remaining content
		chromedp.OuterHTML("body", &movieHTML, chromedp.ByQuery),
	)
	if err != nil {
		return nil, fmt.Errorf("error navigating to movie page: %w", err)
	}

	doc, err = goquery.NewDocumentFromReader(strings.NewReader(movieHTML))
	if err != nil {
		return nil, fmt.Errorf("error parsing HTML: %w", err)
	}

	movieTitle := doc.Find(".MovieCard__title").Text()
	if movieTitle == "" {
		movieTitle = doc.Find("h1").Text()
		if movieTitle == "" {
			return nil, fmt.Errorf("movie title not found")
		}
	}
	s.Logger.Info("  → Movie: %s", movieTitle)

	// Scrape the screening times using the helper function
	screenings, err = s.scrapeScreeningTimes(doc, movieTitle, cinema)
	if err != nil {
		return nil, fmt.Errorf("failed to scrape screening times: %w", err)
	}

	return screenings, nil
}

func (s *Scraper) ScrapeMulticines() ([]models.ScrapedScreening, error) {
	var allScreenings []models.ScrapedScreening
	var cinemas []database.Cinema
	var err error

	// Get cinemas from database
	cinemas, err = database.GetAllCinemas()
	if err != nil {
		return nil, fmt.Errorf("failed to get cinemas from database: %w", err)
	}

	// Filter for Multicines cinemas only
	var multicinesCinemas []database.Cinema
	for _, cinema := range cinemas {
		if cinema.CompanyName == "Multicines" {
			multicinesCinemas = append(multicinesCinemas, cinema)
		}
	}

	var company *database.CinemaCompany
	for _, cinema := range multicinesCinemas {
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
				chromedp.Run(s.Ctx,
					chromedp.Navigate(currentURL),
					chromedp.WaitVisible("body", chromedp.ByQuery),
				)
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
			chromedp.Sleep(2 * time.Second).Do(s.Ctx)
		}
	}

	return allScreenings, nil
}
