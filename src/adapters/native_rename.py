"""Atomic publication that fails if the exact destination already exists."""

import ctypes
import errno
import os
import platform
import sys
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def _native_rename():
    libc = ctypes.CDLL(None, use_errno=True)
    if sys.platform.startswith("linux"):
        # Older DSM builds may have the kernel operation but no glibc wrapper.
        at_fdcwd, noreplace = -100, 1
        args = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        ]
        if hasattr(libc, "renameat2"):
            libc.renameat2.argtypes = args
            libc.renameat2.restype = ctypes.c_int
            return lambda src, dst: libc.renameat2(
                at_fdcwd, src, at_fdcwd, dst, noreplace
            )

        if ctypes.sizeof(ctypes.c_void_p) == 8:
            number = {"x86_64": 316, "aarch64": 276}.get(platform.machine())
            if number is not None:
                # syscall is variadic. Pass each remaining parameter with its C type.
                libc.syscall.argtypes = [ctypes.c_long]
                libc.syscall.restype = ctypes.c_long
                return lambda src, dst: libc.syscall(
                    number,
                    ctypes.c_int(at_fdcwd),
                    ctypes.c_char_p(src),
                    ctypes.c_int(at_fdcwd),
                    ctypes.c_char_p(dst),
                    ctypes.c_uint(noreplace),
                )
    if sys.platform == "darwin" and hasattr(libc, "renamex_np"):
        libc.renamex_np.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
        libc.renamex_np.restype = ctypes.c_int
        return lambda src, dst: libc.renamex_np(src, dst, 4)  # RENAME_EXCL
    raise OSError(
        errno.ENOTSUP, "This platform has no supported atomic no-replace rename"
    )


def rename_noreplace(source: Path, destination: Path) -> None:
    if os.name == "nt":
        os.rename(
            source, destination
        )  # Windows guarantees failure if destination exists.
        return
    if _native_rename()(os.fsencode(source), os.fsencode(destination)) != 0:
        code = ctypes.get_errno()
        raise OSError(
            code, f"{os.strerror(code)}: {source} -> {destination}", str(destination)
        )
