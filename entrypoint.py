import os
import sys

# Use the PORT environment variable provided by the hosting platform.
# Lonch.cloud (and most cloud platforms) inject this to tell the app which port to listen on.
port = os.environ.get("PORT", "3000")

cmd = [
    "gunicorn",
    "-b", f"0.0.0.0:{port}",
    "--workers", "1",
    "--threads", "4",
    "--timeout", "120",
    "--access-logfile", "-",
    "--error-logfile", "-",
    "app:app"
]

print(f"[STARTUP] Launching Gunicorn on port {port}", flush=True)
sys.stdout.flush()
sys.stderr.flush()

try:
    os.execvp("gunicorn", cmd)
except Exception as e:
    print(f"[STARTUP ERROR] Failed to exec gunicorn: {e}", file=sys.stderr, flush=True)
    # Fallback to Flask dev server if gunicorn fails
    from app import app
    app.run(host="0.0.0.0", port=int(port), debug=False)
