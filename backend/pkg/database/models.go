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
	CompanyID   uint   `gorm:"not null"`
	Name        string `gorm:"not null"`
	StoreID     string `gorm:"not null"`
	CompanyName string `gorm:"not null"`
}

// Movie represents a movie that can be screened
type Movie struct {
	BaseModel
	Title      string      `gorm:"unique;not null"`
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
func (CinemaCompany) TableName() string {
	return "cinema_companies"
}

func (Cinema) TableName() string {
	return "cinemas"
}

func (Movie) TableName() string {
	return "movies"
}

func (Screening) TableName() string {
	return "screening_times"
}
