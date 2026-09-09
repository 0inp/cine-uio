import { displayTitle } from "../cartelera";
import type { MovieGroup } from "../types";
import { ScreeningItem } from "./ScreeningItem";

interface MovieCardProps {
  group: MovieGroup;
}

export function MovieCard({ group }: MovieCardProps) {
  const { movie, screeningsByVenue } = group;
  const title = displayTitle(movie);
  const releaseYear = movie.release_date?.slice(0, 4);

  return (
    <div className="movie-card">
      <div className="movie-header">
        {movie.poster_url && (
          <img src={movie.poster_url} alt={title} className="movie-poster" />
        )}
        <div className="movie-info">
          <h3 className="movie-title">{title}</h3>
          <div className="movie-meta">
            {movie.certification && (
              <span className="movie-cert">{movie.certification}</span>
            )}
            {movie.runtime && (
              <span className="movie-runtime">{movie.runtime} min</span>
            )}
            {releaseYear && <span className="movie-year">{releaseYear}</span>}
          </div>
          {movie.overview && <p className="movie-overview">{movie.overview}</p>}
        </div>
      </div>
      <div className="movie-venues">
        {Object.entries(screeningsByVenue).map(([venueKey, screenings]) => (
          <div key={venueKey} className="company-complex-section">
            <h4 className="company-complex-name">{venueKey}</h4>
            <div className="screenings-list">
              {screenings.map((screening) => (
                <ScreeningItem key={screening.id} screening={screening} />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
