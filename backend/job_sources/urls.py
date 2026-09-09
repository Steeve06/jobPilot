from rest_framework.routers import DefaultRouter

from .views import JobSourceViewSet

router = DefaultRouter()
router.register('job-sources', JobSourceViewSet, basename='jobsource')

urlpatterns = router.urls