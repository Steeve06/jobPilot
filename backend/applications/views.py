from rest_framework import viewsets, status as http_status
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.services import get_active_profile
from .models import Application, Note
from .serializers import ApplicationSerializer, NoteSerializer


class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer

    def get_queryset(self):
        active_profile = get_active_profile(self.request)
        queryset = Application.objects.filter(posting__source__profile=active_profile)
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset

    @action(detail=True, methods=['post'])
    def notes(self, request, pk=None):
        application = self.get_object()
        text = request.data.get('text', '').strip()
        if not text:
            return Response({'detail': 'text is required'}, status=http_status.HTTP_400_BAD_REQUEST)
        note = Note.objects.create(application=application, text=text)
        return Response(NoteSerializer(note).data, status=http_status.HTTP_201_CREATED)