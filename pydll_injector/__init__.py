"""Python DLL injector for Windows."""
from .process import spawn_process, is_process_running, terminate_process
from .models import Environment, Launcher, Context

__version__ = "0.1.1"

__all__ = [
    "spawn_process",
    "is_process_running",
    "terminate_process",
    "Environment",
    "Launcher",
    "Context",
]
