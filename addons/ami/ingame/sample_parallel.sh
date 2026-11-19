#!/bin/bash
# AMI の見本を複数のゲームで敷いて撮る。208 画面が 8 台で準備込み約 40 秒（1 台で順に撮ると 2 分以上）。
# 使い方（アドオンのディレクトリで。python -X utf8 build.py で dist/ami.pak を作っておく）:
#   GAME_DIR=<検証用のフォルダ> EXE=<実行ファイル> TRACK=ami_rail_slab bash ingame/sample_parallel.sh
# 台数は JOBS（既定 8）、出力先は OUT（既定 work/sample）。PAK・NUT・TRACK・SAVE・SPOTS・ZOOM は sample_check.sh・sample_capture.sh と同じ。
# ゲームは work/parallel/<番号>/ の写しで起動し、撮り終えたら閉じる。GAME_DIR には書き込まない。
# 同じフォルダで同時に起動すると settings.xml が消えることがある（docs/reference/way-addon.md の 8.2）ので、GAME_DIR では起動しない。
GAME_DIR=${GAME_DIR:?GAME_DIR に検証用のフォルダを指定する}
EXE=${EXE:?EXE に実行ファイルの名前を指定する}
JOBS=${JOBS:-8}
BASE_PORT=${BASE_PORT:-47140}
SAVE=${SAVE:-flat_512}
PAK=${PAK:-dist/ami.pak}
NUT=${NUT:-ingame/sample.nut}
OUT=${OUT:-work/sample}
ZOOM=${ZOOM:-3}
WAIT=${WAIT:-0.3}     # 移動してから撮るまでの秒数
SETTLE=${SETTLE:-5}   # 敷いた後、建設費の表示が消えるまで待つ秒数
WORK=work/parallel
CLIENT=${MCP_CLIENT:-../../../simutrans/.agents/skills/simutrans-mcp-gui-debug/scripts/mcp_client.py}
source "$(dirname "$0")/sample_spots.sh"

mcp() { local port=$1; shift; python -X utf8 "$CLIENT" --port "$port" "$@"; }
pids() { netstat -ano | tr -d '\r' | awk -v p=":$1" '$4 == "LISTENING" && $2 ~ p "$" {print $NF}' | sort -u; }
stop_games() {
  for ((i = 0; i < JOBS; i++)); do
    for pid in $(pids $((BASE_PORT + i))); do taskkill //PID "$pid" //F > /dev/null 2>&1; done
  done
  sleep 1
  rm -rf "$WORK"/[0-9]*
}

for ((i = 0; i < JOBS; i++)); do
  [ -z "$(pids $((BASE_PORT + i)))" ] || { echo "[parallel] ポート $((BASE_PORT + i)) で既にゲームが動いている（BASE_PORT を替えるか、そのゲームを閉じる）"; exit 1; }
done
[ -f "$PAK" ] || { echo "[parallel] $PAK が無い"; exit 1; }

# 写しの元を作る（2 回目からは更新分だけ）。台ごとのフォルダはハードリンクなので容量も時間もほとんど使わない
rm -rf "$WORK"/[0-9]*
BASE="$WORK/base"
mkdir -p "$BASE/save" "$OUT"
cp -u "$GAME_DIR/$EXE" "$GAME_DIR"/*.dll "$BASE/" || exit 1
for d in config font themes text script music pak128 addons; do
  [ -d "$GAME_DIR/$d" ] && { cp -ru "$GAME_DIR/$d" "$BASE/" || exit 1; }
done
cp -u "$GAME_DIR/save/$SAVE.sve" "$BASE/save/" || exit 1
cp "$PAK" "$BASE/addons/pak128/ami.pak" || exit 1
trap stop_games EXIT
for ((i = 0; i < JOBS; i++)); do
  D="$WORK/$i"; mkdir "$D"
  for e in "$BASE"/*; do [ "$(basename "$e")" = config ] || cp -al "$e" "$D/" || exit 1; done
  # 昼夜で画面の明るさが変わると比べられないので止める
  cp -r "$BASE/config" "$D/config"
  printf '\nday_night_shift = 0\n' >> "$D/config/simuconf.tab"
  [ -f "$GAME_DIR/settings.xml" ] && { cp "$GAME_DIR/settings.xml" "$D/settings.xml"; chmod u+w "$D/settings.xml"; }
done

TRACK_SED=${TRACK:+s/^local TRACK = .*/local TRACK = \"$TRACK\";/}
SCRIPT=$(sed -e 's/\r$//' -e 's/^[[:space:]]*//' -e '/^\/\//d' -e '/^$/d' -e "${TRACK_SED:-b}" "$NUT")
OUT_ABS=$(cd "$OUT" && pwd -W)
ALL=()
for season in temperate:20:20 snow:276:20; do for spot in $SPOTS; do ALL+=("$season/$spot"); done; done

worker() {
  local i=$1 port=$((BASE_PORT + i)) n=0 item season spot s ox oy k x y f r
  (cd "$WORK/$i" && "./$EXE" -objects pak128/ -addons -load "$SAVE" -mcp-port "$port" > /dev/null 2>&1 &)
  for r in $(seq 1 120); do timeout 10 python -X utf8 "$CLIENT" --port "$port" --timeout 5 --run-squirrel "return 1;" > /dev/null 2>&1 && break; sleep 1; done
  r=$(mcp "$port" --run-squirrel "$SCRIPT" --timeout 300 2>&1)
  case $r in *'"result":"ok'*) ;; *) echo "[parallel] $i 台目: 見本を敷けない: ${r:0:200}"; return 1 ;; esac
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

LOG="$WORK/capture.log"; : > "$LOG"
pids_w=()
for ((i = 0; i < JOBS; i++)); do worker "$i" >> "$LOG" 2>&1 & pids_w+=($!); done
status=0
for p in "${pids_w[@]}"; do wait "$p" || status=1; done
got=$(grep -c '^\[capture\]' "$LOG")
grep '^\[parallel\]' "$LOG"
echo "[parallel] ${got} / ${#ALL[@]} 画面を $OUT に撮った（$JOBS 台）"
[ "$status" -eq 0 ] && [ "$got" -eq "${#ALL[@]}" ]
