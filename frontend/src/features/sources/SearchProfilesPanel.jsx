import { useState } from 'react';
import SearchProfileForm from './SearchProfileForm';
import {
  useSearchProfiles, useCreateSearchProfile, useUpdateSearchProfile, useDeleteSearchProfile,
} from './useSearchProfiles';

export default function SearchProfilesPanel() {
  const { data: profiles, isLoading } = useSearchProfiles();
  const create = useCreateSearchProfile();
  const update = useUpdateSearchProfile();
  const remove = useDeleteSearchProfile();
  const [editing, setEditing] = useState(null); // null | 'new' | profile object

  function handleSubmit(data) {
    if (editing === 'new') {
      create.mutate(data, { onSuccess: () => setEditing(null) });
    } else {
      update.mutate({ id: editing.id, ...data }, { onSuccess: () => setEditing(null) });
    }
  }

  if (isLoading) return <p className="feed-page__state">Loading search profiles…</p>;

  if (editing) {
    return (
      <SearchProfileForm
        initial={editing === 'new' ? null : editing}
        onSubmit={handleSubmit}
        onCancel={() => setEditing(null)}
        isSubmitting={create.isPending || update.isPending}
      />
    );
  }

  return (
    <div>
      <div className="sources-page__toolbar">
        <button className="save-button" onClick={() => setEditing('new')}>+ New Search Profile</button>
      </div>

      {profiles?.length === 0 && <p className="feed-page__state">No search profiles yet.</p>}

      <div className="search-profile-cards">
        {profiles?.map((p) => (
          <div key={p.id} className="repeater-entry">
            <div className="repeater-entry__row" style={{ justifyContent: 'space-between' }}>
              <strong>{p.name}</strong>
              <span className={`badge ${p.active ? 'badge--remote' : ''}`}>{p.active ? 'Active' : 'Paused'}</span>
            </div>
            <p className="drawer__muted">
              {p.title_keywords.join(', ') || 'No title keywords'}
              {p.locations.length > 0 && ` · ${p.locations.join(', ')}`}
              {p.remote_ok && ' · Remote OK'}
            </p>
            <div className="job-card__actions">
              <button onClick={() => setEditing(p)}>Edit</button>
              <button className="remove-button" onClick={() => remove.mutate(p.id)}>Delete</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}