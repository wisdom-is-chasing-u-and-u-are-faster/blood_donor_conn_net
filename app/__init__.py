"""App package initialization.

Exposes backward-compatible symbols for Flask app.py imports as well as FastAPI components.
"""

from typing import Any

# Expose Flask globals dynamically if app.py is loaded in sys.modules or from local module
try:
    import sys
    # If app.py at root is loaded, make symbols available here
    import importlib.util
    import os
    app_py_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app.py"))
    if os.path.exists(app_py_path):
        spec = importlib.util.spec_from_file_location("root_app", app_py_path)
        if spec and spec.loader:
            root_app = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(root_app)
            app = getattr(root_app, "app", None)
            demands = getattr(root_app, "demands", None)
            alerts = getattr(root_app, "alerts", None)
            donors = getattr(root_app, "donors", None)
            scheduled_donors = getattr(root_app, "scheduled_donors", None)
            audit_logs = getattr(root_app, "audit_logs", None)
            raw_hotspots = getattr(root_app, "raw_hotspots", None)
except Exception:
    pass
