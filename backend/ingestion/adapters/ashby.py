import re

import requests

from .base import JobSourceAdapter, NormalizedPosting


class AshbyAdapter(JobSourceAdapter):
    def fetch_postings(self, job_source):
        board_name = job_source.config.get('board_slug')
        if not board_name:
            raise ValueError(f'JobSource {job_source.id} has no board_slug in config')

        url = f'https://api.ashbyhq.com/posting-api/job-board/{board_name}'
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        jobs = response.json().get('jobPostings', [])

        postings = []
        for job in jobs:
            description = job.get('descriptionHtml') or job.get('descriptionPlain', '')
            postings.append(NormalizedPosting(
                external_id=str(job.get('id', '')),
                title=job.get('title', ''),
                company=job_source.company_name,
                location=job.get('locationName', ''),
                remote=job.get('isRemote', False) or 'remote' in (job.get('locationName') or '').lower(),
                url=job.get('jobUrl', ''),
                description_raw=description,
                description_normalized=self._strip_html(description),
            ))
        return postings

    def _strip_html(self, html):
        text = re.sub(r'<[^>]+>', ' ', html or '')
        return re.sub(r'\s+', ' ', text).strip()