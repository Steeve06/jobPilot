import { useState } from 'react';
import AddSourceModal from '../features/sources/AddSourceModal';
import {
  useJobSources, useUpdateJobSource, useDeleteJobSource, usePollJobSourceNow,
} from '../features/sources/useJobSources';
import SearchProfilesPanel from '../features/sources/SearchProfilesPanel';
import TailoringSettingsPanel from '../features/tailoring/TailoringSettingsPanel';
import './SourcesPage.css';

function PollIntervalInput({ source, onSave }) {
  const [value, setValue] = useState(source.poll_interval_minutes);

  function handleBlur() {
    const numeric = Number(value);
    if (numeric > 0 && numeric !== source.poll_interval_minutes) {
      onSave(numeric);
    } else {
      setValue(source.poll_interval_minutes); // revert if invalid/unchanged
    }
  }

  return (
    <span>
      <input
        type="number" min="1"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onBlur={handleBlur}
        onKeyDown={(e) => { if (e.key === 'Enter') e.target.blur(); }}
        style={{ width: 60 }}
      />m
    </span>
  );
}

export default function SourcesPage() {
  const [tab, setTab] = useState('sources');
  const { data: sources, isLoading } = useJobSources();
  const updateSource = useUpdateJobSource();
  const deleteSource = useDeleteJobSource();
  const pollNow = usePollJobSourceNow();
  const [showAddModal, setShowAddModal] = useState(false);
  const [pollResult, setPollResult] = useState(null);

  function handleToggleEnabled(source) {
    updateSource.mutate({ id: source.id, enabled: !source.enabled });
  }

  function handlePollNow(source) {
    pollNow.mutate(source.id, {
      onSuccess: (result) => setPollResult({ id: source.id, ...result }),
    });
  }

  function handleDelete(source) {
    if (window.confirm(`Remove ${source.company_name} as a job source? This does not delete already-discovered postings.`)) {
      deleteSource.mutate(source.id);
    }
  }

  return (
    <div className="sources-page">
      <div className="sources-page__tabs">
        <button className={tab === 'sources' ? 'active' : ''} onClick={() => setTab('sources')}>Job Sources</button>
        <button className={tab === 'search-profiles' ? 'active' : ''} onClick={() => setTab('search-profiles')}>Search Profiles</button>
        <button className={tab === 'tailoring' ? 'active' : ''} onClick={() => setTab('tailoring')}>Tailoring Settings</button>
      </div>

      {tab === 'sources' && (
        <>
          <div className="sources-page__toolbar">
            <button className="save-button" onClick={() => setShowAddModal(true)}>+ Add Source</button>
          </div>

          {isLoading && <p className="feed-page__state">Loading sources…</p>}

          {sources?.length === 0 && (
            <p className="feed-page__state">No job sources yet. Add one to start discovering postings.</p>
          )}

          {sources?.length > 0 && (
            <table className="sources-table">
              <thead>
                <tr>
                  <th>Company</th><th>ATS Type</th><th>Poll Interval</th>
                  <th>Last Polled</th><th>Status</th><th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {sources.map((s) => (
                  <tr key={s.id}>
                    <td>{s.company_name}</td>
                    <td><span className="badge">{s.type_display}</span></td>
                    <td>
                      <PollIntervalInput
                        key={`${s.id}-${s.poll_interval_minutes}`}
                        source={s}
                        onSave={(value) => updateSource.mutate({ id: s.id, poll_interval_minutes: value })}
                      />
                    </td>
                    <td>{s.last_polled_at ? new Date(s.last_polled_at).toLocaleString() : '—'}</td>
                    <td>
                      <button onClick={() => handleToggleEnabled(s)} className="link-button">
                        {s.enabled ? 'Active' : 'Paused'}
                      </button>
                    </td>
                    <td className="sources-table__actions">
                      <button onClick={() => handlePollNow(s)} disabled={pollNow.isPending} className="poll-now-button">
                        Poll Now
                      </button>
                      <button onClick={() => handleDelete(s)} className="remove-button">Remove</button>
                      {pollResult?.id === s.id && (
                        <span className="drawer__muted">
                          {' '}+{pollResult.created} new, {pollResult.skipped_duplicates} dupes
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}

      {tab === 'search-profiles' && <SearchProfilesPanel />}
      {tab === 'tailoring' && <TailoringSettingsPanel />}

      {showAddModal && <AddSourceModal onClose={() => setShowAddModal(false)} />}
    </div>
  );
}