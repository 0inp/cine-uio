package models

import "time"

type CinemaCompany struct {
	Name    string
	BaseURL string
	Cinemas []Cinema
}

type Cinema struct {
	ID          int
	Name        string
	StoreID     string
	CompanyName string
}

type Movie struct {
	Title string
}

type Screening struct {
	Movie    Movie
	Cinema   Cinema
	Date     time.Time
	Time     string
	Language string
}
