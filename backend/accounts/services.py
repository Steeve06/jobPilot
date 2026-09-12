from .models import Profile


def get_active_profile(request):
    """
    Resolve the active Profile for the current request.

    Auto-creates a default Profile on first access if none exists yet —
    this makes profile creation resilient to any auth path (signup,
    Google OAuth, or an account created directly via /admin/) rather
    than depending on every single one remembering to create it.
    """
    profile, _ = Profile.objects.get_or_create(
        user=request.user,
        defaults={'name': 'Default', 'is_default': True},
    )
    return profile