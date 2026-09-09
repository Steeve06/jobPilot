from rest_framework import viewsets

from accounts.services import get_active_profile
from .models import JobSource
from .serializers import JobSourceSerializer


class JobSourceViewSet(viewsets.ModelViewSet):
    serializer_class = JobSourceSerializer

    def get_queryset(self):
        active_profile = get_active_profile(self.request)
        return JobSource.objects.filter(profile=active_profile)

    def perform_create(self, serializer):
        active_profile = get_active_profile(self.request)
        serializer.save(profile=active_profile)