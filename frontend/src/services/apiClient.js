const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

function getCookie(name) {
  const match = document.cookie.match(new RegExp(`(^| )${name}=([^;]+)`));
  return match ? match[2] : null;
}

export async function apiRequest(path, options = {}) {
  const isWrite = options.method && options.method !== 'GET';

  const response = await fetch(`${API_BASE_URL}${path}`, {
    credentials: 'include', // send/receive the Django session cookie
    headers: {
      'Content-Type': 'application/json',
      ...(isWrite ? { 'X-CSRFToken': getCookie('csrftoken') } : {}),
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `API request failed: ${response.status}`);
  }

  return response.json();
}

export async function ensureCsrfCookie() {
  return apiRequest('/api/auth/csrf/');
}

export async function login(username, password) {
  return apiRequest('/api/auth/login/', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
}

export async function logout() {
  return apiRequest('/api/auth/logout/', { method: 'POST' });
}

export async function getCurrentUser() {
  return apiRequest('/api/auth/me/');
}