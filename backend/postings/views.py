from django.conf import settings
from datetime import timedelta

from urllib3 import request
from resumes.models import TailoringSettings
from django.db.models import Avg, Count, F, OuterRef, Subquery
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from job_sources.models import JobSource
from ingestion.service import poll_source, PollSourceError
from scoring.service import score_unscored_postings

from accounts.services import get_active_profile
from applications.models import Application, StatusEvent
from .models import JobPosting, PostingDecision
from .serializers import JobPostingSerializer
from resumes.models import Resume, TailoredResume, TailoringLog
from ai.service import AIServiceError, tailor_resume
class JobPostingViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = JobPostingSerializer

    def get_queryset(self):
        active_profile = get_active_profile(self.request)

        decision_subquery = PostingDecision.objects.filter(
            posting=OuterRef('pk'), profile=active_profile,
        ).values('decision')[:1]

        queryset = JobPosting.objects.filter(
            source__profile=active_profile,
        ).annotate(decision_value=Subquery(decision_subquery))

        source_id = self.request.query_params.get('source')
        if source_id:
            queryset = queryset.filter(source_id=source_id)

        min_score = self.request.query_params.get('min_score')
        if min_score:
            queryset = queryset.filter(fit_score__gte=min_score)

        status_param = self.request.query_params.get('status')
        if status_param == 'saved':
            queryset = queryset.filter(decision_value='saved')
        elif status_param == 'skipped':
            queryset = queryset.filter(decision_value='skipped')
        elif status_param == 'new':
            queryset = queryset.filter(decision_value__isnull=True)

        ordering = self.request.query_params.get('ordering', '-discovered_at')
        if ordering == '-fit_score':
            queryset = queryset.order_by(F('fit_score').desc(nulls_last=True))
        elif ordering == 'fit_score':
            queryset = queryset.order_by(F('fit_score').asc(nulls_last=True))
        elif ordering == '-discovered_at':
            queryset = queryset.order_by(ordering)

        return queryset
    
    @action(detail=True, methods=['post'])
    def tailor(self, request, pk=None):
        posting = self.get_object()
        active_profile = get_active_profile(request)

        try:
            resume = active_profile.resume
        except Resume.DoesNotExist:
            return Response(
                {'detail': 'Build a resume before tailoring (Resume Editor).'}, status=400,
            )

        tailoring_settings = TailoringSettings.objects.filter(profile=active_profile).first()
        try:
            result = tailor_resume(active_profile, resume, posting, tailoring_settings)
        except AIServiceError as exc:
            return Response({'detail': str(exc)}, status=502)

        tailored_resume = TailoredResume.objects.create(
            resume=resume, posting=posting, content=result['content'],
            model_version=settings.AI_MODEL,
            version_number=TailoredResume.objects.filter(posting=posting).count() + 1,
            accepted=False,
        )
        TailoringLog.objects.create(
            tailored_resume=tailored_resume,
            input_payload=result['_input_payload'], output_payload=result['_output_payload'],
            model_version=settings.AI_MODEL, latency_ms=result['_latency_ms'],
        )

        return Response({
            'tailored_resume_id': tailored_resume.id,
            'content': tailored_resume.content,
        }, status=201)
        
    @action(detail=True, methods=['post'])
    def decide(self, request, pk=None):
        posting = self.get_object()
        decision = request.data.get('decision')
        if decision not in ('saved', 'skipped'):
            return Response({'detail': 'decision must be "saved" or "skipped"'}, status=400)
        active_profile = get_active_profile(request)
        PostingDecision.objects.update_or_create(
            posting=posting, profile=active_profile,
            defaults={'decision': decision},
        )
        return Response({'detail': f'Marked as {decision}'})

class RunSyncView(APIView):
    def post(self, request):
        active_profile = get_active_profile(request)
        sources = JobSource.objects.filter(profile=active_profile, enabled=True)

        poll_results = []
        for source in sources:
            try:
                result = poll_source(source)
                poll_results.append({'source': source.company_name, **result})
            except PollSourceError as exc:
                poll_results.append({'source': source.company_name, 'error': str(exc)})

        scoring_result = None
        try:
            resume = active_profile.resume
            scoring_result = score_unscored_postings(active_profile, resume)
        except Resume.DoesNotExist:
            pass

        return Response({'polled': poll_results, 'scoring': scoring_result})
    
class DashboardSummaryView(APIView):
    def get(self, request):
        active_profile = get_active_profile(request)
        week_ago = timezone.now() - timedelta(days=7)

        postings_qs = JobPosting.objects.filter(source__profile=active_profile)
        applications_qs = Application.objects.filter(
            posting__source__profile=active_profile,
        )

        new_postings_this_week = postings_qs.filter(discovered_at__gte=week_ago).count()
        applications_sent_this_week = applications_qs.filter(
            applied_at__gte=week_ago,
        ).count()
        scored_qs = postings_qs.filter(fit_score__isnull=False)
        avg_fit_score = scored_qs.aggregate(avg=Avg('fit_score'))['avg']

        scored_total = scored_qs.count()
        fit_distribution = None
        if scored_total > 0:
            high = scored_qs.filter(fit_score__gte=80).count()
            mid = scored_qs.filter(fit_score__gte=50, fit_score__lt=80).count()
            low = scored_qs.filter(fit_score__lt=50).count()
            fit_distribution = {
                'high': round(high / scored_total * 100),
                'mid': round(mid / scored_total * 100),
                'low': round(low / scored_total * 100),
            }

        active_sources_count = job_source_active_count = None
        from job_sources.models import JobSource
        active_sources_count = JobSource.objects.filter(profile=active_profile, enabled=True).count()
        total_sources_count = JobSource.objects.filter(profile=active_profile).count()

        by_status = applications_qs.values('status').annotate(count=Count('id'))
        status_counts = {row['status']: row['count'] for row in by_status}

        tailored_count = applications_qs.filter(tailored_resume__isnull=False).count()

        return Response({
            'new_postings_this_week': new_postings_this_week,
            'applications_sent_this_week': applications_sent_this_week,
            'avg_fit_score': round(avg_fit_score, 1) if avg_fit_score is not None else None,
            'applications_by_status': status_counts,
            'fit_distribution': fit_distribution,
            'active_sources_count': active_sources_count,
            'total_sources_count': total_sources_count,
            'tailored_resumes_count': tailored_count,
        })