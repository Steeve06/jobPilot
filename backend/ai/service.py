import json
import re
import time

import anthropic
from django.conf import settings

from .models import AICallLog


class AIServiceError(Exception):
    pass


def _log_call(purpose, profile, input_payload, output_payload, latency_ms, error=''):
    AICallLog.objects.create(
        purpose=purpose,
        profile=profile,
        input_payload=input_payload,
        output_payload=output_payload,
        model_version=settings.AI_MODEL,
        latency_ms=latency_ms,
        error=error,
    )


def _extract_json_block(text):
    """
    Models sometimes wrap JSON in markdown fences or add a sentence of
    preamble/postamble despite instructions not to. Strip that defensively
    rather than trusting the model to always return a bare JSON object.
    """
    text = text.strip()
    fence_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', text, re.DOTALL)
    if fence_match:
        return fence_match.group(1)

    first_brace = text.find('{')
    last_brace = text.rfind('}')
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return text[first_brace:last_brace + 1]

    return text


def extract_resume(profile, raw_text):
    """
    Given raw text extracted from an uploaded resume file, ask the model
    to return structured resume data matching our schema. The caller is
    responsible for presenting this as a *draft* for user review — this
    function never writes to the Resume model directly (ADR-007).
    """
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    system_prompt = (
        "You extract structured resume data from raw resume text. "
        "Respond with ONLY the raw JSON object itself as your entire response. "
        "Do not include markdown code fences, backticks, explanatory text, or any "
        "characters before the opening { or after the closing }. "
        "Return ONLY valid JSON matching exactly this shape:\n"
        '{"full_name": "", "email": "", "phone": "", "location": "", '
        '"linkedin_url": "full https:// URL or empty string", "github_url": "full https:// URL or empty string", "summary": "", '
        '"skills": ["skill1", "skill2"], '
        '"experiences": [{"company": "", "title": "", "start_date": "YYYY-MM-DD", '
        '"end_date": "YYYY-MM-DD or null", "bullets": [{"text": "", "skill_tags": []}]}], '
        '"projects": [{"name": "", "bullets": [{"text": "", "skill_tags": []}]}], '
        '"education": [{"degree": "", "school": "", "start_year": "", "end_year": ""}]}\n'
        "Only extract facts present in the source text. Never invent experience, dates, or skills. "
        "If a field is not present in the source, leave it as an empty string, empty array, or null."
    )

    start = time.monotonic()
    try:
        response = client.messages.create(
            model=settings.AI_MODEL,
            max_tokens=4000,
            system=system_prompt,
            messages=[{"role": "user", "content": raw_text}],
        )
    except anthropic.APIError as exc:
        latency_ms = int((time.monotonic() - start) * 1000)
        _log_call('resume_extraction', profile, {'raw_text_length': len(raw_text)}, {}, latency_ms, error=str(exc))
        raise AIServiceError(f'AI extraction failed: {exc}') from exc

    latency_ms = int((time.monotonic() - start) * 1000)
    text_output = response.content[0].text
    json_candidate = _extract_json_block(text_output)

    try:
        parsed = json.loads(json_candidate)
    except json.JSONDecodeError as exc:
        _log_call(
            'resume_extraction', profile,
            {'raw_text_length': len(raw_text)}, {'raw_output': text_output},
            latency_ms, error=f'JSON parse failed: {exc}',
        )
        raise AIServiceError('AI returned non-JSON output; please try again or fill the form manually.') from exc

    _log_call(
        'resume_extraction', profile,
        {'raw_text_length': len(raw_text)}, parsed, latency_ms,
    )
    return parsed