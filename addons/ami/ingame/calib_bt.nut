// くどさを測る見本の、橋・トンネル用（#79）: 通常の way・橋・トンネルを、同じタイルの並びで横に並べる。
// 名前で種類を分ける: "ridge" を含む名前は橋、"unnel" を含む名前はトンネル、ほかは way（比べる通常の版）。
// 橋と way は同じ線を敷く（BUSY_REF で、橋の画素のうち通常の版と重なる所を比べられる）。トンネルは坑口だけが画面に出る。
// STAGE が "pre" のときは地形だけを作る（トンネルの尾根と坂）。ingame/calib_capture.sh に PRE=1 を渡すと、地面を撮る前に
// STAGE を "pre" にしてこの nut を流し、撮った後に "lay" で流す（地形の変化を way の画素に入れないため）。
// flat_512.sve の温暖側 (20,20) と降雪側 (276,20) に敷く。降雪側は、地形を作った後と敷いた後に一帯を降雪に塗り直す
// （土地を上げたタイルは温暖に変わる。docs/reference/way-addon.md の 8.2）。
// way は WAYS の順に、DX タイルずつ東へずらす。区画（DX x 12）の中の並び（原点から）:
//   東西の 2 本: y=4・5 の (1)-(8)。橋は両端が平地から立ち上がる Ramp
//   南北の 2 本: x=7・8 の (6)-(11)。橋は同じく Ramp
//   トンネル: 東西 y=4・5 は x=3〜5 を 2 段上げた尾根、x=2・6 を 2 段の坂にして掘る。南北 x=7・8 は y=8〜10 を尾根、y=7・11 を坂
//   （pak128 の坑口は 2 段の坂だけ。坂の値は ingame/sample.nut の T1 と同じ）
// 撮る場所は区画の (5,5)（calib_capture.sh に NUT=ingame/calib_bt.nut で渡す）。1 回に並べるのは 14 本まで
// 返り値の先頭が ok なら全部敷けた
// WAYS は 1 行に書く（calib_capture.sh が WAYS_NUT で行ごと置き換える）。STAGE も 1 行に書く（PRE=1 のとき置き換える）
local WAYS = ["ami_rail_ballast", "ami_rail_ballast_bridge", "ami_rail_ballast_tunnel"];
local STAGE = "lay";
local ORIGINS = [[20, 20], [276, 20]];
local SNOW = 1;
local DX = 16;
local pl = player_x(0);
local report = "";
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
function kind(name) {
  if (name.find("unnel") != null) return "tunnel";
  return name.find("ridge") != null ? "bridge" : "way";
}
// 線の並び（[x0, y0, x1, y1]）
local LINES = [[1, 4, 8, 4], [1, 5, 8, 5], [7, 6, 7, 11], [8, 6, 8, 11]];
// トンネルの並び: [東西か, 位置, 坑口 1, 坑口 2]
local TUNNELS = [[true, 4, 2, 6], [true, 5, 2, 6], [false, 7, 7, 11], [false, 8, 7, 11]];
function pre(name, ox, oy) {
  if (kind(name) != "tunnel") return "";
  local c = function(x, y, z = 0) { return coord3d(ox + x, oy + y, z); };
  local s = "";
  foreach (t in TUNNELS) {
    local ew = t[0], at = t[1], a = t[2], b = t[3];
    for (local i = a + 1; i < b; i++) for (local k = 0; k < 2; k++)
      s += r(name + " raise", command_x.set_slope(pl, ew ? c(i, at, k) : c(at, i, k), slope.all_up_slope));
    s += r(name + " ramp1", command_x.set_slope(pl, ew ? c(a, at) : c(at, a), ew ? 24 : 8));
    s += r(name + " ramp2", command_x.set_slope(pl, ew ? c(b, at) : c(at, b), ew ? 56 : 72));
  }
  return s;
}
function lay(name, ox, oy) {
  local c = function(x, y, z = 0) { return coord3d(ox + x, oy + y, z); };
  local k = kind(name), s = "";
  if (k == "tunnel") {
    foreach (t in TUNNELS) s += r(name + " tunnel", command_x(tool_build_tunnel).work(pl, t[0] ? c(t[2], t[1]) : c(t[1], t[2]), name));
    // 坑口のタイルにトンネルがあるかを確かめる（名前は見ない。トンネルの物の desc をスクリプトから引けないため）
    try {
      if (square_x(ox + 2, oy + 4).get_ground_tile().find_object(mo_tunnel) == null) s += name + " check=[no tunnel]\n";
    } catch (e) s += name + " check error=[" + e + "]\n";
    return s;
  }
  if (k == "bridge") {
    local br = bridge_desc_x(name);
    foreach (q in LINES) s += r(name + " bridge", command_x.build_bridge(pl, c(q[0], q[1]), c(q[2], q[3]), br));
    // 端のタイルに橋があるかを確かめる（名前は見ない）
    try {
      if (square_x(ox + 1, oy + 4).get_ground_tile().find_object(mo_bridge) == null) s += name + " check=[no bridge]\n";
    } catch (e) s += name + " check error=[" + e + "]\n";
    return s;
  }
  local w = way_desc_x(name);
  if (w == null) return name + " desc=[missing]\n";
  foreach (q in LINES) s += r(name + " line", command_x.build_way(pl, c(q[0], q[1]), c(q[2], q[3]), w, true));
  local t = square_x(ox + 4, oy + 4).get_ground_tile().get_way(w.get_waytype());
  if (t == null || t.get_desc().get_name() != name) s += name + " check=[" + (t == null ? "none" : t.get_desc().get_name()) + "]\n";
  return s;
}
foreach (n, o in ORIGINS) {
  foreach (i, name in WAYS) report += (STAGE == "pre" ? pre : lay)(name, o[0] + i * DX, o[1]);
  if (n == SNOW) report += r("climate", command_x(tool_set_climate).work(pl, coord3d(o[0] - 3, o[1] - 3, 0),
                                                      coord3d(o[0] + WAYS.len() * DX + 3, o[1] + 15, 0), "7"));
}
return report == "" ? "ok" : report;
