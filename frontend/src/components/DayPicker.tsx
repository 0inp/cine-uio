interface DayPickerProps {
  days: string[];
  day: string | null;
  today: string;
  onSelect: (day: string) => void;
}

function label(day: string, today: string): string {
  if (day === today) return "Hoy";
  // Midday avoids the date shifting when the browser reads an ISO day as UTC.
  return new Date(`${day}T12:00:00`).toLocaleDateString("es-EC", {
    weekday: "short",
    day: "numeric",
    month: "short",
  });
}

/** Hidden when there is only one day to look at. */
export function DayPicker({ days, day, today, onSelect }: DayPickerProps) {
  if (days.length <= 1) return null;

  return (
    <fieldset className="day-picker">
      <legend className="visually-hidden">Día</legend>
      {days.map((d) => (
        <button
          key={d}
          type="button"
          className={`day-chip${d === day ? " day-chip-selected" : ""}`}
          aria-pressed={d === day}
          onClick={() => onSelect(d)}
        >
          {label(d, today)}
        </button>
      ))}
    </fieldset>
  );
}
