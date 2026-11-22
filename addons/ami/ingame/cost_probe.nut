// 操車場など駅・車庫の建設費を測る（#160）。建てる前後の所持金の差と、建物の dat の値を並べる
local pl = player_x(0);
local out = "";
local rail = way_desc_x("ami_rail_ballast");
local yard = building_desc_x("ami_rail_yard");
local st = null;
foreach (d in building_desc_x.get_available_stations(building_desc_x.station, wt_rail, good_desc_x.passenger)) { st = d; break; }
local dep = null;
foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) if (d.get_waytype() == wt_rail && d.get_name() == "ami_rail_depot") dep = d;
function c(x, y) { return coord3d(20 + x, 20 + y, 0); }
function cash() { return pl.get_current_cash(); }
function nw() { return pl.get_current_net_wealth(); }
local a = cash();
local na = nw();
local e = command_x.build_way(pl, c(0, 0), c(0, 30), rail, true);
out += "way err=" + e + " charged " + (a - cash()) + "\n";
function probe(tag, desc, x, y) {
  local b = cash();
  local nb = nw();
  local e = command_x.build_station(pl, c(x, y), desc);
  local m = cash();
  out += tag + " netwealth_diff(1/100cr)=" + (nb - nw()) + " ";
  out += tag + " (" + x + "," + y + ") err=" + e + " charged " + (b - m) + " price=" + desc.get_cost() + " maint=" + desc.get_maintenance() + "\n";
}
probe("yard1", yard, 0, 3);
probe("yard2", yard, 0, 10);
probe("yard3", yard, 0, 11);
probe("pax", st, 0, 20);
probe("yard4", yard, 0, 21);
out += "cash(float) "+cash()+" ; cash after " + cash() + "\n";
return out;
