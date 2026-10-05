"""Check tracked or staged files without printing suspected secret values."""
import argparse
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
PATTERNS = {
    'private key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'provider token': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|AIza[A-Za-z0-9_-]{30,}|sk-[A-Za-z0-9_-]{24,})\b'),
    'database credentials': re.compile(r'(?:postgres(?:ql)?|mysql)://[^\s/:]+:[^\s/@]+@'),
    'literal credential': re.compile(r'''(?i)\b(?:secret_key|api_secret|api_key|client_secret|email_host_password|password|postgres_password)\b['"]?\s*[:=]\s*['"]([^'"\n]+)['"]'''),
    'literal password call': re.compile(r'''\.set_password\(\s*['"]([^'"\n]+)['"]'''),
    'secret default': re.compile(r'''config\(['"](?:SECRET_KEY|EMAIL_HOST_PASSWORD|ESEWA_SECRET_KEY|CLOUDINARY_API_SECRET)['"],\s*default=['"]([^'"\n]+)['"]'''),
}
FORBIDDEN_PARTS = {'media', 'staticfiles', 'node_modules', '.venv', '.test-deps', '.verification-static'}


def git(*args):
    return subprocess.check_output(
        ['git', '-c', f'safe.directory={ROOT.as_posix()}', *args], cwd=ROOT,
        stderr=subprocess.DEVNULL,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--staged', action='store_true', help='Inspect the complete Git index, not working-tree bytes.')
    args = parser.parse_args()
    findings = []
    paths = git('ls-files', '-z').decode().split('\0')
    checked = 0
    for name in filter(None, paths):
        path = Path(name)
        if any(part in FORBIDDEN_PARTS for part in path.parts) or (path.name.startswith('.env') and not path.name.endswith('.example')):
            findings.append((name, 0, 'private/generated file is tracked'))
            continue
        if path.name.endswith('.example'):
            continue
        data = git('show', f':{name}') if args.staged else (ROOT / path).read_bytes()
        if b'\0' in data[:8192]:
            continue
        checked += 1
        for lineno, line in enumerate(data.decode('utf-8', errors='replace').splitlines(), 1):
            for label, pattern in PATTERNS.items():
                match = pattern.search(line)
                if not match:
                    continue
                if match.lastindex and match.group(1).lower().startswith(('test', 'fake', 'your-', 'placeholder')):
                    continue
                if match.lastindex and path.name == 'tests.py' and match.group(1) == 'password123':
                    continue  # Existing isolated admin-access test fixture.
                findings.append((name, lineno, label))
    for name, line, label in findings:
        print(f'{name}:{line}: {label} (value withheld)')
    print(f'Checked {checked} text files; {len(findings)} finding(s).')
    return 1 if findings else 0


if __name__ == '__main__':
    sys.exit(main())
