// AMI の道路の路面表示の版（ami_road_<種類>_lane<n>。#121）の見本。道路 2 種（ROADS）それぞれに、種類ごとに SPACING ずつ南へ敷く。
// 検証用の flat_512.sve に、温暖側 (20,20) と降雪側 (276,20) の 2 か所へ同じ並びで敷き、降雪側は一帯を降雪に塗り直す。
// 使い方（アドオンのディレクトリで）: sample_parallel.sh に NUT=ingame/lane_sample.nut を付ける（撮る場所は sample_spots.sh の LANE_SPOTS）。
// 返り値の先頭が ok なら全部敷けて、[check] で比べた way も期待どおり。違えば先頭が check で、「名前 場所=[…]」が続く。最後に確かめた値（[check] の行）が続く。
//
// 1 種ずつの区画（原点 (ox,oy) から。並びは奥＝北・西から）:
//   L4 東西の 4 車線: y=0 に lane1、y=1 に lane2（x=0〜10）。(5,-2)-(5,3) を通常の版の道路で横切る（十字）
//   L6 東西の 6 車線: y=4・5・6 に lane3・lane4・lane5
//   L8 東西の 8 車線: y=8・9・10・11 に lane3・lane6・lane7・lane5。(5,7)-(5,13) を通常の版で横切る
//   LN 南北の 4 車線: x=13 に lane1、x=14 に lane2（y=0〜8）。(12,4)-(16,4) を通常の版で横切る
//   LW 分離帯とそろえる: y=15 に lane1 と壁 back、y=16 に lane2 と front_divider（x=0〜10）。
//      y=19・20 に lane1・lane2 と、y=20 に center_divider（壁なし）
//   LD 近い斜め: (18,0) から南東へ 5 段、奥の線に lane1、1 タイル東の手前の線に lane2
//   LD6 近い斜めの 6 車線: (18,8) から南東へ 5 段、lane3・lane4・lane5 を 1 タイルずつ東へ
local ROADS = ["ami_road_general", "ami_road_expressway"];
local ORIGINS = [[20, 20], [276, 20]];
local SNOW = 1;
local SPACING = 24;
local AREA = [30, 22];
local pl = player_x(0);
local marker = command_x(tool_set_marker);
local report = "";
local checks = "";
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
function names(x, y) {
  local t = square_x(x, y).get_ground_tile();
  local w = t.get_way(wt_road), o = t.find_object(mo_wayobj);
  return (w == null ? "-" : w.get_desc().get_name() + " d" + w.get_dirs()) + "+" + (o == null ? "-" : o.get_desc().get_name());
}
// タイルの道路の名前が want でなければ、返り値に足す（返り値の先頭が check になる）
function expect(tag, x, y, want) {
  checks += "[check] " + tag + " " + names(x, y) + "\n";
  local w = square_x(x, y).get_ground_tile().get_way(wt_road);
  local got = w == null ? "-" : w.get_desc().get_name();
  return got == want ? "" : tag + " want=[" + want + "] got=[" + got + "]\n";
}
function stair(w, x, y, n) {
  local e = null;
  for (local k = 0; k < n; k++) {
    local a = command_x.build_way(pl, coord3d(x + k, y + k, 0), coord3d(x + k, y + k + 1, 0), w, true);
    local b = command_x.build_way(pl, coord3d(x + k, y + k + 1, 0), coord3d(x + k + 1, y + k + 1, 0), w, true);
    if (a != null) e = a;
    if (b != null) e = b;
  }
  return e;
}

function lay(name, ox, oy) {
  local w = way_desc_x(name);
  if (w == null) return name + " desc=[missing]\n";
  local ln = {};
  for (local n = 1; n <= 7; n++) {
    ln[n] <- way_desc_x(name + "_lane" + n);
    if (ln[n] == null) return name + "_lane" + n + " desc=[missing]\n";
  }
  local od = {};
  foreach (v in ["back", "front_divider", "center_divider"]) {
    od[v] <- wayobj_desc_x("ami_wall_road_" + v);
    if (od[v] == null) return "ami_wall_road_" + v + " desc=[missing]\n";
  }
  local c = function(x, y) { return coord3d(ox + x, oy + y, 0); };
  local row = function(tag, n, y) { return r(tag, command_x.build_way(pl, c(0, y), c(10, y), ln[n], true)); };
  local s = r(name + " label", marker.work(pl, c(0, -3), name + ": L4 / L6 / L8 ew lanes, LN ns, LW with divider, LD close diagonal"));
  // L4
  s += row("L4 1", 1, 0) + row("L4 2", 2, 1);
  s += r("L4 cross", command_x.build_way(pl, c(5, -2), c(5, 3), w, true));
  s += expect(name + " L4 (2,0)", ox + 2, oy, name + "_lane1") + expect(name + " L4 (2,1)", ox + 2, oy + 1, name + "_lane2");
  // 交差点のタイルは、横切った通常の版に置き換わる（通常の版の十字の絵）
  s += expect(name + " L4 (5,1)", ox + 5, oy + 1, name);
  // L6
  s += row("L6 3", 3, 4) + row("L6 4", 4, 5) + row("L6 5", 5, 6);
  s += expect(name + " L6 (2,4)", ox + 2, oy + 4, name + "_lane3") + expect(name + " L6 (2,5)", ox + 2, oy + 5, name + "_lane4")
     + expect(name + " L6 (2,6)", ox + 2, oy + 6, name + "_lane5");
  // L8
  s += row("L8 3", 3, 8) + row("L8 6", 6, 9) + row("L8 7", 7, 10) + row("L8 5", 5, 11);
  s += r("L8 cross", command_x.build_way(pl, c(5, 7), c(5, 13), w, true));
  s += expect(name + " L8 (2,9)", ox + 2, oy + 9, name + "_lane6") + expect(name + " L8 (2,10)", ox + 2, oy + 10, name + "_lane7");
  // LN
  s += r("LN 1", command_x.build_way(pl, c(13, 0), c(13, 8), ln[1], true));
  s += r("LN 2", command_x.build_way(pl, c(14, 0), c(14, 8), ln[2], true));
  s += r("LN cross", command_x.build_way(pl, c(12, 4), c(16, 4), w, true));
  s += expect(name + " LN (13,2)", ox + 13, oy + 2, name + "_lane1");
  // LW
  s += row("LW 1", 1, 15) + row("LW 2", 2, 16);
  s += r("LW back", command_x.build_wayobj(pl, c(0, 15), c(10, 15), od["back"]));
  s += r("LW divider", command_x.build_wayobj(pl, c(0, 16), c(10, 16), od["front_divider"]));
  s += row("LW0 1", 1, 19) + row("LW0 2", 2, 20);
  s += r("LW0 divider", command_x.build_wayobj(pl, c(0, 20), c(10, 20), od["center_divider"]));
  s += expect(name + " LW (3,16)", ox + 3, oy + 16, name + "_lane2");
  // LD
  s += r("LD 1", stair(ln[1], ox + 18, oy, 5)) + r("LD 2", stair(ln[2], ox + 19, oy, 5));
  s += expect(name + " LD (18,1)", ox + 18, oy + 1, name + "_lane1");
  s += r("LD6 3", stair(ln[3], ox + 18, oy + 8, 5)) + r("LD6 4", stair(ln[4], ox + 19, oy + 8, 5))
     + r("LD6 5", stair(ln[5], ox + 20, oy + 8, 5));
  s += expect(name + " LD6 (18,9)", ox + 18, oy + 9, name + "_lane3");
  return s;
}

foreach (n, o in ORIGINS) {
  foreach (i, name in ROADS) report += lay(name, o[0], o[1] + i * SPACING);
  if (n == SNOW)
    report += r("climate", command_x(tool_set_climate).work(pl, coord3d(o[0] - 3, o[1] - 4, 0),
                                                             coord3d(o[0] + AREA[0], o[1] + (ROADS.len() - 1) * SPACING + AREA[1], 0), "7"));
}
gui.close_all_windows();
return (report == "" ? "ok\n" : "check\n" + report) + checks;
