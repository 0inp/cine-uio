import type { Audio, Movie, MovieGroup, Screening } from "./types";

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

export interface Venue {
  key: string;
  label: string;
}

/** The venues actually showing something, so the filter never offers a dead end. */
export function availableVenues(screenings: Screening[]): Venue[] {
  const keys = new Set(screenings.map(venueKeyOf));
  return Array.from(keys)
    .sort((a, b) => a.localeCompare(b))
    .map((key) => ({ key, label: key }));
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
