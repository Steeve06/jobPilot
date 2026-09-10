import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiRequest } from '../../services/apiClient';

export function useApplications() {
  return useQuery({
    queryKey: ['applications'],
    queryFn: () => apiRequest('/api/applications/'),
  });
}

export function useUpdateApplication() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }) =>
      apiRequest(`/api/applications/${id}/`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['applications'] }),
  });
}

export function useAddNote() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ applicationId, text }) =>
      apiRequest(`/api/applications/${applicationId}/notes/`, {
        method: 'POST',
        body: JSON.stringify({ text }),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['applications'] }),
  });
}