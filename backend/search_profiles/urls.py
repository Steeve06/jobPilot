from rest_framework.routers import DefaultRouter

from .views import SearchProfileViewSet

router = DefaultRouter()
router.register('search-profiles', SearchProfileViewSet, basename='searchprofile')

urlpatterns = router.urls