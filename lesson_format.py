"""Teaching-module structure, output sanitization, and assessment validation; no UI or network dependency."""
from __future__ import annotations
import re
from course_core import CourseError

DISCUSSION = 'Discussion and presentation'
SECTIONS = (DISCUSSION, 'Activity', 'Assessment', 'Answer key')

# Strip C0/C1 control chars (except tab/newline) and Unicode bidi/spoofing overrides.
_UNSAFE_CONTROLS = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\u200e\u200f\u202a-\u202e\u2066-\u2069\ufeff]')
_DANGEROUS_HTML_BLOCKS = re.compile(
    r'(?is)<(script|style|iframe|object|form)\b[^>]*>.*?</\1\s*>'
    r'|<(?:script|style|iframe|object|embed|form)\b[^>]*/?>'
    r'|<!--.*?-->'
)
_UNSAFE_MD_LINK = re.compile(r'!?\[([^\]]*)\]\(\s*(?:javascript|vbscript|data|file)\s*:[^)]*\)', re.I)
_UNSAFE_BARE_URI = re.compile(r'(?i)\b(?:javascript|vbscript):[^\s<>"\)]+|data:text/html[^\s<>"\)]*')
_OUTER_FENCE = re.compile(r'^\s*```(?:markdown|md)?\s*\n(.*?)\n```\s*$', re.I | re.S)


_BOLD_HEADING = re.compile(r'(?m)^(#{3,4})\s+\*\*([^*]+?)\*\*\s*:?\s*$')
_PLACEHOLDER_LEAK = re.compile(r'\[(?:todo|tbd|insert|placeholder)(?:[:\s-][^\]]*)?\]', re.I)


def _normalize_answer_key_block(text: str) -> str:
    def clean_key(match):
        body = match[2]
        cleaned_lines = []
        for raw in body.splitlines():
            line = raw.strip()
            if not line:
                continue
            bold_entry = re.fullmatch(r'\*{0,2}([1-5])[.)]\*{0,2}\s*\*{0,2}([A-D])\*{0,2}\.?', line)
            cleaned_lines.append(f'{bold_entry[1]}. {bold_entry[2]}' if bold_entry else line)
        return f"{match[1]}\n" + "\n".join(cleaned_lines) + "\n"
    return re.sub(r'(?ims)(^###\s+Answer key)\s*\n(.*?)(?=^#{1,3}\s|\Z)', clean_key, text)


def sanitize_generated_markdown(text: str) -> str:
    """Sanitize untrusted model Markdown while preserving teaching prose and math."""
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = _UNSAFE_CONTROLS.sub('', text)
    fenced = _OUTER_FENCE.match(text)
    if fenced:
        text = fenced[1]
    text = _DANGEROUS_HTML_BLOCKS.sub('', text)
    text = _UNSAFE_MD_LINK.sub(lambda m: (m[1].strip() + ' ' if m[1].strip() else '') + '[unsafe link removed]', text)
    text = _UNSAFE_BARE_URI.sub('[unsafe link removed]', text)
    text = _BOLD_HEADING.sub(r'\1 \2', text)
    text = _normalize_answer_key_block(text)
    text = '\n'.join(line.rstrip() for line in text.splitlines())
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def section_body(text, heading):
    match = re.search(r'(?ims)^###\s+' + re.escape(heading) + r'\s*\n(.*?)(?=^#{1,3}\s|\Z)', text)
    return match[1].strip() if match else ''


def _subsection_body(section_text, heading):
    match = re.search(r'(?ims)^####\s+' + re.escape(heading) + r'\s*\n(.*?)(?=^#{1,4}\s|\Z)', section_text)
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
    non_empty = [line.strip() for line in key.splitlines() if line.strip()]
    entries = re.findall(r'(?m)^\s*([1-5])[.)]\s*([A-D])\s*$', '\n'.join(non_empty))
    if [number for number, letter in entries] != ['1', '2', '3', '4', '5']:
        raise CourseError('The answer key needs five numbered letters, for example 1. B. Retry this module.')
    if len(non_empty) != 5:
        raise CourseError('Use only numbered answer letters in the answer key.')


def lesson_review_notes(text):
    """Collect advisory structural and quality notes without rejecting completed drafts."""
    notes = []
    missing_sections = [heading for heading in SECTIONS
                        if not re.sub(r'(?m)^#+.*$', '', section_body(text, heading)).strip()]
    for heading in missing_sections:
        notes.append(f'The module is missing {heading.lower()}. Check the draft before teaching.')
    discussion = section_body(text, DISCUSSION)
    if discussion:
        missing_parts = [part for part in ('Introduction', 'Presentation sequence', 'Worked example', 'Summary')
                         if not re.search(r'(?im)^####\s+' + part + r'\s*$', discussion)]
        if missing_parts:
            notes.append(f"The presentation sequence is missing {', '.join(missing_parts)}. Check the draft before teaching.")
        if len(re.findall(r'\b\w+\b', discussion)) < 60:
            notes.append('The module discussion is too short to review as a lesson. Check the draft before teaching.')
        sequence = _subsection_body(discussion, 'Presentation sequence')
        if sequence and len(re.findall(r'(?m)^\s*\d+[.)]\s+\S', sequence)) < 3:
            notes.append('Presentation sequence has fewer than 3 numbered teaching segments. Check the draft before teaching.')
    questions = section_body(text, 'Assessment')
    if questions:
        chunks = re.split(r'(?m)^\s*([1-5])[.)]\s+', questions)
        numbers = chunks[1::2]
        if numbers != ['1', '2', '3', '4', '5']:
            notes.append('Assessment must contain questions 1–5. Check the draft before teaching.')
        else:
            bad_options, duplicate_options = False, False
            for question in chunks[2::2]:
                opts = re.findall(r'(?m)^\s*([A-D])[.)]\s+(.+)$', question)
                if [letter for letter, _ in opts] != ['A', 'B', 'C', 'D']:
                    bad_options = True
                else:
                    normalized = [re.sub(r'\s+', ' ', label.strip().lower()) for _, label in opts]
                    if len(set(normalized)) != 4:
                        duplicate_options = True
            if bad_options:
                notes.append('Each question needs options A–D. Check the draft before teaching.')
            if duplicate_options:
                notes.append('One or more assessment questions contain duplicate options. Check the draft before teaching.')
    key = section_body(text, 'Answer key')
    if key:
        non_empty = [line.strip() for line in key.splitlines() if line.strip()]
        entries = re.findall(r'(?m)^\s*([1-5])[.)]\s*([A-D])\s*$', '\n'.join(non_empty))
        if [number for number, letter in entries] != ['1', '2', '3', '4', '5']:
            notes.append('The answer key needs five numbered letters, for example 1. B. Check the draft before teaching.')
        else:
            if len(non_empty) != 5:
                notes.append('Use only numbered answer letters in the answer key. Check the draft before teaching.')
            if len({letter for _, letter in entries}) == 1:
                notes.append('All five answer key letters are identical; review option balance before teaching.')
    if _PLACEHOLDER_LEAK.search(text):
        notes.append('Draft contains unfilled placeholder markers ([TODO]/[Insert]); complete them before teaching.')
    return notes


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
