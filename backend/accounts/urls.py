from django.urls import path

from .views import CompleteOnboardingView, CreateProfileView, CsrfCookieView, CurrentUserView, LoginView, LogoutView, SignupView, UpdateProfileView

urlpatterns = [
    path('auth/csrf/', CsrfCookieView.as_view(), name='auth-csrf'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/signup/', SignupView.as_view(), name='auth-signup'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('profile/complete-onboarding/', CompleteOnboardingView.as_view(), name='complete-onboarding'),
    path('profile/', UpdateProfileView.as_view(), name='update-profile'),
    path('profiles/', CreateProfileView.as_view(), name='create-profile'),
    path('auth/me/', CurrentUserView.as_view(), name='auth-me'),
]