import feedparser

from .base import JobSourceAdapter, NormalizedPosting


class RssAdapter(JobSourceAdapter):
    def fetch_postings(self, job_source):
        feed_url = job_source.config.get('feed_url')
        if not feed_url:
            raise ValueError(f'JobSource {job_source.id} has no feed_url in config')

        parsed = feedparser.parse(feed_url)
        if parsed.bozo and not parsed.entries:
            # bozo=True with no entries usually means the feed URL is invalid/unreachable
            raise ValueError(f'Could not parse RSS feed at {feed_url}')

        postings = []
        for entry in parsed.entries:
            postings.append(NormalizedPosting(
                external_id=entry.get('id', entry.get('link', '')),
                title=entry.get('title', ''),
                company=job_source.company_name,
                location='',  # RSS feeds (e.g. LinkedIn public search) rarely expose structured location
                remote=False,
                url=entry.get('link', ''),
                description_raw=entry.get('summary', ''),
                description_normalized=entry.get('summary', ''),
            ))
        return postings