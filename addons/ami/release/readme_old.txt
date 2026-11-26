AMI（AI Marunage Infrastructure）{version}

旧描画位置の線路です。SIS など、レールが地面の位置にある旧描画位置の線路につなぐための別配布で、
同じ版のほかの AMI の zip（この zip の名前から -old を除いたもの）と一緒に使います。新描画位置の線路（pak128 標準・ISS に合う）には入れないでください。

■ 注意点
まだベータ版です。設定値は仮です。
旧描画位置の線路は、新描画位置の線路とつなぐと、レールが数 px ずれて見えます。別の物として使ってください。
旧の線路の高架・橋・トンネル・壁・橋脚もこの pak だけで完結します。旧の線路には踏切を作っていません。

■ 動作確認

- Simutrans OTRP（pak128）v63.3以降
- Simutrans 本家 125.0.1（pak128）

■ 導入方法

zip の中の pak128 フォルダを、Simutrans の addons フォルダ（無ければ作る）に入れてください。
  例: <Simutrans のフォルダ>/addons/pak128/ami_rail_old.pak
ami_rail_old.pak は旧の線路・壁・橋脚が入っていて、ami_extra.pak などは要りません。
すべての物の一覧は ami_lineup.txt にあります。

■ ライセンス

CC BY 4.0（ami_license.txt）。

■ 問い合わせ・不具合の報告

https://github.com/128na/simutrans-addon-dev/issues
