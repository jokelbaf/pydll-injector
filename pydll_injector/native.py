import ctypes
from ctypes import wintypes

# Load libraries
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
ntdll    = ctypes.WinDLL('ntdll',    use_last_error=True)
user32   = ctypes.WinDLL('user32',   use_last_error=True)

# Structures
class STARTUPINFOA(ctypes.Structure):
    _fields_ = [
        ('cb',             wintypes.DWORD),
        ('lpReserved',     wintypes.LPSTR),
        ('lpDesktop',      wintypes.LPSTR),
        ('lpTitle',        wintypes.LPSTR),
        ('dwX',            wintypes.DWORD),
        ('dwY',            wintypes.DWORD),
        ('dwXSize',        wintypes.DWORD),
        ('dwYSize',        wintypes.DWORD),
        ('dwXCountChars',  wintypes.DWORD),
        ('dwYCountChars',  wintypes.DWORD),
        ('dwFillAttribute',wintypes.DWORD),
        ('dwFlags',        wintypes.DWORD),
        ('wShowWindow',    wintypes.WORD),
        ('cbReserved2',    wintypes.WORD),
        ('lpReserved2',    ctypes.POINTER(ctypes.c_byte)),
        ('hStdInput',      wintypes.HANDLE),
        ('hStdOutput',     wintypes.HANDLE),
        ('hStdError',      wintypes.HANDLE),
    ]

class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [
        ('hProcess',    wintypes.HANDLE),
        ('hThread',     wintypes.HANDLE),
        ('dwProcessId', wintypes.DWORD),
        ('dwThreadId',  wintypes.DWORD),
    ]

# Function prototypes
# CreateProcessA
kernel32.CreateProcessA.argtypes = [
    wintypes.LPCSTR, wintypes.LPSTR,
    ctypes.c_void_p, ctypes.c_void_p,
    wintypes.BOOL, wintypes.DWORD,
    ctypes.c_void_p,
    wintypes.LPCSTR,
    ctypes.POINTER(STARTUPINFOA),
    ctypes.POINTER(PROCESS_INFORMATION)
]
kernel32.CreateProcessA.restype = wintypes.BOOL

# GetModuleHandleA, GetProcAddress, VirtualAllocEx, WriteProcessMemory, VirtualFreeEx, etc.
kernel32.GetModuleHandleA.argtypes = [wintypes.LPCSTR]
kernel32.GetModuleHandleA.restype  = wintypes.HMODULE
kernel32.GetProcAddress.argtypes  = [wintypes.HMODULE, wintypes.LPCSTR]
kernel32.GetProcAddress.restype   = wintypes.LPVOID
kernel32.VirtualAllocEx.argtypes  = [
    wintypes.HANDLE, wintypes.LPVOID, ctypes.c_size_t,
    wintypes.DWORD,  wintypes.DWORD
]
kernel32.VirtualAllocEx.restype   = wintypes.LPVOID
kernel32.WriteProcessMemory.argtypes = [
    wintypes.HANDLE, wintypes.LPVOID, ctypes.c_void_p,
    ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)
]
kernel32.WriteProcessMemory.restype = wintypes.BOOL
kernel32.VirtualFreeEx.argtypes   = [
    wintypes.HANDLE, wintypes.LPVOID, ctypes.c_size_t,
    wintypes.DWORD
]
kernel32.VirtualFreeEx.restype    = wintypes.BOOL

# CreateRemoteThread, WaitForSingleObject, ResumeThread, etc.
kernel32.CreateRemoteThread.argtypes = [
    wintypes.HANDLE, ctypes.c_void_p, ctypes.c_size_t,
    wintypes.LPVOID, wintypes.LPVOID, wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD)
]
kernel32.CreateRemoteThread.restype  = wintypes.HANDLE
kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
kernel32.WaitForSingleObject.restype  = wintypes.DWORD
kernel32.ResumeThread.argtypes        = [wintypes.HANDLE]
kernel32.ResumeThread.restype         = wintypes.DWORD
kernel32.TerminateProcess.argtypes    = [wintypes.HANDLE, wintypes.UINT]
kernel32.TerminateProcess.restype     = wintypes.BOOL
kernel32.CloseHandle.argtypes         = [wintypes.HANDLE]
kernel32.CloseHandle.restype          = wintypes.BOOL

# APC injection
kernel32.QueueUserAPC.argtypes = [wintypes.LPVOID, wintypes.HANDLE, wintypes.LPVOID]
kernel32.QueueUserAPC.restype  = wintypes.DWORD

# NtCreateThreadEx
ntdll.NtCreateThreadEx.argtypes = [
    ctypes.POINTER(wintypes.HANDLE), wintypes.ULONG, ctypes.c_void_p,
    wintypes.HANDLE, wintypes.LPVOID, wintypes.LPVOID,
    wintypes.BOOL, wintypes.ULONG, wintypes.ULONG,
    wintypes.ULONG, ctypes.c_void_p
]
ntdll.NtCreateThreadEx.restype = wintypes.ULONG

# Hook-based injection
user32.SetWindowsHookExA.argtypes   = [
    wintypes.INT, wintypes.LPVOID, wintypes.HINSTANCE, wintypes.DWORD
]
user32.SetWindowsHookExA.restype    = wintypes.HHOOK
user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
user32.UnhookWindowsHookEx.restype  = wintypes.BOOL
user32.PostThreadMessageA.argtypes  = [wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.PostThreadMessageA.restype   = wintypes.BOOL

# LoadLibrary, FreeLibrary, Sleep
kernel32.LoadLibraryA.argtypes = [wintypes.LPCSTR]
kernel32.LoadLibraryA.restype  = wintypes.HMODULE
kernel32.FreeLibrary.argtypes  = [wintypes.HMODULE]
kernel32.FreeLibrary.restype   = wintypes.BOOL
kernel32.Sleep.argtypes        = [wintypes.DWORD]
kernel32.Sleep.restype         = None
