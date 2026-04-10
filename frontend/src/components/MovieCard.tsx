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
     <div class="relative group rounded-lg shadow-md overflow-hidden transition-all duration-300 hover:shadow-[0_0_0_2px_#fcfbe0]">
       <div
         class="relative z-10 bg-background-light/90 backdrop-blur-sm rounded-lg p-4 space-y-6"
         style={{
           'background-image': props.movie.backdrop_path ? `linear-gradient(rgba(0,0,0,0.9), rgba(0,0,0,0.9)), url(${getBackdropUrl(props.movie.backdrop_path)})` : 'none',
           'background-size': 'cover',
           'background-position': 'center'
         }}
       >
      {/* First Row: Poster + Movie Information (side-by-side on larger screens) */}
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
