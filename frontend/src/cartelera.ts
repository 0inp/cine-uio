import type { Audio, Movie, MovieGroup, Position, Screening } from "./types";

/** Identity for grouping: the same film billed under two titles is one film. */
export function movieKey(movie: Movie): string {
  return movie.tmdb_id != null
    ? `tmdb-${movie.tmdb_id}`
    : `title-${movie.title}`;
}

export function displayTitle(movie: Movie): string {
  return movie.tmdb_title ?? movie.title;
}

/** Today's date in Ecuador, as an ISO day. The reader's clock is not the venue's. */
export function todayInEcuador(now: Date = new Date()): string {
  return now.toLocaleDateString("en-CA", { timeZone: "America/Guayaquil" });
}

function dayOf(screening: Screening): string {
  return screening.datetime.split("T")[0];
}

/** The venue key used everywhere: grouping, filtering and display all agree. */
export function venueKeyOf(screening: Screening): string {
  return `${screening.complex.company.name} - ${screening.complex.name}`;
}

/**
 * The days worth offering: today and after, in order.
 *
 * Past days are excluded here rather than in the picker, so nothing downstream
 * can offer one. A stale database would otherwise show last week's showtimes.
 */
export function availableDays(
  screenings: Screening[],
  today: string,
): string[] {
  const days = new Set<string>();
  for (const screening of screenings) {
    const day = dayOf(screening);
    if (day >= today) days.add(day);
  }
  return Array.from(days).sort();
}

/** Today when something is on, otherwise the nearest day ahead, or nothing. */
export function defaultDay(days: string[], today: string): string | null {
  if (days.includes(today)) return today;
  return days[0] ?? null;
}

const EARTH_RADIUS_KM = 6371;

function toRadians(degrees: number): number {
  return (degrees * Math.PI) / 180;
}

/**
 * Great-circle distance in kilometres.
 *
 * Haversine rather than a flat approximation: cheap, and it does not need a
 * projection chosen for a particular latitude.
 */
export function distanceKm(from: Position, to: Position): number {
  const dLat = toRadians(to.latitude - from.latitude);
  const dLon = toRadians(to.longitude - from.longitude);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRadians(from.latitude)) *
      Math.cos(toRadians(to.latitude)) *
      Math.sin(dLon / 2) ** 2;
  return 2 * EARTH_RADIUS_KM * Math.asin(Math.sqrt(a));
}

export interface Venue {
  key: string;
  label: string;
  /** Undefined until the reader shares a position, or if the venue has no coordinates. */
  distanceKm?: number;
}

/**
 * The venues actually showing something, so the filter never offers a dead end.
 *
 * Ordered by distance once a position is known, alphabetically otherwise. A venue
 * without coordinates sorts last rather than being dropped.
 */
export function availableVenues(
  screenings: Screening[],
  position: Position | null = null,
): Venue[] {
  const byKey = new Map<string, Screening>();
  for (const screening of screenings) {
    const key = venueKeyOf(screening);
    if (!byKey.has(key)) byKey.set(key, screening);
  }

  const venues: Venue[] = Array.from(byKey.entries()).map(
    ([key, screening]) => {
      const { latitude, longitude } = screening.complex;
      const known =
        position !== null &&
        latitude !== null &&
        latitude !== undefined &&
        longitude !== null &&
        longitude !== undefined;
      return {
        key,
        label: key,
        distanceKm: known
          ? distanceKm(position, { latitude, longitude })
          : undefined,
      };
    },
  );

  return venues.sort((a, b) => {
    if (a.distanceKm !== undefined && b.distanceKm !== undefined) {
      return a.distanceKm - b.distanceKm;
    }
    if (a.distanceKm !== undefined) return -1;
    if (b.distanceKm !== undefined) return 1;
    return a.label.localeCompare(b.label);
  });
}

/** Distance per venue key, for showing it next to a venue heading. */
export function venueDistances(venues: Venue[]): Record<string, number> {
  const distances: Record<string, number> = {};
  for (const venue of venues) {
    if (venue.distanceKm !== undefined) distances[venue.key] = venue.distanceKm;
  }
  return distances;
}

/** "1,2 km" or "800 m" — metres below a kilometre, where the difference matters. */
export function formatDistance(km: number): string {
  if (km < 1) return `${Math.round(km * 1000)} m`;
  return `${km.toFixed(1).replace(".", ",")} km`;
}

export interface Filters {
  day: string | null;
  /** Empty means every venue: a filter nobody has touched excludes nothing. */
  venueKeys: string[];
}

export function filterScreenings(
  screenings: Screening[],
  { day, venueKeys }: Filters,
): Screening[] {
  const wanted = new Set(venueKeys);
  return screenings.filter(
    (screening) =>
      (day === null || dayOf(screening) === day) &&
      (wanted.size === 0 || wanted.has(venueKeyOf(screening))),
  );
}

/** Group showings by film, then by venue, ordered by the title the reader sees. */
export function groupByMovie(screenings: Screening[]): MovieGroup[] {
  const groups = new Map<string, MovieGroup>();

  for (const screening of screenings) {
    const key = movieKey(screening.movie);
    const venueKey = venueKeyOf(screening);

    let group = groups.get(key);
    if (!group) {
      group = { movie: screening.movie, screeningsByVenue: {} };
      groups.set(key, group);
    }
    const venues = group.screeningsByVenue;
    if (!venues[venueKey]) venues[venueKey] = [];
    venues[venueKey].push(screening);
  }

  return Array.from(groups.values()).sort((a, b) =>
    displayTitle(a.movie).localeCompare(displayTitle(b.movie)),
  );
}

const AUDIO_LABELS: Record<string, string> = {
  dubbed: "Doblada",
  subtitled: "Subtitulada",
};

/** The reader's word for an audio track, or null when the chain did not say. */
export function audioLabel(audio: Audio): string | null {
  return audio === null ? null : (AUDIO_LABELS[audio] ?? null);
}
