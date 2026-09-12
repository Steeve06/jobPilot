import re

import requests

from .base import JobSourceAdapter, NormalizedPosting


class RemoteOkAdapter(JobSourceAdapter):
    def fetch_postings(self, job_source):
        keyword = job_source.config.get('keyword', '').lower()

        response = requests.get(
            'https://remoteok.com/api', timeout=15,
            headers={'User-Agent': 'JobPilot/1.0 (personal job search tool)'},
        )
        response.raise_for_status()
        jobs = response.json()

        # RemoteOK's first array element is metadata (legal notice), not a job
        jobs = [j for j in jobs if isinstance(j, dict) and j.get('id')]

        postings = []
        for job in jobs:
            title = job.get('position', '')
            if keyword and keyword not in title.lower():
                continue

            description = job.get('description', '')
            postings.append(NormalizedPosting(
                external_id=str(job.get('id', '')),
                title=title,
                company=job.get('company', job_source.company_name),
                location=job.get('location', ''),
                remote=True,  # RemoteOK is remote-only by definition
                url=job.get('url', ''),
                description_raw=description,
                description_normalized=self._strip_html(description),
            ))
        return postings

    def _strip_html(self, html):
        text = re.sub(r'<[^>]+>', ' ', html or '')
        return re.sub(r'\s+', ' ', text).strip()