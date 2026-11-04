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
from test_workflow import background_response, response


def simulated_request(url, headers, payload, *, timeout=60, method=None):
    # No credential, URL or prompt is logged or sent anywhere.
    if not url.startswith('https://generativelanguage.googleapis.com/'):
        raise engines.CourseError('The UI fixture supports simulated Gemini requests only.')
    if url == engines.INTERACTIONS_URL:
        if timeout != 45 or payload.get('generation_config') != {
                'max_output_tokens': 32768, 'thinking_level': 'medium'} or not payload.get('background') or payload.get('store') is not True:
            raise engines.CourseError('The 3.8 Flash request did not use its background reasoning settings.')
        return {'id': 'int_test', 'status': 'in_progress'}
    if url == f'{engines.INTERACTIONS_URL}/int_test' and payload is None:
        if method == 'DELETE':
            return {}
        time.sleep(.9)
        return background_response()
    time.sleep(1.2)
    if 'drone 101' in payload['contents'][0]['parts'][0]['text']:
        return response('### Discussion\nIdentify drone components using a supplied diagram.\n\n### Activity\nLabel the diagram and explain each connection.')
    return response()


engines.FLASH_POLL_INTERVAL = .35
engines.request_json = simulated_request
hosted_keys.gemini_secret = lambda secrets: 'fake-ui-deployment-key'
runpy.run_path(str(ROOT / 'app.py'), run_name='__main__')
