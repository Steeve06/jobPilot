import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiRequest } from '../../services/apiClient';

export function useJobSources() {
  return useQuery({ queryKey: ['job-sources'], queryFn: () => apiRequest('/api/job-sources/') });
}

export function useCreateJobSource() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data) => apiRequest('/api/job-sources/', { method: 'POST', body: JSON.stringify(data) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['job-sources'] }),
  });
}

export function useUpdateJobSource() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }) => apiRequest(`/api/job-sources/${id}/`, { method: 'PATCH', body: JSON.stringify(data) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['job-sources'] }),
  });
}

export function useDeleteJobSource() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id) => apiRequest(`/api/job-sources/${id}/`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['job-sources'] }),
  });
}

export function usePollJobSourceNow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id) => apiRequest(`/api/job-sources/${id}/poll_now/`, { method: 'POST' }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['job-sources'] });
      qc.invalidateQueries({ queryKey: ['postings'] });
    },
  });
}