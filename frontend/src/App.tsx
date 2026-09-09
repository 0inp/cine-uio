import { useMemo } from "react";
import "./App.css";
import {
  groupByMovie,
  movieKey,
  pickVisibleDay,
  todayInEcuador,
} from "./cartelera";
import { CityPicker } from "./components/CityPicker";
import { HealthBanner } from "./components/HealthBanner";
import { MovieCard } from "./components/MovieCard";
import { useCartelera, useCities, useCityPreference, useHealth } from "./hooks";

function App() {
  const [city, selectCity] = useCityPreference();
  const cities = useCities();
  const health = useHealth();
  const { screenings, loading, error } = useCartelera(city);

  const { displayDate, groups } = useMemo(() => {
    const day = pickVisibleDay(screenings ?? [], todayInEcuador());
    return {
      displayDate: day.displayDate,
      groups: groupByMovie(day.screenings),
    };
  }, [screenings]);

  if (loading) return <div className="loading">Loading...</div>;
  if (error) return <div className="error">Error: {error}</div>;
  if (!screenings) return <div className="no-data">No data available</div>;

  return (
    <div className="app">
      <h1 className="title">Cine UIO</h1>
      <HealthBanner health={health} />
      <CityPicker cities={cities} city={city} onSelect={selectCity} />
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
      {groups.length === 0 && (
        <p className="empty-notice">No hay funciones disponibles</p>
      )}
      {groups.map((group) => (
        <MovieCard key={movieKey(group.movie)} group={group} />
      ))}
    </div>
  );
}

export default App;
