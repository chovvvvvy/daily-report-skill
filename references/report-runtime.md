# Shared daily / weekly runtime

Use this fixed interpreter for both skills' Python generation, validation, and daily submission:

```text
C:\Users\eqy\.codex\report-sync\.venv\Scripts\python.exe
```

Do not use bare `python`, `py`, another project's venv, or an app-bundled Python. Node Playwright and browser cache alone do not provide the Python module.

Before delivery, run once per execution session:

```powershell
& 'C:\Users\eqy\.codex\report-sync\.venv\Scripts\python.exe' 'C:\Users\eqy\.codex\skills\daily-report\scripts\check_report_runtime.py'
```

This check launches a headless local page without Feishu login, network navigation, or submission. It prints interpreter, Playwright version, browser path/version, and elapsed time. On failure, report the exact failing layer. Do not repeatedly search unrelated environments or reinstall on every run. Interview and local fact review do not need browser preflight.

Rebuild only when needed and authorized, using the pinned dependencies:

```powershell
uv venv --python 'C:\Users\eqy\AppData\Roaming\uv\python\cpython-3.10.20-windows-x86_64-none\python.exe' 'C:\Users\eqy\.codex\report-sync\.venv'
uv pip sync --python 'C:\Users\eqy\.codex\report-sync\.venv\Scripts\python.exe' 'C:\Users\eqy\.codex\skills\daily-report\references\report-requirements.txt'
& 'C:\Users\eqy\.codex\report-sync\.venv\Scripts\python.exe' -m playwright install chromium
```

Weekly reports use this same environment; their existing delivery is Feishu archive sync, not the daily form. Keep successful archive manifests and submission logs as evidence; never overwrite them merely to probe the runtime.
