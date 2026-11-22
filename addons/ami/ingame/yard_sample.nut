// AMI の操車場（ami_rail_yard。#115）の見本。在来線（ami_rail_ballast）の上に操車場を建てる。
// 検証用の flat_512.sve に、温暖側 (20,20) と降雪側 (276,20) の 2 か所へ同じ並びで敷き、降雪側は一帯を降雪に塗り直す。
// 使い方（アドオンのディレクトリで）: sample_parallel.sh に NUT=ingame/yard_sample.nut を付ける（撮る場所は sample_spots.sh の YARD_SPOTS）。
// 返り値の先頭が ok なら全部建ち、[check] で比べた駅も期待どおり。違えば先頭が check で、「名前=[…]」が続く。
// [info] の行は、建てられるかを試しただけの所（斜め・坂・高架。建たなくてもよい）。最後に確かめた値（[check] の行）が続く。
//
// 区画（原点 (ox,oy) から）:
//   Y1 南北の線路 x=0（y=0〜8）に 1 タイル（y=3）。x=3 に 3 タイル（y=2〜4。真ん中を最後に建てる）
//   YP 乗客の駅の隣: x=6 の線路に、乗客の駅 (6,2) と操車場 (6,3)(6,4)。同じ駅になり、通路は乗客の駅の側へ続く
//   YE 東西の線路 y=11（x=0〜8）に 1 タイル（x=1）。y=14 に 3 タイル（x=2〜4）
//   YG 並べた留置線: 南北の線路 x=10・11・12（y=0〜8）に、それぞれ y=2〜6 の 5 タイル
//   YW 壁つき: x=15 に基盤の版 back と壁 back（y=0〜8）、y=2〜4 に操車場
//   YT 列車: x=19 の線路（y=0〜10）の北の端に車庫、y=4〜6 に操車場。列車を出し、操車場で「荷を満載まで待つ」で止めておく
//   YX 試し: 斜め（(23,0) から南東へ 4 段）・坂（x=30 の線路の y=4 を 1 段上げる）・高架（x=33、y=0〜8 を高さ 2）の上に建てる
local ORIGINS = [[20, 20], [276, 20]];
local SNOW = 1;
local AREA = [38, 18];
local pl = player_x(0);
local report = "";
local checks = "";
local infos = "";
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
local mode = {snow = false};
function set_slope_kept(p, s) {
  local e = command_x.set_slope(pl, p, s);
  if (e == null && mode.snow) e = command_x(tool_set_climate).work(pl, coord3d(p.x - 1, p.y - 1, 0), coord3d(p.x + 1, p.y + 1, 0), "7");
  return e;
}
function halt_at(x, y, z = 0) {
  local t = square_x(x, y).get_tile_at_height(z);
  if (t == null) return null;
  return t.get_halt();
}
// 駅の名前・乗客を扱うか（hname が null なら、駅のあること・乗客と郵便を扱わないことだけ見る。そうでなければ同じ駅か）
function expect_halt(tag, x, y, other = null, z = 0) {
  local h = halt_at(x, y, z);
  local desc = h == null ? "-" : h.get_name() + " pax=" + h.accepts_good(good_desc_x.passenger) + " mail=" + h.accepts_good(good_desc_x.mail);
  checks += "[check] " + tag + " " + desc + "\n";
  if (h == null) return tag + " halt=[none]\n";
  if (other == null) return (h.accepts_good(good_desc_x.passenger) || h.accepts_good(good_desc_x.mail)) ? tag + " accepts=[pax or mail]\n" : "";
  local o = halt_at(other[0], other[1]);
  return (o != null && o.get_name() == h.get_name()) ? "" : tag + " not joined with (" + other[0] + "," + other[1] + ")\n";
}

function lay(ox, oy) {
  local rail = way_desc_x("ami_rail_ballast");
  local yard = building_desc_x("ami_rail_yard");
  local bw = way_desc_x("ami_rail_ballast_base_back");
  local elev = way_desc_x("ami_rail_ballast_elev_single");
  local wall = wayobj_desc_x("ami_wall_rail_back");
  if (rail == null || yard == null || bw == null || elev == null || wall == null) return "desc=[missing]\n";
  local st = null;
  foreach (d in building_desc_x.get_available_stations(building_desc_x.station, wt_rail, good_desc_x.passenger)) { st = d; break; }
  local depot_desc = null;
  foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) if (d.get_waytype() == wt_rail && d.get_name() == "ami_rail_depot") depot_desc = d;
  local c = function(x, y, z = 0) { return coord3d(ox + x, oy + y, z); };
  local way = function(tag, a, b, w = null) { return r(tag, command_x.build_way(pl, a, b, w == null ? rail : w, true)); };
  local build = function(tag, x, y, z = 0) { return r(tag + " (" + x + "," + y + ")", command_x.build_station(pl, c(x, y, z), yard)); };
  local s = "";
  // Y1
  s += way("Y1 a", c(0, 0), c(0, 8));
  local cash = pl.get_current_net_wealth() / 100.0;  // 所持金（get_current_cash）は 32 ビット float で、残高が大きいと 64 cr 刻みに丸められる（#160）
  s += build("Y1", 0, 3);
  infos += "[info] Y1 (0,3) charged " + (cash - pl.get_current_net_wealth() / 100.0) + " cr\n";
  s += way("Y1 b", c(3, 0), c(3, 8)) + build("Y1", 3, 2) + build("Y1", 3, 4) + build("Y1", 3, 3);
  s += expect_halt("Y1 (0,3)", ox, oy + 3) + expect_halt("Y1 (3,3)", ox + 3, oy + 3, [ox + 3, oy + 2]);
  // YP
  s += way("YP", c(6, 0), c(6, 8)) + r("YP pax", command_x.build_station(pl, c(6, 2), st)) + build("YP", 6, 3) + build("YP", 6, 4);
  s += expect_halt("YP (6,4)", ox + 6, oy + 4, [ox + 6, oy + 2]);
  // YE
  s += way("YE a", c(0, 11), c(8, 11)) + build("YE", 1, 11);
  s += way("YE b", c(0, 14), c(8, 14)) + build("YE", 2, 14) + build("YE", 3, 14) + build("YE", 4, 14);
  s += expect_halt("YE (3,14)", ox + 3, oy + 14);
  // YG
  foreach (x in [10, 11, 12]) {
    s += way("YG", c(x, 0), c(x, 8));
    for (local y = 2; y <= 6; y++) s += build("YG", x, y);
  }
  // YW
  s += way("YW", c(15, 0), c(15, 8), bw) + r("YW wall", command_x.build_wayobj(pl, c(15, 0), c(15, 8), wall));
  for (local y = 2; y <= 4; y++) s += build("YW", 15, y);
  s += expect_halt("YW (15,3)", ox + 15, oy + 3);
  // YT
  s += way("YT", c(19, 0), c(19, 10)) + r("YT depot", command_x.build_depot(pl, c(19, 0), depot_desc));
  for (local y = 4; y <= 6; y++) s += build("YT", 19, y);
  local loco = null;
  foreach (v in vehicle_desc_x.get_available_vehicles(wt_rail))
    if (v.get_power() > 0 && !v.needs_electrification() && v.can_be_first() && v.can_be_last() && (loco == null || v.get_topspeed() > loco.get_topspeed())) loco = v;
  local dp = c(19, 0);
  local depot = depot_x(dp.x, dp.y, 0);
  depot.append_vehicle(pl, convoy_x(0), loco);
  local list = depot.get_convoy_list();
  local cnv = list[list.len() - 1];
  if (!cnv.change_schedule(pl, schedule_x(wt_rail, [schedule_entry_x(c(19, 6), 100, 0), schedule_entry_x(c(19, 9), 0, 0)]))) s += "YT schedule=[failed]\n";
  if (!depot.start_convoy(pl, cnv)) s += "YT start=[failed]\n";
  // YX（試し。建たなくても返り値の先頭は ok のまま）
  for (local k = 0; k < 4; k++) {
    command_x.build_way(pl, c(23 + k, k), c(23 + k, k + 1), rail, true);
    command_x.build_way(pl, c(23 + k, k + 1), c(23 + k + 1, k + 1), rail, true);
  }
  local e = command_x.build_station(pl, c(24, 1), yard);
  infos += "[info] YX diagonal (24,1): " + (e == null ? "built" : e) + "\n";
  set_slope_kept(c(30, 4), slope.all_up_slope);
  set_slope_kept(c(30, 3), 4);
  set_slope_kept(c(30, 5), 36);
  command_x.build_way(pl, c(30, 0), c(30, 8), rail, true);
  e = command_x.build_station(pl, c(30, 3), yard);
  infos += "[info] YX slope (30,3): " + (e == null ? "built" : e) + "\n";
  command_x.build_way(pl, c(33, 0), c(33, 8), elev, true);
  e = command_x.build_station(pl, c(33, 4, 2), yard);
  infos += "[info] YX elevated (33,4,z2): " + (e == null ? "built" : e) + "\n";
  return s;
}

foreach (n, o in ORIGINS) {
  mode.snow = n == SNOW;
  try { report += lay(o[0], o[1]); } catch (err) { report += "error=[" + err + "]\n"; }
  if (mode.snow)
    report += r("climate", command_x(tool_set_climate).work(pl, coord3d(o[0] - 3, o[1] - 4, 0), coord3d(o[0] + AREA[0], o[1] + AREA[1], 0), "7"));
}
gui.close_all_windows();
return (report == "" ? "ok\n" : "check\n" + report) + infos + checks;
