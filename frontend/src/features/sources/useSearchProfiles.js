import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiRequest } from '../../services/apiClient';

export function useSearchProfiles() {
  return useQuery({ queryKey: ['search-profiles'], queryFn: () => apiRequest('/api/search-profiles/') });
}

export function useCreateSearchProfile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data) => apiRequest('/api/search-profiles/', { method: 'POST', body: JSON.stringify(data) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['search-profiles'] }),
  });
}

export function useUpdateSearchProfile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }) => apiRequest(`/api/search-profiles/${id}/`, { method: 'PATCH', body: JSON.stringify(data) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['search-profiles'] }),
  });
}

export function useDeleteSearchProfile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id) => apiRequest(`/api/search-profiles/${id}/`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['search-profiles'] }),
  });
}