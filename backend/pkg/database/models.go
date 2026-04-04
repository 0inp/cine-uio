package database

import (
	"time"
)

// CinemaCompany represents a cinema company (e.g., Multicines, Supercines)
type CinemaCompany struct {
	ID        uint      `gorm:"primaryKey"`
	Name      string    `gorm:"unique;not null"`
	BaseURL   string    `gorm:"not null"`
	CreatedAt time.Time `gorm:"autoCreateTime"`
	UpdatedAt time.Time `gorm:"autoUpdateTime"`
	Cinemas   []Cinema  `gorm:"foreignKey:CompanyID"`
}

// Cinema represents an individual cinema location
type Cinema struct {
	ID          uint      `gorm:"primaryKey"`
	CompanyID   uint      `gorm:"not null"`
	Name        string    `gorm:"not null"`
	StoreID     string    `gorm:"not null"`
	CompanyName string    `gorm:"not null"`
	CreatedAt   time.Time `gorm:"autoCreateTime"`
	UpdatedAt   time.Time `gorm:"autoUpdateTime"`
}

// Movie represents a movie that can be screened
type Movie struct {
	ID         uint        `gorm:"primaryKey"`
	Title      string      `gorm:"unique;not null"`
	CreatedAt  time.Time   `gorm:"autoCreateTime"`
	UpdatedAt  time.Time   `gorm:"autoUpdateTime"`
	Screenings []Screening `gorm:"foreignKey:MovieID"`
}

// Screening represents a screening time for a movie at a specific cinema
type Screening struct {
	ID        uint      `gorm:"primaryKey"`
	MovieID   uint      `gorm:"not null"`
	CinemaID  uint      `gorm:"not null"`
	Date      time.Time `gorm:"not null"`
	Time      string    `gorm:"not null"`
	Language  string    `gorm:"not null"`
	CreatedAt time.Time `gorm:"autoCreateTime"`
	UpdatedAt time.Time `gorm:"autoUpdateTime"`
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
