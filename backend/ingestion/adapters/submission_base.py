from dataclasses import dataclass


@dataclass
class SubmissionResult:
    success: bool
    response_payload: dict
    error_message: str = ''


class SubmissionAdapter:
    """
    Base interface for submitting an application to an ATS. Per ADR-002,
    only sources whose type has a registered SubmissionAdapter AND whose
    JobSource.is_auto_submit_eligible is True are ever offered this path
    (see applications/views.py's submit action) — everything else stays
    on the manual "Open Posting" flow (FR22).
    """

    def submit(self, application, answers):
        raise NotImplementedError