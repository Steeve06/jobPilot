from rest_framework import viewsets
from accounts.services import get_active_profile
from .models import JobPosting
from .serializers import JobPostingSerializer
from datetime import timedelta

from django.db.models import Avg, Count
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from applications.models import Application


class JobPostingViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = JobPostingSerializer

    def get_queryset(self):
        active_profile = get_active_profile(self.request)
        queryset = JobPosting.objects.filter(source__profile=active_profile)

        source_id = self.request.query_params.get('source')
        if source_id:
            queryset = queryset.filter(source_id=source_id)

        min_score = self.request.query_params.get('min_score')
        if min_score:
            queryset = queryset.filter(fit_score__gte=min_score)

        return queryset
    
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
        avg_fit_score = postings_qs.filter(
            fit_score__isnull=False,
        ).aggregate(avg=Avg('fit_score'))['avg']

        by_status = applications_qs.values('status').annotate(count=Count('id'))
        status_counts = {row['status']: row['count'] for row in by_status}

        return Response({
            'new_postings_this_week': new_postings_this_week,
            'applications_sent_this_week': applications_sent_this_week,
            'avg_fit_score': round(avg_fit_score, 1) if avg_fit_score is not None else None,
            'applications_by_status': status_counts,
        })