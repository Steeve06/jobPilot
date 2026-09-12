import { useState } from 'react';
import './SubmitConfirmDialog.css';

export default function SubmitConfirmDialog({ application, onConfirm, onCancel, isSubmitting, error }) {
  const [answers, setAnswers] = useState({
    first_name: '', last_name: '', email: '', phone: '',
  });

  function update(field, value) {
    setAnswers((a) => ({ ...a, [field]: value }));
  }

  return (
    <div className="drawer-overlay" onClick={onCancel}>
      <div className="submit-confirm-dialog" onClick={(e) => e.stopPropagation()}>
        <header className="review-modal__header">
          <h2>Confirm Submission</h2>
          <button onClick={onCancel} aria-label="Close">×</button>
        </header>
        <div className="submit-confirm-dialog__body">
          <p className="drawer__muted">
            This will submit a real application to <strong>{application.posting_company}</strong> for{' '}
            <strong>{application.posting_title}</strong> through their ATS. This cannot be undone.
          </p>

          <div className="submit-confirm-dialog__fields">
            <input placeholder="First name" value={answers.first_name} onChange={(e) => update('first_name', e.target.value)} />
            <input placeholder="Last name" value={answers.last_name} onChange={(e) => update('last_name', e.target.value)} />
            <input placeholder="Email" value={answers.email} onChange={(e) => update('email', e.target.value)} />
            <input placeholder="Phone" value={answers.phone} onChange={(e) => update('phone', e.target.value)} />
          </div>

          {error && <p className="auth-error">{error}</p>}
        </div>
        <footer className="submit-confirm-dialog__actions">
          <button onClick={onCancel} disabled={isSubmitting} className="submit-confirm-dialog__cancel">
            Cancel
          </button>
          <button
            onClick={() => onConfirm(answers)}
            disabled={isSubmitting}
            className="submit-confirm-dialog__confirm"
          >
            {isSubmitting ? 'Submitting…' : 'Confirm & Submit'}
          </button>
        </footer>
      </div>
    </div>
  );
}