// リリース用のサムネイル（#96）の見本の街区: AMI の way を一通り、街のように密に並べて敷く。撮るのは ingame/thumbnail_capture.sh。
// 検証用の flat_512_left_v64.sve の写しに敷く（保存はしない）。返り値の先頭が ok なら全部敷けた。失敗した所は「名前=[…]」で続く。
// 撮る画面の中心は VIEW のタイル（thumbnail_capture.sh の既定 101,101。C から (1,1)）。画面の上には題名、左下には内容の文字が乗るので、
// 見せたい物（交差・分岐・曲がり・路面軌道）は画面の真ん中から右に寄せ、左下には道路の碁盤だけを置く。
//
// 並び（C からのずれ (dx,dy)。東西の線は画面の左上から右下へ、dy が小さいほど画面の右上。南北の線は右上から左下へ）:
//   dy=-12 一般道路（ami_road_general）に路面軌道（ami_tram）、両側に歩道（ami_sidewalk）。路面軌道は大通りから曲がって入る。北に歩道の広場
//   dy=-10 ラダー軌道（ami_rail_ladder_base_single）に壁。大通りを橋（ami_rail_ladder_bridge）で越える
//     （高架のすぐ北に置くと、手前の高架の床に隠れる。高架との間を 1 タイル空ける）
//   dy=-8,-7 高速道路の高架（ami_road_expressway_elev_back・front）に道路の壁、真下に道路用の橋脚
//   dy=-5,-4 高速線の高架（ami_rail_slab_elev_back・front）に架線つきの壁、真下に橋脚。大通りの上だけ門型の橋脚
//   dy=-2..0 在来線の地上の 3 線（ami_rail_ballast_base_back・center・front）に架線つきの壁。西の丘（dx<HX）のトンネルから出てくる。
//     坑口は線路の来る側に口が開くので、口が画面に見えるよう、丘を西に置いて東向きに口を開ける。
//     dx=YX から東は壁の無い通常の版（ami_rail_ballast）の構内で、北（dy=-3）と南（dy=1）に側線を分ける
//     （分岐の絵は、分かれた先が曲がって並ぶときに選ばれる。壁つきの線の間の渡り線は、壁と架線の柱が崩れて見えるので敷かない）
//   dy=2 直結軌道（ami_rail_concrete_base_single）に壁。dx=YX から東は通常の版（ami_rail_concrete）で、南の側線（dy=3）へ分岐
//   dx=AV 大通り（ami_road_general）。北から路面軌道を載せて来て、2 本の高架の下をくぐり、線路の上は道路の橋（dy=-3..4）
//   dy=5 一般道路の東西（大通りと十字）、両側に歩道。路面軌道は大通りの南から東へ曲がり、dx=8..12・dy=5..9 の街区を回る（生活道路に載る）
//   dy=9・13 生活道路（ami_road_local）の東西、dx=-6・8・12 の南北。街区の中は歩道の広場
local C = [100, 100];
local UP = 2;  // 高架の床の高さ（段）
local AV = 2;  // 大通りの dx
local HX = -8; // 坑口の dx（丘はその西）
local YX = 6;  // 在来線と直結軌道が、壁のある基盤の版から壁の無い通常の版に替わる dx（構内）
local pl = player_x(0);
local report = "";
function r(name, v) { if (v != null) report += name + "=[" + v + "]\n"; }
function c(x, y, z = 0) { return coord3d(C[0] + x, C[1] + y, z); }
function W(n) { local d = way_desc_x(n); if (!d.is_valid()) { report += n + " desc=[missing]\n"; return null; } return d; }
function O(n) { local d = wayobj_desc_x(n); if (!d.is_valid()) { report += n + " desc=[missing]\n"; return null; } return d; }
function way(tag, n, a, b) { local d = W(n); if (d != null) r(tag, command_x.build_way(pl, a, b, d, true)); }
function obj(tag, n, a, b) { local d = O(n); if (d != null) r(tag, command_x.build_wayobj(pl, a, b, d)); }
function slope_at(tag, p, s) { r(tag, command_x.set_slope(pl, p, s)); }
function bridge(tag, n, a, b) { local d = bridge_desc_x(n); if (!d.is_valid()) { report += n + " desc=[missing]\n"; return; } r(tag, command_x.build_bridge(pl, a, b, d)); }
// 東西の歩道を x0..x1 に敷く。道路を横切ると踏切が立つので、skip の dx（南北の道路）は空ける
function walk_ew(y, x0, x1, skip) {
  local a = x0;
  for (local x = x0; x <= x1 + 1; x++) {
    if (x == x1 + 1 || skip.find(x) != null) {
      if (a <= x - 1) way("walk", "ami_sidewalk", c(a, y), c(x - 1, y));
      a = x + 1;
    }
  }
}
function plaza(x0, y0, x1, y1) { for (local y = y0; y <= y1; y++) way("plaza", "ami_sidewalk", c(x0, y), c(x1, y)); }

// 丘とトンネル（先に地形を作る）: dx=HX-6..HX-1、dy=-2..0 を 2 段上げ、東の dx=HX を坑口の坂、西の dx=HX-7 と北の dy=-3・南の dy=1 を坂にする
for (local x = HX - 6; x <= HX - 1; x++) {
  for (local y = -2; y <= 0; y++) for (local k = 0; k < 2; k++) slope_at("hill", c(x, y, k), slope.all_up_slope);
  slope_at("hill N", c(x, -3), 8);
  slope_at("hill S", c(x, 1), 72);
}
foreach (y in [-2, -1, 0]) {
  slope_at("hill W", c(HX - 7, y), 24);
  slope_at("hill E", c(HX, y), 56);
  r("tunnel", command_x(tool_build_tunnel).work(pl, c(HX, y), "ami_rail_ballast_tunnel"));
}

// 在来線の 3 線と構内の側線
foreach (v in [["back", -2], ["center", -1], ["front", 0]]) {
  way("ballast " + v[0], "ami_rail_ballast_base_" + v[0], c(HX, v[1]), c(YX - 1, v[1]));
  obj("ballast wall " + v[0], "ami_wall_rail_" + v[0] + "_catenary", c(HX - 7, v[1]), c(YX - 1, v[1]));
  way("yard " + v[0], "ami_rail_ballast", c(YX - 1, v[1]), c(24, v[1]));
}
way("siding N", "ami_rail_ballast", c(YX + 2, -2), c(YX + 2, -3));
way("siding N", "ami_rail_ballast", c(YX + 2, -3), c(24, -3));
way("siding S", "ami_rail_ballast", c(YX + 5, 0), c(YX + 5, 1));
way("siding S", "ami_rail_ballast", c(YX + 5, 1), c(24, 1));

// 直結軌道と側線
way("concrete", "ami_rail_concrete_base_single", c(-24, 2), c(YX - 1, 2));
obj("concrete wall", "ami_wall_rail_single", c(-24, 2), c(YX - 1, 2));
way("concrete yard", "ami_rail_concrete", c(YX - 1, 2), c(24, 2));
way("siding", "ami_rail_concrete", c(YX + 8, 2), c(YX + 8, 3));
way("siding", "ami_rail_concrete", c(YX + 8, 3), c(24, 3));

// 高速線の高架。橋脚は大通りの所だけ門型
foreach (v in [["back", -5], ["front", -4]]) {
  way("slab elev " + v[0], "ami_rail_slab_elev_" + v[0], c(-24, v[1]), c(24, v[1]));
  obj("slab wall " + v[0], "ami_wall_rail_" + v[0] + "_catenary", c(-24, v[1], UP), c(24, v[1], UP));
  way("slab pier", "ami_pier_rail", c(-24, v[1]), c(AV - 1, v[1]));
  way("slab pier", "ami_pier_rail", c(AV + 1, v[1]), c(24, v[1]));
  way("slab gate", "ami_pier_rail_gate", c(AV, v[1]), c(AV, v[1]));
}

// 高速道路の高架と道路の壁、真下に道路用の橋脚（大通りの所は空ける。路面軌道と同じ種類の way なので）
foreach (v in [["back", -8], ["front", -7]]) {
  way("expressway " + v[0], "ami_road_expressway_elev_" + v[0], c(-24, v[1]), c(24, v[1]));
  obj("expressway wall " + v[0], "ami_wall_road_" + v[0], c(-24, v[1], UP), c(24, v[1], UP));
  way("road pier", "ami_pier_road", c(-24, v[1]), c(AV - 1, v[1]));
  way("road pier", "ami_pier_road", c(AV + 1, v[1]), c(24, v[1]));
}

// ラダー軌道: 大通りを橋で越える
way("ladder W", "ami_rail_ladder_base_single", c(-24, -10), c(AV - 3, -10));
way("ladder E", "ami_rail_ladder_base_single", c(AV + 3, -10), c(24, -10));
bridge("ladder bridge", "ami_rail_ladder_bridge", c(AV - 3, -10), c(AV + 3, -10));
obj("ladder wall", "ami_wall_rail_single", c(-24, -10), c(24, -10));

// 大通り: 北から高架の下を通り、線路を橋で越えて南へ
way("avenue N", "ami_road_general", c(AV, -24), c(AV, -3));
way("avenue S", "ami_road_general", c(AV, 4), c(AV, 24));
bridge("avenue bridge", "ami_road_general_bridge", c(AV, -3), c(AV, 4));

// 北の一般道路と路面軌道（大通りの北から来て、十字で西へ曲がる）、両側の歩道と広場
way("general N", "ami_road_general", c(-24, -12), c(24, -12));
way("tram N", "ami_tram", c(AV, -24), c(AV, -12));
way("tram N", "ami_tram", c(AV, -12), c(-24, -12));
foreach (y in [-13, -11]) walk_ew(y, -24, 24, [AV]);
plaza(AV + 2, -17, AV + 6, -14);

// 南の道路の碁盤: 一般道路 dy=5、生活道路 dy=9・13 と dx=-6・8・12
way("general S", "ami_road_general", c(-24, 5), c(24, 5));
foreach (y in [9, 13]) way("local EW", "ami_road_local", c(-24, y), c(24, y));
foreach (x in [-6, 8, 12]) way("local NS", "ami_road_local", c(x, 5), c(x, 24));
foreach (y in [4, 6]) walk_ew(y, -24, 24, [-6, AV, 8, 12]);
// 路面軌道: 大通りの南から北へ来て、十字で東へ曲がり、dx=8..12・dy=5..9 の街区を回る
way("tram S", "ami_tram", c(AV, 24), c(AV, 5));
way("tram S", "ami_tram", c(AV, 5), c(12, 5));
way("tram loop", "ami_tram", c(12, 5), c(12, 9));
way("tram loop", "ami_tram", c(12, 9), c(8, 9));
way("tram loop", "ami_tram", c(8, 9), c(8, 6));
// 街区の中の広場
plaza(9, 7, 11, 8);
plaza(AV + 1, 7, 7, 8);
plaza(-5, 7, AV - 1, 8);
plaza(AV + 1, 10, 7, 12);
plaza(-5, 14, AV - 1, 16);
gui.close_all_windows();
return report == "" ? "ok" : "check\n" + report;
