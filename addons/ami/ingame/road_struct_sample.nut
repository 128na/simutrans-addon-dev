// AMI の道路の構造物の見本（#22）: 道路の壁（ami_wall_road_*）・高架の 4 版（<道路>_elev_<版>）・道路用の橋脚（ami_pier_road）・橋・トンネルを、
// 道路 3 種（ROADS）それぞれに敷く。道路の通常の版の見本（road_sample.nut）とは別のゲームで敷く（sample.nut はコマンドラインの長さの上限に近いため）。
// 検証用の flat_512.sve に、温暖側 (20,20) と降雪側 (276,20) の 2 か所へ同じ並びで敷き、降雪側は一帯を降雪に塗り直す（地形を変えたタイルはその場で塗り直す）。
// 使い方（アドオンのディレクトリで）: sample_check.sh・sample_parallel.sh に NUT=ingame/road_struct_sample.nut を付ける（撮る場所は sample_spots.sh の STRUCT_SPOTS）。
// 返り値の先頭が ok なら全部敷けた。失敗した所は「名前 場所=[…]」で続く。最後に確かめた値（[check] の行）が続く。
//
// 1 種ずつの区画（196x28。道路は ROADS の順に SPACING ずつ南へ）。原点 (ox,oy) から東へ:
//   地上の壁（x=0〜）: 通常の版の道路に ami_wall_road_single を同じ経路に重ねる。A 行き止まり・F 1 タイル・C 斜め・B 輪と十字・D 坂・E 急坂（road_sample.nut と同じ並び）
//     G 近い斜め (22,0) から南東へ・(22,18) から北東へ: 道路を road_sample.nut の区画 G と同じに敷き、奥の線に back、1 タイル東の手前の線に front の壁を重ねる
//   地上の複線（x=32〜。地上の基盤の版 <道路>_base_<版> と同じ版の壁）: W1 輪（外 (0,0)-(12,9)・内 (1,1)-(11,8)。奥の線は back、手前の線は front。
//     sample.nut の区画 W1 と同じ敷き方）、W3 行き止まりを並べる（y=12・13・14 に (0)-(3) の東西を back・center・front。center は壁なし）、
//     W2 近い斜め (6,12) から南東へ 5 段（分け合うタイルに ami_wall_road_twin。高架の WV2 と同じ敷き方）
//   高架（x=50〜）: <道路>_elev_single に壁 single を 2 段上（z=2）に重ね、真下の地面に ami_pier_road を敷く。A・F・C・B・D・E と、
//     L 隣り合う十字（南北 (22,0)-(22,8)・(23,0)-(23,8) を東西 (18,4)-(27,4) が横切る。T字の「2」の絵が高架でも出るか）
//   高架の複線（x=90〜）: WV1 輪（elev の back・front と同じ版の壁）、WV2 近い斜め (16,0) から南東へ 5 段（分け合うタイルに ami_wall_road_twin）、
//     WV3 行き止まりを並べる（y=12・13・14 に back・center・front。壁は center だけ無し）
//   橋とトンネル（x=125〜）: B1 平地から立ち上がる橋（東西 y=1 の (4)-(10)、南北 x=19 の (4)-(10)。前後の道路を先に敷いて端を押して架け、壁 single を橋の上も通して重ねる）、
//     B2 2 段の坂から始まる橋（東西 y=19 の (1)-(7)）、B4 高架と橋のつなぎ目（y=24。高架 (0)-(4)・(12)-(15) の間を橋 (5)-(11)）、
//     T1 トンネル（東西 y=19 の x=24〜32、南北 x=37 の y=0〜10）、T3 複線のトンネル（東西 y=24・25 に back・front の壁）
//   橋脚のつながり（x=168〜）: P1 南北の高架 (2,0)-(2,10) の真下に pak128 の道路（STANDARD）を並行して敷き、(-2,5)-(6,5) の東西の STANDARD で横切る、
//     P2 東西の高架 (8,2)-(18,2) の真下に同じ AMI の道路を並行して敷き、(13,-2)-(13,6) の南北の AMI の道路で横切る、
//     P3 南北の高架 (22,0)-(22,10) の真下を、東西 (19,5)-(25,5) の線路（RAIL）が横切る
local ROADS = ["ami_road_local", "ami_road_general", "ami_road_expressway"];
local STANDARD = "Road_050";
local RAIL = "ami_rail_ballast";
local PIER = "ami_pier_road";
local ELEV_UP = 2;
local ORIGINS = [[20, 20], [276, 20]];
local SNOW = 1;
local SPACING = 30;
local AREA = [196, 28];
local pl = player_x(0);
local marker = command_x(tool_set_marker);
local report = "";
local checks = "";
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
local mode = {z = 0, pier = null, snow = false};
function up(p) { return coord3d(p.x, p.y, p.z + mode.z); }
function set_slope_kept(p, s) {
  local e = command_x.set_slope(pl, p, s);
  if (e == null && mode.snow) e = command_x(tool_set_climate).work(pl, coord3d(p.x - 1, p.y - 1, 0), coord3d(p.x + 1, p.y + 1, 0), "7");
  return e;
}
function way2(w, wo, a, b) {
  local e = command_x.build_way(pl, a, b, w, true);
  if (e == null && wo != null) e = command_x.build_wayobj(pl, up(a), up(b), wo);
  if (e == null && mode.pier != null) e = command_x.build_way(pl, a, b, mode.pier, true);
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
function stair_wo(wo, x, y, n, dy) {
  local e = null;
  for (local k = 0; k < n; k++) {
    local a = command_x.build_wayobj(pl, coord3d(x + k, y + k * dy, mode.z), coord3d(x + k, y + (k + 1) * dy, mode.z), wo);
    local b = command_x.build_wayobj(pl, coord3d(x + k, y + (k + 1) * dy, mode.z), coord3d(x + k + 1, y + (k + 1) * dy, mode.z), wo);
    if (a != null) e = a;
    if (b != null) e = b;
  }
  return e;
}
function tile(x, y, z = 0) { return z == 0 ? square_x(x, y).get_ground_tile() : square_x(x, y).get_tile_at_height(z); }
// タイルの道路と壁の名前（d の後ろは道路の向き）。(2) は way が 2 本。高架なら真下の地面の橋脚（tram_track は wt_rail で読む）と道路を / の後ろに出す
function names(x, y, z = 0) {
  local t = tile(x, y, z);
  if (t == null) return "(no tile at z=" + z + ")";
  local w = t.get_way(wt_road), o = t.find_object(mo_wayobj);
  local s = (w == null ? "-" : w.get_desc().get_name() + " d" + w.get_dirs()) + "+" + (o == null ? "-" : o.get_desc().get_name())
            + (t.has_two_ways() ? "(2)" : "") + (t.is_bridge() ? " bridge" : "") + (t.is_tunnel() ? " tunnel" : "");
  if (z != 0) {
    local g = square_x(x, y).get_ground_tile();
    local p = g.get_way(wt_rail), q = g.get_way(wt_road);
    s += " / " + (p == null ? "-" : p.get_desc().get_name() + " d" + p.get_dirs()) + "," + (q == null ? "-" : q.get_desc().get_name() + " d" + q.get_dirs())
         + (g.has_two_ways() ? "(2)" : "");
  }
  return s;
}
function img(x, y, z) { local t = tile(x, y, z); local w = t == null ? null : t.get_way(wt_road); return w == null ? -1 : w.get_image_id(); }

// 1 本ずつの区画（A・F・C・B・D・E）。高架なら L も敷く
function lay_one(w, wo, ox, oy, tag) {
  local c = function(x, y, z = 0) { return coord3d(ox + x, oy + y, z); };
  local line = function(x0, y0, x1, y1) { return way2(w, wo, c(x0, y0), c(x1, y1)); };
  local s = r(tag + " label", marker.work(pl, c(0, -2), tag));
  s += r(tag + " A ew", line(0, 0, 2, 0));
  s += r(tag + " A ns", line(4, 0, 4, 2));
  s += r(tag + " F", line(6, 0, 6, 0));
  s += r(tag + " C se", stair(w, ox + 8, oy + 0, 3, 1, wo));
  s += r(tag + " C ne", stair(w, ox + 13, oy + 3, 3, -1, wo));
  s += r(tag + " B1", line(0, 4, 6, 4));
  s += r(tag + " B2", line(6, 4, 6, 10));
  s += r(tag + " B3", line(6, 10, 0, 10));
  s += r(tag + " B4", line(0, 10, 0, 4));
  s += r(tag + " B5", line(3, 4, 3, 10));
  s += r(tag + " B6", line(0, 7, 6, 7));
  foreach (h in [[11, 7, 1], [17, 7, 2]]) {
    local cx = h[0], cy = h[1], n = h[2];
    for (local k = 0; k < n; k++) s += r("hill raise", set_slope_kept(c(cx, cy, k), slope.all_up_slope));
    s += r("hill rampN", set_slope_kept(c(cx, cy - 1), 4 * n));
    s += r("hill rampS", set_slope_kept(c(cx, cy + 1), 36 * n));
    s += r("hill rampW", set_slope_kept(c(cx - 1, cy), 12 * n));
    s += r("hill rampE", set_slope_kept(c(cx + 1, cy), 28 * n));
    s += r(tag + " hill ns", line(cx, cy - 2, cx, cy + 2));
    s += r(tag + " hill ew", line(cx - 2, cy, cx + 2, cy));
  }
  return s;
}

function lay(name, ox, oy) {
  local w = way_desc_x(name), std = way_desc_x(STANDARD), rail = way_desc_x(RAIL), pier = way_desc_x(PIER);
  local od = {}, ev = {}, bd = {};
  foreach (v in ["single", "back", "front", "twin"]) {
    od[v] <- wayobj_desc_x("ami_wall_road_" + v);
    if (od[v] == null) return "ami_wall_road_" + v + " desc=[missing]\n";
  }
  foreach (v in ["single", "back", "center", "front"]) {
    ev[v] <- way_desc_x(name + "_elev_" + v);
    if (ev[v] == null) return name + "_elev_" + v + " desc=[missing]\n";
    bd[v] <- way_desc_x(name + "_base_" + v);
    if (bd[v] == null) return name + "_base_" + v + " desc=[missing]\n";
  }
  local br = bridge_desc_x(name + "_bridge");
  if (w == null || br == null || pier == null) return name + " desc=[missing]\n";
  local c = function(x, y, z = 0) { return coord3d(ox + x, oy + y, z); };
  local s = r(name + " label", marker.work(pl, c(0, -3), name));
  // 地上の壁
  s += lay_one(w, od["single"], ox, oy, "wall");
  foreach (g in [[22, 0, 1], [22, 18, -1]]) {
    local gx = g[0], gy = g[1], sy = g[2];
    for (local k = 0; k < 5; k++) {
      s += r("G h" + k, way2(w, null, c(gx + k, gy + sy * k), c(gx + k + 2, gy + sy * k)));
      s += r("G v" + k, way2(w, null, c(gx + k + 1, gy + sy * (k - 1)), c(gx + k + 1, gy + sy * (k + 1))));
    }
    // 東西に進んでから南北に折れる線（画面で左か上。sample.nut の区画 W2 の back と同じ側）に back、南北に進んでから東西に折れる線に front。
    // 分け合うタイル（十字）は way-object が 1 つだけなので、後から敷いた front に back の向きが足される
    for (local k = 0; k < 5; k++) {
      s += r("G back", command_x.build_wayobj(pl, c(gx + k, gy + sy * k), c(gx + k + 1, gy + sy * k), od["back"]));
      s += r("G back", command_x.build_wayobj(pl, c(gx + k + 1, gy + sy * k), c(gx + k + 1, gy + sy * (k + 1)), od["back"]));
    }
    for (local k = 0; k < 5; k++) {
      s += r("G front", command_x.build_wayobj(pl, c(gx + k + 1, gy + sy * (k - 1)), c(gx + k + 1, gy + sy * k), od["front"]));
      s += r("G front", command_x.build_wayobj(pl, c(gx + k + 1, gy + sy * k), c(gx + k + 2, gy + sy * k), od["front"]));
    }
    foreach (q in [[gx + 1, gy], [gx + 2, gy + sy], [gx + 2, gy], [gx + 1, gy + sy]])
      checks += "[check] " + name + " G" + (sy > 0 ? "se" : "ne") + " (" + q[0] + "," + q[1] + ") " + names(ox + q[0], oy + q[1]) + "\n";
  }
  // 地上の複線
  local px = 32;
  local EW = [["back", 0, 0, 12, 0], ["front", 0, 9, 12, 9], ["front", 1, 1, 11, 1], ["back", 1, 8, 11, 8]];
  local NS = [["back", 0, 0, 0, 9], ["front", 12, 0, 12, 9], ["front", 1, 1, 1, 8], ["back", 11, 1, 11, 8]];
  local pairs = function(tag, x0, wayd) {
    local t = r(tag + " label", marker.work(pl, c(x0, -2), tag));
    foreach (e in EW) t += r(tag + "1 way", way2(wayd(e[0]), null, c(x0 + e[1], e[2]), c(x0 + e[3], e[4])));
    foreach (e in NS) t += r(tag + "1 way", way2(wayd(e[0]), null, c(x0 + e[1], e[2]), c(x0 + e[3], e[4])));
    foreach (e in NS) t += r(tag + "1 wall", command_x.build_wayobj(pl, up(c(x0 + e[1], e[2])), up(c(x0 + e[3], e[4])), od[e[0]]));
    foreach (e in EW) t += r(tag + "1 wall", command_x.build_wayobj(pl, up(c(x0 + e[1], e[2])), up(c(x0 + e[3], e[4])), od[e[0]]));
    return t;
  };
  // 近い斜めの複線: 奥の線を back、1 タイル東の手前の線を front で敷き、分け合うタイル（way 2 本）の壁を twin に置き換える（sample.nut の区画 W2 と同じ）
  local close_pair = function(tag, x0, y0, wayd) {
    local t = r(tag + " back", stair(wayd["back"], ox + x0, oy + y0, 5, 1));
    t += r(tag + " front", stair(wayd["front"], ox + x0 + 1, oy + y0, 5, 1));
    t += r(tag + " back wall", stair_wo(od["back"], ox + x0, oy + y0, 5, 1));
    t += r(tag + " front wall", stair_wo(od["front"], ox + x0 + 1, oy + y0, 5, 1));
    for (local x = x0; x <= x0 + 7; x++) for (local y = y0 - 1; y <= y0 + 6; y++) {
      local q = tile(ox + x, oy + y, mode.z);
      if (q == null || !q.has_two_ways()) continue;
      t += r(tag + " twin", command_x.build_wayobj(pl, c(x, y, mode.z), c(x, y, mode.z), od["twin"]));
      checks += "[check] " + name + " " + tag + " (" + x + "," + y + ") " + names(ox + x, oy + y, mode.z) + "\n";
    }
    t += r(tag + " back wall again", stair_wo(od["back"], ox + x0, oy + y0, 5, 1));
    t += r(tag + " front wall again", stair_wo(od["front"], ox + x0 + 1, oy + y0, 5, 1));
    return t;
  };
  s += pairs("W", px, function(v) { return bd[v]; });
  foreach (q in [[0, 0], [1, 1], [12, 9], [11, 8]]) checks += "[check] " + name + " W1 (" + q[0] + "," + q[1] + ") " + names(ox + px + q[0], oy + q[1]) + "\n";
  foreach (k, v in ["back", "center", "front"]) {
    s += r("W3 way", way2(bd[v], v == "center" ? null : od[v], c(px, 12 + k), c(px + 3, 12 + k)));
  }
  s += close_pair("W2", px + 6, 12, bd);
  // 高架
  mode.z = ELEV_UP;
  mode.pier = pier;
  local ex = 50;
  s += lay_one(ev["single"], od["single"], ox + ex, oy, "elev");
  s += r("L ns", way2(ev["single"], od["single"], c(ex + 22, 0), c(ex + 22, 8)));
  s += r("L ns", way2(ev["single"], od["single"], c(ex + 23, 0), c(ex + 23, 8)));
  s += r("L ew", way2(ev["single"], od["single"], c(ex + 18, 4), c(ex + 27, 4)));
  local cross = img(ox + ex + 3, oy + 7, ELEV_UP);
  checks += "[check] " + name + " elevL west=" + img(ox + ex + 22, oy + 4, ELEV_UP) + " east=" + img(ox + ex + 23, oy + 4, ELEV_UP) + " plain=" + cross
            + " teeE=" + img(ox + ex, oy + 7, ELEV_UP) + " teeW=" + img(ox + ex + 6, oy + 7, ELEV_UP) + "\n";
  // 高架の複線
  local vx = 90;
  s += pairs("WV", vx, function(v) { return ev[v]; });
  foreach (q in [[0, 0], [1, 1], [12, 9], [11, 8]]) checks += "[check] " + name + " WV1 (" + q[0] + "," + q[1] + ") " + names(ox + vx + q[0], oy + q[1], ELEV_UP) + "\n";
  s += close_pair("WV2", vx + 16, 0, ev);
  foreach (k, v in ["back", "center", "front"]) {
    s += r("WV3 way", way2(ev[v], v == "center" ? null : od[v], c(vx, 12 + k), c(vx + 3, 12 + k)));
  }
  mode.z = 0;
  mode.pier = null;
  // 橋とトンネル
  local bx = 125;
  local b = function(x, y, z = 0) { return coord3d(ox + bx + x, oy + y, z); };
  local wl = function(a, z, wo) {
    local e = command_x.build_way(pl, a, z, w, true);
    if (e == null) e = command_x.build_wayobj(pl, a, z, wo);
    return e;
  };
  // 橋の道具を引いて架けると、橋の上の way は本体が速さで選ぶ（橋の速さ以下で一番速い平地の way。simtool.cc の tool_build_bridge_t::do_work と
  // bauer/wegbauer.cc の weg_search）。道路の端のタイルを 1 回押して架けると、その道路が橋の上に敷かれる（bauer/brueckenbauer.cc の build）。
  // 橋の上の way は後から道路を敷いても替わらない（wegbauer.cc）ので、見本は前後の道路を先に敷き、端を押す形（build_bridge_at）で架ける。
  // 押す端のタイルの道路は、橋の向きと逆へつながっている（1 タイルだけの道路の坂からは架からない。向きが無いため）
  local bridge = function(a, stubs) {
    local e = null;
    foreach (p in stubs) if (e == null) e = command_x.build_way(pl, p[0], p[1], w, true);
    if (e == null) e = command_x.build_bridge_at(pl, a, br);
    return e;
  };
  s += r("BT label", marker.work(pl, b(0, -2), "bridge + tunnel"));
  s += r("B1 ew bridge", bridge(b(4, 1), [[b(0, 1), b(4, 1)], [b(10, 1), b(15, 1)]]));
  s += r("B1 ew", wl(b(0, 1), b(15, 1), od["single"]));
  s += r("B1 ns bridge", bridge(b(19, 4), [[b(19, 0), b(19, 4)], [b(19, 10), b(19, 14)]]));
  s += r("B1 ns", wl(b(19, 0), b(19, 14), od["single"]));
  for (local k = 0; k < 2; k++) foreach (x in [0, 8]) s += r("B2 raise", set_slope_kept(b(x, 19, k), slope.all_up_slope));
  s += r("B2 rampW", set_slope_kept(b(1, 19), 56));
  s += r("B2 rampE", set_slope_kept(b(7, 19), 24));
  s += r("B2 ew bridge", bridge(b(1, 19), [[b(0, 19, 2), b(1, 19)], [b(7, 19), b(8, 19, 2)]]));
  s += r("B2 ew", wl(b(0, 19, 2), b(8, 19, 2), od["single"]));
  s += r("B4 rampW", set_slope_kept(b(5, 24), 56));
  s += r("B4 rampE", set_slope_kept(b(11, 24), 24));
  s += r("B4 elevW", command_x.build_way(pl, b(0, 24), b(4, 24), ev["single"], true));
  s += r("B4 elevE", command_x.build_way(pl, b(12, 24), b(15, 24), ev["single"], true));
  // 高架の端 (4) から坂の端 (5) へ道路を敷いて押し、(4) を高架に敷き直す（東の端 (11) は橋の端が隣の高架 (12) とつながる）
  s += r("B4 bridge", bridge(b(5, 24), [[b(4, 24, ELEV_UP), b(5, 24)]]));
  s += r("B4 elevW again", command_x.build_way(pl, b(0, 24), b(4, 24), ev["single"], true));
  s += r("B4 pierW", command_x.build_way(pl, b(0, 24), b(4, 24), pier, true));
  s += r("B4 pierE", command_x.build_way(pl, b(12, 24), b(15, 24), pier, true));
  s += r("B4 wall", command_x.build_wayobj(pl, b(0, 24, ELEV_UP), b(15, 24, ELEV_UP), od["single"]));
  local tn = name + "_tunnel";
  local tunnel = function(tag, ew, x0, at, wo) {
    local t = "";
    if (ew) {
      for (local x = x0 + 3; x <= x0 + 5; x++) for (local k = 0; k < 2; k++) t += r(tag + " raise", set_slope_kept(b(x, at, k), slope.all_up_slope));
      t += r(tag + " rampW", set_slope_kept(b(x0 + 2, at), 24));
      t += r(tag + " rampE", set_slope_kept(b(x0 + 6, at), 56));
      t += r(tag + " tunnel", command_x(tool_build_tunnel).work(pl, b(x0 + 2, at), tn));
      t += r(tag + " way", command_x.build_way(pl, b(x0, at), b(x0 + 2, at), w, true));
      t += r(tag + " way", command_x.build_way(pl, b(x0 + 6, at), b(x0 + 8, at), w, true));
      t += r(tag + " wall", command_x.build_wayobj(pl, b(x0, at), b(x0 + 8, at), wo));
    } else {
      for (local y = 4; y <= 6; y++) for (local k = 0; k < 2; k++) t += r(tag + " raise", set_slope_kept(b(at, y, k), slope.all_up_slope));
      t += r(tag + " rampN", set_slope_kept(b(at, 3), 8));
      t += r(tag + " rampS", set_slope_kept(b(at, 7), 72));
      t += r(tag + " tunnel", command_x(tool_build_tunnel).work(pl, b(at, 3), tn));
      t += r(tag + " way", command_x.build_way(pl, b(at, 0), b(at, 3), w, true));
      t += r(tag + " way", command_x.build_way(pl, b(at, 7), b(at, 10), w, true));
      t += r(tag + " wall", command_x.build_wayobj(pl, b(at, 0), b(at, 10), wo));
    }
    return t;
  };
  s += tunnel("T1 ew", true, 24, 19, od["single"]);
  s += tunnel("T1 ns", false, 0, 37, od["single"]);
  s += tunnel("T3 back", true, 24, 24, od["back"]);
  s += tunnel("T3 front", true, 24, 25, od["front"]);
  // 橋の床（z=2）と端のタイル（坂の端は z=0）、坑口とトンネルの中（z=0。地面のタイルは上げた尾根なので高さで引く）の道路と壁
  foreach (q in [[4, 1, 0], [7, 1, 2], [19, 7, 2], [1, 19, 0], [4, 19, 2], [5, 24, 0], [8, 24, 2], [12, 24, 2]])
    checks += "[check] " + name + " BT bridge (" + q[0] + "," + q[1] + ",z=" + q[2] + ") " + names_h(ox + bx + q[0], oy + q[1], q[2]) + "\n";
  foreach (q in [[26, 19], [28, 19], [37, 3], [37, 5], [26, 24], [28, 25]])
    checks += "[check] " + name + " BT tunnel (" + q[0] + "," + q[1] + ") " + names_h(ox + bx + q[0], oy + q[1], 0) + "\n";
  // 橋脚のつながり
  local qx = 168;
  local q = function(x, y) { return coord3d(ox + qx + x, oy + y, 0); };
  s += r("P label", marker.work(pl, q(0, -3), "pier: " + STANDARD + " / AMI / rail"));
  mode.z = ELEV_UP;
  mode.pier = pier;
  s += r("P1 elev", way2(ev["single"], od["single"], q(2, 0), q(2, 10)));
  s += r("P1 road", command_x.build_way(pl, q(2, 0), q(2, 10), std, true));
  s += r("P1 cross", command_x.build_way(pl, q(-2, 5), q(6, 5), std, true));
  s += r("P2 elev", way2(ev["single"], od["single"], q(8, 2), q(18, 2)));
  s += r("P2 road", command_x.build_way(pl, q(8, 2), q(18, 2), w, true));
  s += r("P2 cross", command_x.build_way(pl, q(13, -2), q(13, 6), w, true));
  s += r("P3 elev", way2(ev["single"], od["single"], q(22, 0), q(22, 10)));
  mode.z = 0;
  mode.pier = null;
  if (rail != null) s += r("P3 rail", command_x.build_way(pl, q(19, 5), q(25, 5), rail, true));
  foreach (p in [[2, 3], [2, 5], [11, 2], [13, 2], [22, 3], [22, 5], [21, 5], [23, 5]])
    checks += "[check] " + name + " P (" + p[0] + "," + p[1] + ") " + names(ox + qx + p[0], oy + p[1], ELEV_UP) + "\n";
  return s;
}
// 高さ z のタイル（橋の床・坑口・トンネルの中）の道路と壁
function names_h(x, y, z) {
  local t = square_x(x, y).get_tile_at_height(z);
  if (t == null) return "(no tile at z=" + z + ")";
  local w = t.get_way(wt_road), o = t.find_object(mo_wayobj);
  return (w == null ? "-" : w.get_desc().get_name() + " d" + w.get_dirs()) + "+" + (o == null ? "-" : o.get_desc().get_name())
         + (t.is_bridge() ? " bridge" : "") + (t.is_tunnel() ? " tunnel" : "");
}

// 降雪側は、敷いた後に一帯を降雪に塗る（地形を変えたタイルは set_slope_kept がその場で塗り直す）
foreach (n, o in ORIGINS) {
  mode.snow = n == SNOW;
  foreach (i, name in ROADS) report += lay(name, o[0], o[1] + i * SPACING);
  if (mode.snow)
    report += r("climate", command_x(tool_set_climate).work(pl, coord3d(o[0] - 3, o[1] - 4, 0),
                                                             coord3d(o[0] + AREA[0], o[1] + (ROADS.len() - 1) * SPACING + AREA[1], 0), "7"));
}
gui.close_all_windows();
return (report == "" ? "ok\n" : "check\n" + report) + checks;
