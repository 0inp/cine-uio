import { useEffect, useMemo, useState } from "react";
import "./App.css";
import apiConfig from "./config";

interface CinemaCompany {
  name: string;
  base_url: string;
}

interface CinemaComplex {
  name: string;
  url_part: string;
  company: CinemaCompany;
}

interface Movie {
  title: string;
  tmdb_id?: number | null;
  tmdb_title?: string | null;
  poster_url?: string | null;
  overview?: string | null;
  runtime?: number | null;
  certification?: string | null;
  release_date?: string | null;
}

interface Screening {
  id: number;
  datetime: string;
  format: string;
  language: string;
  complex: CinemaComplex;
  movie: Movie;
}

interface ScreeningItemProps {
  screening: Screening;
}

export function ScreeningItem({ screening }: ScreeningItemProps) {
  return (
    <div className="screening-item">
      <span className="screening-time">
        {new Date(screening.datetime).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        })}
      </span>
      <span className="screening-format">{screening.format}</span>
      <span className="screening-language">{screening.language}</span>
    </div>
  );
}

interface MovieGroup {
  movie: Movie;
  screeningsByVenue: Record<string, Screening[]>;
}

function movieKey(movie: Movie): string {
  return movie.tmdb_id != null
    ? `tmdb-${movie.tmdb_id}`
    : `title-${movie.title}`;
}

function displayTitle(movie: Movie): string {
  return movie.tmdb_title ?? movie.title;
}

function App() {
  const [screenings, setScreenings] = useState<Screening[] | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchScreenings = async () => {
      try {
        const response = await fetch(`${apiConfig.url}/screenings`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();
        if (!Array.isArray(result)) {
          throw new Error("API response is not an array of screenings.");
        }
        setScreenings(result);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "An unknown error occurred",
        );
      } finally {
        setLoading(false);
      }
    };

    fetchScreenings();
  }, []);

  const { displayDate, todaysScreenings } = useMemo(() => {
    if (!screenings || screenings.length === 0)
      return { displayDate: null, todaysScreenings: [] };
    const todayEcuador = new Date().toLocaleDateString("en-CA", {
      timeZone: "America/Guayaquil",
    });
    const forToday = screenings.filter(
      (s) => s.datetime.split("T")[0] === todayEcuador,
    );
    if (forToday.length > 0)
      return { displayDate: null, todaysScreenings: forToday };
    // No screenings for today (e.g. scraped in the evening after shows ended).
    // Fall back to the earliest available date.
    const earliest = screenings.map((s) => s.datetime.split("T")[0]).sort()[0];
    return {
      displayDate: earliest,
      todaysScreenings: screenings.filter(
        (s) => s.datetime.split("T")[0] === earliest,
      ),
    };
  }, [screenings]);

  const groupedData = useMemo(() => {
    const result = new Map<string, MovieGroup>();
    for (const screening of todaysScreenings) {
      const key = movieKey(screening.movie);
      const venueKey = `${screening.complex.company.name} - ${screening.complex.name}`;
      let group = result.get(key);
      if (!group) {
        group = { movie: screening.movie, screeningsByVenue: {} };
        result.set(key, group);
      }
      const venue = group.screeningsByVenue;
      if (!venue[venueKey]) venue[venueKey] = [];
      venue[venueKey].push(screening);
    }
    return result;
  }, [todaysScreenings]);

  const sortedGroups = useMemo(
    () =>
      Array.from(groupedData.values()).sort((a, b) =>
        displayTitle(a.movie).localeCompare(displayTitle(b.movie)),
      ),
    [groupedData],
  );

  if (loading) return <div className="loading">Loading...</div>;
  if (error) return <div className="error">Error: {error}</div>;
  if (!screenings) return <div className="no-data">No data available</div>;

  return (
    <div className="app">
      <h1 className="title">Cine UIO</h1>
      {displayDate && (
        <p className="date-notice">
          Sin funciones para hoy —{" "}
          {new Date(`${displayDate}T12:00:00`).toLocaleDateString("es-EC", {
            weekday: "long",
            day: "numeric",
            month: "long",
          })}
        </p>
      )}
      {sortedGroups.map((group) => {
        const key = movieKey(group.movie);
        const title = displayTitle(group.movie);
        const releaseYear = group.movie.release_date?.slice(0, 4);

        return (
          <div key={key} className="movie-card">
            <div className="movie-header">
              {group.movie.poster_url && (
                <img
                  src={group.movie.poster_url}
                  alt={title}
                  className="movie-poster"
                />
              )}
              <div className="movie-info">
                <h3 className="movie-title">{title}</h3>
                <div className="movie-meta">
                  {group.movie.certification && (
                    <span className="movie-cert">
                      {group.movie.certification}
                    </span>
                  )}
                  {group.movie.runtime && (
                    <span className="movie-runtime">
                      {group.movie.runtime} min
                    </span>
                  )}
                  {releaseYear && (
                    <span className="movie-year">{releaseYear}</span>
                  )}
                </div>
                {group.movie.overview && (
                  <p className="movie-overview">{group.movie.overview}</p>
                )}
              </div>
            </div>
            <div className="movie-venues">
              {Object.entries(group.screeningsByVenue).map(
                ([venueKey, slotScreenings]) => (
                  <div key={venueKey} className="company-complex-section">
                    <h4 className="company-complex-name">{venueKey}</h4>
                    <div className="screenings-list">
                      {slotScreenings.map((s) => (
                        <ScreeningItem key={s.id} screening={s} />
                      ))}
                    </div>
                  </div>
                ),
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default App;
