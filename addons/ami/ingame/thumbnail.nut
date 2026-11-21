// リリース用のサムネイル（#96）の見本の街区: AMI の way を一通り、街のように並べて敷く。撮るのは ingame/thumbnail_capture.sh。
// 検証用の flat_512.sve の写しに敷く（保存はしない）。返り値の先頭が ok なら全部敷けた。失敗した所は「名前=[…]」で続く。
// 撮る画面の中心は VIEW のタイル（thumbnail_capture.sh の既定）。画面の上には題名、左下には内容の文字が乗るので、
// 見せたい物は画面の真ん中から右に置き、左下（南西）には道路だけを置く。
//
// 並び（C からのずれ (dx,dy)。東西の線は画面の左上から右下へ、dy が小さいほど画面の右上。南北の線は右上から左下へ）:
//   dy=-12 一般道路（ami_road_general）の東西に路面軌道（ami_tram）、両側に歩道（ami_sidewalk）。路面軌道は大通りから曲がって入る
//   dy=-9,-8 高速道路の高架（ami_road_expressway_elev_back・front）に道路の壁、真下に道路用の橋脚
//   dy=-6 ラダー軌道（ami_rail_ladder_base_single）に壁。大通りを橋（ami_rail_ladder_bridge）で越える
//   dy=-4,-3 高速線の高架（ami_rail_slab_elev_back・front）に架線つきの壁、真下に橋脚。大通りの上だけ門型の橋脚
//   dy=-1..1 在来線の地上の 3 線（ami_rail_ballast_base_back・center・front）に架線つきの壁。西の丘（dx<HX）のトンネルから出てくる。
//     坑口は線路の来る側に口が開くので、口が画面に見えるよう、丘を西に置いて東向きに口を開ける。
//     dx=YX から東は壁の無い通常の版（ami_rail_ballast）の構内で、北と南に側線（分岐）
//   dy=3 直結軌道（ami_rail_concrete_base_single）に壁。dx=YX から東は通常の版（ami_rail_concrete）で、南の側線（dy=4）へ分岐
//   dx=AV 大通り（ami_road_general）。北から路面軌道を載せて来て、2 本の高架の下をくぐり、線路の上は道路の橋（dy=-2..5）
//   dy=7 生活道路（ami_road_local）の東西、dx=-6 の南北（左下の文字の下）
local C = [100, 100];
local UP = 2;  // 高架の床の高さ（段）
local AV = 2;  // 大通りの dx
local HX = -8; // 坑口の dx（丘はその西）
local YX = 6;  // 在来線と直結軌道が、壁のある基盤の版から壁の無い通常の版に替わる dx（構内）
local pl = player_x(0);
local report = "";
function r(name, v) { if (v != null) report += name + "=[" + v + "]\n"; }
function c(x, y, z = 0) { return coord3d(C[0] + x, C[1] + y, z); }
function W(n) { local d = way_desc_x(n); if (d == null) report += n + " desc=[missing]\n"; return d; }
function O(n) { local d = wayobj_desc_x(n); if (d == null) report += n + " desc=[missing]\n"; return d; }
function way(tag, n, a, b) { r(tag, command_x.build_way(pl, a, b, W(n), true)); }
function obj(tag, n, a, b) { r(tag, command_x.build_wayobj(pl, a, b, O(n))); }
function slope_at(tag, p, s) { r(tag, command_x.set_slope(pl, p, s)); }
function bridge(tag, n, a, b) { r(tag, command_x.build_bridge(pl, a, b, bridge_desc_x(n))); }

// 丘とトンネル（先に地形を作る）: dx=HX-6..HX-1、dy=-1..1 を 2 段上げ、東の dx=HX を坑口の坂、西の dx=HX-7 と北の dy=-2・南の dy=2 を坂にする
for (local x = HX - 6; x <= HX - 1; x++) {
  for (local y = -1; y <= 1; y++) for (local k = 0; k < 2; k++) slope_at("hill", c(x, y, k), slope.all_up_slope);
  slope_at("hill N", c(x, -2), 8);
  slope_at("hill S", c(x, 2), 72);
}
foreach (y in [-1, 0, 1]) {
  slope_at("hill W", c(HX - 7, y), 24);
  slope_at("hill E", c(HX, y), 56);
  r("tunnel", command_x(tool_build_tunnel).work(pl, c(HX, y), "ami_rail_ballast_tunnel"));
}

// 在来線の 3 線: 坑口から dx=YX-1 までは基盤の版に架線つきの壁（坑口とトンネルの中も通す）、dx=YX から東は壁の無い通常の版の構内。
// 構内で back から北（dy=-2）、front から南（dy=2）へ側線を分ける（分岐の絵は、分かれた先が曲がって並ぶときに選ばれる。通常の版の物を見せる）
foreach (v in [["back", -1], ["center", 0], ["front", 1]]) {
  way("ballast " + v[0], "ami_rail_ballast_base_" + v[0], c(HX, v[1]), c(YX - 1, v[1]));
  obj("ballast wall " + v[0], "ami_wall_rail_" + v[0] + "_catenary", c(HX - 7, v[1]), c(YX - 1, v[1]));
  way("yard " + v[0], "ami_rail_ballast", c(YX - 1, v[1]), c(24, v[1]));
}
way("siding N", "ami_rail_ballast", c(YX + 3, -1), c(YX + 3, -2));
way("siding N", "ami_rail_ballast", c(YX + 3, -2), c(24, -2));
way("siding S", "ami_rail_ballast", c(YX + 7, 1), c(YX + 7, 2));
way("siding S", "ami_rail_ballast", c(YX + 7, 2), c(24, 2));

// 直結軌道: dx=YX-1 までは基盤の版に壁、東は通常の版。東で南の側線（dy=4）へ分岐
way("concrete", "ami_rail_concrete_base_single", c(HX + 1, 3), c(YX - 1, 3));
obj("concrete wall", "ami_wall_rail_single", c(HX + 1, 3), c(YX - 1, 3));
way("concrete yard", "ami_rail_concrete", c(YX - 1, 3), c(24, 3));
way("siding", "ami_rail_concrete", c(YX + 5, 3), c(YX + 5, 4));
way("siding", "ami_rail_concrete", c(YX + 5, 4), c(24, 4));

// 高速線の高架。橋脚は大通りの所だけ門型
foreach (v in [["back", -4], ["front", -3]]) {
  way("slab elev " + v[0], "ami_rail_slab_elev_" + v[0], c(-24, v[1]), c(24, v[1]));
  obj("slab wall " + v[0], "ami_wall_rail_" + v[0] + "_catenary", c(-24, v[1], UP), c(24, v[1], UP));
  way("slab pier", "ami_pier_rail", c(-24, v[1]), c(AV - 1, v[1]));
  way("slab pier", "ami_pier_rail", c(AV + 1, v[1]), c(24, v[1]));
  way("slab gate", "ami_pier_rail_gate", c(AV, v[1]), c(AV, v[1]));
}

// 高速道路の高架と道路の壁、真下に道路用の橋脚（路面軌道の無い所の道路とは同じタイルに置ける）
foreach (v in [["back", -9], ["front", -8]]) {
  way("expressway " + v[0], "ami_road_expressway_elev_" + v[0], c(-24, v[1]), c(24, v[1]));
  obj("expressway wall " + v[0], "ami_wall_road_" + v[0], c(-24, v[1], UP), c(24, v[1], UP));
  way("road pier", "ami_pier_road", c(-24, v[1]), c(24, v[1]));
}

// 大通り: 北から高架の下を通り、線路を橋で越えて南へ
way("avenue N", "ami_road_general", c(AV, -24), c(AV, -2));
way("avenue S", "ami_road_general", c(AV, 5), c(AV, 24));
bridge("avenue bridge", "ami_road_general_bridge", c(AV, -2), c(AV, 5));

// 北の一般道路と路面軌道（大通りの北から来て、十字で西へ曲がる）、両側の歩道（交差点のタイルは空ける）
way("general N", "ami_road_general", c(-24, -12), c(24, -12));
way("tram NS", "ami_tram", c(AV, -24), c(AV, -12));
way("tram EW", "ami_tram", c(AV, -12), c(-24, -12));
foreach (y in [-13, -11]) { way("walk W", "ami_sidewalk", c(-24, y), c(AV - 1, y)); way("walk E", "ami_sidewalk", c(AV + 1, y), c(24, y)); }

// ラダー軌道: 大通りを橋で越える
way("ladder W", "ami_rail_ladder_base_single", c(-24, -6), c(AV - 3, -6));
way("ladder E", "ami_rail_ladder_base_single", c(AV + 3, -6), c(24, -6));
bridge("ladder bridge", "ami_rail_ladder_bridge", c(AV - 3, -6), c(AV + 3, -6));
obj("ladder wall", "ami_wall_rail_single", c(-24, -6), c(24, -6));

// 南の生活道路（左下の文字の下）
way("local EW", "ami_road_local", c(-24, 7), c(24, 7));
way("local NS", "ami_road_local", c(-6, 7), c(-6, 24));
gui.close_all_windows();
return report == "" ? "ok" : "check\n" + report;
