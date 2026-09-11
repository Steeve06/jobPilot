import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiRequest } from '../../services/apiClient';

export function usePostings(filters) {
  const params = new URLSearchParams();
  if (filters.source) params.set('source', filters.source);
  if (filters.minScore) params.set('min_score', filters.minScore);
  if (filters.status) params.set('status', filters.status);
  if (filters.ordering) params.set('ordering', filters.ordering);

  return useQuery({
    queryKey: ['postings', filters],
    queryFn: () => apiRequest(`/api/postings/?${params.toString()}`),
  });
}

export function useDecidePosting() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ postingId, decision }) =>
      apiRequest(`/api/postings/${postingId}/decide/`, {
        method: 'POST',
        body: JSON.stringify({ decision }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['postings'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] });
    },
  });
}

export function useDashboardSummary() {
  return useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: () => apiRequest('/api/dashboard/summary/'),
  });
}

export function useTailorPosting() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (postingId) =>
      apiRequest(`/api/postings/${postingId}/tailor/`, { method: 'POST' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications'] });
    },
  });
}