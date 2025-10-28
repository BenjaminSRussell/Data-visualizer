import os
import sys
import time
import threading

LOG_PATH = os.environ.get("PY_IMPORT_LOG", os.path.join(os.getcwd(), ".forensics", "python_imports.log"))
ROOT = os.environ.get("PY_IMPORT_ROOT", os.getcwd())
_lock = threading.Lock()

def _record(line: str) -> None:
    try:
        with _lock:
            with open(LOG_PATH, "a", encoding="utf-8") as fh:
                fh.write(line)
    except Exception:
        pass

def _normalize(path: str) -> str:
    try:
        return os.path.realpath(path)
    except OSError:
        return path

def _should_log(path: str) -> bool:
    if not path:
        return False
    if not isinstance(path, str):
        return False
    path = _normalize(path)
    if not path.startswith(ROOT):
        return False
    return True

def _audit(event, args):
    if event != "import":
        return
    if not args:
        return
    name = args[0]
    filename = None
    if len(args) > 1:
        filename = args[1] or None
    if len(args) > 2 and not filename:
        filename = args[2] if isinstance(args[2], str) else None
    if not filename:
        return
    if not _should_log(filename):
        return
    ts = f"{time.time():.6f}"
    line = f"{ts}\t{name}\t{_normalize(filename)}\n"
    _record(line)

try:
    sys.addaudithook(_audit)
except Exception:
    pass
