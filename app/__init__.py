"""App package initialization.

Exposes backward-compatible symbols for Flask app.py imports as well as FastAPI components.
"""

import os
import sys
import importlib.util

# Forward declarations so linters and static analysis tools recognize them
app = None
demands = None
alerts = None
donors = None
scheduled_donors = None
audit_logs = None
raw_hotspots = None

# Dynamically bind symbols from root app.py if present
_app_py_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app.py"))
if os.path.exists(_app_py_path):
    _spec = importlib.util.spec_from_file_location("root_app", _app_py_path)
    if _spec and _spec.loader:
        _root_app = importlib.util.module_from_spec(_spec)
        # Register in sys.modules so recursive imports inside app.py resolve cleanly
        sys.modules["root_app"] = _root_app
        _spec.loader.exec_module(_root_app)
        app = getattr(_root_app, "app", None)
        demands = getattr(_root_app, "demands", None)
        alerts = getattr(_root_app, "alerts", None)
        donors = getattr(_root_app, "donors", None)
        scheduled_donors = getattr(_root_app, "scheduled_donors", None)
        audit_logs = getattr(_root_app, "audit_logs", None)
        raw_hotspots = getattr(_root_app, "raw_hotspots", None)
