import { Component, For } from "solid-js";
import { MovieWithScreenings } from "../types/movie";
import { getBackdropUrl, getPosterUrl } from "../utils/tmdb";
import CinemaScreeningGroup from "./CinemaScreeningGroup";
import MovieDetails from "./MovieDetails";

interface MovieCardProps {
  movie: MovieWithScreenings;
}

const MovieCard: Component<MovieCardProps> = (props) => {
  return (
    <div class="relative group rounded-lg shadow-md overflow-hidden transition-all duration-300 hover:shadow-[0_0_0_1px_#fcfbe0]">
      {/* Background image layer (blurred) */}
      {props.movie.backdrop_path && (
        <div
          class="absolute inset-0 z-10"
          style={{
            'background-image': `url(${getBackdropUrl(props.movie.backdrop_path)})`,
            'background-size': 'cover',
            'background-position': 'center',
          }}
        />
      )}

      {/* Content layer (not blurred) */}
      <div class="relative z-20 bg-background-light/80 backdrop-blur-xs rounded-lg p-4 space-y-6">
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
          <div class="flex-1">
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
  );
};

export default MovieCard;
