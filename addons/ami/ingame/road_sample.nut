// AMI の道路の見本: 道路 3 種（ROADS）の通常の版の絵を、周りのタイルとつながった形で全部出す（全方位・分岐・近い斜め・坂・雪）。
// 線路の見本（sample.nut）とは別のゲームで敷く（sample.nut は Windows のコマンドラインの長さの上限に近いので、道路の区画を足さない）。
// 検証用の flat_512.sve に、温暖側 (20,20) と降雪側 (276,20) の 2 か所へ同じ並びで敷く。降雪側は敷いた後に一帯を降雪に塗り直す
// （土地を上げたタイルは温暖に変わり、坂の道が雪の絵にならないため。docs/reference/way-addon.md の 8.2）。
// 道路は ROADS の順に、SPACING タイルずつ南へずらして 1 種ずつ敷く。名札（ASCII）付き。見つからない way は失敗として報告する。
// 使い方（アドオンのディレクトリで）: sample_check.sh・sample_parallel.sh に NUT=ingame/road_sample.nut を付ける（撮る場所は sample_spots.sh の ROAD_SPOTS）。
// 返り値の先頭が ok なら全部敷けた。失敗した所は「名前 場所=[…]」で続く。最後に確かめた値（[check] の行）が続く。
//
// 1 種ずつの区画（64x27）。原点 (ox,oy) から:
//   A 行き止まり 4 方向: 東西 (0,0)-(2,0)・南北 (4,0)-(4,2)                       … image[w] [e] [n] [s]
//   F 1 タイルだけ: (6,0)                                                         … image[-]
//   C 斜め 2 本（階段）: (8,0) から南東へ・(13,3) から北東へ 3 段                   … diagonal 4
//   B 輪と十字: (0,4)-(6,10) の輪に (3,4)-(3,10) と (0,7)-(6,7)                   … image[ns] [ew]、カーブ 4（斜めの絵）、T字 4、十字
//   D 坂の十字: (11,7) を 1 段上げ、四方を坂にして越える                          … imageup 4
//   E 急坂の十字: (17,7) を 2 段上げ、四方を 2 段の坂にして越える                  … imageup2 4
//   G 近い斜め: (22,0) から南東へ・(22,18) から北東へ、1 タイルずらした斜め 2 本    … diagonal[close1] [close2]
//   H 分岐の自動選択（道路の条件。本体の weg_t::select_switch_road_image）: T字の枝の側の隣が T字か十字で、本線の両隣が分岐でないと「1」の絵。
//     2 本の道路を隣り合わせに並べ、渡り口でつなぐ: 南北 (34,0)-(34,8)・(35,0)-(35,8) を (34,4)-(35,4) でつなぐ（nse1・nsw1）、
//     東西 (33,12)-(43,12)・(33,13)-(43,13) を (38,12)-(38,13) でつなぐ（sew1・new1）
//   I 分岐の絵を固定（固定の道具がある OTRP だけ）: y=23 の行に x=2 から 6 ずつ、T字 4 種と十字を、選択 2（image[..1]）・選択 1（image[..2]）の順に
//     （本体の apply_switch_image_override: 選択 1 は nw=true の絵 = dat の「2」、選択 2 は nw=false の絵 = dat の「1」）
//   K pak128 標準の道路（STANDARD）とのつなぎ目: 東西 y=1 の (44)-(49) が標準・(49)-(55) が AMI、南北 x=58 の (0)-(4) が標準・(4)-(9) が AMI
//   L 隣り合う十字: 南北 (50,11)-(50,19)・(51,11)-(51,19) を東西 (46,15)-(55,15) が横切る。十字の隣が T字か十字だと、ex 画像の無い way では
//     十字のタイルに T字の「2」の絵（西の十字は image[nse2]、東の十字は image[nsw2]）が出る（select_switch_road_image の ribi_t::all）
// [check] の行: 区画 G の分け合うタイルが way 1 本か（two_ways=false なら近い斜めの絵）、区画 H の自動選択の絵が区画 I の選択 2 と同じ絵で
// 通常の T字（区画 B）と違うか、区画 I の選択 1 と 2 が違う絵か（get_image_id）、区画 L の十字が T字の「2」の絵になるか（t2）、固定の道具があるか
local ROADS = ["ami_road_local", "ami_road_general", "ami_road_expressway"];
local STANDARD = "Road_050";   // 区画 K でつなぐ pak128 標準の道路
local ORIGINS = [[20, 20], [276, 20]];
local SNOW = 1;          // ORIGINS の何番目を降雪に塗り直すか
local SPACING = 30;
local AREA = [64, 27];   // 1 種の区画の大きさ（降雪の塗り直しに使う）
local pl = player_x(0);
local marker = command_x(tool_set_marker);
local report = "";
local checks = "";
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
function set_slope_kept(p, s) { return command_x.set_slope(pl, p, s); }
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
function road_at(x, y) { return square_x(x, y).get_ground_tile().get_way(wt_road); }
function img(x, y) { local w = road_at(x, y); return w == null ? -1 : w.get_image_id(); }
// 分岐の絵を固定する道具（OTRP の改修版だけにある）。無ければ null
local pin = null;
try { pin = command_x(tool_set_switch_image); } catch (e) { pin = null; }
// 区画 I の並び: [dat の絵の名前, 本線の向き, 枝の向き dx, dy（十字は 0, 0）]
local PINS = [["nse", "ns", 1, 0], ["new", "ew", 0, -1], ["nsw", "ns", -1, 0], ["sew", "ew", 0, 1], ["nsew", "ns", 0, 0]];

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
    for (local k = 0; k < n; k++) s += r("hill raise", set_slope_kept(c(cx, cy, k), slope.all_up_slope));
    s += r("hill rampN", set_slope_kept(c(cx, cy - 1), 4 * n));
    s += r("hill rampS", set_slope_kept(c(cx, cy + 1), 36 * n));
    s += r("hill rampW", set_slope_kept(c(cx - 1, cy), 12 * n));
    s += r("hill rampE", set_slope_kept(c(cx + 1, cy), 28 * n));
    s += r("hill ns", line(cx, cy - 2, cx, cy + 2));
    s += r("hill ew", line(cx - 2, cy, cx + 2, cy));
  }
  // G: 斜め 2 本を、分け合うタイルが十字になる形で敷く（東西と南北の直線を 1 本ずつ通す。カーブのタイルから 3 本目を足すと崩れるため）
  foreach (g in [[22, 0, 1], [22, 18, -1]]) {
    local gx = g[0], gy = g[1], sy = g[2];
    for (local k = 0; k < 5; k++) {
      s += r("G h" + k, line(gx + k, gy + sy * k, gx + k + 2, gy + sy * k));
      s += r("G v" + k, line(gx + k + 1, gy + sy * (k - 1), gx + k + 1, gy + sy * (k + 1)));
    }
    local t = square_x(ox + gx + 2, oy + gy + sy).get_ground_tile();
    checks += "[check] " + name + " close " + (sy > 0 ? "se" : "ne") + " two_ways=" + t.has_two_ways() + "\n";
  }
  // H: 2 本を隣り合わせに並べ、渡り口でつなぐ
  s += r("H ns", line(34, 0, 34, 8));
  s += r("H ns", line(35, 0, 35, 8));
  s += r("H ns rung", line(34, 4, 35, 4));
  s += r("H ew", line(33, 12, 43, 12));
  s += r("H ew", line(33, 13, 43, 13));
  s += r("H ew rung", line(38, 12, 38, 13));
  s += r("H label", marker.work(pl, c(36, -1), "auto: nse1 nsw1"));
  s += r("H label", marker.work(pl, c(33, 15), "auto: sew1 new1"));
  // I: 固定。選択 2（dat の「1」）・選択 1（dat の「2」）の順
  local pinned = {};
  foreach (j, p in PINS) {
    foreach (k, choice in [2, 1]) {
      local ix = 2 + 6 * (2 * j + k), iy = 23;
      if (p[1] == "ns") s += r("I main", line(ix, iy - 2, ix, iy + 2));
      else s += r("I main", line(ix - 2, iy, ix + 2, iy));
      if (p[0] == "nsew") s += r("I cross", line(ix - 2, iy, ix + 2, iy));
      else s += r("I branch", line(ix, iy, ix + 2 * p[2], iy + 2 * p[3]));
      if (pin != null) s += r("I pin" + choice, pin.work(pl, c(ix, iy), "" + wt_road + "," + choice));
      s += r("I label", marker.work(pl, c(ix, iy + 3), p[0] + (choice == 2 ? "1" : "2")));
      pinned[p[0] + (choice == 2 ? "1" : "2")] <- img(ox + ix, oy + iy);
    }
  }
  // K: pak128 標準の道路とのつなぎ目
  local std = way_desc_x(STANDARD);
  if (std == null) s += STANDARD + " desc=[missing]\n";
  else {
    s += r("K ew std", command_x.build_way(pl, c(44, 1), c(49, 1), std, true));
    s += r("K ew ami", line(49, 1, 55, 1));
    s += r("K ns std", command_x.build_way(pl, c(58, 0), c(58, 4), std, true));
    s += r("K ns ami", line(58, 4, 58, 9));
    s += r("K label", marker.work(pl, c(44, -1), STANDARD + " | AMI"));
  }
  // L: 隣り合う十字
  s += r("L ns", line(50, 11, 50, 19));
  s += r("L ns", line(51, 11, 51, 19));
  s += r("L ew", line(46, 15, 55, 15));
  s += r("L label", marker.work(pl, c(46, 10), "auto: nsew next to nsew"));
  // [check]: 自動選択（H）と固定（I）の絵。通常の T字は区画 B の (0,7) nse・(6,7) nsw・(3,10) new・(3,4) sew
  local plain = {nse = img(ox, oy + 7), nsw = img(ox + 6, oy + 7), new = img(ox + 3, oy + 10), sew = img(ox + 3, oy + 4)};
  local auto = {nse = img(ox + 34, oy + 4), nsw = img(ox + 35, oy + 4), sew = img(ox + 38, oy + 12), new = img(ox + 38, oy + 13)};
  foreach (k, v in auto) {
    // 1 と 2 が同じ絵なら same12（前は生活道路で出た。轍のカーブで分けたので出ない）
    local ok = v == pinned[k + "1"] && v != plain[k];
    checks += "[check] " + name + " " + k + " auto=" + v + " pin1=" + pinned[k + "1"] + " pin2=" + pinned[k + "2"] + " plain=" + plain[k]
              + (pin == null ? "" : (ok ? " ok" : " NG")) + (pinned[k + "1"] == pinned[k + "2"] ? " same12" : "") + "\n";
  }
  checks += "[check] " + name + " nsew pin1=" + pinned["nsew1"] + " pin2=" + pinned["nsew2"] + " plain=" + img(ox + 3, oy + 7) + "\n";
  local lw = img(ox + 50, oy + 15), le = img(ox + 51, oy + 15);
  checks += "[check] " + name + " L west=" + lw + " east=" + le + " plain=" + img(ox + 3, oy + 7)
            + ((lw == pinned["nse2"] && le == pinned["nsw2"]) ? " t2" : "") + "\n";
  return s;
}

foreach (n, o in ORIGINS) {
  foreach (i, name in ROADS) report += lay(name, o[0], o[1] + i * SPACING);
  if (n == SNOW)
    report += r("climate", command_x(tool_set_climate).work(pl, coord3d(o[0] - 2, o[1] - 3, 0),
                                                             coord3d(o[0] + AREA[0], o[1] + (ROADS.len() - 1) * SPACING + AREA[1], 0), "7"));
}
checks += "[check] pin tool=" + (pin != null) + "\n";
gui.close_all_windows();
return (report == "" ? "ok\n" : "check\n" + report) + checks;
