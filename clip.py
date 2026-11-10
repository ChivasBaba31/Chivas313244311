import ctypes
import time

CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002
_api = {}


def _load():
    if _api:
        return _api["u"], _api["k"]
    from ctypes import wintypes
    u = ctypes.WinDLL("user32", use_last_error=True)
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    u.OpenClipboard.argtypes = [wintypes.HWND]
    u.OpenClipboard.restype = wintypes.BOOL
    u.CloseClipboard.argtypes = []
    u.CloseClipboard.restype = wintypes.BOOL
    u.EmptyClipboard.argtypes = []
    u.EmptyClipboard.restype = wintypes.BOOL
    u.GetClipboardData.argtypes = [wintypes.UINT]
    u.GetClipboardData.restype = wintypes.HANDLE
    u.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    u.SetClipboardData.restype = wintypes.HANDLE
    k.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    k.GlobalAlloc.restype = wintypes.HGLOBAL
    k.GlobalLock.argtypes = [wintypes.HGLOBAL]
    k.GlobalLock.restype = ctypes.c_void_p
    k.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    k.GlobalUnlock.restype = wintypes.BOOL
    k.GlobalFree.argtypes = [wintypes.HGLOBAL]
    k.GlobalFree.restype = wintypes.HGLOBAL
    _api["u"] = u
    _api["k"] = k
    return u, k


def _open(u):
    for _ in range(20):
        if u.OpenClipboard(None):
            return True
        time.sleep(0.05)
    return False


def set_text(text):
    text = text or ""
    try:
        u, k = _load()
        data = ctypes.create_unicode_buffer(text)
        size = ctypes.sizeof(data)
        if not _open(u):
            return False
        try:
            u.EmptyClipboard()
            h = k.GlobalAlloc(GMEM_MOVEABLE, size)
            if not h:
                return False
            p = k.GlobalLock(h)
            ctypes.memmove(p, data, size)
            k.GlobalUnlock(h)
            if not u.SetClipboardData(CF_UNICODETEXT, h):
                k.GlobalFree(h)
                return False
            return True
        finally:
            u.CloseClipboard()
    except Exception:
        return False


def get_text():
    try:
        u, k = _load()
        if not _open(u):
            return ""
        try:
            h = u.GetClipboardData(CF_UNICODETEXT)
            if not h:
                return ""
            p = k.GlobalLock(h)
            if not p:
                return ""
            try:
                return ctypes.wstring_at(p)
            finally:
                k.GlobalUnlock(h)
        finally:
            u.CloseClipboard()
    except Exception:
        return ""
