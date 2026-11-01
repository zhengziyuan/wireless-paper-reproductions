"""Read-only exact Windows identities for our own newly created processes."""
import ctypes
from ctypes import wintypes

def _kernel():
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
    k.GetProcessTimes.argtypes=[wintypes.HANDLE,*([ctypes.POINTER(wintypes.FILETIME)]*4)];k.GetProcessTimes.restype=wintypes.BOOL
    k.GetExitCodeProcess.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)];k.GetExitCodeProcess.restype=wintypes.BOOL
    k.CloseHandle.argtypes=[wintypes.HANDLE];k.CloseHandle.restype=wintypes.BOOL
    return k

def _from_handle(k,handle,pid):
    t=[wintypes.FILETIME() for _ in range(4)]
    if not k.GetProcessTimes(handle,*[ctypes.byref(x) for x in t]):raise ctypes.WinError(ctypes.get_last_error())
    return dict(PID=int(pid),creation_FILETIME=(t[0].dwHighDateTime<<32)|t[0].dwLowDateTime)

def identity(pid):
    k=_kernel();handle=k.OpenProcess(0x1000,False,pid)
    if not handle:raise ctypes.WinError(ctypes.get_last_error())
    try:return _from_handle(k,handle,pid)
    finally:k.CloseHandle(handle)

def identity_from_process(process):
    # Popen retains this exact OS process handle after wait. This avoids a
    # post-exit PID lookup accidentally observing a later unrelated process.
    k=_kernel();return _from_handle(k,wintypes.HANDLE(int(process._handle)),process.pid)

def exited_process_observation(process):
    k=_kernel();handle=wintypes.HANDLE(int(process._handle));out=_from_handle(k,handle,process.pid);code=wintypes.DWORD()
    if not k.GetExitCodeProcess(handle,ctypes.byref(code)):raise ctypes.WinError(ctypes.get_last_error())
    out['actual_OS_exit_code']=int(code.value)
    out['exact_original_Popen_handle_used']=True
    return out

def available_GiB():
    class Memory(ctypes.Structure):
        _fields_=[('dwLength',ctypes.c_ulong),('dwMemoryLoad',ctypes.c_ulong)]+[(n,ctypes.c_ulonglong) for n in ('ullTotalPhys','ullAvailPhys','ullTotalPageFile','ullAvailPageFile','ullTotalVirtual','ullAvailVirtual','ullAvailExtendedVirtual')]
    value=Memory();value.dwLength=ctypes.sizeof(value)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(value)):raise ctypes.WinError(ctypes.get_last_error())
    return value.ullAvailPhys/2**30
