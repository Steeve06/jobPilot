from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import DashboardSummaryView, JobPostingViewSet

router = DefaultRouter()
router.register('postings', JobPostingViewSet, basename='jobposting')

urlpatterns = router.urls + [
    path('dashboard/summary/', DashboardSummaryView.as_view(), name='dashboard-summary'),
]