package migrations

import (
	"fmt"

	"gorm.io/gorm"
	"scraper/pkg/database"
)

// SeedCinemaData runs the second migration to populate initial cinema data
func SeedCinemaData(db *gorm.DB) error {
	fmt.Println("🌱 Running migration 002: Seed cinema data...")

	// Check if data already exists
	var count int64
	db.Model(&database.CinemaCompany{}).Count(&count)
	if count > 0 {
		fmt.Println("ℹ️  Cinema data already exists, skipping seed migration")
		return nil
	}

	// Create Multicines company
	multicines := database.CinemaCompany{
		Name:    "Multicines",
		BaseURL: "https://www.multicines.com.ec",
	}
	result := db.Create(&multicines)
	if result.Error != nil {
		return fmt.Errorf("failed to create Multicines company: %w", result.Error)
	}

	// Create Supercines company
	supercines := database.CinemaCompany{
		Name:    "Supercines",
		BaseURL: "https://www.supercines.com",
	}
	result = db.Create(&supercines)
	if result.Error != nil {
		return fmt.Errorf("failed to create Supercines company: %w", result.Error)
	}

	// Create cinemas for Multicines
	multicinesCinemas := []database.Cinema{
		{Name: "Plaza Americas", StoreID: "3566", CompanyName: "Multicines", CompanyID: multicines.ID},
		{Name: "CCI", StoreID: "3555", CompanyName: "Multicines", CompanyID: multicines.ID},
	}

	for _, cinema := range multicinesCinemas {
		result := db.Create(&cinema)
		if result.Error != nil {
			return fmt.Errorf("failed to create cinema %s: %w", cinema.Name, result.Error)
		}
		fmt.Printf("✅ Created cinema: %s (StoreID: %s)\n", cinema.Name, cinema.StoreID)
	}

	fmt.Println("✅ Migration 002 completed: Cinema data seeded successfully!")
	return nil
}
