# Cine UIO — Frontend

React + TypeScript + Vite frontend for the Cine UIO screening aggregator.

## Dev

```bash
bun install
bun dev          # start on http://localhost:5173
```

## Build

```bash
bun run build    # outputs to dist/
bun run preview  # preview the production build
```

## Lint & Format

```bash
bun run lint     # biome lint
bun run format   # biome check --write
bun run typecheck
```

## Test

```bash
bun run test     # vitest run
```

## Environment

Set `VITE_API_URL` to override the backend base URL (default: `http://localhost:8000/api`).
