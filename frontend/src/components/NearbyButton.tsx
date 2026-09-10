import type { GeolocationState } from "../hooks";

/**
 * Asks for the reader's position, once, on purpose.
 *
 * Hidden where geolocation does not exist, and replaced by a note when the
 * request is refused rather than inviting an argument with the browser.
 */
export function NearbyButton({ status, request, available }: GeolocationState) {
  if (!available || status === "granted") return null;

  if (status === "denied") {
    return <p className="nearby-note">No se pudo obtener tu ubicación</p>;
  }

  return (
    <button
      type="button"
      className="nearby-button"
      onClick={request}
      disabled={status === "asking"}
    >
      {status === "asking" ? "Ubicando…" : "📍 Cines cerca de mí"}
    </button>
  );
}
