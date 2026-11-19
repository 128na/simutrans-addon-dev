# 作業ログ: AMI の道路の T字の分岐の絵（1・2）を T字の形にし、轍のカーブで分ける（#21・#22 の続き）

（2026-11-19）

## 目的 / 発端

[2026-11-19_ami-road-open-cross.md](2026-11-19_ami-road-open-cross.md) の後、ユーザーがゲームで見て指摘した（2026-11-19）:

1. 固定した T字の `sew2`（生活道路の区画 I、(64,43)）が十字の絵になっている。ほかの 3 方位の「2」も同じ
2. `sew1` は「左上」、`sew2` は「右下」なので、轍は添付の画像のように描く（`sew1` は直進と南–東のカーブ、`sew2` は直進と南–西のカーブ）
3. 「ゲームで見ていない」と挙げたもののうち、確かめられるものは確かめてから判断を仰ぐ

## 分かったこと（事実）

- 固定の道具の選択肢の名前（`128na/simutrans` の `feature/switch-image-override` の `gui/ground_info.cc` の `switch_choice_label`）は、選択 1（`apply_switch_image_override` で `nw` = true、dat の「2」）が sew は東、nse は南、new は西、nsw は北。選択 2（「1」）はその反対。ユーザーの「sew1 は左上、sew2 は右下」はこの名前と合う
- ユーザーの描いた轍は、枝と、名前の反対側の本線の端をつなぐ（`sew2`「東（右下）」は南–西）。本体のコメント（nse2 は南–東のカーブ）と、線路の分岐の絵（名前の側の端と枝をつなぐ。`docs/reference/way-addon.md` の 9.2）とは逆の向き。8 枚の対応は `addons/ami/README.md` の「T字の 1・2 の轍」の表
- 「2」を T字の形にすると、本体は ex 画像の無い道路の十字で、隣が T字か十字のときにその向きの T字の「2」を十字のタイルに出す（`select_switch_road_image` の `ribi_t::all`）ので、多車線の十字で横切る道路の側に実線が出る。前の T字の形の「2」と同じ（[2026-11-19_ami-road.md](2026-11-19_ami-road.md)）

## 直したこと

- `sheetlib` の `road_sheet` にキー `switch_ruts` を足した。T字の 1・2 をどちらも「1」の白線（枝の無い側は実線、枝の口の点線なし）にし、走行跡（`weathering` の部品）を直進と、`road_parts` の `SWITCH_RUT_ARCS` のカーブ 1 本にする。`switch2_cross` と一緒には使えない。blender-poc はキーを持たないので変わらない
- AMI の道路 3 種のプロファイルを `switch2_cross` から `switch_ruts` に替え、通常の版・基盤の版・高架の版を描き直した

## 確かめたこと

- `SHEET_LAYOUT=1` で一般道路の T字・1・2 のセルを描き、轍のカーブの向きを 8 枚とも見てから塗った
- 前のシートと比べ、通常の版で変わったのは T字の 1・2 のセル（列 10〜13、奥と雪の行）だけで、透過の範囲は変わらない（`tools/blender/sheet_diff.py`）
- ゲーム（`OTRPv64_3.exe`、`flat_512.sve`、`road_sample.nut`）: 区画 H の自動の「1」が固定の選択 2 と同じ絵で、通常の T字と違うこと（`[check]` の `ok`、3 種）。区画 I の 8 枚を 1 枚ずつ画面の中ほどに置いて撮り、3 倍で轍の向きが表のとおりであることを見た（`addons/ami/docs/road_{LO,GE,EX}_pin_tees.png`）
- 区画 L と `road_junction_sample.nut` の 4×2・4×4・6×6 で、十字のタイルに T字の「2」が出て、横切る道路の側に実線が引かれることを見た（`road_L_tee2_auto.png`・`road_GE_junction_tee2.png`）。4×2 は `nse2 nsw2`、6×6 はどの行も `nse2 nse2 nsw2`

## 見ていないこと

- タイルの詳細ダイアログでの選択の見た目（MCP ではダイアログを開けない）
