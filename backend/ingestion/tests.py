from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import Profile
from job_sources.models import JobSource
from postings.models import JobPosting
from .adapters.base import compute_dedupe_hash
from .adapters.greenhouse import GreenhouseAdapter
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


class GreenhouseAdapterTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='alex', password='pw')
        profile = Profile.objects.create(user=user, name='Backend Track')
        self.source = JobSource.objects.create(
            profile=profile, company_name='TestCo', type=JobSource.SourceType.GREENHOUSE,
            config={'board_slug': 'testco'},
        )

    @patch('ingestion.adapters.greenhouse.requests.get')
    def test_normalizes_response_correctly(self, mock_get):
        mock_get.return_value = Mock(status_code=200, json=lambda: {
            'jobs': [{
                'id': 12345,
                'title': 'Backend Engineer',
                'location': {'name': 'Remote - US'},
                'content': '<p>Great <b>job</b> description</p>',
                'absolute_url': 'https://testco.com/jobs/12345',
            }],
        })
        mock_get.return_value.raise_for_status = Mock()

        postings = GreenhouseAdapter().fetch_postings(self.source)

        self.assertEqual(len(postings), 1)
        self.assertEqual(postings[0].title, 'Backend Engineer')
        self.assertEqual(postings[0].company, 'TestCo')
        self.assertTrue(postings[0].remote)
        self.assertEqual(postings[0].description_normalized, 'Great job description')

    def test_missing_board_slug_raises_value_error(self):
        self.source.config = {}
        with self.assertRaises(ValueError):
            GreenhouseAdapter().fetch_postings(self.source)


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