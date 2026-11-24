// 踏切の見本（ingame/crossing_sample.nut）の H 線・V 線に、閉じた踏切を撮るための列車を 1 本ずつ走らせる（#111）。
// 車庫は線の始まりの端 (0)、駅は (START - 4) と (LEN - 2)。編成は機関車 1 両（いちばん遅いもの。撮る間に踏切を通り過ぎないように）。
// 並びの値（ORIGINS・START・SP・LEN・VX・VY）は crossing_sample.nut と同じにする。返り値に列車ごとの車庫の場所を書く
local ORIGINS = [[20, 24], [276, 24]];
local START = 10, SP = 6;
local LEN = START + 16 * SP + 4;
local VX = 4, VY = 12;
local pl = player_x(0);
local s = "";
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
local depot_desc = null;
foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) if (d.get_waytype() == wt_rail) { depot_desc = d; break; }
local st = null;
foreach (d in building_desc_x.get_available_stations(building_desc_x.station, wt_rail, good_desc_x.passenger)) { st = d; break; }
local loco = null;
foreach (v in vehicle_desc_x.get_available_vehicles(wt_rail))
  if (v.get_power() > 0 && v.can_be_first() && v.can_be_last() && (loco == null || v.get_topspeed() < loco.get_topspeed())) loco = v;
foreach (o in ORIGINS) {
  local lines = [["H", function(i) { return coord3d(o[0] + i, o[1] + 2, 0); }],
                 ["V", function(i) { return coord3d(o[0] + VX, o[1] + VY + i, 0); }]];
  foreach (line in lines) {
    local p = line[1];
    s += r(line[0] + " depot", command_x.build_depot(pl, p(0), depot_desc));
    s += r(line[0] + " st1", command_x.build_station(pl, p(START - 4), st));
    s += r(line[0] + " st2", command_x.build_station(pl, p(LEN - 2), st));
    local dp = p(0);
    local depot = depot_x(dp.x, dp.y, 0);
    depot.append_vehicle(pl, convoy_x(0), loco);
    local list = depot.get_convoy_list();
    local cnv = list[list.len() - 1];
    local e1 = schedule_entry_x(p(START - 4), 0, 0);
    if (e1.x != p(START - 4).x) return s + "schedule_entry_x is broken: the game's script/ folder is not OTRP's\n";
    cnv.change_schedule(pl, schedule_x(wt_rail, [e1, schedule_entry_x(p(LEN - 2), 0, 0)]));
    depot.start_convoy(pl, cnv);
    s += "[train] " + line[0] + " depot=" + dp.x + "," + dp.y + "\n";
  }
}
gui.close_all_windows();
return s + "loco=" + loco.get_name() + " " + loco.get_topspeed() + "km/h";
