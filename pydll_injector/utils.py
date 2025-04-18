import os

def absolute_path(cwd: str, path: str) -> str:
    """Convert a relative path to an absolute path."""
    if os.path.isabs(path):
        return os.path.normpath(path)
    return os.path.normpath(os.path.join(cwd, path))
