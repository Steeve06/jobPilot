from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from accounts.models import Profile


class TwoProfileTestCase(APITestCase):
    """
    Base for tests that need to verify cross-profile isolation.
    Creates two separate users, each with their own Profile, and
    logs in as `self.user_a` by default via `self.client`.
    """

    def setUp(self):
        self.user_a = User.objects.create_user(username='alex', password='pw')
        self.profile_a = Profile.objects.create(user=self.user_a, name='Backend Track')

        self.user_b = User.objects.create_user(username='sam', password='pw')
        self.profile_b = Profile.objects.create(user=self.user_b, name='Frontend Track')

        self.client.login(username='alex', password='pw')