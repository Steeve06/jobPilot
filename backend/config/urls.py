from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('accounts.urls')),
    path('api/', include('search_profiles.urls')),
    path('api/', include('job_sources.urls')),
    path('api/', include('resumes.urls')),
    path('api/', include('postings.urls')),
    path('api/', include('applications.urls')),
    path('api/', include('notifications.urls')),
    
]