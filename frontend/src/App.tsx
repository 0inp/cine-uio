import { useEffect, useMemo, useState } from "react";
import "./App.css";
import apiConfig from "./config";

interface CinemaCompany {
  name: string;
  base_url: string;
}

interface CinemaComplex {
  name: string;
  city: string;
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

interface Health {
  status: "ok" | "stale" | "failing" | "unknown";
  detail: string;
  hours_since_success: number | null;
}

const DEFAULT_CITY = "Quito";
const CITY_STORAGE_KEY = "cine-uio.city";

function storedCity(): string {
  try {
    return localStorage.getItem(CITY_STORAGE_KEY) ?? DEFAULT_CITY;
  } catch {
    return DEFAULT_CITY;
  }
}

function App() {
  const [screenings, setScreenings] = useState<Screening[] | null>(null);
  const [cities, setCities] = useState<string[]>([]);
  const [health, setHealth] = useState<Health | null>(null);
  const [city, setCity] = useState<string>(storedCity);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCities = async () => {
      try {
        const response = await fetch(`${apiConfig.url}/cities`);
        if (!response.ok) return;
        const result = await response.json();
        if (Array.isArray(result)) setCities(result);
      } catch {
        // The city picker is a convenience; failing to list them must not stop
        // the listings from rendering for the currently selected city.
      }
    };
    fetchCities();
  }, []);

  useEffect(() => {
    // Without this the app happily shows week-old listings as if they were today's.
    const fetchHealth = async () => {
      try {
        const response = await fetch(`${apiConfig.url}/health`);
        if (!response.ok) return;
        setHealth(await response.json());
      } catch {
        // If we cannot tell whether the data is fresh, say nothing rather than
        // claiming a problem that may not exist.
      }
    };
    fetchHealth();
  }, []);

  useEffect(() => {
    // Fetch one city at a time: the whole country is tens of thousands of
    // screenings, far too large a payload to filter client-side.
    const fetchScreenings = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(
          `${apiConfig.url}/screenings?city=${encodeURIComponent(city)}`,
        );
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
  }, [city]);

  const selectCity = (next: string) => {
    setCity(next);
    try {
      localStorage.setItem(CITY_STORAGE_KEY, next);
    } catch {
      // Private browsing: the choice simply does not persist.
    }
  };

  const { displayDate, visibleScreenings } = useMemo(() => {
    if (!screenings || screenings.length === 0)
      return { displayDate: null, visibleScreenings: [] };
    const todayEcuador = new Date().toLocaleDateString("en-CA", {
      timeZone: "America/Guayaquil",
    });
    const onDate = (date: string) =>
      screenings.filter((s) => s.datetime.split("T")[0] === date);

    const forToday = onDate(todayEcuador);
    if (forToday.length > 0)
      return { displayDate: null, visibleScreenings: forToday };

    // No screenings today (e.g. scraped in the evening after shows ended).
    // Fall back to the nearest *upcoming* date — never a past one, which would
    // happen whenever the scraper hasn't run in a while and the DB is stale.
    // ISO date strings sort chronologically, so a plain sort is enough.
    const upcoming = screenings
      .map((s) => s.datetime.split("T")[0])
      .filter((date) => date > todayEcuador)
      .sort();
    const earliest = upcoming[0];
    if (!earliest) return { displayDate: null, visibleScreenings: [] };

    return { displayDate: earliest, visibleScreenings: onDate(earliest) };
  }, [screenings]);

  const groupedData = useMemo(() => {
    const result = new Map<string, MovieGroup>();
    for (const screening of visibleScreenings) {
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
  }, [visibleScreenings]);

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
      {health !== null &&
        health.status !== "ok" &&
        health.status !== "unknown" && (
          <p className={`health-notice health-${health.status}`} role="status">
            {health.status === "failing"
              ? "Hubo un problema al actualizar la cartelera"
              : "La cartelera puede estar desactualizada"}
            {health.hours_since_success !== null &&
              ` — última actualización hace ${Math.round(health.hours_since_success)} h`}
          </p>
        )}
      {cities.length > 1 && (
        <div className="city-picker">
          <label htmlFor="city">Ciudad</label>
          <select
            id="city"
            value={city}
            onChange={(e) => selectCity(e.target.value)}
          >
            {cities.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
      )}
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
      {sortedGroups.length === 0 && (
        <p className="empty-notice">No hay funciones disponibles</p>
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
