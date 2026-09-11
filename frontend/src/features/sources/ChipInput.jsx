import { useState } from 'react';

export default function ChipInput({ values, onChange, placeholder }) {
  const [draft, setDraft] = useState('');

  function add() {
    const v = draft.trim();
    if (v && !values.includes(v)) onChange([...values, v]);
    setDraft('');
  }

  return (
    <div>
      <div className="chip-list">
        {values.map((v) => (
          <span key={v} className="chip">
            {v}
            <button type="button" onClick={() => onChange(values.filter((x) => x !== v))} aria-label={`Remove ${v}`}>×</button>
          </span>
        ))}
      </div>
      <div className="chip-input-row">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); add(); } }}
          placeholder={placeholder}
        />
        <button type="button" onClick={add}>+</button>
      </div>
    </div>
  );
}