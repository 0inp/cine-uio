import { describe, expect, it } from "vitest";
import {
  audioLabel,
  displayTitle,
  groupByMovie,
  movieKey,
  pickVisibleDay,
  todayInEcuador,
} from "./cartelera";
import type { Movie, Screening } from "./types";

function movie(overrides: Partial<Movie> = {}): Movie {
  return { title: "Toy Story 5", ...overrides };
}

function screening(
  day: string,
  overrides: {
    movie?: Movie;
    venue?: string;
    company?: string;
    id?: number;
  } = {},
): Screening {
  return {
    id: overrides.id ?? 1,
    datetime: `${day}T20:00:00`,
    projection: "2D",
    audio: "dubbed" as const,
    complex: {
      name: overrides.venue ?? "CCI",
      city: "Quito",
      url_part: "/x",
      company: {
        name: overrides.company ?? "Multicines",
        base_url: "https://x",
      },
    },
    movie: overrides.movie ?? movie(),
  };
}

describe("movieKey", () => {
  it("uses the TMDB id when the film has been matched", () => {
    expect(movieKey(movie({ tmdb_id: 862 }))).toBe("tmdb-862");
  });

  it("falls back to the scraped title when it has not", () => {
    expect(movieKey(movie({ tmdb_id: null }))).toBe("title-Toy Story 5");
  });

  it("gives two chains' names for the same film one identity", () => {
    // The whole point of the TMDB match: one film, one card.
    const a = movie({ title: "Toy Story Five", tmdb_id: 862 });
    const b = movie({ title: "Toy Story 5 (Doblada)", tmdb_id: 862 });
    expect(movieKey(a)).toBe(movieKey(b));
  });
});

describe("displayTitle", () => {
  it("prefers the canonical title", () => {
    expect(displayTitle(movie({ tmdb_title: "Toy Story 5" }))).toBe(
      "Toy Story 5",
    );
  });

  it("uses the scraped title when TMDB has none", () => {
    expect(displayTitle(movie({ title: "Raw Title", tmdb_title: null }))).toBe(
      "Raw Title",
    );
  });
});

describe("todayInEcuador", () => {
  it("uses Ecuador's day, not the reader's", () => {
    // 02:00 UTC is still the previous evening in Quito (UTC-5).
    expect(todayInEcuador(new Date("2026-09-10T02:00:00Z"))).toBe("2026-09-09");
  });
});

describe("pickVisibleDay", () => {
  it("shows today when anything is on", () => {
    const day = pickVisibleDay(
      [screening("2026-09-09"), screening("2026-09-11", { id: 2 })],
      "2026-09-09",
    );
    expect(day.displayDate).toBeNull();
    expect(day.screenings).toHaveLength(1);
  });

  it("falls back to the nearest upcoming day", () => {
    const day = pickVisibleDay(
      [screening("2026-09-13", { id: 1 }), screening("2026-09-11", { id: 2 })],
      "2026-09-09",
    );
    expect(day.displayDate).toBe("2026-09-11");
    expect(day.screenings.map((s) => s.id)).toEqual([2]);
  });

  it("never falls back to a past day", () => {
    // A stale database must show nothing rather than last week's showtimes.
    const day = pickVisibleDay([screening("2026-09-01")], "2026-09-09");
    expect(day.displayDate).toBeNull();
    expect(day.screenings).toEqual([]);
  });

  it("handles an empty payload", () => {
    expect(pickVisibleDay([], "2026-09-09")).toEqual({
      displayDate: null,
      screenings: [],
    });
  });
});

describe("groupByMovie", () => {
  it("collapses two billings of the same film into one group", () => {
    const groups = groupByMovie([
      screening("2026-09-09", {
        id: 1,
        movie: movie({ title: "Toy Story Five", tmdb_id: 862 }),
      }),
      screening("2026-09-09", {
        id: 2,
        venue: "San Luis",
        company: "Supercines",
        movie: movie({ title: "Toy Story 5", tmdb_id: 862 }),
      }),
    ]);
    expect(groups).toHaveLength(1);
    expect(Object.keys(groups[0].screeningsByVenue)).toEqual([
      "Multicines - CCI",
      "Supercines - San Luis",
    ]);
  });

  it("keeps a venue's showings together", () => {
    const groups = groupByMovie([
      screening("2026-09-09", { id: 1 }),
      screening("2026-09-09", { id: 2 }),
    ]);
    expect(groups[0].screeningsByVenue["Multicines - CCI"]).toHaveLength(2);
  });

  it("orders by the title the reader actually sees", () => {
    // Sorting on the scraped title would put these the other way round.
    const groups = groupByMovie([
      screening("2026-09-09", {
        id: 1,
        movie: movie({ title: "Aaa Raw", tmdb_id: 1, tmdb_title: "Zebra" }),
      }),
      screening("2026-09-09", {
        id: 2,
        movie: movie({ title: "Zzz Raw", tmdb_id: 2, tmdb_title: "Antelope" }),
      }),
    ]);
    expect(groups.map((g) => displayTitle(g.movie))).toEqual([
      "Antelope",
      "Zebra",
    ]);
  });

  it("returns nothing for no screenings", () => {
    expect(groupByMovie([])).toEqual([]);
  });
});

describe("audioLabel", () => {
  it("gives the reader Spanish, not the stored code", () => {
    expect(audioLabel("dubbed")).toBe("Doblada");
    expect(audioLabel("subtitled")).toBe("Subtitulada");
  });

  it("says nothing when the chain did not say", () => {
    expect(audioLabel(null)).toBeNull();
  });
});
