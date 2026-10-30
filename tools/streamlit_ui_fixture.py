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
from test_workflow import response


def simulated_request(url, headers, payload):
    # No credential, URL or prompt is logged or sent anywhere.
    if not url.startswith('https://generativelanguage.googleapis.com/'):
        raise engines.CourseError('The UI fixture supports simulated Gemini requests only.')
    time.sleep(1.2)
    return response()


engines.request_json = simulated_request
runpy.run_path(str(ROOT / 'app.py'), run_name='__main__')
