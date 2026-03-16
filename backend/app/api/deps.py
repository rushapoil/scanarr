"""Shared FastAPI dependencies."""
from app.core.security import get_current_user
from app.db.database import get_db

# Re-export so routes only need to import from here
__all__ = ["get_db", "get_current_user"]
