// 第 2 弾のベータ版（beta.2。#170）のサムネイルの見本の街区。ingame/thumbnail_capture.sh が NUT として流す（#103 の撮影用レイアウトの記録を元にした）。
// 検証用の flat_512.sve の写しに敷く（保存はしない）。返り値の先頭が ok なら全部敷けた。失敗した所は「名前=[…]」で続く。
// 座標は撮る画面の中心のタイル V=(101,101) からのずれ (rx,ry)。等倍（gui.set_zoom(3)）で画面に入るのは |rx|+|ry| がおよそ 20 まで（ひし形）。
// 東西の線（rx の向き）は画面の左上から右下へ、南北の線（ry の向き）は右上から左下へ走る。左上に題名、左下に文字が乗る。
//   rx>=2 は降雪（tool_set_climate。画面の右下の半分）。左が温暖、右が降雪。
//   ry=-15  運河（ami_canal）と船の車庫。大通り（rx=1）が跳ね橋の踏切で越える
//   ry=-12  懸垂式モノレールの高架（center）、ry=-10 跨座式の高架（center）。どちらも電化
//   ry=-6,-5 高速道路の高架（分離帯つきの壁）、真下に道路用の橋脚
//   ry=0,1  複線の在来線（在来線+直結軌道）。西の丘のトンネルから出て、東の構内（車庫・操車場・側線）へ
//   rx=5,6  高架の高速線+ラダー軌道の複線。地上の複線と大通りの上をまたぐ
//   rx=1    大通り（北から来て、運河を越え、高速道路の高架の下をくぐり、線路を橋で越える）
//   ry=7,8  4 車線の幹線（路面表示の版）、両側に歩道（舗装の種類を替える）と電柱。南に生活道路の碁盤・路面軌道・標識
local V = [101, 101];
local UP = 2;
local AV = 1;
local pl = player_x(0);
local report = "";
function r(name, v) { if (v != null) report += name + "=[" + v + "]\n"; }
function c(x, y, z = 0) { return coord3d(V[0] + x, V[1] + y, z); }
function W(n) { local d = way_desc_x(n); if (d == null) report += n + " desc=[missing]\n"; return d; }
local WOBJ = {};
foreach (wt in [wt_rail, wt_road, wt_water, wt_monorail, wt_tram])
  foreach (d in wayobj_desc_x.get_available_wayobjs(wt)) WOBJ[d.get_name()] <- d;
function O(n) { if (!(n in WOBJ)) { report += n + " wayobj=[missing]\n"; return null; } return WOBJ[n]; }
function way(tag, n, a, b) { r(tag, command_x.build_way(pl, a, b, W(n), true)); }
function obj(tag, n, a, b) { r(tag, command_x.build_wayobj(pl, a, b, O(n))); }
function slope_at(tag, p, s) { r(tag, command_x.set_slope(pl, p, s)); }
function bridge(tag, n, a, b) { r(tag, command_x.build_bridge(pl, a, b, bridge_desc_x(n))); }
// 東西の歩道を x0..x1 に敷く。道路を横切ると踏切が立つので、skip の rx（南北の道路）は空ける。pole が空でなければ、各区間に電柱を重ねる
function walk_ew(tag, n, y, x0, x1, skip, pole) {
  local a = x0;
  for (local x = x0; x <= x1 + 1; x++) {
    if (x == x1 + 1 || skip.find(x) != null) {
      if (a <= x - 1) {
        way(tag, n, c(a, y), c(x - 1, y));
        if (pole != null && a < x - 1) obj(tag + " pole", pole, c(a, y), c(x - 1, y));
      }
      a = x + 1;
    }
  }
}

// 降雪（rx>=2）。先に塗る
r("climate", command_x(tool_set_climate).work(pl, coord3d(V[0] + 2, V[1] - 40, 0), coord3d(V[0] + 40, V[1] + 40, 0), "7"));

// 丘とトンネル: rx=-9..-4、ry=0,1 を 2 段上げ、東の rx=-3 を坑口の坂、西の rx=-10 と北の ry=-1・南の ry=2 を坂にする
for (local x = -9; x <= -4; x++) {
  for (local y = 0; y <= 1; y++) for (local k = 0; k < 2; k++) slope_at("hill", c(x, y, k), slope.all_up_slope);
  slope_at("hill N", c(x, -1), 8);
  slope_at("hill S", c(x, 2), 72);
}
foreach (y in [0, 1]) {
  slope_at("hill W", c(-10, y), 24);
  slope_at("hill E", c(-3, y), 56);
}
r("tunnel ballast", command_x(tool_build_tunnel).work(pl, c(-3, 0), "ami_rail_ballast_tunnel"));
r("tunnel concrete", command_x(tool_build_tunnel).work(pl, c(-3, 1), "ami_rail_concrete_tunnel"));

// 複線の在来線（ry=0）と直結軌道（ry=1）。rx=9 から東は壁の無い通常の版（構内）
local YX = 9;
way("ballast", "ami_rail_ballast_base_back", c(-3, 0), c(YX - 1, 0));
obj("ballast wall", "ami_wall_rail_back_catenary", c(-10, 0), c(YX - 1, 0));
way("concrete", "ami_rail_concrete_base_front", c(-3, 1), c(YX - 1, 1));
obj("concrete wall", "ami_wall_rail_front_catenary", c(-10, 1), c(YX - 1, 1));
way("yard ballast", "ami_rail_ballast", c(YX - 1, 0), c(17, 0));
way("yard concrete", "ami_rail_concrete", c(YX - 1, 1), c(17, 1));
// 側線: 北（在来線から rx=12 で分かれる）の行き止まりに車庫、南（直結軌道から rx=14 で分かれる）
way("siding N", "ami_rail_ballast", c(12, 0), c(12, -1));
way("siding N", "ami_rail_ballast", c(12, -1), c(16, -1));
way("siding S", "ami_rail_concrete", c(14, 1), c(14, 2));
way("siding S", "ami_rail_concrete", c(14, 2), c(17, 2));

// 高架の高速線（rx=5）+ ラダー軌道（rx=6）。地上の複線（ry=0,1）と幹線（ry=7,8）の上は門型の橋脚、そのほかは橋脚の way
local VY0 = -2, VY1 = 12;
way("slab elev", "ami_rail_slab_elev_back", c(5, VY0), c(5, VY1));
obj("slab wall", "ami_wall_rail_back_catenary", c(5, VY0, UP), c(5, VY1, UP));
way("ladder elev", "ami_rail_ladder_elev_front", c(6, VY0), c(6, VY1));
obj("ladder wall", "ami_wall_rail_front_catenary", c(6, VY0, UP), c(6, VY1, UP));
foreach (x in [5, 6]) {
  way("viaduct pier", "ami_pier_rail", c(x, VY0), c(x, -1));
  way("viaduct pier", "ami_pier_rail", c(x, 2), c(x, 6));
  way("viaduct pier", "ami_pier_rail", c(x, 9), c(x, VY1));
  foreach (y in [0, 1, 7, 8]) way("viaduct gate", "ami_pier_rail_gate", c(x, y), c(x, y));
}

// 高速道路の高架（分離帯つきの壁）と、真下の橋脚（大通りの所は空ける）。ry=-6 が奥、ry=-5 が手前
way("expressway back", "ami_road_expressway_elev_back", c(-13, -6), c(13, -6));
obj("expressway wall back", "ami_wall_road_back", c(-13, -6, UP), c(13, -6, UP));
way("expressway front", "ami_road_expressway_elev_front", c(-13, -5), c(13, -5));
obj("expressway wall front", "ami_wall_road_front_divider", c(-13, -5, UP), c(13, -5, UP));
foreach (y in [-6, -5]) {
  way("road pier", "ami_pier_road", c(-13, y), c(AV - 1, y));
  way("road pier", "ami_pier_road", c(AV + 1, y), c(13, y));
}

// モノレール: 懸垂式（ry=-12）と跨座式（ry=-10）の高架。どちらも電化する
way("suspended", "ami_monorail_suspended_elev_center", c(-7, -12), c(6, -12));
obj("suspended power", "ami_monorail_suspended_power", c(-7, -12, UP), c(6, -12, UP));
way("straddle", "ami_monorail_straddle_elev_center", c(-9, -10), c(8, -10));
obj("straddle power", "ami_monorail_power", c(-9, -10, UP), c(8, -10, UP));

// 運河（ry=-15）と西の端の船の車庫。大通りが跳ね橋の踏切で越える
way("canal", "ami_canal", c(-4, -15), c(5, -15));
local depots = {};
foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) depots[d.get_name()] <- d;
function depot(tag, n, p) {
  if (!(n in depots)) { report += "no depot " + n + "\n"; return; }
  r(tag, command_x.build_depot(pl, p, depots[n]));
}
depot("canal depot", "ami_canal_depot", c(-4, -15));
depot("rail depot", "ami_rail_depot", c(16, -1));
local yard = building_desc_x("ami_rail_yard");
if (yard == null) report += "no yard\n";
else {
  r("yard", command_x.build_station(pl, c(14, 0), yard));
  r("yard 2", command_x.build_station(pl, c(15, 1), yard));
  // 駅名のラベルが画面に出るので、空白にする（建てた駅は 1 つずつ名前を持つ）
  foreach (p in [c(14, 0), c(15, 1)]) { local h = square_x(p.x, p.y).get_ground_tile().get_halt(); if (h != null) h.set_name(" "); }
}

// 大通り: 北から運河・高架の下を通り、線路を橋で越えて南へ
way("avenue N", "ami_road_general", c(AV, -19), c(AV, -1));
way("avenue S", "ami_road_general", c(AV, 2), c(AV, 14));
bridge("avenue bridge", "ami_road_general_bridge", c(AV, -1), c(AV, 2));

// 4 車線の幹線（路面表示の版。ry=7 が奥、ry=8 が手前）。大通りとの交差点は通常の版に置き換わる
way("main back", "ami_road_general_lane1", c(-12, 7), c(14, 7));
way("main front", "ami_road_general_lane2", c(-12, 8), c(14, 8));
// 南の生活道路と碁盤
way("local EW", "ami_road_local", c(-12, 12), c(14, 12));
foreach (x in [-6, 8]) way("local NS", "ami_road_local", c(x, 9), c(x, 14));
// 歩道（舗装の種類を街区ごとに替える）と電柱。南北の道路の所は空ける
walk_ew("walk N W", "ami_sidewalk_brick", 6, -12, AV - 1, [-6], "ami_sidewalk_pole_front");
walk_ew("walk N E", "ami_sidewalk_tile", 6, AV + 1, 14, [5, 6, 8], "ami_sidewalk_pole_front");
walk_ew("walk S W", "ami_sidewalk_asphalt", 9, -12, AV - 1, [-6], null);
walk_ew("walk S E", "ami_sidewalk", 9, AV + 1, 14, [5, 6, 8], null);
// 路面軌道: 生活道路に載せ、東の道で幹線へ向かう
way("tram", "ami_tram", c(-6, 12), c(8, 12));
way("tram", "ami_tram", c(8, 12), c(8, 10));
// 道路標識
local SIGNS = {};
foreach (d in sign_desc_x.get_available_signs(wt_road)) SIGNS[d.get_name()] <- d;
function sign(tag, n, p) {
  if (!(n in SIGNS)) { report += "no sign " + n + "\n"; return; }
  r(tag, command_x.build_sign_at(pl, p, SIGNS[n]));
}
sign("sign one way", "ami_sign_one_way", c(-3, 12));
sign("sign stop", "ami_sign_stop", c(8, 11));
sign("sign speed", "ami_sign_speed_40", c(-6, 11));
gui.close_all_windows();
return report == "" ? "ok" : "check\n" + report;
