import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import App, { ScreeningItem } from "./App";

// Compute today/tomorrow in Ecuador time so tests stay date-independent.
function ecuadorDate(offsetDays = 0): string {
  const d = new Date(Date.now() + offsetDays * 86_400_000);
  return d.toLocaleDateString("en-CA", { timeZone: "America/Guayaquil" });
}

const today = ecuadorDate(0);
const tomorrow = ecuadorDate(1);

const BASE_COMPLEX = {
  name: "CCI",
  url_part: "/?cityId=19&storeId=3555",
  company: { name: "Multicines", base_url: "https://www.multicines.com.ec" },
};

const BASE_SCREENING = {
  id: 1,
  datetime: `${today}T14:30:00`,
  format: "2D",
  language: "Doblada",
  complex: BASE_COMPLEX,
  movie: { title: "Toy Story 5" },
};

function mockFetch(screenings: unknown[], ok = true): void {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValueOnce({
      ok,
      status: ok ? 200 : 500,
      json: async () => screenings,
    }),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

// ---------------------------------------------------------------------------

describe("ScreeningItem", () => {
  it("renders format and language", () => {
    render(<ScreeningItem screening={BASE_SCREENING} />);
    expect(screen.getByText("2D")).toBeInTheDocument();
    expect(screen.getByText("Doblada")).toBeInTheDocument();
  });

  it("renders a time string", () => {
    render(<ScreeningItem screening={BASE_SCREENING} />);
    expect(screen.getByText(/\d{1,2}:\d{2}/)).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------

describe("App", () => {
  it("shows a loading indicator before data arrives", () => {
    vi.stubGlobal("fetch", vi.fn().mockReturnValue(new Promise(() => {})));
    render(<App />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("shows an error message when the fetch fails", async () => {
    mockFetch([], false);
    render(<App />);
    await waitFor(() => expect(screen.getByText(/error/i)).toBeInTheDocument());
  });

  it("renders today's movies after a successful fetch", async () => {
    mockFetch([BASE_SCREENING]);
    render(<App />);
    await waitFor(() =>
      expect(screen.getByText("Toy Story 5")).toBeInTheDocument(),
    );
  });

  it("excludes screenings from other days", async () => {
    const todayScreening = {
      ...BASE_SCREENING,
      id: 1,
      datetime: `${today}T14:30:00`,
    };
    const tomorrowScreening = {
      ...BASE_SCREENING,
      id: 2,
      datetime: `${tomorrow}T09:00:00`,
      movie: { title: "Supergirl" },
    };
    mockFetch([todayScreening, tomorrowScreening]);
    render(<App />);
    await waitFor(() =>
      expect(screen.getByText("Toy Story 5")).toBeInTheDocument(),
    );
    expect(screen.queryByText("Supergirl")).not.toBeInTheDocument();
  });

  it("sorts movie titles alphabetically", async () => {
    const supergirl = {
      ...BASE_SCREENING,
      id: 2,
      movie: { title: "Supergirl" },
      complex: {
        ...BASE_COMPLEX,
        name: "San Luis",
        company: { name: "Supercines", base_url: "https://www.supercines.com" },
      },
    };
    mockFetch([BASE_SCREENING, supergirl]);
    render(<App />);
    await waitFor(() =>
      expect(screen.getByText("Toy Story 5")).toBeInTheDocument(),
    );

    const titles = screen
      .getAllByRole("heading", { level: 3 })
      .map((h) => h.textContent);
    expect(titles).toEqual(
      [...titles].sort((a, b) => (a ?? "").localeCompare(b ?? "")),
    );
  });

  it("groups screenings under company–complex headings", async () => {
    mockFetch([BASE_SCREENING]);
    render(<App />);
    await waitFor(() =>
      expect(screen.getByText("Multicines - CCI")).toBeInTheDocument(),
    );
  });
});

// ---------------------------------------------------------------------------

describe("TMDB enrichment display", () => {
  it("shows tmdb_title instead of raw title when available", async () => {
    const enriched = {
      ...BASE_SCREENING,
      movie: {
        title: "Toy Story Five",
        tmdb_id: 862,
        tmdb_title: "Toy Story 5",
        poster_url: null,
        overview: null,
        runtime: null,
        certification: null,
        release_date: null,
      },
    };
    mockFetch([enriched]);
    render(<App />);
    await waitFor(() =>
      expect(screen.getByText("Toy Story 5")).toBeInTheDocument(),
    );
    expect(screen.queryByText("Toy Story Five")).not.toBeInTheDocument();
  });

  it("groups screenings with different raw titles but same tmdb_id into one card", async () => {
    const multicines = {
      ...BASE_SCREENING,
      id: 1,
      movie: {
        title: "Toy Story Five",
        tmdb_id: 862,
        tmdb_title: "Toy Story 5",
      },
    };
    const supercines = {
      ...BASE_SCREENING,
      id: 2,
      complex: {
        ...BASE_COMPLEX,
        name: "San Luis",
        company: { name: "Supercines", base_url: "https://www.supercines.com" },
      },
      movie: {
        title: "Toy Story 5 (Doblada)",
        tmdb_id: 862,
        tmdb_title: "Toy Story 5",
      },
    };
    mockFetch([multicines, supercines]);
    render(<App />);
    await waitFor(() =>
      expect(screen.getByText("Toy Story 5")).toBeInTheDocument(),
    );
    expect(screen.getAllByRole("heading", { level: 3 })).toHaveLength(1);
  });

  it("renders a poster image when poster_url is provided", async () => {
    const enriched = {
      ...BASE_SCREENING,
      movie: {
        title: "Toy Story 5",
        tmdb_id: 862,
        tmdb_title: "Toy Story 5",
        poster_url: "https://image.tmdb.org/t/p/w500/poster.jpg",
        overview: null,
        runtime: null,
        certification: null,
        release_date: null,
      },
    };
    mockFetch([enriched]);
    render(<App />);
    await waitFor(() =>
      expect(
        screen.getByRole("img", { name: "Toy Story 5" }),
      ).toBeInTheDocument(),
    );
  });

  it("renders runtime and certification metadata when present", async () => {
    const enriched = {
      ...BASE_SCREENING,
      movie: {
        title: "Toy Story 5",
        tmdb_id: 862,
        tmdb_title: "Toy Story 5",
        poster_url: null,
        overview: "Woody is back.",
        runtime: 98,
        certification: "PG",
        release_date: "2026-06-20",
      },
    };
    mockFetch([enriched]);
    render(<App />);
    await waitFor(() => expect(screen.getByText("PG")).toBeInTheDocument());
    expect(screen.getByText("98 min")).toBeInTheDocument();
    expect(screen.getByText("2026")).toBeInTheDocument();
    expect(screen.getByText("Woody is back.")).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------

describe("date fallback when there are no screenings today", () => {
  it("falls back to the nearest upcoming date", async () => {
    const future = {
      ...BASE_SCREENING,
      id: 3,
      datetime: `${tomorrow}T18:00:00`,
      movie: { title: "Supergirl" },
    };
    mockFetch([future]);
    render(<App />);
    await waitFor(() =>
      expect(screen.getByText("Supergirl")).toBeInTheDocument(),
    );
    expect(screen.getByText(/Sin funciones para hoy/)).toBeInTheDocument();
  });

  it("picks the earliest upcoming date, not just any future one", async () => {
    const dayAfter = ecuadorDate(2);
    mockFetch([
      {
        ...BASE_SCREENING,
        id: 1,
        datetime: `${dayAfter}T18:00:00`,
        movie: { title: "Farther Away" },
      },
      {
        ...BASE_SCREENING,
        id: 2,
        datetime: `${tomorrow}T18:00:00`,
        movie: { title: "Closer" },
      },
    ]);
    render(<App />);
    await waitFor(() => expect(screen.getByText("Closer")).toBeInTheDocument());
    expect(screen.queryByText("Farther Away")).not.toBeInTheDocument();
  });

  it("never falls back to a past date when the DB is stale", async () => {
    const yesterday = ecuadorDate(-1);
    mockFetch([
      {
        ...BASE_SCREENING,
        id: 1,
        datetime: `${yesterday}T18:00:00`,
        movie: { title: "Yesterday's Show" },
      },
    ]);
    render(<App />);
    await waitFor(() =>
      expect(
        screen.getByText(/No hay funciones disponibles/),
      ).toBeInTheDocument(),
    );
    expect(screen.queryByText("Yesterday's Show")).not.toBeInTheDocument();
    expect(
      screen.queryByText(/Sin funciones para hoy/),
    ).not.toBeInTheDocument();
  });

  it("prefers today's screenings over upcoming ones", async () => {
    mockFetch([
      {
        ...BASE_SCREENING,
        id: 1,
        datetime: `${tomorrow}T18:00:00`,
        movie: { title: "Tomorrow's Show" },
      },
      {
        ...BASE_SCREENING,
        id: 2,
        datetime: `${today}T18:00:00`,
        movie: { title: "Today's Show" },
      },
    ]);
    render(<App />);
    await waitFor(() =>
      expect(screen.getByText("Today's Show")).toBeInTheDocument(),
    );
    expect(screen.queryByText("Tomorrow's Show")).not.toBeInTheDocument();
    expect(
      screen.queryByText(/Sin funciones para hoy/),
    ).not.toBeInTheDocument();
  });
});
