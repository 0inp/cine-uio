import { Component, For } from "solid-js";
import { MovieWithScreenings } from "~/types/movie";
import { getBackdropUrl, getPosterUrl } from "~/utils/tmdb";
import CinemaScreeningGroup from "./CinemaScreeningGroup";
import MovieDetails from "./MovieDetails";

interface MovieCardProps {
  movie: MovieWithScreenings;
}

const MovieCard: Component<MovieCardProps> = (props) => {
  return (
    <div class="group rounded-lg shadow-md transition-all duration-300 hover:ring-1 hover:ring-card-border w-full">
      {/* Background with backdrop image */}
      <div class="relative rounded-lg overflow-hidden">
        {props.movie.backdrop_path && (
          <div
            class="absolute inset-0 z-0"
            style={{
              'background-image': `url(${getBackdropUrl(props.movie.backdrop_path)})`,
              'background-size': 'cover',
              'background-position': 'center',
              'filter': 'blur(8px)',
            }}
          />
        )}

        {/* Content layer */}
        <div class="relative z-10 bg-background-light/80 backdrop-blur-sm p-4 space-y-6">
          {/* First Row: Poster + Movie Information */}
          <div class="flex flex-col md:flex-row gap-6">
            {/* Poster Image - Only visible on laptop and desktop (769px+) */}
            {props.movie.poster_path && (
              <div class="flex-shrink-0 w-full md:w-48 mx-auto md:mx-0 hidden md:block">
                <img
                  src={getPosterUrl(props.movie.poster_path)}
                  alt={props.movie.spanish_title || props.movie.scraped_title}
                  class="w-full h-auto rounded-lg shadow-md object-cover aspect-[2/3]"
                />
              </div>
            )}

            {/* Movie Details */}
            <div class="flex-1 min-w-0">
              <MovieDetails movie={props.movie} />
            </div>
          </div>

          {/* Second Row: Screenings organized by cinema */}
          <div class="space-y-4">
            <For each={props.movie.screenings}>
              {(cinemaGroup) => (
                <CinemaScreeningGroup group={cinemaGroup} />
              )}
            </For>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MovieCard;
