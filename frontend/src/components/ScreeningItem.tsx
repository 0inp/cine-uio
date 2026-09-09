import type { Screening } from "../types";

interface ScreeningItemProps {
  screening: Screening;
}

export function ScreeningItem({ screening }: ScreeningItemProps) {
  return (
    <div className="screening-item">
      <span className="screening-time">
        {new Date(screening.datetime).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        })}
      </span>
      <span className="screening-format">{screening.format}</span>
      <span className="screening-language">{screening.language}</span>
    </div>
  );
}
