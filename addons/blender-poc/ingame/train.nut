// 車両を走らせる確認（未完成: 車庫・駅・編成までは作れるが、ダイヤの設定 change_schedule が通らない）: 側壁付きの線路（single）に、車庫・駅 2 つ・編成 1 本を置いて往復させる。flat.sve で使う。
// 線路: (100,40) から東へ (112,40)、角を曲がって南へ (112,48)。車庫は (100,40)、駅は (103,40) と (112,46)。
// 撮るときは gui.jump(coord3d(108, 42, 0))。
function r(name, v) { return name + "=" + (v == null ? "ok" : "[" + v + "]") + "\n"; }
local pl = player_x(0);
local w = way_desc_x("bpoc_track_wall_single");
local s = "";
s += r("ew", command_x.build_way(pl, coord3d(100, 40, 0), coord3d(112, 40, 0), w, true));
s += r("ns", command_x.build_way(pl, coord3d(112, 40, 0), coord3d(112, 48, 0), w, true));
local depot_desc = null;
foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) if (d.get_waytype() == wt_rail) { depot_desc = d; break; }
s += r("depot " + depot_desc.get_name(), command_x.build_depot(pl, coord3d(100, 40, 0), depot_desc));
local st = null;
foreach (d in building_desc_x.get_available_stations(building_desc_x.station, wt_rail, good_desc_x.passenger)) { st = d; break; }
s += r("st1 " + st.get_name(), command_x.build_station(pl, coord3d(103, 40, 0), st));
s += r("st2", command_x.build_station(pl, coord3d(112, 46, 0), st));
local depot = depot_x(100, 40, 0);
local loco = null;
foreach (v in vehicle_desc_x.get_available_vehicles(wt_rail)) if (v.get_power() > 0 && v.can_be_first() && v.can_be_last()) { loco = v; break; }
s += "loco=" + loco.get_name() + "\n";
depot.append_vehicle(pl, convoy_x(0), loco);
local cnv = depot.get_convoy_list()[0];
local sched = schedule_x(wt_rail, [schedule_entry_x(coord3d(103, 40, 0), 0, 0), schedule_entry_x(coord3d(112, 46, 0), 0, 0)]);
cnv.change_schedule(pl, sched);
depot.start_convoy(pl, cnv);
gui.close_all_windows();
return s;
