// 交差点の路面表示（#156）の見本。道路の交差点を作り、交差点の手前の 2 タイルに右折レーンの表示を敷く（ingame/marking.sh で流す）。
// 敷き方（README の「交差点の路面表示の作り」。関数 approach）: 口のタイル S は交差点の隣、導流帯のタイル T は S の手前
//   2 車線: 1. T から S へ ami_mark_taper  2. S だけに ami_mark_stop（1 タイル。向きはそのままで名前だけが置き換わる）
//   4 車線: 1. S から、進む向きの右の隣（出る側の口）へ ami_mark_branch（枝。絵は無い）
//           2. 出る側の口から交差点のタイルへ ami_mark_crosswalk_wide  3. T から S へ ami_mark_stop_wide
// 区画（原点 OX・OY から）:
//   C（中心 (6,4)）: 一般道路の十字。4 つの腕に右折レーン
//   P（中心 (16,4)）: 一般道路の十字。南北の腕だけ（東西が優先）
//   T（中心 (26,4)）: 一般道路の T字（南へ枝）。3 つの腕
//   W（交差点 (8..9, 12..13)）: 一般道路の 4 車線どうしの十字（ami_road_general_lane1・lane2 を 2 本ずつ並べる。奥は lane1）。
//      左側通行: 東西の道は北が東行き、南北の道は東が南行き
//   O（y 4・12。x 36〜）: 敷いた順の見本。西の腕だけに敷き、途中で止めた物を東へ並べる
//      2 車線（y 4）: 交差点 (38,4) は 1 だけ、(44,4) は 1→2（できあがり）、(50,4) は反対の順（ami_mark_stop を T から S へ敷き、
//         T だけに ami_mark_taper。できあがりは 44 と同じ）
//      4 車線（y 12）: 交差点の西の列 38 は 1 だけ、44 は 1→2、50 は 1→2→3（できあがり）
//   K（中心 (60,4)）: 一般道路の十字の両脇に歩道（ami_sidewalk）を敷き、4 つの腕に右折レーン（口の右の隣が歩道でも敷ける）
// 返り値: 失敗した所と、[link] の行（タイルの表示の名前と向き）
local OX = 20;
local OY = 20;
local pl = player_x(0);
local report = "";
function r(name, v) { if (v != null) report += name + "=[" + v + "]\n"; }
function c(x, y) { return coord3d(OX + x, OY + y, 0); }
function way(tag, n, a, b) { r(tag, command_x.build_way(pl, a, b, way_desc_x(n), true)); }
function look(tag, x, y) {
  local w = tile_x(OX + x, OY + y, 0).get_way(wt_rail);
  report += "[link] " + tag + " (" + x + "," + y + ") " + (w == null ? "-" : w.get_desc().get_name() + "/d" + w.get_dirs()) + "\n";
}
// 口 (x,y) に、交差点の向き (dx,dy) で右折レーンを敷く。steps は敷く手順（上の番号）。画面の y は南が正なので、進む向きの右は (-dy, dx)
function approach(tag, kind, x, y, dx, dy, steps = [1, 2, 3]) {
  local tx = x - dx, ty = y - dy, rx = x - dy, ry = y + dx;
  foreach (s in steps) {
    if (kind == "ami_mark_stop") {
      if (s == 1) way(tag + " taper", "ami_mark_taper", c(tx, ty), c(x, y));
      if (s == 2) way(tag + " stop", kind, c(x, y), c(x, y));
      if (s == -1) way(tag + " stop", kind, c(tx, ty), c(x, y));       // 反対の順の 1
      if (s == -2) way(tag + " taper", "ami_mark_taper", c(tx, ty), c(tx, ty));  // 反対の順の 2
    } else {
      if (s == 1) way(tag + " branch", "ami_mark_branch", c(x, y), c(rx, ry));
      if (s == 2) way(tag + " out", "ami_mark_crosswalk_wide", c(rx, ry), c(rx + dx, ry + dy));
      if (s == 3) way(tag + " turn", kind, c(tx, ty), c(x, y));
    }
  }
  look(tag + " taper", tx, ty); look(tag + " mouth", x, y); look(tag + " right", rx, ry);
}

local G = "ami_road_general";
local S2 = "ami_mark_stop", S4 = "ami_mark_stop_wide";
function cross(tag, x, y) { way(tag + " ew", G, c(x - 4, y), c(x + 4, y)); way(tag + " ns", G, c(x, y - 4), c(x, y + 4)); }
// C
cross("C", 6, 4);
approach("C w", S2, 5, 4, 1, 0); approach("C e", S2, 7, 4, -1, 0);
approach("C n", S2, 6, 3, 0, 1); approach("C s", S2, 6, 5, 0, -1);
look("C center", 6, 4);
// P
cross("P", 16, 4);
approach("P n", S2, 16, 3, 0, 1); approach("P s", S2, 16, 5, 0, -1);
look("P center", 16, 4);
// T
way("T ew", G, c(22, 4), c(30, 4)); way("T s", G, c(26, 4), c(26, 8));
approach("T w", S2, 25, 4, 1, 0); approach("T e", S2, 27, 4, -1, 0); approach("T s", S2, 26, 5, 0, -1);
look("T center", 26, 4);
// 4 車線どうしの十字。x0 は交差点の西の列、y0 は北の行
function wide_roads(tag, x0, y0) {
  way(tag + " ew1", G + "_lane1", c(x0 - 4, y0), c(x0 + 5, y0));
  way(tag + " ew2", G + "_lane2", c(x0 - 4, y0 + 1), c(x0 + 5, y0 + 1));
  way(tag + " ns1", G + "_lane1", c(x0, y0 - 4), c(x0, y0 + 5));
  way(tag + " ns2", G + "_lane2", c(x0 + 1, y0 - 4), c(x0 + 1, y0 + 5));
}
// W
wide_roads("W", 8, 12);
approach("W w", S4, 7, 12, 1, 0);  approach("W e", S4, 10, 13, -1, 0);
approach("W n", S4, 9, 11, 0, 1);  approach("W s", S4, 8, 14, 0, -1);
look("W inner nw", 8, 12); look("W inner se", 9, 13);
// O: 敷いた順
cross("O2a", 38, 4); approach("O2a w", S2, 37, 4, 1, 0, [1]);
cross("O2b", 44, 4); approach("O2b w", S2, 43, 4, 1, 0, [1, 2]);
cross("O2c", 50, 4); approach("O2c w", S2, 49, 4, 1, 0, [-1, -2]);
wide_roads("O4a", 38, 12); approach("O4a w", S4, 37, 12, 1, 0, [1]);
wide_roads("O4b", 44, 12); approach("O4b w", S4, 43, 12, 1, 0, [1, 2]);
wide_roads("O4c", 50, 12); approach("O4c w", S4, 49, 12, 1, 0, [1, 2, 3]);
// K: 歩道つきの十字
cross("K", 60, 4);
foreach (d in [-1, 1]) foreach (e in [-1, 1]) {  // 角ごとに L 字の歩道（道路は横切らない）
  way("K sw", "ami_sidewalk", c(60 + 4 * e, 4 + d), c(60 + e, 4 + d));
  way("K sw", "ami_sidewalk", c(60 + e, 4 + d), c(60 + e, 4 + 4 * d));
}
approach("K w", S2, 59, 4, 1, 0); approach("K e", S2, 61, 4, -1, 0);
approach("K n", S2, 60, 3, 0, 1); approach("K s", S2, 60, 5, 0, -1);
gui.close_all_windows();
return report;
