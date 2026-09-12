from django.urls import path

from .views import CsrfCookieView, CurrentUserView, LoginView, LogoutView, SignupView

urlpatterns = [
    path('auth/csrf/', CsrfCookieView.as_view(), name='auth-csrf'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/signup/', SignupView.as_view(), name='auth-signup'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('auth/me/', CurrentUserView.as_view(), name='auth-me'),
]