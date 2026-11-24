# 調査/作業ログ: 本体に登録された名前の一覧と makeobj list を比べる検査（#245）

（2026-11-24）

## 目的 / 発端

[#236](https://github.com/128na/simutrans-addon-dev/issues/236) の検査（[2026-11-24_headless-pak-load](2026-11-24_headless-pak-load.md)）は、出力の文字列で読み込みの誤りを見つける。半分で切れた pak のように、本体が何も出さずに物を捨てる壊れ方は見つけられない（同記録の「壊した pak の結果」）。その第 2 段として、本体に登録された名前の一覧を出し、`makeobj list` と比べる（[#245](https://github.com/128na/simutrans-addon-dev/issues/245)）。

## 分かったこと（事実）

- 作り: `tools/ci/pak_names_scenario/`（`scenario.nut` と、本体の `tests/automated-tests/empty-16x16.sve` の写し 1979 バイト）を、起動のたびに作業フォルダへ置き、`-scenario pakchk` で動かす。scenario は `PAKNAMES <種類> <名前>` の行と、終わりの `PAKNAMES done` を出す。`check_pak_load.py` は `--makeobj makeobj` を渡されると、この合図を終わりの印にして、名前を `makeobj list` と比べる。
- 本体の API で出せる種類: way（`way_desc_x.get_available_ways(wt, st)`。waytype 9 種 × st_flat・st_elevated・st_tram）・way-object・tunnel・bridge・roadsign（waytype ごと）・building（`building_desc_x.get_building_list`。駅・車庫・桟橋・駅の拡張は、どの種類を渡しても同じ一覧）。**crossing（踏切）は一覧の API が無い**ので比べない（件数だけ出す。AMI は 19 個）。
- 今の AMI の `dist/` で一致した: 種類別の 8 本で 214 個、全部入りの `ami.pak` で 158 個（`ami_rail_old` は種類別だけ）。way は `get_builder()` が要る（アイコンの無い way は一覧に出ない）が、AMI の way は全部アイコンがあり、差は出なかった。
- 一覧は年表（timeline）で絞られる。AMI の dat は `intro_year` が 1900〜2000。scenario の地図は年表が無効なので全部出る。scenario が年表の有効・無効を出し、有効なら検査を失敗にする（地図を差し替えたときに、黙って足りなくならないように）。
- 「余る」は、pakset だけで起動した一覧（基準）を引いて求める。基準の起動を 1 回余分に走らせる（1 回の実行の中で使い回す。約 3 秒）。
- **scenario の置き場**: 本体は `addons/<pak>/scenario/` を先に探し、無ければ pakset の `pak/scenario/` を探す。先に探して無いと `ERROR: scenario_t::load_script` が出る（失敗の判定に引っかかる）。ただし `addons/pak/` に物が無いとき（基準の起動）は先を探さない。**両方に置く**と、どちらでも ERROR は出ない。
- 壊した pak の結果（`ami_monorail.pak` から。`--self-test --makeobj`）:

  | 壊し方 | 結果 |
  |---|---|
  | ROOT の最後の物（WAY）を削り、ROOT の子の数を 1 減らす（出力には何も出ない） | 失敗: `pak にあるが登録されていない: way-object ami_monorail_suspended_power`（削った WAY の子の way-object。1 つだけ） |
  | ファイルの半分で切る | 失敗: way 5 個と way-object 1 個が登録されない |
  | `makeobj list` の側を 1 つ少なくする（逆向き） | 失敗: `pak に無いのに登録されている` |
  | 元の pak | 通る（14 個） |

  空・ROOT の大きさ・参照切れ・名前の重複は、今までどおり読み込みの出力で失敗する（空の pak は、一覧の比較でも「登録されていない」が出る）。
- 手元は Windows（`HEADLESS_SIM_BIN`・`HEADLESS_PAKSET` を渡したとき）で、`check.sh` 全体が通った。

## 推測・未確認事項

- CI（Linux）での通過。CI の `makeobj` は本家 125.0 の 60.10 で、手元は 60.12。`list` の出力の形が同じことは、PR の CI で確かめる。
- CI の本体のコミット（`ci.env` の `HEADLESS_SIM`）は、手元で使った本体より古い。scenario の API 名（`wayobj_desc_x`・`sign_desc_x`・`building_desc_x.get_building_list`）が通ることも CI で確かめる。
- 余る側の確かめは、基準との差で求めるので、pakset が pak と同じ名前を持つとき（上書き）は見えない（名前の重複の検査が先に失敗にする）。

## 結果どうしたか

`tools/ci/check_pak_load.py` に `--makeobj` を足し、`addons/ami/check.sh` の 3 つの呼び出し（種類別・全部入り・`--self-test`）に渡した。CI は `check.sh` を回すので、そのまま動く。使い方は `addons/ami/README.md` の「画面を出さない本体での読み込みの検査」。
