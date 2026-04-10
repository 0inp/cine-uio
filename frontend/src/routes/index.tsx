import { For } from "solid-js";
import DaysSlider from "../components/DaysSlider";
import MovieCard from "../components/MovieCard";
import { useMovies } from "../hooks/useMovies";
import { Skeleton } from "../components/Skeleton";

export default function MoviesPage() {
  const { filteredMovies, dates, selectedDate, setSelectedDate, error, isLoading } = useMovies();

  return (
    <main class="container mx-auto px-4 py-8 max-w-5xl text-white min-h-screen">
      <h1 class="text-4xl font-bold text-center mb-8 title-flashy">CINE-UIO</h1>

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
        <div class="space-y-4">
          <Skeleton class="h-64 w-full" />
          <Skeleton class="h-8 w-3/4" />
          <Skeleton class="h-6 w-1/2" />
          <Skeleton class="h-4 w-full" />
          <Skeleton class="h-4 w-5/6" />
        </div>
      ) : filteredMovies().length === 0 ? (
           <div class="text-center py-8 text-gray-400">No movies available for selected date</div>
         ) : (
            <For each={filteredMovies()}>
             {(movie) => <MovieCard movie={movie} />}
           </For>
        )}
      </div>
    </main>
  );
}
