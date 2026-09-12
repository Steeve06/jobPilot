from job_sources.models import JobSource
from .greenhouse_submission import GreenhouseSubmissionAdapter
from .lever_submission import LeverSubmissionAdapter

SUBMISSION_ADAPTER_REGISTRY = {
    JobSource.SourceType.GREENHOUSE: GreenhouseSubmissionAdapter,
    JobSource.SourceType.LEVER: LeverSubmissionAdapter,
}


def get_submission_adapter(source_type):
    adapter_cls = SUBMISSION_ADAPTER_REGISTRY.get(source_type)
    if adapter_cls is None:
        return None
    return adapter_cls()