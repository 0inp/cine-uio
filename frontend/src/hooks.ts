import { useEffect, useState } from "react";
import { fetchCities, fetchHealth, fetchScreenings } from "./api";
import type { Health, Position, Screening } from "./types";

export type Theme = "light" | "dark";

const THEME_STORAGE_KEY = "cine-uio.theme";
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

function systemTheme(): Theme {
  // jsdom and older browsers have no matchMedia; light is the safer assumption
  // because the stylesheet's base palette is the light one.
  if (typeof window === "undefined" || !window.matchMedia) return "light";
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

function storedTheme(): Theme | null {
  try {
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    return stored === "light" || stored === "dark" ? stored : null;
  } catch {
    return null;
  }
}

/**
 * The active theme and a way to flip it.
 *
 * Starts from the reader's system preference and only departs from it once they
 * ask: an explicit choice is remembered and wins over the system from then on.
 */
export function useTheme(): [Theme, () => void] {
  const [theme, setTheme] = useState<Theme>(
    () => storedTheme() ?? systemTheme(),
  );

  useEffect(() => {
    // The stylesheet keys off this attribute; nothing else needs to know.
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  const toggleTheme = () => {
    const next: Theme = theme === "dark" ? "light" : "dark";
    setTheme(next);
    try {
      localStorage.setItem(THEME_STORAGE_KEY, next);
    } catch {
      // Private browsing: the choice applies now but does not persist.
    }
  };

  return [theme, toggleTheme];
}

export type GeolocationStatus = "idle" | "asking" | "granted" | "denied";

export interface GeolocationState {
  position: Position | null;
  status: GeolocationStatus;
  request: () => void;
  available: boolean;
}

/**
 * The reader's position, only ever after they ask for it.
 *
 * Nothing is requested on load: a page that pops a location prompt before being
 * asked is one people dismiss reflexively, and a dismissed prompt is hard to undo.
 */
export function useGeolocation(): GeolocationState {
  const [position, setPosition] = useState<Position | null>(null);
  const [status, setStatus] = useState<GeolocationStatus>("idle");

  const available =
    typeof navigator !== "undefined" && navigator.geolocation !== undefined;

  const request = () => {
    if (!available) return;
    setStatus("asking");
    navigator.geolocation.getCurrentPosition(
      (result) => {
        setPosition({
          latitude: result.coords.latitude,
          longitude: result.coords.longitude,
        });
        setStatus("granted");
      },
      () => {
        // Refused, unavailable, or timed out — all the same to the page: it
        // carries on without distances.
        setStatus("denied");
      },
      { timeout: 10_000, maximumAge: 5 * 60_000 },
    );
  };

  return { position, status, request, available };
}
