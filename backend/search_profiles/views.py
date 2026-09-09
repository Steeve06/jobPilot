from rest_framework import viewsets

from accounts.services import get_active_profile
from .models import SearchProfile
from .serializers import SearchProfileSerializer


class SearchProfileViewSet(viewsets.ModelViewSet):
    serializer_class = SearchProfileSerializer

    def get_queryset(self):
        active_profile = get_active_profile(self.request)
        return SearchProfile.objects.filter(profile=active_profile)

    def perform_create(self, serializer):
        active_profile = get_active_profile(self.request)
        serializer.save(profile=active_profile)