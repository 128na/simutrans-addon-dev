// 狭軌の見本（#370）。ingame/narrow.sh がゲームの写しを起動して流す。
// 区画（原点 OX・OY から。30 の木のまくらぎ ami_narrow_wood は y +0〜、60 の砕石 ami_narrow_ballast は y +14〜）:
//   輪（角 4 つ。北の辺に車庫の口の T字と、輪を横切る十字）・斜め・行き止まり・坂（1 段の丘を東西に越える）
//   60 だけ: トンネル（東西。丘の両側に地上の版をつなぐ）
//   比べ（y +10〜12）: 30・60・在来線を平行に並べる（撮る所は narrow.sh の compare。ZOOM=1 で寄せる）
// 車両は、輪の車庫（60 の輪）から、狭軌の車両（1 両で走れる物）を回す。無ければ返り値に「no narrowgauge vehicle」と出す。
// 降雪側（x=256〜）に敷くときは narrow.sh が OX に 256 を足し、敷いた後に一帯を降雪に塗る。
// 返り値: 失敗した所と、車両の名前（[v] の行）
local OX = 20;
local OY = 20;
local pl = player_x(0);
local report = "";
function r(name, v) { if (v != null) report += name + "=[" + v + "]\n"; }
function c(x, y, z = 0) { return coord3d(OX + x, OY + y, z); }
function way(tag, w, a, b) { r(tag, command_x.build_way(pl, a, b, w, true)); }
function set_slope_kept(p, s) { return command_x.set_slope(pl, p, s); }

local TYPES = [["ami_narrow_wood", 0], ["ami_narrow_ballast", 14]];
foreach (t in TYPES) {
  local w = way_desc_x(t[0]), y0 = t[1], tag = t[0].slice(11);
  // 車庫の口の道と十字を先に敷く（build_way は置き換えるので、後から敷くと輪の角のつながりが消える）
  way(tag + " depot", w, c(1, y0 + 2), c(3, y0 + 2));
  way(tag + " cross", w, c(7, y0 + 0), c(7, y0 + 4));  // 輪の北の辺を横切る十字（北は行き止まり）
  way(tag + " loopN", w, c(3, y0 + 2), c(12, y0 + 2));
  way(tag + " loopE", w, c(12, y0 + 2), c(12, y0 + 8));
  way(tag + " loopS", w, c(12, y0 + 8), c(3, y0 + 8));
  way(tag + " loopW", w, c(3, y0 + 8), c(3, y0 + 2));
  way(tag + " diag", w, c(16, y0 + 2), c(22, y0 + 8));
  way(tag + " dead", w, c(25, y0 + 2), c(25, y0 + 6));
  // 坂: x 30〜32 を 1 段上げた丘を、東西の線で越える
  local sy = y0 + 4;
  for (local x = 30; x <= 32; x++) r(tag + " raise", set_slope_kept(c(x, sy), slope.all_up_slope));
  r(tag + " rampW", set_slope_kept(c(29, sy), 12));  // 東の 2 つの角が 1 段上（sw 1・se 3・ne 9・nw 27 の和）
  r(tag + " rampE", set_slope_kept(c(33, sy), 28));  // 西の 2 つの角が 1 段上
  way(tag + " slope", w, c(27, sy), c(35, sy));
}

// ---- 60 のトンネル（東西。丘は x 41〜43 を 2 段上げる）
local ty = 14 + 4, G = way_desc_x("ami_narrow_ballast");
for (local x = 41; x <= 43; x++) for (local k = 0; k < 2; k++) r("T raise", set_slope_kept(c(x, ty, k), slope.all_up_slope));
r("T rampW", set_slope_kept(c(40, ty), 24));
r("T rampE", set_slope_kept(c(44, ty), 56));
r("T tunnel", command_x(tool_build_tunnel).work(pl, c(40, ty), "ami_narrow_ballast_tunnel"));
way("T wayW", G, c(38, ty), c(40, ty));
way("T wayE", G, c(44, ty), c(46, ty));

// ---- 比べ: 30・60・在来線（ami_rail_ballast）を東西に平行に（y +10〜12）、南北に平行に（x +14〜16）並べる
local CMP = ["ami_narrow_wood", "ami_narrow_ballast", "ami_rail_ballast"];
for (local i = 0; i < 3; i++) {
  local w = way_desc_x(CMP[i]);
  way("cmp ew " + CMP[i], w, c(3, 10 + i), c(10, 10 + i));
  way("cmp ns " + CMP[i], w, c(14 + i, 7), c(14 + i, 13));
}

// ---- 車庫（30・60 の輪の口）
local depot = null;
foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) if (d.get_name() == "ami_narrow_depot") depot = d;
if (depot == null) return report + "no ami_narrow_depot\n";
foreach (t in TYPES) r(t[0] + " depot", command_x.build_depot(pl, c(1, t[1] + 2), depot));

// ---- 車両（両方の輪で、1 両ずつ）
local set = null;
foreach (e in vehicle_desc_x.get_available_vehicles(wt_narrowgauge))
  if (set == null && e.can_be_first() && e.can_be_last() && !e.needs_electrification()) set = e;
if (set == null) {
  report += "no narrowgauge vehicle\n";
} else {
  foreach (t in TYPES) {
    local d = depot_x(OX + 1, OY + t[1] + 2, 0);
    d.append_vehicle(pl, convoy_x(0), set);
    local list = d.get_convoy_list();
    local cnv = list[list.len() - 1];
    cnv.change_schedule(pl, schedule_x(wt_narrowgauge, [schedule_entry_x(c(12, t[1] + 8), 0, 0), schedule_entry_x(c(3, t[1] + 8), 0, 0)]));
    r(t[0] + " start", d.start_convoy(pl, cnv));
  }
  report += "[v] " + set.get_name() + "\n";
}
if (OX >= 256) r("climate", command_x(tool_set_climate).work(pl, c(-2, -2), c(48, 26), "7"));
gui.close_all_windows();
return report;
