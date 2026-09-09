from .models import Profile


def get_active_profile(request):
    """
    Resolve the active Profile for the current request.

    Today: returns the requesting user's first Profile (single-profile
    dev workflow). Sprint 16 will change this to read an explicit
    'active profile' selection (e.g. from session or a header) once
    the frontend profile switcher exists — nothing that calls this
    function needs to change when that happens.
    """
    profile = Profile.objects.filter(user=request.user).first()
    if profile is None:
        raise Profile.DoesNotExist(
            f'User {request.user} has no Profile. Create one via /admin/.'
        )
    return profile