import type { Venue } from "../cartelera";

interface VenueFilterProps {
  venues: Venue[];
  selected: string[];
  onChange: (selected: string[]) => void;
}

/**
 * Picks any number of venues. Selecting none means all of them: a filter nobody
 * has touched should not empty the page.
 */
export function VenueFilter({ venues, selected, onChange }: VenueFilterProps) {
  if (venues.length <= 1) return null;

  const toggle = (key: string) => {
    onChange(
      selected.includes(key)
        ? selected.filter((k) => k !== key)
        : [...selected, key],
    );
  };

  return (
    <details className="venue-filter">
      <summary>
        Cines
        {selected.length > 0 && ` (${selected.length})`}
      </summary>
      <div className="venue-list">
        {venues.map((venue) => (
          <label key={venue.key} className="venue-option">
            <input
              type="checkbox"
              checked={selected.includes(venue.key)}
              onChange={() => toggle(venue.key)}
            />
            {venue.label}
          </label>
        ))}
      </div>
      {selected.length > 0 && (
        <button
          type="button"
          className="venue-clear"
          onClick={() => onChange([])}
        >
          Ver todos
        </button>
      )}
    </details>
  );
}
