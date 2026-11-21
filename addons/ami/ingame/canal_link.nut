// 運河と歩道（どちらも waytype が water）がつながるか、船が歩道に入るかを見る（#114、ADR 0008 の未確認点）。ingame/canal.sh の NUT で流す。
// 運河は CANAL（既定は pak128 の canal_020。AMI の運河ができたら ami_canal）、歩道は ami_sidewalk。区画（原点 OX・OY から）:
//   A（y +2・+3）: 東西の歩道と運河を隣の列に並べる
//   B（y +6〜+9）: 東西の歩道に、南から運河を突き当てる（運河の端が歩道のタイル）
//   C（y +12〜+15）: 東西の運河に、南から歩道を突き当てる（歩道の端が運河のタイル）
//   D（x +14、y +1〜+14）: 運河・歩道・運河を南北に一続きに敷き、北の端の車庫から出した船を南の端へ向かわせる（歩道を通れるか）
//   E（x +18、y +1〜+14）: D と同じで、歩道の代わりに運河（比べる組）
// 返り値: [link] の行（タイルの way の名前と向き）と、船の名前
local OX = 20;
local OY = 20;
local CANAL = "canal_020";
local pl = player_x(0);
local report = "";
function r(name, v) { if (v != null) report += name + "=[" + v + "]\n"; }
function c(x, y, z = 0) { return coord3d(OX + x, OY + y, z); }
local CW = way_desc_x(CANAL);
local SW = way_desc_x("ami_sidewalk");
function way(tag, w, a, b) { r(tag, command_x.build_way(pl, a, b, w, true)); }
function look(tag, x, y) {
  local t = tile_x(OX + x, OY + y, 0);
  local w = t.get_way(wt_water);
  report += "[link] " + tag + " (" + x + "," + y + ") " + (w == null ? "-" : w.get_desc().get_name() + "/d" + w.get_dirs()) + " ways=" + (t.has_two_ways() ? 2 : (w == null ? 0 : 1)) + "\n";
}

// A
way("A side", SW, c(2, 2), c(10, 2));
way("A canal", CW, c(2, 3), c(10, 3));
look("A side", 6, 2); look("A canal", 6, 3);
// B
way("B side", SW, c(2, 6), c(10, 6));
way("B canal", CW, c(6, 9), c(6, 6));
look("B end", 6, 6); look("B sideW", 5, 6); look("B sideE", 7, 6); look("B canal", 6, 7);
// C
way("C canal", CW, c(2, 12), c(10, 12));
way("C side", SW, c(6, 15), c(6, 12));
look("C end", 6, 12); look("C canalW", 5, 12); look("C side", 6, 13);
// D・E
way("D canalN", CW, c(14, 1), c(14, 5));
way("D side", SW, c(14, 5), c(14, 9));
way("D canalS", CW, c(14, 9), c(14, 14));
foreach (y in [5, 6, 9]) look("D", 14, y);
way("E canal", CW, c(18, 1), c(18, 14));

local depot = null;
foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) if (d.get_waytype() == wt_water && depot == null) depot = d;
local ship = null;
foreach (e in vehicle_desc_x.get_available_vehicles(wt_water)) if (ship == null && e.can_be_first() && e.can_be_last()) ship = e;
if (depot == null || ship == null) return report + "no ship depot or ship\n";
foreach (x in [14, 18]) {
  r("depot" + x, command_x.build_depot(pl, c(x, 1), depot));
  local d = depot_x(OX + x, OY + 1, 0);
  d.append_vehicle(pl, convoy_x(0), ship);
  local list = d.get_convoy_list();
  local cnv = list[list.len() - 1];
  cnv.change_schedule(pl, schedule_x(wt_water, [schedule_entry_x(c(x, 14), 0, 0), schedule_entry_x(c(x, 2), 0, 0)]));
  r("start" + x, d.start_convoy(pl, cnv));
}
report += "[v] " + ship.get_name() + " depot " + depot.get_name() + "\n";
gui.close_all_windows();
return report;
