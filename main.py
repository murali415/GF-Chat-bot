"""Vercel entrypoint (official layout): root-level module exporting `app`.

The Python runtime serves this for all routes — no rewrites needed.
Local dev is unchanged: `uvicorn app:app` from backend/.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

from app import app  # noqa: E402  (FastAPI `app` = Vercel handler)
