import { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AppLayout from './layouts/AppLayout';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import FeedPage from './pages/FeedPage';
import ApplicationsPage from './pages/ApplicationsPage';
import ResumePage from './pages/ResumePage';
import SourcesPage from './pages/SourcesPage';
import SettingsPage from './pages/SettingsPage';
import { getCurrentUser, logout } from './services/apiClient';

const queryClient = new QueryClient();

function ProtectedShell({ currentUser, onLogout }) {
  if (!currentUser) return <Navigate to="/login" replace />;
  return <AppLayout currentUser={currentUser} onLogout={onLogout} />;
}

export default function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [checkedAuth, setCheckedAuth] = useState(false);

  if (!checkedAuth) {
    getCurrentUser()
      .then(setCurrentUser)
      .catch(() => setCurrentUser(null))
      .finally(() => setCheckedAuth(true));
  }

  async function handleLogout() {
    await logout();
    setCurrentUser(null);
  }

  if (!checkedAuth) return null;

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route
            path="/login"
            element={
              currentUser
                ? <Navigate to="/" replace />
                : <LoginPage onLoggedIn={() => getCurrentUser().then(setCurrentUser)} />
            }
          />
          <Route
            path="/signup"
            element={
              currentUser
                ? <Navigate to="/" replace />
                : <SignupPage onLoggedIn={() => getCurrentUser().then(setCurrentUser)} />
            }
          />
          <Route element={<ProtectedShell currentUser={currentUser} onLogout={handleLogout} />}>
            <Route path="/" element={<FeedPage />} />
            <Route path="/applications" element={<ApplicationsPage />} />
            <Route path="/resume" element={<ResumePage />} />
            <Route path="/sources" element={<SourcesPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}