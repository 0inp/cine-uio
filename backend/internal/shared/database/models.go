package database

import "time"

// BaseModel contains common fields for all database models
type BaseModel struct {
	ID        uint      `gorm:"primaryKey"`
	CreatedAt time.Time `gorm:"autoCreateTime"`
	UpdatedAt time.Time `gorm:"autoUpdateTime"`
}

// CinemaCompany represents a cinema company (e.g., Multicines, Supercines)
type CinemaCompany struct {
	BaseModel
	Name    string   `gorm:"unique;not null"`
	BaseURL string   `gorm:"not null"`
	Cinemas []Cinema `gorm:"foreignKey:CompanyID"`
}

// Cinema represents an individual cinema location
type Cinema struct {
	BaseModel
	CompanyID uint   `gorm:"not null"`
	Name      string `gorm:"not null"`
	StoreID   string `gorm:"not null"`
}

// Movie represents a movie that can be screened
type Movie struct {
	BaseModel
	Title      string      `gorm:"unique;not null"`
	Duration   *int        `gorm:"default:null"` // Duration in minutes
	Screenings []Screening `gorm:"foreignKey:MovieID"`
}

// Screening represents a screening time for a movie at a specific cinema
type Screening struct {
	BaseModel
	MovieID  uint      `gorm:"not null"`
	CinemaID uint      `gorm:"not null"`
	Date     time.Time `gorm:"not null"`
	Time     string    `gorm:"not null"`
	Language string    `gorm:"not null"`
}

// TableName overrides for explicit table naming
// CinemaCompany.TableName returns the database table name for CinemaCompany.
func (CinemaCompany) TableName() string {
	return "cinema_companies"
}

// TableName returns the database table name for Cinema.
func (Cinema) TableName() string {
	return "cinemas"
}

// TableName returns the database table name for Movie.
func (Movie) TableName() string {
	return "movies"
}

// TableName returns the database table name for Screening.
func (Screening) TableName() string {
	return "screening_times"
}
