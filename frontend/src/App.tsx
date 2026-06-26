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

  const todaysScreenings = useMemo(() => {
    if (!screenings) return [];
    const todayEcuador = new Date().toLocaleDateString("en-CA", {
      timeZone: "America/Guayaquil",
    });
    return screenings.filter((s) => s.datetime.split("T")[0] === todayEcuador);
  }, [screenings]);

  const groupedData = useMemo(
    () =>
      todaysScreenings.reduce(
        (acc, screening) => {
          const movieTitle = screening.movie.title;
          const companyComplexKey = `${screening.complex.company.name} - ${screening.complex.name}`;
          if (!acc[movieTitle]) acc[movieTitle] = {};
          if (!acc[movieTitle][companyComplexKey])
            acc[movieTitle][companyComplexKey] = [];
          acc[movieTitle][companyComplexKey].push(screening);
          return acc;
        },
        {} as Record<string, Record<string, Screening[]>>,
      ),
    [todaysScreenings],
  );

  const sortedMovieTitles = useMemo(
    () => Object.keys(groupedData).sort((a, b) => a.localeCompare(b)),
    [groupedData],
  );

  if (loading) return <div className="loading">Loading...</div>;
  if (error) return <div className="error">Error: {error}</div>;
  if (!screenings) return <div className="no-data">No data available</div>;

  return (
    <div className="app">
      <h1 className="title">Cine UIO</h1>
      {sortedMovieTitles.map((movieTitle) => (
        <div key={movieTitle} className="movie-card">
          <h3 className="movie-title">{movieTitle}</h3>
          {Object.entries(groupedData[movieTitle]).map(
            ([companyComplexKey, slotScreenings]) => (
              <div
                key={`${movieTitle}-${companyComplexKey}`}
                className="company-complex-section"
              >
                <h4 className="company-complex-name">{companyComplexKey}</h4>
                <div className="screenings-list">
                  {slotScreenings.map((s) => (
                    <ScreeningItem key={s.id} screening={s} />
                  ))}
                </div>
              </div>
            ),
          )}
        </div>
      ))}
    </div>
  );
}

export default App;
