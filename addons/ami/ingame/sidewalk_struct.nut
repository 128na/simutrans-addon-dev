// AMI の歩道の種類・高架の歩道・歩道の柵の見本（#119）。ingame/game.sh で flat_512_left_v64.sve に流す（降雪側は OX=276 を渡す。敷いた後に一帯を降雪に塗る）。
// 区画（原点 (OX,OY) から）:
//   P 舗装の種類: 12 ずつ東へ ami_sidewalk・_asphalt・_brick・_tile。東西の一般道路 (x,2)-(x+8,2) の両脇 (·,1)・(·,3) に歩道、(x+2..x+4, 5..7) に 3x3 の広場
//   F 柵（地上）: F1 南北の一般道路 (2,12)-(2,22) の東 (3,·) に back、西 (1,·) に front（どちらも道路の側の辺）
//     F2 L字 (8,12)-(14,12)-(14,18) に single。F3 3x3 の広場 (18..20, 12..14) に single。F5 T字 (38,12)-(44,12) と (41,12)-(41,16) に single
//     F4 坂: 南北の一般道路 (26,·)・(32,·) の両脇の歩道（東 back・西 front）。(·,15) を 1 段（26）・2 段（32）上げた坂
//   E 高架: E1 東西の一般道路の高架 (0,28)-(10,28) の両脇 (·,27)・(·,29) に高架の歩道と柵（北 back・南 front）。真下の地面に ami_pier_road
//     E2 南北の地上の一般道路 (16,25)-(16,33) の上を横切る高架の歩道 (13,29)-(20,29) に single。E3 L字 (24,27)-(30,27)-(30,32) に single（橋脚つき）
// 返り値の先頭が ok なら全部敷けた。[check] の行は、高架の歩道のタイル（z=2）の way と柵、地上の道路のタイルの way 2 本の有無
local OX = 20;
local OY = 20;
local pl = player_x(0);
local report = "";
local checks = "";
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
function c(x, y, z = 0) { return coord3d(OX + x, OY + y, z); }
function wd(n) { local d = way_desc_x(n); if (d == null) report += n + " desc=[missing]\n"; return d; }
local OBJS = {};
foreach (d in wayobj_desc_x.get_available_wayobjs(wt_water)) OBJS[d.get_name()] <- d;
function od(n) { if (!(n in OBJS)) { report += n + " wayobj=[missing]\n"; return null; } return OBJS[n]; }
function way(d, x0, y0, x1, y1) { return command_x.build_way(pl, c(x0, y0), c(x1, y1), d, true); }
function fence(d, x0, y0, x1, y1, z = 0) { return command_x.build_wayobj(pl, c(x0, y0, z), c(x1, y1, z), d); }
local road = wd("ami_road_general");
local relev = wd("ami_road_general_elev_single");
local pier = wd("ami_pier_road");
local selev = wd("ami_sidewalk_elev");
local fs = od("ami_wall_sidewalk_single"), fb = od("ami_wall_sidewalk_back"), ff = od("ami_wall_sidewalk_front");
local marker = command_x(tool_set_marker);

// P
foreach (i, n in ["ami_sidewalk", "ami_sidewalk_asphalt", "ami_sidewalk_brick", "ami_sidewalk_tile"]) {
  local d = wd(n), x = i * 12;
  report += r("P label", marker.work(pl, c(x, -2), n));
  report += r("P road", way(road, x, 2, x + 8, 2));
  report += r("P side1", way(d, x, 1, x + 8, 1));
  report += r("P side3", way(d, x, 3, x + 8, 3));
  for (local k = 0; k < 3; k++) {
    report += r("P plaza ew", way(d, x + 2, 5 + k, x + 4, 5 + k));
    report += r("P plaza ns", way(d, x + 2 + k, 5, x + 2 + k, 7));
  }
}
local sw = wd("ami_sidewalk");
// F1
report += r("F1 road", way(road, 2, 12, 2, 22));
report += r("F1 sideE", way(sw, 3, 12, 3, 22));
report += r("F1 sideW", way(sw, 1, 12, 1, 22));
report += r("F1 back", fence(fb, 3, 12, 3, 22));
report += r("F1 front", fence(ff, 1, 12, 1, 22));
// F2
report += r("F2 a", way(sw, 8, 12, 14, 12)); report += r("F2 b", way(sw, 14, 12, 14, 18));
report += r("F2 fa", fence(fs, 8, 12, 14, 12)); report += r("F2 fb", fence(fs, 14, 12, 14, 18));
// F3
for (local k = 0; k < 3; k++) {
  report += r("F3 ew", way(sw, 18, 12 + k, 20, 12 + k));
  report += r("F3 ns", way(sw, 18 + k, 12, 18 + k, 14));
}
for (local k = 0; k < 3; k++) {
  report += r("F3 few", fence(fs, 18, 12 + k, 20, 12 + k));
  report += r("F3 fns", fence(fs, 18 + k, 12, 18 + k, 14));
}
// F4
foreach (h in [[26, 1], [32, 2]]) {
  local cx = h[0], n = h[1];
  for (local x = cx - 1; x <= cx + 1; x++) {
    for (local j = 0; j < n; j++) report += r("F4 raise", command_x.set_slope(pl, c(x, 15, j), slope.all_up_slope));
    report += r("F4 rampN", command_x.set_slope(pl, c(x, 14), 4 * n));
    report += r("F4 rampS", command_x.set_slope(pl, c(x, 16), 36 * n));
  }
  report += r("F4 road", way(road, cx, 12, cx, 18));
  report += r("F4 sideW", way(sw, cx - 1, 12, cx - 1, 18));
  report += r("F4 sideE", way(sw, cx + 1, 12, cx + 1, 18));
  report += r("F4 back", fence(fb, cx + 1, 12, cx + 1, 18));
  report += r("F4 front", fence(ff, cx - 1, 12, cx - 1, 18));
}
// F5
report += r("F5 a", way(sw, 38, 12, 44, 12)); report += r("F5 b", way(sw, 41, 12, 41, 16));
report += r("F5 fa", fence(fs, 38, 12, 44, 12)); report += r("F5 fb", fence(fs, 41, 12, 41, 16));
// E1
report += r("E1 road", way(relev, 0, 28, 10, 28));
report += r("E1 sideN", way(selev, 0, 27, 10, 27));
report += r("E1 sideS", way(selev, 0, 29, 10, 29));
report += r("E1 pier", way(pier, 0, 28, 10, 28));
report += r("E1 back", fence(fb, 0, 27, 10, 27, 2));
report += r("E1 front", fence(ff, 0, 29, 10, 29, 2));
// E2
report += r("E2 road", way(road, 16, 25, 16, 33));
report += r("E2 side", way(selev, 13, 29, 20, 29));
report += r("E2 fence", fence(fs, 13, 29, 20, 29, 2));
report += r("E2 pierW", way(pier, 13, 29, 15, 29));
report += r("E2 pierE", way(pier, 17, 29, 20, 29));
// E3
report += r("E3 a", way(selev, 24, 27, 30, 27)); report += r("E3 b", way(selev, 30, 27, 30, 32));
report += r("E3 fa", fence(fs, 24, 27, 30, 27, 2)); report += r("E3 fb", fence(fs, 30, 27, 30, 32, 2));
report += r("E3 pa", way(pier, 24, 27, 30, 27)); report += r("E3 pb", way(pier, 30, 27, 30, 32));

function wayobj_name(t) {
  if (t == null) return "-";
  local o = t.find_object(mo_wayobj);
  return o == null ? "-" : o.get_desc().get_name();
}
foreach (p in [[5, 27], [5, 29], [16, 29], [27, 27], [30, 27]]) {
  local t = square_x(OX + p[0], OY + p[1]);
  local h = t.get_tile_at_height(2), g = t.get_ground_tile();
  local hw = h == null ? null : h.get_way(wt_water);
  checks += "[check] (" + p[0] + "," + p[1] + ") z2=" + (hw == null ? "-" : hw.get_desc().get_name() + "/d" + hw.get_dirs()) + " fence=" + wayobj_name(h)
            + " ground two_ways=" + g.has_two_ways() + "\n";
}
foreach (p in [[3, 15], [1, 15], [14, 12], [27, 15]]) {
  local g = square_x(OX + p[0], OY + p[1]).get_ground_tile();
  local w = g.get_way(wt_water);
  checks += "[check] (" + p[0] + "," + p[1] + ") ground=" + (w == null ? "-" : w.get_desc().get_name() + "/d" + w.get_dirs()) + " fence=" + wayobj_name(g) + "\n";
}
if (OX >= 256)  // 降雪側は OX=276。200 で比べると温暖側の x=200〜255 に置いたときに雪になる（#398）
  report += r("climate", command_x(tool_set_climate).work(pl, c(-2, -6), c(50, 36), "7"));
gui.close_all_windows();
return (report == "" ? "ok\n" : "check\n" + report) + checks;
