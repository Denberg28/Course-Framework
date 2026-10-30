"""CI-only UI entry point: actual app with a delayed, no-network API fixture.

Production deployments must continue to use app.py.
"""
from pathlib import Path
import runpy
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]

import engines
import hosted_keys
from test_workflow import response


def simulated_request(url, headers, payload, *, timeout=60):
    # No credential, URL or prompt is logged or sent anywhere.
    if not url.startswith('https://generativelanguage.googleapis.com/'):
        raise engines.CourseError('The UI fixture supports simulated Gemini requests only.')
    if '/gemini-3.8-flash:generateContent' in url:
        if timeout != 180 or payload.get('generationConfig') != {
                'maxOutputTokens': 32768, 'thinkingConfig': {'thinkingLevel': 'medium'}}:
            raise engines.CourseError('The 3.8 Flash request did not use its reasoning settings.')
    time.sleep(1.2)
    return response()


engines.request_json = simulated_request
hosted_keys.gemini_secret = lambda secrets: 'fake-ui-deployment-key'
runpy.run_path(str(ROOT / 'app.py'), run_name='__main__')
