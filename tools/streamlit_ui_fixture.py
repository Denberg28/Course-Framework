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


flash_rejected = False


def simulated_request(url, headers, payload, *, timeout=60):
    global flash_rejected
    # No credential, URL or prompt is logged or sent anywhere.
    if not url.startswith('https://generativelanguage.googleapis.com/'):
        raise engines.CourseError('The UI fixture supports simulated Gemini requests only.')
    if url.endswith('/gemini-3.8-flash:generateContent'):
        if timeout != 300 or payload.get('generationConfig') != {
                'maxOutputTokens': 32768, 'thinkingConfig': {'thinkingLevel': 'high'}}:
            raise engines.CourseError('The 3.8 Flash request did not use high reasoning.')
        if not flash_rejected:
            flash_rejected = True
            raise engines.ProviderUnavailable('Simulated HTTP 503')
    time.sleep(1.2)
    if 'drone 101' in payload['contents'][0]['parts'][0]['text']:
        return response('### Discussion\nIdentify drone components using a supplied diagram.\n\n### Activity\nLabel the diagram and explain each connection.')
    return response()


engines.FLASH_RETRY_DELAYS = (.9, 1.5)
engines.request_json = simulated_request
hosted_keys.gemini_secret = lambda secrets: 'fake-ui-deployment-key'
runpy.run_path(str(ROOT / 'app.py'), run_name='__main__')
