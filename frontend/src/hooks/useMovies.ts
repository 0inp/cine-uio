// Custom hook for managing movie data
import { createResource, createSignal, createEffect } from "solid-js";
import { Movie, MovieWithScreenings } from "../types/movie";
import { getDateRange } from "../utils/date";

export function useMovies() {
  // Fetch movies from API
  const [movies] = createResource<Movie[]>(async () => {
    try {
      const response = await fetch("http://localhost:8080/api/movies");
      if (!response.ok) throw new Error("Failed to fetch movies");
      return await response.json();
    } catch (error) {
      console.error("Error fetching movies:", error);
      return [];
    }
  });

  // Date selection state
  const [selectedDate, setSelectedDate] = createSignal(new Date());
  const [filteredMovies, setFilteredMovies] = createSignal<MovieWithScreenings[]>([]);
  const [error, setError] = createSignal<string | null>(null);
  const [isLoading, setIsLoading] = createSignal(true);

  // Create date range (today to today + 6 days)
  const dates = getDateRange(new Date(), 7);

  // Filter and organize movies by selected date
  createEffect(() => {
    const rawMovies = movies();
    if (!rawMovies || rawMovies.length === 0) {
      setFilteredMovies([]);
      return;
    }

    const selectedDateStr = selectedDate().toISOString().split('T')[0];

    const filtered = rawMovies
      .map((movie): MovieWithScreenings => {
        const screeningsByLanguage = new Map<string, string[]>();

        movie.screenings.forEach((screening) => {
          const screeningDateStr = screening.date.split('T')[0];
          if (screeningDateStr === selectedDateStr) {
            if (!screeningsByLanguage.has(screening.language)) {
              screeningsByLanguage.set(screening.language, []);
            }
            screeningsByLanguage.get(screening.language)?.push(screening.time);
          }
        });

        const organizedScreenings = Array.from(screeningsByLanguage.entries())
          .map(([language, times]) => ({
            language,
            times: times.sort() // Sort times chronologically
          }))
          .sort((a, b) => a.language.localeCompare(b.language));

        return {
          ...movie,
          screenings: organizedScreenings
        };
      })
      .filter((movie) => movie.screenings.length > 0);

    setFilteredMovies(filtered);
    setIsLoading(false);
  });

  return {
    movies,
    filteredMovies,
    selectedDate,
    setSelectedDate,
    dates,
    error,
    isLoading
  };
}
