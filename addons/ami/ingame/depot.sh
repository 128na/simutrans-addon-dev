#!/bin/bash
# 車庫の見本（#112）。ingame/depot.nut を流す。
# ゲームは work/depot_game/<PORT>/ の写し（GAME_DIR の exe・dll・設定・pak128・addons と保存データ）に AMI の pak を足して起動する。
# GAME_DIR には書き込まない。敷いた後はゲームを開いたままにする（撮るのは CAPTURE=1）。
# 使い方（アドオンのディレクトリで。python -X utf8 build.py で dist/ami.pak を作っておく）:
#   GAME_DIR=<検証用のフォルダ> EXE=OTRPv64_3.exe PORT=47400 bash ingame/depot.sh   … 起動して敷く
#   PORT=47400 SNOW=1 bash ingame/depot.sh                                          … 動いているゲームの降雪側（x+256）に同じ見本を敷く
#   PORT=47400 CAPTURE=1 OUT=work/depot/shots bash ingame/depot.sh                  … 撮る（行ごと。SNOW=1 を足すと降雪側。名前の先頭に snow_）
#   PORT=47400 CAPTURE=1 VEH=1 OUT=work/depot/shots bash ingame/depot.sh            … 車庫から編成を出して、続けて SHOTS 枚撮る（1 回だけ。出した編成は戻らない）
#   PORT=47400 STOP=1 bash ingame/depot.sh                                          … 閉じて写しを消す
# PAK で AMI の pak を替えられる。ZOOM は gui.set_zoom の値（3 が等倍）
PORT=${PORT:?PORT を指定する}
source "$(dirname "$0")/mcp_client.sh"
M="python $MCP_CLIENT --port $PORT"
WORK="work/depot_game/$PORT"
# depot.nut の OX・OY・ROW_DY・DIR_DX と行の並びに合わせる
OX=20; OY=20; ROW_DY=12; DIR_DX=8
ROWS="ami_rail pak_rail ami_tram pak_tram ami_road pak_road ami_cat ami_wall"
[ "$SNOW" = 1 ] && OX=$((OX + 256))
NUT_SED="s/^local OX = 20;/local OX = $OX;/"
PRE=""; [ "$SNOW" = 1 ] && PRE="snow_"

stop_game() {
  local win; win=$(cd "$WORK" 2> /dev/null && pwd -W) || return 0
  powershell.exe -NoProfile -Command "\$d = '$win'.Replace('/', '\') + '\'; Get-Process | Where-Object { \$_.Path -and \$_.Path.StartsWith(\$d, 'OrdinalIgnoreCase') } | Stop-Process -Force" > /dev/null 2>&1
  sleep 1
  rm -rf "$WORK"
}

if [ "$STOP" = 1 ]; then stop_game; echo "[depot] stopped"; exit 0; fi

run_nut() { $M --run-squirrel "$(sed -e "$NUT_SED" -e 's/^[[:space:]]*//' -e '/^\/\//d' -e '/^$/d' "${NUT:-ingame/depot.nut}")" --timeout 300; }

if [ "$SNOW" = 1 ] && [ "$CAPTURE" != 1 ]; then run_nut; exit 0; fi

shot() {  # shot <x> <y> <名前>
  $M --run-squirrel "gui.close_all_windows(); gui.set_zoom(${ZOOM:-3}); gui.jump(coord3d($1,$2,0)); return 1;" > /dev/null 2>&1
  sleep 1
  $M --capture "$OUT/${PRE}$3.png" > /dev/null 2>&1 && echo "[capture] $OUT/${PRE}$3.png"
}

if [ "$CAPTURE" = 1 ]; then
  OUT=${OUT:-work/depot/shots}
  mkdir -p "$OUT"
  if [ "$VEH" = 1 ]; then
    # 車両の行（depot.nut の VEH。組の並びの下）: 車庫ごとに、画面を合わせてから編成を出し、続けて SHOTS 枚撮る
    vy=$((OY + $(echo $ROWS | wc -w) * ROW_DY + 3))
    k=0
    for v in rail tram road; do
      for di in 0 1; do
        x=$((OX + (k * 2 + di) * DIR_DX * 2 + 3))
        $M --run-squirrel "gui.close_all_windows(); gui.set_zoom(${ZOOM:-3}); gui.jump(coord3d($((x + 1)),$((vy + 1)),0)); return 1;" > /dev/null 2>&1
        sleep 1
        $M --run-squirrel "local d = depot_x($x, $vy, 0); local l = d.get_convoy_list(); if (l.len() > 0) d.start_convoy(player_x(0), l[0]); return 1;" > /dev/null 2>&1
        for i in $(seq 1 ${SHOTS:-6}); do
          $M --capture "$OUT/${PRE}veh_${v}_${di}_$i.png" > /dev/null 2>&1 && echo "[capture] $OUT/${PRE}veh_${v}_${di}_$i.png"
        done
      done
      k=$((k + 1))
    done
    exit 0
  fi
  ri=0
  for row in $ROWS; do
    if [ -z "$ONLY" ] || [[ " $ONLY " == *" $row "* ]]; then
      shot $((OX + 4)) $((OY + ri * ROW_DY + 4)) "$row"  # depot.nut の POS の 4 つの真ん中
    fi
    ri=$((ri + 1))
  done
  exit 0
fi

GAME_DIR=${GAME_DIR:?GAME_DIR に検証用のフォルダを指定する}
EXE=${EXE:?EXE を指定する（例: OTRPv64_3.exe）}
SAVE=${SAVE:-flat_512}
PAK=${PAK:-dist/ami.pak}

$M --run-squirrel "return 1;" > /dev/null 2>&1 && { echo "[depot] ポート $PORT で既にゲームが動いている"; exit 1; }
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
run_nut
$M --run-squirrel "gui.close_all_windows(); gui.set_zoom(3); gui.jump(coord3d($((OX + 4)), $((OY + 4)), 0)); return 1;" > /dev/null
