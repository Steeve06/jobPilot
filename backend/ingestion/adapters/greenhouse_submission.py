import requests

from .submission_base import SubmissionAdapter, SubmissionResult


class GreenhouseSubmissionAdapter(SubmissionAdapter):
    def submit(self, application, answers):
        posting = application.posting
        board_slug = posting.source.config.get('board_slug')
        job_external_id = posting.external_id

        if not board_slug or not job_external_id:
            return SubmissionResult(
                success=False, response_payload={},
                error_message='Missing board slug or job id for this posting.',
            )

        url = f'https://boards-api.greenhouse.io/v1/boards/{board_slug}/jobs/{job_external_id}/apply'

        payload = {
            'first_name': answers.get('first_name', ''),
            'last_name': answers.get('last_name', ''),
            'email': answers.get('email', ''),
            'phone': answers.get('phone', ''),
        }

        files = {}
        resume_path = answers.get('resume_file_path')
        if resume_path:
            files['resume'] = open(resume_path, 'rb')

        try:
            response = requests.post(url, data=payload, files=files or None, timeout=20)
        except requests.exceptions.RequestException as exc:
            return SubmissionResult(success=False, response_payload={}, error_message=str(exc))
        finally:
            for f in files.values():
                f.close()

        if response.status_code in (200, 201):
            return SubmissionResult(success=True, response_payload={'status_code': response.status_code})

        return SubmissionResult(
            success=False,
            response_payload={'status_code': response.status_code, 'body': response.text[:500]},
            error_message=(
                f'Greenhouse returned {response.status_code}. This job may not support '
                f'API-based submission — check if it requires applying through their hosted form instead.'
            ),
        )