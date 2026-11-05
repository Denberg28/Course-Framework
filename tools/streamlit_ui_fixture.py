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
from test_workflow import antigravity_response, response


agent_rejected = False


def simulated_request(url, headers, payload, *, timeout=60):
    global agent_rejected
    # No credential, URL or prompt is logged or sent anywhere.
    if not url.startswith('https://generativelanguage.googleapis.com/'):
        raise engines.CourseError('The UI fixture supports simulated Gemini requests only.')
    if url == engines.INTERACTIONS_URL:
        if timeout != 300 or payload.get('agent') != engines.ANTIGRAVITY_AGENT or payload.get('agent_config') != {
                'type': 'antigravity', 'model': engines.DEFAULT_GEMINI_MODEL, 'max_total_tokens': 50000}:
            raise engines.CourseError('The Antigravity request did not use its managed agent settings.')
        if not agent_rejected:
            agent_rejected = True
            raise engines.ProviderUnavailable('Simulated HTTP 503')
        time.sleep(1.2)
        return antigravity_response()
    time.sleep(1.2)
    if 'drone 101' in payload['contents'][0]['parts'][0]['text']:
        return response('### Discussion\nIdentify drone components using a supplied diagram.\n\n### Activity\nLabel the diagram and explain each connection.')
    return response()


engines.FLASH_RETRY_DELAYS = (.9, 1.5)
engines.request_json = simulated_request
hosted_keys.gemini_secret = lambda secrets: 'fake-ui-deployment-key'
runpy.run_path(str(ROOT / 'app.py'), run_name='__main__')
