"""Shared one-module-at-a-time generation and resumable, credential-free checkpoints."""
from __future__ import annotations

import hashlib
import re
from urllib.parse import quote_plus, urlsplit

from course_core import (CourseError, MAX_OUTPUT, analyze_syllabus, bounded_text,
                         make_project, validate_pending)
from engines import EngineConfig, generate_course

GEMINI_MODELS = ('gemini-3.8-flash', 'gemini-3.5-flash-lite')
CUSTOM_MODEL = 'Custom model…'


def profile(config):
    # No key in the fingerprint. A replacement key for the same engine can resume.
    base = config.base_url.strip().rstrip('/') if config.provider == 'OpenAI-compatible' else ''
    model = '' if config.provider == 'Local template' else config.model.strip().removeprefix('models/')
    return hashlib.sha256((config.provider + '\n' + model + '\n' + base).encode()).hexdigest()


def new_job(syllabus, title, config, indices=None):
    plan = analyze_syllabus(syllabus)
    if not plan['topics']:
        raise CourseError('No modules found. Add lines such as Week 1: Aircraft loads.')
    selected = list(range(len(plan['topics']))) if indices is None else list(indices)
    job = {'syllabus': syllabus, 'title': title.strip() or plan['metadata'].get('title', 'Untitled Course'),
           'provider': config.provider, 'model': '' if config.provider == 'Local template' else config.model.strip(),
           'profile': profile(config), 'indices': selected, 'completed': []}
    return validate_pending(job)


def can_resume(job, syllabus, title, config, indices=None):
    if not job:
        return False
    target = new_job(syllabus, title, config, indices)
    return (len(job['completed']) < len(job['indices']) and
            all(job[k] == target[k] for k in ('syllabus', 'title', 'profile', 'indices')))


def is_complete(job):
    return bool(job) and len(job['completed']) == len(job['indices'])


def video_resources(syllabus, topic, course_title):
    query = f"{course_title} {topic}".strip()
    lines = ['### Video resources', '',
             f'- [Find a lesson on YouTube](https://www.youtube.com/results?search_query={quote_plus(query + " lecture")})',
             f'- [Find a worked example](https://www.youtube.com/results?search_query={quote_plus(query + " worked example")})']
    videos = []
    for link in re.findall(r'https?://[^\s<>"\)]+', syllabus):
        link = link.rstrip('.,;]')
        try:
            parsed = urlsplit(link)
        except ValueError:
            continue
        if (parsed.scheme == 'https' and not parsed.username and not parsed.password and
                parsed.hostname in {'youtube.com', 'www.youtube.com', 'youtu.be', 'vimeo.com', 'www.vimeo.com'}):
            if link not in videos:
                videos.append(link)
    if videos:
        lines += ['', 'Syllabus-supplied videos (check relevance to this module):']
        lines += [f'- [Syllabus video {i}]({link})' for i, link in enumerate(videos[:12], 1)]
    lines += ['', 'Choose and review videos for accuracy, level, captions, and availability before teaching.']
    return '\n'.join(lines)


def remove_invented_video_links(text, syllabus):
    supplied = {u.rstrip(".,;]") for u in re.findall(r'https?://[^\s<>"\)]+', syllabus)}
    def allowed(url):
        try:
            return (url in supplied or urlsplit(url).hostname not in
                    {'youtube.com', 'www.youtube.com', 'youtu.be', 'vimeo.com', 'www.vimeo.com'})
        except ValueError:
            return False
    text = re.sub(r'\[([^\]]*)\]\((https?://[^\s)]+)\)',
                  lambda m: m[0] if allowed(m[2]) else m[1] + ' (use video searches below)', text)
    return re.sub(r'https?://[^\s<>\)]+',
                  lambda m: m[0] if allowed(m[0]) else '(use video searches below)', text)


def draft_text(job):
    job = validate_pending(job)
    plan = analyze_syllabus(job['syllabus'])
    lines = [f"# {job['title']}", '', '> Draft · instructor review required.', '', '## Course outcomes', '']
    lines += [f'{i}. {text}' for i, text in enumerate(plan['outcomes'], 1)] or ['[Confirm course outcomes.]']
    lines += ['', '## Modules', '']
    for index in job['indices']:
        topic = plan['topics'][index]
        lines.append(f"- Module {index + 1}: {topic['title']} · Week(s): {topic['schedule'] or 'Unassigned'}")
    lines += ['', f"**Progress:** {len(job['completed'])}/{len(job['indices'])} modules.", '']
    lines += job['completed']
    remaining = job['indices'][len(job['completed']):]
    if remaining:
        lines += ['', '## Not generated yet', *[f"- Module {i + 1}: {plan['topics'][i]['title']}" for i in remaining]]
    lines += ['', '## Instructor review', '- Check facts, worked examples, activities, answer guides, and supplied references.',
              '- Confirm syllabus coverage, timing, assessment load, and video suitability.', '']
    result = '\n'.join(lines)
    bounded_text(result, 'Course draft', MAX_OUTPUT)
    return result


def advance(job, config, *, transport=None):
    """Return a new checkpoint only after the next module succeeds. Never retry a paid call."""
    job = validate_pending(job)
    if job['profile'] != profile(config):
        raise CourseError('The agent model or endpoint changed. Start a new draft to use it.')
    if is_complete(job):
        return job
    index = job['indices'][len(job['completed'])]
    topic = analyze_syllabus(job['syllabus'])['topics'][index]
    text = generate_course(job['syllabus'], job['title'], config, module_index=index, transport=transport)
    text = re.sub(r'(?ms)^### Video resources\s*\n.*?(?=^### |^## |\Z)', '', text)
    text = remove_invented_video_links(text, job['syllabus'])
    text = re.sub(r'(?m)^#{1,2} .+\n?', '', text)
    text = re.sub(r'(?im)^\*\*Week\(s\):\*\*[^\n]*(?:\n|$)', '', text).strip()
    module = f"## Module {index + 1}: {topic['title']}\n\n**Week(s):** {topic['schedule'] or 'Unassigned'}\n\n{text}\n\n"
    module += video_resources(job['syllabus'], topic['title'], job['title']) + '\n'
    updated = validate_pending({**job, 'completed': [*job['completed'], module]})
    draft_text(updated)  # Check the entire rendered draft bound before exposing a checkpoint.
    return updated


def accept_job(project, job):
    if not is_complete(job):
        raise CourseError('Finish the selected modules before using the draft. Save a project to keep partial work.')
    job = validate_pending(job)
    return make_project(job['syllabus'], job['title'], draft_text(job), job['provider'], model=job['model'])
