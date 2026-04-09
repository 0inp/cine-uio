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
    <div
      class="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow relative"
      style={
        props.movie.backdrop_path ? {
          'background-image': `linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url(${getBackdropUrl(props.movie.backdrop_path)})`,
          'background-size': 'cover',
          'background-position': 'center'
        } : {}
      }
    >
      <div class="p-4 sm:p-6">
        {/* First Row: Poster + Movie Information (side-by-side on larger screens) */}
        <div class="flex flex-col md:flex-row gap-6 mb-6">
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

          {/* Movie Details - Full width on mobile, side-by-side on larger screens */}
          <div class="flex-1">
            <MovieDetails movie={props.movie} />
          </div>
        </div>

        {/* Second Row: Screenings organized by cinema */}
        <div class="space-y-4">
          <For each={props.movie.screenings}>
            {(cinemaGroup) => {
              return (
                <CinemaScreeningGroup
                  group={cinemaGroup}
                />
              );
            }}
          </For>
        </div>
      </div>
    </div>
  );
};

export default MovieCard;
