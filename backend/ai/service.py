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

def tailor_resume(profile, resume, posting, tailoring_settings=None):
    
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    bullet_library = _build_bullet_library(resume)

    style_rules = []
    if tailoring_settings:
        if tailoring_settings.avoid_em_dash:
            style_rules.append("Never use an em dash (—) anywhere. Use commas, colons, or restructure the sentence.")
        if tailoring_settings.exclude_company_name_from_body:
            style_rules.append(f"Never mention the company name ('{posting.company}') anywhere in the output.")
        if tailoring_settings.professional_title:
            style_rules.append(f"Use this exact professional title in the summary context: '{tailoring_settings.professional_title}'. Do not mirror the job posting's title.")
        if tailoring_settings.max_bullets_per_experience:
            style_rules.append(f"Include at most {tailoring_settings.max_bullets_per_experience} bullets per experience entry.")
        if tailoring_settings.max_bullets_per_project:
            style_rules.append(f"Include at most {tailoring_settings.max_bullets_per_project} bullets per project entry.")
        if tailoring_settings.style_notes:
            style_rules.append(tailoring_settings.style_notes)

    style_block = ('\n' + '\n'.join(f'- {r}' for r in style_rules)) if style_rules else ''

    system_prompt = (
        "You are tailoring resume bullets for a specific job posting. For each experience/project, "
        "select relevant existing bullets (by the id given below) and you MAY rewrite their wording "
        "to better emphasize relevance to the posting — but you must ONLY restate facts, tools, "
        "numbers, and outcomes already present in that specific bullet's original text. Never invent "
        "a fact, metric, tool, or outcome not already stated in the source bullet you are rewriting. "
        "Write natural, human-sounding bullets, not a mirror of the job posting's own phrasing. "
        "The result must fit on a SINGLE PAGE resume: be concise, prioritize only the most relevant "
        "bullets per entry, and trim rather than include everything. When in doubt, favor fewer, "
        "stronger bullets over a complete list. "
        "Also write a new professional summary using only facts present in the resume below."
        + style_block + "\n"
        "Respond with ONLY the raw JSON object itself, no markdown fences. Return ONLY valid JSON:\n"
        '{"summary": "2-3 sentence summary", '
        '"experience_bullets": {"<experience_id>": [{"source_bullet_id": 0, "text": "rewritten or original text"}]}, '
        '"project_bullets": {"<project_id>": [{"source_bullet_id": 0, "text": "..."}]}}\n'
        "source_bullet_id must always be a real id from the bullet library below — never invent one."
    )

    user_content = (
        f"JOB POSTING:\nTitle: {posting.title}\nCompany: {posting.company}\n"
        f"Description: {posting.description_normalized[:4000]}\n\n"
        f"RESUME BULLET LIBRARY:\n{bullet_library}"
    )

    input_payload = {'posting_id': posting.id, 'style_rules': style_rules}
    start = time.monotonic()

    try:
        response = client.messages.create(
            model=settings.AI_MODEL, max_tokens=2500,
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
        _log_call('tailoring', profile, input_payload, {'raw_output': text_output}, latency_ms, error=f'Parse failed: {exc}')
        raise AIServiceError('AI returned unparseable tailoring output') from exc

    content = _build_tailored_content(resume, parsed)
    output_payload = {
        'summary': content['summary'],
        'experience_bullets': parsed.get('experience_bullets', {}),
        'project_bullets': parsed.get('project_bullets', {}),
    }
    _log_call('tailoring', profile, input_payload, output_payload, latency_ms)

    return {
        'content': content, '_input_payload': input_payload,
        '_output_payload': output_payload, '_latency_ms': latency_ms,
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
    Builds a dict matching the ResumeSerializer shape. Bullet text now
    comes from the MODEL's rewrite (validated only for a real
    source_bullet_id reference, not for exact text match) — see the
    architecture note on tailor_resume for the guarantee tradeoff this
    represents as of Sprint 12. source_bullet_id is carried through on
    every bullet so the frontend diff view can trace rewrites back to
    their origin.
    """
    exp_bullets = parsed.get('experience_bullets', {})
    proj_bullets = parsed.get('project_bullets', {})

    experiences = []
    for exp in resume.experiences.all():
        valid_source_ids = set(exp.bullets.values_list('id', flat=True))
        requested = exp_bullets.get(str(exp.id), [])
        rewritten = [
            {
                'text': item.get('text', ''),
                'skill_tags': [],
                'source_bullet_id': item.get('source_bullet_id'),
            }
            for item in requested
            if item.get('source_bullet_id') in valid_source_ids and item.get('text', '').strip()
        ]
        if not rewritten:
            rewritten = [
                {'text': b.text, 'skill_tags': b.skill_tags, 'source_bullet_id': b.id}
                for b in exp.bullets.all()
            ]
        experiences.append({
            'company': exp.company, 'title': exp.title,
            'start_date': str(exp.start_date) if exp.start_date else None,
            'end_date': str(exp.end_date) if exp.end_date else None,
            'bullets': rewritten,
        })

    projects = []
    for proj in resume.projects.all():
        valid_source_ids = set(proj.bullets.values_list('id', flat=True))
        requested = proj_bullets.get(str(proj.id), [])
        rewritten = [
            {
                'text': item.get('text', ''),
                'skill_tags': [],
                'source_bullet_id': item.get('source_bullet_id'),
            }
            for item in requested
            if item.get('source_bullet_id') in valid_source_ids and item.get('text', '').strip()
        ]
        if not rewritten:
            rewritten = [
                {'text': b.text, 'skill_tags': b.skill_tags, 'source_bullet_id': b.id}
                for b in proj.bullets.all()
            ]
        projects.append({'name': proj.name, 'bullets': rewritten})

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