// AMI の 6 車線の路面表示（ami_mark_lane6_m・junction6_*。#189）の見本。一般道路（ami_road_general）を 3 本並べ、表示を重ねる。
// 検証用の flat_512.sve に、温暖側 (20,20) と降雪側 (276,20) の 2 か所へ同じ並びで敷き、降雪側は一帯を降雪に塗り直す。
// 使い方（アドオンのディレクトリで）: sample_parallel.sh に NUT=ingame/marking6_sample.nut を付ける（撮る場所は sample_spots.sh の MARKING6_SPOTS）。
// 返り値の先頭が ok なら全部敷けて、[check] で比べた名前も期待どおり。違えば先頭が check で、「名前 場所=[…]」が続く。
// 敷き方は README の「路面表示の作り」の 6 車線と同じ。区画は 19×19 で、中心 3×3 が (8..10, 8..10)。
//   左側通行。西の腕は東へ向かう（入る側が北の列 y=8、分離帯 y=9、出る側が南の列 y=10）、東の腕は西へ（入る側 y=10、出る側 y=8）、
//   北の腕は南へ（入る側 x=10、出る側 x=8）、南の腕は北へ（入る側 x=8、出る側 x=10）。1 マス目は交差点の隣、2 マス目はその外
local ORIGINS = [[20, 20], [276, 20]];
local SNOW = 1;
local AREA = [[-3, -4], [22, 22]];
local G = "ami_road_general";
local L4 = "ami_mark_lane4", LM = "ami_mark_lane6_m", JI4 = "ami_mark_junction4_in";
local JI = "ami_mark_junction6_in", JO = "ami_mark_junction6_out", JM = "ami_mark_junction6_m", JC = "ami_mark_junction6_c";
local pl = player_x(0);
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
function one(tag, n, x, y) { way(tag, n, x, y, x, y); }
function expect(tag, x, y, road, mark) {
  local t = square_x(OX + x, OY + y).get_ground_tile();
  local w = t.get_way(wt_road), m = t.get_way(wt_rail);
  local rn = w == null ? "-" : w.get_desc().get_name(), mn = m == null ? "-" : m.get_desc().get_name();
  checks += "[check] " + tag + " (" + x + "," + y + ") " + rn + "/d" + (w == null ? "-" : w.get_dirs()) + " + " + mn + "/d" + (m == null ? "-" : m.get_dirs()) + "\n";
  if (rn != road || mn != mark) report += tag + " (" + x + "," + y + ") want=[" + road + " + " + mark + "] got=[" + rn + " + " + mn + "]\n";
}

function x6(tag) {
  foreach (y in [8, 9, 10]) way(tag, G, 0, y, 18, y);
  foreach (x in [8, 9, 10]) way(tag, G, x, 0, x, 18);
  // 直線: 外の 2 列は lane4、真ん中は lane6_m。腕の 2 マスの手前まで（腕とつなげない）
  foreach (y in [8, 10]) { way(tag, L4, 0, y, 5, y); way(tag, L4, 13, y, 18, y); }
  way(tag, LM, 0, 9, 5, 9); way(tag, LM, 13, 9, 18, 9);
  foreach (x in [8, 10]) { way(tag, L4, x, 0, x, 5); way(tag, L4, x, 13, x, 18); }
  way(tag, LM, 9, 0, 9, 5); way(tag, LM, 9, 13, 9, 18);
  // L 字（junction4_in）: 入る側の腕の外の端 → 中心の角 → 左隣の腕の出る側の外の端
  foreach (l in [[10, 6, 10, 8, 12, 8], [12, 10, 10, 10, 10, 12], [8, 12, 8, 10, 6, 10], [6, 8, 8, 8, 8, 6]]) {
    way(tag + " L", JI4, l[0], l[1], l[2], l[3]);
    way(tag + " L", JI4, l[2], l[3], l[4], l[5]);
  }
  // 1 マス目を 3 列、横につなぐ（junction6_m）。分離帯の列は外へ 2 マス目につなぐ
  foreach (k in [[7, 8, 7, 10], [11, 8, 11, 10], [8, 7, 10, 7], [8, 11, 10, 11], [6, 9, 7, 9], [12, 9, 11, 9], [9, 6, 9, 7], [9, 12, 9, 11]])
    way(tag + " link", JM, k[0], k[1], k[2], k[3]);
  // 入る側・出る側の外の列の 2 マスを、1 マスずつ敷き直す（向きはそのままで名前だけが置き換わる）
  local ins = [[6, 8], [7, 8], [12, 10], [11, 10], [10, 6], [10, 7], [8, 12], [8, 11]];
  local outs = [[6, 10], [7, 10], [12, 8], [11, 8], [8, 6], [8, 7], [10, 12], [10, 11]];
  foreach (p in ins) one(tag + " in", JI, p[0], p[1]);
  foreach (p in outs) one(tag + " out", JO, p[0], p[1]);
  // 中心 3×3 の角を除く 5 枚（辺の 4 枚と中央）
  way(tag + " center", JC, 9, 8, 9, 10);
  way(tag + " center", JC, 8, 9, 10, 9);
  foreach (p in ins) expect(tag + " in", p[0], p[1], G, JI);
  foreach (p in outs) expect(tag + " out", p[0], p[1], G, JO);
  foreach (p in [[7, 9], [6, 9], [11, 9], [12, 9], [9, 7], [9, 6], [9, 11], [9, 12]]) expect(tag + " mid", p[0], p[1], G, JM);
  foreach (p in [[8, 8], [10, 8], [8, 10], [10, 10]]) expect(tag + " corner", p[0], p[1], G, JI4);
  foreach (p in [[9, 8], [8, 9], [9, 9], [10, 9], [9, 10]]) expect(tag + " center", p[0], p[1], G, JC);
  foreach (p in [[3, 8], [3, 10], [8, 3], [10, 3]]) expect(tag + " lane4", p[0], p[1], G, L4);
  foreach (p in [[3, 9], [9, 3]]) expect(tag + " lane6_m", p[0], p[1], G, LM);
}

foreach (n, o in ORIGINS) {
  OX = o[0]; OY = o[1];
  x6("X6");
  if (n == SNOW)
    report += r("climate", command_x(tool_set_climate).work(pl, c(AREA[0][0], AREA[0][1]), c(AREA[1][0], AREA[1][1]), "7"));
}
gui.close_all_windows();
return (report == "" ? "ok\n" : "check\n" + report) + checks;
