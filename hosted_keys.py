"""Read a deployment-owned Gemini credential without copying it into UI/session state."""
from course_core import CourseError


def gemini_secret(secrets):
    try:
        value = secrets.get('GEMINI_API_KEY', '')
    except (FileNotFoundError, KeyError):
        return ''
    if value is None or value == '':
        return ''
    if (not isinstance(value, str) or len(value) > 4096 or not value.isascii() or
            any(ord(c) < 32 for c in value)):
        raise CourseError('Check GEMINI_API_KEY in Streamlit Secrets: use a quoted API key string.')
    return value.strip()
