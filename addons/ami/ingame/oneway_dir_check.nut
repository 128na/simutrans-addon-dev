// 一方通行の標識（ami_sign_one_way）の絵の向きと、効く車の向きを、車を走らせて確かめる（#200）。
// 検証用の左側通行のセーブ flat_512_left_v64.sve の (20,24) から、道路を 8 本敷く。各道路に標識を 1 回か 2 回置き、道の片方の端の車庫から
// もう片方の端（旅客の停留所）へバスを出す。着いた道路が「通れる」向き。
//   NS0〜NS3: 南北の道路 x=2+4i, y=0..10。標識は (x,5)。i=0 1 回・車庫が北端（南行き）、1: 1 回・南端（北行き）、2: 2 回・北端、3: 2 回・南端
//   EW0〜EW3: 東西の道路 y=14+4i, x=0..10。標識は (5,y)。i=0 1 回・車庫が西端（東行き）、1: 1 回・東端（西行き）、2: 2 回・西端、3: 2 回・東端
// 使い方: 標識の絵は、撮る前に PAK で差し替えて起動する。返り値の [veh] の行が、出した車の車庫と行き先。
local OX = 20;
local OY = 24;
local pl = player_x(0);
local s = "";
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
local c = function(x, y) { return coord3d(20 + x, 24 + y, 0); };  // squirrel の関数は外の local を読めないので、OX・OY の値を直に書く
local road = way_desc_x("ami_road_general");
local sg = null;
foreach (d in sign_desc_x.get_available_signs(wt_road)) if (d.get_name() == "ami_sign_one_way") sg = d;
local depot_desc = null;
foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) if (d.get_waytype() == wt_road) { depot_desc = d; break; }
// 道路の車は、行き先に停留所が要る（道路のタイルだけの行き先は、スケジュールを変えられない）。バス（旅客）を出し、行き先に旅客の停留所を建てる
local veh = null;
foreach (v in vehicle_desc_x.get_available_vehicles(wt_road))
  if (v.get_power() > 0 && v.can_be_first() && v.can_be_last() && v.get_freight().get_name() == "Passagiere" && (veh == null || v.get_topspeed() < veh.get_topspeed())) veh = v;
local st = null;
foreach (d in building_desc_x.get_available_stations(building_desc_x.station, wt_road, good_desc_x.passenger)) { st = d; break; }
if (road == null || sg == null || depot_desc == null || veh == null || st == null) return "missing road=" + road + " sign=" + sg + " depot=" + depot_desc + " veh=" + veh + " stop=" + st + "\n";
// 道路 i: [名前, 始点, 終点, 標識の場所, 標識を置く回数, 車庫の場所, 行き先]
local tests = [];
for (local i = 0; i < 4; i++) {
  local times = i < 2 ? 1 : 2;
  local from_start = (i % 2) == 0;
  local x = 2 + 4 * i;
  tests.append(["NS" + i, c(x, 0), c(x, 10), c(x, 5), times, from_start ? c(x, 0) : c(x, 10), from_start ? c(x, 10) : c(x, 0)]);
  local y = 14 + 4 * i;
  tests.append(["EW" + i, c(0, y), c(10, y), c(5, y), times, from_start ? c(0, y) : c(10, y), from_start ? c(10, y) : c(0, y)]);
}
foreach (t in tests) {
  s += r(t[0] + " way", command_x.build_way(pl, t[1], t[2], road, true));
  for (local k = 0; k < t[4]; k++) command_x.build_sign_at(pl, t[3], sg);
  s += r(t[0] + " depot", command_x.build_depot(pl, t[5], depot_desc));
  s += r(t[0] + " stop", command_x.build_station(pl, t[6], st));
  // 出発側にも停留所（車庫の隣の 1 マス先）。スケジュールは 2 つ以上の停車が要る
  local near = coord3d(t[5].x + (t[6].x > t[5].x ? 1 : (t[6].x < t[5].x ? -1 : 0)), t[5].y + (t[6].y > t[5].y ? 1 : (t[6].y < t[5].y ? -1 : 0)), 0);
  s += r(t[0] + " stop0", command_x.build_station(pl, near, st));
  local dp = t[5];
  local depot = depot_x(dp.x, dp.y, 0);
  depot.append_vehicle(pl, convoy_x(0), veh);
  local list = depot.get_convoy_list();
  local cnv = list[list.len() - 1];
  cnv.change_schedule(pl, schedule_x(wt_road, [schedule_entry_x(t[6], 0, 0), schedule_entry_x(near, 0, 0)]));
  depot.start_convoy(pl, cnv);
  local o = square_x(t[3].x, t[3].y).get_ground_tile().find_object(mo_roadsign);
  local w = square_x(t[3].x, t[3].y).get_ground_tile().get_way(wt_road);
  s += "[veh] " + t[0] + " depot=" + dp.x + "," + dp.y + " goal=" + t[6].x + "," + t[6].y + " masked=" + (w == null ? "-" : w.get_dirs_masked()) + " sign=" + (o == null ? "-" : o.get_desc().get_name()) + "\n";
}
gui.close_all_windows();
return s + "veh=" + veh.get_name() + " " + veh.get_topspeed() + "km/h\n";
