// AMI の見本: 絵を作った way の絵を、周りのタイルとつながった形で全部出す（全方位・分岐・近い斜め・坂・雪）。
// 検証用の flat_512.sve に、温暖側 (20,20) と降雪側 (276,20) の 2 か所へ同じ並びで敷く。降雪側は敷いた後に一帯を降雪に塗り直す
// （土地を上げたタイルは温暖に変わり、坂の道が雪の絵にならないため。docs/reference/way-addon.md の 8.2）。
// way は WAYS の順に、SPACING タイルずつ南へずらして 1 本ずつ敷く。名札（ASCII）付き。見つからない way は失敗として報告する（WAYS には dat と pak を作った way だけを足す）。
// 使い方: ゲームを -mcp-port 47123 で起動し、flat_512 を開いて
//   python <mcp_client.py> --port 47123 --timeout 300 --run-squirrel "$(cat ingame/sample.nut)"
// 返り値の先頭が ok なら全部敷けた。失敗した所は「名前 場所=[…]」で続く。最後に確かめた値（[check] の行）が続く。
//
// 1 本ずつの区画（64x27）。原点 (ox,oy) から（撮る場所は ingame/sample_capture.sh の SPOTS）:
//   A 行き止まり 4 方向: 東西 (0,0)-(2,0)・南北 (4,0)-(4,2)                       … image[w] [e] [n] [s]
//   F 1 タイルだけ: (6,0)                                                         … image[-]
//   C 斜め 2 本（階段）: (8,0) から南東へ・(13,3) から北東へ 3 段                   … diagonal 4
//   B 輪と十字: (0,4)-(6,10) の輪に (3,4)-(3,10) と (0,7)-(6,7)                   … image[ns] [ew]、カーブ 4、T字 4、十字
//   D 坂の十字: (11,7) を 1 段上げ、四方を坂にして越える                          … imageup 4
//   E 急坂の十字: (17,7) を 2 段上げ、四方を 2 段の坂にして越える                  … imageup2 4
//   G 近い斜め: (22,0) から南東へ・(22,18) から北東へ、1 タイルずらした斜め 2 本    … diagonal[close1] [close2]
//   I 十字の分岐の絵を固定: (2,14) を選択 1・(8,14) を選択 2                       … image[nsew1] [nsew2]（固定の道具がある OTRP だけ）
//   H 分岐の自動選択 8 通り: y=22 の行に x=3 から 8 ずつ                          … image[nse1]〜[sew2]
local WAYS = ["ami_rail_ballast"];
local ORIGINS = [[20, 20], [276, 20]];
local SNOW = 1;          // ORIGINS の何番目を降雪に塗り直すか
local SPACING = 30;
local AREA = [64, 27];   // 区画の大きさ（降雪の塗り直しに使う）
local pl = player_x(0);
local marker = command_x(tool_set_marker);
local report = "";
local checks = "";
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
function stair(w, x, y, n, dy) {
  local e = null;
  for (local k = 0; k < n; k++) {
    local a = command_x.build_way(pl, coord3d(x + k, y + k * dy, 0), coord3d(x + k, y + (k + 1) * dy, 0), w, true);
    local b = command_x.build_way(pl, coord3d(x + k, y + (k + 1) * dy, 0), coord3d(x + k + 1, y + (k + 1) * dy, 0), w, true);
    if (a != null) e = a;
    if (b != null) e = b;
  }
  return e;
}
// 分岐の絵を固定する道具（OTRP の改修版だけにある）。無ければ null
local pin = null;
try { pin = command_x(tool_set_switch_image); } catch (e) { pin = null; }
// [選ばれる絵, 本線の向き, 枝の出る向き dx, dy, 枝が曲がる向き dx, dy]（blender-poc の switch_all.nut と同じ。決まりは docs/reference/way-addon.md の 9.2）
local AUTO = [["nse2", "ns", 1, 0, 0, -1], ["nse1", "ns", 1, 0, 0, 1], ["nsw2", "ns", -1, 0, 0, 1], ["nsw1", "ns", -1, 0, 0, -1],
              ["new2", "ew", 0, -1, 1, 0], ["new1", "ew", 0, -1, -1, 0], ["sew2", "ew", 0, 1, -1, 0], ["sew1", "ew", 0, 1, 1, 0]];

function lay(name, ox, oy) {
  local w = way_desc_x(name);
  if (w == null) return name + " desc=[missing]\n";
  local c = function(x, y, z = 0) { return coord3d(ox + x, oy + y, z); };
  local line = function(x0, y0, x1, y1) { return command_x.build_way(pl, c(x0, y0), c(x1, y1), w, true); };
  local s = r(name + " label", marker.work(pl, c(0, -2), name));
  // A・F
  s += r("A ew", line(0, 0, 2, 0));
  s += r("A ns", line(4, 0, 4, 2));
  s += r("F", line(6, 0, 6, 0));
  // C
  s += r("C se", stair(w, ox + 8, oy + 0, 3, 1));
  s += r("C ne", stair(w, ox + 13, oy + 3, 3, -1));
  // B
  s += r("B1", line(0, 4, 6, 4));
  s += r("B2", line(6, 4, 6, 10));
  s += r("B3", line(6, 10, 0, 10));
  s += r("B4", line(0, 10, 0, 4));
  s += r("B5", line(3, 4, 3, 10));
  s += r("B6", line(0, 7, 6, 7));
  // D・E
  foreach (h in [[11, 7, 1], [17, 7, 2]]) {
    local cx = h[0], cy = h[1], n = h[2];
    for (local k = 0; k < n; k++) s += r("hill raise", command_x.set_slope(pl, c(cx, cy, k), slope.all_up_slope));
    s += r("hill rampN", command_x.set_slope(pl, c(cx, cy - 1), 4 * n));
    s += r("hill rampS", command_x.set_slope(pl, c(cx, cy + 1), 36 * n));
    s += r("hill rampW", command_x.set_slope(pl, c(cx - 1, cy), 12 * n));
    s += r("hill rampE", command_x.set_slope(pl, c(cx + 1, cy), 28 * n));
    s += r("hill ns", line(cx, cy - 2, cx, cy + 2));
    s += r("hill ew", line(cx - 2, cy, cx + 2, cy));
  }
  // G: 斜め 2 本を、分け合うタイルが十字になる形で敷く（東西と南北の直線を 1 本ずつ通す。カーブのタイルから 3 本目を足すと崩れるため）
  local N = 5;
  foreach (g in [[22, 0, 1], [22, 18, -1]]) {
    local gx = g[0], gy = g[1], sy = g[2];
    for (local k = 0; k < N; k++) {
      s += r("G h" + k, line(gx + k, gy + sy * k, gx + k + 2, gy + sy * k));
      s += r("G v" + k, line(gx + k + 1, gy + sy * (k - 1), gx + k + 1, gy + sy * (k + 1)));
    }
    // 分け合うタイル（十字）が way 1 本（近い斜めの絵）になっているか
    local t = square_x(ox + gx + 2, oy + gy + sy).get_ground_tile();
    checks += "[check] " + name + " close " + (sy > 0 ? "se" : "ne") + " two_ways=" + t.has_two_ways() + "\n";
  }
  // I
  foreach (k, ix in [2, 8]) {
    s += r("I ns", line(ix, 12, ix, 16));
    s += r("I ew", line(ix - 2, 14, ix + 2, 14));
    if (pin != null) s += r("I pin" + (k + 1), pin.work(pl, c(ix, 14), "" + wt_rail + "," + (k + 1)));
  }
  s += r("I label", marker.work(pl, c(0, 17), pin != null ? "nsew1 / nsew2" : "nsew (no pin tool)"));
  // H
  foreach (j, cs in AUTO) {
    local jx = 3 + 8 * j, jy = 22;
    if (cs[1] == "ns") s += r("H main", line(jx, jy - 3, jx, jy + 3));
    else s += r("H main", line(jx - 3, jy, jx + 3, jy));
    local bx = jx + cs[2], by = jy + cs[3];
    s += r("H out", line(jx, jy, bx, by));
    s += r("H turn", line(bx, by, bx + 3 * cs[4], by + 3 * cs[5]));
    s += r("H label", marker.work(pl, c(jx - cs[2], jy - cs[3]), cs[0]));
  }
  return s;
}
foreach (n, o in ORIGINS) {
  foreach (i, name in WAYS) report += lay(name, o[0], o[1] + i * SPACING);
  if (n == SNOW) {
    local y1 = o[1] + (WAYS.len() - 1) * SPACING + AREA[1];
    report += r("climate", command_x(tool_set_climate).work(pl, coord3d(o[0] - 2, o[1] - 3, 0), coord3d(o[0] + AREA[0], y1, 0), "7"));
  }
}
checks += "[check] pin tool=" + (pin != null) + "\n";
gui.close_all_windows();
return (report == "" ? "ok\n" : "check\n" + report) + checks;
