"""Vercel serverless entrypoint: exposes the FastAPI app as the handler."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app import app  # noqa: E402  (uvicorn-style `app` object = Vercel handler)

# Vercel cold-start note: RAG loads the bundled 10k sample (~1s). Writes go to
# /tmp (ephemeral) — see backend/app.py IS_VERCEL handling.
