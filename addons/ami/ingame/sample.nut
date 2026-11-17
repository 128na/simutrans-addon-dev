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
// 基盤の版（WALLED）も同じ並びで、同じ版の壁の way-object を同じ経路に重ねる（center は壁なし）。G は敷かない（近い斜めは区画 W）。
//
// 区画 W（複線と壁の組。WAYS と WALLED の区画の後。原点は (ox, oy + (WAYS と WALLED の数) * SPACING)）:
//   W1 複線の輪: 外 (0,0)-(12,9)・内 (1,1)-(11,8)。辺ごとに奥の線は back、手前の線は front。カーブ（斜めの絵）のタイルは南北の辺と同じ版
//   W2 近い斜めの複線: (16,0) から南東へ・(16,16) から北東へ 5 段。奥の線が back、1 タイル東の手前の線が front。
//      分け合うタイル（way 2 本）には、back・front を敷いた後に ami_wall_rail_close を 1 タイルずつ敷いて置き換える
//   W3 行き止まりを並べる: y=12・13・14 に (0)-(3) の東西を back・center・front（両端が行き止まり）
local WAYS = ["ami_rail_ballast"];
// [基盤の版の way, 壁の way-object（null は壁なし）]
local WALLED = [["ami_rail_ballast_base_single", "ami_wall_rail_single"], ["ami_rail_ballast_base_back", "ami_wall_rail_back"],
                ["ami_rail_ballast_base_center", null], ["ami_rail_ballast_base_front", "ami_wall_rail_front"]];
local W_AREA = [24, 18];  // 区画 W の大きさ（降雪の塗り直しに使う）
local ORIGINS = [[20, 20], [276, 20]];
local SNOW = 1;          // ORIGINS の何番目を降雪に塗り直すか
local SPACING = 30;
local AREA = [64, 27];   // 区画の大きさ（降雪の塗り直しに使う）
local pl = player_x(0);
local marker = command_x(tool_set_marker);
local report = "";
local checks = "";
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
// way を a から b へ敷き、壁の way-object（wo。null なら無し）を同じ経路に重ねる
function way2(w, wo, a, b) {
  local e = command_x.build_way(pl, a, b, w, true);
  if (e == null && wo != null) e = command_x.build_wayobj(pl, a, b, wo);
  return e;
}
function stair(w, x, y, n, dy, wo = null) {
  local e = null;
  for (local k = 0; k < n; k++) {
    local a = way2(w, wo, coord3d(x + k, y + k * dy, 0), coord3d(x + k, y + (k + 1) * dy, 0));
    local b = way2(w, wo, coord3d(x + k, y + (k + 1) * dy, 0), coord3d(x + k + 1, y + (k + 1) * dy, 0));
    if (a != null) e = a;
    if (b != null) e = b;
  }
  return e;
}
// stair と同じ経路に壁の way-object だけを敷く
function stair_wo(wo, x, y, n, dy) {
  local e = null;
  for (local k = 0; k < n; k++) {
    local a = command_x.build_wayobj(pl, coord3d(x + k, y + k * dy, 0), coord3d(x + k, y + (k + 1) * dy, 0), wo);
    local b = command_x.build_wayobj(pl, coord3d(x + k, y + (k + 1) * dy, 0), coord3d(x + k + 1, y + (k + 1) * dy, 0), wo);
    if (a != null) e = a;
    if (b != null) e = b;
  }
  return e;
}
// タイルの way と壁の名前（[check] の行に出す）。(2) は way が 2 本（近い斜めの分け合うタイル）
function names(x, y) {
  local t = square_x(x, y).get_ground_tile();
  local w = t.get_way(wt_rail);
  local o = t.find_object(mo_wayobj);
  return (w == null ? "-" : w.get_desc().get_name()) + "+" + (o == null ? "-" : o.get_desc().get_name()) + (t.has_two_ways() ? "(2)" : "");
}
// 分岐の絵を固定する道具（OTRP の改修版だけにある）。無ければ null
local pin = null;
try { pin = command_x(tool_set_switch_image); } catch (e) { pin = null; }
// [選ばれる絵, 本線の向き, 枝の出る向き dx, dy, 枝が曲がる向き dx, dy]（blender-poc の switch_all.nut と同じ。決まりは docs/reference/way-addon.md の 9.2）
local AUTO = [["nse2", "ns", 1, 0, 0, -1], ["nse1", "ns", 1, 0, 0, 1], ["nsw2", "ns", -1, 0, 0, 1], ["nsw1", "ns", -1, 0, 0, -1],
              ["new2", "ew", 0, -1, 1, 0], ["new1", "ew", 0, -1, -1, 0], ["sew2", "ew", 0, 1, -1, 0], ["sew1", "ew", 0, 1, 1, 0]];

function lay(name, wall, ox, oy) {
  local w = way_desc_x(name);
  if (w == null) return name + " desc=[missing]\n";
  local wo = null;
  if (wall != null) {
    wo = wayobj_desc_x(wall);
    if (wo == null) return wall + " desc=[missing]\n";
  }
  local is_base = name.find("_base_") != null;
  local c = function(x, y, z = 0) { return coord3d(ox + x, oy + y, z); };
  local line = function(x0, y0, x1, y1) { return way2(w, wo, c(x0, y0), c(x1, y1)); };
  local s = r(name + " label", marker.work(pl, c(0, -2), name));
  // A・F
  s += r("A ew", line(0, 0, 2, 0));
  s += r("A ns", line(4, 0, 4, 2));
  s += r("F", line(6, 0, 6, 0));
  // C
  s += r("C se", stair(w, ox + 8, oy + 0, 3, 1, wo));
  s += r("C ne", stair(w, ox + 13, oy + 3, 3, -1, wo));
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
  foreach (g in (is_base ? [] : [[22, 0, 1], [22, 18, -1]])) {
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
// 区画 W: 複線と壁の組（冒頭の表）
function lay_pairs(ox, oy) {
  local wd = {}, od = {};
  foreach (v in ["single", "back", "center", "front"]) wd[v] <- way_desc_x("ami_rail_ballast_base_" + v);
  foreach (v in ["single", "back", "front", "close"]) od[v] <- wayobj_desc_x("ami_wall_rail_" + v);
  local c = function(x, y) { return coord3d(ox + x, oy + y, 0); };
  local way = function(v, x0, y0, x1, y1) { return command_x.build_way(pl, c(x0, y0), c(x1, y1), wd[v], true); };
  local obj = function(v, x0, y0, x1, y1) { return command_x.build_wayobj(pl, c(x0, y0), c(x1, y1), od[v]); };
  local s = r("W label", marker.work(pl, c(0, -2), "walls: double track"));
  // W1: way は東西の辺を先に、南北の辺を後に敷く（角のタイルは後から敷いた南北の辺の版になる。スクリプトの build_way は置き換える）。
  // 壁は南北の辺を先に敷く（同じ速さの壁を後から敷くと、前の版のまま向きだけ足される。obj/wayobj.cc の extend_wayobj）
  local EW = [["back", 0, 0, 12, 0], ["front", 0, 9, 12, 9], ["front", 1, 1, 11, 1], ["back", 1, 8, 11, 8]];
  local NS = [["back", 0, 0, 0, 9], ["front", 12, 0, 12, 9], ["front", 1, 1, 1, 8], ["back", 11, 1, 11, 8]];
  foreach (e in EW) s += r("W1 way", way(e[0], e[1], e[2], e[3], e[4]));
  foreach (e in NS) s += r("W1 way", way(e[0], e[1], e[2], e[3], e[4]));
  foreach (e in NS) s += r("W1 wall", obj(e[0], e[1], e[2], e[3], e[4]));
  foreach (e in EW) s += r("W1 wall", obj(e[0], e[1], e[2], e[3], e[4]));
  foreach (p in [[0, 0], [1, 0], [0, 1], [12, 0], [11, 1], [12, 9], [11, 8], [0, 9], [1, 8]])
    checks += "[check] W1 (" + p[0] + "," + p[1] + ") " + names(ox + p[0], oy + p[1]) + "\n";
  // W2
  foreach (g in [[16, 0, 1], [16, 16, -1]]) {
    s += r("W2 back", stair(wd["back"], ox + g[0], oy + g[1], 5, g[2]));
    s += r("W2 front", stair(wd["front"], ox + g[0] + 1, oy + g[1], 5, g[2]));
    s += r("W2 back wall", stair_wo(od["back"], ox + g[0], oy + g[1], 5, g[2]));
    s += r("W2 front wall", stair_wo(od["front"], ox + g[0] + 1, oy + g[1], 5, g[2]));
    for (local x = g[0]; x <= g[0] + 7; x++) {
      for (local y = -1; y <= 6; y++) {
        local yy = g[1] + g[2] * y;
        if (!square_x(ox + x, oy + yy).get_ground_tile().has_two_ways()) continue;
        s += r("W2 close", obj("close", x, yy, x, yy));
        checks += "[check] W2 (" + x + "," + yy + ") " + names(ox + x, oy + yy) + "\n";
      }
    }
    // close で置き換えると、前の way-object が消えるときに隣のタイルの壁の向きから自分の側を外す（obj/wayobj.cc の ~wayobj_t）。
    // 新しい close は向きを引き継ぐので隣へつなぎ直さない。back・front を同じ経路にもう一度敷いて、隣の向きを戻す
    // （close の方が速いので、分け合うタイルは close のまま向きだけ足される）
    s += r("W2 back wall again", stair_wo(od["back"], ox + g[0], oy + g[1], 5, g[2]));
    s += r("W2 front wall again", stair_wo(od["front"], ox + g[0] + 1, oy + g[1], 5, g[2]));
  }
  // W3
  foreach (k, v in ["back", "center", "front"]) {
    s += r("W3 way", way(v, 0, 12 + k, 3, 12 + k));
    if (v != "center") s += r("W3 wall", obj(v, 0, 12 + k, 3, 12 + k));
  }
  return s;
}

foreach (n, o in ORIGINS) {
  foreach (i, name in WAYS) report += lay(name, null, o[0], o[1] + i * SPACING);
  foreach (i, pr in WALLED) report += lay(pr[0], pr[1], o[0], o[1] + (WAYS.len() + i) * SPACING);
  local wy = o[1] + (WAYS.len() + WALLED.len()) * SPACING;
  report += lay_pairs(o[0], wy);
  if (n == SNOW) {
    local y1 = wy + W_AREA[1];
    report += r("climate", command_x(tool_set_climate).work(pl, coord3d(o[0] - 2, o[1] - 3, 0), coord3d(o[0] + AREA[0], y1, 0), "7"));
  }
}
checks += "[check] pin tool=" + (pin != null) + "\n";
gui.close_all_windows();
return (report == "" ? "ok\n" : "check\n" + report) + checks;
