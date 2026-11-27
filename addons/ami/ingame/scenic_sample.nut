// 景観の補助（#372）の見本: ラウンドアバウトの路面表示（ami_mark_roundabout）・説明用の色の way（ami_describe_*）・盛土の建物の版。
// 検証用の flat_512_left_v64.sve に、温暖側 (20,20) と降雪側 (276,20) の 2 か所へ同じ並びで敷き、降雪側は一帯を降雪に塗り直す。
// 使い方（アドオンのディレクトリで）: sample_parallel.sh に NUT=ingame/scenic_sample.nut を付ける（撮る場所は sample_spots.sh の SCENIC_SPOTS）。
// 返り値の先頭が ok なら全部敷けた。違えば先頭が check で、「名前 場所=[…]」が続く。最後に [check] の行が続く。
// 区画（原点から）:
//   RA: ラウンドアバウト。中心 (6,6)。一般道路を 3x3 の輪と 4 本の腕（中心から 5 マスまで）に敷き、表示を輪・中心・腕の 1 マス目に重ねる
//   DG: 地上の説明用の線（y 2〜）。赤・青・緑・黄を東西の直線・曲がり・T字・十字で。x 18〜
//   DE: 高架の説明用の線（赤・青は y 18〜、緑・黄は y 18 の x 26〜36）
//   MB: 盛土の建物。中心 (40,8) の周りに 3x3 の輪（直線 4 向きと角 4 向き）。中心は空き
//   EW: 盛土の way（back・front）と並べて比べる (48,5)〜(48,12)
local ORIGINS = [[20, 20], [276, 20]];
local SNOW = 1;
local AREA = [[-3, -4], [60, 24]];
local G = "ami_road_general", RA = "ami_mark_roundabout";
local pl = player_x(0);
local pub = player_x(1);
local report = "";
local checks = "";
local OX = 0, OY = 0;
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
function c(x, y) { return coord3d(OX + x, OY + y, 0); }
function way(tag, n, x0, y0, x1, y1) {
  local w = way_desc_x(n);
  if (w == null) { report += n + " desc=[missing]\n"; return; }
  report += r(tag + " " + n, command_x.build_way(pl, c(x0, y0), c(x1, y1), w, true));
}
function house(tag, n, x, y, rot) {
  report += r(tag + " " + n + " " + x + "," + y, command_x(tool_build_house).work(pub, c(x, y), "1" + rot + n));
}
function info(tag, x, y) {
  local t = square_x(OX + x, OY + y).get_ground_tile();
  local m = t.get_way(wt_rail), w = t.get_way(wt_road);
  checks += "[check] " + tag + " (" + x + "," + y + ") road=" + (w == null ? "-" : w.get_desc().get_name() + "/d" + w.get_dirs()) +
    " tram=" + (m == null ? "-" : m.get_desc().get_name() + "/d" + m.get_dirs()) + "\n";
}

foreach (n, o in ORIGINS) {
  OX = o[0]; OY = o[1];
  // ラウンドアバウト。輪は辺ごとに敷く（角が曲がりになる）。腕は辺の中央から外へ（辺の中央が T字になる）
  foreach (w in [G, RA]) {
    way("RA", w, 5, 5, 7, 5); way("RA", w, 7, 5, 7, 7); way("RA", w, 7, 7, 5, 7); way("RA", w, 5, 7, 5, 5);
  }
  way("RA", G, 7, 6, 11, 6); way("RA", G, 5, 6, 1, 6); way("RA", G, 6, 5, 6, 1); way("RA", G, 6, 7, 6, 11);
  way("RA", RA, 7, 6, 8, 6); way("RA", RA, 5, 6, 4, 6); way("RA", RA, 6, 5, 6, 4); way("RA", RA, 6, 7, 6, 8);
  way("RA", RA, 6, 6, 6, 6);
  foreach (p in [[6, 6], [5, 5], [7, 5], [6, 5], [7, 6], [8, 6], [6, 8]]) info("RA", p[0], p[1]);
  // 地上の説明用の線
  foreach (i, col in ["red", "blue", "green", "yellow"]) {
    local name = "ami_describe_" + col, y = 1 + 4 * i;
    way("DG", name, 18, y, 24, y);
    way("DG", name, 21, y, 21, y + 2);
    way("DG", name, 26, y, 28, y);
    way("DG", name, 28, y, 28, y + 2);
  }
  info("DG", 21, 1);
  // 高架の説明用の線
  way("DE", "ami_describe_red_elev", 18, 18, 24, 18);
  way("DE", "ami_describe_blue_elev", 21, 18, 21, 21);
  way("DE", "ami_describe_green_elev", 26, 18, 30, 18);
  way("DE", "ami_describe_yellow_elev", 32, 18, 36, 18);
  // 高架に載れば、地面のタイルに way は無い（[check] の DE は road=- tram=-）
  info("DE", 19, 18); info("DE", 21, 20);
  // 盛土の建物の輪（直線の layout 0 南・1 東・2 北・3 西、角の高い角は 0 北西・1 南西・2 南東・3 北東）
  local B = "ami_embankment_building", K = "ami_embankment_building_corner";
  house("MB", K, 39, 7, 2); house("MB", B, 40, 7, 2); house("MB", K, 41, 7, 1);
  house("MB", B, 39, 8, 3);                          house("MB", B, 41, 8, 1);
  house("MB", K, 39, 9, 3); house("MB", B, 40, 9, 0); house("MB", K, 41, 9, 0);
  // 比べ: 盛土の way
  way("EW", "ami_embankment_back", 48, 5, 48, 12);
  way("EW", "ami_embankment_front", 50, 5, 50, 12);
  if (n == SNOW)
    report += r("climate", command_x(tool_set_climate).work(pl, c(AREA[0][0], AREA[0][1]), c(AREA[1][0], AREA[1][1]), "7"));
}
gui.close_all_windows();
return (report == "" ? "ok\n" : "check\n" + report) + checks;
