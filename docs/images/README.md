# Screenshot sources

The screenshots are generated from this repository's actual HTML/CSS/JavaScript,
using only fictional fixtures in `scripts/capture_screenshots.py`.
The capture server serves static assets and demo API responses on loopback. It
does not import the application backend, launch Codex, read configuration,
connect to model providers, or load real accounts/conversations. Browser requests
to other origins are blocked. PNGs are re-encoded without metadata.

To regenerate from the repository root in a development environment:

```sh
python3 -m pip install playwright Pillow
python3 -m playwright install chromium
python3 scripts/capture_screenshots.py
```

Install a Chinese font such as `fonts-noto-cjk` on Linux. Set `CHROMIUM_PATH`
if using an existing Chromium binary. These dependencies are only for screenshot
generation; the website does not require them. Inspect all images before publishing.
