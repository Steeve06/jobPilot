import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiRequest } from '../../services/apiClient';

export function useResume() {
  return useQuery({
    queryKey: ['resume'],
    queryFn: () => apiRequest('/api/resume/'),
  });
}

export function useSaveResume() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data) =>
      apiRequest('/api/resume/', { method: 'PATCH', body: JSON.stringify(data) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['resume'] }),
  });
}

export async function importResume(file) {
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
  const csrfToken = document.cookie.match(/csrftoken=([^;]+)/)?.[1];
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/resume/import/`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'X-CSRFToken': csrfToken },
    body: formData,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || 'Import failed');
  }
  return response.json();
}