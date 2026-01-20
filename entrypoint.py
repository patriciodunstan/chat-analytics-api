#!/usr/bin/env python3
"""Entrypoint script for Railway deployment."""
import os
import sys
import subprocess

# Get PORT from environment, default to 8000
port = os.environ.get("PORT", "8000")

# Ensure port is valid
try:
    port_int = int(port)
    if not (1 <= port_int <= 65535):
        raise ValueError("Port must be between 1 and 65535")
except ValueError as e:
    print(f"Error: Invalid PORT value '{port}': {e}", file=sys.stderr)
    sys.exit(1)

# Build uvicorn command
cmd = [
    "uvicorn",
    "app.main:app",
    "--host", "0.0.0.0",
    "--port", str(port_int)
]

print(f"Starting server on port {port_int}...", flush=True)

# Execute uvicorn
try:
    subprocess.run(cmd, check=True)
except subprocess.CalledProcessError as e:
    print(f"Error: Uvicorn exited with code {e.returncode}", file=sys.stderr)
    sys.exit(e.returncode)
except KeyboardInterrupt:
    print("\nShutting down...", flush=True)
    sys.exit(0)
