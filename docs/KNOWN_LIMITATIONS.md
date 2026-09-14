# JobPilot — Known Limitations

Honest list, not a marketing page.

- **Tailoring can rewrite bullet wording**, not just select/reorder (changed in Sprint 12). The no-fabrication guarantee is prompt-enforced, not structurally guaranteed. Spot-check `TailoringLog` entries occasionally.
- **Auto-submit only works for jobs whose specific ATS board has API submission enabled** — many Greenhouse/Lever-hosted jobs don't, and will cleanly fail with a clear error rather than silently succeed. This is expected, not a bug.
- **YOE and salary hard filtering aren't real** — only title keywords and remote preference are structurally enforced in the scoring pipeline.
- **Meta, Google, Amazon, Microsoft, Cox** (per the original target list) have no public job API — they'd need a manual-scrape adapter, which was never built. RSS is the closest fit for LinkedIn/Indeed discovery only.
- **RemoteOK and RSS adapters have no automated test coverage** — verified manually once, not regression-tested.
- **No pagination** on postings/applications lists — fine now, will need it if data volume grows substantially.
- **`RunSyncView` blocks the request** while polling+scoring runs — can take tens of seconds for several active sources.
- **Not accessibility-audited** — basic semantic markup exists, no formal WCAG pass.
- **HTTPS/production security settings are off by default** — must be flipped manually before any real deployment (see DEPLOYMENT.md).
- **Gmail-based automatic status detection** (flagged in scope back in Sprint 15's ADR-008) was never built — status changes are still fully manual.