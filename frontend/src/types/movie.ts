// Movie-related types for the cine-uio application
export interface Screening {
  date: string;
  language: string;
  time: string;
}

export interface OrganizedScreening {
  language: string;
  times: string[];
}

export interface BaseMovie {
  title: string;
  duration?: number; // Duration in minutes
  overview?: string;
  poster_path?: string;
  backdrop_path?: string;
  original_title?: string;
  vote_average?: number;
}

export interface Movie extends BaseMovie {
  screenings: Screening[];
}

export interface MovieWithScreenings extends BaseMovie {
  screenings: OrganizedScreening[];
}

export interface TMDBConfig {
  base_url: string;
  secure_base_url: string;
  backdrop_sizes: string[];
  poster_sizes: string[];
}

export type MovieTransformer = (movie: Movie) => MovieWithScreenings;
