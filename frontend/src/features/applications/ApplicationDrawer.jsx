import { useState } from 'react';
import { useUpdateApplication, useAddNote } from './useApplications';

import './ApplicationDrawer.css';

const ALL_STATUSES = [
  'discovered', 'tailoring', 'ready', 'applied',
  'oa_interview', 'offer', 'rejected', 'ghosted',
];

export default function ApplicationDrawer({ application, onClose }) {
  const updateApplication = useUpdateApplication();
  const addNote = useAddNote();
  const [noteText, setNoteText] = useState('');
  const [nextActionDate, setNextActionDate] = useState(application.next_action_date ?? '');

  function handleStatusChange(e) {
    updateApplication.mutate({ id: application.id, status: e.target.value });
  }

  function handleNextActionBlur() {
    if (nextActionDate !== application.next_action_date) {
      updateApplication.mutate({ id: application.id, next_action_date: nextActionDate || null });
    }
  }

  function handleAddNote(e) {
    e.preventDefault();
    if (!noteText.trim()) return;
    addNote.mutate(
      { applicationId: application.id, text: noteText },
      { onSuccess: () => setNoteText('') },
    );
  }

  async function handleDownloadTailoredResume() {
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
    const response = await fetch(
      `${API_BASE_URL}/api/tailored-resumes/${application.tailored_resume}/download/`,
      { credentials: 'include' },
    );
    if (!response.ok) {
      alert('Could not download the tailored resume. Try again.');
      return;
    }
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `tailored_resume_${application.posting_company}.docx`;
    a.click();
    window.URL.revokeObjectURL(url);
  }

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <aside
        className="drawer"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-label={`${application.posting_title} details`}
      >
        <header className="drawer__header">
          <div>
            <h2>{application.posting_title}</h2>
            <p>{application.posting_company}</p>
          </div>
          <button onClick={onClose} aria-label="Close">×</button>
        </header>

        <section className="drawer__section">
          <label htmlFor="status-select">Status</label>
          <select id="status-select" value={application.status} onChange={handleStatusChange}>
            {ALL_STATUSES.map((s) => (
              <option key={s} value={s}>{s.replace('_', ' ')}</option>
            ))}
          </select>
        </section>

        <section className="drawer__section">
          <label htmlFor="next-action">Next action date</label>
          <input
            id="next-action"
            type="date"
            value={nextActionDate ?? ''}
            onChange={(e) => setNextActionDate(e.target.value)}
            onBlur={handleNextActionBlur}
          />
        </section>

        <section className="drawer__section">
          <h4>Resume</h4>
          {application.tailored_resume ? (
            <button onClick={handleDownloadTailoredResume} className="import-button">
              Download tailored resume
            </button>
          ) : (
            <p className="drawer__muted">No tailored resume yet.</p>
          )}
        </section>

        <section className="drawer__section">
          <h4>Timeline</h4>
          <ol className="drawer__timeline">
            {application.status_events.map((event) => (
              <li key={event.id}>
                <span className="drawer__timeline-status">{event.status.replace('_', ' ')}</span>
                <span className="drawer__timeline-date">
                  {new Date(event.occurred_at).toLocaleDateString()}
                  {event.source === 'gmail_auto' && !event.confirmed && ' (auto-detected, unconfirmed)'}
                </span>
              </li>
            ))}
          </ol>
        </section>

        <section className="drawer__section">
          <h4>Notes</h4>
          <ul className="drawer__notes">
            {application.notes.map((note) => (
              <li key={note.id}>
                <p>{note.text}</p>
                <span className="drawer__muted">{new Date(note.created_at).toLocaleDateString()}</span>
              </li>
            ))}
          </ul>
          <form onSubmit={handleAddNote} className="drawer__note-form">
            <textarea
              value={noteText}
              onChange={(e) => setNoteText(e.target.value)}
              placeholder="Add a note…"
              rows={2}
            />
            <button type="submit">Add</button>
          </form>
        </section>
      </aside>
    </div>
  );
}