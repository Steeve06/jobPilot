from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import Profile
from job_sources.models import JobSource
from postings.models import JobPosting
from .adapters.base import compute_dedupe_hash
from .adapters.greenhouse import GreenhouseAdapter
from .adapters.greenhouse_submission import GreenhouseSubmissionAdapter
from .adapters.lever import LeverAdapter
from .service import poll_source, PollSourceError


class DedupeHashTests(TestCase):
    def test_same_inputs_produce_same_hash(self):
        h1 = compute_dedupe_hash('Stripe', 'Backend Engineer', 'San Francisco')
        h2 = compute_dedupe_hash('Stripe', 'Backend Engineer', 'San Francisco')
        self.assertEqual(h1, h2)

    def test_case_and_whitespace_insensitive(self):
        h1 = compute_dedupe_hash('Stripe', 'Backend Engineer', 'San Francisco')
        h2 = compute_dedupe_hash('  stripe  ', 'BACKEND ENGINEER', 'san francisco')
        self.assertEqual(h1, h2)

    def test_different_inputs_produce_different_hash(self):
        h1 = compute_dedupe_hash('Stripe', 'Backend Engineer', 'San Francisco')
        h2 = compute_dedupe_hash('Stripe', 'Frontend Engineer', 'San Francisco')
        self.assertNotEqual(h1, h2)


class GreenhouseSubmissionAdapterTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='sam', password='pw')
        profile = Profile.objects.create(user=user, name='Backend Track')
        self.source = JobSource.objects.create(
            profile=profile, company_name='TestCo', type=JobSource.SourceType.GREENHOUSE,
            config={'board_slug': 'testco'},
        )
        posting = JobPosting.objects.create(
            source=self.source, company='TestCo', title='Engineer',
            url='https://x.com/1', dedupe_hash='gsa-1', external_id='999',
        )
        from applications.models import Application
        self.application = Application.objects.create(posting=posting)

    @patch('ingestion.adapters.greenhouse_submission.requests.post')
    def test_successful_submission(self, mock_post):
        mock_post.return_value = Mock(status_code=200, text='OK')
        result = GreenhouseSubmissionAdapter().submit(
            self.application, {'first_name': 'A', 'last_name': 'B', 'email': 'a@x.com'},
        )
        self.assertTrue(result.success)

    @patch('ingestion.adapters.greenhouse_submission.requests.post')
    def test_failed_submission_returns_clear_error(self, mock_post):
        mock_post.return_value = Mock(status_code=404, text='Not found')
        result = GreenhouseSubmissionAdapter().submit(self.application, {})
        self.assertFalse(result.success)
        self.assertIn('404', result.error_message)

    def test_missing_board_slug_returns_error_without_http_call(self):
        self.source.config = {}
        self.source.save()
        result = GreenhouseSubmissionAdapter().submit(self.application, {})
        self.assertFalse(result.success)
        self.assertIn('board slug', result.error_message.lower())


class LeverAdapterTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='sam', password='pw')
        profile = Profile.objects.create(user=user, name='Frontend Track')
        self.source = JobSource.objects.create(
            profile=profile, company_name='TestCo', type=JobSource.SourceType.LEVER,
            config={'board_slug': 'testco'},
        )

    @patch('ingestion.adapters.lever.requests.get')
    def test_normalizes_response_correctly(self, mock_get):
        mock_get.return_value = Mock(status_code=200, json=lambda: [{
            'id': 'abc-123',
            'text': 'Platform Engineer',
            'categories': {'location': 'New York, NY', 'commitment': 'Full-time'},
            'description': '<p>desc</p>',
            'descriptionPlain': 'desc',
            'hostedUrl': 'https://jobs.lever.co/testco/abc-123',
        }])
        mock_get.return_value.raise_for_status = Mock()

        postings = LeverAdapter().fetch_postings(self.source)

        self.assertEqual(len(postings), 1)
        self.assertEqual(postings[0].title, 'Platform Engineer')
        self.assertFalse(postings[0].remote)


class PollSourceServiceTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='alex', password='pw')
        profile = Profile.objects.create(user=user, name='Backend Track')
        self.source = JobSource.objects.create(
            profile=profile, company_name='TestCo', type=JobSource.SourceType.GREENHOUSE,
            config={'board_slug': 'testco'},
        )

    @patch('ingestion.adapters.greenhouse.requests.get')
    def test_creates_new_postings(self, mock_get):
        mock_get.return_value = Mock(status_code=200, json=lambda: {
            'jobs': [{
                'id': 1, 'title': 'Engineer', 'location': {'name': 'SF'},
                'content': 'desc', 'absolute_url': 'https://x.com/1',
            }],
        })
        mock_get.return_value.raise_for_status = Mock()

        result = poll_source(self.source)

        self.assertEqual(result['created'], 1)
        self.assertEqual(JobPosting.objects.count(), 1)
        self.source.refresh_from_db()
        self.assertIsNotNone(self.source.last_polled_at)

    @patch('ingestion.adapters.greenhouse.requests.get')
    def test_second_poll_skips_duplicates(self, mock_get):
        mock_get.return_value = Mock(status_code=200, json=lambda: {
            'jobs': [{
                'id': 1, 'title': 'Engineer', 'location': {'name': 'SF'},
                'content': 'desc', 'absolute_url': 'https://x.com/1',
            }],
        })
        mock_get.return_value.raise_for_status = Mock()

        poll_source(self.source)
        result = poll_source(self.source)

        self.assertEqual(result['created'], 0)
        self.assertEqual(result['skipped_duplicates'], 1)
        self.assertEqual(JobPosting.objects.count(), 1)

    @patch('ingestion.adapters.greenhouse.requests.get')
    def test_http_error_raises_poll_source_error_not_raw_exception(self, mock_get):
        import requests
        mock_response = Mock(status_code=404)
        mock_get.return_value = mock_response
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)

        with self.assertRaises(PollSourceError):
            poll_source(self.source)

        # Confirm no partial/broken state was left behind
        self.assertEqual(JobPosting.objects.count(), 0)