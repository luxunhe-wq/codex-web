# First GitHub publication

The local release preparation initializes a `main` branch and stages only source,
tests, public fixtures and deployment/documentation files. Private data, uploads,
real screenshots, logs, virtual environments and credentials remain ignored.

Before the initial commit:

```sh
git diff --cached --stat
git diff --cached --check
python3 scripts/check_release.py --staged
python3 -m unittest discover -s tests -v
```

Review the staged file list and licenses. The scanner catches known credential
patterns but cannot replace review. Do not force-add ignored files. Do not copy
your real `.codex` directory, account database or environment configuration into
the repository. AGPL-3.0-only is the chosen project license; dependencies retain
their own licenses.

Choose your own Git commit name/email, create an empty GitHub repository (without
an automatically generated README/license), and use its actual URL:

```sh
git config user.name "Your chosen name"
git config user.email "Your GitHub private noreply email"
git commit -m "Prepare Codex Web Community for Linux self-hosting"
git remote add origin https://github.com/YOUR_ACCOUNT/YOUR_REPOSITORY.git
git push -u origin main
```

Use GitHub SSH authentication or a credential manager for the push; never embed
a token in the remote URL or commit a token. A repository URL and authenticated
Git access are necessary to publish; no destination is assumed by the installer.

After publishing, enable private vulnerability reporting and review the GitHub
Actions results. The local verified CLI baseline is documented in README. CI
uses mocks and does not need production credentials or model calls. Linux/Python
matrix results become available when Actions runs on GitHub.

If sharing a source archive, generate it from the reviewed Git tree, not by
archiving the running server directory. This excludes ignored runtime files.
Keep the source archive under ignored `dist/`; do not include test output or
private deployment screenshots as release attachments.
