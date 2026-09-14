# JobPilot — Architecture Review

## System Overview

JobPilot is a modular Django monolith (ADR-001) with a React SPA frontend,
PostgreSQL for persistence, Redis/Celery for background work, and Anthropic's
Claude API behind a single internal AI service boundary (ADR-005).

React SPA (Vite) → Django REST Framework API → PostgreSQL
↓
Celery worker + beat → Redis (broker)
↓
Anthropic API (scoring, tailoring, extraction)


## Domain Apps

| App | Owns |
|---|---|
| `accounts` | User, Profile, multi-profile header-based scoping |
| `resumes` | Resume, Experience/Project/Bullet, TailoredResume, TailoringSettings |
| `search_profiles` | SearchProfile (hard-filter criteria) |
| `job_sources` | JobSource, Celery Beat sync signal |
| `postings` | JobPosting, ScoringLog, PostingDecision, dashboard summary |
| `applications` | Application, StatusEvent, Note, SubmissionLog |
| `ingestion` | Adapters (Greenhouse/Lever/Ashby/RemoteOK/RSS) + submission adapters |
| `scoring` | Hard filters + scoring orchestration |
| `notifications` | Notification, digest/stale-check tasks |
| `ai` | Single AI service boundary — every LLM call goes through here |

## Key Architecture Decisions (ADR summary)

1. **Modular monolith**, not microservices — appropriate at personal scale.
2. **Adapter pattern** for both ingestion and submission — new source types are new classes, not core rewrites.
3. **Profile scoping via `X-Active-Profile` header**, validated server-side against the authenticated user — never trusts the header blindly (see `accounts/services.py::get_active_profile`).
4. **Hard filters before any LLM call** — cost control is structural.
5. **Constrained-rewrite tailoring** (changed from Sprint 11's selection-only to Sprint 12's rewrite-with-source-tracing) — the no-fabrication guarantee is now prompt-enforced, not structurally guaranteed. This is the single most important thing to know if you ever suspect a tailored resume drifted from fact — check `TailoringLog` for that call's raw input/output.
6. **Submission always requires explicit `confirm: true`**, server-enforced independent of the frontend (ADR-006).
7. **Constrained-rewrite calibration is only as good as the prompt** — `ai/service.py` is the one file worth re-reading if scoring or tailoring quality ever feels off.

## Database

Single PostgreSQL instance. No partitioning, no read replicas — appropriate for personal-scale data volume (thousands, not millions, of rows). `dedupe_hash`, `fit_score`, and FK columns are indexed; nothing else needed indexing at this scale during testing.

## Security Posture (as of Sprint 18 hardening)

- Real generated `DJANGO_SECRET_KEY`, session cookies explicit 2-week expiry
- CSRF enforced on all state-changing requests; CORS explicitly whitelisted (no wildcard)
- Passwords validated via Django's built-in strength checks
- Rate limiting on `/api/auth/login/` (10/min) and `/api/auth/signup/` (5/min)
- Prompt-injection mitigation on both scoring and tailoring calls (untrusted job description text is explicitly delimited and framed as data-not-instructions)
- Every profile-scoped endpoint validated against cross-user access (tested explicitly for the multi-profile header mechanism)
- **Not yet done:** `SECURE_SSL_REDIRECT`/`SESSION_COOKIE_SECURE`/`CSRF_COOKIE_SECURE` are `False` — flip these the moment you deploy behind real HTTPS.

## Performance

- Feed list response reduced ~10x (4.8MB → ~470KB) by dropping `description_normalized` from the list serializer (Sprint 15/redesign).
- No caching layer exists — not needed yet at current data volume.
- `RunSyncView` runs synchronously in the request cycle — acceptable for a manual convenience button, would need to move to a Celery task with progress polling if it ever feels slow.

## Accessibility

Basic semantic structure and `aria-label`s exist on interactive elements (drawer, modals, nav). Not audited against WCAG formally — a real gap if this ever needs to meet a compliance bar.

## AI Cost Control

- Hard filters before every LLM call (ADR-004)
- Daily scoring cap (`AI_DAILY_SCORING_CAP`, default 100/day)
- Every call logged with latency; cost estimation itself was flagged as a follow-up (`ai/service.py`'s `_log_call` doesn't compute `cost_estimate` yet) — worth adding if AI spend ever becomes a concern.

## Known Technical Debt

- No pagination on list endpoints (`/api/postings/`, `/api/applications/`) — fine at current scale, will need it if postings grow into the tens of thousands.
- YOE/salary hard filtering was never fully implemented — only title keywords and remote preference are structurally enforced (flagged honestly in Sprint 10).
- RemoteOK/RSS adapters have no dedicated test coverage (explicitly deferred).
- `RunSyncView` is synchronous, not a Celery task.