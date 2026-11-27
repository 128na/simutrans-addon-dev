// リニアの見本（#371）。ingame/maglev.sh がゲームの写しを起動して流す。
// 区画（原点 OX・OY から）:
//   G（x +0〜, y +0〜+9）: 超電導の地上の single。車庫と輪（ガイドを重ねる）・斜め・行き止まり・十字（ガイドを重ねる）
//   B（x +0〜, y +12〜+21）: 常電導の地上。車庫と輪・斜め・行き止まり
//   U（x +0〜, y +24〜+33）: チューブ式の地上の single。車庫と輪・斜め・行き止まり・十字（チューブを重ねる）
//   P（x +0〜, y +36〜）: 複線（超電導の地上と高架、チューブ式の地上。南北は西を back・東を front、東西は北を back・南を front）。
//     ガイド・チューブを重ねる。y +46 に center の版（超電導・チューブ式）の直線
//   T（x +0〜, y +48〜）: トンネル（東西）。3 種を 3 本並べ、丘の両側に地上の way をつなぐ
//   EG（x +40〜, y +0 から 10 ずつ）: 超電導の高架の 4 版（真下に橋脚の way）。直線・L 字・T字・斜め・行き止まり。ガイドを重ねる
//   EB（x +80〜, y +0 から 10 ずつ）: 常電導の高架の 3 版
//   EU（x +120〜, y +0 から 10 ずつ）: チューブ式の高架の 4 版（真下に橋脚の way）。チューブを重ねる
// 車両は別のアドオンの物（maglev.sh の EXTRA_PAKS で写しにだけ入れる。コミットしない）。VEHICLES の種類ごとに、最初に見つかった
// 編成を輪で回す（電化の要る編成は G、要らない編成は B・U）。登場年より前の地図でも、名前で引いて連結する
// 返り値: 失敗した所と、[check]・[v] の行（タイルの way と way-object の名前、車両）。車両が無いとき（カタログ）は [v] の行で知らせる
// カタログ（ingame/catalog.py の REUSE）でも、原点を書き換えて流す
local OX = 20;
local OY = 20;
local SNOW = 9;  // 0 で区画を降雪に塗る（maglev.sh の SNOW=1、catalog.py の降雪側が書き換える）
local ELEV_UP = 2;
local pl = player_x(0);
local report = "";
function r(name, v) { if (v != null) report += name + "=[" + v + "]\n"; }
function c(x, y, z = 0) { return coord3d(OX + x, OY + y, z); }
function wd(n) { local d = way_desc_x(n); if (!d.is_valid()) { report += n + " desc=[missing]\n"; return null; } return d; }
local WO = {};
foreach (d in wayobj_desc_x.get_available_wayobjs(wt_maglev)) WO[d.get_name()] <- d;
function wod(n) { if (!(n in WO)) { report += n + " wayobj=[missing]\n"; return null; } return WO[n]; }
local GUIDE = wod("ami_maglev_guide"), COVER = wod("ami_maglev_tube_cover");
function way(tag, w, a, b) { if (w != null) r(tag, command_x.build_way(pl, a, b, w, true)); }
function wo(tag, o, a, b) { if (o != null) r(tag + " wayobj", command_x.build_wayobj(pl, a, b, o)); }
local DEPOT = null;
foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) if (d.get_name() == "ami_maglev_depot") DEPOT = d;
if (DEPOT == null) report += "ami_maglev_depot desc=[missing]\n";

// 地上の輪の区画（車庫・輪・十字・斜め・行き止まり）。y0 は区画の上の端。o は輪と十字に重ねる way-object（null なら重ねない）
function ground(tag, w, y0, o) {
  way(tag + " depot", w, c(1, y0 + 2), c(3, y0 + 2));
  way(tag + " cross", w, c(7, y0), c(7, y0 + 4));
  way(tag + " loopN", w, c(3, y0 + 2), c(12, y0 + 2));
  way(tag + " loopE", w, c(12, y0 + 2), c(12, y0 + 8));
  way(tag + " loopS", w, c(12, y0 + 8), c(3, y0 + 8));
  way(tag + " loopW", w, c(3, y0 + 8), c(3, y0 + 2));
  way(tag + " diag", w, c(16, y0 + 2), c(22, y0 + 8));
  way(tag + " dead", w, c(25, y0 + 2), c(25, y0 + 6));
  if (DEPOT != null) r(tag + " depot", command_x.build_depot(pl, c(1, y0 + 2), DEPOT));
  if (o != null) {
    wo(tag + " depot", o, c(1, y0 + 2), c(3, y0 + 2));
    wo(tag + " loopN", o, c(3, y0 + 2), c(12, y0 + 2));
    wo(tag + " loopE", o, c(12, y0 + 2), c(12, y0 + 8));
    wo(tag + " loopS", o, c(12, y0 + 8), c(3, y0 + 8));
    wo(tag + " loopW", o, c(3, y0 + 8), c(3, y0 + 2));
    wo(tag + " cross", o, c(7, y0), c(7, y0 + 4));
    wo(tag + " diag", o, c(16, y0 + 2), c(22, y0 + 8));
    wo(tag + " dead", o, c(25, y0 + 2), c(25, y0 + 6));
  }
}
ground("G", wd("ami_maglev_guideway_single"), 0, GUIDE);
ground("B", wd("ami_maglev_beam"), 12, null);
ground("U", wd("ami_maglev_tube_single"), 24, COVER);

// ---- 高架（x0 は区画の西の端。pier は真下に敷く橋脚の way、o は重ねる way-object）
function elev(tag, w, x0, y, pier, o) {
  local segs = [[2, 0, 2, 6], [4, 3, 12, 3], [14, 0, 20, 0], [20, 0, 20, 6], [17, 0, 17, 4], [24, 0, 30, 6]];
  foreach (s in segs) {
    local a = c(x0 + s[0], y + s[1]), b = c(x0 + s[2], y + s[3]);
    way(tag, w, a, b);
    if (pier != null) way(tag + " pier", pier, a, b);
    wo(tag, o, c(x0 + s[0], y + s[1], ELEV_UP), c(x0 + s[2], y + s[3], ELEV_UP));
  }
}
local PIER = wd("ami_pier_rail");
foreach (i, v in ["single", "back", "center", "front"]) {
  elev("EG " + v, wd("ami_maglev_guideway_elev_" + v), 40, i * 10, PIER, GUIDE);
  elev("EU " + v, wd("ami_maglev_tube_elev_" + v), 120, i * 10, PIER, COVER);
}
foreach (i, v in ["front", "center", "back"]) elev("EB " + v, wd("ami_maglev_beam_elev_" + v), 80, i * 10, null, null);

// ---- P: 複線（超電導の地上と高架、チューブ式の地上）と center の版
local gb = wd("ami_maglev_guideway_back"), gf = wd("ami_maglev_guideway_front");
local eb = wd("ami_maglev_guideway_elev_back"), ef = wd("ami_maglev_guideway_elev_front");
local tb = wd("ami_maglev_tube_back"), tf = wd("ami_maglev_tube_front");
foreach (k in [[gb, gf, 0, 0, GUIDE], [eb, ef, 18, ELEV_UP, GUIDE], [tb, tf, 36, 0, COVER]]) {
  local x = k[2];
  way("P ns back", k[0], c(x + 2, 36), c(x + 2, 44));
  way("P ns front", k[1], c(x + 3, 36), c(x + 3, 44));
  way("P ew back", k[0], c(x + 6, 38), c(x + 14, 38));
  way("P ew front", k[1], c(x + 6, 39), c(x + 14, 39));
  if (k[3] > 0) {
    way("P pier", PIER, c(x + 2, 36), c(x + 2, 44));
    way("P pier", PIER, c(x + 3, 36), c(x + 3, 44));
    way("P pier", PIER, c(x + 6, 38), c(x + 14, 38));
    way("P pier", PIER, c(x + 6, 39), c(x + 14, 39));
  }
  wo("P ns back", k[4], c(x + 2, 36, k[3]), c(x + 2, 44, k[3]));
  wo("P ns front", k[4], c(x + 3, 36, k[3]), c(x + 3, 44, k[3]));
  wo("P ew back", k[4], c(x + 6, 38, k[3]), c(x + 14, 38, k[3]));
  wo("P ew front", k[4], c(x + 6, 39, k[3]), c(x + 14, 39, k[3]));
}
way("P center", wd("ami_maglev_guideway_center"), c(0, 46), c(8, 46));
wo("P center", GUIDE, c(0, 46), c(8, 46));
way("P center", wd("ami_maglev_tube_center"), c(10, 46), c(18, 46));
wo("P center", COVER, c(10, 46), c(18, 46));

// ---- T: トンネル（東西。丘は x 3〜5 を 2 段上げる）
function set_slope_kept(p, s) { return command_x.set_slope(pl, p, s); }
foreach (i, t in [["ami_maglev_guideway_tunnel", "ami_maglev_guideway_single"], ["ami_maglev_beam_tunnel", "ami_maglev_beam"],
                  ["ami_maglev_tube_tunnel", "ami_maglev_tube_center"]]) {
  local ty = 48 + i * 3;
  for (local x = 3; x <= 5; x++) for (local k = 0; k < 2; k++) r("T raise", set_slope_kept(c(x, ty, k), slope.all_up_slope));
  r("T rampW", set_slope_kept(c(2, ty), 24));
  r("T rampE", set_slope_kept(c(6, ty), 56));
  r("T tunnel " + t[0], command_x(tool_build_tunnel).work(pl, c(2, ty), t[0]));
  way("T wayW", wd(t[1]), c(0, ty), c(2, ty));
  way("T wayE", wd(t[1]), c(6, ty), c(8, ty));
}

// ---- 車両（編成の候補。電化の要る物と要らない物。先に見つかった物を使う）
local VEHICLES = {
  elec = [["test_maglev_e"]],
  plain = [["MarineExpress_Msc1", "MarineExpress_Ms1", "MarineExpress_Msc2"], ["test_maglev_d"]]
};
function find_set(kind) {
  foreach (cand in VEHICLES[kind]) {
    local set = [];
    foreach (n in cand) {
      local e = vehicle_desc_x(n);
      if (e.is_valid()) set.append(e);
    }
    if (set.len() == cand.len()) return set;
  }
  return null;
}
function run(tag, kind, y0) {
  local set = find_set(kind);
  if (set == null) { report += "[v] " + tag + " no " + kind + " vehicle\n"; return; }
  local d = depot_x(OX + 1, OY + y0 + 2, 0);
  local ok = d.append_vehicle(pl, convoy_x(0), set[0]);  // convoy_x(0) は新しい編成。2 両目からはその編成に足す
  if (ok != true) r(tag + " append", ok);
  local list = d.get_convoy_list();
  if (list.len() == 0) { report += tag + " convoy=[none]\n"; return; }
  local cnv = list[list.len() - 1];
  for (local k = 1; k < set.len(); k++) { ok = d.append_vehicle(pl, cnv, set[k]); if (ok != true) r(tag + " append", ok); }
  cnv.change_schedule(pl, schedule_x(wt_maglev, [schedule_entry_x(c(12, y0 + 8), 0, 0), schedule_entry_x(c(3, y0 + 8), 0, 0)]));
  r("start", d.start_convoy(pl, cnv));
  foreach (e in set) report += "[v] " + tag + " " + e.get_name() + "\n";
}
run("G", "elec", 0);
run("B", "plain", 12);
run("U", "plain", 24);

// ---- [check] タイルの way と way-object
function names(x, y, z) {
  local t = tile_x(x, y, z);
  if (!t.is_valid()) return "(none)";
  local w = t.get_way(wt_maglev), p = t.get_way(wt_rail), o = t.find_object(mo_wayobj);
  return (w == null ? "-" : w.get_desc().get_name()) + (p == null ? "" : " / " + p.get_desc().get_name())
         + "+" + (o == null ? "-" : o.get_desc().get_name()) + (w != null && w.is_electrified() ? " elec" : "");
}
foreach (q in [["G loop", 5, 2, 0], ["G cross", 7, 2, 0], ["EG single", 42, 3, ELEV_UP], ["EG pier", 42, 3, 0], ["P elev", 20, 40, ELEV_UP],
               ["U loop", 5, 26, 0], ["EU single", 122, 3, ELEV_UP]])
  report += "[check] " + q[0] + " " + names(OX + q[1], OY + q[2], q[3]) + "\n";
if (SNOW == 0) r("climate", command_x(tool_set_climate).work(pl, c(-2, -2), c(152, 58), "7"));
gui.close_all_windows();
return report;
