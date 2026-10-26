# Tests paketi
import sys

for _akis in (sys.stdout, sys.stderr):
    if hasattr(_akis, "reconfigure"):
        try:
            _akis.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
