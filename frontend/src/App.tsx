import { useMemo, useState } from "react";
import "./App.css";
import {
  availableDays,
  availableVenues,
  defaultDay,
  filterScreenings,
  groupByMovie,
  movieKey,
  todayInEcuador,
} from "./cartelera";
import { CityPicker } from "./components/CityPicker";
import { DayPicker } from "./components/DayPicker";
import { HealthBanner } from "./components/HealthBanner";
import { MovieCard } from "./components/MovieCard";
import { VenueFilter } from "./components/VenueFilter";
import { useCartelera, useCities, useCityPreference, useHealth } from "./hooks";

function App() {
  const [city, selectCity] = useCityPreference();
  const cities = useCities();
  const health = useHealth();
  const { screenings, loading, error } = useCartelera(city);

  const [chosenDay, setChosenDay] = useState<string | null>(null);
  const [chosenVenues, setChosenVenues] = useState<string[]>([]);

  const today = todayInEcuador();
  const all = useMemo(() => screenings ?? [], [screenings]);
  const days = useMemo(() => availableDays(all, today), [all, today]);
  const venues = useMemo(() => availableVenues(all), [all]);

  // Derived rather than reset in an effect: changing city can leave a day or a
  // venue that no longer exists selected, and the fallback handles it in one place.
  const day =
    chosenDay !== null && days.includes(chosenDay)
      ? chosenDay
      : defaultDay(days, today);
  const venueKeys = chosenVenues.filter((key) =>
    venues.some((venue) => venue.key === key),
  );

  // No offerable day means nothing to show. `day: null` reads as "no day filter"
  // to filterScreenings, which on a stale database would put the past back on
  // screen — the one thing availableDays exists to prevent.
  const groups = useMemo(
    () =>
      day === null
        ? []
        : groupByMovie(filterScreenings(all, { day, venueKeys })),
    [all, day, venueKeys],
  );

  if (loading) return <div className="loading">Loading...</div>;
  if (error) return <div className="error">Error: {error}</div>;
  if (!screenings) return <div className="no-data">No data available</div>;

  return (
    <div className="app">
      <h1 className="title">Cine UIO</h1>
      <HealthBanner health={health} />
      <CityPicker cities={cities} city={city} onSelect={selectCity} />
      <DayPicker days={days} day={day} today={today} onSelect={setChosenDay} />
      <VenueFilter
        venues={venues}
        selected={chosenVenues}
        onChange={setChosenVenues}
      />
      {day !== null && day !== today && (
        <p className="date-notice">
          Sin funciones para hoy —{" "}
          {new Date(`${day}T12:00:00`).toLocaleDateString("es-EC", {
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
