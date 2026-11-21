AMI（AI Marunage Infrastructure）{version}

pak128,128Japan 用のインフラアドオン集です。
いにしえの時代のインフラアドオンであるISSをベースにAI(claude)に丸投げしてリニューアルしたイマドキスタイルです。

最新リリースはGithubのReleaseに順次公開します。
https://github.com/128na/simutrans-addon-dev/releases

■ 注意点
まだベータ版です。ノリと勢いでアドオンが増えたり減ったりする場合があります。
設定値は仮です。クラッシュしなければどうということないという心持ちでご利用ください。
Y字、三方分岐などOTRPでのみ表示可能なものも含まれています。

■ 動作確認

- Simutrans OTRP（pak128）v63.3以降
- Simutrans 本家 125.0.1（pak128）

■ 導入方法

zip の中の pak128 フォルダを、Simutrans の addons フォルダ（無ければ作る）に入れてください。
  例: <Simutrans のフォルダ>/addons/pak128/ami_rail.pak
pak は種類ごとに分かれています。使わない種類は入れなくてもかまいませんが、ami_extra.pak は線路・道路の壁と橋脚が入っているので、ami_rail.pak か ami_road.pak を使うときは一緒に入れてください。
主な中身は次のとおりです（すべてを載せてはいません。すべての物の一覧は ami_lineup.txt にあります）。

  ami_rail.pak   線路：地上・高架・橋・トンネル
  ami_road.pak   道路：地上・高架・橋・トンネル
  ami_tram.pak   路面軌道
  ami_extra.pak  装飾パーツ：線路・道路の壁（架線つきの壁を含む）、橋脚、歩道など
  ami_scenery.pak  景観：盛土

■ ライセンス

CC BY 4.0（ami_license.txt）。

■ 問い合わせ・不具合の報告

https://github.com/128na/simutrans-addon-dev/issues
