import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ensureCsrfCookie, signup } from '../services/apiClient';
import './AuthPages.css';

export default function SignupPage({ onLoggedIn }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    try {
      await ensureCsrfCookie();
      await signup(username, password);
      onLoggedIn();
      navigate('/');
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-card__logo">
          <span className="auth-card__logo-icon">J</span>
          <span className="auth-card__logo-text">JobPilot</span>
        </div>

        <h1>Create your account</h1>
        <p className="auth-card__subtitle">Start automating your job search</p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <input
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button type="submit">Sign up</button>
        </form>

        {error && <p className="auth-error">{error}</p>}

        <p className="auth-footer">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}