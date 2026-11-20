// AMI の歩道の見本: ami_sidewalk を道路の隣のタイルに敷き、縁石が道路とつながるかを見る（ACCEPTANCE の 5-1）。
// 道路は UNDER の順に SPACING タイルずつ南へずらす（AMI の道路 3 種・pak128 標準の Road_050）。名札（ASCII）付き。
// 検証用の flat_512.sve に、温暖側 (20,24) と降雪側 (276,24) の 2 か所へ同じ並びで敷く。降雪側は敷いた後に一帯を降雪に塗り直す。
// 使い方（アドオンのディレクトリで）: sample_parallel.sh に NUT=ingame/sidewalk_sample.nut を付ける（撮る場所は sample_spots.sh の SIDEWALK_SPOTS）。
// 返り値の先頭が ok なら全部敷けた。失敗した所は「名前 場所=[…]」で続く。最後に確かめた値（[check] の行）が続く。
//
// 1 つの道路ごとの区画（40x11）。原点 (ox,oy) から:
//   R 交差点の四隅: 東西の道路 (0,2)-(12,2) と南北の道路 (6,-2)-(6,6) の十字。歩道は四隅のブロックを L字に囲む（交差点のタイルは空ける）
//   Q 広場と 1 タイル: (14,0)-(16,2) の 3x3 の歩道（東西の道路 (13,3)-(17,3) の北）、(19,0) に 1 タイルの歩道
//   S 坂: (22,·) の南北の道路の両脇 (21,·)・(23,·) に歩道。(·,3) を 1 段上げた坂。T は急坂（2 段。(26〜28,·)）
//   D 斜めの道路: (32,1) から南東への階段の道路と、その両脇の階段の歩道（北東 (33,0) から・南西 (31,2) から）
//   X 横切り: 東西の歩道 (40,2)-(48,2) を、南北の道路 (42,0)-(42,4) と pak128 の運河 canal_020 (46,0)-(46,4) が横切る（歩道の waytype の確かめ）
// [check] の行: 歩道を敷いた後も道路の向き（get_dirs）と絵が変わらないか（road=）、歩道の waytype、交差点の隣の歩道の向き（R の (5,1) は西と北の L字）、
//   区画 X の横切ったタイルの way（道路は歩道と 2 本の way になり踏切の物が立つか。運河は歩道を置き換えるか）。
local SIDE = "ami_sidewalk";
local UNDER = ["ami_road_local", "ami_road_general", "ami_road_expressway", "Road_050"];
// ラウンドの版（#56）: AMI の名前（ami_ で始まるもの）の末尾に付ける。例: "_round1"。空なら今の名前（sample_parallel.sh の SUFFIX が置き換える）
local SUFFIX = "";
function wdx(n) { return way_desc_x(n.find("ami_") == 0 ? n + SUFFIX : n); }
local ORIGINS = [[20, 24], [276, 24]];
local SNOW = 1;
local SPACING = 14;
local AREA = [50, 11];
local pl = player_x(0);
local marker = command_x(tool_set_marker);
local report = "";
local checks = "";
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
function way_at(x, y, wt) { return square_x(x, y).get_ground_tile().get_way(wt); }
function road_state(x, y) { local w = way_at(x, y, wt_road); return w == null ? "-" : w.get_dirs() + "#" + w.get_image_id(); }

function lay(under, ox, oy) {
  local sd = wdx(SIDE);
  if (sd == null) return SIDE + " desc=[missing]\n";
  local rd = wdx(under);
  if (rd == null) return under + " desc=[missing]\n";
  local swt = sd.get_waytype();
  local c = function(x, y, z = 0) { return coord3d(ox + x, oy + y, z); };
  local road = function(x0, y0, x1, y1) { return command_x.build_way(pl, c(x0, y0), c(x1, y1), rd, true); };
  local side = function(x0, y0, x1, y1) { return command_x.build_way(pl, c(x0, y0), c(x1, y1), sd, true); };
  local stair = function(f, x, y, n) {
    local e = null;
    for (local k = 0; k < n; k++) {
      local a = f(x + k, y + k, x + k, y + k + 1);
      local b = f(x + k, y + k + 1, x + k + 1, y + k + 1);
      if (a != null) e = a;
      if (b != null) e = b;
    }
    return e;
  };
  local s = r(under + " label", marker.work(pl, c(0, -4), SIDE + " / " + under));
  // R
  s += r("R road ew", road(0, 2, 12, 2));
  s += r("R road ns", road(6, -2, 6, 6));
  local probe = [[3, 2], [6, 2], [9, 2], [6, 0], [6, 4]];
  local before = probe.map(function(p) { return road_state(ox + p[0], oy + p[1]); });
  s += r("R nw", side(0, 1, 5, 1)); s += r("R nw2", side(5, -2, 5, 1));
  s += r("R ne", side(7, 1, 12, 1)); s += r("R ne2", side(7, -2, 7, 1));
  s += r("R sw", side(0, 3, 5, 3)); s += r("R sw2", side(5, 3, 5, 6));
  s += r("R se", side(7, 3, 12, 3)); s += r("R se2", side(7, 3, 7, 6));
  // Q
  s += r("Q road", road(13, 3, 17, 3));
  for (local k = 0; k < 3; k++) {
    s += r("Q ew" + k, side(14, k, 16, k));
    s += r("Q ns" + k, side(14 + k, 0, 14 + k, 2));
  }
  s += r("Q single", side(19, 0, 19, 0));
  s += r("Q label", marker.work(pl, c(14, -2), "plaza / single"));
  // S・T（坂・急坂）
  foreach (h in [[22, 1], [27, 2]]) {
    local cx = h[0], n = h[1];
    for (local x = cx - 1; x <= cx + 1; x++) {
      for (local j = 0; j < n; j++) s += r("hill raise", command_x.set_slope(pl, c(x, 3, j), slope.all_up_slope));
      s += r("hill rampN", command_x.set_slope(pl, c(x, 2), 4 * n));
      s += r("hill rampS", command_x.set_slope(pl, c(x, 4), 36 * n));
    }
    s += r("hill road", road(cx, 0, cx, 6));
    s += r("hill sideW", side(cx - 1, 0, cx - 1, 6));
    s += r("hill sideE", side(cx + 1, 0, cx + 1, 6));
  }
  // D
  s += r("D road", stair(road, 32, 1, 4));
  s += r("D sideNE", stair(side, 33, 0, 4));
  s += r("D sideSW", stair(side, 31, 2, 4));
  // X
  s += r("X side", side(40, 2, 48, 2));
  s += r("X road", road(42, 0, 42, 4));
  local canal = way_desc_x("canal_020");
  if (canal != null) s += r("X canal", command_x.build_way(pl, c(46, 0), c(46, 4), canal, true));
  s += r("X label", marker.work(pl, c(40, -2), "x road / canal"));
  local xr = square_x(ox + 42, oy + 2).get_ground_tile(), xc = way_at(ox + 46, oy + 2, swt), xs = way_at(ox + 44, oy + 2, swt);
  local objs = "";
  foreach (o in xr.get_objects()) objs += "" + o.get_type() + ",";
  checks += "[check] " + under + " X road_tile two_ways=" + xr.has_two_ways() + " objs=" + objs
            + " canal_tile=" + (xc == null ? "-" : xc.get_desc().get_name()) + " side(44,2)=" + (xs == null ? "-" : xs.get_desc().get_name() + "/d" + xs.get_dirs()) + "\n";
  local after = probe.map(function(p) { return road_state(ox + p[0], oy + p[1]); });
  local same = true;
  foreach (i, b in before) if (b != after[i]) same = false;
  local corner = way_at(ox + 5, oy + 1, swt);
  checks += "[check] " + under + " road=" + (same ? "same" : "CHANGED " + before.reduce(@(a, b) a + "," + b) + " -> " + after.reduce(@(a, b) a + "," + b))
            + " sidewalk_wt=" + swt + " corner(5,1)=" + (corner == null ? "-" : corner.get_dirs()) + "\n";
  return s;
}

foreach (n, o in ORIGINS) {
  foreach (i, under in UNDER) report += lay(under, o[0], o[1] + i * SPACING);
  if (n == SNOW)
    report += r("climate", command_x(tool_set_climate).work(pl, coord3d(o[0] - 2, o[1] - 6, 0),
                                                             coord3d(o[0] + AREA[0], o[1] + (UNDER.len() - 1) * SPACING + AREA[1], 0), "7"));
}
gui.close_all_windows();
return (report == "" ? "ok\n" : "check\n" + report) + checks;
