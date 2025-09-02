import os
import sys
import tempfile
import atexit
import shutil
from pathlib import Path


# Ensure project root is importable as module base
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Default to sync indexing in test runs unless explicitly disabled
# In tests with mocked Queue we still want async code path (202),
# but ensure the index exists eagerly as well.
os.environ.setdefault("INDEX_EAGER", "1")
os.environ.setdefault("EMBED_BACKEND", "hash")

# Isolate data dir per test session to avoid cross-run contamination
_DATA_ROOT = Path(tempfile.mkdtemp(prefix="docrag_data_"))
os.environ["DOC_RAG_DATA_DIR"] = str(_DATA_ROOT)
(_DATA_ROOT / "faiss").mkdir(parents=True, exist_ok=True)
(_DATA_ROOT / "uploads").mkdir(parents=True, exist_ok=True)

def _cleanup():
    shutil.rmtree(_DATA_ROOT, ignore_errors=True)

atexit.register(_cleanup)
