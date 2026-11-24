#!/bin/bash
# iss と AMI の版ごとのカーブ・分岐の絵を、同じ配置で敷いて並べる検討用の見本（#88）。ingame/curve_switch_study.nut を流す。
# ゲームは work/study_game/<PORT>/ の写し（GAME_DIR の exe・dll・設定・pak128・addons と保存データ）に、AMI の pak と iss の線路の pak を
# 足して起動する。GAME_DIR には書き込まない（iss の pak は写しの中だけに置く）。敷いた後はゲームを開いたままにする（撮るのは CAPTURE=1）。
# 使い方（アドオンのディレクトリで。python -X utf8 build.py で dist/ami.pak を作っておく）:
#   GAME_DIR=<検証用のフォルダ> PORT=47400 bash ingame/curve_switch_study.sh   … 起動して敷く
#   PORT=47400 CLASSIFY=1 bash ingame/curve_switch_study.sh                                     … 分岐のタイルの自動の絵が標準・分岐 1・2 のどれかを出す
#   PORT=47400 TRAIN=1 bash ingame/curve_switch_study.sh                                        … 列車を走らせ、渡り線の絵が予約で変わるかを読む
#   PORT=47400 CAPTURE=1 OUT=work/study/shots bash ingame/curve_switch_study.sh                 … 撮る（区画ごと）
#   PORT=47400 STOP=1 bash ingame/curve_switch_study.sh                                         … 閉じて写しを消す
# ISS_PAKS で iss の pak を渡す（既定は親フォルダの refs/iss/release/pak128/iss_rail_way.pak）
PORT=${PORT:?PORT を指定する}
source "$(dirname "$0")/game_lib.sh"   # 起動・停止・MCP のコマンド M（#243）
WORK="work/study_game/$PORT"
OX=150; OY=20; SPACING=34
SETS=${SETS:-"iss ami amin"}


if [ "$STOP" = 1 ]; then game_stop; echo "[study] stopped"; exit 0; fi

if [ "$TRAIN" = 1 ]; then
  # curve_switch_train.nut を流し、渡り線の 2 タイル（組ごとに (OX+36, y+5) の back と (OX+36, y+6) の front）の絵の番号を
  # 1 秒ごとに SECONDS_TRAIN 秒読み、変わったときだけ出す。番号の意味は CLASSIFY の back-T@4,12・front-T@8,14 と同じ way・同じ向き
  echo "$($M --run-squirrel "$(sed -e 's/^[[:space:]]*//' -e '/^\/\//d' -e '/^$/d' ingame/curve_switch_train.nut)" --timeout 120)"
  NSETS=$(echo $SETS | wc -w)
  prev=""
  for t in $(seq 1 ${SECONDS_TRAIN:-90}); do
    now=$($M --run-squirrel "local s = \"\"; for (local i = 0; i < $NSETS; i++) foreach (dy in [5, 6]) s += square_x($((OX + 36)), $OY + i * $SPACING + dy).get_ground_tile().get_way(wt_rail).get_image_id() + \" \"; return s;" | sed 's/.*"result":"\(.*\) ".*/\1/')
    [ "$now" != "$prev" ] && echo "[train] t=$t $now"
    prev=$now
    sleep 1
  done
  exit 0
fi

if [ "$CLASSIFY" = 1 ]; then
  # 分岐のタイルごとに、自動の絵が固定の道具の標準（0）・選択 1（dat の「2」）・選択 2（dat の「1」）のどれと同じかを出す。
  # 固定の効き目は次の呼び出しで絵に出るので、固定と読み出しを別の呼び出しにする。最後に自動（-1）へ戻す
  TILES="[4,12],[4,13],[8,13],[8,14],[12,14],[14,12]"
  NSETS=$(echo $SETS | wc -w)
  read_all() {
    $M --run-squirrel "local s = \"\"; for (local i = 0; i < $NSETS; i++) foreach (p in [$TILES]) { local t = square_x($OX + p[0], $OY + i * $SPACING + p[1]).get_ground_tile(); local w = t == null ? null : t.get_way(wt_rail); s += (w == null ? -1 : w.get_image_id()) + \" \"; } return s;" | sed 's/.*"result":"\(.*\) ".*/\1/'
  }
  pin_all() {
    $M --run-squirrel "local pl = player_x(0); local pin = command_x(tool_set_switch_image); for (local i = 0; i < $NSETS; i++) foreach (p in [$TILES]) pin.work(pl, coord3d($OX + p[0], $OY + i * $SPACING + p[1], 0), \"\" + wt_rail + \",$1\"); return 1;" > /dev/null
    sleep 2
  }
  A=($(read_all)); pin_all 0; P0=($(read_all)); pin_all 1; P1=($(read_all)); pin_all 2; P2=($(read_all)); pin_all -1; R=($(read_all))
  names=(back-T@4,12 center-T@4,13 center-T@8,13 front-T@8,14 front-side@12,14 back-side@14,12)
  k=0
  for s in $SETS; do
    line="[sw] $s"
    for n in "${names[@]}"; do
      a=${A[$k]}
      if [ "${P0[$k]}" = "${P1[$k]}" ] && [ "${P1[$k]}" = "${P2[$k]}" ]; then c="no-switch-image(auto=$([ $a = ${P0[$k]} ] && echo plain || echo other))"
      elif [ "$a" = "${P0[$k]}" ]; then c=plain; elif [ "$a" = "${P1[$k]}" ]; then c=sw2; elif [ "$a" = "${P2[$k]}" ]; then c=sw1; else c="other($a)"; fi
      [ "${R[$k]}" = "$a" ] || c="$c reset-differs"
      line="$line $n=$c"
      k=$((k + 1))
    done
    echo "$line"
  done
  exit 0
fi

if [ "$CAPTURE" = 1 ]; then
  OUT=${OUT:-work/study/shots}
  ZOOM=${ZOOM:-3}
  mkdir -p "$OUT"
  i=0
  for s in $SETS; do
    # 区画の中の見どころ（nut の冒頭の表の場所）: corner = 単線のカーブ、x3 = 3 本の渡り線、sid = 側線への分岐、dc = 複線のカーブ
    for spot in corner:5:4 x3:7:13 sid:13:13 dc:5:23; do
      IFS=: read name dx dy <<< "$spot"
      x=$((OX + dx)); y=$((OY + i * SPACING + dy))
      $M --run-squirrel "gui.close_all_windows(); gui.set_zoom($ZOOM); gui.jump(coord3d($x,$y,0)); return 1;" > /dev/null 2>&1
      sleep 1
      $M --capture "$OUT/${s}_${name}.png" > /dev/null 2>&1 && echo "[capture] $OUT/${s}_${name}.png"
    done
    i=$((i + 1))
  done
  exit 0
fi

PAK=${PAK:-dist/ami.pak}
REFS=$(cd "$(dirname "$0")" && git rev-parse --path-format=absolute --git-common-dir 2> /dev/null | xargs dirname | xargs dirname)/refs
ISS_PAKS=${ISS_PAKS:-$REFS/iss/release/pak128/iss_rail_way.pak}
NUT=${NUT:-ingame/curve_switch_study.nut}

GAME_TAG=study
game_start "$PAK=ami.pak" $ISS_PAKS || exit 1
echo "$($M --run-squirrel "$(sed -e 's/^[[:space:]]*//' -e '/^\/\//d' -e '/^$/d' "$NUT")" --timeout 300)"
$M --run-squirrel "gui.close_all_windows(); gui.set_zoom(3); gui.jump(coord3d($((OX + 6)), $((OY + 13)), 0)); return 1;" > /dev/null
