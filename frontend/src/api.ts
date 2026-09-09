import apiConfig from "./config";
import type { Health, Screening } from "./types";

/**
 * Screenings for one city.
 *
 * One city at a time on purpose: the whole country runs to tens of thousands of
 * rows, far too large a payload to fetch and filter client-side.
 *
 * Throws — the listings are the page, so a failure here is worth showing.
 */
export async function fetchScreenings(city: string): Promise<Screening[]> {
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
  return result;
}

/**
 * The cities that have listings, or an empty list if they cannot be fetched.
 *
 * Never throws: the picker is a convenience, and failing to list cities must not
 * stop the currently selected city's listings from rendering.
 */
export async function fetchCities(): Promise<string[]> {
  try {
    const response = await fetch(`${apiConfig.url}/cities`);
    if (!response.ok) return [];
    const result = await response.json();
    return Array.isArray(result) ? result : [];
  } catch {
    return [];
  }
}

/**
 * Whether the listings can be trusted, or null if that cannot be determined.
 *
 * Never throws: if we cannot tell whether the data is fresh, the page says
 * nothing rather than claiming a problem that may not exist.
 */
export async function fetchHealth(): Promise<Health | null> {
  try {
    const response = await fetch(`${apiConfig.url}/health`);
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}
