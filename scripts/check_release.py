#!/usr/bin/env python3
"""Check Git-index files for private data and common credential patterns."""
import argparse
from pathlib import PurePosixPath
import re
import subprocess
import sys

BLOCKED_DIRS = {'data', 'artifacts', '.codex', '.ssh', '.venv', 'venv', '__pycache__', 'backups', 'workspace'}
SECRET_PATTERNS = [
    re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
    re.compile(rb'\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}\b'),
    re.compile(rb'\bgh[pousr]_[A-Za-z0-9]{30,}\b'),
    re.compile(rb'\bgithub_pat_[A-Za-z0-9_]{30,}\b'),
    re.compile(rb'\bAKIA[A-Z0-9]{16}\b'),
]


def check_entry(name, data, mode='100644'):
    path = PurePosixPath(name)
    reasons = []
    if any(part in BLOCKED_DIRS for part in path.parts):
        reasons.append('private/runtime directory')
    if ((path.name.startswith('.env') and path.name not in {'.env.example', '.env.docker.example'})
            or path.name in {'auth.json', 'credentials.json'}
            or re.search(r'\.(sqlite3?|db)(?:-.*)?$|\.(pem|key|p12|pfx|log|pyc)$', path.name)):
        reasons.append('private/runtime file')
    if mode == '120000':
        reasons.append('symlink must be reviewed explicitly')
    if len(data) > 3 * 1024 * 1024:
        reasons.append('unexpected large file')
    if any(pattern.search(data) for pattern in SECRET_PATTERNS):
        reasons.append('credential pattern')
    if re.search(rb'/root/[a-zA-Z0-9_.-]+', data):
        reasons.append('private deployment reference')
    return reasons


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--staged', action='store_true', help='Scan the complete Git index (also used in CI)')
    parser.parse_args()
    result = subprocess.run(['git', 'ls-files', '--stage', '-z'], capture_output=True, check=True)
    count = 0
    failures = []
    for entry in result.stdout.split(b'\0'):
        if not entry:
            continue
        metadata, raw_name = entry.split(b'\t', 1)
        mode, oid, stage = metadata.split()
        name = raw_name.decode('utf-8')
        if stage != b'0':
            failures.append((name, ['unresolved merge']))
            continue
        data = subprocess.run(['git', 'cat-file', 'blob', oid.decode()], capture_output=True, check=True).stdout
        reasons = check_entry(name, data, mode.decode())
        count += 1
        if reasons:
            failures.append((name, reasons))
    if not count:
        parser.exit(1, 'No indexed files; initialize Git and stage release sources first.\n')
    for name, reasons in failures:
        # Never print matched secrets.
        print(name + ': ' + ', '.join(reasons), file=sys.stderr)
    if failures:
        parser.exit(1, 'Release check failed.\n')
    print('Release check passed: %d indexed files; no blocked data or known credential patterns.' % count)


if __name__ == '__main__':
    main()
