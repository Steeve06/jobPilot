import re

import requests

from .base import JobSourceAdapter, NormalizedPosting


class GreenhouseAdapter(JobSourceAdapter):
    def fetch_postings(self, job_source):
        board_slug = job_source.config.get('board_slug')
        if not board_slug:
            raise ValueError(f'JobSource {job_source.id} has no board_slug in config')

        url = f'https://boards-api.greenhouse.io/v1/boards/{board_slug}/jobs'
        response = requests.get(url, params={'content': 'true'}, timeout=15)
        response.raise_for_status()
        jobs = response.json().get('jobs', [])

        postings = []
        for job in jobs:
            raw_html = job.get('content', '')
            postings.append(NormalizedPosting(
                external_id=str(job['id']),
                title=job.get('title', ''),
                company=job_source.company_name,
                location=job.get('location', {}).get('name', ''),
                remote=self._looks_remote(job.get('location', {}).get('name', '')),
                url=job.get('absolute_url', ''),
                description_raw=raw_html,
                description_normalized=self._strip_html(raw_html),
            ))
        return postings

    def _looks_remote(self, location_text):
        return 'remote' in (location_text or '').lower()

    def _strip_html(self, html):
        text = re.sub(r'<[^>]+>', ' ', html or '')
        return re.sub(r'\s+', ' ', text).strip()