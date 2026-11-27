#!/bin/bash
# AMI の見本を複数のゲームで敷いて撮る。208 画面が 8 台で準備込み約 40 秒（1 台で順に撮ると 2 分以上）。
# 使い方（アドオンのディレクトリで。python -X utf8 build.py で dist/ami.pak を作っておく）:
#   GAME_DIR=<検証用のフォルダ> TRACK=ami_rail_slab bash ingame/sample_parallel.sh
# 台数は JOBS（既定 8）、出力先は OUT（既定 work/sample）。PAK・NUT・TRACK・SAVE・SPOTS・ZOOM は sample_check.sh・sample_capture.sh と同じ。
# ラウンドの版（#56）を撮るときは、EXTRA_PAKS（空白区切り）でその pak を足し、SUFFIX（例: _round1）で sample.nut の SUFFIX を替える。
# SEASONS（既定は温暖側と降雪側の「名前:原点 x:原点 y」2 つ）を渡すと、その原点だけ撮る（温暖側だけの見本は SEASONS=temperate:20:20）。
# モノレールの見本（NUT=ingame/monorail.nut・suspended_sample.nut）は原点が 1 つ（行頭の local OX・OY）なので、SEASONS の原点ごとに
# 置き換えて 1 回ずつ敷く（sample_spots.sh の PER_SEASON）。車両は EXTRA_PAKS で写しに足す。
# 256 のタイルは PAKSET=pak256poc PAKSET_SRC=<検証用のフォルダ>/pak256poc PAK=dist256/ami.pak（README の「導入と検証」）。
# ゲームは work/parallel/<BASE_PORT>/ の写しで起動し、撮り終えたら閉じて写しも消す。GAME_DIR には書き込まない。
# 同じフォルダで同時に起動すると settings.xml が消えることがある（docs/reference/way-addon.md の 8.2）ので、GAME_DIR では起動しない。
JOBS=${JOBS:-8}
BASE_PORT=${BASE_PORT:-47140}
PAK=${PAK:-dist/ami.pak}
NUT=${NUT:-ingame/sample.nut}
OUT=${OUT:-work/sample}
ZOOM=${ZOOM:-3}
WAIT=${WAIT:-0.3}     # 移動してから撮るまでの秒数
SETTLE=${SETTLE:-5}   # 敷いた後、建設費の表示が消えるまで待つ秒数
WORK="work/parallel/$BASE_PORT"
LOG="work/parallel/$BASE_PORT.log"
source "$(dirname "$0")/game_lib.sh"   # 起動・停止の共通（#243。PORT は台ごとなので M は使わない）
GAME_TAG=parallel
CLIENT=$MCP_CLIENT
source "$(dirname "$0")/sample_spots.sh"

game_log() { if [ -n "$GAME_LOG" ]; then echo "$GAME_LOG.$1"; else echo /dev/null; fi; }  # GAME_LOG があれば台ごとに .<台番号> を付けて残す
mcp() { local port=$1; shift; python -X utf8 "$CLIENT" --port "$port" "$@"; }
pids() { netstat -ano | tr -d '\r' | awk -v p=":$1" '$4 == "LISTENING" && $2 ~ p "$" {print $NF}' | sort -u; }
# 写しの中の exe で動いているものだけを止める（ポートを開く前のゲームも含む）
stop_games() {
  [ "${#pids_w[@]}" -eq 0 ] || kill "${pids_w[@]}" 2> /dev/null
  game_kill "$WORK"
  sleep 1
  game_unlink_all "$WORK" && rm -rf "$WORK"  # PAKSET_SRC のジャンクションを先に外す。外せなければ残す
}

for ((i = 0; i < JOBS; i++)); do
  [ -z "$(pids $((BASE_PORT + i)))" ] || { echo "[parallel] ポート $((BASE_PORT + i)) で既にゲームが動いている（BASE_PORT を替えるか、そのゲームを閉じる）"; exit 1; }
done
[ -f "$PAK" ] || { echo "[parallel] $PAK が無い"; exit 1; }

# 写しの元を毎回作り直す（GAME_DIR の今の状態で撮る）。台ごとのフォルダはハードリンクなので容量も時間もほとんど使わない
game_unlink_all "$WORK" || exit 1  # 前の実行が残したジャンクションは、先に外す
rm -rf "$WORK"
BASE="$WORK/base"
mkdir -p "$BASE/save" "$OUT"
pids_w=()
trap stop_games EXIT
trap 'exit 130' INT TERM
NO_SETTINGS=1 game_copy "$BASE" "$PAK=ami.pak" ${EXTRA_PAKS:-} || exit 1  # 設定は台ごとに写す（ハードリンクで共有しない）
for ((i = 0; i < JOBS; i++)); do
  D="$WORK/$i"; mkdir "$D"
  for e in "$BASE"/*; do
    [ "$(basename "$e")" = config ] && continue
    # PAKSET_SRC のジャンクションは cp -al できないので、台ごとに作り直す（元の pak は読むだけ）
    if [ -n "$PAKSET_SRC" ] && [ "$(basename "$e")" = "${PAKSET:-pak128}" ]; then game_junction "$D/$(basename "$e")" "$PAKSET_SRC" || exit 1; else cp -al "$e" "$D/" || exit 1; fi
  done
  cp -r "$BASE/config" "$D/config"  # 昼夜を止めた設定（game_copy）。台ごとに書かれるので共有しない
  game_settings "$D" || exit 1  # 送信用の記録を外した設定（#235）
done

TRACK_SED=${TRACK:+s/^local TRACK = .*/local TRACK = \"$TRACK\";/}
SUFFIX_SED=${SUFFIX:+s/^local SUFFIX = .*/local SUFFIX = \"$SUFFIX\";/}
# 置き換えは渡されたものだけを足す（無いときに b を渡すと、sed は残りの置き換えを飛ばす）
SED_ARGS=()
[ -n "$TRACK_SED" ] && SED_ARGS+=(-e "$TRACK_SED")
[ -n "$SUFFIX_SED" ] && SED_ARGS+=(-e "$SUFFIX_SED")
SCRIPT=$(sed -e 's/\r$//' -e 's/^[[:space:]]*//' -e '/^\/\//d' -e '/^$/d' "${SED_ARGS[@]}" "$NUT")
OUT_ABS=$(cd "$OUT" && pwd -W)
ALL=()
for season in ${SEASONS:-temperate:20:20 snow:276:20}; do for spot in $SPOTS; do ALL+=("$season/$spot"); done; done

# lay <ポート> <Squirrel> <台番号>: 見本を敷く。返り値が ok か check で始まらなければ失敗
lay() {
  local r
  r=$(mcp "$1" --run-squirrel "$2" --timeout 300 2>&1)
  case $r in
    # 1 台目の報告（[check] の行を含む）は、全部敷けたときも出す
    *'"result":"ok'* | *'"result":"check'*) [ "$3" -ne 0 ] || echo "[parallel] 見本の報告: $r" ;;
    *) echo "[parallel] $3 台目: 見本を敷けない: ${r:0:200}"; return 1 ;;
  esac
}

worker() {
  local i=$1 port=$((BASE_PORT + i)) n=0 item season spot s ox oy k x y f
  GAME_LOG=$(game_log "$i") game_launch "$WORK/$i" "$port"
  game_wait "$port" || { echo "[parallel] $i 台目: 起動しなかった"; return 1; }
  if [ "$PER_SEASON" = 1 ]; then
    # 原点が 1 つの見本は、SEASONS の原点ごとに 1 回ずつ敷く
    for season in ${SEASONS:-temperate:20:20 snow:276:20}; do
      IFS=: read s ox oy <<< "$season"
      lay "$port" "$(sed -e "s/^local OX = [0-9]*;/local OX = $ox;/" -e "s/^local OY = [0-9]*;/local OY = $oy;/" <<< "$SCRIPT")" "$i" || return 1
    done
  else
    lay "$port" "$SCRIPT" "$i" || return 1
  fi
  sleep "$SETTLE"
  for item in "${ALL[@]}"; do
    if [ $((n % JOBS)) -eq "$i" ]; then
      IFS=/ read season spot <<< "$item"; IFS=: read s ox oy <<< "$season"; IFS=: read k x y <<< "$spot"
      f="$OUT_ABS/${s}_$k.png"; rm -f "$f"
      mcp "$port" --run-squirrel "gui.close_all_windows(); gui.set_zoom($ZOOM); gui.jump(coord3d($((ox + x)),$((oy + y)),0)); return 1;" > /dev/null 2>&1
      sleep "$WAIT"
      mcp "$port" --capture "$f" > /dev/null 2>&1
      [ -f "$f" ] && echo "[capture] $OUT/${s}_$k.png" || echo "[parallel] 撮れない: ${s}_$k"
    fi
    n=$((n + 1))
  done
}

: > "$LOG"
for ((i = 0; i < JOBS; i++)); do worker "$i" >> "$LOG" 2>&1 & pids_w+=($!); done
status=0
for p in "${pids_w[@]}"; do wait "$p" || status=1; done
got=$(grep -c '^\[capture\]' "$LOG")
grep '^\[parallel\]' "$LOG"
echo "[parallel] ${got} / ${#ALL[@]} 画面を $OUT に撮った（$JOBS 台）"
[ "$status" -eq 0 ] && [ "$got" -eq "${#ALL[@]}" ]
