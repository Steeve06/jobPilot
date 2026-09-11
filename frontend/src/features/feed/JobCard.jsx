import FitScoreBadge from './FitScoreBadge';
import { useDecidePosting, useTailorPosting } from './usePostings';
import './JobCard.css';

export default function JobCard({ posting }) {
  const decide = useDecidePosting();
  const tailor = useTailorPosting();

  return (
    <article className="job-card">
      <div className="job-card__avatar" aria-hidden="true">
        {posting.company.charAt(0)}
      </div>

      <div className="job-card__body">
        <div className="job-card__header">
          <h3>{posting.title}</h3>
          <span className="job-card__meta">
            {posting.company} · {posting.location || 'Location n/a'}
            {posting.remote && <span className="badge badge--remote">Remote</span>}
          </span>
        </div>

        {posting.fit_rationale && (
          <p className="job-card__rationale">{posting.fit_rationale}</p>
        )}

        <div className="job-card__footer">
          <span className="job-card__timestamp">
            {new Date(posting.discovered_at).toLocaleDateString()}
          </span>
          <span className="badge">{posting.source_type}</span>

          <div className="job-card__actions">
            <button onClick={() => tailor.mutate(posting.id)} disabled={tailor.isPending}>
              {tailor.isPending ? 'Tailoring…' : tailor.isSuccess ? 'Tailored ✓' : 'Tailor Resume'}
            </button>
            <button
              onClick={() => decide.mutate({ postingId: posting.id, decision: 'saved' })}
              disabled={posting.decision === 'saved'}
            >
              {posting.decision === 'saved' ? 'Saved' : 'Save'}
            </button>
            <button
              onClick={() => decide.mutate({ postingId: posting.id, decision: 'skipped' })}
              disabled={posting.decision === 'skipped'}
            >
              Skip
            </button>
          </div>
        </div>
        {tailor.isError && (
          <p className="job-card__error">{tailor.error.message}</p>
        )}
      </div>

      <FitScoreBadge score={posting.fit_score} />
    </article>
  );
}