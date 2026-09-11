import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiRequest } from '../../services/apiClient';

export function useTailoringSettings() {
  return useQuery({ queryKey: ['tailoring-settings'], queryFn: () => apiRequest('/api/tailoring-settings/') });
}

export function useUpdateTailoringSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data) => apiRequest('/api/tailoring-settings/', { method: 'PATCH', body: JSON.stringify(data) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tailoring-settings'] }),
  });
}