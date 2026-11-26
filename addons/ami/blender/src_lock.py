"""src/・dist/ を書き換える道具どうしを同時に走らせないためのロック（#326）。

`check.sh`・`blender/ami_dat.py`・`build.py` が取る。重なると、`check.sh` の dat の比較と、ほかの `ami_dat.py`・`build.py` が
`src/*.dat` を読み書きしてぶつかり、壊れた pak ができた（#197）。ロックは worktree ごと（`work/src.lock`）。

- OS のファイルロック（Windows は msvcrt、Linux は fcntl）を、取ったプロセスが持つ。プロセスが落ちても（強制終了も）OS が外すので、
  古いロックが残らない。
- 取ったプロセスは環境変数 AMI_SRC_LOCK にロックの場所を入れる。その子（check.sh が呼ぶ ami_dat.py・build.py）は取り直さない。
- 先に取った物があれば、終わるまで待つ（最初に持ち主を 1 行出す）。待つ上限は環境変数 SRC_LOCK_WAIT（秒。既定 1800）。超えたら止まる。
- シートの描画（render.py・render_parallel.py・icons.py）は取らない（Blender を並べて描くのを直列にしないため）。

使い方:
    with src_lock.hold("build.py"): ...                         # Python から
    python -X utf8 blender/src_lock.py run <名前> -- <コマンド>…   # コマンドをロックの下で走らせる（check.sh が自分を包む）
"""
import contextlib
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # addons/ami
LOCK = os.path.join(HERE, "work", "src.lock")
OWNER = LOCK + ".owner"  # 持ち主の名前（Windows はロックした所を読めないので別のファイル）
ENV = "AMI_SRC_LOCK"


def _try_lock(f):
    try:
        if os.name == "nt":
            import msvcrt
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        return False


def _owner():
    try:
        with open(OWNER, encoding="utf8") as f:
            return f.read().strip() or "不明"
    except OSError:
        return "不明"


@contextlib.contextmanager
def hold(who):
    """ロックを取って、抜けるときに外す。親が持っているときは何もしない"""
    if os.environ.get(ENV) == LOCK:
        yield
        return
    os.makedirs(os.path.dirname(LOCK), exist_ok=True)
    f = open(LOCK, "a+")
    try:
        try:
            limit = float(os.environ.get("SRC_LOCK_WAIT") or "1800")
        except ValueError:
            sys.exit(f"[src_lock] SRC_LOCK_WAIT は秒数: {os.environ.get('SRC_LOCK_WAIT')}")
        start = time.monotonic()
        told = False
        while not _try_lock(f):
            if not told:
                print(f"[src_lock] {who}: ほかの道具が src/・dist/ を使っている（{_owner()}）。終わるまで待つ（上限 {limit:.0f} 秒。SRC_LOCK_WAIT）",
                      file=sys.stderr, flush=True)
                told = True
            if time.monotonic() - start > limit:
                sys.exit(f"[src_lock] {who}: {limit:.0f} 秒待っても空かなかった（{_owner()}）。止まった道具が残っていないか見る")
            time.sleep(1)
        if told:
            print(f"[src_lock] {who}: 空いたので続ける", file=sys.stderr, flush=True)
        with open(OWNER, "w", encoding="utf8") as o:
            o.write(f"{who} pid={os.getpid()} {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        os.environ[ENV] = LOCK
        try:
            yield
        finally:
            del os.environ[ENV]
    finally:
        f.close()  # 閉じるとロックも外れる


def main():
    args = sys.argv[1:]
    if len(args) < 4 or args[0] != "run" or args[2] != "--":
        sys.exit("使い方: src_lock.py run <名前> -- <コマンド>…")
    with hold(args[1]):
        sys.exit(subprocess.call(args[3:]))


if __name__ == "__main__":
    main()
