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

export interface VisibleDay {
  /** Set only when showing a day other than today, so the page can say so. */
  displayDate: string | null;
  screenings: Screening[];
}

/**
 * The day worth showing: today if anything is on, otherwise the nearest one ahead.
 *
 * Never a past date. Falling back to the earliest date in the payload would show
 * last week's showtimes whenever the scraper has not run in a while.
 */
export function pickVisibleDay(
  screenings: Screening[],
  today: string,
): VisibleDay {
  if (screenings.length === 0) return { displayDate: null, screenings: [] };

  const onDay = (day: string) => screenings.filter((s) => dayOf(s) === day);

  const forToday = onDay(today);
  if (forToday.length > 0) return { displayDate: null, screenings: forToday };

  // ISO day strings sort chronologically, so a plain sort finds the nearest one.
  const upcoming = screenings
    .map(dayOf)
    .filter((day) => day > today)
    .sort();
  const earliest = upcoming[0];
  if (!earliest) return { displayDate: null, screenings: [] };

  return { displayDate: earliest, screenings: onDay(earliest) };
}

/** Group showings by film, then by venue, ordered by the title the reader sees. */
export function groupByMovie(screenings: Screening[]): MovieGroup[] {
  const groups = new Map<string, MovieGroup>();

  for (const screening of screenings) {
    const key = movieKey(screening.movie);
    const venueKey = `${screening.complex.company.name} - ${screening.complex.name}`;

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
