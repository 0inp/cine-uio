import { For } from "solid-js";
import DaysSlider from "../components/DaysSlider";
import MovieCard from "../components/MovieCard";
import { useMovies } from "../hooks/useMovies";

export default function MoviesPage() {
  const { filteredMovies, dates, selectedDate, setSelectedDate, error, isLoading } = useMovies();

  return (
    <main class="container mx-auto px-4 py-8 max-w-4xl">
      <h1 class="text-4xl font-bold text-center mb-8 text-sky-700">cine-uio</h1>

      <DaysSlider
        dates={dates}
        selectedDate={selectedDate()}
        onDateSelect={setSelectedDate}
      />

      {error() && (
        <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
          <strong class="font-bold">Error!</strong>
          <span class="block sm:inline"> {error()}</span>
        </div>
      )}

      <div class="space-y-6 mt-6">
        {isLoading() ? (
          <div class="text-center py-8">Loading movies...</div>
        ) : filteredMovies().length === 0 ? (
          <div class="text-center py-8 text-gray-500">No movies available for selected date</div>
        ) : (
          <For each={filteredMovies()}>
            {(movie) => <MovieCard movie={movie} />}
          </For>
        )}
      </div>
    </main>
  );
}
