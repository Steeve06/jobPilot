import { useDraggable } from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';

function daysAgo(dateString) {
  const diffMs = Date.now() - new Date(dateString).getTime();
  return Math.floor(diffMs / (1000 * 60 * 60 * 24));
}

export default function ApplicationCard({ application, onOpen }) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: application.id,
  });

  const style = {
    transform: CSS.Translate.toString(transform),
    opacity: isDragging ? 0.5 : 1,
  };

  const isGhosted = application.status === 'ghosted';
  const isOffer = application.status === 'offer';
  const isRejected = application.status === 'rejected';

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      className="app-card"
      role="button"
      tabIndex={0}
      aria-label={`${application.posting_title} at ${application.posting_company}, open details`}
      onClick={() => onOpen(application)}
      onKeyDown={(e) => (e.key === 'Enter' ? onOpen(application) : null)}
    >
      <div className="app-card__avatar" aria-hidden="true">
        {application.posting_company.charAt(0)}
      </div>
      <div className="app-card__body">
        <strong>{application.posting_title}</strong>
        <span className="app-card__company">{application.posting_company}</span>
        <div className="app-card__footer">
          <span>{daysAgo(application.updated_at)}d</span>
          {isGhosted && <span className="badge badge--warning">Ghosted</span>}
          {isOffer && <span className="badge badge--success">Offer</span>}
          {isRejected && <span className="badge badge--danger">Rejected</span>}
        </div>
      </div>
    </div>
  );
}