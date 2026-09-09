from rest_framework import viewsets

from accounts.services import get_active_profile
from .models import Application
from .serializers import ApplicationSerializer


class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer

    def get_queryset(self):
        active_profile = get_active_profile(self.request)
        queryset = Application.objects.filter(posting__source__profile=active_profile)

        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        return queryset