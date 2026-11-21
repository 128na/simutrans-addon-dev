// 交差点の路面表示（#156）の確かめ。路面軌道の way（tram_track・system_type=0。iss の util/road_misc と同じ作り）を道路に重ねたときの
// 車の速さ・路面電車と汽車が走れるか・AMI の路面軌道と線路とのつながりを見る。ingame/marking.sh で流し、速さは SPEED=1 で読む。
// 重ねる way は MARK（既定は ami_mark_stop。速さ 1）。作る前は、ami_tram の dat の名前と速さ（10）だけを変えた試しの way を
// ゲームの写しにだけ入れて確かめた（#156 のコメント）。区画は見本（marking_sample.nut）と重ならないよう、OY を 40 にしてある。
// 区画（原点 OX・OY から）:
//   A（y +2）: 東西の一般道路 (0,2)-(30,2)。(12,2)-(16,2) に MARK を重ねる。西の端の車庫から出した車を東の端へ向かわせる（速さは marking.sh の外で読む）
//   B（y +6）: AMI の路面軌道 (0,6)-(10,6) の東の端から MARK を (16,6) まで延ばす。架線を張り、西の端の車庫から出した路面電車を (15,6) へ向かわせる
//   R（y +9）: AMI の線路 (0,9)-(10,9) の東の端から MARK を (16,9) まで延ばす。西の端の車庫から出した汽車を (15,9) へ向かわせる
//   X（y +12）: 道路の十字 (20,12) の上を、東西に MARK (18,12)-(22,12) で横切る
//   L（x +28）: 南北の線路 (28,6)-(28,10) を、東西の MARK (26,8)-(30,8) で横切る
//   T（y +14）: 東西の MARK (2,14)-(6,14) の行き止まりへ、南から AMI の路面軌道 (4,17)-(4,14) を突き当てる
// 返り値: 失敗した所、[link] の行（タイルの way の名前と向き）、[v] の行（走らせた車両）
local OX = 20;
local OY = 40;
local MARK = "ami_mark_stop";
local pl = player_x(0);
local report = "";
function r(name, v) { if (v != null) report += name + "=[" + v + "]\n"; }
function c(x, y, z = 0) { return coord3d(OX + x, OY + y, z); }
local MW = way_desc_x(MARK);
local ROAD = way_desc_x("ami_road_general");
local TRAM = way_desc_x("ami_tram");
local RAIL = way_desc_x("ami_rail_ballast");
function way(tag, w, a, b) { r(tag, command_x.build_way(pl, a, b, w, true)); }
function look(tag, x, y) {
  local t = tile_x(OX + x, OY + y, 0);
  local s = "[link] " + tag + " (" + x + "," + y + ")";
  foreach (wt in [wt_road, wt_rail, wt_tram]) {
    local w = t.get_way(wt);
    if (w != null) s += " " + w.get_desc().get_name() + "/d" + w.get_dirs();
  }
  report += s + " two_ways=" + (t.has_two_ways() ? 1 : 0) +"\n";
}
function depot_of(name) {
  foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) if (d.get_name() == name) return d;
  return null;
}
// 路面電車は電気のものしか単独で走れないので、電気の車両も選ぶ（架線 CAT を張る）。汽車は架線の無い線路なので電気でないもの
local CAT = wayobj_desc_x("tramway_classic");
function pick(wt) {
  local best = null;
  foreach (e in vehicle_desc_x.get_available_vehicles(wt))
    if (e.can_be_first() && e.can_be_last() && e.get_power() > 0 && (wt == wt_tram || !e.needs_electrification())
        && (best == null || e.get_topspeed() > best.get_topspeed())) best = e;
  return best;
}
function run(tag, dx, dy, depot, wt, vwt, to) {
  local v = pick(vwt);
  if (v == null) { report += "no vehicle for " + tag + "\n"; return; }
  r(tag + " depot", command_x.build_depot(pl, c(dx, dy), depot_of(depot)));
  local d = depot_x(OX + dx, OY + dy, 0);
  d.append_vehicle(pl, convoy_x(0), v);
  local list = d.get_convoy_list();
  local cnv = list[list.len() - 1];
  cnv.change_schedule(pl, schedule_x(wt, [schedule_entry_x(to, 0, 0), schedule_entry_x(c(dx + 2, dy), 0, 0)]));
  r(tag + " start", d.start_convoy(pl, cnv));
  report += "[v] " + tag + " " + v.get_name() + " " + v.get_topspeed() + "km/h\n";
}

// A
way("A road", ROAD, c(0, 2), c(30, 2));
way("A mark", MW, c(12, 2), c(16, 2));
look("A", 14, 2);
// B
way("B tram", TRAM, c(0, 6), c(10, 6));
way("B mark", MW, c(10, 6), c(16, 6));
r("B cat", command_x.build_wayobj(pl, c(0, 6), c(16, 6), CAT));
look("B joint", 10, 6); look("B", 12, 6);
// R
way("R rail", RAIL, c(0, 9), c(10, 9));
way("R mark", MW, c(10, 9), c(16, 9));
look("R joint", 10, 9); look("R", 12, 9);
// X
way("X roadEW", ROAD, c(16, 12), c(24, 12));
way("X roadNS", ROAD, c(20, 8), c(20, 16));
way("X mark", MW, c(18, 12), c(22, 12));
look("X cross", 20, 12); look("X", 19, 12);
// L
way("L rail", RAIL, c(28, 6), c(28, 10));
way("L mark", MW, c(26, 8), c(30, 8));
look("L cross", 28, 8); look("L railN", 28, 7);
// T
way("T mark", MW, c(2, 14), c(6, 14));
way("T tram", TRAM, c(4, 17), c(4, 14));
look("T joint", 4, 14); look("T markW", 3, 14);

run("A car", 0, 2, "ami_road_depot", wt_road, wt_road, c(29, 2));
run("B tram", 0, 6, "ami_tram_depot", wt_tram, wt_tram, c(15, 6));
run("R train", 0, 9, "ami_rail_depot", wt_rail, wt_rail, c(15, 9));
gui.close_all_windows();
return report;
