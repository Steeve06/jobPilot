import { NavLink, Outlet } from 'react-router-dom';
import ProfileSwitcher from '../components/ProfileSwitcher';
import './AppLayout.css';

const NAV_ITEMS = [
  { to: '/', label: 'Feed', end: true },
  { to: '/applications', label: 'Applications' },
  { to: '/resume', label: 'Resume' },
  { to: '/sources', label: 'Sources' },
  { to: '/settings', label: 'Settings' },
];

export default function AppLayout({ currentUser, onLogout }) {
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
                  aria-current={undefined}
                >
                  {item.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
        <div className="sidebar-footer">
          <span className="user-name">{currentUser?.username}</span>
          <button className="link-button" onClick={onLogout}>Sign out</button>
        </div>
      </aside>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}