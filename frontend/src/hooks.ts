import { useEffect, useState } from "react";
import { fetchCities, fetchHealth, fetchScreenings } from "./api";
import type { Health, Screening } from "./types";

const DEFAULT_CITY = "Quito";
const CITY_STORAGE_KEY = "cine-uio.city";

function storedCity(): string {
  try {
    return localStorage.getItem(CITY_STORAGE_KEY) ?? DEFAULT_CITY;
  } catch {
    return DEFAULT_CITY;
  }
}

/** The chosen city, remembered between visits where storage allows it. */
export function useCityPreference(): [string, (next: string) => void] {
  const [city, setCity] = useState<string>(storedCity);

  const selectCity = (next: string) => {
    setCity(next);
    try {
      localStorage.setItem(CITY_STORAGE_KEY, next);
    } catch {
      // Private browsing: the choice simply does not persist.
    }
  };

  return [city, selectCity];
}

export function useCities(): string[] {
  const [cities, setCities] = useState<string[]>([]);
  useEffect(() => {
    fetchCities().then(setCities);
  }, []);
  return cities;
}

export function useHealth(): Health | null {
  const [health, setHealth] = useState<Health | null>(null);
  useEffect(() => {
    fetchHealth().then(setHealth);
  }, []);
  return health;
}

export interface CarteleraState {
  screenings: Screening[] | null;
  loading: boolean;
  error: string | null;
}

/** One city's listings, refetched whenever the city changes. */
export function useCartelera(city: string): CarteleraState {
  const [screenings, setScreenings] = useState<Screening[] | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let current = true;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await fetchScreenings(city);
        if (current) setScreenings(result);
      } catch (err) {
        if (current)
          setError(
            err instanceof Error ? err.message : "An unknown error occurred",
          );
      } finally {
        if (current) setLoading(false);
      }
    };

    load();
    return () => {
      // Switching city twice quickly must not let the first answer overwrite the
      // second: whichever request resolves last would otherwise win.
      current = false;
    };
  }, [city]);

  return { screenings, loading, error };
}
