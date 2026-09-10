from config.test_utils import TwoProfileTestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.test import APITestCase
from postings.models import JobPosting
from job_sources.models import JobSource
from accounts.models import Profile
from .models import Bullet, Experience, Resume, TailoredResume
from .docx_renderer import render_resume_to_docx

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
        
class DocxRendererTests(TestCase):
    def test_renders_minimal_data_without_error(self):
        buffer = render_resume_to_docx({'full_name': 'Alex Johnson', 'email': 'alex@x.com'})
        self.assertGreater(len(buffer.getvalue()), 0)

    def test_renders_full_data_without_error(self):
        data = {
            'full_name': 'Alex Johnson', 'email': 'alex@x.com', 'phone': '555-1234',
            'location': 'SF, CA', 'linkedin_url': 'https://linkedin.com/in/alexj',
            'summary': 'Experienced engineer.',
            'skills': ['Go', 'PostgreSQL'],
            'experiences': [{
                'company': 'Acme', 'title': 'SWE', 'start_date': '2021-01-01', 'end_date': None,
                'bullets': [{'text': 'Did a thing'}],
            }],
            'projects': [{'name': 'Side Project', 'bullets': [{'text': 'Built a thing'}]}],
            'education': [{'degree': 'B.S. CS', 'school': 'State University'}],
        }
        buffer = render_resume_to_docx(data)
        self.assertGreater(len(buffer.getvalue()), 0)

    def test_renders_empty_data_without_error(self):
        # An empty/near-empty resume (e.g. brand new profile) shouldn't crash the renderer
        buffer = render_resume_to_docx({})
        self.assertGreater(len(buffer.getvalue()), 0)


class ResumeExportAPITests(APITestCase):
    def setUp(self):
        user = User.objects.create_user(username='alex', password='pw')
        Profile.objects.create(user=user, name='Backend Track')
        self.client.login(username='alex', password='pw')

    def test_export_returns_docx_file(self):
        response = self.client.get('/api/resume/export/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        )
        self.assertIn('attachment', response['Content-Disposition'])

    def test_export_requires_authentication(self):
        self.client.logout()
        response = self.client.get('/api/resume/export/')
        self.assertEqual(response.status_code, 403)  # IsAuthenticated default


class TailoredResumeDownloadScopingTests(TwoProfileTestCase):
    def setUp(self):
        super().setUp()
        source = JobSource.objects.create(
            profile=self.profile_a, company_name='Stripe', type=JobSource.SourceType.GREENHOUSE,
        )
        posting = JobPosting.objects.create(
            source=source, company='Stripe', title='Backend Engineer',
            url='https://stripe.com/1', dedupe_hash='dl-1',
        )
        resume = Resume.objects.create(profile=self.profile_a, full_name='Alex', email='a@x.com')
        self.tailored = TailoredResume.objects.create(
            resume=resume, posting=posting, content={'full_name': 'Alex Johnson'},
        )

    def test_owner_can_download(self):
        response = self.client.get(f'/api/tailored-resumes/{self.tailored.id}/download/')
        self.assertEqual(response.status_code, 200)

    def test_other_profile_gets_404(self):
        self.client.logout()
        self.client.login(username='sam', password='pw')
        response = self.client.get(f'/api/tailored-resumes/{self.tailored.id}/download/')
        self.assertEqual(response.status_code, 404)

    def test_nonexistent_id_returns_404_not_500(self):
        response = self.client.get('/api/tailored-resumes/99999/download/')
        self.assertEqual(response.status_code, 404)