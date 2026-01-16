"""
Asyncio compatibility helpers for sandboxed runtimes.

Some sandbox environments forbid the `send` syscall from non-main threads.
Asyncio's `call_soon_threadsafe()` wakeup uses a socketpair and `send()`,
so thread→loop wakeups can silently fail (the exception is swallowed).

This module detects that condition and patches asyncio to use `os.write()`
to the socket FD instead, restoring reliable wakeups for:
- `loop.call_soon_threadsafe(...)`
- `loop.run_in_executor(...)`
- thread-backed libraries that signal the loop (e.g., aiosqlite)
"""

from __future__ import annotations

import os
import socket
import threading
from typing import Optional


_THREAD_SOCKET_SEND_SUPPORTED: Optional[bool] = None
_PATCH_APPLIED: bool = False


def _thread_socket_send_supported() -> bool:
    global _THREAD_SOCKET_SEND_SUPPORTED
    if _THREAD_SOCKET_SEND_SUPPORTED is not None:
        return _THREAD_SOCKET_SEND_SUPPORTED

    s1 = s2 = None
    send_error: Exception | None = None

    try:
        s1, s2 = socket.socketpair()

        def _worker():
            nonlocal send_error
            try:
                s1.send(b"x")
            except Exception as e:  # pragma: no cover - env-specific
                send_error = e

        t = threading.Thread(target=_worker)
        t.start()
        t.join(timeout=1)

        _THREAD_SOCKET_SEND_SUPPORTED = send_error is None
        return _THREAD_SOCKET_SEND_SUPPORTED
    finally:
        for s in (s1, s2):
            try:
                if s is not None:
                    s.close()
            except Exception:
                pass


def ensure_threadsafe_wakeup() -> None:
    """
    Ensure `call_soon_threadsafe()` can wake the loop in restricted sandboxes.

    Idempotent: safe to call multiple times.
    """
    global _PATCH_APPLIED
    if _PATCH_APPLIED:
        return

    if _thread_socket_send_supported():
        _PATCH_APPLIED = True
        return

    import asyncio.selector_events

    target = asyncio.selector_events.BaseSelectorEventLoop
    if getattr(target._write_to_self, "__orion_patched__", False):
        _PATCH_APPLIED = True
        return

    def _write_to_self(self) -> None:
        csock = getattr(self, "_csock", None)
        if csock is None:
            return
        try:
            os.write(csock.fileno(), b"\0")
        except OSError:
            pass

    _write_to_self.__orion_patched__ = True  # type: ignore[attr-defined]
    target._write_to_self = _write_to_self  # type: ignore[method-assign]
    _PATCH_APPLIED = True

