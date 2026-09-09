from django.urls import path

from .views import ResumeDetailView

urlpatterns = [
    path('resume/', ResumeDetailView.as_view(), name='resume-detail'),
]