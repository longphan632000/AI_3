"""Install a pinned, checksum-verified CPU model inside this project (Windows x64)."""

import hashlib
import json
from pathlib import Path
import platform
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / 'runtime' / 'local_ai'
MODEL_NAME = 'Qwen3-1.7B-Q8_0.gguf'
MODEL = ROOT / 'local_models' / MODEL_NAME
RUNTIME_URL = ('https://github.com/ggml-org/llama.cpp/releases/download/b11935/'
               'llama-b11935-bin-win-cpu-x64.zip')
RUNTIME_SHA = 'd13e3d617a724eef10a533b18d1178b5292f7f1395965adf4e83b1ab4e9fc4b6'
MODEL_REVISION = '90862c4b9d2787eaed51d12237eafdfe7c5f6077'
MODEL_URL = f'https://huggingface.co/Qwen/Qwen3-1.7B-GGUF/resolve/{MODEL_REVISION}/{MODEL_NAME}'
MODEL_SHA = '061b54daade076b5d3362dac252678d17da8c68f07560be70818cace6590cb1a'


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(4 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def download(url, destination, expected_sha):
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and sha256(destination) == expected_sha:
        print(f'Already verified: {destination.name}', flush=True)
        return
    partial = destination.with_suffix(destination.suffix + '.part')
    request = urllib.request.Request(url, headers={'User-Agent': 'ProjectLocalBrain/1.0'})
    with urllib.request.urlopen(request, timeout=60) as response, partial.open('wb') as output:
        count = 0
        next_report = 64 * 1024 * 1024
        total = response.headers.get('Content-Length', 'unknown')
        print(f'Downloading {destination.name}; bytes={total}', flush=True)
        while block := response.read(4 * 1024 * 1024):
            output.write(block)
            count += len(block)
            if count >= next_report:
                print(f'{destination.name}: {count // (1024 * 1024)} MiB', flush=True)
                next_report += 64 * 1024 * 1024
    if sha256(partial) != expected_sha:
        partial.unlink(missing_ok=True)
        raise RuntimeError(f'Checksum mismatch: {destination.name}; installation stopped.')
    partial.replace(destination)


def main():
    if platform.system() != 'Windows' or platform.machine().lower() not in ('amd64', 'x86_64'):
        raise SystemExit('This installer provides Windows x64 CPU binaries only.')
    RUNTIME.mkdir(parents=True, exist_ok=True)
    archive_path = RUNTIME / 'runtime.zip'
    download(RUNTIME_URL, archive_path, RUNTIME_SHA)
    with zipfile.ZipFile(archive_path) as archive:
        for item in archive.infolist():
            target = (RUNTIME / item.filename).resolve()
            if not target.is_relative_to(RUNTIME.resolve()):
                raise RuntimeError('Unsafe archive path.')
        archive.extractall(RUNTIME)
    download(MODEL_URL, MODEL, MODEL_SHA)
    (RUNTIME / 'installation.json').write_text(json.dumps({
        'runtime_version': 'b11935', 'runtime_url': RUNTIME_URL, 'runtime_sha256': RUNTIME_SHA,
        'model_repository': 'Qwen/Qwen3-1.7B-GGUF', 'model_revision': MODEL_REVISION,
        'model_file': MODEL_NAME, 'model_sha256': MODEL_SHA,
        'model_license': 'Apache-2.0', 'runtime_license': 'MIT',
    }, indent=2), encoding='utf-8')
    print('Local model installed. The application starts it on the first API fallback.', flush=True)


if __name__ == '__main__':
    main()
