import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import { ScreeningItem } from "./components/ScreeningItem";

// Compute today/tomorrow in Ecuador time so tests stay date-independent.
function ecuadorDate(offsetDays = 0): string {
  const d = new Date(Date.now() + offsetDays * 86_400_000);
  return d.toLocaleDateString("en-CA", { timeZone: "America/Guayaquil" });
}

const today = ecuadorDate(0);
const tomorrow = ecuadorDate(1);

const BASE_COMPLEX = {
  name: "CCI",
  city: "Quito",
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

// The app makes two calls: the city list, then that city's screenings. Route by
// URL rather than by call order, so a test does not depend on which fires first.
const HEALTHY = { status: "ok", detail: "fresh", hours_since_success: 2 };

function mockFetch(
  screenings: unknown[],
  ok = true,
  cities: string[] = ["Quito"],
  health: unknown = HEALTHY,
): void {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      if (url.includes("/cities")) {
        return { ok: true, status: 200, json: async () => cities };
      }
      if (url.includes("/health")) {
        return { ok: true, status: 200, json: async () => health };
      }
      return { ok, status: ok ? 200 : 500, json: async () => screenings };
    }),
  );
}

// This runtime does not provide localStorage, and the app treats it as optional
// anyway (private browsing). Stub an in-memory one so the persistence of the city
// choice is actually exercised rather than silently skipped.
function memoryStorage(): Storage {
  let store: Record<string, string> = {};
  return {
    getItem: (k) => store[k] ?? null,
    setItem: (k, v) => {
      store[k] = String(v);
    },
    removeItem: (k) => {
      delete store[k];
    },
    clear: () => {
      store = {};
    },
    key: (i) => Object.keys(store)[i] ?? null,
    get length() {
      return Object.keys(store).length;
    },
  } as Storage;
}

beforeEach(() => {
  vi.stubGlobal("localStorage", memoryStorage());
});

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

// ---------------------------------------------------------------------------

describe("city selection", () => {
  it("requests only the selected city's screenings", async () => {
    mockFetch([BASE_SCREENING]);
    render(<App />);
    await waitFor(() =>
      expect(screen.getByText("Toy Story 5")).toBeInTheDocument(),
    );
    const calls = (
      globalThis.fetch as unknown as { mock: { calls: string[][] } }
    ).mock.calls.map((c) => c[0]);
    expect(calls.some((u) => u.includes("city=Quito"))).toBe(true);
  });

  it("hides the picker when only one city exists", async () => {
    mockFetch([BASE_SCREENING], true, ["Quito"]);
    render(<App />);
    await waitFor(() =>
      expect(screen.getByText("Toy Story 5")).toBeInTheDocument(),
    );
    expect(screen.queryByLabelText("Ciudad")).not.toBeInTheDocument();
  });

  it("offers every city when there are several", async () => {
    mockFetch([BASE_SCREENING], true, ["Cuenca", "Guayaquil", "Quito"]);
    render(<App />);
    await waitFor(() =>
      expect(screen.getByLabelText("Ciudad")).toBeInTheDocument(),
    );
    expect(screen.getAllByRole("option").map((o) => o.textContent)).toEqual([
      "Cuenca",
      "Guayaquil",
      "Quito",
    ]);
  });

  it("refetches and remembers the city when it changes", async () => {
    mockFetch([BASE_SCREENING], true, ["Guayaquil", "Quito"]);
    render(<App />);
    await waitFor(() =>
      expect(screen.getByLabelText("Ciudad")).toBeInTheDocument(),
    );

    fireEvent.change(screen.getByLabelText("Ciudad"), {
      target: { value: "Guayaquil" },
    });

    await waitFor(() => {
      const calls = (
        globalThis.fetch as unknown as { mock: { calls: string[][] } }
      ).mock.calls.map((c) => c[0]);
      expect(calls.some((u) => u.includes("city=Guayaquil"))).toBe(true);
    });
    expect(localStorage.getItem("cine-uio.city")).toBe("Guayaquil");
  });

  it("starts from the remembered city", async () => {
    localStorage.setItem("cine-uio.city", "Cuenca");
    mockFetch([], true, ["Cuenca", "Quito"]);
    render(<App />);
    await waitFor(() => {
      const calls = (
        globalThis.fetch as unknown as { mock: { calls: string[][] } }
      ).mock.calls.map((c) => c[0]);
      expect(calls.some((u) => u.includes("city=Cuenca"))).toBe(true);
    });
  });
});

// ---------------------------------------------------------------------------

describe("staleness banner", () => {
  const stale = {
    status: "stale",
    detail: "the last clean scrape was 50h ago",
    hours_since_success: 50.4,
  };

  it("stays quiet when the data is fresh", async () => {
    mockFetch([BASE_SCREENING]);
    render(<App />);
    await waitFor(() =>
      expect(screen.getByText("Toy Story 5")).toBeInTheDocument(),
    );
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("warns when the listings may be out of date", async () => {
    mockFetch([BASE_SCREENING], true, ["Quito"], stale);
    render(<App />);
    await waitFor(() => expect(screen.getByRole("status")).toBeInTheDocument());
    expect(screen.getByRole("status").textContent).toContain(
      "puede estar desactualizada",
    );
  });

  it("says how long ago the data was refreshed", async () => {
    mockFetch([BASE_SCREENING], true, ["Quito"], stale);
    render(<App />);
    await waitFor(() => expect(screen.getByRole("status")).toBeInTheDocument());
    expect(screen.getByRole("status").textContent).toContain("50 h");
  });

  it("reports a failed refresh differently from a stale one", async () => {
    mockFetch([BASE_SCREENING], true, ["Quito"], {
      status: "failing",
      detail: "the last scrape lost 7 complex(es)",
      hours_since_success: 30,
    });
    render(<App />);
    await waitFor(() => expect(screen.getByRole("status")).toBeInTheDocument());
    expect(screen.getByRole("status").textContent).toContain(
      "Hubo un problema",
    );
  });

  it("stays quiet when no scrape has been recorded yet", async () => {
    // A fresh install is not a problem worth alarming the reader about.
    mockFetch([BASE_SCREENING], true, ["Quito"], {
      status: "unknown",
      detail: "no scrape has been recorded yet",
      hours_since_success: null,
    });
    render(<App />);
    await waitFor(() =>
      expect(screen.getByText("Toy Story 5")).toBeInTheDocument(),
    );
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("says nothing when health cannot be reached", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        if (url.includes("/health")) throw new Error("offline");
        if (url.includes("/cities"))
          return { ok: true, status: 200, json: async () => ["Quito"] };
        return { ok: true, status: 200, json: async () => [BASE_SCREENING] };
      }),
    );
    render(<App />);
    await waitFor(() =>
      expect(screen.getByText("Toy Story 5")).toBeInTheDocument(),
    );
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });
});
