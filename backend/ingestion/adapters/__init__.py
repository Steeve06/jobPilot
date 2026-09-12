from job_sources.models import JobSource
from .ashby import AshbyAdapter
from .greenhouse import GreenhouseAdapter
from .lever import LeverAdapter
from .remoteok import RemoteOkAdapter
from .rss import RssAdapter

ADAPTER_REGISTRY = {
    JobSource.SourceType.GREENHOUSE: GreenhouseAdapter,
    JobSource.SourceType.LEVER: LeverAdapter,
    JobSource.SourceType.ASHBY: AshbyAdapter,
    JobSource.SourceType.REMOTEOK: RemoteOkAdapter,
    JobSource.SourceType.RSS: RssAdapter,
}


def get_adapter(source_type):
    adapter_cls = ADAPTER_REGISTRY.get(source_type)
    if adapter_cls is None:
        raise ValueError(f'No adapter registered for source type: {source_type}')
    return adapter_cls()