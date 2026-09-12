import requests

from .submission_base import SubmissionAdapter, SubmissionResult


class LeverSubmissionAdapter(SubmissionAdapter):
    def submit(self, application, answers):
        posting = application.posting
        board_slug = posting.source.config.get('board_slug')
        job_external_id = posting.external_id

        if not board_slug or not job_external_id:
            return SubmissionResult(
                success=False, response_payload={},
                error_message='Missing board slug or job id for this posting.',
            )

        url = f'https://api.lever.co/v0/postings/{board_slug}/{job_external_id}'

        payload = {
            'name': f"{answers.get('first_name', '')} {answers.get('last_name', '')}".strip(),
            'email': answers.get('email', ''),
            'phone': answers.get('phone', ''),
        }

        try:
            response = requests.post(url, data=payload, timeout=20)
        except requests.exceptions.RequestException as exc:
            return SubmissionResult(success=False, response_payload={}, error_message=str(exc))

        if response.status_code in (200, 201):
            return SubmissionResult(success=True, response_payload={'status_code': response.status_code})

        return SubmissionResult(
            success=False,
            response_payload={'status_code': response.status_code, 'body': response.text[:500]},
            error_message=(
                f'Lever returned {response.status_code}. This job may not support '
                f'API-based submission — check if it requires applying through their hosted form instead.'
            ),
        )