import requests

from .base import JobSourceAdapter, NormalizedPosting


class LeverAdapter(JobSourceAdapter):
    def fetch_postings(self, job_source):
        company_slug = job_source.config.get('board_slug')
        if not company_slug:
            raise ValueError(f'JobSource {job_source.id} has no board_slug in config')

        url = f'https://api.lever.co/v0/postings/{company_slug}'
        response = requests.get(url, params={'mode': 'json'}, timeout=15)
        response.raise_for_status()
        jobs = response.json()

        postings = []
        for job in jobs:
            location = job.get('categories', {}).get('location', '')
            postings.append(NormalizedPosting(
                external_id=job.get('id', ''),
                title=job.get('text', ''),
                company=job_source.company_name,
                location=location,
                remote=job.get('categories', {}).get('commitment', '').lower() == 'remote'
                    or 'remote' in (location or '').lower(),
                url=job.get('hostedUrl', ''),
                description_raw=job.get('description', ''),
                description_normalized=job.get('descriptionPlain', ''),
            ))
        return postings