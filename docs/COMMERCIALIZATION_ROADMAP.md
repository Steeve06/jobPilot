# JobPilot — Commercialization Roadmap

Per the original framing (Sprint 0): this is a personal tool to prove out
over 2-3 months of real use, with a decision point after that — not a
pre-committed SaaS plan. This document exists so that decision, if you
reach it, has a concrete starting point rather than a blank page.

## Decision Point Checklist (revisit after your 2-3 month trial)

- Did it genuinely save you time in your job search?
- Would you pay for this yourself, if someone else built it?
- Do you know 3+ other people who'd want the same thing?

If yes to most of these, the path below is a reasonable starting sketch.

## What Would Need to Change

**Multi-tenancy** — `Profile` already cleanly separates data per search-track;
a `Tenant` layer above `User` would sit on top without touching that scoping
logic (per ADR-003's original design intent).

**Billing** — Stripe or similar, metering AI calls (scoring/tailoring) as
the natural usage unit, since that's the real marginal cost per user.

**AI cost at scale** — the daily cap mechanism already exists per-profile;
would need per-tenant tiers and real `cost_estimate` tracking (currently
unimplemented — see ARCHITECTURE.md's technical debt list).

**Infrastructure** — current Docker Compose setup is fine for hundreds of
users; thousands+ would need managed Postgres/Redis and possibly split
Celery queues by task type (ingestion/scoring/tailoring separately).

**Legal** — Terms of Service, Privacy Policy, and a real answer to "what
happens to a user's resume/career data if they delete their account" —
none of this exists yet and all of it is a genuine legal review, not
something to self-serve from a template without care.

**Auth** — already solid (Google OAuth + password, per Sprint 16) — this
part scales to commercial use with minimal change.

## What Would NOT Need to Change

The core domain model, the adapter pattern for sources/submission, the AI
service boundary, and the modular app structure are all already built in a
way that supports this transition without a rewrite — that was the explicit
intent of ADR-001/002/003/005 from day one.