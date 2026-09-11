import { useState } from 'react';
import { useCreateJobSource } from './useJobSources';

const SUPPORTED_TYPES = [
  { value: 'greenhouse', label: 'Greenhouse' },
  { value: 'lever', label: 'Lever' },
];

export default function AddSourceModal({ onClose }) {
  const createSource = useCreateJobSource();
  const [companyName, setCompanyName] = useState('');
  const [type, setType] = useState('greenhouse');
  const [boardSlug, setBoardSlug] = useState('');
  const [pollInterval, setPollInterval] = useState(120);

  function handleSubmit(e) {
    e.preventDefault();
    createSource.mutate(
      {
        company_name: companyName, type,
        config: { board_slug: boardSlug },
        poll_interval_minutes: pollInterval, enabled: true,
      },
      { onSuccess: onClose },
    );
  }

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div className="add-source-modal" onClick={(e) => e.stopPropagation()}>
        <h3>Add Job Source</h3>
        <form onSubmit={handleSubmit}>
          <label>Company</label>
          <input value={companyName} onChange={(e) => setCompanyName(e.target.value)} placeholder="e.g. Stripe" required />

          <label>ATS Type</label>
          <select value={type} onChange={(e) => setType(e.target.value)}>
            {SUPPORTED_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
          </select>

          <label>Board URL / Slug</label>
          <input value={boardSlug} onChange={(e) => setBoardSlug(e.target.value)} placeholder="e.g. stripe" required />
          <label>Poll Interval (minutes)</label>
          <input
            type="number"
            value={pollInterval}
            onChange={(e) => setPollInterval(parseInt(e.target.value))}
            placeholder="e.g. 120"
            min="1"
            required
          />
          <p className="drawer__muted">
            Ashby, RemoteOK, and RSS adapters aren't built yet (coming in a future sprint).
          </p>

          {createSource.isError && <p className="resume-page__error">{createSource.error.message}</p>}

          <div className="add-source-modal__actions">
            <button type="button" onClick={onClose}>Cancel</button>
            <button type="submit" className="save-button" disabled={createSource.isPending}>
              {createSource.isPending ? 'Adding…' : 'Add Source'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}