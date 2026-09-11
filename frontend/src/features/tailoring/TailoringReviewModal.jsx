import { computeExperienceDiff } from './computeDiff';
import './TailoringReviewModal.css';

export default function TailoringReviewModal({
  posting, baseResume, tailoredContent, onRegenerate, onAccept, onClose,
  isRegenerating, isAccepting,
}) {
  const diffs = computeExperienceDiff(baseResume.experiences, tailoredContent.experiences);

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div className="review-modal" onClick={(e) => e.stopPropagation()}>
        <header className="review-modal__header">
          <div>
            <h2>Tailoring Review</h2>
            <p>{posting.title} — {posting.company} {posting.fit_score != null && `· ${posting.fit_score} FIT`}</p>
          </div>
          <button onClick={onClose} aria-label="Close">×</button>
        </header>

        <div className="review-modal__columns">
          <div className="review-modal__column">
            <h3>Base Resume</h3>
            <p className="review-modal__summary">{baseResume.summary}</p>
            {diffs.map((exp) => (
              <div key={exp.company + exp.title} className="review-modal__entry">
                <strong>{exp.title}</strong>
                <span className="review-modal__company">{exp.company}</span>
                <ul>
                  {exp.bulletDiffs.map((b, i) => (
                    <li key={i} className={b.kept ? '' : 'diff-removed'}>{b.text}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          <div className="review-modal__column">
            <h3>Tailored Version</h3>
            <p className="review-modal__summary diff-changed">{tailoredContent.summary}</p>
            {tailoredContent.experiences.map((exp, ei) => {
              const baseExp = diffs[ei];
              // Highlight the whole entry's bullets if any bullet within it
              // was rewritten — precise per-bullet matching isn't reliable
              // once wording can change, so this is a deliberately coarse
              // but honest signal rather than a misleading exact one.
              const anyRewrittenInEntry = baseExp?.bulletDiffs.some((bd) => bd.rewritten) ?? false;

              return (
                <div key={exp.company + exp.title} className="review-modal__entry">
                  <strong>{exp.title}</strong>
                  <span className="review-modal__company">{exp.company}</span>
                  <ul>
                    {exp.bullets.map((b, i) => (
                      <li key={i} className={anyRewrittenInEntry ? 'diff-reordered' : ''}>
                        {b.text}
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>
        </div>

        <div className="review-modal__legend">
          <span><span className="legend-swatch diff-removed" /> Removed</span>
          <span><span className="legend-swatch diff-reordered" /> Reworded / reordered</span>
        </div>

        <footer className="review-modal__actions">
          <button onClick={onRegenerate} disabled={isRegenerating || isAccepting}>
            {isRegenerating ? 'Regenerating…' : 'Regenerate'}
          </button>
          <button onClick={onClose} disabled={isRegenerating || isAccepting}>
            Edit Manually
          </button>
          <button
            onClick={onAccept}
            disabled={isRegenerating || isAccepting}
            className="review-modal__accept"
          >
            {isAccepting ? 'Accepting…' : 'Accept & Continue'}
          </button>
        </footer>
      </div>
    </div>
  );
}