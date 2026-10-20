"""
Top-level entrypoint alias to allow both:
  uvicorn main:app --reload
and:
  uvicorn app.main:app --reload
"""
from app.main import app

__all__ = ["app"]
