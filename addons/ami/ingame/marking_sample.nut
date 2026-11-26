// AMI の多車線と交差点の路面表示（ami_mark_*。#187）の見本。一般道路（ami_road_general）を敷き、表示を重ねる。
// 検証用の flat_512_left_v64.sve に、温暖側 (20,20) と降雪側 (276,20) の 2 か所へ同じ並びで敷き、降雪側は一帯を降雪に塗り直す。
// 使い方（アドオンのディレクトリで）: sample_parallel.sh に NUT=ingame/marking_sample.nut を付ける（撮る場所は sample_spots.sh の MARKING_SPOTS）。
// 返り値の先頭が ok なら全部敷けて、[check] で比べた名前も期待どおり。違えば先頭が check で、「名前 場所=[…]」が続く。最後に [check] の行が続く。
// 敷き方は README の「路面表示の作り」と同じ:
//   4 車線どうし: 1. 道路を 2 本ずつ並べる 2. 直線の 2 列に lane4 を腕の手前まで 3. junction4_in で 4 本の L 字（入る側の腕の外の端
//   → 中心の角 → 左隣の腕の出る側の外の端）と、腕の 1 マス目の 2 列を横につなぐ 4. 出る側の 2 マス（スクランブルなら中心も）を
//   junction4_out で 1 マスずつ敷き直す 5. ふつうの中心は、中心の 4 マスを junction4_c で 1 マスずつ敷き直す（中心の印。#313）
//   4 車線 × 2 車線: 4 車線の 2 列を junction4_in で通して敷き、1 マス目を横につなぎ、2 車線の腕から中心へ junction2、出る側を junction4_out
//   2 車線: 腕の外の端から反対の腕の外の端へ junction2（T字路は junction2_t）
// 区画（原点から。左側通行。東西の道は北の列が東行き、南北の道は東の列が南行き）:
//   X4（中心 (8..9, 8..9)）: 4 車線どうしの十字。X4S（x を 22 東へ）: 同じでスクランブル
//   X42（x を 44 東。4 車線が南北の x 8・9、2 車線が東西の y 8）: 4 車線 × 2 車線の十字
//   X2（中心 (5,27)）: 2 車線どうしの十字。T2（中心 (19,27)、南へ枝）: 2 車線の T字路
local ORIGINS = [[20, 20], [276, 20]];
local SNOW = 1;
local AREA = [[-3, -4], [66, 36]];
// ラウンドの版（#56）: ami_mark_ で始まる名前の末尾に付ける。例: "_round1"。空なら今の名前（sample_parallel.sh の SUFFIX が置き換える）
local SUFFIX = "";
local G = "ami_road_general";
local L4 = "ami_mark_lane4", J2 = "ami_mark_junction2", J2T = "ami_mark_junction2_t";
local JI = "ami_mark_junction4_in", JO = "ami_mark_junction4_out", JC = "ami_mark_junction4_c";
local pl = player_x(0);
local report = "";
local checks = "";
local OX = 0, OY = 0;
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
function c(x, y) { return coord3d(OX + x, OY + y, 0); }
function way(tag, n, x0, y0, x1, y1) {
  local w = way_desc_x(n.find("ami_mark_") == 0 ? n + SUFFIX : n);
  if (w == null) { report += n + " desc=[missing]\n"; return; }
  report += r(tag + " " + n, command_x.build_way(pl, c(x0, y0), c(x1, y1), w, true));
}
function one(tag, n, x, y) { way(tag, n, x, y, x, y); }
// タイルの道路と表示の名前が want でなければ、返り値に足す
function expect(tag, x, y, road, mark) {
  local t = square_x(OX + x, OY + y).get_ground_tile();
  local w = t.get_way(wt_road), m = t.get_way(wt_rail);
  local rn = w == null ? "-" : w.get_desc().get_name(), mn = m == null ? "-" : m.get_desc().get_name();
  checks += "[check] " + tag + " (" + x + "," + y + ") " + rn + "/d" + (w == null ? "-" : w.get_dirs()) + " + " + mn + "/d" + (m == null ? "-" : m.get_dirs()) + "\n";
  if (rn != road || mn != mark) report += tag + " (" + x + "," + y + ") want=[" + road + " + " + mark + "] got=[" + rn + " + " + mn + "]\n";
}

// 4 車線どうしの十字（区画の西の端 dx）
function x4(tag, dx, scramble) {
  foreach (y in [8, 9]) way(tag, G, dx, y, dx + 17, y);
  foreach (x in [8, 9]) way(tag, G, dx + x, 0, dx + x, 17);
  foreach (y in [8, 9]) { way(tag, L4, dx, y, dx + 5, y); way(tag, L4, dx + 12, y, dx + 17, y); }
  foreach (x in [8, 9]) { way(tag, L4, dx + x, 0, dx + x, 5); way(tag, L4, dx + x, 12, dx + x, 17); }
  // L 字: 入る側の腕の外の端 → 中心の角 → 左隣の腕の出る側の外の端
  foreach (l in [[9, 6, 9, 8, 11, 8], [11, 9, 9, 9, 9, 11], [8, 11, 8, 9, 6, 9], [6, 8, 8, 8, 8, 6]]) {
    way(tag + " L", JI, dx + l[0], l[1], dx + l[2], l[3]);
    way(tag + " L", JI, dx + l[2], l[3], dx + l[4], l[5]);
  }
  foreach (k in [[8, 7, 9, 7], [10, 8, 10, 9], [8, 10, 9, 10], [7, 8, 7, 9]]) way(tag + " link", JI, dx + k[0], k[1], dx + k[2], k[3]);
  local outs = [[8, 6], [8, 7], [10, 8], [11, 8], [9, 10], [9, 11], [6, 9], [7, 9]];
  local centers = [[8, 8], [9, 8], [8, 9], [9, 9]];
  foreach (p in outs) one(tag + " out", JO, dx + p[0], p[1]);
  foreach (p in centers) one(tag + (scramble ? " scramble" : " center"), scramble ? JO : JC, dx + p[0], p[1]);
  foreach (p in [[9, 6], [9, 7], [10, 9], [11, 9], [8, 10], [8, 11], [6, 8], [7, 8]]) expect(tag + " in", dx + p[0], p[1], G, JI);
  foreach (p in outs) expect(tag + " out", dx + p[0], p[1], G, JO);
  foreach (p in centers) expect(tag + " center", dx + p[0], p[1], G, scramble ? JO : JC);
  foreach (p in [[3, 8], [3, 9], [8, 3], [9, 3]]) expect(tag + " lane4", dx + p[0], p[1], G, L4);
}

// 4 車線（南北の x 8・9）× 2 車線（東西の y 8）
function x42(tag, dx) {
  way(tag, G, dx, 8, dx + 17, 8);
  foreach (x in [8, 9]) way(tag, G, dx + x, 0, dx + x, 17);
  foreach (x in [8, 9]) { way(tag, L4, dx + x, 0, dx + x, 5); way(tag, L4, dx + x, 11, dx + x, 17); }
  foreach (x in [8, 9]) way(tag, JI, dx + x, 6, dx + x, 10);
  way(tag + " link", JI, dx + 8, 7, dx + 9, 7);
  way(tag + " link", JI, dx + 8, 9, dx + 9, 9);
  way(tag + " 2lane", J2, dx + 7, 8, dx + 8, 8);
  way(tag + " 2lane", J2, dx + 10, 8, dx + 9, 8);
  local outs = [[8, 6], [8, 7], [9, 9], [9, 10]];
  foreach (p in outs) one(tag + " out", JO, dx + p[0], p[1]);
  foreach (p in outs) expect(tag + " out", dx + p[0], p[1], G, JO);
  foreach (p in [[9, 6], [9, 7], [8, 9], [8, 10]]) expect(tag + " in", dx + p[0], p[1], G, JI);
  foreach (p in [[7, 8], [8, 8], [9, 8], [10, 8]]) expect(tag + " 2lane", dx + p[0], p[1], G, J2);
  expect(tag + " road", dx + 3, 8, G, "-");
}

// 2 車線の十字（中心 (x,y)）か、T字路（南へ枝。tee）
function x2(tag, x, y, tee) {
  way(tag, G, x - 5, y, x + 5, y);
  way(tag, G, x, tee ? y : y - 5, x, y + 5);
  local m = tee ? J2T : J2;
  way(tag, m, x - 1, y, x + 1, y);
  way(tag, m, x, tee ? y : y - 1, x, y + 1);
  foreach (p in (tee ? [[-1, 0], [0, 0], [1, 0], [0, 1]] : [[-1, 0], [0, 0], [1, 0], [0, -1], [0, 1]]))
    expect(tag, x + p[0], y + p[1], G, m);
  expect(tag + " road", x - 3, y, G, "-");
}

foreach (n, o in ORIGINS) {
  OX = o[0]; OY = o[1];
  x4("X4", 0, false);
  x4("X4S", 22, true);
  x42("X42", 44);
  x2("X2", 5, 27, false);
  x2("T2", 19, 27, true);
  if (n == SNOW)
    report += r("climate", command_x(tool_set_climate).work(pl, c(AREA[0][0], AREA[0][1]), c(AREA[1][0], AREA[1][1]), "7"));
}
gui.close_all_windows();
return (report == "" ? "ok\n" : "check\n" + report) + checks;
