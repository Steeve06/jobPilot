from datetime import timedelta

from django.db.models import Avg, Count, F, OuterRef, Subquery
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.services import get_active_profile
from applications.models import Application
from .models import JobPosting, PostingDecision
from .serializers import JobPostingSerializer


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