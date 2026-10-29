"""Official source locations checked 29 October 2026, selected by syllabus/topic.

This is a curated link catalog, not full-text retrieval or verification of AI claims.
"""
from __future__ import annotations
import re

CHECKED = '2026-10-29'
CATALOG = (
    {'id': 'FAA-HANDBOOKS', 'title': 'FAA Aviation Handbooks & Manuals',
     'url': 'https://www.faa.gov/regulations_policies/handbooks_manuals/aviation',
     'scope': 'US aviation handbooks; choose the relevant maintenance, flying, or other handbook and chapter.'},
    {'id': 'CAAP-PCAR', 'title': 'CAAP Philippine Civil Aviation Regulations and Standards',
     'url': 'https://www.caap.gov.ph/philippine-civil-aviation-regulations/',
     'scope': 'Philippine regulations; confirm current part, revision and applicability.'},
    {'id': 'EASA-EAR', 'title': 'EASA Easy Access Rules',
     'url': 'https://www.easa.europa.eu/en/document-library/easy-access-rules',
     'scope': 'European rules; choose the applicable CS/Part and revision, separately from Philippine rules.'},
    {'id': 'MIT-MATERIALS', 'title': 'MIT OpenCourseWare — Mechanics & Materials I',
     'url': 'https://ocw.mit.edu/courses/2-001-mechanics-materials-i-fall-2006/',
     'scope': 'University mechanics-of-solids course materials.'},
    {'id': 'OPENSTAX-ELASTICITY', 'title': 'OpenStax University Physics Vol. 1 — Stress, Strain, and Elastic Modulus',
     'url': 'https://openstax.org/books/university-physics-volume-1/pages/12-3-stress-strain-and-elastic-modulus',
     'scope': 'University-level stress, strain and elasticity teaching reference.'},
)


def select_references(syllabus, topic):
    context = syllabus.lower()
    focus = topic.lower()
    ids = set()
    aviation = bool(re.search(r'\b(aircraft|aviation|aeronautical|airframe|flight|airworthiness|rpas|drone|caap|easa|faa)\b', context))
    if aviation:
        ids.add('FAA-HANDBOOKS')
    if aviation and (re.search(r'\b(caap|pcar|philippine|philippines)\b', context) or
                     re.search(r'\b(airworthiness|regulation|licensing|certification|rpas|drone)\b', focus)):
        ids.add('CAAP-PCAR')
    if aviation and ('easa' in context or re.search(r'\b(airworthiness|certification|regulation)\b', focus)):
        ids.add('EASA-EAR')
    if re.search(r'\b(stress|strain|strength|materials|structures|bending|torsion|elasticity|solid mechanics)\b', focus):
        ids.update(('MIT-MATERIALS', 'OPENSTAX-ELASTICITY'))
    return [dict(ref) for ref in CATALOG if ref['id'] in ids]


def reference_context(syllabus, topic):
    refs = select_references(syllabus, topic)
    return '\n'.join(f"[{r['id']}] {r['title']} — {r['scope']}" for r in refs) or 'Use the syllabus-supplied references; no matching curated source is available.'


def reference_section(syllabus, topic):
    refs = select_references(syllabus, topic)
    lines = ['### References', '']
    lines += [f"- [{r['id']}] [{r['title']}]({r['url']}) — {r['scope']}" for r in refs]
    if not refs:
        lines.append('Use and verify the references supplied in the syllabus for this topic.')
    lines += ['', f'Official/publisher source locations checked {CHECKED}. Check the relevant text and current revision before teaching; generated claims and answers are not independently verified.']
    return '\n'.join(lines)
