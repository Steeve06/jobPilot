from unittest.mock import Mock

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APITestCase

from .models import Profile
from .services import get_active_profile


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


class SignupViewTests(APITestCase):
    def test_signup_creates_user_and_default_profile(self):
        response = self.client.post('/api/auth/signup/', {
            'username': 'newuser', 'password': 'a-genuinely-strong-pw-93!',
        }, format='json')
        self.assertEqual(response.status_code, 201)

        user = User.objects.get(username='newuser')
        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.name, 'Default')
        self.assertTrue(profile.is_default)

    def test_signup_logs_user_in_immediately(self):
        self.client.post('/api/auth/signup/', {
            'username': 'newuser2', 'password': 'a-genuinely-strong-pw-93!',
        }, format='json')
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], 'newuser2')

    def test_duplicate_username_rejected(self):
        User.objects.create_user(username='existing', password='pw12345!!')
        response = self.client.post('/api/auth/signup/', {
            'username': 'existing', 'password': 'a-genuinely-strong-pw-93!',
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_weak_password_rejected(self):
        response = self.client.post('/api/auth/signup/', {
            'username': 'newuser3', 'password': '1234',
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(username='newuser3').exists())

    def test_missing_fields_rejected(self):
        response = self.client.post('/api/auth/signup/', {'username': 'onlyusername'}, format='json')
        self.assertEqual(response.status_code, 400)


class LoginLogoutTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alexlogin', password='a-genuinely-strong-pw-93!')
        Profile.objects.create(user=self.user, name='Backend Track')

    def test_login_with_correct_credentials_succeeds(self):
        response = self.client.post('/api/auth/login/', {
            'username': 'alexlogin', 'password': 'a-genuinely-strong-pw-93!',
        }, format='json')
        self.assertEqual(response.status_code, 200)

    def test_login_with_wrong_password_fails(self):
        response = self.client.post('/api/auth/login/', {
            'username': 'alexlogin', 'password': 'wrong-password',
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_logout_clears_session(self):
        self.client.login(username='alexlogin', password='a-genuinely-strong-pw-93!')
        self.client.post('/api/auth/logout/')
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, 403)


class GetActiveProfileTests(TestCase):
    def test_auto_creates_profile_for_user_with_none(self):
        user = User.objects.create_user(username='newbie', password='pw')
        self.assertFalse(Profile.objects.filter(user=user).exists())

        request = Mock(user=user)
        profile = get_active_profile(request)

        self.assertEqual(profile.name, 'Default')
        self.assertTrue(profile.is_default)
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_returns_existing_profile_without_creating_duplicate(self):
        user = User.objects.create_user(username='existing2', password='pw')
        existing = Profile.objects.create(user=user, name='My Custom Profile')

        profile = get_active_profile(Mock(user=user))

        self.assertEqual(profile.id, existing.id)
        self.assertEqual(Profile.objects.filter(user=user).count(), 1)
        
class GetActiveProfileTests(TestCase):
    def test_auto_creates_profile_for_user_with_none(self):
        user = User.objects.create_user(username='newbie', password='pw')
        self.assertFalse(Profile.objects.filter(user=user).exists())

        request = Mock(user=user)
        request.headers = {}  # simulates a real request with no X-Active-Profile header
        profile = get_active_profile(request)

        self.assertEqual(profile.name, 'Default')
        self.assertTrue(profile.is_default)
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_returns_existing_profile_without_creating_duplicate(self):
        user = User.objects.create_user(username='existing2', password='pw')
        existing = Profile.objects.create(user=user, name='My Custom Profile')

        request = Mock(user=user)
        request.headers = {}
        profile = get_active_profile(request)

        self.assertEqual(profile.id, existing.id)
        self.assertEqual(Profile.objects.filter(user=user).count(), 1)
        
    def test_header_selects_specific_profile_when_valid(self):
        user = User.objects.create_user(username='multi', password='pw')
        profile_a = Profile.objects.create(user=user, name='Backend Track', is_default=True)
        profile_b = Profile.objects.create(user=user, name='Frontend Track')

        request = Mock(user=user)
        request.headers = {'X-Active-Profile': str(profile_b.id)}
        profile = get_active_profile(request)

        self.assertEqual(profile.id, profile_b.id)

    def test_header_naming_another_users_profile_falls_back_to_own_default(self):
        user = User.objects.create_user(username='alice', password='pw')
        Profile.objects.create(user=user, name='Alice Default', is_default=True)

        other_user = User.objects.create_user(username='bob', password='pw')
        bobs_profile = Profile.objects.create(user=other_user, name='Bobs Profile', is_default=True)

        request = Mock(user=user)
        request.headers = {'X-Active-Profile': str(bobs_profile.id)}
        profile = get_active_profile(request)

        self.assertEqual(profile.user, user)
        self.assertNotEqual(profile.id, bobs_profile.id)

    def test_invalid_header_value_falls_back_gracefully(self):
        user = User.objects.create_user(username='charlie', password='pw')
        Profile.objects.create(user=user, name='Charlie Default', is_default=True)

        request = Mock(user=user)
        request.headers = {'X-Active-Profile': 'not-a-number'}
        profile = get_active_profile(request)

        self.assertEqual(profile.name, 'Charlie Default')