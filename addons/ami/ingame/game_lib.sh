#!/bin/bash
# ingame/ のスクリプトが source する、ゲームの起動・停止の共通部分（#243）。
# 検証用のフォルダ（GAME_DIR）の写し（work/…/<PORT>/）でゲームを起動し、閉じて写しを消す。GAME_DIR には書き込まない。
# 写しには exe・dll・設定・pak128・addons・保存データを写し、AMI の pak（addons/pak128/ami*.pak）は外してから、渡した pak だけを入れる。
# 起動の前に必ず strip_usage_log.sh で settings.xml の使用状況の送信用の記録を空にする（#235）。昼夜の切り替えは止める（画面の明るさをそろえる）。
#
# 使い方: スクリプトで PORT を決めてから `source "$(dirname "$0")/game_lib.sh"`（MCP のクライアントの場所 MCP_CLIENT と、MCP のコマンド M も決まる）。
#   WORK=work/<名前>/$PORT          … 写しの置き場（アドオンのディレクトリからの相対でよい）
#   trap game_cleanup EXIT; trap 'exit 130' INT TERM    … 終わりに（KEEP=1 でないとき）、このスクリプトが起動したゲームだけ閉じる
#   game_start "dist/ami.pak=ami.pak" extra.pak …       … 写しを作って起動し、MCP が応えるまで待つ。pak は「元」か「元=入れる名前」
#   game_stop                                           … 写しの中のゲームだけ閉じて、写しを消す（STOP=1 の呼び出しでも使う）
# 環境変数（既定は v64 の検証。親の AGENTS.md の「Simutrans 本体の検証環境の使い分け」）:
#   GAME_DIR  … 必須（検証用のフォルダ。addon_check）。絶対パスは既定に書かない
#   EXE       … 既定 sim-WinGDI64-OTRPv64.exe
#   SAVE      … 既定 flat_512_left_v64（512 四方・左側通行・フリープレイ）。カタログは SAVE=ami_catalog
#   SETTINGS  … 写しに入れる設定（GAME_DIR の中のファイル名。既定 settings.xml.v64。settings.xml は OTRPv64_3 の形で v64 は読めない）
#   GAME_ARGS … ゲームに足す引数（例: -screensize 2560x1400）
#   EXTRA_TEXTS … 写しの addons/pak128/text/ に入れる訳のファイル（*.tab。空白区切り）
#   GAME_LOG… ゲームの標準出力・エラーの書き先の絶対パス（既定は捨てる）
#   GAME_WAIT … 起動を待つ回数（2 秒おき。既定 60）
#   GAME_TAG  … メッセージの先頭の名前（既定 game）
#   COPY_DIRS … 写すフォルダ（既定 config font themes text script music pak128 addons）
#   NO_SETTINGS=1 … game_copy で settings.xml を写さない（sample_parallel.sh が台ごとに写す）
_GL_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$_GL_DIR/mcp_client.sh" || return 1
[ -n "$PORT" ] && M="python -X utf8 $MCP_CLIENT --port $PORT"

game_defaults() {
  GAME_DIR=${GAME_DIR:?GAME_DIR に検証用のフォルダを指定する（addon_check の場所は親の AGENTS.md）}
  EXE=${EXE:-sim-WinGDI64-OTRPv64.exe}
  SAVE=${SAVE:-flat_512_left_v64}
  SETTINGS=${SETTINGS:-settings.xml.v64}
}

# game_up <ポート>: MCP が応えるか
game_up() { timeout 20 python -X utf8 "$MCP_CLIENT" --port "$1" --timeout 5 --run-squirrel "return 1;" > /dev/null 2>&1; }

# game_settings <写し>: 設定を写して、使用状況の送信用の記録を空にする
game_settings() {
  if [ -f "$GAME_DIR/$SETTINGS" ]; then
    cp "$GAME_DIR/$SETTINGS" "$1/settings.xml" && chmod u+w "$1/settings.xml" || return 1
  fi
  bash "$_GL_DIR/strip_usage_log.sh" "$1/settings.xml" || return 1
}

# game_copy <写し> [pak …]: 写しを作る（起動はしない）。pak は「元」か「元=入れる名前」
game_copy() {
  local dir=$1 p src dest d; shift
  game_defaults
  mkdir -p "$dir/save" || return 1
  cp "$GAME_DIR/$EXE" "$GAME_DIR"/*.dll "$dir/" || return 1
  for d in ${COPY_DIRS:-config font themes text script music pak128 addons}; do
    [ -d "$GAME_DIR/$d" ] && { cp -r "$GAME_DIR/$d" "$dir/" || return 1; }
  done
  mkdir -p "$dir/addons/pak128" "$dir/config" || return 1
  rm -f "$dir"/addons/pak128/ami*.pak  # 検証用のフォルダに古い AMI の写しがあっても、二重に読まない
  printf '\nday_night_shift = 0\n' >> "$dir/config/simuconf.tab"
  cp "$GAME_DIR/save/$SAVE.sve" "$dir/save/" || return 1
  [ -n "$NO_SETTINGS" ] || game_settings "$dir" || return 1
  # 訳のファイル（EXTRA_TEXTS。addons/pak128/text/<言語>_<名前>.tab。本体は名前の先頭 2 文字で言語を決める: dataobj/translator.cc）
  for p in ${EXTRA_TEXTS:-}; do mkdir -p "$dir/addons/pak128/text" && cp "$p" "$dir/addons/pak128/text/$(basename "$p")" || return 1; done
  for p in "$@"; do
    src=${p%%=*}; dest=$(basename "$src"); [ "$src" = "$p" ] || dest=${p#*=}
    [ -f "$src" ] || { echo "[${GAME_TAG:-game}] pak が無い: $src" >&2; return 1; }
    cp "$src" "$dir/addons/pak128/$dest" || return 1
  done
}

# game_launch <写し> <ポート>: 写しの中の exe を MCP つきで起動する（待たない）
game_launch() {
  (cd "$1" && "./$EXE" -objects pak128/ -addons -load "$SAVE" -mcp-port "$2" ${GAME_ARGS:-} > "${GAME_LOG:-/dev/null}" 2>&1 &)
}

# game_wait <ポート>: MCP が応えるまで待つ（GAME_WAIT 回、2 秒おき）。応えなければ 1
game_wait() {
  local i
  for i in $(seq 1 "${GAME_WAIT:-60}"); do game_up "$1" && return 0; sleep 2; done
  echo "[${GAME_TAG:-game}] ゲームが起動しなかった（ポート $1）" >&2
  return 1
}

# game_kill <写し>: 写しの中の exe で動いているものだけを止める（ポートを開く前のゲームも含む）
game_kill() {
  local win; win=$(cd "$1" 2> /dev/null && pwd -W) || return 0
  powershell.exe -NoProfile -Command "\$d = '$win'.Replace('/', '\') + '\'; Get-Process | Where-Object { \$_.Path -and \$_.Path.StartsWith(\$d, 'OrdinalIgnoreCase') } | Stop-Process -Force" > /dev/null 2>&1
}

# game_start [pak …]: PORT のゲームを WORK の写しで起動する。同じポートで別のゲームが動いていたら何もせず 1
game_start() {
  game_up "$PORT" && { echo "[${GAME_TAG:-game}] ポート $PORT で既にゲームが動いている（PORT を替えるか、そのゲームを閉じる）" >&2; return 1; }
  _GL_OWN=1
  rm -rf "$WORK"
  game_copy "$WORK" "$@" || { game_stop; return 1; }
  game_launch "$WORK" "$PORT"
  game_wait "$PORT" || { game_stop; return 1; }
}

# game_stop: WORK の写しの中のゲームだけ閉じて、写しを消す
game_stop() {
  game_kill "$WORK"
  sleep 1
  rm -rf "$WORK"
}

# game_cleanup: trap 用。KEEP=1 なら開いたままにする。game_start に着手する前（別のゲームが動いていたとき）は何もしない
game_cleanup() {
  [ -n "$KEEP" ] && return 0
  [ -n "$_GL_OWN" ] && game_stop
  return 0
}
