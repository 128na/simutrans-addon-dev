// AMI の道路の見本（交差点の組み合わせ）: 道路を何本か隣り合わせに並べた「多車線」どうしの交差点で、本体が十字のタイルにどの絵を選ぶかを見る。
// OTRP v64 の本体は、多車線の交差点（4×2・4×4・6×6・T4x2・T4x4）の十字を標準の十字の絵にする（KUTA 流の決まりは無くなった: teamhimeh/simutrans#816）。
// AMI の道路は分岐の絵（switch 画像 1・2）を dat に持つ（ami_dat.py の ROAD_SWITCH_IMAGES、#46）が、十字はどれも通常の十字、T字は通常の T字になるはず。
// 検証用の flat_512_left_v64.sve の温暖側 (20,20) に敷く。道路は ROADS の順に、SPACING タイルずつ南へずらして 1 種ずつ。
// 使い方（アドオンのディレクトリで）: sample_check.sh・sample_parallel.sh に NUT=ingame/road_junction_sample.nut を付ける
// （撮る場所は sample_spots.sh の JUNCTION_SPOTS）。返り値の先頭が ok なら全部敷けた。最後に確かめた値（[check] の行）が続く。
//
// 1 種ずつの区画: 原点 (ox,oy) から、x=0 から 12 ずつ COMBOS の組み合わせを 1 つずつ置く。組み合わせ [a, b] は
// 南北の道路 a 本（x=3 から 1 タイルずつ東へ、y=0〜10）と東西の道路 b 本（y=4 から 1 タイルずつ南へ、x=0〜a+5）。
// 道路 1 本は中央線のある 2 車線なので、a 本は 2a 車線（例: [2, 3] は南北 4 車線と東西 6 車線）。
// T字の組み合わせ（TEES）は x=96 から 12 ずつ。東西の道路 b 本が西から来て、南北の道路 a 本の東端の道路で止まる（手前の南北の道路は十字、
// 東端は T字。T字の枝の先が十字なので、分岐の絵があれば本体は東端の T字に「1」を出す）。
// 区画 P（y=14）: 判定に使う絵。T字 4 種と十字を固定の道具で「1」「2」に固定したもの（road_sample.nut の区画 I と同じ）と、通常の十字。
// [check] の行: 組み合わせごとに、十字のタイルの絵を北の行から順に、西から東へ並べる（nsew は通常の十字、nse2 などは T字の「2」、
// ? はどれでもない）。「1」と「2」が同じ絵なら「2」の名前で出す
local ROADS = ["ami_road_local", "ami_road_general", "ami_road_trunk", "ami_road_expressway"];
// ラウンドの版（#56）: AMI の名前（ami_ で始まるもの）の末尾に付ける。例: "_round1"。空なら今の名前（sample_parallel.sh の SUFFIX が置き換える）
local SUFFIX = "";
function wdx(n) { return way_desc_x(n.find("ami_") == 0 ? n + SUFFIX : n); }
local ORIGINS = [[20, 20]];
local SPACING = 22;
local COMBOS = [[2, 1], [1, 2], [3, 1], [1, 3], [2, 2], [2, 3], [3, 2], [3, 3]];
local TEES = [[2, 1], [2, 2]];
local TEE_X = 96;
local pl = player_x(0);
local marker = command_x(tool_set_marker);
local report = "";
local checks = "";
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
function road_at(x, y) { return square_x(x, y).get_ground_tile().get_way(wt_road); }
function img(x, y) { local w = road_at(x, y); return w == null ? -1 : w.get_image_id(); }
local pin = null;
try { pin = command_x(tool_set_switch_image); } catch (e) { pin = null; }
// [dat の絵の名前, 本線の向き, 枝の向き dx, dy（十字は 0, 0）]
local PINS = [["nse", "ns", 1, 0], ["new", "ew", 0, -1], ["nsw", "ns", -1, 0], ["sew", "ew", 0, 1], ["nsew", "ns", 0, 0]];

function lay(name, ox, oy) {
  local w = wdx(name);
  if (w == null) return name + " desc=[missing]\n";
  local c = function(x, y, z = 0) { return coord3d(ox + x, oy + y, z); };
  local line = function(x0, y0, x1, y1) { return command_x.build_way(pl, c(x0, y0), c(x1, y1), w, true); };
  local s = r(name + " label", marker.work(pl, c(0, -2), name));
  foreach (k, cb in COMBOS) {
    local bx = 12 * k, a = cb[0], b = cb[1];
    for (local i = 0; i < a; i++) s += r("ns", line(bx + 3 + i, 0, bx + 3 + i, 10));
    for (local j = 0; j < b; j++) s += r("ew", line(bx, 4 + j, bx + a + 5, 4 + j));
    s += r("label", marker.work(pl, c(bx, -1), (2 * a) + "x" + (2 * b)));
  }
  foreach (k, cb in TEES) {
    local bx = TEE_X + 12 * k, a = cb[0], b = cb[1];
    for (local i = 0; i < a; i++) s += r("T ns", line(bx + 3 + i, 0, bx + 3 + i, 10));
    for (local j = 0; j < b; j++) s += r("T ew", line(bx, 4 + j, bx + 3 + a - 1, 4 + j));
    s += r("T label", marker.work(pl, c(bx, -1), "T" + (2 * a) + "x" + (2 * b)));
  }
  // P: 判定に使う絵（「2」を先に固定し、同じ絵の「1」より先に名前を引く）
  local names = {};
  if (pin != null) {
    foreach (j, p in PINS) {
      foreach (k, choice in [1, 2]) {
        local ix = 2 + 6 * (2 * j + k), iy = 16;
        if (p[1] == "ns") s += r("P main", line(ix, iy - 2, ix, iy + 2));
        else s += r("P main", line(ix - 2, iy, ix + 2, iy));
        if (p[0] == "nsew") s += r("P cross", line(ix - 2, iy, ix + 2, iy));
        else s += r("P branch", line(ix, iy, ix + 2 * p[2], iy + 2 * p[3]));
        s += r("P pin" + choice, pin.work(pl, c(ix, iy), "" + wt_road + "," + choice));
        local n = p[0] + (choice == 1 ? "2" : "1");
        local id = img(ox + ix, oy + iy);
        if (!(id in names)) names[id] <- n;
      }
    }
  }
  // 通常の十字（固定しない。周りに分岐が無い）
  s += r("P plain", line(62, 14, 62, 18));
  s += r("P plain", line(60, 16, 64, 16));
  local plain = img(ox + 62, oy + 16);
  names[plain] <- "nsew";
  foreach (k, cb in COMBOS) {
    local bx = 12 * k, a = cb[0], b = cb[1];
    local t = "[check] " + name + " " + (2 * a) + "x" + (2 * b) + " (ns " + a + " x ew " + b + "):";
    for (local j = 0; j < b; j++) {
      t += " |";
      for (local i = 0; i < a; i++) {
        local id = img(ox + bx + 3 + i, oy + 4 + j);
        t += " " + (id in names ? names[id] : "?" + id);
      }
    }
    checks += t + "\n";
  }
  // T字の組み合わせ: 南北の道路のタイルの絵（十字は nsew、T字は通常の T字なら plain、ほかは番号）
  foreach (k, cb in TEES) {
    local bx = TEE_X + 12 * k, a = cb[0], b = cb[1];
    local t = "[check] " + name + " T" + (2 * a) + "x" + (2 * b) + ":";
    for (local j = 0; j < b; j++) {
      t += " |";
      for (local i = 0; i < a; i++) {
        local x = ox + bx + 3 + i, y = oy + 4 + j;
        local id = img(x, y);
        t += " " + (id in names ? names[id] : "d" + road_at(x, y).get_dirs() + ":" + id);
      }
    }
    checks += t + "\n";
  }
  return s;
}

foreach (n, o in ORIGINS) {
  foreach (i, name in ROADS) report += lay(name, o[0], o[1] + i * SPACING);
}
checks += "[check] pin tool=" + (pin != null) + "\n";
gui.close_all_windows();
return (report == "" ? "ok\n" : "check\n" + report) + checks;
