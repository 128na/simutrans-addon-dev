#!/bin/bash
# 配る pak の読み込みの確認（#91）: 配る zip と同じ種類別の pak だけを入れたゲームを起動し、ingame/beta_check.nut で全部の物を 1 つずつ道具で敷く。
# 使い方（アドオンのディレクトリで。python -X utf8 build.py で dist/ を作っておく）:
#   GAME_DIR=F:/Simutrans/addon_check EXE=OTRPv64_3.exe PORT=47400 bash ingame/beta_check.sh
# ゲームは work/beta_game/<PORT>/ の写し（GAME_DIR の exe・dll・設定・pak128・addons と保存データ）で起動し、GAME_DIR には書き込まない。
# 写しからは AMI の古い pak（addons/pak128/ami*.pak）を外し、PAKS（既定は dist/ の種類別の 4 つ。zip の中身と同じ）を入れる。
# 敷く物は src/*.dat の obj・name・waytype・system_type から作る（提供用の ex_donors.dat は除く）。終わったらゲームを閉じて写しを消す。
# 出力: 敷いた結果（先頭が ok なら全部敷けた）と、ゲームのログ（-log 1 -debug 3 の simu.log。work/beta_game/simu_<PORT>.log に残す）のうち、
# 読んだ AMI の pak と、AMI の物の名前を含む警告・エラーの行（同じ物を二重に読むと「object way::<名前> is overlaid!」が出る）。
# 全部敷けて警告が無ければ 0、どちらかが外れたら 1 で終わる
GAME_DIR=${GAME_DIR:?GAME_DIR に検証用のフォルダを指定する}
EXE=${EXE:?EXE を指定する（例: OTRPv64_3.exe）}
PORT=${PORT:?PORT に MCP のポートを指定する}
SAVE=${SAVE:-flat_512}
PAKS=${PAKS:-"dist/ami_rail.pak dist/ami_road.pak dist/ami_tram.pak dist/ami_extra.pak dist/ami_scenery.pak"}
NUT=ingame/beta_check.nut
source "$(dirname "$0")/mcp_client.sh"
M="python -X utf8 $MCP_CLIENT --port $PORT"
WORK="work/beta_game/$PORT"
for p in $PAKS; do [ -f "$p" ] || { echo "[beta] $p が無い"; exit 1; }; done
$M --run-squirrel "return 1;" > /dev/null 2>&1 && { echo "[beta] ポート $PORT で既にゲームが動いている"; exit 1; }

stop_game() {
  powershell.exe -NoProfile -Command "\$d = '$WORK_WIN'.Replace('/', '\') + '\'; Get-Process | Where-Object { \$_.Path -and \$_.Path.StartsWith(\$d, 'OrdinalIgnoreCase') } | Stop-Process -Force" > /dev/null 2>&1
  sleep 1
  rm -rf "$WORK"
}
rm -rf "$WORK"
mkdir -p "$WORK/save"
WORK_WIN=$(cd "$WORK" && pwd -W)
trap stop_game EXIT
trap 'exit 130' INT TERM
cp "$GAME_DIR/$EXE" "$GAME_DIR"/*.dll "$WORK/" || exit 1
for d in config font themes text script music pak128 addons; do
  [ -d "$GAME_DIR/$d" ] && { cp -r "$GAME_DIR/$d" "$WORK/" || exit 1; }
done
rm -f "$WORK"/addons/pak128/ami*.pak
cp "$GAME_DIR/save/$SAVE.sve" "$WORK/save/" || exit 1
for p in $PAKS; do cp "$p" "$WORK/addons/pak128/" || exit 1; done
[ -f "$GAME_DIR/settings.xml" ] && { cp "$GAME_DIR/settings.xml" "$WORK/settings.xml"; chmod u+w "$WORK/settings.xml"; }
(cd "$WORK" && "./$EXE" -objects pak128/ -addons -load "$SAVE" -log 1 -debug 3 -mcp-port "$PORT" > /dev/null 2>&1 &)
up=""
for r in $(seq 1 120); do timeout 10 $M --timeout 5 --run-squirrel "return 1;" > /dev/null 2>&1 && { up=1; break; }; sleep 1; done
[ -n "$up" ] || { echo "[beta] ゲームが起動しなかった"; exit 1; }
sleep 3

# 敷く物の一覧: [名前, obj, waytype, system_type]
ITEMS=$(for f in src/*.dat; do
  case $f in *ex_donors.dat) continue ;; esac
  awk -F= 'tolower($1)=="obj"{o=$2} tolower($1)=="name"{n=$2} tolower($1)=="waytype"{w=$2} tolower($1)=="system_type"{s=$2}
    END{gsub(/\r/,"",o); gsub(/\r/,"",n); gsub(/\r/,"",w); gsub(/\r/,"",s); if (s=="") s=0; printf "[\"%s\",\"%s\",\"%s\",%s],", n, o, w, s}' "$f"
done | sed 's/,$//')
SQ=$(sed -e '/^[[:space:]]*\/\//d' -e '/^[[:space:]]*$/d' -e "s/^local ITEMS = .*/local ITEMS = [$ITEMS];/" "$NUT")
RESULT=$(python -X utf8 -c "import json,sys; print(json.load(sys.stdin).get('result'))" <<< "$($M --timeout 300 --run-squirrel "$SQ")")
echo "$RESULT"
fail=0
[ "${RESULT#ok }" != "$RESULT" ] || fail=1
# ログ（-debug 3 で警告と読み込みの行まで出す。段を下げると 1 行しか出ず、二重に読んだ物の overlaid の警告も出ない）
LOG="work/beta_game/simu_$PORT.log"
[ -f "$WORK/simu.log" ] && cp "$WORK/simu.log" "$LOG"  # 写しを消した後も読めるように
if [ -f "$LOG" ] && grep -aq "obj_reader_t::read_file" "$LOG"; then
  echo "[beta] 読んだ AMI の pak: $(grep -aoE "addons/pak128/ami[a-z_]*\.pak" "$LOG" | sort -u | tr '\n' ' ')"
  echo "[beta] ログの警告・エラー（AMI の物の名前 ami_ を含む行。全体は $LOG）:"
  if grep -aiE "warning|error" "$LOG" | grep -aE "ami_"; then fail=1; else echo "  なし"; fi
else
  echo "[beta] ログに pak の読み込みの行が無い（ログを読めなかった。$LOG）"
  fail=1
fi
exit $fail  # 敷けない物か、AMI の物の警告があれば 1（trap でゲームを閉じる）
