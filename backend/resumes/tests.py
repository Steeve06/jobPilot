from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.test import APITestCase

from accounts.models import Profile
from .models import Bullet, Experience, Resume


class BulletConstraintTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='alex', password='pw')
        profile = Profile.objects.create(user=user, name='Backend Track')
        self.resume = Resume.objects.create(profile=profile, full_name='Alex Johnson', email='a@x.com')
        self.experience = Experience.objects.create(
            resume=self.resume, company='Acme', title='SWE',
            start_date='2021-01-01',
        )

    def test_bullet_with_only_experience_is_valid(self):
        bullet = Bullet(experience=self.experience, text='Did a thing', skill_tags=['Go'])
        bullet.full_clean()  # should not raise
        bullet.save()
        self.assertEqual(Bullet.objects.count(), 1)

    def test_bullet_with_no_parent_fails_validation(self):
        bullet = Bullet(text='Orphan bullet')
        with self.assertRaises(ValidationError):
            bullet.full_clean()

    def test_bullet_with_both_parents_violates_db_constraint(self):
        from .models import Project
        project = Project.objects.create(resume=self.resume, name='Side Project')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Bullet.objects.create(
                    experience=self.experience, project=project, text='Bad bullet',
                )


class ResumeProfileRelationTests(TestCase):
    def test_resume_is_one_per_profile(self):
        user = User.objects.create_user(username='sam', password='pw')
        profile = Profile.objects.create(user=user, name='Data Track')
        Resume.objects.create(profile=profile, full_name='Sam', email='s@x.com')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Resume.objects.create(profile=profile, full_name='Sam Again', email='s2@x.com')
                
class ResumeNestedUpdateAPITests(APITestCase):
    def setUp(self):
        user = User.objects.create_user(username='alex', password='pw')
        Profile.objects.create(user=user, name='Backend Track')
        self.client.login(username='alex', password='pw')

    def test_patch_creates_nested_experience_and_bullet(self):
        response = self.client.patch('/api/resume/', {
            'full_name': 'Alex Johnson',
            'email': 'alex@gmail.com',
            'experiences': [{
                'company': 'Acme', 'title': 'SWE', 'start_date': '2021-01-01',
                'bullets': [{'text': 'Did a thing', 'skill_tags': ['Go']}],
            }],
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Experience.objects.count(), 1)
        self.assertEqual(Bullet.objects.count(), 1)

    def test_second_patch_without_bullet_deletes_it(self):
        first = self.client.patch('/api/resume/', {
            'experiences': [{
                'company': 'Acme', 'title': 'SWE', 'start_date': '2021-01-01',
                'bullets': [{'text': 'Did a thing', 'skill_tags': ['Go']}],
            }],
        }, format='json')
        experience_id = first.data['experiences'][0]['id']

        self.client.patch('/api/resume/', {
            'experiences': [{
                'id': experience_id, 'company': 'Acme', 'title': 'Staff SWE',
                'start_date': '2021-01-01', 'bullets': [],
            }],
        }, format='json')

        self.assertEqual(Experience.objects.count(), 1)
        self.assertEqual(Experience.objects.first().title, 'Staff SWE')
        self.assertEqual(Bullet.objects.count(), 0)
        
class ResumeUrlNormalizationAPITests(APITestCase):
    def setUp(self):
        user = User.objects.create_user(username='alex', password='pw')
        Profile.objects.create(user=user, name='Backend Track')
        self.client.login(username='alex', password='pw')

    def test_bare_domain_gets_https_prefix(self):
        response = self.client.patch('/api/resume/', {
            'linkedin_url': 'linkedin.com/in/alexj',
            'github_url': 'github.com/alexj',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['linkedin_url'], 'https://linkedin.com/in/alexj')
        self.assertEqual(response.data['github_url'], 'https://github.com/alexj')

    def test_url_with_scheme_already_present_is_unchanged(self):
        response = self.client.patch('/api/resume/', {
            'linkedin_url': 'https://linkedin.com/in/alexj',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['linkedin_url'], 'https://linkedin.com/in/alexj')

    def test_empty_url_stays_empty(self):
        response = self.client.patch('/api/resume/', {'linkedin_url': ''}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['linkedin_url'], '')