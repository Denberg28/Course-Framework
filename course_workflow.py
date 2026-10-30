"""Shared one-module-at-a-time generation and resumable, credential-free checkpoints."""
from __future__ import annotations

import hashlib
import re

from course_core import (CourseError, MAX_OUTPUT, analyze_syllabus, bounded_text,
                         course_allocation, make_project, topic_allocation, validate_pending)
from engines import EngineConfig, generate_course
from reference_catalog import reference_section, restrict_generated_reference_links
from lesson_format import validate_lesson

GEMINI_MODELS = ('gemini-3.8-flash', 'gemini-3.5-flash-lite')
CUSTOM_MODEL = 'Custom model…'


def profile(config):
    # No key in the fingerprint. A replacement key for the same engine can resume.
    base = config.base_url.strip().rstrip('/') if config.provider == 'OpenAI-compatible' else ''
    model = '' if config.provider == 'Local template' else config.model.strip().removeprefix('models/')
    return hashlib.sha256(('syllabus-references-v3\n' + config.provider + '\n' + model + '\n' + base).encode()).hexdigest()


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


def remove_video_sections(text):
    text = re.sub(r'(?ims)^#{1,6}\s+(?:recommended\s+|suggested\s+)?video[^\n]*\n.*?(?=^#{1,3}\s|\Z)', '', text)
    # Video URLs are not part of new module creation, including supplied syllabus links.
    text = re.sub(r'\[[^\]]*\]\(https?://(?:www\.)?(?:youtube\.com|youtu\.be|vimeo\.com)/[^\s)]+\)', '', text, flags=re.I)
    return re.sub(r'https?://(?:www\.)?(?:youtube\.com|youtu\.be|vimeo\.com)/[^\s<>)]*', '', text, flags=re.I)


def draft_text(job):
    job = validate_pending(job)
    plan = analyze_syllabus(job['syllabus'])
    lines = [f"# {job['title']}", '', '> Draft · instructor review required.', '']
    for field, value in plan['metadata'].items():
        if field != 'title':
            lines += [f"**{field.replace('_', ' ').title()}:** {value:g}" if isinstance(value, (int, float))
                      else f"**{field.replace('_', ' ').title()}:** {value}", '']
    lines += ['## Course outcomes', '']
    lines += [f'{i}. {text}' for i, text in enumerate(plan['outcomes'], 1)] or ['[Confirm course outcomes.]']
    lines += ['', '## Course allocation', '', course_allocation(plan, job['indices'])]
    if plan['references']:
        lines += ['', '## Syllabus readings', '', *[f'- {r}' for r in plan['references']]]
    lines += ['']
    lines += job['completed']
    remaining = job['indices'][len(job['completed']):]
    if remaining:
        lines += ['', '## Not generated yet', *[f"- Module {i + 1}: {plan['topics'][i]['title']}" for i in remaining]]
    lines += ['']
    result = remove_video_sections('\n'.join(lines))
    bounded_text(result, 'Course draft', MAX_OUTPUT)
    return result


def advance(job, config, *, transport=None):
    """Return a new checkpoint only after the next module succeeds. Never retry a paid call."""
    job = validate_pending(job)
    if job['profile'] != profile(config):
        raise CourseError('The generation format, agent model, or endpoint changed. Start a new draft to use it.')
    if is_complete(job):
        return job
    index = job['indices'][len(job['completed'])]
    topic = analyze_syllabus(job['syllabus'])['topics'][index]
    text = generate_course(job['syllabus'], job['title'], config, module_index=index, transport=transport)
    text = restrict_generated_reference_links(remove_video_sections(text), job['syllabus'])
    text = re.sub(r'(?ims)^###\s+References\s*\n.*?(?=^#{1,3}\s|\Z)', '', text)
    text = re.sub(r'(?m)^#{1,2} .+\n?', '', text)
    text = re.sub(r'(?im)^\*\*(?:Week\(s\)|Allocation):\*\*[^\n]*(?:\n|$)', '', text).strip()
    if config.provider != 'Local template':
        validate_lesson(text)
    allocation = (f"**Allocation:** {topic_allocation(topic)}" if 'lecture_hours' in topic or 'lab_hours' in topic
                  else f"**Week(s):** {topic['schedule'] or 'Unassigned'}")
    module = f"## Module {index + 1}: {topic['title']}\n\n{allocation}\n\n{text}\n\n"
    module += reference_section(job['syllabus'], topic['title']) + '\n'
    updated = validate_pending({**job, 'completed': [*job['completed'], module]})
    draft_text(updated)  # Check the entire rendered draft bound before exposing a checkpoint.
    return updated


def accept_job(project, job):
    if not is_complete(job):
        raise CourseError('Finish the selected modules before using the draft. Save a project to keep partial work.')
    job = validate_pending(job)
    return make_project(job['syllabus'], job['title'], draft_text(job), job['provider'], model=job['model'])
