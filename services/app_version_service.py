"""An opaque content version lets connected clients detect a changed build."""
import hashlib
from pathlib import Path
import threading

ROOT = Path(__file__).resolve().parents[1]
_lock = threading.Lock()
_signature = None
_version = None


def get_app_version():
    global _signature, _version
    files = [ROOT / 'app.py', ROOT / 'requirements.txt', ROOT / 'static/sw.js']
    for folder, pattern in (('routes', '*.py'), ('services', '*.py'), ('templates', '*.html'),
                            ('database', '*.py'), ('static/js', '*.js'), ('static/css', '*.css')):
        files.extend(sorted((ROOT / folder).glob(pattern)))
    signature = tuple((str(p.relative_to(ROOT)), p.stat().st_mtime_ns, p.stat().st_size) for p in files)
    with _lock:
        if signature != _signature:
            digest = hashlib.sha256()
            for file in files:
                digest.update(str(file.relative_to(ROOT)).encode('utf-8'))
                digest.update(b'\0')
                digest.update(file.read_bytes())
            _version = digest.hexdigest()[:20]
            _signature = signature
        return _version
