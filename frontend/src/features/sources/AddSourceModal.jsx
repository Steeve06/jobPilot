import { useState } from 'react';
import { useCreateJobSource } from './useJobSources';

const SUPPORTED_TYPES = [
  { value: 'greenhouse', label: 'Greenhouse', configField: 'board_slug', configLabel: 'Board slug' },
  { value: 'lever', label: 'Lever', configField: 'board_slug', configLabel: 'Board slug' },
  { value: 'ashby', label: 'Ashby', configField: 'board_slug', configLabel: 'Board name' },
  { value: 'remoteok', label: 'RemoteOK', configField: 'keyword', configLabel: 'Keyword filter (optional)' },
  { value: 'rss', label: 'RSS Feed', configField: 'feed_url', configLabel: 'Feed URL' },
];

export default function AddSourceModal({ onClose }) {
  const createSource = useCreateJobSource();
  const [companyName, setCompanyName] = useState('');
  const [type, setType] = useState('greenhouse');
  const [configValue, setConfigValue] = useState('');
  const [pollInterval, setPollInterval] = useState(120);

  const selectedType = SUPPORTED_TYPES.find((option) => option.value === type) ?? SUPPORTED_TYPES[0];

  function handleSubmit(e) {
    e.preventDefault();

    const config = {};
    if (configValue.trim()) {
      config[selectedType.configField] = configValue.trim();
    }

    createSource.mutate(
      {
        company_name: companyName,
        type,
        config,
        poll_interval_minutes: pollInterval,
        enabled: true,
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

          <label>{selectedType.configLabel}</label>
          <input
            value={configValue}
            onChange={(e) => setConfigValue(e.target.value)}
            placeholder={type === 'remoteok' ? 'e.g. frontend' : 'e.g. stripe'}
            required={type !== 'remoteok'}
          />

          <label>Poll Interval (minutes)</label>
          <input
            type="number"
            value={pollInterval}
            onChange={(e) => setPollInterval(parseInt(e.target.value))}
            placeholder="e.g. 120"
            min="1"
            required
          />
          
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