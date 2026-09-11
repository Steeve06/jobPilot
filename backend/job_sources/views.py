from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ingestion.service import poll_source, PollSourceError
from accounts.services import get_active_profile
from .models import JobSource
from .serializers import JobSourceSerializer


class JobSourceViewSet(viewsets.ModelViewSet):
    serializer_class = JobSourceSerializer
    
    @action(detail=True, methods=['post'])
    def poll_now(self, request, pk=None):
        job_source = self.get_object()
        try:
            result = poll_source(job_source)
        except PollSourceError as exc:
            return Response({'detail': str(exc)}, status=502)
        return Response(result)

    def get_queryset(self):
        active_profile = get_active_profile(self.request)
        return JobSource.objects.filter(profile=active_profile)

    def perform_create(self, serializer):
        active_profile = get_active_profile(self.request)
        serializer.save(profile=active_profile)