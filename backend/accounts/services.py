from .models import Profile


def get_active_profile(request):
    """
    Resolve the active Profile for the current request.

    Reads the X-Active-Profile header (a Profile id) if present and
    validates it belongs to the authenticated user — this is what lets
    the frontend's profile switcher actually scope every API call to
    whichever profile is currently selected, not just the first one.

    Falls back to the user's default profile (is_default=True, else
    the first one) if the header is absent, invalid, or names a
    profile belonging to someone else. Auto-creates a default Profile
    on first-ever access for a user with none.
    """
    header_profile_id = request.headers.get('X-Active-Profile')
    if header_profile_id:
        try:
            return Profile.objects.get(id=header_profile_id, user=request.user)
        except (Profile.DoesNotExist, ValueError):
            pass  # invalid or not-yours — fall through to default resolution

    profile = Profile.objects.filter(user=request.user).order_by('-is_default', 'id').first()
    if profile is None:
        profile = Profile.objects.create(user=request.user, name='Default', is_default=True)
    return profile