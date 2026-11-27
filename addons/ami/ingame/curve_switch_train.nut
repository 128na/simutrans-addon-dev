// 列車の予約で分岐の絵が切り替わるかを見る見本（#88）。curve_switch_study.nut の区画の東（x = OX + 30〜）に、組ごとに敷く:
//   y=5 back を x=30〜44、y=6 front を x=33〜44。x=36 で back↔front の渡り線（T字どうし）。車庫は (30,5)、駅は (32,5) と (42,6)
//   編成 1 本が back から渡り線を通って front の駅へ往復する。渡り線の 2 タイルの絵の番号は curve_switch_study.sh の TRAIN=1 が読む
// 使い方: ゲームを curve_switch_study.sh で起動したまま、PORT=<ポート> TRAIN=1 bash ingame/curve_switch_study.sh が流す
local SETS = [["iss", "iss_wtg_0240_back", "iss_wtg_0240_front"], ["ami", "ami_rail_ballast_base_back", "ami_rail_ballast_base_front"], ["amin", "ami_rail_ballast", "ami_rail_ballast"]];
local OX = 180;
local OY = 20;
local SPACING = 34;
local pl = player_x(0);
local s = "";
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
local depot_desc = null;
foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) if (d.get_waytype() == wt_rail) { depot_desc = d; break; }
local st = null;
foreach (d in building_desc_x.get_available_stations(building_desc_x.station, wt_rail, good_desc_x.passenger)) { st = d; break; }
local loco = null;
foreach (v in vehicle_desc_x.get_available_vehicles(wt_rail)) if (v.get_power() > 0 && v.can_be_first() && v.can_be_last()) { loco = v; break; }
foreach (i, set in SETS) {
  local oy = OY + i * SPACING;
  local back = way_desc_x(set[1]);
  local front = way_desc_x(set[2]);
  if (!back.is_valid() || !front.is_valid()) { s += set[0] + " desc=[missing]\n"; continue; }
  local c = function(x, y) { return coord3d(OX + x, oy + y, 0); };
  s += r("back", command_x.build_way(pl, c(0, 5), c(14, 5), back, true));
  s += r("front", command_x.build_way(pl, c(3, 6), c(14, 6), front, true));
  s += r("x", command_x.build_way(pl, c(6, 5), c(6, 6), back, true));
  s += r("back again", command_x.build_way(pl, c(0, 5), c(14, 5), back, true));
  s += r("front again", command_x.build_way(pl, c(3, 6), c(14, 6), front, true));
  s += r("depot", command_x.build_depot(pl, c(0, 5), depot_desc));
  s += r("st1", command_x.build_station(pl, c(2, 5), st));
  s += r("st2", command_x.build_station(pl, c(12, 6), st));
  local depot = depot_x(OX, oy + 5, 0);
  depot.append_vehicle(pl, convoy_x(0), loco);
  local list = depot.get_convoy_list();
  local cnv = list[list.len() - 1];
  local e1 = schedule_entry_x(c(2, 5), 0, 0);
  if (e1.x != OX + 2) return s + "schedule_entry_x is broken: the game's script/ folder is not OTRP's\n";
  cnv.change_schedule(pl, schedule_x(wt_rail, [e1, schedule_entry_x(c(12, 6), 0, 0)]));
  depot.start_convoy(pl, cnv);
}
gui.close_all_windows();
return s + "loco=" + loco.get_name();
