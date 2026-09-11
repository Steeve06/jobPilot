import { useState } from 'react';
import ChipInput from './ChipInput';

export default function SearchProfileForm({ initial, onSubmit, onCancel, isSubmitting }) {
  const [form, setForm] = useState(initial ?? {
    name: '', title_keywords: [], excluded_keywords: [], locations: [],
    yoe_min: '', yoe_max: '', remote_ok: true, salary_floor: '', active: true,
  });

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  function handleSubmit(e) {
    e.preventDefault();
    onSubmit({
      ...form,
      yoe_min: form.yoe_min === '' ? null : Number(form.yoe_min),
      yoe_max: form.yoe_max === '' ? null : Number(form.yoe_max),
      salary_floor: form.salary_floor === '' ? null : Number(form.salary_floor),
    });
  }

  return (
    <form onSubmit={handleSubmit} className="search-profile-form">
      <label>Profile Name</label>
      <input value={form.name} onChange={(e) => update('name', e.target.value)} required />

      <label>Title Keywords</label>
      <ChipInput values={form.title_keywords} onChange={(v) => update('title_keywords', v)} placeholder="Add a job title keyword…" />

      <label>Excluded Keywords</label>
      <ChipInput values={form.excluded_keywords} onChange={(v) => update('excluded_keywords', v)} placeholder="Add an excluded keyword…" />

      <label>Locations</label>
      <ChipInput values={form.locations} onChange={(v) => update('locations', v)} placeholder="Add a location…" />

      <div className="repeater-entry__row">
        <div>
          <label>YOE Min</label>
          <input type="number" value={form.yoe_min} onChange={(e) => update('yoe_min', e.target.value)} />
        </div>
        <div>
          <label>YOE Max</label>
          <input type="number" value={form.yoe_max} onChange={(e) => update('yoe_max', e.target.value)} />
        </div>
      </div>

      <label>Salary Floor</label>
      <input type="number" value={form.salary_floor} onChange={(e) => update('salary_floor', e.target.value)} />

      <label>
        <input type="checkbox" checked={form.remote_ok} onChange={(e) => update('remote_ok', e.target.checked)} />
        {' '}Remote OK
      </label>
      <label>
        <input type="checkbox" checked={form.active} onChange={(e) => update('active', e.target.checked)} />
        {' '}Active
      </label>

      <div className="add-source-modal__actions">
        <button type="button" onClick={onCancel}>Cancel</button>
        <button type="submit" className="save-button" disabled={isSubmitting}>
          {isSubmitting ? 'Saving…' : 'Save'}
        </button>
      </div>
    </form>
  );
}