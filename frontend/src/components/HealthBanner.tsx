import type { Health } from "../types";

interface HealthBannerProps {
  health: Health | null;
}

/**
 * Warns when the listings may not be current.
 *
 * Silent on "unknown", which only means no scrape has been recorded yet — a fresh
 * install is not a problem worth alarming the reader about.
 */
export function HealthBanner({ health }: HealthBannerProps) {
  if (
    health === null ||
    health.status === "ok" ||
    health.status === "unknown"
  ) {
    return null;
  }

  return (
    <p className={`health-notice health-${health.status}`} role="status">
      {health.status === "failing"
        ? "Hubo un problema al actualizar la cartelera"
        : "La cartelera puede estar desactualizada"}
      {health.hours_since_success !== null &&
        ` — última actualización hace ${Math.round(health.hours_since_success)} h`}
    </p>
  );
}
