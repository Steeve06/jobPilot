import { useState } from 'react';
import { useTailoringSettings, useUpdateTailoringSettings } from './useTailoringSettings';

export default function TailoringSettingsPanel() {
  const { data, isLoading } = useTailoringSettings();
  const update = useUpdateTailoringSettings();
  const [form, setForm] = useState(null);

  if (isLoading || !form && data) {
    if (data && !form) setForm(data);
  }
  if (isLoading || !form) return <p className="feed-page__state">Loading tailoring settings…</p>;

  function handleSubmit(e) {
    e.preventDefault();
    update.mutate(form);
  }

  return (
    <form onSubmit={handleSubmit} className="search-profile-form">
      <label>Professional Title Override</label>
      <input
        value={form.professional_title}
        onChange={(e) => setForm({ ...form, professional_title: e.target.value })}
        placeholder="e.g. Senior Software Engineer"
      />

      <label>Style Notes</label>
      <textarea
        rows={3}
        value={form.style_notes}
        onChange={(e) => setForm({ ...form, style_notes: e.target.value })}
        placeholder="Any additional style guidance for tailored resumes…"
      />

      <div className="repeater-entry__row">
        <div>
          <label>Max Bullets / Experience</label>
          <input
            type="number"
            value={form.max_bullets_per_experience ?? ''}
            onChange={(e) => setForm({ ...form, max_bullets_per_experience: e.target.value || null })}
          />
        </div>
        <div>
          <label>Max Bullets / Project</label>
          <input
            type="number"
            value={form.max_bullets_per_project ?? ''}
            onChange={(e) => setForm({ ...form, max_bullets_per_project: e.target.value || null })}
          />
        </div>
      </div>

      <label>
        <input
          type="checkbox"
          checked={form.avoid_em_dash}
          onChange={(e) => setForm({ ...form, avoid_em_dash: e.target.checked })}
        /> Avoid em dashes
      </label>
      <label>
        <input
          type="checkbox"
          checked={form.exclude_company_name_from_body}
          onChange={(e) => setForm({ ...form, exclude_company_name_from_body: e.target.checked })}
        /> Never mention company name in resume body
      </label>

      <button type="submit" className="save-button" disabled={update.isPending}>
        {update.isPending ? 'Saving…' : 'Save'}
      </button>
      {update.isSuccess && <p className="resume-page__success">Saved.</p>}
    </form>
  );
}