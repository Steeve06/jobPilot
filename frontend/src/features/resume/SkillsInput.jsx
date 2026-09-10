import { useState } from 'react';

export default function SkillsInput({ skills, onChange }) {
  const [draft, setDraft] = useState('');

  function addSkill() {
    const value = draft.trim();
    if (value && !skills.includes(value)) {
      onChange([...skills, value]);
    }
    setDraft('');
  }

  function removeSkill(skill) {
    onChange(skills.filter((s) => s !== skill));
  }

  return (
    <div>
      <div className="chip-list">
        {skills.map((skill) => (
          <span key={skill} className="chip">
            {skill}
            <button type="button" onClick={() => removeSkill(skill)} aria-label={`Remove ${skill}`}>×</button>
          </span>
        ))}
      </div>
      <div className="chip-input-row">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addSkill(); } }}
          placeholder="Add skill…"
        />
        <button type="button" onClick={addSkill}>+</button>
      </div>
    </div>
  );
}