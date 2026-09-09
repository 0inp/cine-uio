export interface CinemaCompany {
  name: string;
  base_url: string;
}

export interface CinemaComplex {
  name: string;
  city: string;
  url_part: string;
  company: CinemaCompany;
}

export interface Movie {
  title: string;
  tmdb_id?: number | null;
  tmdb_title?: string | null;
  poster_url?: string | null;
  overview?: string | null;
  runtime?: number | null;
  certification?: string | null;
  release_date?: string | null;
}

export interface Screening {
  id: number;
  datetime: string;
  format: string;
  language: string;
  complex: CinemaComplex;
  movie: Movie;
}

export interface Health {
  status: "ok" | "stale" | "failing" | "unknown";
  detail: string;
  hours_since_success: number | null;
}

/** One movie's showings for a day, split by the venue showing them. */
export interface MovieGroup {
  movie: Movie;
  screeningsByVenue: Record<string, Screening[]>;
}
