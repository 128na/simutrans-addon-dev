// 跨座式モノレールの見本（#113）。ingame/monorail.sh がゲームの写しを起動して流す。
// 区画（原点 OX・OY から）:
//   G（y +0〜+9）: 地上の版。車庫（道が東へ出る）と、角 4 つの輪（車庫の口が T字）・斜め・行き止まり・十字。車両は輪を回る
//   E（y +12 から 10 ずつ、版ごと）: 高架の front・center・back。直線（南北・東西）・L 字の角・T字・斜め・行き止まり
//   P（y +42〜）: 複線。南北は西の線を back・東の線を front、東西は北の線を back・南の線を front（柱が外側に立つ組）
//   T（y +50）: トンネル（東西）。丘の両側に地上の版をつなぐ
// 車両は、電化の要らない monorail の車両（ユーザーが渡した玉野の編成。無ければ 1 両で走れる物）を輪で回す。
// 降雪側（x=256〜）に敷くときは monorail.sh が OX に 256 を足し、敷いた後に一帯を降雪に塗る。
// 返り値: 先頭が ok なら全部敷けた。違えば先頭が check で「名前=[…]」が続く。最後に車両の名前（[v] の行）
// 使い方: monorail.sh か、sample_parallel.sh に NUT=ingame/monorail.nut（撮る場所は sample_spots.sh の MONORAIL_SPOTS）
local OX = 20;
local OY = 20;
local pl = player_x(0);
local report = "";
local info = "";
function r(name, v) { if (v != null) report += name + "=[" + v + "]\n"; }
function c(x, y, z = 0) { return coord3d(OX + x, OY + y, z); }
local G = way_desc_x("ami_monorail_straddle");
local TN = "ami_monorail_straddle_tunnel";
function way(tag, w, a, b) { r(tag, command_x.build_way(pl, a, b, w, true)); }

// ---- G: 地上
// 車庫の口の道と十字を先に敷く（スクリプトの build_way は置き換えるので、後から敷くと輪の角のつながりが消える）
way("G depot", G, c(1, 2), c(3, 2));
way("G cross", G, c(7, 0), c(7, 4));  // 輪の北の辺を横切る十字（北は行き止まり）
way("G loopN", G, c(3, 2), c(12, 2));
way("G loopE", G, c(12, 2), c(12, 8));
way("G loopS", G, c(12, 8), c(3, 8));
way("G loopW", G, c(3, 8), c(3, 2));
way("G diag", G, c(16, 2), c(22, 8));
way("G dead", G, c(25, 2), c(25, 6));
local depot = null;
foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) if (d.get_name() == "ami_monorail_depot") depot = d;
if (depot == null) return "check\n" + report + "no ami_monorail_depot\n";
r("G depot", command_x.build_depot(pl, c(1, 2), depot));

// ---- E: 高架の 3 版
local VARIANTS = ["front", "center", "back"];
foreach (i, v in VARIANTS) {
  local e = way_desc_x("ami_monorail_straddle_elev_" + v), y = 12 + i * 10;
  way("E " + v + " ns", e, c(2, y), c(2, y + 6));
  way("E " + v + " ew", e, c(4, y + 3), c(12, y + 3));
  way("E " + v + " L1", e, c(14, y), c(20, y));
  way("E " + v + " L2", e, c(20, y), c(20, y + 6));
  way("E " + v + " T", e, c(17, y), c(17, y + 4));
  way("E " + v + " diag", e, c(24, y), c(30, y + 6));
}

// ---- P: 複線（柱が外側）
local eb = way_desc_x("ami_monorail_straddle_elev_back"), ef = way_desc_x("ami_monorail_straddle_elev_front");
way("P ns back", eb, c(2, 42), c(2, 48));
way("P ns front", ef, c(3, 42), c(3, 48));
way("P ew back", eb, c(6, 44), c(14, 44));
way("P ew front", ef, c(6, 45), c(14, 45));

// ---- T: トンネル（東西。丘は x 3〜5 を 2 段上げる）
local ty = 52;
function set_slope_kept(p, s) { return command_x.set_slope(pl, p, s); }
for (local x = 3; x <= 5; x++) for (local k = 0; k < 2; k++) r("T raise", set_slope_kept(c(x, ty, k), slope.all_up_slope));
r("T rampW", set_slope_kept(c(2, ty), 24));
r("T rampE", set_slope_kept(c(6, ty), 56));
r("T tunnel", command_x(tool_build_tunnel).work(pl, c(2, ty), TN));
way("T wayW", G, c(0, ty), c(2, ty));
way("T wayE", G, c(6, ty), c(8, ty));

// ---- 車両（地上の輪）
local avail = {};
foreach (e in vehicle_desc_x.get_available_vehicles(wt_monorail)) avail[e.get_name()] <- e;
local set = [];
foreach (n in ["TTM1100", "TTM1200", "TTM1300", "TTM1400"]) if (n in avail) set.append(avail[n]);
if (set.len() < 4) {
  set = [];
  foreach (n, e in avail) if (e.can_be_first() && e.can_be_last() && !e.needs_electrification()) { set = [e]; break; }
}
if (set.len() == 0) {
  info += "no monorail vehicle:";
  foreach (n, e in avail) info += " " + n + (e.needs_electrification() ? "(e)" : "");
  info += "\n";
} else {
  local d = depot_x(OX + 1, OY + 2, 0);
  d.append_vehicle(pl, convoy_x(0), set[0]);  // convoy_x(0) は新しい編成。2 両目からはその編成に足す
  local list = d.get_convoy_list();
  local cnv = list[list.len() - 1];
  for (local k = 1; k < set.len(); k++) d.append_vehicle(pl, cnv, set[k]);
  cnv.change_schedule(pl, schedule_x(wt_monorail, [schedule_entry_x(c(12, 8), 0, 0), schedule_entry_x(c(3, 8), 0, 0)]));
  local started = d.start_convoy(pl, cnv);
  if (started != true) r("start", started);
  foreach (e in set) info += "[v] " + e.get_name() + "\n";
}
if (OX >= 256) r("climate", command_x(tool_set_climate).work(pl, c(-2, -2), c(34, 56), "7"));
gui.close_all_windows();
return (report == "" ? "ok\n" : "check\n" + report) + info;
