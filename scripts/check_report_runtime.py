"""Local-only runtime check shared by daily and weekly reports."""
import importlib.metadata
import json
import sys
import time
from pathlib import Path


def main():
    started = time.monotonic()
    expected = Path(r"C:\Users\eqy\.codex\report-sync\.venv\Scripts\python.exe")
    result = {"python": sys.executable, "expected_python": str(expected)}
    try:
        if Path(sys.executable).resolve() != expected.resolve():
            raise RuntimeError("Use the shared report-sync .venv interpreter")
        from playwright.sync_api import sync_playwright

        result["playwright"] = importlib.metadata.version("playwright")
        with sync_playwright() as playwright:
            result["chromium"] = playwright.chromium.executable_path
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.set_content("<title>report-runtime-ok</title>")
                if page.title() != "report-runtime-ok":
                    raise RuntimeError("Browser smoke check failed")
                result["browser_version"] = browser.version
            finally:
                browser.close()
        result["status"] = "ok"
    except Exception as exc:
        result.update(status="failed", error=str(exc))
    result["elapsed_seconds"] = round(time.monotonic() - started, 3)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
