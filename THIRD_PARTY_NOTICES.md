# Third-party components

The application source is licensed under AGPL-3.0-only. Dependencies are installed
separately and retain their own licenses:

| Component | License | Use |
| --- | --- | --- |
| Pillow | HPND (see its bundled notices) | Uploaded image validation |
| PyMuPDF / MuPDF | AGPL-3.0 or Artifex commercial license | PDF extraction and rendering |
| Playwright | Apache-2.0 | Optional development/browser tests |
| Codex CLI | Its upstream license and applicable service terms | Separately installed App Server |

This repository does not supply a Codex subscription, API key or model quota.
Users configure their own Codex installation and authentication.

The OpenAI logo and the OpenAI and Codex names belong to their respective owners
and are not covered by this project's AGPL license. They identify the compatible
upstream product; this project is independent and is not affiliated with,
endorsed by, or an official OpenAI client.

See each dependency's distribution for its complete license text. AGPL network
source obligations apply to modified versions offered under that license;
provide users access to the corresponding source.
