# 調査/作業ログ: 一般道路・生活道路の基盤・高架を single だけにして、カーブをそろえる（#260）

## 目的 / 発端

#209 の 3 本目。ユーザーの判断（2026-11-24）「バリエーションを減らして整理したい。center などの 4 種類→single のみ、橋、トンネルは残しカーブはそろえる」により、一般道路（`ami_road_general`）・生活道路（`ami_road_local`）の基盤・高架の `back`・`center`・`front`（12 個）を消し、残す `single` のカーブを地上の版（#259 の円弧・L 字）にそろえる。高速道路・幹線道路は変えない。

## 分かったこと（事実）

- 橋（`_bridge`）はセルが直線と坂だけ、トンネル（`_tunnel`）は坑口の 4 向きだけで、カーブのセルが無い。そろえる対象は、基盤と高架の `single`（一般・生活の 2 道路 × 2 種）だった。
- 壁（`ami_wall_road_single`）は way-object で、4 道路で 1 つを共有していた。way-object は 1 タイルに 1 つで、カーブのセルは斜めの形。円弧・L 字の基盤に重ねるとカーブで合わない。壁の方針は、ユーザーの判断（2026-11-24「お勧めでOK」）で、カーブの形ごとの壁を足す案にした: `ami_wall_road_single_arc`（一般道路用）・`ami_wall_road_single_ell`（生活道路用）。直線・T字・十字・坂・端の壁は `ami_wall_road_single` と同じ絵で、カーブのセル（行 2 の列 5〜8）だけが違う。もう 1 つの案（壁を way の絵に焼き込む）は、橋・トンネルの壁と扱いが食い違い、壁を way-object に分けた方針（ADR 0003）から外れるので採らなかった。
- 基盤の版は「通常の版の路面から、壁の外側を削る」作りで、削る型は `sheetlib/assemble.py` の `_beyond_prisms`。円弧・L 字の経路を壁に通すと、型が壊れた:
  - L 字（`MiterPath`。経路の点が 3 つ）は、直線の枝に落ちて、始点と終点を結ぶ斜めの線で外側を削った。タイルの半分（三角）が消え、壁の頂点の内側に草の三角が出た。直し: 点が 3 つの経路は、2 本の直線（辺の中点→中心、中心→辺の中点）として、それぞれの外側を削る。
  - 円弧の外側は、64 個の薄い柱（半径 r+uw〜40 の輪を 64 等分）を 1 つずつ抜く作りで、路面が扇形に欠け、白線の脇に細い透明のすき間が出た（ゲームでは草の筋）。型を 4 個の大きな柱（16 区間ずつ）にまとめると、欠けもすき間も出ない（削る範囲は同じ）。外側を全く削らないと扇形もすき間も出ないが、壁の外側（遠い角の三角）まで路面が残る。
- 消した 12 個: `ami_road_<general|local>_<base|elev>_<back|center|front>`。`Road.variants`（`catalog.py`。一般・生活は `("single",)`、幹線・高速は 4 版）で道路ごとに版を持たせ、`BUILT_WAYS`・dat・`render.py` の対象・見本の棚が読む。dat の突き合わせ（`check.sh`）で、dat が 12 個減る以外の差が無いことを見た。
- 12 個の訳の行は、#265（#263）では足していなかった（`release/text/ja_ami.tab` に無い）ので、消す行は無かった。壁 2 個の訳の行を足した。
- 見本を直した: `road_struct_sample.nut`（一般・生活は複線・T3 を敷かない。`single` の壁をカーブの形ごとの壁に替える）、`divider_sample.nut`（分離帯は幹線・高速だけ）、`pole_sample.nut`・`sidewalk_struct.nut`（`elev_center` → `elev_single`）、`embankment_sample.nut`（一般の高架にカーブの壁）、`curve_sample.nut`（基盤 single と壁で敷ける。`WALLED`。前の pak との比べ用に、カーブの形ごとの壁が無いときは `ami_wall_road_single`）、`sample_spots.sh`、`ingame/catalog.py`（カタログの棚）、`icon_capture.sh`（メニューの位置。道路メニューが短くなって並びが変わった）。
- ゲーム（`OTRPv64`、`flat_512_left_v64.sve`、温暖 (20,20) と降雪 (276,20)）で、`curve_sample.nut`（輪・2 本並べた輪・坂の隣・斜めの継ぎ目・T字の隣）と `road_struct_sample.nut`（高架・橋・トンネル）を、前（main の pak）と後で撮って比べた。円弧・L 字の基盤 single に、カーブの形ごとの壁がそろって立つ（画像は `addons/ami/docs/260_road_single/`）。

## 推測・未確認事項

- 通常の版（壁なし）に壁を重ねると、一般道路の円弧のカーブでは、壁の外（遠い角）に路面の三角が出る（`docs/260_road_single/temperate_GE_WA_B.png` の輪の頂点。通常の版の路面はタイル全面なので）。壁は基盤の版と組む前提（README の「道路の壁・高架・橋脚・橋・トンネルの作り」）。
- 急坂（2 段）のすぐ隣のカーブ、右側通行の地図、夜の見え方は見ていない。
- 路面軌道を重ねたときの壁との重なりは見ていない（#259 では路面軌道だけ見た）。

## 結果どうしたか

- `tools/blender/sheetlib/assemble.py`（`_beyond_prisms`）、`addons/ami` の `blender/catalog.py`（`Road.variants`・`ROAD_WALL_CURVED`）・`ami_dat.py`・`render.py`、dat とシート（消した 12 個の dat・PNG、描き直した 4 枚と壁 2 枚）、`ingame/` の見本、README、リリースの `readme.txt`（消えた 12 個と、保存データは読み込めなくなること・置き換えはしないこと）を直した。
