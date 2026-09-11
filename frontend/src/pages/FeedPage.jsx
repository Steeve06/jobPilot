import { useState } from 'react';
import JobCard from '../features/feed/JobCard';
import { usePostings, useDashboardSummary } from '../features/feed/usePostings';
import { useResume } from '../features/resume/useResume';
import { useGenerateTailoredResume, useAcceptTailoredResume } from '../features/tailoring/useTailoring';
import TailoringReviewModal from '../features/tailoring/TailoringReviewModal';
import './FeedPage.css';

export default function FeedPage() {
  const [filters, setFilters] = useState({ status: 'new', ordering: '-fit_score' });
  const { data: postings, isLoading, isError } = usePostings(filters);
  const { data: summary } = useDashboardSummary();
  const { data: baseResume } = useResume();

  const [reviewState, setReviewState] = useState(null); // { posting, tailoredResumeId, content } | null
  const generate = useGenerateTailoredResume();
  const accept = useAcceptTailoredResume();

  function handleTailor(posting) {
    generate.mutate(posting.id, {
      onSuccess: (data) => {
        setReviewState({ posting, tailoredResumeId: data.tailored_resume_id, content: data.content });
      },
    });
  }

  function handleRegenerate() {
    generate.mutate(reviewState.posting.id, {
      onSuccess: (data) => {
        setReviewState((prev) => ({ ...prev, tailoredResumeId: data.tailored_resume_id, content: data.content }));
      },
    });
  }

  function handleAccept() {
    accept.mutate(reviewState.tailoredResumeId, {
      onSuccess: () => setReviewState(null),
    });
  }

  return (
    <div className="feed-page">
      <div className="feed-page__main">
        <div className="feed-page__filters">
          <select
            value={filters.status}
            onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}
          >
            <option value="new">New</option>
            <option value="saved">Saved</option>
            <option value="skipped">Skipped</option>
          </select>
          <select
            value={filters.ordering}
            onChange={(e) => setFilters((f) => ({ ...f, ordering: e.target.value }))}
          >
            <option value="-fit_score">Best Fit</option>
            <option value="-discovered_at">Newest</option>
          </select>
        </div>

        {isLoading && <p className="feed-page__state">Loading postings…</p>}
        {isError && <p className="feed-page__state">Couldn't load the feed. Try refreshing.</p>}
        {!isLoading && !isError && postings?.length === 0 && (
          <p className="feed-page__state">
            No postings match these filters yet. New matches will appear here as sources are polled.
          </p>
        )}

        {postings?.map((posting) => (
          <JobCard key={posting.id} posting={posting} onTailor={handleTailor} />
        ))}
      </div>

      {summary && (
        <aside className="feed-page__sidebar">
          <h4>This Week</h4>
          <dl>
            <dt>New postings</dt><dd>{summary.new_postings_this_week}</dd>
            <dt>Applications sent</dt><dd>{summary.applications_sent_this_week}</dd>
            <dt>Avg fit score</dt><dd>{summary.avg_fit_score ?? '—'}</dd>
          </dl>
        </aside>
      )}

      {reviewState && baseResume && (
        <TailoringReviewModal
          posting={reviewState.posting}
          baseResume={baseResume}
          tailoredContent={reviewState.content}
          onRegenerate={handleRegenerate}
          onAccept={handleAccept}
          onClose={() => setReviewState(null)}
          isRegenerating={generate.isPending}
          isAccepting={accept.isPending}
        />
      )}
    </div>
  );
}