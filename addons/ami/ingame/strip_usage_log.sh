#!/usr/bin/env bash
# 写した settings.xml から、OTRP の使用状況の送信用の記録を空にする（#235）。
# OTRP の本体は、settings.xml の送信用の記録（env_t::otrp_statistics_log。<![CDATA[/registerOTRPUsage?...]]> の行）が
# 空でないと、起動のたびに使用状況を外へ送る。記録は終了のたびに書き出されるので、起動の前に毎回呼ぶ。
# 空にすると、起動のログ（-debug 3）に "statistics log is not send." が出る。
# 使い方: bash strip_usage_log.sh <写した settings.xml>（無ければ何もしない）。検証環境の本物の settings.xml には使わない。
f=${1:?usage: strip_usage_log.sh <settings.xml>}
[ -f "$f" ] || exit 0
sed -i 's#<!\[CDATA\[/registerOTRPUsage[^]]*\]\]>#<![CDATA[]]>#' "$f"
if grep -q registerOTRPUsage "$f"; then echo "strip_usage_log: 送信用の記録が残っている: $f" >&2; exit 1; fi
