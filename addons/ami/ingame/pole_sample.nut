// AMI の電柱の見本（#120）。ingame/game.sh で flat_512.sve に流す（降雪側は OX=276 を渡す。敷いた後に一帯を降雪に塗る）。
// 区画（原点 (OX,OY) から）:
//   A 東西の一般道路 (2,2)-(16,2) の両脇の歩道。北 (·,1): x2〜8 に電柱 front（柵なし。柱は道路の側）、x9〜16 に柵つきの電柱 front（道路の側の辺に柵）。
//     南 (·,3): 全部に柵 back を敷いた後、x9〜16 に柵つきの電柱 back を重ねる（置き換わる）。x4〜5 に電柱 back を重ねる（柵と同じ速さなので置き換わらない）
//   B 南北の一般道路 (22,0)-(22,12) の両脇の歩道。西 (21,·) に柵つきの電柱 front、東 (23,·) に柵つきの電柱 back（どちらも道路の側の辺に柵）
//   C 曲がり・分岐: L字 (28,1)-(34,1)-(34,7) に柵つきの電柱 front、T字 (38,1)-(44,1) と (41,1)-(41,5) と十字 (48,3)-(54,3) と (51,0)-(51,6) に電柱 front
//   D 坂: 南北の歩道 (60,0)-(60,8) に電柱 front。(·,4) を 1 段上げた坂（x59〜61）。急坂は (66,·) に 2 段
//   E 高架: 東西の一般道路の高架 (2,10)-(12,10) の北 (·,9) に高架の歩道と柵つきの電柱 front、南 (·,11) に電柱 back。真下の地面に ami_pier_road
//   F 架線と比べる: 東西の線路 (2,15)-(16,15)（ami_rail_ballast_base_single と架線つきの壁 single）の北 (·,14) の歩道に柵つきの電柱 front（電柱の高さを架線の柱と比べる。#120）
// 返り値の先頭が ok なら全部敷けて、[check] の期待どおり。違えば先頭が check で、「名前 場所=[…]」が続く。最後に [check] の行が続く
local OX = 20;
local OY = 24;
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
function obj(d, x0, y0, x1, y1, z = 0) { return command_x.build_wayobj(pl, c(x0, y0, z), c(x1, y1, z), d); }
local road = wd("ami_road_general");
local relev = wd("ami_road_general_elev_center");
local pier = wd("ami_pier_road");
local sw = wd("ami_sidewalk");
local selev = wd("ami_sidewalk_elev");
local P = od("ami_sidewalk_pole_front"), PNB = od("ami_sidewalk_pole_back");
local PB = od("ami_wall_sidewalk_back_pole"), PF = od("ami_wall_sidewalk_front_pole");
local FB = od("ami_wall_sidewalk_back");
local marker = command_x(tool_set_marker);
report += r("label", marker.work(pl, c(0, -3), "pole: A ew / B ns / C L T X / D slope / E elev"));

// A
report += r("A road", way(road, 2, 2, 16, 2));
report += r("A sideN", way(sw, 2, 1, 16, 1));
report += r("A sideS", way(sw, 2, 3, 16, 3));
report += r("A pole", obj(P, 2, 1, 8, 1));
report += r("A front_pole", obj(PF, 9, 1, 16, 1));
report += r("A fence", obj(FB, 2, 3, 16, 3));
report += r("A back_pole", obj(PB, 9, 3, 16, 3));
report += r("A pole over fence", obj(PNB, 4, 3, 5, 3));
// B
report += r("B road", way(road, 22, 0, 22, 12));
report += r("B sideW", way(sw, 21, 0, 21, 12));
report += r("B sideE", way(sw, 23, 0, 23, 12));
report += r("B front_pole", obj(PF, 21, 0, 21, 12));
report += r("B back_pole", obj(PB, 23, 0, 23, 12));
// C
report += r("C L a", way(sw, 28, 1, 34, 1)); report += r("C L b", way(sw, 34, 1, 34, 7));
report += r("C L pa", obj(PF, 28, 1, 34, 1)); report += r("C L pb", obj(PF, 34, 1, 34, 7));
report += r("C T a", way(sw, 38, 1, 44, 1)); report += r("C T b", way(sw, 41, 1, 41, 5));
report += r("C T pa", obj(P, 38, 1, 44, 1)); report += r("C T pb", obj(P, 41, 1, 41, 5));
report += r("C X a", way(sw, 48, 3, 54, 3)); report += r("C X b", way(sw, 51, 0, 51, 6));
report += r("C X pa", obj(P, 48, 3, 54, 3)); report += r("C X pb", obj(P, 51, 0, 51, 6));
// D
foreach (h in [[60, 1], [66, 2]]) {
  local cx = h[0], n = h[1];
  for (local x = cx - 1; x <= cx + 1; x++) {
    for (local j = 0; j < n; j++) report += r("D raise", command_x.set_slope(pl, c(x, 4, j), slope.all_up_slope));
    report += r("D rampN", command_x.set_slope(pl, c(x, 3), 4 * n));
    report += r("D rampS", command_x.set_slope(pl, c(x, 5), 36 * n));
  }
  report += r("D side", way(sw, cx, 0, cx, 8));
  report += r("D pole", obj(P, cx, 0, cx, 8));
}
// E
report += r("E road", way(relev, 2, 10, 12, 10));
report += r("E sideN", way(selev, 2, 9, 12, 9));
report += r("E sideS", way(selev, 2, 11, 12, 11));
foreach (y in [9, 10, 11]) report += r("E pier", way(pier, 2, y, 12, y));
report += r("E front_pole", obj(PF, 2, 9, 12, 9, 2));
report += r("E pole", obj(PNB, 2, 11, 12, 11, 2));
// F
local rbase = wd("ami_rail_ballast_base_single");
local CAT = null;
foreach (d in wayobj_desc_x.get_available_wayobjs(wt_rail)) if (d.get_name() == "ami_wall_rail_single_catenary") CAT = d;
if (CAT == null) report += "ami_wall_rail_single_catenary wayobj=[missing]\n";
report += r("F rail", way(rbase, 2, 15, 16, 15));
report += r("F cat", obj(CAT, 2, 15, 16, 15));
report += r("F side", way(sw, 2, 14, 16, 14));
report += r("F front_pole", obj(PF, 2, 14, 16, 14));

// [check]: タイルに残った way-object の名前（柵と電柱の置き換え）
function wayobj_name(t) {
  if (t == null) return "-";
  local o = t.find_object(mo_wayobj);
  return o == null ? "-" : o.get_desc().get_name();
}
function expect(tag, x, y, z, want) {
  local s = square_x(OX + x, OY + y);
  local t = z == 0 ? s.get_ground_tile() : s.get_tile_at_height(z);
  local got = wayobj_name(t);
  checks += "[check] " + tag + " (" + x + "," + y + "," + z + ")=" + got + "\n";
  return got == want ? "" : tag + " (" + x + "," + y + ")=[" + got + " want " + want + "]\n";
}
report += expect("A pole", 5, 1, 0, "ami_sidewalk_pole_front");
report += expect("A front_pole", 12, 1, 0, "ami_wall_sidewalk_front_pole");
report += expect("A fence kept", 5, 3, 0, "ami_wall_sidewalk_back");
report += expect("A fence replaced", 12, 3, 0, "ami_wall_sidewalk_back_pole");
report += expect("B W", 21, 6, 0, "ami_wall_sidewalk_front_pole");
report += expect("B E", 23, 6, 0, "ami_wall_sidewalk_back_pole");
report += expect("C L corner", 34, 1, 0, "ami_wall_sidewalk_front_pole");
report += expect("C X", 51, 3, 0, "ami_sidewalk_pole_front");
report += expect("D slope", 60, 3, 0, "ami_sidewalk_pole_front");
report += expect("E N", 6, 9, 2, "ami_wall_sidewalk_front_pole");
report += expect("E S", 6, 11, 2, "ami_sidewalk_pole_back");
if (OX > 200)
  report += r("climate", command_x(tool_set_climate).work(pl, c(-2, -6), c(72, 18), "7"));
gui.close_all_windows();
return (report == "" ? "ok\n" : "check\n" + report) + checks;
