import os
import sys
import ctypes
from ctypes import wintypes
import logging

from pydll_injector.native import (
    STARTUPINFOA, PROCESS_INFORMATION, kernel32
)
from pydll_injector.constants import (
    CREATE_SUSPENDED, ENV_VAR_SEPARATOR, STILL_ACTIVE
)
from pydll_injector.utils import absolute_path
from pydll_injector.injectors import (
    inject_standard, inject_apc, inject_nt, inject_hook
)
from pydll_injector.models import Launcher, Environment, Context

logger = logging.getLogger(__name__)


def spawn_process(launcher: Launcher, env: Environment) -> Context:
    """Spawn a process and inject DLLs into it."""
    if sys.platform != "win32":
        raise RuntimeError("PyDll-Injector only works on Windows.")

    cwd = launcher.current_dir or os.getcwd()
    cwd = os.path.normpath(cwd)
    exe_path = absolute_path(cwd, launcher.executable_file)
    if not os.path.isfile(exe_path):
        raise FileNotFoundError(f"{exe_path} not found")

    dll_paths: list[str] = []
    for dll in launcher.dll_list:
        p = absolute_path(cwd, dll)
        if not os.path.isfile(p):
            raise FileNotFoundError(f"{p} not found")
        dll_paths.append(p)

    # build environment block if needed...
    env_buffer = None
    if env.vars is not None:
        sys_vars = os.environ.copy() if env.use_system_env else {}
        for var in env.vars:
            k, v = var.split("=", 1)
            if k in sys_vars and env.environment_append:
                v = f"{v}{ENV_VAR_SEPARATOR}{sys_vars[k]}"
            sys_vars[k] = v
        block = "".join(f"{k}={v}\x00" for k, v in sys_vars.items()) + "\x00"
        buf = block.encode('mbcs')
        env_buffer = ctypes.create_string_buffer(buf)

    si = STARTUPINFOA()
    si.cb = ctypes.sizeof(si)
    pi = PROCESS_INFORMATION()

    cmd_buffer = None
    if launcher.cmd_line_args:
        cmd_buffer = ctypes.create_string_buffer(
            launcher.cmd_line_args.encode('mbcs')
        )

    success = kernel32.CreateProcessA(
        exe_path.encode('mbcs'),
        cmd_buffer,
        None, None,
        False,
        CREATE_SUSPENDED,
        ctypes.cast(env_buffer, ctypes.c_void_p) if env_buffer else None,
        cwd.encode('mbcs'),
        ctypes.byref(si),
        ctypes.byref(pi)
    )
    if not success:
        raise ctypes.WinError(ctypes.get_last_error())

    logger.debug(f"Started process {pi.dwProcessId} suspended")

    for dll in dll_paths:
        try:
            m = launcher.injection_method.lower()
            if m == 'standard':
                inject_standard(pi.hProcess, dll)
            elif m == 'apc':
                inject_apc(pi.hProcess, pi.hThread, dll)
            elif m == 'nt':
                inject_nt(pi.hProcess, dll)
            elif m == 'hook':
                inject_hook(pi, dll)
            else:
                raise ValueError(f"Unknown injection method: {launcher.injection_method}")
            logger.debug(f"Injected {dll} via {m}")
        except Exception as e:
            logger.error(f"Failed to inject {dll}: {e}")
            kernel32.TerminateThread(pi.hThread, 0)
            kernel32.TerminateProcess(pi.hProcess, 0)
            kernel32.CloseHandle(pi.hThread)
            kernel32.CloseHandle(pi.hProcess)
            raise RuntimeError(f"DllInjection error: {dll}\n{e}")

    # resume main thread
    kernel32.ResumeThread(pi.hThread)
    logger.debug("All DLLs injected; process resumed")
    return Context(proc_info=pi, _env_buffer=env_buffer)

def is_process_running(ctx: Context) -> bool:
    """Check if the process is still running."""
    code = wintypes.DWORD()
    ok = kernel32.GetExitCodeProcess(
        ctx.proc_info.hProcess, ctypes.byref(code)
    )
    if not ok:
        logger.error(f"GetExitCodeProcess failed: {ctypes.get_last_error()}")
        return True
    if code.value == STILL_ACTIVE:
        return True
    kernel32.CloseHandle(ctx.proc_info.hThread)
    kernel32.CloseHandle(ctx.proc_info.hProcess)
    return False

def terminate_process(ctx: Context) -> None:
    """Terminate the process and clean up handles."""
    if is_process_running(ctx):
        logger.debug("Terminating process...")
        if not kernel32.TerminateProcess(ctx.proc_info.hProcess, 1):
            raise ctypes.WinError(ctypes.get_last_error())
    else:
        logger.debug("Process already exited.")

    kernel32.CloseHandle(ctx.proc_info.hThread)
    kernel32.CloseHandle(ctx.proc_info.hProcess)

    logger.debug("Handles closed, process terminated.")
