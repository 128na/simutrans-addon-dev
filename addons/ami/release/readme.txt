AMI（AI Marunage Infrastructure）{version}

pak128,128Japan 用のインフラアドオン集です。
いにしえの時代のインフラアドオンであるISSをベースにAI(claude)に丸投げしてリニューアルしたイマドキスタイルです。

最新リリースはGithubのReleaseに順次公開します。
https://github.com/128na/simutrans-addon-dev/releases

■ 注意点
まだベータ版です。ノリと勢いでアドオンが増えたり減ったりする場合があります。
設定値は仮です。クラッシュしなければどうということないという心持ちでご利用ください。
Y字、三方分岐などOTRPでのみ表示可能なものも含まれています。
道路標識の最高速度・一時停止は飾りで、車の速さは変わりません（効くのは一方通行と最低速度）。
版ごとの変更（増えた物・無くなった物）は、上の Release の各版の説明に書いています。

■ 動作確認

- Simutrans OTRP（pak128）v63.3以降
- Simutrans 本家 125.0.1（pak128）

■ 導入方法

zip の中の pak128 フォルダを、Simutrans の addons フォルダ（無ければ作る）に入れてください。
  例: <Simutrans のフォルダ>/addons/pak128/ami_rail.pak
pak は種類ごとに分かれています。使わない種類は入れなくてもかまいませんが、ami_extra.pak は線路・道路の壁と橋脚が入っているので、ami_rail.pak か ami_road.pak を使うときは一緒に入れてください。ami_maglev.pak の高架（超電導・チューブ式）の橋脚も ami_extra.pak に入っています。
主な中身は次のとおりです（すべてを載せてはいません。すべての物の一覧は ami_lineup.txt にあります）。

  ami_rail.pak   線路：地上・高架・橋・トンネル、車庫、操車場、転車台・遷車台（道路のメニュー）
  ami_road.pak   道路：地上・高架・橋・トンネル、多車線（6 車線まで）・交差点・高速道路の分岐と合流・路面の色（赤・青・緑・赤の縞）・黄色の中央線の路面表示（路面軌道のメニュー。一般道路・高速道路に重ねる）
  ami_tram.pak   路面軌道
  ami_monorail.pak  モノレール：跨座式・懸垂式、電化、車庫
  ami_canal.pak  運河：運河、景観の運河、船の車庫
  ami_maglev.pak  リニア：超電導（ガイド）・常電導・チューブ式（チューブ。電化しないので、電化の要る車両は走れません）、高架、トンネル、車庫（車両は入っていません）
  ami_narrow.pak  狭軌：30 km/h・60 km/h、トンネル、車庫（狭軌の車両は別のアドオンが要ります）
  ami_extra.pak  装飾パーツ：線路・道路の壁（架線つきの壁、中央分離帯つきの壁を含む）、橋脚、歩道、電柱など
  ami_scenery.pak  景観：盛土、道路標識（横断歩道を含む）
  pak128/text/ja_ami.tab  日本語の名前（道路標識）。pak128 フォルダと一緒に入ります

■ ライセンス

CC BY 4.0（ami_license.txt）。

■ 問い合わせ・不具合の報告

https://github.com/128na/simutrans-addon-dev/issues
