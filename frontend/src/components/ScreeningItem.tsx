import { audioLabel } from "../cartelera";
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
      <span className="screening-format">{screening.projection}</span>
      {audioLabel(screening.audio) && (
        <span className="screening-language">
          {audioLabel(screening.audio)}
        </span>
      )}
    </div>
  );
}
