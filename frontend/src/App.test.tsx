import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
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
    await waitFor(() => expect(screen.getByText("Toy Story 5")).toBeInTheDocument());
  });

  it("excludes screenings from other days", async () => {
    const todayScreening = { ...BASE_SCREENING, id: 1, datetime: `${today}T14:30:00` };
    const tomorrowScreening = { ...BASE_SCREENING, id: 2, datetime: `${tomorrow}T09:00:00`, movie: { title: "Supergirl" } };
    mockFetch([todayScreening, tomorrowScreening]);
    render(<App />);
    await waitFor(() => expect(screen.getByText("Toy Story 5")).toBeInTheDocument());
    expect(screen.queryByText("Supergirl")).not.toBeInTheDocument();
  });

  it("sorts movie titles alphabetically", async () => {
    const supergirl = {
      ...BASE_SCREENING,
      id: 2,
      movie: { title: "Supergirl" },
      complex: { ...BASE_COMPLEX, name: "San Luis", company: { name: "Supercines", base_url: "https://www.supercines.com" } },
    };
    mockFetch([BASE_SCREENING, supergirl]);
    render(<App />);
    await waitFor(() => expect(screen.getByText("Toy Story 5")).toBeInTheDocument());

    const titles = screen.getAllByRole("heading", { level: 3 }).map((h) => h.textContent);
    expect(titles).toEqual([...titles].sort((a, b) => (a ?? "").localeCompare(b ?? "")));
  });

  it("groups screenings under company–complex headings", async () => {
    mockFetch([BASE_SCREENING]);
    render(<App />);
    await waitFor(() =>
      expect(screen.getByText("Multicines - CCI")).toBeInTheDocument(),
    );
  });
});
