import { useState } from 'react';

export default function ProfileSwitcher({ profiles }) {
  const [selectedId, setSelectedId] = useState(
    profiles.find((p) => p.is_default)?.id ?? profiles[0]?.id,
  );
  if (profiles.length === 0) {
    return <div style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)' }}>No profile yet</div>;
  }

  return (
    <div style={{ marginBottom: 'var(--space-2)' }}>
      <select
        value={selectedId}
        onChange={(e) => setSelectedId(Number(e.target.value))}
        aria-label="Active search profile"
        style={{
          width: '100%',
          padding: 'var(--space-2)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-sm)',
          background: 'var(--color-surface)',
        }}
      >
        {profiles.map((p) => (
          <option key={p.id} value={p.id}>{p.name}</option>
        ))}
      </select>
    </div>
  );
}