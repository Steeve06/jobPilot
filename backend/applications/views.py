from django.utils import timezone
from rest_framework import viewsets, status as http_status
from rest_framework.decorators import action
from rest_framework.response import Response
from ingestion.adapters.submission_registry import get_submission_adapter
from .models import SubmissionLog
from accounts.services import get_active_profile
from .models import Application, Note
from .serializers import ApplicationSerializer, NoteSerializer
from .models import Application, Note, StatusEvent

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
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        application = self.get_object()

        if not request.data.get('confirm'):
            return Response(
                {'detail': 'Submission requires explicit confirmation: {"confirm": true}'},
                status=400,
            )

        job_source = application.posting.source
        if not job_source.is_auto_submit_eligible:
            return Response(
                {'detail': 'This posting is not eligible for automated submission. Use "Open Posting" instead.'},
                status=400,
            )

        adapter = get_submission_adapter(job_source.type)
        if adapter is None:
            return Response(
                {'detail': f'No submission adapter available for source type "{job_source.type}".'},
                status=400,
            )

        answers = request.data.get('answers', {})
        if isinstance(answers, str):
            import json
            try:
                answers = json.loads(answers)
            except (json.JSONDecodeError, TypeError):
                answers = {}
        if not isinstance(answers, dict):
            answers = {}
            
        result = adapter.submit(application, answers)

        SubmissionLog.objects.create(
            application=application, success=result.success,
            request_payload={'answers': {k: v for k, v in answers.items() if k != 'resume_file_path'}},
            response_payload=result.response_payload,
            error_message=result.error_message,
        )

        if result.success:
            application.status = Application.Status.APPLIED
            application.applied_at = timezone.now()
            application.submission_method = Application.SubmissionMethod.API
            application.save(update_fields=['status', 'applied_at', 'submission_method'])
            StatusEvent.objects.create(
                application=application, status=Application.Status.APPLIED,
                source=StatusEvent.Source.MANUAL, confirmed=True,
            )
            return Response({'detail': 'Submitted successfully.'})

        return Response({'detail': result.error_message or 'Submission failed.'}, status=502)