import { useState } from 'react';
import JobCard from '../features/feed/JobCard';
import { usePostings, useDashboardSummary } from '../features/feed/usePostings';
import './FeedPage.css';

export default function FeedPage() {
  const [filters, setFilters] = useState({ status: 'new', ordering: '-fit_score' });
  const { data: postings, isLoading, isError } = usePostings(filters);
  const { data: summary } = useDashboardSummary();

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
          <JobCard key={posting.id} posting={posting} />
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
    </div>
  );
}