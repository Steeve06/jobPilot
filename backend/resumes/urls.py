from django.urls import path

from .views import ResumeDetailView, ResumeImportView, ResumeExportView, TailoredResumeDownloadView

urlpatterns = [
    path('resume/', ResumeDetailView.as_view(), name='resume-detail'),
    path('resume/import/', ResumeImportView.as_view(), name='resume-import'),
    path('resume/export/', ResumeExportView.as_view(), name='resume-export'),
    path('tailored-resumes/<int:pk>/download/', TailoredResumeDownloadView.as_view(), name='tailored-resume-download'),
    
]