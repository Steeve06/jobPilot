from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import DashboardSummaryView, JobPostingViewSet, RunSyncView

router = DefaultRouter()
router.register('postings', JobPostingViewSet, basename='jobposting')

urlpatterns = router.urls + [
    path('dashboard/summary/', DashboardSummaryView.as_view(), name='dashboard-summary'),
    path('sync/', RunSyncView.as_view(), name='run-sync'),
]