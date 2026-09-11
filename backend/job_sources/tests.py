from unittest.mock import patch

from config.test_utils import TwoProfileTestCase
from ingestion.service import PollSourceError
from .models import JobSource


class PollNowActionTests(TwoProfileTestCase):
    def setUp(self):
        super().setUp()
        self.source = JobSource.objects.create(
            profile=self.profile_a, company_name='TestCo', type=JobSource.SourceType.GREENHOUSE,
            config={'board_slug': 'testco'},
        )
        self.other_source = JobSource.objects.create(
            profile=self.profile_b, company_name='OtherCo', type=JobSource.SourceType.LEVER,
            config={'board_slug': 'otherco'},
        )

    @patch('job_sources.views.poll_source')
    def test_poll_now_returns_summary_on_success(self, mock_poll):
        mock_poll.return_value = {'created': 5, 'skipped_duplicates': 2}
        response = self.client.post(f'/api/job-sources/{self.source.id}/poll_now/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'created': 5, 'skipped_duplicates': 2})

    @patch('job_sources.views.poll_source')
    def test_poll_now_returns_502_on_poll_error(self, mock_poll):
        mock_poll.side_effect = PollSourceError('Bad board slug')
        response = self.client.post(f'/api/job-sources/{self.source.id}/poll_now/')
        self.assertEqual(response.status_code, 502)
        self.assertIn('Bad board slug', response.data['detail'])

    def test_cannot_poll_another_profiles_source(self):
        response = self.client.post(f'/api/job-sources/{self.other_source.id}/poll_now/')
        self.assertEqual(response.status_code, 404)