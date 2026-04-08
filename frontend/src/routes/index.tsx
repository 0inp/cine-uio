import { createResource, For, createSignal, createEffect } from "solid-js";
import DaysSlider from "../components/DaysSlider";
interface Screening {
  date: string;
  language: string;
  time: string;
}
interface Movie {
  title: string;
  duration?: number; // Duration in minutes
  screenings: Screening[];
}
interface OrganizedScreening {
  language: string;
  times: string[];
}
interface MovieWithScreenings {
  title: string;
  duration?: number; // Duration in minutes
  screenings: OrganizedScreening[];
}
export default function MoviesPage() {
  // Fetch movie data from Go backend API
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
  // Create date range (today to today + 6 days)
  const today = new Date();
  const dates = Array.from({ length: 7 }, (_, i) => {
    const date = new Date(today);
    date.setDate(today.getDate() + i);
    return date;
  });
  // Selected date state
  const [selectedDate, setSelectedDate] = createSignal(today);
  // Filter and organize movies by selected date
  const [filteredMovies, setFilteredMovies] = createSignal<MovieWithScreenings[]>([]);
  createEffect(() => {
    const rawMovies = movies();
    if (!rawMovies || rawMovies.length === 0) return;
    const selected = selectedDate();
    const selectedDateStr = selected.toISOString().split('T')[0]; // Format: YYYY-MM-DD
    const filtered = rawMovies
      .map((movie: Movie): MovieWithScreenings => {
        const screeningsByLanguage = new Map<string, string[]>();
        movie.screenings.forEach((screening: Screening) => {
          const screeningDateStr = screening.date.split('T')[0];
          if (screeningDateStr === selectedDateStr) {
            if (!screeningsByLanguage.has(screening.language)) {
              screeningsByLanguage.set(screening.language, []);
            }
            screeningsByLanguage.get(screening.language)?.push(screening.time);
          }
        });
        const organizedScreenings: OrganizedScreening[] = Array.from(screeningsByLanguage.entries())
          .map(([language, times]) => ({
            language,
            times: times.sort() // Sort times chronologically
          }))
          .sort((a, b) => a.language.localeCompare(b.language));
        return {
          title: movie.title,
          duration: movie.duration,
          screenings: organizedScreenings
        };
      })
      .filter((movie: MovieWithScreenings) => movie.screenings.length > 0);
    setFilteredMovies(filtered);
  });
  return (
    <main class="container mx-auto px-4 py-8 max-w-4xl">
      <h1 class="text-4xl font-bold text-center mb-8 text-sky-700">cine-uio</h1>
      <DaysSlider
        dates={dates}
        selectedDate={selectedDate()}
        onDateSelect={setSelectedDate}
      />
      <div class="space-y-6">
        <For each={filteredMovies()} fallback={<div class="text-center py-8">Loading movies...</div>}>
          {(movie: MovieWithScreenings) => (
            <div class="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
              <div class="p-6">
                <div class="flex justify-between items-start mb-4">
                  <h2 class="text-xl font-semibold text-gray-800 border-b pb-2 flex-1">{movie.title}</h2>
                  {movie.duration && (
                    <span class="text-sm text-gray-500 ml-4 whitespace-nowrap">
                      {Math.floor(movie.duration / 60)}h {movie.duration % 60}min
                    </span>
                  )}
                </div>
                {/* Screenings organized by language */}
                <div class="space-y-3">
                  <For each={movie.screenings}>
                    {(screeningGroup: OrganizedScreening) => (
                      <div class="bg-gray-50 rounded-lg p-3">
                        <div class="flex items-center mb-2">
                          <span class="font-medium text-gray-700 uppercase text-sm">{screeningGroup.language}</span>
                        </div>
                        <div class="flex flex-wrap gap-2">
                          <For each={screeningGroup.times}>
                            {(time: string) => (
                              <span class="px-3 py-1 bg-white rounded border text-sm text-gray-600">{time}</span>
                            )}
                          </For>
                        </div>
                      </div>
                    )}
                  </For>
                </div>
              </div>
            </div>
          )}
        </For>
      </div>
    </main>
  );
}
