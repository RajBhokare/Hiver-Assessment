"""One-command entrypoint to launch the Hiver Agent Web UI.

Usage:
    python app.py
"""
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from hiver_agent.server import start_server

if __name__ == "__main__":
    start_server(5000)
