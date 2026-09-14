# How to Use JobPilot

This is a practical guide to actually running your job search through the
app — not a feature list, a workflow.

## First-Time Setup

1. **Sign up** at `/signup` (or Google sign-in). This auto-creates a
   "Default" profile.
2. **Onboarding wizard** walks you through: naming a search profile,
   uploading your resume, and adding one job source. You can skip any step
   and do it later — nothing here is one-shot.
3. **If you want separate tracks** (e.g. Backend vs. Frontend roles),
   create additional profiles from the sidebar profile switcher (the
   pencil icon renames, the dropdown's "+ New Profile" creates). Each
   profile has its own resume, search criteria, sources, and applications
   — genuinely separate job searches, not filtered views of one search.

## Getting Real Data Flowing

4. **Add job sources** (Sources page): for each company you're targeting,
   find their board type (Greenhouse/Lever/Ashby — check `jobs.{company}.com`
   or search `site:jobs.{ats}.com`) and the exact board slug. Verify with a
   direct API check before adding if you're unsure — the "Poll Now" button
   confirms immediately whether it worked.
5. **Set a poll interval** you're comfortable with — every 1-2 hours is
   reasonable for active companies; longer for ones you're less urgent about.
6. **Build your search profile** (Sources → Search Profiles): title
   keywords are the main lever — be specific but not overly narrow (recall
   from real testing, `["Backend Engineer"]` alone missed hundreds of
   relevant "Software Engineer" titles — cast a slightly wider net).
7. Once Celery is running (`docker compose up`, or your three local
   terminals), sources poll and postings score **automatically** on their
   own schedule. Use "Run sync now" on the Feed page for an immediate check
   rather than waiting.

## Daily Workflow

8. **Check the Feed**, sorted by Best Fit. Read the AI rationale on each
   card — it tells you *why* it scored what it did, which is often more
   useful than the number itself.
9. For anything you're seriously considering: click **Tailor Resume**.
   Review the diff carefully — check "Edit Manually" if a rewritten bullet
   doesn't sit right with you, since the AI can reword (not just reorder)
   bullets as of the current tailoring logic. Never accept something that
   overstates what you actually did.
10. **Accept & Continue** moves it into your Applications Kanban under
    "Tailoring."
11. Download the tailored DOCX from the application drawer, or — if the
    posting shows "Submit Application" (API-eligible) — use that instead,
    reviewing the confirmation dialog carefully before submitting for real.
12. Drag cards through the pipeline as things progress: Ready → Applied →
    Interview → Offer/Rejected. Add notes as you go (interview prep,
    follow-up reminders) — they're timestamped and stay attached to the
    application permanently.

## Weekly Habits Worth Building

- Check the **Weekly overview** panel's fit distribution — if most
  postings are scoring low, your search profile keywords may be too broad
  or your sources may not match your actual target roles.
- Skim the **Notifications** panel for the daily digest and stale-application
  reminders (an application sitting in "Applied" for 7+ days with no update
  gets flagged automatically).
- Prune job sources that consistently return nothing useful — better to
  have 5 sources that work well than 15 that mostly don't.

## When Something Looks Wrong

- **A tailored bullet claims something you didn't do** — this is exactly
  the risk flagged in the architecture notes (rewriting is prompt-enforced,
  not structurally guaranteed). Use Edit Manually to fix it before
  accepting, and consider tightening `Sources → Tailoring Settings`'
  style notes if it keeps happening.
- **Fit scores all cluster around the same number** — check your resume's
  actual skill breadth against what you're targeting; this happened during
  testing and turned out to be an accurate signal (broad backend skills
  scoring similarly across many backend roles), not a bug — but worth a
  sanity check either way.
- **A source stops returning new postings** — check its "Last Polled"
  timestamp and try "Poll Now" directly; a clear error message will tell
  you if the board slug is wrong or the company moved ATS platforms.

## The Honest Goal

This tool is built to reduce the *mechanical* overhead of job searching —
discovery, tailoring, tracking — so your time goes into the parts that
actually matter: deciding which roles are worth pursuing, and doing well
in the conversations once you're in them. It doesn't replace judgment
about fit, and it shouldn't replace proofreading a tailored resume before
you send it.