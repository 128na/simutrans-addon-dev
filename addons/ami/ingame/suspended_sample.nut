// AMI の懸垂式モノレールの見本（#116）。ingame/game.sh で flat_512.sve に流す（降雪側は OX=276 を渡す。敷いた後に一帯を降雪に塗る）。
// 区画（原点 (OX,OY) から。版ごとに y を 12 ずつずらす。i は版の番号 0〜2 = front・center・back）:
//   G 地上の版（y = 12i）: 直線 南北 (2,y)-(2,y+6)・東西 (4,y+3)-(12,y+3)、L 字 (14,y)-(20,y)-(20,y+6)、T字 (17,y)-(17,y+4)、斜め (24,y)-(30,y+6)
//   E 高架の版（y = 36 + 12i）: G と同じ並び
//   P 複線（y = 72）: 地上で、南北は西の線を back・東の線を front、東西は北の線を back・南の線を front（柱が外側に立つ組）
//   S 坂（y = 80〜88）: 地上の center の南北 (2,80)-(2,88)。(·,84) を 1 段上げた坂（x1〜3）
//   V 車両（y = 92〜98）: 地上の center の輪 (3,92)-(12,92)-(12,98)-(3,98) と、西の車庫（跨座式の ami_monorail_depot、(1,92)。口の道が東へ出る）。
//     懸垂式の車両（ユーザーが渡した Higashiyama_1A。game.sh の EXTRA_PAKS で写しにだけ入れる）が輪を回る。無ければ 1 両で走れる monorail の車両
// つながりは [check] の行で、タイルの way の名前と向き（ribi）を期待と比べる。
// 返り値の先頭が ok なら全部敷けて、[check] の期待どおり。違えば先頭が check で、「名前 場所=[…]」が続く。最後に [check] の行が続く
local OX = 20;
local OY = 24;
local pl = player_x(0);
local report = "";
local checks = "";
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
function c(x, y, z = 0) { return coord3d(OX + x, OY + y, z); }
function wd(n) { local d = way_desc_x(n); if (d == null) report += n + " desc=[missing]\n"; return d; }
function way(tag, d, x0, y0, x1, y1) { report += r(tag, command_x.build_way(pl, c(x0, y0), c(x1, y1), d, true)); }
local VARIANTS = ["front", "center", "back"];
local marker = command_x(tool_set_marker);
report += r("label", marker.work(pl, c(0, -3), "suspended: G ground / E elev / P pair / S slope"));

// G・E
foreach (i, v in VARIANTS) {
  foreach (k, pre in ["ami_monorail_suspended_", "ami_monorail_suspended_elev_"]) {
    local d = wd(pre + v), y = 12 * i + 36 * k, t = (k == 0 ? "G " : "E ") + v;
    way(t + " ns", d, 2, y, 2, y + 6);
    way(t + " ew", d, 4, y + 3, 12, y + 3);
    way(t + " L1", d, 14, y, 20, y);
    way(t + " L2", d, 20, y, 20, y + 6);
    way(t + " T", d, 17, y, 17, y + 4);
    way(t + " diag", d, 24, y, 30, y + 6);
  }
}
// P
local gb = wd("ami_monorail_suspended_back"), gf = wd("ami_monorail_suspended_front"), gc = wd("ami_monorail_suspended_center");
way("P ns back", gb, 2, 72, 2, 78);
way("P ns front", gf, 3, 72, 3, 78);
way("P ew back", gb, 6, 74, 14, 74);
way("P ew front", gf, 6, 75, 14, 75);
// S
for (local x = 1; x <= 3; x++) {
  report += r("S raise", command_x.set_slope(pl, c(x, 84), slope.all_up_slope));
  report += r("S rampN", command_x.set_slope(pl, c(x, 83), 4));
  report += r("S rampS", command_x.set_slope(pl, c(x, 85), 36));
}
way("S ns", gc, 2, 80, 2, 88);
// V（車庫の口の道を先に敷く。後から敷くと輪の角のつながりが消える。monorail.nut と同じ）
way("V depot", gc, 1, 92, 3, 92);
way("V N", gc, 3, 92, 12, 92);
way("V E", gc, 12, 92, 12, 98);
way("V S", gc, 12, 98, 3, 98);
way("V W", gc, 3, 98, 3, 92);
local depot = null;
foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) if (d.get_name() == "ami_monorail_depot") depot = d;
if (depot == null) report += "ami_monorail_depot=[missing]\n";
else report += r("V depot", command_x.build_depot(pl, c(1, 92), depot));
local vset = null, vnames = "";
foreach (e in vehicle_desc_x.get_available_vehicles(wt_monorail)) {
  vnames += " " + e.get_name();
  if (e.get_name() == "Higashiyama_1A") vset = e;
}
if (vset == null) foreach (e in vehicle_desc_x.get_available_vehicles(wt_monorail)) if (vset == null && e.can_be_first() && e.can_be_last() && !e.needs_electrification()) vset = e;
if (vset == null || depot == null) report += "V vehicle=[none:" + vnames + "]\n";
else {
  local d = depot_x(OX + 1, OY + 92, 0);
  d.append_vehicle(pl, convoy_x(0), vset);
  local list = d.get_convoy_list();
  local cnv = list[list.len() - 1];
  cnv.change_schedule(pl, schedule_x(wt_monorail, [schedule_entry_x(c(12, 98), 0, 0), schedule_entry_x(c(3, 98), 0, 0)]));
  local st = d.start_convoy(pl, cnv);
  if (st != true) report += r("V start", st);
  checks += "[v] " + vset.get_name() + "\n";
}

// [check]: タイルの way の名前と向き（ribi。北 1・東 2・南 4・西 8）
function expect(tag, x, y, z, want_name, want_dirs) {
  local s = square_x(OX + x, OY + y);
  local t = z == 0 ? s.get_ground_tile() : s.get_tile_at_height(z);
  local w = t == null ? null : t.get_way(wt_monorail);
  local got = w == null ? "-" : w.get_desc().get_name() + " " + w.get_dirs();
  checks += "[check] " + tag + " (" + x + "," + y + "," + z + ")=" + got + "\n";
  local want = want_name + " " + want_dirs;
  return got == want ? "" : tag + " (" + x + "," + y + ")=[" + got + " want " + want + "]\n";
}
foreach (i, v in VARIANTS) {
  foreach (k, pre in ["ami_monorail_suspended_", "ami_monorail_suspended_elev_"]) {
    local y = 12 * i + 36 * k, z = k == 0 ? 0 : 2, t = (k == 0 ? "G " : "E ") + v, n = pre + v;
    report += expect(t + " ns", 2, y + 3, z, n, 5);
    report += expect(t + " ew", 8, y + 3, z, n, 10);
    report += expect(t + " L corner", 20, y, z, n, 12);
    report += expect(t + " T", 17, y, z, n, 14);
    report += expect(t + " diag", 26, y + 2, z, n, 3);  // 階段の途中の北・東につながるタイル
  }
}
report += expect("S top", 2, 84, 1, "ami_monorail_suspended_center", 5);
report += expect("S ramp", 2, 83, 0, "ami_monorail_suspended_center", 5);
if (OX > 200)
  report += r("climate", command_x(tool_set_climate).work(pl, c(-2, -6), c(34, 100), "7"));
gui.close_all_windows();
return (report == "" ? "ok\n" : "check\n" + report) + checks;
