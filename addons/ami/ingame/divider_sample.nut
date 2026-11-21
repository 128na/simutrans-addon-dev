// AMI の中央分離帯つきの壁（ami_wall_road_front_divider・ami_wall_road_center_divider・ami_wall_road_twin_divider。#118）の見本。
// 道路を 2 タイル並べた 4 車線の、手前のタイルに分離帯つきの壁を重ねる。道路 2 種（ROADS）それぞれに、種類ごとに SPACING ずつ南へ敷く。
// 検証用の flat_512.sve に、温暖側 (20,20) と降雪側 (276,20) の 2 か所へ同じ並びで敷き、降雪側は一帯を降雪に塗り直す（地形を変えたタイルはその場で塗り直す）。
// 使い方（アドオンのディレクトリで）: sample_parallel.sh に NUT=ingame/divider_sample.nut を付ける（撮る場所は sample_spots.sh の DIVIDER_SPOTS）。
// 返り値の先頭が ok なら全部敷けて、[check] で比べた way-object も期待どおり。違えば先頭が check で、「名前 場所=[…]」が続く。最後に確かめた値（[check] の行）が続く。
//
// 1 種ずつの区画（原点 (ox,oy) から）:
//   P2 東西の 4 車線: y=0 に基盤の版 back と壁 back、y=1 に基盤の版 front と front_divider（x=0〜10。西の端は行き止まり）。
//      (5,-2)-(5,4) を、壁の無い通常の版の道路で横切る（十字・T字）
//   PN 南北の 4 車線: x=13 に back と壁 back、x=14 に front と front_divider（y=0〜8）。(·,4) を 1 段上げた坂
//   P0 壁の無い 4 車線: y=4・5 に基盤の版 center、y=5 に center_divider（x=0〜10）
//   P3 6 車線: y=8・9・10 に基盤の版 back・center・front。壁 back・center_divider・front_divider（x=0〜10）
//   PE 高架の 4 車線: y=0・1 に高架の版 back・front と、壁 back・front_divider（x=18〜28）
//   PD 近い斜め: (32,0) から南東へ 5 段、奥の線に back と壁 back、1 タイル東の手前の線に front と front_divider。
//      分け合うタイル（way 2 本）の way-object を twin_divider に置き換え、壁を敷き直す（road_struct_sample.nut の W2 と同じ敷き方）
local ROADS = ["ami_road_general", "ami_road_expressway"];
local ORIGINS = [[20, 20], [276, 20]];
local SNOW = 1;
local SPACING = 16;
local AREA = [44, 13];
local ELEV_UP = 2;
local pl = player_x(0);
local marker = command_x(tool_set_marker);
local report = "";
local checks = "";
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
// タイルの道路と way-object の名前（d の後ろは道路の向き）。(2) は way が 2 本
function names(x, y, z = 0) {
  local t = square_x(x, y).get_tile_at_height(z);
  if (t == null) return "-";
  local w = t.get_way(wt_road), o = t.find_object(mo_wayobj);
  return (w == null ? "-" : w.get_desc().get_name() + " d" + w.get_dirs()) + "+" + (o == null ? "-" : o.get_desc().get_name())
         + (t.has_two_ways() ? "(2)" : "");
}
// タイルの way-object の名前が want でなければ（two なら way 2 本でなければ）、返り値に足す（返り値の先頭が check になる）
function expect(tag, x, y, want, two = false, z = 0) {
  checks += "[check] " + tag + " " + names(x, y, z) + "\n";
  local t = square_x(x, y).get_tile_at_height(z);
  local o = t == null ? null : t.find_object(mo_wayobj);
  local got = o == null ? "-" : o.get_desc().get_name();
  if (got == want && (!two || t.has_two_ways())) return "";
  return tag + " want=[" + want + (two ? "(2)" : "") + "] got=[" + got + "]\n";
}
local mode = {snow = false};
function set_slope_kept(p, s) {
  local e = command_x.set_slope(pl, p, s);
  if (e == null && mode.snow) e = command_x(tool_set_climate).work(pl, coord3d(p.x - 1, p.y - 1, 0), coord3d(p.x + 1, p.y + 1, 0), "7");
  return e;
}
// way を敷き、同じ経路に way-object を重ねる（wo が null なら way だけ）。z は way-object を敷く高さ（高架）
function way2(w, wo, a, b, z = 0) {
  local e = command_x.build_way(pl, a, b, w, true);
  if (wo != null) {
    local e2 = command_x.build_wayobj(pl, coord3d(a.x, a.y, z), coord3d(b.x, b.y, z), wo);
    if (e2 != null) e = e2;
  }
  return e;
}
function stair(w, x, y, n) {
  local e = null;
  for (local k = 0; k < n; k++) {
    local a = command_x.build_way(pl, coord3d(x + k, y + k, 0), coord3d(x + k, y + k + 1, 0), w, true);
    local b = command_x.build_way(pl, coord3d(x + k, y + k + 1, 0), coord3d(x + k + 1, y + k + 1, 0), w, true);
    if (a != null) e = a;
    if (b != null) e = b;
  }
  return e;
}
function stair_wo(wo, x, y, n) {
  local e = null;
  for (local k = 0; k < n; k++) {
    local a = command_x.build_wayobj(pl, coord3d(x + k, y + k, 0), coord3d(x + k, y + k + 1, 0), wo);
    local b = command_x.build_wayobj(pl, coord3d(x + k, y + k + 1, 0), coord3d(x + k + 1, y + k + 1, 0), wo);
    if (a != null) e = a;
    if (b != null) e = b;
  }
  return e;
}

function lay(name, ox, oy) {
  local w = way_desc_x(name);
  if (w == null) return name + " desc=[missing]\n";
  local bd = {}, ed = {}, od = {};
  foreach (v in ["back", "center", "front"]) {
    bd[v] <- way_desc_x(name + "_base_" + v);
    ed[v] <- way_desc_x(name + "_elev_" + v);
    if (bd[v] == null || ed[v] == null) return name + "_base/elev_" + v + " desc=[missing]\n";
  }
  foreach (v in ["back", "front_divider", "center_divider", "twin_divider"]) {
    od[v] <- wayobj_desc_x("ami_wall_road_" + v);
    if (od[v] == null) return "ami_wall_road_" + v + " desc=[missing]\n";
  }
  local c = function(x, y, z = 0) { return coord3d(ox + x, oy + y, z); };
  local s = r(name + " label", marker.work(pl, c(0, -3), name + ": P2 ew / PN ns slope / P0 no walls / P3 6 lanes / PE elevated / PD close diagonal"));
  // P2
  s += r("P2 back", way2(bd["back"], od["back"], c(0, 0), c(10, 0)));
  s += r("P2 front", way2(bd["front"], od["front_divider"], c(0, 1), c(10, 1)));
  s += r("P2 cross", way2(w, null, c(5, -2), c(5, 4)));
  s += expect(name + " P2 (2,1)", ox + 2, oy + 1, "ami_wall_road_front_divider");
  s += expect(name + " P2 (5,1)", ox + 5, oy + 1, "ami_wall_road_front_divider");
  // PN（坂）
  for (local x = 12; x <= 15; x++) {
    s += r("PN raise", set_slope_kept(c(x, 4), slope.all_up_slope));
    s += r("PN rampN", set_slope_kept(c(x, 3), 4));
    s += r("PN rampS", set_slope_kept(c(x, 5), 36));
  }
  s += r("PN back", way2(bd["back"], od["back"], c(13, 0), c(13, 8)));
  s += r("PN front", way2(bd["front"], od["front_divider"], c(14, 0), c(14, 8)));
  s += expect(name + " PN (14,3)", ox + 14, oy + 3, "ami_wall_road_front_divider");
  // P0（壁なし）
  s += r("P0 back", way2(bd["center"], null, c(0, 4), c(10, 4)));
  s += r("P0 front", way2(bd["center"], od["center_divider"], c(0, 5), c(10, 5)));
  s += expect(name + " P0 (3,5)", ox + 3, oy + 5, "ami_wall_road_center_divider");
  // P3（6 車線）
  s += r("P3 back", way2(bd["back"], od["back"], c(0, 8), c(10, 8)));
  s += r("P3 center", way2(bd["center"], od["center_divider"], c(0, 9), c(10, 9)));
  s += r("P3 front", way2(bd["front"], od["front_divider"], c(0, 10), c(10, 10)));
  // PE（高架）
  s += r("PE back", way2(ed["back"], od["back"], c(18, 0), c(28, 0), ELEV_UP));
  s += r("PE front", way2(ed["front"], od["front_divider"], c(18, 1), c(28, 1), ELEV_UP));
  s += expect(name + " PE (23,1)", ox + 23, oy + 1, "ami_wall_road_front_divider", false, ELEV_UP);
  // PD（近い斜め）
  local dx = 32;
  s += r("PD back", stair(bd["back"], ox + dx, oy, 5));
  s += r("PD front", stair(bd["front"], ox + dx + 1, oy, 5));
  s += r("PD back wall", stair_wo(od["back"], ox + dx, oy, 5));
  s += r("PD front wall", stair_wo(od["front_divider"], ox + dx + 1, oy, 5));
  for (local x = dx; x <= dx + 7; x++) for (local y = -1; y <= 6; y++) {
    local t = square_x(ox + x, oy + y).get_ground_tile();
    if (t == null || !t.has_two_ways()) continue;
    s += r("PD twin", command_x.build_wayobj(pl, c(x, y), c(x, y), od["twin_divider"]));
  }
  s += r("PD back wall again", stair_wo(od["back"], ox + dx, oy, 5));
  s += r("PD front wall again", stair_wo(od["front_divider"], ox + dx + 1, oy, 5));
  // 敷き直した後も、分け合うタイル（way 2 本）は twin_divider（1011）のまま残る
  for (local k = 1; k <= 4; k++)
    s += expect(name + " PD (" + (dx + k) + "," + k + ")", ox + dx + k, oy + k, "ami_wall_road_twin_divider", true);
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
