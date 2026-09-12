from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APITestCase
from .models import Profile

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
        self.user = User.objects.create_user(username='alex', password='a-genuinely-strong-pw-93!')
        Profile.objects.create(user=self.user, name='Backend Track')

    def test_login_with_correct_credentials_succeeds(self):
        response = self.client.post('/api/auth/login/', {
            'username': 'alex', 'password': 'a-genuinely-strong-pw-93!',
        }, format='json')
        self.assertEqual(response.status_code, 200)

    def test_login_with_wrong_password_fails(self):
        response = self.client.post('/api/auth/login/', {
            'username': 'alex', 'password': 'wrong-password',
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_logout_clears_session(self):
        self.client.login(username='alex', password='a-genuinely-strong-pw-93!')
        self.client.post('/api/auth/logout/')
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, 403)
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