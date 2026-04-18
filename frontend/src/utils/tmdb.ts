// Utility functions for working with TMDB data
import { createResource } from "solid-js";
import { TMDBConfig } from "~/types/movie";

// Create a resource to fetch TMDB config from our backend
const [tmdbConfigResource] = createResource(async () => {
  try {
    const response = await fetch("http://localhost:8080/api/tmdb-config");
    if (!response.ok) throw new Error("Failed to fetch TMDB config");
    return await response.json() as TMDBConfig;
  } catch (error) {
    console.error("Error fetching TMDB config:", error);
    return null;
  }
});

export function getTMDBConfig(): TMDBConfig | null {
  return tmdbConfigResource() || null;
}

export function buildTMDBImageUrl(path: string | undefined, sizeType: 'poster' | 'backdrop' = 'poster'): string | undefined {
  if (!path) return undefined;

  // Use cached config or fall back to default
  const config = getTMDBConfig() || {
    secure_base_url: "https://image.tmdb.org/t/p/",
    poster_sizes: ["w92", "w154", "w185", "w342", "w500", "w780", "original"],
    backdrop_sizes: ["w300", "w780", "w1280", "original"]
  };

  const size = sizeType === 'poster' ? 'w500' : 'w1280';
  return `${config.secure_base_url}${size}${path}`;
}

export function getPosterUrl(posterPath: string | undefined): string | undefined {
  return buildTMDBImageUrl(posterPath, 'poster');
}

export function getBackdropUrl(backdropPath: string | undefined): string | undefined {
  return buildTMDBImageUrl(backdropPath, 'backdrop');
}
