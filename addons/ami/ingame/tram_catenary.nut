// 路面軌道の架線（#376）の見本。ingame/tram_catenary.sh が流す。路面軌道を敷いた経路にそのまま架線を張る。
// 2 つの組（UNDER の順に SPACING タイルずつ南へ）: AMI の一般道路の上と、土の上。原点 (ox,oy) から:
//   A 直線の行き止まり（東西・南北）・B 輪と十字（カーブ・T字）・C 斜めの階段 2 本（se・ne）・D 坂の十字・E 急坂の十字
//   F 並べた 2 本の直線（柱が線の間に立つ）
//   G 近い斜め（分け合うタイル）・H 車庫を建てた後に車庫のタイルまで架線を張る
// 電車（V）: 輪の外の直線の西の端に路面軌道の車庫を建て、電化の要る路面電車を 1 編成入れて、東の端と車庫の前を往復させる（出すのは .sh の CAPTURE）。
// 返り値の先頭が ok なら全部敷けた。[check] の行は、電化されたか（elec）と、使った車両
local TRAM = "ami_tram";
local CAT = "ami_tram_catenary";
local DEPOT = "ami_tram_depot";
local UNDER = ["ami_road_general", null];
local OX = 20;
local OY = 20;
local SPACING = 26;
local pl = player_x(0);
local report = "";
local checks = "";
function r(name, v) { if (v == null) return ""; return name + "=[" + v + "]\n"; }

local wo = wayobj_desc_x(CAT);
local w = way_desc_x(TRAM);
if (wo == null || w == null) return "missing desc";
local depots = {};
foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) depots[d.get_name()] <- d;

local veh = null;
foreach (e in vehicle_desc_x.get_available_vehicles(wt_tram))
  if (e.can_be_first() && e.can_be_last() && e.needs_electrification() && e.get_power() > 0
      && (veh == null || e.get_topspeed() < veh.get_topspeed())) veh = e;
if (veh == null) report += "no electric tram vehicle\n";

foreach (ui, under in UNDER) {
  local ox = OX, oy = OY + ui * SPACING;
  local u = under == null ? null : way_desc_x(under);
  local c = function(x, y, z = 0) { return coord3d(ox + x, oy + y, z); };
  local line = function(x0, y0, x1, y1) {
    local e = null;
    if (u != null) e = command_x.build_way(pl, c(x0, y0), c(x1, y1), u, true);
    local f = command_x.build_way(pl, c(x0, y0), c(x1, y1), w, true);
    local g = command_x.build_wayobj(pl, c(x0, y0), c(x1, y1), wo);
    return g != null ? g : (f != null ? f : e);
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
  report += r("A ew", line(0, 0, 3, 0));
  report += r("A ns", line(5, 0, 5, 3));
  report += r("C se", stair(8, 0, 3, 1));
  report += r("C ne", stair(13, 3, 3, -1));
  report += r("B1", line(0, 5, 6, 5));
  report += r("B2", line(6, 5, 6, 11));
  report += r("B3", line(6, 11, 0, 11));
  report += r("B4", line(0, 11, 0, 5));
  report += r("B5", line(3, 5, 3, 11));
  report += r("B6", line(0, 8, 6, 8));
  foreach (h in [[11, 8, 1], [17, 8, 2]]) {
    local cx = h[0], cy = h[1], n = h[2];
    for (local k = 0; k < n; k++) report += r("hill raise", command_x.set_slope(pl, c(cx, cy, k), slope.all_up_slope));
    report += r("hill rampN", command_x.set_slope(pl, c(cx, cy - 1), 4 * n));
    report += r("hill rampS", command_x.set_slope(pl, c(cx, cy + 1), 36 * n));
    report += r("hill rampW", command_x.set_slope(pl, c(cx - 1, cy), 12 * n));
    report += r("hill rampE", command_x.set_slope(pl, c(cx + 1, cy), 28 * n));
    report += r("hill ns", line(cx, cy - 2, cx, cy + 2));
    report += r("hill ew", line(cx - 2, cy, cx + 2, cy));
  }
  report += r("F1", line(0, 14, 8, 14));
  report += r("F2", line(0, 15, 8, 15));

  // G 近い斜め（1 タイルを 2 本の斜めが分け合う。路面軌道は近い斜めの絵を持つ way 1 本になる）
  local gx = 22, gy = 0;
  for (local k = 0; k < 5; k++) {
    report += r("G h" + k, line(gx + k, gy + k, gx + k + 2, gy + k));
    report += r("G v" + k, line(gx + k + 1, gy + k - 1, gx + k + 1, gy + k + 1));
  }
  // H 車庫を建てた後に、車庫のタイルまで架線を張る
  report += r("H way", command_x.build_way(pl, c(22, 12), c(27, 12), w, true));
  report += r("H depot", command_x.build_depot(pl, c(22, 12), depots[DEPOT]));
  report += r("H catenary", command_x.build_wayobj(pl, c(22, 12), c(27, 12), wo));
  local hway = square_x(ox + 22, oy + 12).get_ground_tile().get_way(wt_rail);
  checks += "[check] depot-after (" + (ox + 22) + "," + (oy + 12) + ")=" + (hway == null ? "-" : (hway.is_electrified() ? "elec" : "NG")) + "\n";

  // V: 車庫と電車
  local y = 18;
  // 車庫は道路のあるタイルに建てられないので、車庫のタイルには道路を敷かない
  if (u != null) report += r("V road", command_x.build_way(pl, c(1, y), c(12, y), u, true));
  report += r("V way", command_x.build_way(pl, c(0, y), c(12, y), w, true));
  report += r("V catenary", command_x.build_wayobj(pl, c(0, y), c(12, y), wo));
  report += r("V depot", command_x.build_depot(pl, c(0, y), depots[DEPOT]));
  if (veh != null) {
    local p = c(0, y), q = c(12, y), back = c(1, y);
    local depot = depot_x(p.x, p.y, 0);
    depot.append_vehicle(pl, convoy_x(0), veh);
    local list = depot.get_convoy_list();
    if (list.len() == 0) report += "V no convoy\n";
    else {
      local cnv = list[list.len() - 1];
      cnv.change_schedule(pl, schedule_x(wt_tram, [schedule_entry_x(q, 0, 0), schedule_entry_x(back, 0, 0)]));
    }
  }
  local tag = under == null ? "ground" : under;
  local elec = "";
  foreach (p in [[1, 0], [5, 1], [3, 8], [11, 6], [0, y], [6, y]]) {
    local way = square_x(ox + p[0], oy + p[1]).get_ground_tile().get_way(wt_rail);
    elec += " (" + (ox + p[0]) + "," + (oy + p[1]) + ")=" + (way == null ? "-" : (way.is_electrified() ? "elec" : "NG"));
  }
  checks += "[check] " + tag + elec + "\n";
}
checks += "[check] vehicle=" + (veh == null ? "-" : veh.get_name()) + "\n";
gui.close_all_windows();
return (report == "" ? "ok\n" : "check\n" + report) + checks;
