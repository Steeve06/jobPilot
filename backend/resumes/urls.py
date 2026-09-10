from django.urls import path

from .views import ResumeDetailView, ResumeImportView

urlpatterns = [
    path('resume/', ResumeDetailView.as_view(), name='resume-detail'),
    path('resume/import/', ResumeImportView.as_view(), name='resume-import'),
]