// AMI の路面軌道の見本: ami_tram の絵を、周りのタイルとつながった形で全部出す（全方位・分岐・近い斜め・坂・雪）。
// 路面軌道は道路に重ねて敷く（ADR 0002）ので、同じ並びを「土の上」と「道路の上」（AMI の道路 3 種・pak128 標準の Road_050）に敷く。
// 線路の見本（sample.nut）とは別のゲームで敷く（sample.nut は Windows のコマンドラインの長さの上限に近いので、区画を足さない）。
// 検証用の flat_512.sve に、温暖側 (20,20) と降雪側 (276,20) の 2 か所へ同じ並びで敷く。降雪側は敷いた後に一帯を降雪に塗り直す。
// 下に敷く物は UNDER の順に SPACING タイルずつ南へずらす（null は土の上）。名札（ASCII）付き。見つからない way は失敗として報告する。
// 使い方（アドオンのディレクトリで）: sample_parallel.sh に NUT=ingame/tram_sample.nut を付ける（撮る場所は sample_spots.sh の TRAM_SPOTS）。
// 返り値の先頭が ok なら全部敷けた。失敗した所は「名前 場所=[…]」で続く。最後に確かめた値（[check] の行）が続く。
//
// 1 つの下敷きごとの区画（64x27）。原点 (ox,oy) から（区画の並びは sample.nut と同じ）:
//   A 行き止まり 4 方向・F 1 タイルだけ・C 斜め 2 本（階段）・B 輪と十字（カーブは曲線のセル）・D 坂の十字・E 急坂の十字・G 近い斜め
//   I 十字の分岐の絵を固定: (2,14) を選択 1・(8,14) を選択 2（固定の道具がある OTRP だけ）
//   H 分岐の自動選択 8 通り: y=22 の行に x=3 から 8 ずつ（線路と同じ条件。本体の weg_t::select_switch_image）
//   P 橋脚とのつながり（土の上の区画だけ）: (40,0)-(44,0) に線路用の橋脚 ami_pier_rail（tram_track）を敷き、(42,-1)-(42,2) に路面軌道を横切らせる。
//     同じ waytype なので、横切るタイルは 1 本の way（置き換え）になる。[check] の行に、そのタイルと隣の way の名前を出す
// [check] の行: 区画 G の分け合うタイルが way 1 本か（two_ways=false なら近い斜めの絵）、区画 H の自動選択の絵と、通常の T字の絵（get_image_id）、
//   区画 I の固定の絵（SWITCH_IMAGES が真なら、選択 1・2 と通常の十字が全部違えば ok。偽なら全部同じで ok）、道路の上の区画で道路が残っているか（road=）、区画 P。
//   区画 H は、通常の T字と同じ絵なら (plain) を付ける（分岐の絵があれば、どれにも付かない）
local TRAM = "ami_tram";
local SWITCH_IMAGES = true;  // dat に分岐の絵（switch 画像 1・2）があるか（ami_dat.py の TRAM_SWITCH_IMAGES と同じにする）
local UNDER = [null, "ami_road_local", "ami_road_general", "ami_road_expressway", "Road_050"];
local PIER = "ami_pier_rail";
local ORIGINS = [[20, 20], [276, 20]];
local SNOW = 1;
local SPACING = 30;
local AREA = [64, 27];
local pl = player_x(0);
local marker = command_x(tool_set_marker);
local report = "";
local checks = "";
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
function set_slope_kept(p, s) { return command_x.set_slope(pl, p, s); }
function tram_at(x, y) { return square_x(x, y).get_ground_tile().get_way(wt_rail); }  // tram_track は本体では track
function img(x, y) { local w = tram_at(x, y); return w == null ? -1 : w.get_image_id(); }
function wname(x, y) { local w = tram_at(x, y); return w == null ? "-" : w.get_desc().get_name(); }
local pin = null;
try { pin = command_x(tool_set_switch_image); } catch (e) { pin = null; }
// [選ばれる絵, 本線の向き, 枝の出る向き dx, dy, 枝が曲がる向き dx, dy]（sample.nut の AUTO と同じ）
local AUTO = [["nse2", "ns", 1, 0, 0, -1], ["nse1", "ns", 1, 0, 0, 1], ["nsw2", "ns", -1, 0, 0, 1], ["nsw1", "ns", -1, 0, 0, -1],
              ["new2", "ew", 0, -1, 1, 0], ["new1", "ew", 0, -1, -1, 0], ["sew2", "ew", 0, 1, -1, 0], ["sew1", "ew", 0, 1, 1, 0]];

function lay(under, ox, oy) {
  local w = way_desc_x(TRAM);
  if (w == null) return TRAM + " desc=[missing]\n";
  local u = null;
  if (under != null) {
    u = way_desc_x(under);
    if (u == null) return under + " desc=[missing]\n";
  }
  local c = function(x, y, z = 0) { return coord3d(ox + x, oy + y, z); };
  // 道路を先に敷き、同じ経路に路面軌道を重ねる
  local line = function(x0, y0, x1, y1) {
    local e = null;
    if (u != null) e = command_x.build_way(pl, c(x0, y0), c(x1, y1), u, true);
    local f = command_x.build_way(pl, c(x0, y0), c(x1, y1), w, true);
    return f != null ? f : e;
  };
  local stair = function(x, y, n, dy) {
    local e = null;
    for (local k = 0; k < n; k++) {
      local a = line(x + k, y + k * dy, x + k, y + (k + 1) * dy);
      local b = line(x + k, y + (k + 1) * dy, x + k + 1, y + (k + 1) * dy);
      if (a != null) e = a;
      if (b != null) e = b;
    }
    return e;
  };
  local tag = under == null ? "ground" : under;
  local s = r(tag + " label", marker.work(pl, c(0, -2), TRAM + " on " + tag));
  s += r("A ew", line(0, 0, 2, 0));
  s += r("A ns", line(4, 0, 4, 2));
  s += r("F", line(6, 0, 6, 0));
  s += r("C se", stair(8, 0, 3, 1));
  s += r("C ne", stair(13, 3, 3, -1));
  s += r("B1", line(0, 4, 6, 4));
  s += r("B2", line(6, 4, 6, 10));
  s += r("B3", line(6, 10, 0, 10));
  s += r("B4", line(0, 10, 0, 4));
  s += r("B5", line(3, 4, 3, 10));
  s += r("B6", line(0, 7, 6, 7));
  foreach (h in [[11, 7, 1], [17, 7, 2]]) {
    local cx = h[0], cy = h[1], n = h[2];
    for (local k = 0; k < n; k++) s += r("hill raise", set_slope_kept(c(cx, cy, k), slope.all_up_slope));
    s += r("hill rampN", set_slope_kept(c(cx, cy - 1), 4 * n));
    s += r("hill rampS", set_slope_kept(c(cx, cy + 1), 36 * n));
    s += r("hill rampW", set_slope_kept(c(cx - 1, cy), 12 * n));
    s += r("hill rampE", set_slope_kept(c(cx + 1, cy), 28 * n));
    s += r("hill ns", line(cx, cy - 2, cx, cy + 2));
    s += r("hill ew", line(cx - 2, cy, cx + 2, cy));
  }
  foreach (g in [[22, 0, 1], [22, 18, -1]]) {
    local gx = g[0], gy = g[1], sy = g[2];
    for (local k = 0; k < 5; k++) {
      s += r("G h" + k, line(gx + k, gy + sy * k, gx + k + 2, gy + sy * k));
      s += r("G v" + k, line(gx + k + 1, gy + sy * (k - 1), gx + k + 1, gy + sy * (k + 1)));
    }
    local t = square_x(ox + gx + 2, oy + gy + sy).get_ground_tile();
    checks += "[check] " + tag + " close " + (sy > 0 ? "se" : "ne") + " two_ways=" + t.has_two_ways() + "\n";
  }
  local pinned = [];
  foreach (k, ix in [2, 8]) {
    s += r("I ns", line(ix, 12, ix, 16));
    s += r("I ew", line(ix - 2, 14, ix + 2, 14));
    if (pin != null) s += r("I pin" + (k + 1), pin.work(pl, c(ix, 14), "" + wt_rail + "," + (k + 1)));
    pinned.append(img(ox + ix, oy + 14));
  }
  s += r("I label", marker.work(pl, c(0, 17), pin != null ? "nsew pin 1 / 2" : "nsew (no pin tool)"));
  local cross = img(ox + 3, oy + 7);
  checks += "[check] " + tag + " nsew pin1=" + pinned[0] + " pin2=" + pinned[1] + " plain=" + cross
            + (pin == null ? "" : ((SWITCH_IMAGES ? pinned[0] != cross && pinned[1] != cross && pinned[0] != pinned[1]
                                                  : pinned[0] == cross && pinned[1] == cross) ? " ok" : " NG")) + "\n";
  // 通常の T字（区画 B の (0,7) nse・(6,7) nsw・(3,10) new・(3,4) sew）
  local plain = {nse = img(ox, oy + 7), nsw = img(ox + 6, oy + 7), new = img(ox + 3, oy + 10), sew = img(ox + 3, oy + 4)};
  local autos = "";
  foreach (j, cs in AUTO) {
    local jx = 3 + 8 * j, jy = 22;
    if (cs[1] == "ns") s += r("H main", line(jx, jy - 3, jx, jy + 3));
    else s += r("H main", line(jx - 3, jy, jx + 3, jy));
    local bx = jx + cs[2], by = jy + cs[3];
    s += r("H out", line(jx, jy, bx, by));
    s += r("H turn", line(bx, by, bx + 3 * cs[4], by + 3 * cs[5]));
    s += r("H label", marker.work(pl, c(jx - cs[2], jy - cs[3]), cs[0]));
    local v = img(ox + jx, oy + jy);
    autos += " " + cs[0] + "=" + v + (v == plain[cs[0].slice(0, cs[0].len() - 1)] ? "(plain)" : "");
  }
  checks += "[check] " + tag + " auto" + autos + "\n";
  if (u != null) {
    // 道路の上の区画: 路面軌道を重ねたタイルに道路が残っているか（直線・十字・斜め・坂）
    local roads = "";
    foreach (p in [[1, 0], [3, 7], [9, 1], [11, 6]]) {
      local rw = square_x(ox + p[0], oy + p[1]).get_ground_tile().get_way(wt_road);
      roads += " " + (rw == null ? "-" : "ok");
    }
    checks += "[check] " + tag + " road=" + roads + "\n";
  }
  if (under == null) {
    // P: 橋脚とのつながり
    local pd = way_desc_x(PIER);
    if (pd == null) s += PIER + " desc=[missing]\n";
    else {
      s += r("P pier", command_x.build_way(pl, c(40, 0), c(44, 0), pd, true));
      s += r("P tram", command_x.build_way(pl, c(42, -1), c(42, 2), w, true));
      s += r("P label", marker.work(pl, c(40, -3), "tram x pier"));
      checks += "[check] P cross=" + wname(ox + 42, oy) + " west=" + wname(ox + 41, oy) + " north=" + wname(ox + 42, oy - 1) + "\n";
    }
  }
  return s;
}

foreach (n, o in ORIGINS) {
  foreach (i, under in UNDER) report += lay(under, o[0], o[1] + i * SPACING);
  if (n == SNOW)
    report += r("climate", command_x(tool_set_climate).work(pl, coord3d(o[0] - 2, o[1] - 4, 0),
                                                             coord3d(o[0] + AREA[0], o[1] + (UNDER.len() - 1) * SPACING + AREA[1], 0), "7"));
}
checks += "[check] pin tool=" + (pin != null) + "\n";
gui.close_all_windows();
return (report == "" ? "ok\n" : "check\n" + report) + checks;
