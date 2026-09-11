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

def tailor_resume(profile, resume, posting):
    """
    Selects and reorders existing resume bullets to best match a job
    posting, and generates a rewritten summary. Per FR12: bullet TEXT is
    never generated by the model — only which existing bullets to include
    per experience/project, and their order. Every returned bullet id is
    validated against the real database records before use, so fabricated
    content cannot enter a tailored resume even if the model hallucinates
    an id.
    """
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    bullet_library = _build_bullet_library(resume)

    system_prompt = (
        "You are tailoring a resume's bullet point selection for a specific job posting. "
        "You do NOT write or rewrite bullet text — you only choose which existing bullets "
        "(by id, given below) to include for each experience/project, and their order, plus "
        "write a new professional summary. "
        "Respond with ONLY the raw JSON object itself as your entire response, no markdown fences. "
        "Return ONLY valid JSON matching exactly this shape:\n"
        '{"summary": "2-3 sentence professional summary", '
        '"experience_bullet_order": {"<experience_id>": [bullet_id, bullet_id, ...]}, '
        '"project_bullet_order": {"<project_id>": [bullet_id, ...]}}\n'
        "Only use bullet ids that were given to you below — never invent an id. Select the "
        "most relevant bullets per entry (you may omit less-relevant ones, but keep at least "
        "one bullet per experience if any exist) and order them by relevance to the posting. "
        "The summary must only restate facts already present in the resume below — never "
        "invent skills, employers, titles, or achievements not shown."
    )

    user_content = (
        f"JOB POSTING:\nTitle: {posting.title}\nCompany: {posting.company}\n"
        f"Description: {posting.description_normalized[:4000]}\n\n"
        f"RESUME BULLET LIBRARY:\n{bullet_library}"
    )

    input_payload = {'posting_id': posting.id}
    start = time.monotonic()

    try:
        response = client.messages.create(
            model=settings.AI_MODEL, max_tokens=2000,
            system=system_prompt, messages=[{"role": "user", "content": user_content}],
        )
    except anthropic.APIError as exc:
        latency_ms = int((time.monotonic() - start) * 1000)
        _log_call('tailoring', profile, input_payload, {}, latency_ms, error=str(exc))
        raise AIServiceError(f'AI tailoring failed: {exc}') from exc

    latency_ms = int((time.monotonic() - start) * 1000)
    text_output = response.content[0].text
    json_candidate = _extract_json_block(text_output)

    try:
        parsed = json.loads(json_candidate)
    except json.JSONDecodeError as exc:
        _log_call(
            'tailoring', profile, input_payload, {'raw_output': text_output},
            latency_ms, error=f'Parse failed: {exc}',
        )
        raise AIServiceError('AI returned unparseable tailoring output') from exc

    content = _build_tailored_content(resume, parsed)

    output_payload = {
        'summary': content['summary'],
        'experience_bullet_order': parsed.get('experience_bullet_order', {}),
        'project_bullet_order': parsed.get('project_bullet_order', {}),
    }
    _log_call('tailoring', profile, input_payload, output_payload, latency_ms)

    return {
        'content': content,
        '_input_payload': input_payload,
        '_output_payload': output_payload,
        '_latency_ms': latency_ms,
    }


def _build_bullet_library(resume):
    lines = []
    for exp in resume.experiences.all():
        lines.append(f"Experience [id={exp.id}] {exp.title} at {exp.company}:")
        for b in exp.bullets.all():
            lines.append(f"  bullet [id={b.id}]: {b.text}")
    for proj in resume.projects.all():
        lines.append(f"Project [id={proj.id}] {proj.name}:")
        for b in proj.bullets.all():
            lines.append(f"  bullet [id={b.id}]: {b.text}")
    return '\n'.join(lines)


def _build_tailored_content(resume, parsed):
    """
    Builds a dict matching the same shape ResumeSerializer produces, so
    render_resume_to_docx() (Sprint 8) can render a TailoredResume with
    zero changes. Every bullet's text/skill_tags is read directly from
    the database — the model only ever supplies an ordering of ids.
    """
    exp_order = parsed.get('experience_bullet_order', {})
    proj_order = parsed.get('project_bullet_order', {})

    experiences = []
    for exp in resume.experiences.all():
        all_bullets = {b.id: b for b in exp.bullets.all()}
        requested_ids = exp_order.get(str(exp.id), [])
        valid_ids = [bid for bid in requested_ids if bid in all_bullets]
        if not valid_ids:
            valid_ids = list(all_bullets.keys())  # fallback: model gave nothing usable, keep original
        experiences.append({
            'company': exp.company, 'title': exp.title,
            'start_date': str(exp.start_date) if exp.start_date else None,
            'end_date': str(exp.end_date) if exp.end_date else None,
            'bullets': [
                {'text': all_bullets[bid].text, 'skill_tags': all_bullets[bid].skill_tags}
                for bid in valid_ids
            ],
        })

    projects = []
    for proj in resume.projects.all():
        all_bullets = {b.id: b for b in proj.bullets.all()}
        requested_ids = proj_order.get(str(proj.id), [])
        valid_ids = [bid for bid in requested_ids if bid in all_bullets]
        if not valid_ids:
            valid_ids = list(all_bullets.keys())
        projects.append({
            'name': proj.name,
            'bullets': [
                {'text': all_bullets[bid].text, 'skill_tags': all_bullets[bid].skill_tags}
                for bid in valid_ids
            ],
        })

    return {
        'full_name': resume.full_name, 'email': resume.email, 'phone': resume.phone,
        'location': resume.location, 'linkedin_url': resume.linkedin_url,
        'github_url': resume.github_url,
        'summary': parsed.get('summary') or resume.summary,
        'skills': resume.skills, 'education': resume.education,
        'experiences': experiences, 'projects': projects,
    }

def _summarize_resume_for_prompt(resume):
    lines = [f"Skills: {', '.join(resume.skills)}"]
    for exp in resume.experiences.all():
        bullets = '; '.join(b.text for b in exp.bullets.all())
        lines.append(f"{exp.title} at {exp.company}: {bullets}")
    return '\n'.join(lines)