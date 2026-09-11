from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import Profile
from job_sources.models import JobSource
from postings.models import JobPosting
from search_profiles.models import SearchProfile
from .hard_filter import apply_hard_filters


class HardFilterTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='alex', password='pw')
        self.profile = Profile.objects.create(user=user, name='Backend Track')
        source = JobSource.objects.create(
            profile=self.profile, company_name='TestCo', type=JobSource.SourceType.GREENHOUSE,
        )
        self.backend_posting = JobPosting.objects.create(
            source=source, company='TestCo', title='Backend Engineer',
            url='https://x.com/1', dedupe_hash='hf-1',
        )
        self.frontend_posting = JobPosting.objects.create(
            source=source, company='TestCo', title='Frontend Engineer',
            url='https://x.com/2', dedupe_hash='hf-2',
        )
        self.relocate_posting = JobPosting.objects.create(
            source=source, company='TestCo', title='Backend Engineer (Relocate Required)',
            url='https://x.com/3', dedupe_hash='hf-3',
        )

    def test_no_active_search_profiles_returns_everything(self):
        result = apply_hard_filters(JobPosting.objects.all(), [])
        self.assertEqual(result.count(), 3)

    def test_title_keyword_filters_correctly(self):
        sp = SearchProfile.objects.create(
            profile=self.profile, name='Backend', title_keywords=['Backend Engineer'],
        )
        result = apply_hard_filters(JobPosting.objects.all(), [sp])
        titles = set(result.values_list('title', flat=True))
        self.assertIn('Backend Engineer', titles)
        self.assertIn('Backend Engineer (Relocate Required)', titles)  # matches keyword too
        self.assertNotIn('Frontend Engineer', titles)

    def test_excluded_keyword_removes_matching_postings(self):
        sp = SearchProfile.objects.create(
            profile=self.profile, name='Backend', title_keywords=['Backend Engineer'],
            excluded_keywords=['Relocate'],
        )
        result = apply_hard_filters(JobPosting.objects.all(), [sp])
        titles = set(result.values_list('title', flat=True))
        self.assertIn('Backend Engineer', titles)