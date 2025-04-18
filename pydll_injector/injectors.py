import ctypes
import logging
from ctypes import wintypes

from pydll_injector.native import kernel32, ntdll, user32
from pydll_injector.constants import (
    MEM_COMMIT, MEM_RESERVE, PAGE_READWRITE,
    MEM_RELEASE, WH_CBT, WM_NULL, INFINITE,
)
from pydll_injector.models import PROCESS_INFORMATION

logger = logging.getLogger(__name__)


def inject_standard(h_process: wintypes.HANDLE, dll_path: str) -> None:
    """Classic CreateRemoteThread + LoadLibraryA."""
    h_k32 = kernel32.GetModuleHandleA(b"kernel32.dll")
    addr = kernel32.GetProcAddress(h_k32, b"LoadLibraryA")
    dll_bytes = dll_path.encode('mbcs') + b'\x00'
    size = len(dll_bytes)

    remote = kernel32.VirtualAllocEx(
        h_process,
        None,
        size,
        MEM_COMMIT | MEM_RESERVE,
        PAGE_READWRITE
    )
    if not remote:
        raise ctypes.WinError(ctypes.get_last_error())

    written = ctypes.c_size_t()
    if not kernel32.WriteProcessMemory(
        h_process,
        remote,
        dll_bytes, size,
        ctypes.byref(written)
    ):
        raise ctypes.WinError(ctypes.get_last_error())

    thread_id = wintypes.DWORD(0)
    h_thread = kernel32.CreateRemoteThread(
        h_process,None, 0, addr, remote, 0,
        ctypes.byref(thread_id)
    )
    if not h_thread:
        raise ctypes.WinError(ctypes.get_last_error())

    kernel32.WaitForSingleObject(h_thread, INFINITE)
    kernel32.VirtualFreeEx(h_process, remote, 0, MEM_RELEASE)
    kernel32.CloseHandle(h_thread)

def inject_apc(
    h_process: wintypes.HANDLE,
    h_thread: wintypes.HANDLE,
    dll_path: str
) -> None:
    """QueueUserAPC + LoadLibraryA. Target thread must enter an alertable state."""
    h_k32 = kernel32.GetModuleHandleA(b"kernel32.dll")
    addr = kernel32.GetProcAddress(h_k32, b"LoadLibraryA")
    dll_bytes = dll_path.encode('mbcs') + b'\x00'
    size = len(dll_bytes)

    remote = kernel32.VirtualAllocEx(
        h_process,
        None,
        size,
        MEM_COMMIT | MEM_RESERVE,
        PAGE_READWRITE
    )
    if not remote:
        raise ctypes.WinError(ctypes.get_last_error())

    written = ctypes.c_size_t()
    if not kernel32.WriteProcessMemory(
        h_process, remote,
        dll_bytes, size,
        ctypes.byref(written)
    ):
        raise ctypes.WinError(ctypes.get_last_error())

    if not kernel32.QueueUserAPC(addr, h_thread, remote):
        raise ctypes.WinError(ctypes.get_last_error())

    logger.debug("APC queued; resume the thread and wait for it to hit an alertable wait.")

def inject_nt(h_process: wintypes.HANDLE, dll_path: str) -> None:
    """NtCreateThreadEx + LoadLibraryA (stealthier than CreateRemoteThread)."""
    h_k32 = kernel32.GetModuleHandleA(b"kernel32.dll")
    addr = kernel32.GetProcAddress(h_k32, b"LoadLibraryA")
    dll_bytes = dll_path.encode('mbcs') + b'\x00'
    size = len(dll_bytes)

    remote = kernel32.VirtualAllocEx(
        h_process,
        None,
        size,
        MEM_COMMIT | MEM_RESERVE,
        PAGE_READWRITE
    )
    if not remote:
        raise ctypes.WinError(ctypes.get_last_error())

    written = ctypes.c_size_t()
    if not kernel32.WriteProcessMemory(
        h_process, remote,
        dll_bytes, size,
        ctypes.byref(written)
    ):
        raise ctypes.WinError(ctypes.get_last_error())

    thread_handle = wintypes.HANDLE()
    status = ntdll.NtCreateThreadEx(
        ctypes.byref(thread_handle),
        0x1FFFFF, None,
        h_process,
        addr, remote,
        False, 0, 0, 0, None
    )
    if status != 0:
        raise ctypes.WinError(ctypes.get_last_error())

    kernel32.WaitForSingleObject(thread_handle, INFINITE)
    kernel32.VirtualFreeEx(h_process, remote, 0, MEM_RELEASE)
    kernel32.CloseHandle(thread_handle)

def inject_hook(
    pi: PROCESS_INFORMATION,
    dll_path: str,
    hook_proc_name: bytes = b"HookProc"
) -> None:
    """SetWindowsHookExA(WH_CBT) injection. DLL must export `HookProc`."""
    # load into the process so SetWindowsHookEx can find it
    h_mod = kernel32.LoadLibraryA(dll_path.encode('mbcs'))
    if not h_mod:
        raise ctypes.WinError(ctypes.get_last_error())

    addr = kernel32.GetProcAddress(h_mod, hook_proc_name)
    if not addr:
        kernel32.FreeLibrary(h_mod)
        raise ctypes.WinError(ctypes.get_last_error())

    h_hook = user32.SetWindowsHookExA(
        WH_CBT, addr, h_mod, pi.dwThreadId
    )
    if not h_hook:
        kernel32.FreeLibrary(h_mod)
        raise ctypes.WinError(ctypes.get_last_error())

    # nudge the thread so the hook fires
    user32.PostThreadMessageA(pi.dwThreadId, WM_NULL, 0, 0)
    kernel32.Sleep(100)               # let the hook land
    user32.UnhookWindowsHookEx(h_hook)
    kernel32.FreeLibrary(h_mod)
