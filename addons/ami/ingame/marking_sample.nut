// 交差点の路面表示（#156）の見本。道路の交差点を作り、口のタイルから交差点のタイルへ表示を敷く（ingame/marking.sh で流す）。
// 区画（原点 OX・OY から）:
//   C（中心 (6,4)）: 一般道路の十字。4 つの口に ami_mark_stop
//   P（中心 (16,4)）: 一般道路の十字。南北の 2 つの口だけに ami_mark_stop（東西が優先。交差点のタイルは表示の直線になり、何も描かない）
//   T（中心 (26,4)）: 一般道路の T字（南へ枝）。3 つの口に ami_mark_stop
//   W（交差点 (8..9, 12..13)）: 4 車線どうしの十字（ami_road_general_lane1・lane2 を 2 本ずつ並べる。奥は lane1）。入る側の口に
//      ami_mark_stop_wide、出る側の口に ami_mark_crosswalk_wide（左側通行: 東西の道は北が東行き、南北の道は東が南行き）
//   E（交差点 (22..23, 12..13)）: 高速道路の 4 車線どうしの十字（W と同じ並び）
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
// 口 (x,y) から交差点の隣のタイル (x+dx, y+dy) へ表示を敷く
function mouth(tag, n, x, y, dx, dy) { way(tag, n, c(x, y), c(x + dx, y + dy)); look(tag, x, y); }

local G = "ami_road_general";
// C
way("C ew", G, c(2, 4), c(10, 4)); way("C ns", G, c(6, 0), c(6, 8));
mouth("C w", "ami_mark_stop", 5, 4, 1, 0); mouth("C e", "ami_mark_stop", 7, 4, -1, 0);
mouth("C n", "ami_mark_stop", 6, 3, 0, 1); mouth("C s", "ami_mark_stop", 6, 5, 0, -1);
look("C center", 6, 4);
// P
way("P ew", G, c(12, 4), c(20, 4)); way("P ns", G, c(16, 0), c(16, 8));
mouth("P n", "ami_mark_stop", 16, 3, 0, 1); mouth("P s", "ami_mark_stop", 16, 5, 0, -1);
look("P center", 16, 4);
// T
way("T ew", G, c(22, 4), c(30, 4)); way("T s", G, c(26, 4), c(26, 8));
mouth("T w", "ami_mark_stop", 25, 4, 1, 0); mouth("T e", "ami_mark_stop", 27, 4, -1, 0);
mouth("T s", "ami_mark_stop", 26, 5, 0, -1);
look("T center", 26, 4);
// W・E: 4 車線どうしの十字。x0 は交差点の西の列
function wide(tag, road, x0) {
  local y0 = 12;
  way(tag + " ew1", road + "_lane1", c(x0 - 4, y0), c(x0 + 5, y0));
  way(tag + " ew2", road + "_lane2", c(x0 - 4, y0 + 1), c(x0 + 5, y0 + 1));
  way(tag + " ns1", road + "_lane1", c(x0, y0 - 4), c(x0, y0 + 5));
  way(tag + " ns2", road + "_lane2", c(x0 + 1, y0 - 4), c(x0 + 1, y0 + 5));
  local IN = "ami_mark_stop_wide", OUT = "ami_mark_crosswalk_wide";
  mouth(tag + " w in", IN, x0 - 1, y0, 1, 0);         mouth(tag + " w out", OUT, x0 - 1, y0 + 1, 1, 0);
  mouth(tag + " e in", IN, x0 + 2, y0 + 1, -1, 0);    mouth(tag + " e out", OUT, x0 + 2, y0, -1, 0);
  mouth(tag + " n in", IN, x0 + 1, y0 - 1, 0, 1);     mouth(tag + " n out", OUT, x0, y0 - 1, 0, 1);
  mouth(tag + " s in", IN, x0, y0 + 2, 0, -1);        mouth(tag + " s out", OUT, x0 + 1, y0 + 2, 0, -1);
  look(tag + " inner nw", x0, y0); look(tag + " inner se", x0 + 1, y0 + 1);
}
wide("W", G, 8);
wide("E", "ami_road_expressway", 22);
gui.close_all_windows();
return report;
