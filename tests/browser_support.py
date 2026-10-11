"""Use a caller-supplied Chromium or Playwright's managed browser installation."""
import os
from pathlib import Path

(Path(__file__).resolve().parents[1] / 'artifacts').mkdir(exist_ok=True)


def chromium_path():
    return os.environ.get('CHROMIUM_PATH') or None
