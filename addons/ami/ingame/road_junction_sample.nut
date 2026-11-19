// AMI の道路の見本（交差点の組み合わせ）: 道路を何本か隣り合わせに並べた「多車線」どうしの交差点で、本体が十字のタイルにどの絵を選ぶかを見る。
// 本体（OTRP の boden/wege/weg.cc の select_switch_road_image）は、ex 画像の無い way の十字で、隣が T字か十字なら、その隣の向きの
// T字の「2」の絵（dat の image[nse2] など）を十字のタイルに出す。AMI の道路の「2」は十字の形に停止線を引いた絵（README の「道路の作り」）。
// 検証用の flat_512.sve の温暖側 (20,20) に敷く。道路は ROADS の順に、SPACING タイルずつ南へずらして 1 種ずつ。
// 使い方（アドオンのディレクトリで）: sample_check.sh・sample_parallel.sh に NUT=ingame/road_junction_sample.nut を付ける
// （撮る場所は sample_spots.sh の JUNCTION_SPOTS）。返り値の先頭が ok なら全部敷けた。最後に確かめた値（[check] の行）が続く。
//
// 1 種ずつの区画: 原点 (ox,oy) から、x=0 から 12 ずつ COMBOS の組み合わせを 1 つずつ置く。組み合わせ [a, b] は
// 南北の道路 a 本（x=3 から 1 タイルずつ東へ、y=0〜10）と東西の道路 b 本（y=4 から 1 タイルずつ南へ、x=0〜a+5）。
// 道路 1 本は中央線のある 2 車線なので、a 本は 2a 車線（例: [2, 3] は南北 4 車線と東西 6 車線）。
// 区画 P（y=14）: 判定に使う絵。T字 4 種と十字を固定の道具で「1」「2」に固定したもの（road_sample.nut の区画 I と同じ）と、通常の十字。
// [check] の行: 組み合わせごとに、十字のタイルの絵を北の行から順に、西から東へ並べる（nsew は通常の十字、nse2 などは T字の「2」、
// ? はどれでもない）。「1」と「2」が同じ絵なら「2」の名前で出す
local ROADS = ["ami_road_local", "ami_road_general", "ami_road_expressway"];
local ORIGINS = [[20, 20]];
local SPACING = 22;
local COMBOS = [[2, 1], [1, 2], [3, 1], [1, 3], [2, 2], [2, 3], [3, 2], [3, 3]];
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
  local w = way_desc_x(name);
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
  return s;
}

foreach (n, o in ORIGINS) {
  foreach (i, name in ROADS) report += lay(name, o[0], o[1] + i * SPACING);
}
checks += "[check] pin tool=" + (pin != null) + "\n";
gui.close_all_windows();
return (report == "" ? "ok\n" : "check\n" + report) + checks;
