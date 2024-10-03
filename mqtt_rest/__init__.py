import os
import importlib.metadata
from pathlib import Path
import toml

PYPROJECT_TOML_FILE = Path(__file__).parent.parent / "pyproject.toml"
if PYPROJECT_TOML_FILE.exists():
    PYPROJECT_TOML = toml.load(PYPROJECT_TOML_FILE)
    __app_name__ = PYPROJECT_TOML["tool"]["poetry"]["name"]
    __version__ = PYPROJECT_TOML["tool"]["poetry"]["version"]
else:
    __app_name__ = __package__ or __name__
    __version__ = importlib.metadata.version(__app_name__)

DEV_ENV_FILE = Path(__file__).parent.parent / ".env.dev"
print(DEV_ENV_FILE)
if DEV_ENV_FILE.exists():
    with open(DEV_ENV_FILE) as f:
        for line in f:
            key, value = line.strip().split("=")
            os.environ[key] = value
