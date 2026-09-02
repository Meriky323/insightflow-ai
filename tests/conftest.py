import atexit
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_TEST_DATA = Path(tempfile.mkdtemp(prefix='insightflow-tests-'))
os.environ['DATA_DIR'] = str(_TEST_DATA)
os.environ['PUBLIC_DEPLOYMENT'] = '0'
os.environ['ALLOW_PUBLIC_LIVE_RESEARCH'] = '0'

@atexit.register
def _cleanup_test_data():
    shutil.rmtree(_TEST_DATA, ignore_errors=True)
