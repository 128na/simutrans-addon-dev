// AMI の道路のカーブ（一般道路の円弧・生活道路の L 字。#259。#209 の 2 本目）の見本。通常の版（壁なし）の道路で、カーブの前後のつながりを見る。
// 道路 2 種（ROADS）それぞれに、種類ごとに SPACING ずつ南へ敷く。検証用の flat_512_left_v64.sve に、温暖側 (20,20) と降雪側 (276,20) の 2 か所へ
// 同じ並びで敷き、降雪側は敷いた後に一帯を降雪に塗り直す（土地を上げたタイルは温暖に変わるため。docs/reference/way-addon.md の 8.2）。
// 使い方（アドオンのディレクトリで）: sample_parallel.sh に NUT=ingame/curve_sample.nut を付ける（撮る場所は sample_spots.sh の CURVE_SPOTS）。
// 返り値の先頭が ok なら全部敷けた。失敗した所は「名前 場所=[…]」で続く。
//
// 1 種ずつの区画（原点 (ox,oy) から）:
//   R1 1 本の輪: (0,0)-(8,8)。カーブ 4 向き（nw・ne・se・sw）
//   R2 2 本並べた輪（4 車線の直角の曲がり）: 外の輪 (12,0)-(20,8)、内の輪 (13,1)-(19,7)。壁は付けない（壁は 3 本目の #260）
//   S  坂の隣のカーブ: 東西 y=14 の (0)-(6) の (3) を 1 段上げて坂で越え、(6,14) で北へ曲がって (6,8) まで
//   D  斜めとの継ぎ目: (12,12) から南東へ 3 段の階段の先に、(15,15) で南へ曲がるカーブ
//   T  T字・十字の隣のカーブ: 東西 (20,12)-(28,12) と 南北 (24,12)-(24,18)（T字）、(24,18) から東へ (28,18) の曲がり
local ROADS = ["ami_road_local", "ami_road_general"];
local ORIGINS = [[20, 20], [276, 20]];
local SNOW = 1;
local SPACING = 30;
local AREA = [34, 22];
local pl = player_x(0);
local marker = command_x(tool_set_marker);
local report = "";
local checks = "";
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
local mode = {snow = false};
function set_slope_kept(p, s) {
  local e = command_x.set_slope(pl, p, s);
  if (e == null && mode.snow) e = command_x(tool_set_climate).work(pl, coord3d(p.x - 1, p.y - 1, 0), coord3d(p.x + 1, p.y + 1, 0), "7");
  return e;
}
function road_at(x, y) { return square_x(x, y).get_ground_tile().get_way(wt_road); }
function dirs(x, y) { local w = road_at(x, y); return w == null ? -1 : w.get_dirs(); }
function ring(w, c, x0, y0, x1, y1) {
  local s = "";
  s += r("ring n", command_x.build_way(pl, c(x0, y0), c(x1, y0), w, true));
  s += r("ring e", command_x.build_way(pl, c(x1, y0), c(x1, y1), w, true));
  s += r("ring s", command_x.build_way(pl, c(x1, y1), c(x0, y1), w, true));
  s += r("ring w", command_x.build_way(pl, c(x0, y1), c(x0, y0), w, true));
  return s;
}
function stair(w, c, x, y, n) {
  local e = null;
  for (local k = 0; k < n; k++) {
    local a = command_x.build_way(pl, c(x + k, y + k), c(x + k, y + k + 1), w, true);
    local b = command_x.build_way(pl, c(x + k, y + k + 1), c(x + k + 1, y + k + 1), w, true);
    if (a != null) e = a;
    if (b != null) e = b;
  }
  return e;
}

function lay(name, ox, oy) {
  local w = way_desc_x(name);
  if (w == null) return name + " desc=[missing]\n";
  local c = function(x, y, z = 0) { return coord3d(ox + x, oy + y, z); };
  local s = r(name + " label", marker.work(pl, c(0, -3), name + ": R1 ring / R2 double ring / S slope / D diagonal / T tee"));
  // R1
  s += ring(w, c, 0, 0, 8, 8);
  // R2
  s += ring(w, c, 12, 0, 20, 8);
  s += ring(w, c, 13, 1, 19, 7);
  // S（坂の隣のカーブ）
  s += r("S raise", set_slope_kept(c(3, 14), slope.all_up_slope));
  s += r("S rampW", set_slope_kept(c(2, 14), 12));
  s += r("S rampE", set_slope_kept(c(4, 14), 28));
  s += r("S ew", command_x.build_way(pl, c(0, 14), c(6, 14), w, true));
  s += r("S ns", command_x.build_way(pl, c(6, 14), c(6, 10), w, true));
  // D（斜めとの継ぎ目）
  s += r("D stair", stair(w, c, 12, 12, 3));
  s += r("D tail", command_x.build_way(pl, c(15, 15), c(15, 19), w, true));
  // T（T字・十字の隣のカーブ）
  s += r("T ew", command_x.build_way(pl, c(20, 12), c(28, 12), w, true));
  s += r("T ns", command_x.build_way(pl, c(24, 12), c(24, 18), w, true));
  s += r("T bend", command_x.build_way(pl, c(24, 18), c(28, 18), w, true));
  checks += "[check] " + name + " R1 corners nw=" + dirs(ox, oy) + " ne=" + dirs(ox + 8, oy) + " se=" + dirs(ox + 8, oy + 8) + " sw=" + dirs(ox, oy + 8) + "\n";
  return s;
}

foreach (n, o in ORIGINS) {
  mode.snow = n == SNOW;
  foreach (i, name in ROADS) report += lay(name, o[0], o[1] + i * SPACING);
  if (mode.snow)
    report += r("climate", command_x(tool_set_climate).work(pl, coord3d(o[0] - 3, o[1] - 4, 0),
                                                             coord3d(o[0] + AREA[0], o[1] + (ROADS.len() - 1) * SPACING + AREA[1], 0), "7"));
}
gui.close_all_windows();
return (report == "" ? "ok\n" : "check\n" + report) + checks;
