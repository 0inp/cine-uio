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
      <div class="p-6">
        <div class="flex flex-col md:flex-row gap-6">
          {/* Poster Image - Left Column */}
          {props.movie.poster_path && (
            <div class="flex-shrink-0 w-full md:w-48">
               <img
                 src={getPosterUrl(props.movie.poster_path)}
                 alt={props.movie.spanish_title || props.movie.scraped_title}
                 class="w-full h-auto rounded-lg shadow-md object-cover aspect-[2/3]"
               />
            </div>
          )}

          {/* Movie Details - Right Column */}
          <div class="flex-1 flex flex-col">
            <MovieDetails movie={props.movie} />

            {/* Screenings organized by cinema */}
            <div class="space-y-3 mt-4 flex-1">
              <For each={props.movie.screenings}>
                {(cinemaGroup) => <CinemaScreeningGroup group={cinemaGroup} />}
              </For>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MovieCard;
