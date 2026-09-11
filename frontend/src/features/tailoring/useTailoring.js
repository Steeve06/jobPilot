import { useMutation } from '@tanstack/react-query';
import { apiRequest } from '../../services/apiClient';

export function useGenerateTailoredResume() {
  return useMutation({
    mutationFn: (postingId) =>
      apiRequest(`/api/postings/${postingId}/tailor/`, { method: 'POST' }),
  });
}

export function useAcceptTailoredResume() {
  return useMutation({
    mutationFn: (tailoredResumeId) =>
      apiRequest(`/api/tailored-resumes/${tailoredResumeId}/accept/`, { method: 'POST' }),
  });
}