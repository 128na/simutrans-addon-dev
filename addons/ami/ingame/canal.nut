// 運河と船の車庫の見本（#114）。ingame/canal.sh がゲームの写しを起動して流す。
// 区画（原点 OX・OY から）:
//   G（y +0〜+9）: 車庫（運河が東へ出る）と、角 4 つの輪（車庫の口が T字）・十字（北は行き止まり）・斜め・行き止まり。船は輪を回る
//   S（y +12〜+18）: 坂（丘を 1 段と 2 段上げ、南北・東西に運河を通す）
//   C（x +16〜、y +12〜+18）: 近い斜め（1 タイルずらして並べた斜め 2 本。分け合うタイルが十字）
// 降雪側（x=256〜）に敷くときは canal.sh が OX に 256 を足し、敷いた後に一帯を降雪に塗る。
// 返り値: 失敗した所と、船の名前（[v] の行）・確かめの行（[check]）
local OX = 20;
local OY = 20;
local pl = player_x(0);
local report = "";
function r(name, v) { if (v != null) report += name + "=[" + v + "]\n"; }
function c(x, y, z = 0) { return coord3d(OX + x, OY + y, z); }
local W = way_desc_x("ami_canal");
function way(tag, a, b) { r(tag, command_x.build_way(pl, a, b, W, true)); }
function set_slope_kept(p, s) { return command_x.set_slope(pl, p, s); }

// ---- G: 地上（車庫の口の運河と十字を先に敷く。スクリプトの build_way は置き換えるので、後から敷くと輪の角のつながりが消える）
way("G depot", c(1, 2), c(3, 2));
way("G cross", c(7, 0), c(7, 4));
way("G loopN", c(3, 2), c(12, 2));
way("G loopE", c(12, 2), c(12, 8));
way("G loopS", c(12, 8), c(3, 8));
way("G loopW", c(3, 8), c(3, 2));
way("G diag", c(16, 2), c(22, 8));
way("G dead", c(25, 2), c(25, 6));

// ---- S: 坂（丘の中心 (cx, cy) を n 段上げ、四方を坂にする）
foreach (h in [[3, 15, 1], [12, 15, 2]]) {
  local cx = h[0], cy = h[1], n = h[2];
  for (local k = 0; k < n; k++) r("S raise", set_slope_kept(c(cx, cy, k), slope.all_up_slope));
  r("S rampN", set_slope_kept(c(cx, cy - 1), 4 * n));
  r("S rampS", set_slope_kept(c(cx, cy + 1), 36 * n));
  r("S rampW", set_slope_kept(c(cx - 1, cy), 12 * n));
  r("S rampE", set_slope_kept(c(cx + 1, cy), 28 * n));
  way("S ns", c(cx, cy - 3), c(cx, cy + 3));
  way("S ew", c(cx - 3, cy), c(cx + 3, cy));
}

// ---- C: 近い斜め（南東へ下る斜めを 2 本、1 タイルずらして敷く。分け合うタイルは 4 方向につながり、近い斜めの絵になる）
way("C diagA", c(16, 12), c(22, 18));
way("C diagB", c(17, 12), c(23, 18));
foreach (p in [[17, 12], [18, 13], [19, 14]]) {
  local t = square_x(OX + p[0], OY + p[1]).get_ground_tile();
  local w = t.get_way(wt_water);
  report += "[check] close (" + p[0] + "," + p[1] + ") " + (w == null ? "-" : "d" + w.get_dirs()) + " two_ways=" + t.has_two_ways() + "\n";
}

// ---- 車庫と船
local depot = null;
foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) if (d.get_name() == "ami_canal_depot") depot = d;
if (depot == null) return report + "no ami_canal_depot\n";
r("G depot", command_x.build_depot(pl, c(1, 2), depot));
local ship = null;
foreach (e in vehicle_desc_x.get_available_vehicles(wt_water)) if (ship == null && e.can_be_first() && e.can_be_last()) ship = e;
if (ship == null) {
  report += "no ship\n";
} else {
  local d = depot_x(OX + 1, OY + 2, 0);
  d.append_vehicle(pl, convoy_x(0), ship);
  local list = d.get_convoy_list();
  local cnv = list[list.len() - 1];
  cnv.change_schedule(pl, schedule_x(wt_water, [schedule_entry_x(c(12, 8), 0, 0), schedule_entry_x(c(3, 8), 0, 0)]));
  r("start", d.start_convoy(pl, cnv));
  report += "[v] " + ship.get_name() + "\n";
}
if (OX >= 256) r("climate", command_x(tool_set_climate).work(pl, c(-2, -2), c(32, 24), "7"));
gui.close_all_windows();
return report;
