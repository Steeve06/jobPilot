import { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import ProfileSwitcher from '../components/ProfileSwitcher';
import NotificationsPanel from '../features/notifications/NotificationsPanel';
import { useNotifications } from '../features/notifications/useNotifications';
import './AppLayout.css';

const NAV_ITEMS = [
  { to: '/', label: 'Feed', end: true },
  { to: '/applications', label: 'Applications' },
  { to: '/resume', label: 'Resume' },
  { to: '/sources', label: 'Sources' },
  { to: '/settings', label: 'Settings' },
];

export default function AppLayout({ currentUser, onLogout }) {
  const [showNotifications, setShowNotifications] = useState(false);
  const { data: notifications } = useNotifications();
  const unreadCount = (notifications ?? []).filter((n) => !n.read).length;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <ProfileSwitcher profiles={currentUser?.profiles ?? []} />
        <nav aria-label="Primary">
          <ul className="nav-list">
            {NAV_ITEMS.map((item) => (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  end={item.end}
                  className={({ isActive }) => `nav-link${isActive ? ' nav-link--active' : ''}`}
                >
                  {item.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        <div className="sidebar-bottom-links">
          <div style={{ position: 'relative' }}>
            <button
              className="nav-link notifications-trigger"
              onClick={() => setShowNotifications((s) => !s)}
            >
              Notifications {unreadCount > 0 && <span className="badge">{unreadCount}</span>}
            </button>
            {showNotifications && (
              <NotificationsPanel onClose={() => setShowNotifications(false)} />
            )}
          </div>
        </div>

        <div className="sidebar-footer">
          <span className="user-name">{currentUser?.username}</span>
          <button className="link-button" onClick={onLogout}>Sign out</button>
        </div>
      </aside>
      <main className="app-main">
        {showNotifications && (
          <div
            style={{ position: 'fixed', inset: 0, zIndex: 40 }}
            onClick={() => setShowNotifications(false)}
          />
        )}
        <Outlet />
      </main>
    </div>
  );
}