# Contributing

Use Python 3.9+ (3.11/3.12 recommended), a virtual environment and Linux.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m playwright install chromium
.venv/bin/python tests/browser_workspace.py
```

Browser tests use Playwright's installed Chromium unless `CHROMIUM_PATH` is set.
API and simulated browser tests do not require Codex credentials. Tests named
`smoke_*.py` call a real configured model and must be run explicitly.

Describe the trigger, resulting behavior and relevant checks in pull requests.
Never include account databases, uploaded files, model credentials, private logs
or screenshots of real conversations. Run
`python scripts/check_release.py --staged` before committing.

Contributions are provided under AGPL-3.0-only. Report vulnerabilities privately
using GitHub security advisories once enabled by the repository maintainer;
do not post credentials or exploit details in a public issue.
