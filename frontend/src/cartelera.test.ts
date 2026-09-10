import { describe, expect, it } from "vitest";
import {
  audioLabel,
  availableDays,
  availableVenues,
  defaultDay,
  displayTitle,
  distanceKm,
  filterScreenings,
  formatDistance,
  groupByMovie,
  movieKey,
  todayInEcuador,
  venueKeyOf,
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
    latitude?: number | null;
    longitude?: number | null;
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
      latitude:
        overrides.latitude === undefined ? -0.17737 : overrides.latitude,
      longitude:
        overrides.longitude === undefined ? -78.48497 : overrides.longitude,
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

describe("availableDays", () => {
  it("offers each day once, in order", () => {
    const days = availableDays(
      [
        screening("2026-09-12"),
        screening("2026-09-10"),
        screening("2026-09-10"),
      ],
      "2026-09-10",
    );
    expect(days).toEqual(["2026-09-10", "2026-09-12"]);
  });

  it("never offers a day that has passed", () => {
    // Excluded here rather than in the picker, so nothing downstream can offer
    // last week's showtimes from a stale database.
    expect(availableDays([screening("2026-09-01")], "2026-09-10")).toEqual([]);
  });

  it("has nothing to offer for an empty payload", () => {
    expect(availableDays([], "2026-09-10")).toEqual([]);
  });
});

describe("defaultDay", () => {
  it("starts on today when something is on", () => {
    expect(defaultDay(["2026-09-10", "2026-09-11"], "2026-09-10")).toBe(
      "2026-09-10",
    );
  });

  it("falls forward to the nearest day when today has nothing", () => {
    expect(defaultDay(["2026-09-11", "2026-09-13"], "2026-09-10")).toBe(
      "2026-09-11",
    );
  });

  it("has no day to pick when there are none", () => {
    expect(defaultDay([], "2026-09-10")).toBeNull();
  });
});

describe("availableVenues", () => {
  it("lists only the venues actually showing something", () => {
    const venues = availableVenues([
      screening("2026-09-10", { venue: "San Luis", company: "Supercines" }),
      screening("2026-09-10", { venue: "CCI", company: "Multicines", id: 2 }),
    ]);
    expect(venues.map((v) => v.key)).toEqual([
      "Multicines - CCI",
      "Supercines - San Luis",
    ]);
  });

  it("agrees with the key used for grouping", () => {
    const one = screening("2026-09-10");
    expect(availableVenues([one])[0].key).toBe(venueKeyOf(one));
  });
});

describe("filterScreenings", () => {
  const showings = [
    screening("2026-09-10", { id: 1, venue: "CCI", company: "Multicines" }),
    screening("2026-09-11", { id: 2, venue: "CCI", company: "Multicines" }),
    screening("2026-09-10", {
      id: 3,
      venue: "San Luis",
      company: "Supercines",
    }),
  ];

  it("keeps a single day", () => {
    const kept = filterScreenings(showings, {
      day: "2026-09-11",
      venueKeys: [],
    });
    expect(kept.map((s) => s.id)).toEqual([2]);
  });

  it("keeps the chosen venues", () => {
    const kept = filterScreenings(showings, {
      day: null,
      venueKeys: ["Supercines - San Luis"],
    });
    expect(kept.map((s) => s.id)).toEqual([3]);
  });

  it("keeps several venues at once", () => {
    const kept = filterScreenings(showings, {
      day: "2026-09-10",
      venueKeys: ["Supercines - San Luis", "Multicines - CCI"],
    });
    expect(kept.map((s) => s.id)).toEqual([1, 3]);
  });

  it("treats an untouched venue filter as every venue", () => {
    // Selecting nothing must not empty the page.
    const kept = filterScreenings(showings, { day: null, venueKeys: [] });
    expect(kept).toHaveLength(3);
  });

  it("combines both filters", () => {
    const kept = filterScreenings(showings, {
      day: "2026-09-10",
      venueKeys: ["Multicines - CCI"],
    });
    expect(kept.map((s) => s.id)).toEqual([1]);
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

const QUITO = { latitude: -0.1807, longitude: -78.4678 };
const GUAYAQUIL = { latitude: -2.1894, longitude: -79.8891 };

describe("distanceKm", () => {
  it("matches a known distance", () => {
    // Quito to Guayaquil is about 270 km as the crow flies.
    expect(distanceKm(QUITO, GUAYAQUIL)).toBeGreaterThan(260);
    expect(distanceKm(QUITO, GUAYAQUIL)).toBeLessThan(285);
  });

  it("is zero for the same place", () => {
    expect(distanceKm(QUITO, QUITO)).toBeCloseTo(0, 6);
  });

  it("does not care about direction", () => {
    expect(distanceKm(QUITO, GUAYAQUIL)).toBeCloseTo(
      distanceKm(GUAYAQUIL, QUITO),
      9,
    );
  });

  it("would notice swapped coordinates", () => {
    // The classic bug: reading lat as lon puts Quito in the wrong hemisphere.
    const swapped = { latitude: QUITO.longitude, longitude: QUITO.latitude };
    expect(distanceKm(QUITO, swapped)).toBeGreaterThan(1000);
  });
});

describe("formatDistance", () => {
  it("uses metres below a kilometre, where the difference matters", () => {
    expect(formatDistance(0.842)).toBe("842 m");
  });

  it("uses kilometres above one, with a comma", () => {
    expect(formatDistance(3.47)).toBe("3,5 km");
  });
});

describe("availableVenues with a position", () => {
  const near = screening("2026-09-10", {
    id: 1,
    venue: "Near",
    latitude: -0.181,
    longitude: -78.468,
  });
  const far = screening("2026-09-10", {
    id: 2,
    venue: "Far",
    latitude: GUAYAQUIL.latitude,
    longitude: GUAYAQUIL.longitude,
  });

  it("orders by proximity once a position is known", () => {
    const venues = availableVenues([far, near], QUITO);
    expect(venues.map((v) => v.key)).toEqual([
      "Multicines - Near",
      "Multicines - Far",
    ]);
  });

  it("keeps alphabetical order without a position", () => {
    const venues = availableVenues([near, far]);
    expect(venues.map((v) => v.key)).toEqual([
      "Multicines - Far",
      "Multicines - Near",
    ]);
  });

  it("puts a venue with no coordinates last rather than dropping it", () => {
    const unknown = screening("2026-09-10", {
      id: 3,
      venue: "Unknown",
      latitude: null,
      longitude: null,
    });
    const venues = availableVenues([unknown, near], QUITO);
    expect(venues.map((v) => v.key)).toEqual([
      "Multicines - Near",
      "Multicines - Unknown",
    ]);
    expect(venues[1].distanceKm).toBeUndefined();
  });
});
