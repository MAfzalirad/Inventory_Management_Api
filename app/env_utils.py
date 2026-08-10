"""
Shared environment-variable accessor.

This lives in its own module (rather than inline in database.py) to break
a circular import: database.py needs env vars at import time, and
dependencies.py imports from database.py while also needing env vars of
its own. Centralizing get_required_env() here lets both import it
independently without importing each other.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def get_required_env(name):
    """Fetch an environment variable, failing loudly if it's missing.

    Raises ValueError instead of silently returning None, so misconfigured
    deployments fail fast at startup rather than surfacing as a confusing
    error deep in request handling.
    """
    require_env = os.getenv(name)
    if require_env is None:
        raise ValueError(f"Environment variable '{name}' is required but not set.")
    return require_env