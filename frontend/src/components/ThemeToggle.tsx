import type { Theme } from "../hooks";

interface ThemeToggleProps {
  theme: Theme;
  onToggle: () => void;
}

export function ThemeToggle({ theme, onToggle }: ThemeToggleProps) {
  const goingDark = theme === "light";
  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={onToggle}
      aria-label={goingDark ? "Cambiar a tema oscuro" : "Cambiar a tema claro"}
    >
      {goingDark ? "🌙" : "☀️"}
    </button>
  );
}
