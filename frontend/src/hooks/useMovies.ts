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
        // Group screenings by cinema first, then by language, preserving URLs
        const screeningsByCinema = new Map<string, Map<string, {time: string, url?: string}[]>>();

        movie.screenings.forEach((screening) => {
          const screeningDateStr = screening.date.split('T')[0];
          if (screeningDateStr === selectedDateStr) {
            if (!screeningsByCinema.has(screening.cinema)) {
              screeningsByCinema.set(screening.cinema, new Map<string, {time: string, url?: string}[]>());
            }
            const cinemaLanguages = screeningsByCinema.get(screening.cinema);
            if (!cinemaLanguages?.has(screening.language)) {
              cinemaLanguages?.set(screening.language, []);
            }
            cinemaLanguages?.get(screening.language)?.push({
              time: screening.time,
              url: screening.url
            });
          }
        });

        // Convert to the new cinema-based structure
        const organizedScreenings = Array.from(screeningsByCinema.entries())
          .map(([cinema, languagesMap]) => ({
            cinema,
            languages: Array.from(languagesMap.entries())
              .map(([language, screenings]) => ({
                language,
                times: screenings.map(s => s.time).sort(), // Sort times chronologically
                url: screenings[0]?.url // Use URL from first screening (all same language screenings should have same URL)
              }))
              .sort((a, b) => a.language.localeCompare(b.language))
          }))
          .sort((a, b) => a.cinema.localeCompare(b.cinema));

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
