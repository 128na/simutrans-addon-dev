// 水路の踏切（跳ね橋）の見本（#117）。ingame/canal_crossing.sh がゲームの写しを起動して流す。
// 区画（原点 OX・OY から）:
//   H（y +0〜+8）: 東西の運河 (1,4)-(58,4)。k 番目の線路・道路（WAYS）が x = 5 + 6k で南北 (x,0)-(x,8) に横切る（[ns] の絵）。
//                  x = 47・53 は pak128 の線路・道路（MIXED。どの踏切が選ばれるかを見る）
//   V（x +1〜+11、y +12〜+50）: 南北の運河 (6,12)-(6,50)。k 番目が y = 15 + 5k で東西 (1,y)-(11,y) に横切る（[ew] の絵）
//   W（x +16〜+24、y +12〜+18）: 歩道 (20,12)-(20,18) を一般道路 (16,15)-(24,15) が横切る（歩道も water なので、水路の踏切が選ばれる）
// 乗り物: 運河の端に船の車庫を建て、船 1 隻を運河の両端の間で往復させる（H・V に 1 隻ずつ）。
//         線路・道路は北（V は西）の端に車庫を建て、車両 1 編成を両端の間で往復させる（電化の要らない、いちばん遅いもの）
// 降雪側（x=256〜）に敷くときは canal_crossing.sh が OX に 256 を足し、敷いた後に一帯を降雪に塗る。
// 返り値: 失敗した所、[check] の行（踏切のタイルごとの way の名前・踏切か・速さ）、[v] の行（車両）
local OX = 20;
local OY = 20;
local pl = player_x(0);
local report = "";
local WAYS = ["ami_rail_ballast", "ami_rail_concrete", "ami_rail_ladder", "ami_rail_slab",
              "ami_road_local", "ami_road_general", "ami_road_expressway"];
local MIXED = [[47, "Rail_160_Tracks"], [53, "Road_050"]];
local DEPOTS = {track = "ami_rail_depot", road = "ami_road_depot"};
function r(name, v) { if (v != null) report += name + "=[" + v + "]\n"; }
function c(x, y, z = 0) { return coord3d(OX + x, OY + y, z); }
local CANAL = way_desc_x("ami_canal");
function way(tag, a, b, desc) { r(tag, command_x.build_way(pl, a, b, desc, true)); }
local depots = {};
foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) depots[d.get_name()] <- d;
local vehicles = {};
foreach (wt in [wt_rail, wt_road, wt_water]) {
  local veh = null;
  foreach (e in vehicle_desc_x.get_available_vehicles(wt))
    if (e.can_be_first() && e.can_be_last() && !e.needs_electrification() && (e.get_power() > 0 || wt == wt_road)
        && (veh == null || e.get_topspeed() < veh.get_topspeed())) veh = e;
  vehicles[wt] <- veh;
}

// 踏切のタイルの way の名前・踏切か・最高速度（crossing_sample.nut の state と同じ見方）。
// speed= は「運河の速さ/運河の最高速度 相手の速さ/相手の最高速度」。踏切の速さが way より遅いと get_max_speed が下がる（capped）
function state(x, y) {
  local t = square_x(x, y).get_ground_tile();
  local w = t.get_way(wt_water), o = t.get_way(wt_rail);
  if (o == null) o = t.get_way(wt_road);
  if (w == null || o == null) return "missing water=" + (w != null) + " other=" + (o != null);
  local wd = w.get_desc(), od = o.get_desc();
  local same = w.get_max_speed() == wd.get_topspeed() && o.get_max_speed() == od.get_topspeed();
  return wd.get_name() + " x " + od.get_name() + " crossing=" + (w.is_crossing() && o.is_crossing())
    + " speed=" + w.get_max_speed() + "/" + wd.get_topspeed() + " " + o.get_max_speed() + "/" + od.get_topspeed() + (same ? " full" : " capped");
}

// 車庫を建てて 1 編成を出し、a と b の間を往復させる
function run(tag, depot_name, at, wt, a, b) {
  if (!(depot_name in depots)) { report += "no depot " + depot_name + "\n"; return; }
  local veh = vehicles[wt];
  if (veh == null) { report += "no vehicle " + tag + "\n"; return; }
  r(tag + " depot", command_x.build_depot(pl, at, depots[depot_name]));
  local d = depot_x(at.x, at.y, 0);
  d.append_vehicle(pl, convoy_x(0), veh);
  local list = d.get_convoy_list();
  local cnv = list[list.len() - 1];
  local e1 = schedule_entry_x(a, 0, 0);
  if (e1.x != a.x) { report += "schedule_entry_x is broken: the game's script/ folder is not OTRP's\n"; return; }
  cnv.change_schedule(pl, schedule_x(wt, [e1, schedule_entry_x(b, 0, 0)]));
  local started = d.start_convoy(pl, cnv);  // 出せれば true。name=[…] の行はカタログが失敗と数える（#398）
  if (started != true) r(tag + " start", started);
  report += "[v] " + tag + " " + veh.get_name() + "\n";
}

function wt_of(name) { return way_desc_x(name).get_waytype() == wt_road ? wt_road : wt_rail; }

// ---- H: 東西の運河を、南北の線路・道路が横切る
way("H canal", c(1, 4), c(58, 4), CANAL);
foreach (k, name in WAYS) {
  local x = 5 + 6 * k;
  way("H " + name, c(x, 0), c(x, 8), way_desc_x(name));
}
foreach (m in MIXED) {
  if (way_desc_x(m[1]) == null) { report += "no way " + m[1] + "\n"; continue; }
  way("H " + m[1], c(m[0], 0), c(m[0], 8), way_desc_x(m[1]));
}
// ---- V: 南北の運河を、東西の線路・道路が横切る
way("V canal", c(6, 12), c(6, 50), CANAL);
foreach (k, name in WAYS) {
  local y = 15 + 5 * k;
  way("V " + name, c(1, y), c(11, y), way_desc_x(name));
}
// ---- W: 歩道を一般道路が横切る
way("W sidewalk", c(20, 12), c(20, 18), way_desc_x("ami_sidewalk"));
way("W road", c(16, 15), c(24, 15), way_desc_x("ami_road_general"));

foreach (k, name in WAYS) {
  local x = 5 + 6 * k, y = 15 + 5 * k;
  report += "[check] H " + k + " (" + (OX + x) + "," + (OY + 4) + ") " + state(OX + x, OY + 4) + "\n";
  report += "[check] V " + k + " (" + (OX + 6) + "," + (OY + y) + ") " + state(OX + 6, OY + y) + "\n";
}
foreach (m in MIXED) report += "[check] M " + m[1] + " (" + (OX + m[0]) + "," + (OY + 4) + ") " + state(OX + m[0], OY + 4) + "\n";
report += "[check] W (" + (OX + 20) + "," + (OY + 15) + ") " + state(OX + 20, OY + 15) + "\n";

// ---- 乗り物
run("H ship", "ami_canal_depot", c(1, 4), wt_water, c(57, 4), c(2, 4));
run("V ship", "ami_canal_depot", c(6, 12), wt_water, c(6, 49), c(6, 13));
foreach (k, name in WAYS) {
  local wt = wt_of(name), dn = wt == wt_road ? DEPOTS.road : DEPOTS.track;
  local x = 5 + 6 * k, y = 15 + 5 * k;
  run("H " + name, dn, c(x, 0), wt, c(x, 8), c(x, 1));
  run("V " + name, dn, c(1, y), wt, c(11, y), c(2, y));
}
if (OX >= 256) r("climate", command_x(tool_set_climate).work(pl, c(-2, -2), c(62, 52), "7"));
gui.close_all_windows();
return report;
