import { Component } from "solid-js";
import { MovieWithScreenings } from "../types/movie";
import { ClockIcon, StarIcon } from "./icons";

interface MovieDetailsProps {
  movie: MovieWithScreenings;
}

const MovieDetails: Component<MovieDetailsProps> = (props) => {
  return (
    <div class="mb-4">
      <h2 class="text-xl font-semibold text-white border-b border-gray-400 pb-2 mb-2">
        {props.movie.spanish_title || props.movie.scraped_title}
        {props.movie.original_title && props.movie.spanish_title && props.movie.original_title !== props.movie.spanish_title && (
          <span class="text-sm font-normal text-gray-300 ml-2">
            ({props.movie.original_title})
          </span>
        )}
      </h2>

      <div class="space-y-2 text-sm">
        {props.movie.duration && (
          <div class="flex items-center text-gray-200">
            <ClockIcon />
            <span>{Math.floor(props.movie.duration / 60)}h {props.movie.duration % 60}min</span>
          </div>
        )}

        {props.movie.vote_average && (
          <div class="flex items-center text-gray-200">
            <StarIcon />
            <span>{props.movie.vote_average.toFixed(1)} ★</span>
          </div>
        )}

        {props.movie.overview && (
          <div class="text-gray-200 mt-2">
            <p class="text-sm leading-relaxed">{props.movie.overview}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default MovieDetails;
