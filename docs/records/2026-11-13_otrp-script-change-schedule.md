# 調査/作業ログ: OTRP のスクリプトで編成のダイヤを設定できない（起票用のメモ）

（2026-11-13。対象は [addons/blender-poc](../../addons/blender-poc/README.md) の確認用スクリプト `ingame/train.nut`。
原因は特定していない。別途調査するための材料を残す）

## 目的 / 発端

側壁付きの線路で、カメラに近い側の壁が車両より手前に描かれるかを、車両を走らせて確かめたかった。
MCP（`--run-squirrel`）で車庫・駅・編成を作り、ダイヤを付けて出発させようとしたところ、ダイヤの設定だけが通らなかった。
確認そのものは、手で編成を走らせて済んだ（問題なし）。

## 再現手順

`flat.sve` を読み込んだゲームに、MCP で次を順に流す。

1. 線路・車庫・駅を作る（どれも成功する）

   ```
   local pl=player_x(0); local w=way_desc_x("bpoc_track_wall_single");
   command_x.build_way(pl, coord3d(100,40,0), coord3d(112,40,0), w, true);
   command_x.build_way(pl, coord3d(112,40,0), coord3d(112,48,0), w, true);
   command_x.build_depot(pl, coord3d(100,40,0), building_desc_x("TrainDepot"));
   local d=building_desc_x("train_platform_early");
   command_x.build_station(pl, coord3d(103,40,0), d);
   command_x.build_station(pl, coord3d(112,46,0), d);
   ```

2. 車庫に編成を作る（成功する。`get_convoy_list().len()` が 1 になる）

   ```
   depot_x(100,40,0).append_vehicle(player_x(0), convoy_x(0), vehicle_desc_x("1-3-1T_Sceccu"));
   ```

3. ダイヤを付ける（失敗する）

   ```
   local cnv=depot_x(100,40,0).get_convoy_list()[0];
   local s=schedule_x(wt_rail, [schedule_entry_x(coord3d(103,40,0),0,0), schedule_entry_x(coord3d(112,46,0),0,0)]);
   cnv.change_schedule(player_x(0), s);
   ```

## 結果

- 3 の `change_schedule` が、次の文字列を例外として返す:
  `Invalid schedule provided: less than two entries remained after removing doubles`
- 確かめたビルド: `sim-roundabout-plan3-tool.exe`（手元のビルド）と `sim-WinGDI64-OTRPv63_3.exe`（OTRP v63_3）。どちらも同じ
- 項目を変えても同じ: 駅 2 つ、線路の上の通過点 3 つ、`schedule_entry_x` を継承して欄を補ったクラス
- `schedule_x(...)` を作った直後の `s.entries.len()` は 2 で、スクリプトの側では項目が入っている
- 駅のタイルは `tile_x(103,40,0).get_halt() != null`、`get_way(wt_rail) != null`
- 作ったばかりの編成の `cnv.get_schedule()` は null を返す（これを書き換えようとすると「trying to set 'null'」のエラーの窓が出る。
  スクリーンショットに出ていたのはこのエラーで、ダイヤの設定の失敗とは別）
- ダイヤが無いまま `depot.start_convoy` を呼ぶと true が返るが、編成は車庫から出ない

## 見立て（未確認）

本体のソース（`script/api/api_convoy.cc` の `convoy_change_schedule`、`script/api/api_schedule.cc` の `param<schedule_t*>::get` と `append_entry`）を読んだ範囲では、
エラーの文字列は、スクリプトのダイヤを本体の `schedule_t` に写した後の項目数が 2 未満のときに出る。
つまり、項目を 1 つずつ足す `schedule_t::append`（`is_stop_allowed` の判定を含む）が失敗しているか、項目の読み出しの途中で止まっている。
どちらかは確かめていない。

## 次に調べるなら

- デバッグ出力（`-debug 3`）を付けて起動し、`schedule_t::append()` の「forbidden stop」が出ているかを見る
- 路線（`player_x.create_line` → `line_x.change_schedule`）でも同じかを見る
- OTRP ではない本家のビルド（`simutrans.exe`）で同じ手順を試す
- 再現できたら、OTRP のリポジトリに起票する（この文書の「再現手順」と「結果」をそのまま使える）
