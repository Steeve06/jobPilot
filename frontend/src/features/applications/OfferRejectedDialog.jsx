export default function OfferRejectedDialog({ onChoose, onCancel }) {
  return (
    <div className="drawer-overlay" onClick={onCancel}>
      <div className="submit-confirm-dialog" style={{ width: 320 }} onClick={(e) => e.stopPropagation()}>
        <header className="review-modal__header">
          <h2>Update outcome</h2>
          <button onClick={onCancel} aria-label="Close">×</button>
        </header>
        <div className="submit-confirm-dialog__body">
          <p className="drawer__muted">What was the outcome for this application?</p>
        </div>
        <footer className="submit-confirm-dialog__actions">
          <button onClick={() => onChoose('rejected')} className="submit-confirm-dialog__cancel">
            Rejected
          </button>
          <button onClick={() => onChoose('offer')} className="submit-confirm-dialog__confirm">
            Offer
          </button>
        </footer>
      </div>
    </div>
  );
}