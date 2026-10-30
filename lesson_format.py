"""Teaching-module structure and assessment validation; no UI or network dependency."""
from __future__ import annotations
import re
from course_core import CourseError

DISCUSSION = 'Discussion and presentation'
SECTIONS = (DISCUSSION, 'Activity', 'Assessment', 'Answer key')


def section_body(text, heading):
    match = re.search(r'(?ims)^###\s+' + re.escape(heading) + r'\s*\n(.*?)(?=^#{1,3}\s|\Z)', text)
    return match[1].strip() if match else ''


def validate_lesson(text):
    for heading in SECTIONS:
        body = re.sub(r'(?m)^#+.*$', '', section_body(text, heading)).strip()
        if not body:
            raise CourseError(f'The module is missing {heading.lower()}. Completed modules are preserved.')
    discussion = section_body(text, DISCUSSION)
    for part in ('Introduction', 'Presentation sequence', 'Worked example', 'Summary'):
        if not re.search(r'(?im)^####\s+' + part + r'\s*$', discussion):
            raise CourseError('The presentation sequence is incomplete. Retry this module; completed work is preserved.')
    if len(re.findall(r'\b\w+\b', discussion)) < 60:
        raise CourseError('The module discussion is too short to review as a lesson. Retry this module.')
    questions = section_body(text, 'Assessment')
    chunks = re.split(r'(?m)^\s*([1-5])[.)]\s+', questions)
    numbers = chunks[1::2]
    if numbers != ['1', '2', '3', '4', '5']:
        raise CourseError('Assessment must contain questions 1–5. Retry this module.')
    for question in chunks[2::2]:
        if re.findall(r'(?m)^\s*([A-D])[.)]\s+\S', question) != ['A', 'B', 'C', 'D']:
            raise CourseError('Each question needs options A–D. Retry this module.')
    key = section_body(text, 'Answer key')
    entries = re.findall(r'(?m)^\s*([1-5])[.)]\s*([A-D])\s*$', key)
    if [number for number, letter in entries] != ['1', '2', '3', '4', '5']:
        raise CourseError('The answer key needs five numbered letters, for example 1. B. Retry this module.')
    if len(key.splitlines()) != 5:
        raise CourseError('Use only numbered answer letters in the answer key.')


def lesson_review_notes(text):
    """Formatting is advisory when generating; retain useful completed drafts."""
    try:
        validate_lesson(text)
    except CourseError as error:
        note = str(error).split(' Completed modules')[0].split(' Retry this module')[0]
        return [note.rstrip('.') + '. Check the draft before teaching.']
    return []


def presentation_parts(text):
    """Separate assessment/key from prose for collapsible previews; preserve legacy text."""
    modules = re.split(r'(?m)(^## Module \d+:[^\n]*\n)', text)
    result = []
    if modules[0].strip():
        result.append({'title': '', 'body': modules[0].strip(), 'assessment': '', 'key': '', 'references': ''})
    for offset in range(1, len(modules), 2):
        title, body = modules[offset].strip(), modules[offset + 1]
        assessment, key = section_body(body, 'Assessment'), section_body(body, 'Answer key')
        references = section_body(body, 'References')
        body = re.sub(r'(?ims)^###\s+(?:Assessment|Answer key|References)\s*\n.*?(?=^#{1,3}\s|\Z)', '', body).strip()
        result.append({'title': title, 'body': body, 'assessment': assessment, 'key': key, 'references': references})
    return result
