"""Create a reproducible, explicit allowlist of Azure Functions source files."""
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    destination = ROOT / 'build' / 'function'
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    names = ['function_app.py', 'host.json', 'requirements.txt', 'LICENSE', 'NOTICE', *[str(p.relative_to(ROOT)) for p in sorted((ROOT / 'app').glob('*.py'))]]
    hashes = {}
    archive = ROOT / 'build' / 'function.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as output:
        for name in sorted(names):
            data = (ROOT / name).read_bytes()
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            hashes[name] = hashlib.sha256(data).hexdigest()
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            output.writestr(info, data)
    (ROOT / 'build' / 'manifest.json').write_text(json.dumps({'files': hashes, 'zip_sha256': hashlib.sha256(archive.read_bytes()).hexdigest()}, indent=2) + '\n')
    print(f'Staged {len(names)} files for managed-identity Flex deployment with remote dependency build.')


if __name__ == '__main__':
    main()
