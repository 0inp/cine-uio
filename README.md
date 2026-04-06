# Cine-UIO: Quito Cinema Screenings Dashboard

A web scraper and dashboard application that aggregates and displays movie screening times from all cinemas in Quito, Ecuador.

## 🎬 Overview

Cine-UIO is a Go-based application that scrapes cinema websites to collect and reassemble screening times for all movies playing in Quito, Ecuador. Currently focused on Multicines cinemas, the application provides a unified view of movie showtimes across different locations.

## 🎯 Features

- **Multi-cinema scraping**: Collects screening data from multiple Multicines locations in Quito
- **Deduplication**: Removes duplicate screenings to provide clean, accurate data
- **Structured data**: Organizes screenings by movie, cinema, date, time, and language
- **Logging**: Comprehensive logging with configurable log levels
- **Timezone-aware**: Properly handles Quito, Ecuador timezone (UTC-5)

## 🏗️ Current Status

This is currently a **backend-only** application that:
- Scrapes Multicines websites (Plaza Americas and CCI locations)
- Extracts movie titles, screening times, dates, and languages
- Outputs structured data to the console
- Provides the foundation for a future web dashboard
- Includes a comprehensive Go toolchain for web scraping and data processing

## 🚀 Getting Started

### Prerequisites

- Go 1.26.1 or higher
- Google Chrome (for headless browsing)
- Internet connection (for web scraping)
- mise (optional, for tool version management)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/cine-uio.git
   cd cine-uio
   ```

2. Install dependencies:
   ```bash
   go mod download
   ```

3. Install required tools (using mise):
   ```bash
   mise install
   ```

### Running the Scraper

```bash
cd backend
go run main.go
```

#### Command Line Options

- `--log-level`: Set the logging level (debug, info, warn, error, fatal)
  ```bash
  go run main.go --log-level debug
  ```

## 📂 Project Structure

```
cine-uio/
├── backend/
│   ├── main.go                # Main application entry point
│   ├── go.mod                 # Go module definition
│   ├── go.sum                 # Go dependencies checksums
│   ├── pkg/
│   │   ├── scraper/           # Web scraping logic
│   │   │   ├── scraper.go     # Main scraper implementation
│   │   │   └── utils.go        # Utility functions
│   │   ├── models/            # Data models
│   │   │   └── models.go      # Data structures
│   │   ├── database/          # Database operations
│   │   │   ├── db.go           # Database connection
│   │   │   ├── service.go     # Database services
│   │   │   ├── models.go      # Database models
│   │   │   └── migrations/    # Database migrations
│   └── logger/                # Logging functionality
│       └── logger.go          # Logger implementation
├── mise.toml                  # Tool version management
├── .opencode/                 # OpenAgents framework context
└── README.md                  # Project documentation
```

## 🎥 Supported Cinemas

Currently scraping from:
- **Multicines Plaza Americas** (Store ID: 3566)
- **Multicines CCI** (Store ID: 3555)

## 📊 Data Model

### Screening
```go
type Screening struct {
    Movie    Movie    // Movie information
    Cinema   Cinema   // Cinema information
    Date     time.Time // Screening date
    Time     string    // Screening time
    Language string    // Language (e.g., "Español", "Subtitulado")
}
```

### Movie
```go
type Movie struct {
    Title string // Movie title
}
```

### Cinema
```go
type Cinema struct {
    ID          int    // Cinema ID
    Name        string // Cinema name
    StoreID     string // Store identifier for scraping
    CompanyName string // Cinema company name
}
```

## 🔧 Technical Details

### Web Scraping

- Uses **chromedp** for headless Chrome automation
- Handles dynamic content loading with appropriate waits
- Processes HTML with **goquery** for DOM parsing
- Handles Spanish date formats and timezone conversion
- Implements comprehensive error handling and recovery
- Uses context-based cancellation for resource cleanup

### Timezone Handling

- All dates are processed in **America/Guayaquil** timezone (UTC-5)
- Supports Spanish locale date formatting
- Handles 7-day forward-looking scheduling
- Uses fixed timezone for consistent date processing

### Error Handling

- Comprehensive error logging with multiple log levels
- Graceful handling of missing elements and network issues
- Automatic recovery from navigation issues
- Deduplication of screening data
- Context-based error handling and cleanup

## 🚧 Future Development

### Planned Features

- **Web Dashboard**: Interactive UI to view and filter screenings
- **Additional Cinemas**: Support for other Quito cinema chains
- **API Endpoints**: REST API for programmatic access
- **Database Storage**: Persistent storage of historical data
- **Notifications**: Alerts for new movies or schedule changes
- **Search & Filtering**: Advanced filtering by movie, cinema, time, etc.

### Web Dashboard (Future)

The planned web interface will include:
- Interactive calendar view of screenings
- Cinema location map
- Movie details and trailers
- Language filtering
- Time-based filtering (morning, afternoon, evening)
- Mobile-responsive design

## 📝 Example Output

```
🚀 Starting Multicines scraper with log level: info
🎬 Starting to scrape cinema: Plaza Americas
  🎥 Processing movie card 1/5
    🔗 Movie URL: https://www.multicines.com.ec/movie/123
  → Starting to scrape movie page: https://www.multicines.com.ec/movie/123
  → Movie: Dune: Part Two
  🎬 Found 2 session type containers on the page
  📆 Found month on page: 'mar. 2026'
    → Processing expected day: lun. 2 -> 2026-03-02
      ✅ Scraped: Dune: Part Two at 14:30 on 2026-03-02 (Language: Español)
      ✅ Scraped: Dune: Part Two at 19:45 on 2026-03-02 (Language: Subtitulado)
✅ Scraping completed!
📊 Total screenings (after deduplication): 42

📋 Scraped Screenings:
🎬 Dune: Part Two at Plaza Americas (Español): 14:30 on 2026-03-02
🎬 Dune: Part Two at Plaza Americas (Subtitulado): 19:45 on 2026-03-02
🎬 The Batman at CCI (Español): 16:00 on 2026-03-02
🎬 The Batman at CCI (Subtitulado): 21:15 on 2026-03-02
```

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Submit a pull request

### Development Setup

```bash
# Install dependencies
go mod tidy

# Run tests (when available)
go test ./...

# Build the application
go build -o cine-uio ./backend/main.go
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📬 Contact

For questions or suggestions, please open an issue on GitHub.

---

**Cine-UIO** - Your comprehensive guide to Quito's cinema screenings! 🎥🍿
