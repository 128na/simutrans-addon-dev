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

■ ami-beta.3 からの変更（道路）

- 一般道路・生活道路（ami_road_general・ami_road_local）の基盤と高架を、single（両側に壁）だけにしました。奥だけ・手前だけ・壁なし（back・center・front）の版は無くなります。
  消えた物: ami_road_general_base_back・_base_center・_base_front、ami_road_general_elev_back・_elev_center・_elev_front と、生活道路（ami_road_local）の同じ 6 個（計 12 個）。
  幹線道路・高速道路は今までどおり 4 版です。
- 消えた物を使っていた保存データは読み込めなくなります（その区間は消えるか、読み込みに失敗します）。代わりの物への置き換えはしません（ベータ版のため）。必要なら single の版で敷き直してください。

■ 動作確認

- Simutrans OTRP（pak128）v63.3以降
- Simutrans 本家 125.0.1（pak128）

■ 導入方法

zip の中の pak128 フォルダを、Simutrans の addons フォルダ（無ければ作る）に入れてください。
  例: <Simutrans のフォルダ>/addons/pak128/ami_rail.pak
pak は種類ごとに分かれています。使わない種類は入れなくてもかまいませんが、ami_extra.pak は線路・道路の壁と橋脚が入っているので、ami_rail.pak か ami_road.pak を使うときは一緒に入れてください。
主な中身は次のとおりです（すべてを載せてはいません。すべての物の一覧は ami_lineup.txt にあります）。

  ami_rail.pak   線路：地上・高架・橋・トンネル、車庫、操車場
  ami_road.pak   道路：地上・高架・橋・トンネル、多車線（6 車線まで）・交差点・高速道路の分岐と合流の路面表示（路面軌道のメニュー。一般道路・高速道路に重ねる）
  ami_tram.pak   路面軌道
  ami_monorail.pak  モノレール：跨座式・懸垂式、電化、車庫
  ami_canal.pak  運河：運河、景観の運河、船の車庫
  ami_extra.pak  装飾パーツ：線路・道路の壁（架線つきの壁、中央分離帯つきの壁を含む）、橋脚、歩道、電柱など
  ami_scenery.pak  景観：盛土、道路標識（横断歩道を含む）
  pak128/text/ja_ami.tab  日本語の名前（道路標識）。pak128 フォルダと一緒に入ります

■ ライセンス

CC BY 4.0（ami_license.txt）。

■ 問い合わせ・不具合の報告

https://github.com/128na/simutrans-addon-dev/issues
