"""シートを描く道具の設定値（Blender を使わない。sheetlib と render_parallel が読む）。

環境変数で上書きできる。アドオンごとの値（シート名・部品の組み合わせ）はここに置かない（tools/README.md）。
"""
import os
import tempfile

# 並列で描くプロセスの数（render_parallel.py の --jobs の既定）。作業する PC（i9-12900F・メモリ 128GB）に合わせた値。
# 12・16・24・28 で測ると 16 が最速（287 秒）で、それより増やしても速くならない（2026-11-17）。メモリは 1 プロセスあたり数百 MB
JOBS = int(os.environ.get("SHEET_JOBS", "16"))

# 描画の枠の合計（render_slots.py）。作業者（worktree・セッション）をまたいで、マシン全体で同時に動く Blender の数の上限（#74）。
# 既定は論理コア数 − 4（このマシンで 20）。--jobs 16 の 1 本だけなら待ちは起きない。呼び出しごとに値が違うと、大きいほうが実効の上限になるので、変えるときは全員で同じ値にする
SLOTS = int(os.environ.get("SHEET_SLOTS") or max(1, (os.cpu_count() or 8) - 4))

# 描画の枠を数える共有の場所。リポジトリの外で、worktree をまたいで同じ場所になる所（既定は %LOCALAPPDATA%、無ければ OS の一時フォルダの下）
SLOT_DIR = os.environ.get("SHEET_SLOT_DIR") or os.path.join(
    os.environ.get("LOCALAPPDATA") or tempfile.gettempdir(), "simutrans-addon-dev", "render-slots")

# 描画のプロセスの優先度（render_parallel.py の --priority の既定）。low・below_normal・normal のどれか。
# 既定は low。描画が CPU を使い切っても、ほかの作業（エディタ・ブラウザ・ゲームの確認）が重くならないようにする
PRIORITY = os.environ.get("SHEET_PRIORITY", "low")

# Blender の実行ファイル（render_parallel.py の --blender の既定）
BLENDER = os.environ.get("SHEET_BLENDER", r"D:\bin\blender\blender.exe")

# レイアウト検証用モード: SHEET_LAYOUT=1 で、部品ごとに画像で見分けやすい単色で塗る（sheetlib/layout_colors.py）。
# 塗り（材質・汚れ・雪）を見る前に、部品の配置・組み合わせ・タイルどうしの接合を確かめるときに使う。
# シートは src ではなく work/layout/ に書く（src は変えない）
LAYOUT = os.environ.get("SHEET_LAYOUT") == "1"

# 試しに描くとき: SHEET_ONLY=ns,diag_nw,up12 でシートのセルを絞る（ns はいつも描く）。シートは src ではなく work/only/ に書く
ONLY = tuple(c for c in os.environ.get("SHEET_ONLY", "").split(",") if c)
