"""Syllabus-supplied bibliography and links; no built-in source catalog.

Entries are source data, not retrieved texts or verified citations.
The filename is retained for existing build entry points.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from course_core import analyze_syllabus

URL = re.compile(r'https?://[^\s<>"\)]+', re.I)


def select_references(syllabus, topic):
    """Keep supplied readings in order without inferring sources from a topic.

    Without the actual texts, book-to-module relevance requires instructor review.
    """
    return [{'id': f'SYL-{i}', 'title': reading}
            for i, reading in enumerate(analyze_syllabus(syllabus)['references'], 1)]


def reference_context(syllabus, topic):
    refs = select_references(syllabus, topic)
    return ('\n'.join(f"[{r['id']}] {r['title']}" for r in refs) if refs else
            'No references supplied in the syllabus. Mark this gap; do not invent a bibliography.')


def reference_section(syllabus, topic):
    refs = select_references(syllabus, topic)
    lines = ['### References', '']
    lines += [f"- [{r['id']}] {r['title']}" for r in refs]
    if refs:
        lines += ['', 'Syllabus reading list: confirm the relevant readings for this module. '
                  'Bibliographic entries are supplied, not independently verified source texts; '
                  'check explanations, citations and answer keys against the actual readings.']
    else:
        lines.append('No references supplied in the syllabus. Add the course readings before teaching; '
                     'no references have been inferred.')
    return '\n'.join(lines)


def _safe_url(url):
    try:
        parsed = urlsplit(url)
        return (parsed.scheme.lower() in {'http', 'https'} and parsed.hostname and
                not parsed.username and not parsed.password)
    except ValueError:
        return False


def restrict_generated_reference_links(text, syllabus):
    """Preserve any-domain bibliography links; flag model-invented URLs."""
    refs = select_references(syllabus, '')
    allowed = {m[0].rstrip('.,;:') for r in refs for m in URL.finditer(r['title'])
               if _safe_url(m[0].rstrip('.,;:'))}
    text = re.sub(r'\[([^\]]+)\]\((https?://[^\s)]+)\)',
                  lambda m: m[0] if m[2] in allowed else m[1] + ' [source link needs verification]', text)

    def replace(match):
        url = match[0].rstrip('.,;:')
        return match[0] if url in allowed else '[source link needs verification]' + match[0][len(url):]

    return URL.sub(replace, text)
