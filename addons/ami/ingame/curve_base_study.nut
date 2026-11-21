// 複線の直角のカーブで、角のタイルの版（back・front）の敷き方を比べる検討用の見本（#94）。使い方は ingame/curve_base_study.sh。
// 複線の輪（外 (0,0)-(6,6)・内 (1,1)-(5,5)）で 4 方向の角を一度に出す。画面で上の角が (0,0)、右が (6,0)、下が (6,6)、左が (0,6)。
// 輪ごとに敷き方を変え、LAYOUTS の順に東へ LDX ずつ並べる:
//   N  線ごとに版を通す（外の線は全部 back、内の線は全部 front。#88 の区画 dc と同じ敷き方）
//   R  辺ごとに奥の線を back・手前の線を front にし、角のタイルは南北の辺の版にする（sample.nut の区画 W1 と同じ。東西の辺を先に、南北の辺を後に敷く）
//   X  R と同じ辺の版で、角のタイルを東西の辺の版にする（南北の辺を先に、東西の辺を後に敷く）
// SETS の組ごとに南へ SDY ずつ並べる: [名札, back の way, front の way, back の壁, front の壁]（壁は null で重ねない）。
// 壁（way-object）は、同じ速さの物を後から敷くと前の版のまま向きだけ足される（obj/wayobj.cc の extend_wayobj）ので、
// 角のタイルに残したい版の辺を先に敷く（way と逆の順）。
// 返り値の [check] の行に、外の角のタイルとその隣（12 か所）と内の角のタイル（4 か所）の way・way-object の名前を出す（敷いた版が思ったとおりかを目で確かめる。期待値との照合はしない）。
// 名札は ASCII。行頭の空白と // で始まる行は curve_base_study.sh が消して渡す
local SETS = [
  ["iss", "iss_wtg_0240_back", "iss_wtg_0240_front", null, null],
  ["ami", "ami_rail_ballast_base_back", "ami_rail_ballast_base_front", null, null],
  ["ami+wall", "ami_rail_ballast_base_back", "ami_rail_ballast_base_front", "ami_wall_rail_back", "ami_wall_rail_front"],
  ["ami+cat", "ami_rail_ballast_base_back", "ami_rail_ballast_base_front", "ami_wall_rail_back_catenary", "ami_wall_rail_front_catenary"]
];
local LAYOUTS = ["N", "R", "X"];
local OX = 150;
local OY = 20;
local LDX = 12;
local SDY = 12;
local pl = player_x(0);
local marker = command_x(tool_set_marker);
local report = "";
local checks = "";
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
function names(x, y) {
  local t = square_x(x, y).get_ground_tile();
  local w = t.get_way(wt_rail);
  local o = t.find_object(mo_wayobj);
  return (w == null ? "-" : w.get_desc().get_name()) + (o == null ? "" : " + " + o.get_desc().get_name());
}

foreach (si, set in SETS) {
  // local は 1 つずつ書く（docs/reference/way-addon.md の 8.2）
  local wb = way_desc_x(set[1]);
  local wf = way_desc_x(set[2]);
  local ob = set[3] == null ? null : wayobj_desc_x(set[3]);
  local of = set[4] == null ? null : wayobj_desc_x(set[4]);
  if (wb == null || wf == null || (set[3] != null && (ob == null || of == null))) { report += set[0] + " desc=[missing]\n"; continue; }
  foreach (li, lay in LAYOUTS) {
    local ox = OX + li * LDX;
    local oy = OY + si * SDY;
    local c = function(x, y) { return coord3d(ox + x, oy + y, 0); };
    local s = "";
    // 名札は 4 つの角の 1 タイル外に置く（角ごとに撮った画面に、その輪の名札が入るように）
    foreach (p in [[-1, -1], [7, -1], [7, 7], [-1, 7]]) s += r("label", marker.work(pl, c(p[0], p[1]), set[0] + " " + lay));
    // 辺: [版, x0, y0, x1, y1]。外の輪の北・西は奥（back）、南・東は手前（front）。内の輪は逆
    local EW = [["back", 0, 0, 6, 0], ["front", 0, 6, 6, 6], ["front", 1, 1, 5, 1], ["back", 1, 5, 5, 5]];
    local NS = [["back", 0, 0, 0, 6], ["front", 6, 0, 6, 6], ["front", 1, 1, 1, 5], ["back", 5, 1, 5, 5]];
    if (lay == "N") {
      // 外は全部 back、内は全部 front
      foreach (e in EW) e[0] = (e[2] == 0 || e[2] == 6) ? "back" : "front";
      foreach (e in NS) e[0] = (e[1] == 0 || e[1] == 6) ? "back" : "front";
    }
    local first = lay == "X" ? NS : EW;
    local second = lay == "X" ? EW : NS;
    local way = function(e) { return command_x.build_way(pl, c(e[1], e[2]), c(e[3], e[4]), e[0] == "back" ? wb : wf, true); };
    local obj = function(e) { return command_x.build_wayobj(pl, c(e[1], e[2]), c(e[3], e[4]), e[0] == "back" ? ob : of); };
    foreach (e in first) s += r("way", way(e));
    foreach (e in second) s += r("way", way(e));
    if (ob != null) {
      foreach (e in second) s += r("wall", obj(e));
      foreach (e in first) s += r("wall", obj(e));
    }
    report += s;
    foreach (p in [[0, 0], [1, 0], [0, 1], [6, 0], [5, 0], [6, 1], [6, 6], [5, 6], [6, 5], [0, 6], [1, 6], [0, 5],
                   [1, 1], [5, 1], [5, 5], [1, 5]])
      checks += "[check] " + set[0] + " " + lay + " (" + p[0] + "," + p[1] + ") " + names(ox + p[0], oy + p[1]) + "\n";
  }
}
gui.close_all_windows();
return (report == "" ? "ok\n" : report) + checks;
