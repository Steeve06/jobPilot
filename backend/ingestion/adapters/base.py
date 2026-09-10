import hashlib
from dataclasses import dataclass, field


@dataclass
class NormalizedPosting:
    external_id: str
    title: str
    company: str
    location: str
    remote: bool
    url: str
    description_raw: str
    description_normalized: str
    posted_at: object = None  # datetime or None; adapters parse their own date formats


class JobSourceAdapter:
    """
    Base interface every ingestion adapter implements. Subclasses only
    need to override fetch_postings() — everything about deciding what's
    a duplicate or writing to the database happens in the ingestion
    service, not here.
    """

    def fetch_postings(self, job_source):
        raise NotImplementedError


def compute_dedupe_hash(company, title, location):
    """
    Per FR4: normalize (company, title, location) and hash. Shared here
    so every adapter and the ingestion service agree on the exact same
    normalization, rather than each reimplementing it slightly differently.
    """
    normalized = '|'.join([
        (company or '').strip().lower(),
        (title or '').strip().lower(),
        (location or '').strip().lower(),
    ])
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:64]