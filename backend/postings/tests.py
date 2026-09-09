from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import Profile
from job_sources.models import JobSource
from .models import JobPosting


class JobPostingDedupeTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='alex', password='pw')
        profile = Profile.objects.create(user=user, name='Backend Track')
        self.source = JobSource.objects.create(
            profile=profile, company_name='Stripe', type=JobSource.SourceType.GREENHOUSE,
        )

    def test_duplicate_dedupe_hash_rejected(self):
        JobPosting.objects.create(
            source=self.source, company='Stripe', title='Backend Engineer',
            url='https://stripe.com/jobs/1', dedupe_hash='abc123',
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                JobPosting.objects.create(
                    source=self.source, company='Stripe', title='Backend Engineer (dup)',
                    url='https://stripe.com/jobs/1-dup', dedupe_hash='abc123',
                )

    def test_fit_score_defaults_to_null_until_scored(self):
        posting = JobPosting.objects.create(
            source=self.source, company='Stripe', title='Backend Engineer',
            url='https://stripe.com/jobs/2', dedupe_hash='xyz789',
        )
        self.assertIsNone(posting.fit_score)