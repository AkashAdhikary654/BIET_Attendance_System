import os
import sys

# Collect all potential ports to listen on
env_port = os.environ.get("PORT")
candidate_ports = [env_port, "3000", "5000", "8080", "80"]
ports = []
for p in candidate_ports:
    if p and p not in ports:
        ports.append(str(p))

bind_args = []
for p in ports:
    bind_args.extend(["-b", f"0.0.0.0:{p}"])

cmd = [
    "gunicorn",
    *bind_args,
    "--workers", "1",
    "--threads", "4",
    "--timeout", "120",
    "--access-logfile", "-",
    "--error-logfile", "-",
    "app:app"
]

print(f"[STARTUP] Launching Gunicorn listening on ports: {', '.join(ports)}", flush=True)
sys.stdout.flush()
sys.stderr.flush()

try:
    os.execvp("gunicorn", cmd)
except Exception as e:
    print(f"[STARTUP ERROR] Failed to exec gunicorn: {e}", file=sys.stderr, flush=True)
    # Fallback to python app.py if gunicorn fails for any reason
    from app import app
    port = int(env_port) if env_port else 3000
    app.run(host="0.0.0.0", port=port, debug=False)
