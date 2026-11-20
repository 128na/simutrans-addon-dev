"""描画の枠: マシン全体で同時に動く Blender の数を、作業者（worktree・セッション）をまたいで抑える（#74）。

render_parallel.py が使う。標準ライブラリだけで動く（Blender は使わない）。

- 枠は共有の場所（sheet_settings.SLOT_DIR）の slot_<番号>.lock で、番号は 0 から sheet_settings.SLOTS - 1 まで。
  1 本の Blender を起こす前に、どれか 1 つのファイルに OS のロック（Windows は msvcrt.locking、ほかは fcntl.flock）を
  かけて取り、Blender が終わったら外して返す。空きが無ければ、呼び出し側が待つ。
- ロックはプロセスが落ちると OS が外す。そのため、止めたり落ちたりした render_parallel の枠は残らない。
  ロックファイルは消さない（消すと、別のプロセスが同じ番号を二重に取れる）。
- 親が強制終了されたときに Blender だけが動き続けると、枠は空いたのに Blender が残って合計を超える。
  Windows では親を Job Object（閉じたら中のプロセスを止める）に入れ、子の Blender も同じ Job に入れて道連れにする。
"""
import errno
import os
import sys

# ほかのプロセスが持っているときにロックが返すエラー。これ以外（権限・場所が無いなど）は「使用中」と見なさず、そのまま出す
# （見なすと、原因が見えないまま枠待ちが続く）
_BUSY = {errno.EACCES, errno.EAGAIN, errno.EWOULDBLOCK, getattr(errno, "EDEADLOCK", errno.EDEADLK), errno.EDEADLK}


class Slot:
    """取った枠 1 つ。release() で返す（プロセスが終われば OS が外す）"""

    def __init__(self, index, fd):
        self.index = index
        self._fd = fd

    def release(self):
        if self._fd is None:
            return
        try:
            _unlock(self._fd)
        finally:
            os.close(self._fd)
            self._fd = None


if os.name == "nt":
    import msvcrt

    def _try_lock(fd):
        os.lseek(fd, 0, os.SEEK_SET)
        try:
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            return True
        except OSError as e:
            if e.errno in _BUSY:
                return False
            raise

    def _unlock(fd):
        os.lseek(fd, 0, os.SEEK_SET)
        try:
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
else:
    import fcntl

    def _try_lock(fd):
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except OSError as e:
            if e.errno in _BUSY:
                return False
            raise

    def _unlock(fd):
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        except OSError:
            pass


class SlotPool:
    """共有の場所にある total 個の枠。try_acquire() は空きが無ければ None を返す（待たない）"""

    def __init__(self, directory, total):
        if total < 1:
            raise ValueError(f"枠の合計は 1 以上: {total}")
        self.directory = directory
        self.total = total
        os.makedirs(directory, exist_ok=True)

    def try_acquire(self):
        for i in range(self.total):
            path = os.path.join(self.directory, f"slot_{i}.lock")
            fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o666)
            try:
                locked = _try_lock(fd)
            except BaseException:
                os.close(fd)
                raise
            if locked:
                return Slot(i, fd)
            os.close(fd)
        return None


def kill_children_with_parent():
    """Windows: このプロセスを「閉じたら中のプロセスを止める」Job に入れる。以後に起こす子も同じ Job に入る。

    親が強制終了されると Job のハンドルが閉じ、子の Blender も止まる（枠だけ空いて Blender が残るのを防ぐ）。
    入れられなかったら False（古い Windows など。そのときは Ctrl+C などで止めたときの後始末だけになる）。
    ほかの OS では何もしない（False）。
    """
    if os.name != "nt":
        return False
    import ctypes
    from ctypes import wintypes

    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateJobObjectW.argtypes = (wintypes.LPVOID, wintypes.LPCWSTR)
    k32.CreateJobObjectW.restype = wintypes.HANDLE
    k32.SetInformationJobObject.argtypes = (wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD)
    k32.SetInformationJobObject.restype = wintypes.BOOL
    k32.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE)
    k32.AssignProcessToJobObject.restype = wintypes.BOOL
    k32.GetCurrentProcess.argtypes = ()
    k32.GetCurrentProcess.restype = wintypes.HANDLE

    class IO_COUNTERS(ctypes.Structure):
        _fields_ = [(n, ctypes.c_ulonglong) for n in (
            "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
            "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

    class BASIC(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_longlong),
            ("PerJobUserTimeLimit", ctypes.c_longlong),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class EXTENDED(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", BASIC),
            ("IoInfo", IO_COUNTERS),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    JobObjectExtendedLimitInformation = 9
    JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
    job = k32.CreateJobObjectW(None, None)
    if not job:
        return False
    info = EXTENDED()
    info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    if not k32.SetInformationJobObject(job, JobObjectExtendedLimitInformation, ctypes.byref(info), ctypes.sizeof(info)):
        return False
    if not k32.AssignProcessToJobObject(job, k32.GetCurrentProcess()):
        return False
    # job のハンドルは閉じない（プロセスが終わるまで持ち続け、終わったときに OS が閉じて子を止める）
    return True


if __name__ == "__main__":
    # 枠の空き具合を見る（python -X utf8 tools/blender/render_slots.py）
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import sheet_settings

    pool = SlotPool(sheet_settings.SLOT_DIR, sheet_settings.SLOTS)
    held = []
    while (s := pool.try_acquire()) is not None:
        held.append(s)
    print(f"枠: {sheet_settings.SLOT_DIR}  合計 {pool.total}、使用中 {pool.total - len(held)}")
    for s in held:
        s.release()
