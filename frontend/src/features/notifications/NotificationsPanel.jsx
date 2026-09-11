import { useState } from 'react';
import { useNotifications, useMarkAllRead, useMarkRead } from './useNotifications';
import './NotificationsPanel.css';

const FILTERS = [
  { id: 'all', label: 'All' },
  { id: 'unread', label: 'Unread' },
  { id: 'jobs', label: 'Jobs', kinds: ['high_fit_job', 'weekly_digest'] },
  { id: 'status', label: 'Status', kinds: ['application_advanced', 'deadline_reminder'] },
  { id: 'errors', label: 'Errors', kinds: ['source_poll_failed'] },
];

const KIND_ICONS = {
  high_fit_job: '⭐', application_advanced: '📋', deadline_reminder: '⏰',
  source_poll_failed: '⚠️', weekly_digest: '📰',
};

// eslint-disable-next-line no-unused-vars
export default function NotificationsPanel({ onClose }) {
  const { data: notifications, isLoading } = useNotifications();
  const markAllRead = useMarkAllRead();
  const markRead = useMarkRead();
  const [filter, setFilter] = useState('all');

  const filtered = (notifications ?? []).filter((n) => {
    if (filter === 'all') return true;
    if (filter === 'unread') return !n.read;
    const filterDef = FILTERS.find((f) => f.id === filter);
    return filterDef?.kinds?.includes(n.kind);
  });

  const unreadCount = (notifications ?? []).filter((n) => !n.read).length;

  return (
    <div className="notifications-panel" onClick={(e) => e.stopPropagation()}>
      <div className="notifications-panel__header">
        <strong>Notifications {unreadCount > 0 && <span className="badge">{unreadCount}</span>}</strong>
        <button onClick={() => markAllRead.mutate()} className="link-button">Mark all read</button>
      </div>

      <div className="notifications-panel__filters">
        {FILTERS.map((f) => (
          <button
            key={f.id}
            className={filter === f.id ? 'active' : ''}
            onClick={() => setFilter(f.id)}
          >
            {f.label}
          </button>
        ))}
      </div>

      <div className="notifications-panel__list">
        {isLoading && <p className="drawer__muted">Loading…</p>}
        {!isLoading && filtered.length === 0 && (
          <p className="drawer__muted">No notifications here.</p>
        )}
        {filtered.map((n) => (
          <div
            key={n.id}
            className={`notification-item${n.read ? '' : ' notification-item--unread'}`}
            onClick={() => !n.read && markRead.mutate(n.id)}
          >
            <span className="notification-item__icon">{KIND_ICONS[n.kind] ?? '🔔'}</span>
            <div className="notification-item__body">
              <strong>{n.title}</strong>
              {n.body && <p>{n.body.length > 150 ? n.body.slice(0, 150) + '…' : n.body}</p>}
              <span className="drawer__muted">{new Date(n.created_at).toLocaleString()}</span>
            </div>
            {!n.read && <span className="notification-item__dot" aria-hidden="true" />}
          </div>
        ))}
      </div>

      <div className="notifications-panel__footer">
        <span>{notifications?.length ?? 0} notifications total</span>
      </div>
    </div>
  );
}