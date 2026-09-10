from job_sources.models import JobSource
from .greenhouse import GreenhouseAdapter
from .lever import LeverAdapter

ADAPTER_REGISTRY = {
    JobSource.SourceType.GREENHOUSE: GreenhouseAdapter,
    JobSource.SourceType.LEVER: LeverAdapter,
}


def get_adapter(source_type):
    adapter_cls = ADAPTER_REGISTRY.get(source_type)
    if adapter_cls is None:
        raise ValueError(f'No adapter registered for source type: {source_type}')
    return adapter_cls()