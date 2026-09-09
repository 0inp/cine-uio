# Hosting plan (deferred)

**Status:** decided in principle, not implemented. Production currently runs on a
developer laptop. Revisit this document when the site needs a public URL.

**Decided:** 2026-09-09.

## The constraint that drives everything

The scraper needs Playwright and Chromium; the API needs almost nothing. They only
have to be co-located because they share one SQLite file. Both managed platforms
forbid sharing that file between services:

> **Render** — "A persistent disk is accessible by only a single service instance,
> and only at runtime. You can't access a service's disk from any other service."
> Disks are paid-tier only, block zero-downtime deploys, and pin the service to a
> single instance.

> **Fly.io** — "A Machine can only mount one volume at a time and a volume can be
> attached to only one Machine."

So a separate scraper service cannot write to the API's database as long as the
database is a file. Every viable architecture either co-locates the two or drops
SQLite.

## Chosen architecture

Drop SQLite in production; make the scraper a scheduled job that writes to a managed
Postgres, and let the API become a stateless reader.

```
GitHub Actions (daily cron)          Cloudflare Pages
  └─ Playwright + Chromium             └─ React SPA (static, free)
     scrapes Multicines + Supercines            │
     enriches via TMDB                          │ fetch
     writes ─────────┐                          ▼
                     ▼                   Fly.io — FastAPI
              Neon Postgres  ◀─── reads ── stateless, no Chromium
              (free tier)                  shared-cpu-1x
```

| Piece | Choice | Why |
|---|---|---|
| Scraper | GitHub Actions cron | Playwright is a first-class use case there; free minutes on a public repo; per-run logs, history, and a re-run button |
| Database | Neon free tier | 0.5 GB and 100 CU-hours/month against a ~1 MB database. Scale-to-zero after 5 min idle, but projects are **never paused or deleted** for inactivity — the compute resumes on its own |
| API | Fly.io `shared-cpu-1x` | Roughly $2/month. Only affordable *because* the API no longer carries Chromium |
| Frontend | Cloudflare Pages | `vite build` output is static; free, CDN, deploy on push |

Expected cost: about **$2/month**, the API being the only paid line.

### Why not the alternatives

**Everything in one container, keeping SQLite.** Fastest route to a live site and no
database migration. Rejected because it permanently bakes in three limits: a
deployment outage on every release, a single instance forever, and an always-on image
sized for a Chromium that runs five minutes a day. A ceiling, not a foundation.

**VPS + Docker Compose.** No platform constraints at all and the cheapest option, but
it means operating a machine — TLS, updates, backups, monitoring. Rejected for the
operational load, not the technology.

**Supabase instead of Neon.** Comparable free storage, but "Free projects are paused
after 1 week of inactivity" and need a *manual* unpause. For a low-traffic site that
is an operational trap. First paid tier is $25/month.

## Known caveats

- **The Neon connection string lives in GitHub secrets.** Write access to production
  therefore depends on the security of the GitHub account. Create a dedicated Neon
  role for the scraper rather than reusing the project owner.
- **GitHub Actions cron is not punctual.** Runs can drift by minutes or be skipped
  under load. Harmless for a listing refreshed once a day, but worth knowing.
- **Neon cold starts.** The compute suspends after 5 minutes idle; the first visitor
  after a quiet period pays the wake-up latency. Not measured yet. If it turns out to
  be noticeable, a periodic ping hides it.

## Still open

- Domain name.
- Whether Alembic migrations run on API deploy or as a separate step.
- Whether the test suite runs against Postgres in CI (a service container) or keeps
  SQLite. Given that a test/production session-semantics divergence has already
  caused a real gap in this repo, running database tests against Postgres in CI is
  the safer default.

## Sources

- [Render — Persistent Disks](https://render.com/docs/disks)
- [Fly.io — Volumes overview](https://fly.io/docs/volumes/overview/)
- [Fly.io — Pricing](https://fly.io/docs/about/pricing/)
- [Neon — Plans](https://neon.com/docs/introduction/plans)
- [Supabase — Pricing](https://supabase.com/pricing)
