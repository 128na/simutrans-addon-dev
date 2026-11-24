// 斜めの運河の並びの確かめ（#217。2026-11-24）: 景観の運河を (OX,OY) から (OX+4,OY+4) へ敷き、通ったタイルの get_dirs を返す。
// 12（南＋西）= diagonal[sw]、3（北＋東）= diagonal[ne] が交互に並ぶ。flat_512_left_v64 は 512 四方なので OY は 100 など範囲内にする。
// 使い方: GAME_DIR=… PORT=47200 NUT=ingame/canal_diag_probe.nut bash ingame/game.sh（出力はファイルへ。終わったら PORT=47200 … STOP）
local pl = player_x(0);
local W = way_desc_x("ami_canal_scenic");
local report = "";
local OX = 30;
local OY = 100;
local e = command_x.build_way(pl, coord3d(OX, OY, 0), coord3d(OX + 4, OY + 4, 0), W, true);
report += "build=[" + (e == null ? "ok" : e) + "]\n";
for (local i = -1; i <= 5; i++) {
  for (local j = -1; j <= 5; j++) {
    local t = square_x(OX + i, OY + j).get_ground_tile();
    local w = t.get_way(wt_water);
    if (w != null) report += "(" + i + "," + j + ") dirs=" + w.get_dirs() + "\n";
  }
}
return report;
