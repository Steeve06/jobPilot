from django.contrib.auth.models import User
from django.test import TestCase

from .models import Profile


class ProfileModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alex', password='pw')

    def test_profile_created_and_linked_to_user(self):
        profile = Profile.objects.create(user=self.user, name='Backend Track')
        self.assertEqual(profile.user, self.user)
        self.assertIn(profile, self.user.profiles.all())

    def test_multiple_profiles_per_user_allowed(self):
        Profile.objects.create(user=self.user, name='Backend Track')
        Profile.objects.create(user=self.user, name='Frontend Track')
        self.assertEqual(self.user.profiles.count(), 2)