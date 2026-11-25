// AMI の道路の停留所（ami_road_bus_stop・ami_road_truck_stop。#277）の見本。道路の種類ごとに、停留所を建てて、駅になることと扱う荷を確かめる。
// 検証用の flat_512_left_v64.sve に、温暖側 (20,20) と降雪側 (276,20) の 2 か所へ同じ並びで敷き、降雪側は一帯を降雪に塗り直す。
// 使い方: PORT=<ポート> NUT=ingame/road_stop_sample.nut bash ingame/game.sh の後、SPOTS で撮る（道路ごとの区画の左上が撮る場所）。
// 返り値の先頭が ok なら全部建ち、[check] も期待どおり。違えば「名前=[…]」が続く。
//
// 区画（原点 (ox,oy) から。道路ごとに南へ ROW_DY ずつ）:
//   A 南北の道路 x=0（y=0〜10）に、バス停 1 タイル（y=1）と、バス停 3 タイル（y=4〜6。真ん中を最後に建てる）
//   B 南北の道路 x=4（y=0〜10）に、荷役所 1 タイル（y=1）と、荷役所 3 タイル（y=4〜6）
//   C 東西の道路 y=14 を使う（x=0〜14）: バス停 1 タイル（x=1）、バス停 3 タイル（x=4〜6）、荷役所 3 タイル（x=9〜11）
//   D 歩道つき: 南北の道路 x=8（y=0〜10）の東の隣 x=9 に ami_sidewalk を敷き、バス停 3 タイル（y=3〜5）
local ORIGINS = [[20, 20], [276, 20]];
local SNOW = 1;
local ROADS = ["ami_road_local", "ami_road_general", "ami_road_trunk"];
local ROW_DY = 20;
local AREA = [16, 61];
local pl = player_x(0);
local report = "";
local checks = "";
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
local mode = {snow = false};

function halt_at(x, y) {
  local t = square_x(x, y).get_tile_at_height(0);
  return t == null ? null : t.get_halt();
}
// 駅になること・扱う荷（pax・post・ware）を確かめる
function expect_halt(tag, x, y, pax, mail, ware) {
  local h = halt_at(x, y);
  if (h == null) { checks += "[check] " + tag + " halt=none\n"; return tag + " halt=[none]\n"; }
  local p = h.accepts_good(good_desc_x.passenger), m = h.accepts_good(good_desc_x.mail);
  local w = false;
  foreach (nm in ["Coal", "Kohle", "Gravel", "Kies", "Iron", "Steel", "Beer", "Bier"]) {  // 貨物の種類（get_catg_index > 2）のどれかを受け取るか。pak128 に無い名前は飛ばす
    try { local g = good_desc_x(nm); if (g.get_catg_index() > 2 && h.accepts_good(g)) { w = true; break; } } catch (e) {}
  }
  checks += "[check] " + tag + " " + h.get_name() + " pax=" + p + " mail=" + m + " ware=" + w + "\n";
  if (p != pax || m != mail || w != ware) return tag + " goods=[pax " + p + " mail " + m + " ware " + w + "]\n";
  return "";
}

function lay(road, ox, oy) {
  local rd = way_desc_x(road);
  local bus = building_desc_x("ami_road_bus_stop");
  local truck = building_desc_x("ami_road_truck_stop");
  local side = way_desc_x("ami_sidewalk");
  if (rd == null || bus == null || truck == null || side == null) return road + " desc=[missing]\n";
  local c = function(x, y) { return coord3d(ox + x, oy + y, 0); };
  local way = function(tag, a, b, w = null) { return r(road + " " + tag, command_x.build_way(pl, a, b, w == null ? rd : w, true)); };
  local build = function(tag, x, y, d) { return r(road + " " + tag + " (" + x + "," + y + ")", command_x.build_station(pl, c(x, y), d)); };
  local s = "";
  // A・B
  s += way("A", c(0, 0), c(0, 10)) + build("A1", 0, 1, bus);
  s += build("A3", 0, 4, bus) + build("A3", 0, 6, bus) + build("A3", 0, 5, bus);
  s += way("B", c(4, 0), c(4, 10)) + build("B1", 4, 1, truck);
  s += build("B3", 4, 4, truck) + build("B3", 4, 6, truck) + build("B3", 4, 5, truck);
  s += expect_halt("A1", ox, oy + 1, true, true, false) + expect_halt("A3", ox, oy + 5, true, true, false);
  s += expect_halt("B1", ox + 4, oy + 1, false, false, true) + expect_halt("B3", ox + 4, oy + 5, false, false, true);
  // C
  s += way("C", c(0, 14), c(14, 14)) + build("C1", 1, 14, bus);
  s += build("C3", 4, 14, bus) + build("C3", 6, 14, bus) + build("C3", 5, 14, bus);
  s += build("C3t", 9, 14, truck) + build("C3t", 11, 14, truck) + build("C3t", 10, 14, truck);
  s += expect_halt("C1", ox + 1, oy + 14, true, true, false) + expect_halt("C3t", ox + 10, oy + 14, false, false, true);
  // D
  s += way("D", c(8, 0), c(8, 10)) + way("D side", c(9, 0), c(9, 10), side);
  s += build("D3", 8, 3, bus) + build("D3", 8, 5, bus) + build("D3", 8, 4, bus);
  return s;
}

foreach (n, o in ORIGINS) {
  mode.snow = n == SNOW;
  if (mode.snow)
    report += r("climate", command_x(tool_set_climate).work(pl, coord3d(o[0] - 3, o[1] - 4, 0), coord3d(o[0] + AREA[0], o[1] + AREA[1], 0), "7"));
  foreach (i, road in ROADS) report += lay(road, o[0], o[1] + i * ROW_DY);
}
return (report == "" ? "ok\n" : "check\n" + report) + checks;
