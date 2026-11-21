// 車庫の見本（#112）。ingame/depot.sh がゲームの写しを起動して流す。
// 組（南へ ROW_DY ずつ）: 車庫の組（ROWS）。AMI の車庫と、比べる pak128 の車庫を、同じ AMI の way の上に建てる。
// 組の中: 道の出る向き 南・東・北・西（layout 0〜3。simtool.cc の tool_depot_aux）の 4 つを、画面 1 枚に入るよう 2×2 に置く（POS）。
//   道は車庫から出る向きへ STUB タイル延ばす（車庫のタイルは行き止まり）。
// 最後の行（VEH）は、道が南と東へ出る車庫に車両を 1 編成ずつ入れておく（出すのは depot.sh の CAPTURE=1 VEH=1。手前の絵が車両の上に描かれるのを見る）。
// 降雪側（x=256〜）に敷くときは depot.sh が OX に 256 を足し、敷いた後に一帯を降雪に塗る。
// 返り値: 失敗した所と、建てた車庫の名前・layout（[d] の行）
local OX = 20;
local OY = 20;
local ROW_DY = 12;
local DIR_DX = 8;  // 車両の行の間隔
local STUB = 2;
local pl = player_x(0);
local report = "";
function r(name, v) { if (v != null) report += name + "=[" + v + "]\n"; }
function c(x, y) { return coord3d(x, y, 0); }

local DIRS = [[0, 1], [1, 0], [0, -1], [-1, 0]];  // 南・東・北・西（道の出る向き）
local POS = [[2, 2], [6, 6], [6, 2], [2, 6]];  // 向きごとの車庫の位置（組の左上から）。道が隣の車庫に当たらない並び
local ROWS = [
  {name = "ami_rail", way = "ami_rail_ballast", depot = "ami_rail_depot"},
  {name = "pak_rail", way = "ami_rail_ballast", depot = "TrainDepot"},
  {name = "ami_tram", way = "ami_tram", depot = "ami_tram_depot"},
  {name = "pak_tram", way = "ami_tram", depot = "TramDepot"},
  {name = "ami_road", way = "ami_road_general", depot = "ami_road_depot"},
  {name = "pak_road", way = "ami_road_general", depot = "CarDepot"},
  // 壁つきの架線の版の上（電化した車両はこの上でしか走れない）。way-object を車庫のタイルまで敷いてから建てる
  {name = "ami_cat", way = "ami_rail_ballast_base_single", depot = "ami_rail_depot", wo = "ami_wall_rail_single_catenary"},
  // 壁の版の上（壁だけ）
  {name = "ami_wall", way = "ami_rail_ballast_base_single", depot = "ami_rail_depot", wo = "ami_wall_rail_single"},
];
local depots = {};
foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) depots[d.get_name()] <- d;

foreach (ri, row in ROWS) {
  local y0 = OY + ri * ROW_DY;
  foreach (di, dir in DIRS) {
    local p = c(OX + POS[di][0], y0 + POS[di][1]), q = c(p.x + dir[0] * STUB, p.y + dir[1] * STUB);
    r(row.name + " way " + di, command_x.build_way(pl, p, q, way_desc_x(row.way), true));
    if ("wo" in row) r(row.name + " wo " + di, command_x.build_wayobj(pl, p, q, wayobj_desc_x(row.wo)));
    if (!(row.depot in depots)) { report += "no depot " + row.depot + "\n"; continue; }
    r(row.name + " depot " + di, command_x.build_depot(pl, p, depots[row.depot]));
    report += "[d] " + row.name + " " + di + " (" + p.x + "," + p.y + ")\n";
  }
}

// 車両: 道が南（layout 0）と東（layout 1）へ出る AMI の車庫に、それぞれ 1 編成（電化の要らない、いちばん遅い車両。見本の道に架線は無い）。道は 8 タイル延ばし、出したら端と車庫の前を往復させる
local VEH = [
  {name = "rail", way = "ami_rail_ballast", depot = "ami_rail_depot", wt = wt_rail},
  {name = "tram", way = "ami_tram", depot = "ami_tram_depot", wt = wt_tram},
  {name = "road", way = "ami_road_general", depot = "ami_road_depot", wt = wt_road},
];
local vy = OY + ROWS.len() * ROW_DY;
foreach (vi, v in VEH) {
  local veh = null;
  foreach (e in vehicle_desc_x.get_available_vehicles(v.wt))
    if (e.can_be_first() && e.can_be_last() && !e.needs_electrification() && (e.get_power() > 0 || v.wt == wt_road) && (veh == null || e.get_topspeed() < veh.get_topspeed())) veh = e;
  if (veh == null) { report += "no vehicle " + v.name + "\n"; continue; }
  foreach (di in [0, 1]) {
    local dir = DIRS[di];
    local x0 = OX + (vi * 2 + di) * DIR_DX * 2;
    local p = c(x0 + 3, vy + 3), q = c(x0 + 3 + dir[0] * 8, vy + 3 + dir[1] * 8);
    r("veh way " + v.name + di, command_x.build_way(pl, p, q, way_desc_x(v.way), true));
    r("veh depot " + v.name + di, command_x.build_depot(pl, p, depots[v.depot]));
    local depot = depot_x(p.x, p.y, 0);
    depot.append_vehicle(pl, convoy_x(0), veh);
    local list = depot.get_convoy_list();
    local cnv = list[list.len() - 1];
    local e1 = schedule_entry_x(q, 0, 0);
    if (e1.x != q.x) return report + "schedule_entry_x is broken: the game's script/ folder is not OTRP's\n";
    local back = c(p.x + dir[0], p.y + dir[1]);
    cnv.change_schedule(pl, schedule_x(v.wt, [e1, schedule_entry_x(back, 0, 0)]));
    report += "[v] " + v.name + " " + di + " (" + p.x + "," + p.y + ") " + veh.get_name() + "\n";
  }
}
if (OX >= 256) r("climate", command_x(tool_set_climate).work(pl, c(OX - 2, OY - 2), c(OX + 6 * DIR_DX * 2, vy + 14), "7"));
gui.close_all_windows();
return report;
