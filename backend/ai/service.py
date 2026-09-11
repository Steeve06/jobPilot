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

def score_posting_fit(profile, resume, posting):
    """
    Scores a JobPosting against a Resume: 0-100 fit score, rationale,
    and missing-skills list (FR8). Returns raw call metadata alongside
    the parsed result so the caller (scoring.service) can build its own
    domain-specific ScoringLog without this function needing to know
    about that model.
    """
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    resume_summary = _summarize_resume_for_prompt(resume)

    system_prompt = (
        "You evaluate how well a candidate's resume fits a job posting. "
        "Respond with ONLY the raw JSON object itself as your entire response. "
        "Do not include markdown code fences, backticks, explanatory text, or any "
        "characters before the opening { or after the closing }. "
        "Return ONLY valid JSON matching exactly this shape:\n"
        '{"fit_score": 0, "rationale": "one or two sentence explanation", '
        '"missing_skills": ["skill1", "skill2"]}\n'
        "fit_score must be an integer 0-100. Base it on overlap between the "
        "candidate's actual skills/experience and the job's stated requirements. "
        "Do not reward generic keyword stuffing over genuine relevance. "
        "Weight scoring calibration as follows: skill/technology overlap alone should "
        "not exceed a 70 unless seniority level and domain also match. A clear seniority "
        "mismatch (e.g. an intern posting vs. an experienced candidate, or vice versa) or "
        "a hard requirement the candidate clearly lacks should cap the score at 50 or below, "
        "even if technical skills otherwise overlap well."
    )

    user_content = (
        f"CANDIDATE RESUME:\n{resume_summary}\n\n"
        f"JOB POSTING:\nTitle: {posting.title}\nCompany: {posting.company}\n"
        f"Description: {posting.description_normalized[:4000]}"
    )

    input_payload = {'resume_summary': resume_summary, 'posting_id': posting.id}
    start = time.monotonic()

    try:
        response = client.messages.create(
            model=settings.AI_MODEL,
            max_tokens=500,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )
    except anthropic.APIError as exc:
        latency_ms = int((time.monotonic() - start) * 1000)
        _log_call('scoring', profile, input_payload, {}, latency_ms, error=str(exc))
        raise AIServiceError(f'AI scoring failed: {exc}') from exc

    latency_ms = int((time.monotonic() - start) * 1000)
    text_output = response.content[0].text
    json_candidate = _extract_json_block(text_output)

    try:
        parsed = json.loads(json_candidate)
        fit_score = max(0, min(100, int(parsed.get('fit_score', 0))))  # clamp defensively
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        _log_call(
            'scoring', profile, input_payload, {'raw_output': text_output},
            latency_ms, error=f'Parse failed: {exc}',
        )
        raise AIServiceError('AI returned unparseable scoring output') from exc

    output_payload = {
        'fit_score': fit_score,
        'rationale': parsed.get('rationale', ''),
        'missing_skills': parsed.get('missing_skills', []),
    }
    _log_call('scoring', profile, input_payload, output_payload, latency_ms)

    return {
        'fit_score': fit_score,
        'rationale': parsed.get('rationale', ''),
        'missing_skills': parsed.get('missing_skills', []),
        '_input_payload': input_payload,
        '_output_payload': output_payload,
        '_latency_ms': latency_ms,
    }


def _summarize_resume_for_prompt(resume):
    lines = [f"Skills: {', '.join(resume.skills)}"]
    for exp in resume.experiences.all():
        bullets = '; '.join(b.text for b in exp.bullets.all())
        lines.append(f"{exp.title} at {exp.company}: {bullets}")
    return '\n'.join(lines)