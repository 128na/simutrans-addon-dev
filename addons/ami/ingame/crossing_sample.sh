#!/bin/bash
# AMI の踏切の見本（#111）。ingame/crossing_sample.nut を流して 12 組 × 2 向きの踏切を温暖・降雪に敷き、開いた絵と閉じた絵を撮る。
# ゲームは work/crossing_game/<PORT>/ の写し（GAME_DIR の exe・dll・設定・pak128・addons と保存データ）に dist/ami.pak を足して起動する。
# GAME_DIR には書き込まない。敷いた後はゲームを開いたままにする。
# 使い方（アドオンのディレクトリで。python -X utf8 build.py で dist/ami.pak を作っておく）:
#   GAME_DIR=<検証用のフォルダ> EXE=OTRPv64_3.exe PORT=47500 bash ingame/crossing_sample.sh > work/crossing/launch.log
#                                                       … 起動して敷き、[check] の行を出す（出力は管に通さずファイルへ。
#                                                         ゲームを起動した子のシェルが管を持ったままになり、ゲームを閉じるまで終わらない）
#   PORT=47500 CAPTURE=open OUT=work/crossing/shots bash ingame/crossing_sample.sh    … 開いた踏切を撮る（<気候>_<線>_<k>_open.png）
#   PORT=47500 TRAIN=1 bash ingame/crossing_sample.sh                                 … 列車を走らせる（crossing_train.nut）
#   PORT=47500 CAPTURE=closed OUT=work/crossing/shots bash ingame/crossing_sample.sh  … 列車が踏切の 1〜3 タイル手前に来たら撮る（閉じた絵。
#                                                         撮った物は飛ばすので流し直せる。WAIT 秒で打ち切る）
#   COMPOSE=1 OUT=work/crossing/shots bash ingame/crossing_sample.sh                  … 撮った画面を切り出し、気候・線・開閉ごとの格子に並べる
#   PORT=47500 STOP=1 bash ingame/crossing_sample.sh                                  … 閉じて写しを消す
# 並びの値は crossing_sample.nut と同じにする（ORIGINS・START・SP・VX・VY）
ORIGINS="temperate:20:24 snow:276:24"
START=10; SP=6; VX=4; VY=12
# 画面（704x536、gui.jump で踏切のタイルへ飛んだとき）のうち、格子に並べる範囲（x0,y0,x1,y1）。踏切のタイルが中ほどに来る
CROP=${CROP:-196,250,456,470}

if [ "$COMPOSE" = 1 ]; then
  OUT=${OUT:-work/crossing/shots}
  BLENDER=${BLENDER:-blender}
  for o in $ORIGINS; do
    clim=${o%%:*}
    for line in H V; do
      for st in open closed; do
        files=()
        for k in $(seq 0 11); do files+=("$OUT/${clim}_${line}_${k}_${st}.png"); done
        "$BLENDER" -b --factory-startup --python ../../tools/blender/grid.py -- "$OUT/../grid_${clim}_${line}_${st}.png" "$CROP" 4 "${files[@]}" \
          > /dev/null 2>&1 && echo "[compose] $OUT/../grid_${clim}_${line}_${st}.png"
      done
    done
  done
  exit 0
fi

PORT=${PORT:?PORT を指定する}
source "$(dirname "$0")/mcp_client.sh"
M="python $MCP_CLIENT --port $PORT"
WORK="work/crossing_game/$PORT"

stop_game() {
  local win; win=$(cd "$WORK" 2> /dev/null && pwd -W) || return 0
  powershell.exe -NoProfile -Command "\$d = '$win'.Replace('/', '\') + '\'; Get-Process | Where-Object { \$_.Path -and \$_.Path.StartsWith(\$d, 'OrdinalIgnoreCase') } | Stop-Process -Force" > /dev/null 2>&1
  sleep 1
  rm -rf "$WORK"
}

squirrel() { $M --run-squirrel "$1" | sed 's/.*"result":"\(.*\)".*/\1/'; }

if [ "$STOP" = 1 ]; then stop_game; echo "[crossing] stopped"; exit 0; fi

if [ "$TRAIN" = 1 ]; then
  echo "$($M --run-squirrel "$(sed -e 's/^[[:space:]]*//' -e '/^\/\//d' -e '/^$/d' ingame/crossing_train.nut)" --timeout 120)"
  exit 0
fi

# 踏切のタイル: 線 H は (ox + i, oy + 2)、線 V は (ox + VX, oy + VY + i)。i = START + k * SP
tile_of() {  # $1=ox $2=oy $3=線 $4=k
  local i=$((START + $4 * SP))
  if [ "$3" = H ]; then echo "$(($1 + i)) $(($2 + 2))"; else echo "$(($1 + VX)) $(($2 + VY + i))"; fi
}

shoot() {  # $1=x $2=y $3=ファイル
  $M --run-squirrel "gui.close_all_windows(); gui.set_zoom(3); gui.jump(coord3d($1,$2,0)); return 1;" > /dev/null 2>&1
  sleep "${SHOT_WAIT:-2}"  # 1 秒だと、前に飛んだ場所の画面が撮れることがあった（2026-11-21、閉じた絵の 48 枚のうち 8 枚）
  $M --capture "$3" > /dev/null 2>&1 && echo "[capture] $3 ($1,$2)"
}

if [ "$CAPTURE" = open ]; then
  OUT=${OUT:-work/crossing/shots}
  mkdir -p "$OUT"
  for o in $ORIGINS; do
    IFS=: read -r clim ox oy <<< "$o"
    for line in H V; do
      for k in $(seq 0 11); do
        read -r x y <<< "$(tile_of "$ox" "$oy" "$line" "$k")"
        shoot "$x" "$y" "$OUT/${clim}_${line}_${k}_open.png"
      done
    done
  done
  exit 0
fi

if [ "$CAPTURE" = closed ]; then
  # 4 本の線の列車をまとめて見張り、列車が 1〜3 タイル手前（行き・帰りのどちら向きでも）にある踏切のうち、まだ撮っていないものを撮る。
  # 撮った物（ファイルがある物）は飛ばすので、途中で止めても流し直せる。WAIT 秒で打ち切り、撮れなかった物を出す（開いた絵を閉じた名前で残さない）
  OUT=${OUT:-work/crossing/shots}
  mkdir -p "$OUT"
  sq="local out = \"\"; foreach (c in world.get_convoy_list()) { local q = c.get_pos();"
  for o in $ORIGINS; do
    IFS=: read -r clim ox oy <<< "$o"
    sq="$sq if (q.y == $((oy + 2)) && q.x >= $ox && q.x <= $((ox + 100))) for (local k = 0; k < 12; k++) { local d = q.x - $((ox + START)) - k * $SP; if (d < 0) d = -d; if (d >= 1 && d <= 3) out += \"${clim}:H:\" + k + \" \"; }"
    sq="$sq if (q.x == $((ox + VX)) && q.y >= $((oy + VY)) && q.y <= $((oy + VY + 100))) for (local k = 0; k < 12; k++) { local d = q.y - $((oy + VY + START)) - k * $SP; if (d < 0) d = -d; if (d >= 1 && d <= 3) out += \"${clim}:V:\" + k + \" \"; }"
  done
  sq="$sq } return out;"
  end_at=$((SECONDS + ${WAIT:-1500}))
  while [ $SECONDS -lt $end_at ]; do
    left=0
    for o in $ORIGINS; do for line in H V; do for k in $(seq 0 11); do
      [ -f "$OUT/${o%%:*}_${line}_${k}_closed.png" ] || left=$((left + 1))
    done; done; done
    [ $left = 0 ] && { echo "[capture] 全部撮った"; exit 0; }
    for tok in $(squirrel "$sq"); do
      IFS=: read -r clim line k <<< "$tok"
      f="$OUT/${clim}_${line}_${k}_closed.png"
      [ -f "$f" ] && continue
      for o in $ORIGINS; do IFS=: read -r c2 ox oy <<< "$o"; [ "$c2" = "$clim" ] && break; done
      read -r x y <<< "$(tile_of "$ox" "$oy" "$line" "$k")"
      shoot "$x" "$y" "$f"
    done
    sleep 0.3
  done
  for o in $ORIGINS; do for line in H V; do for k in $(seq 0 11); do
    [ -f "$OUT/${o%%:*}_${line}_${k}_closed.png" ] || echo "[capture] 撮れなかった: ${o%%:*} ${line} ${k}"
  done; done; done
  exit 1
fi

GAME_DIR=${GAME_DIR:?GAME_DIR に検証用のフォルダを指定する}
EXE=${EXE:?EXE を指定する（例: OTRPv64_3.exe）}
SAVE=${SAVE:-flat_512}
PAK=${PAK:-dist/ami.pak}

$M --run-squirrel "return 1;" > /dev/null 2>&1 && { echo "[crossing] ポート $PORT で既にゲームが動いている"; exit 1; }
rm -rf "$WORK"
mkdir -p "$WORK/save"
cp "$GAME_DIR/$EXE" "$GAME_DIR"/*.dll "$WORK/" || exit 1
for d in config font themes text script music pak128 addons; do
  [ -d "$GAME_DIR/$d" ] && { cp -r "$GAME_DIR/$d" "$WORK/" || exit 1; }
done
cp "$GAME_DIR/save/$SAVE.sve" "$WORK/save/" || exit 1
[ -f "$GAME_DIR/settings.xml" ] && { cp "$GAME_DIR/settings.xml" "$WORK/settings.xml"; chmod u+w "$WORK/settings.xml"; }
cp "$PAK" "$WORK/addons/pak128/ami.pak" || exit 1
(cd "$WORK" && "./$EXE" -objects pak128/ -addons -load "$SAVE" -mcp-port "$PORT" > /dev/null 2>&1 &)
for i in $(seq 1 60); do $M --run-squirrel "return 1;" > /dev/null 2>&1 && break; sleep 2; done
echo "$($M --run-squirrel "$(sed -e 's/^[[:space:]]*//' -e '/^\/\//d' -e '/^$/d' ingame/crossing_sample.nut)" --timeout 300)"
$M --run-squirrel "gui.close_all_windows(); gui.set_zoom(3); gui.jump(coord3d(30, 26, 0)); return 1;" > /dev/null
