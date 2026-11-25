// AMI の線路の信号（ami_rail_signal。#278）の見本。線路に信号を置き、状態の切り替えと閉塞（列車の停止と発車）を確かめる。
// 検証用の flat_512_left_v64.sve の温暖側 (20,20) に敷く（降雪側 (276,20) にも絵を撮るための信号の列を敷く。SNOW）。
// 使い方: PORT=<ポート> NUT=ingame/signal_sample.nut bash ingame/game.sh の後、PORT=<ポート> NUT=ingame/signal_status.nut bash ingame/game.sh RUN で状態を読む。
// 返り値の先頭が ok なら、信号が置けて（[check] の行）、路面軌道・道路標識と同じタイルへの置けるかの結果も出る。
//
// 区画（原点 (ox,oy) から）:
//   P 線 y=2: 東西の線路 x=0〜34。車庫 x=0、駅 x=4 と x=30。信号 x=15（東行きの列車に向く）。列車 1 本（1 本だけなので信号は進行になり通り抜ける）
//   Q 線 y=8: 同じ作りで列車 2 本。1 本目は駅 x=30 で長く止まり、2 本目が信号で止まるはず
//   R 線 y=14: 絵を見るための線路（x=0〜20）に、信号を東行き・西行きに 1 つずつ（x=6 と x=12。向きの絵を見る）
//   S 線 x=24 の南北の線路（y=14〜24）に信号（南行き・北行き）。東西と南北の絵の位置を見る
//   T 路面軌道 y=28: ami_tram（x=0〜6）に信号が置けるか
//   U 踏切 y=34: 線路 × 道路の交差（x=3）に、信号と道路標識（ami_sign_stop）を重ねて置けるか
local ORIGINS = [[20, 20], [276, 20]];
local pl = player_x(0);
local s = "";
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }

// way の desc は名前で引けても、その pak に無ければ中身が空なので、使える way の一覧から探す
function find_way(name, wt) { foreach (w in way_desc_x.get_available_ways(wt, st_flat)) if (w.get_name() == name) return w; return null; }
local rail = find_way("ami_rail_ballast", wt_rail);
local tram = way_desc_x("ami_tram");  // 路面軌道は get_available_ways の一覧に出ないので、名前で引く（pak に無いと build_way が失敗する）
local road = find_way("ami_road_local", wt_road);
local sig = null;
foreach (d in sign_desc_x.get_available_signs(wt_rail)) if (d.get_name() == "ami_rail_signal") sig = d;
local stop_sign = null;
foreach (d in sign_desc_x.get_available_signs(wt_road)) if (d.get_name() == "ami_sign_stop") stop_sign = d;
// 256 の確認（信号の pak だけ。AMI の線路・道路・路面軌道の 256 のシートがそろうまでの間）: AMI の線路が無いとき、ほかの線路で R・S の信号の列だけを敷く
local only_signal = sig != null && (rail == null || tram == null || road == null || stop_sign == null);
if (only_signal && rail == null) foreach (w in way_desc_x.get_available_ways(wt_rail, st_flat)) { rail = w; break; }
if (rail == null || sig == null || (!only_signal && (tram == null || road == null || stop_sign == null))) return "desc=[missing rail " + (rail != null) + " sig " + (sig != null) + " tram " + (tram != null) + " road " + (road != null) + " stop " + (stop_sign != null) + "]\n";
s += "[check] signal is_signal=" + sig.is_signal() + " cost=" + sig.get_cost() + "\n";

local depot_desc = null;
foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) if (d.get_waytype() == wt_rail) { depot_desc = d; break; }
local st = null;
foreach (d in building_desc_x.get_available_stations(building_desc_x.station, wt_rail, good_desc_x.passenger)) { st = d; break; }
local loco = null;
foreach (v in vehicle_desc_x.get_available_vehicles(wt_rail))
  if (v.get_power() > 0 && !v.needs_electrification() && v.can_be_first() && v.can_be_last() && (loco == null || v.get_topspeed() > loco.get_topspeed())) loco = v;

function place(pos, d) {
  try { local e = command_x.build_sign_at(pl, pos, d); return e == null ? "placed" : "refused:" + e; } catch (e) { return "refused:" + e; }
}
local first = true;
try {
foreach (o in ORIGINS) {
  local ox = o[0], oy = o[1];
  local c = function(x, y) { return coord3d(ox + x, oy + y, 0); };
  local way = function(x0, y0, x1, y1) { return command_x.build_way(pl, c(x0, y0), c(x1, y1), rail, true); };
  // R・S: 絵を見るための信号の列（降雪側にも敷く）
  s += r("R way", way(0, 14, 20, 14));
  s += r("R sig E", command_x.build_sign_at(pl, c(6, 14), sig));
  s += r("R sig W", command_x.build_sign_at(pl, c(12, 14), sig));
  s += r("S way", way(24, 14, 24, 24));
  s += r("S sig", command_x.build_sign_at(pl, c(24, 18), sig));
  if (!first || only_signal) continue;
  first = false;
  // P・Q: 列車を走らせる線（温暖側だけ）
  foreach (ln in [["P", 2, 1], ["Q", 8, 2]]) {
    local y = ln[1];
    s += r(ln[0] + " way", way(0, y, 34, y));
    s += r(ln[0] + " depot", command_x.build_depot(pl, c(0, y), depot_desc));
    s += r(ln[0] + " st1", command_x.build_station(pl, c(4, y), st));
    s += r(ln[0] + " st2", command_x.build_station(pl, c(30, y), st));
    s += r(ln[0] + " sig", command_x.build_sign_at(pl, c(15, y), sig));
    local ok = true;
    for (local k = 0; k < ln[2]; k++) {
      local depot = depot_x(ox, oy + y, 0);
      depot.append_vehicle(pl, convoy_x(0), loco);
      local list = depot.get_convoy_list();
      local cnv = list[list.len() - 1];
      // 1 本目は駅 x=30 で満載まで待つ（積む物が無いので長く止まる）。それ以外は通過するだけ
      local wait_load = (ln[0] == "Q" && k == 0) ? 100 : 0;
      cnv.change_schedule(pl, schedule_x(wt_rail, [schedule_entry_x(c(30, y), wait_load, 0), schedule_entry_x(c(4, y), 0, 0)]));
      depot.start_convoy(pl, cnv);
      s += "[train] " + ln[0] + " " + k + " id=" + cnv.id + "\n";
    }
  }
  // T: 路面軌道に信号が置けるか
  s += r("T way", command_x.build_way(pl, c(0, 28), c(6, 28), tram, true));
  s += "[check] T tram_track signal=" + place(c(3, 28), sig) + "\n";
  // U: 線路 × 道路の踏切（x=3 と x=14）。1 マスに標識は 1 つ: 信号の後の道路標識（x=3）と、道路標識の後の信号（x=14）がどうなるか
  s += r("U rail", way(0, 34, 18, 34));
  s += r("U road1", command_x.build_way(pl, c(3, 31), c(3, 37), road, true));
  s += r("U road2", command_x.build_way(pl, c(14, 31), c(14, 37), road, true));
  s += "[check] U1 crossing rail_signal=" + place(c(3, 34), sig) + " then road_sign=" + place(c(3, 34), stop_sign) + "\n";
  s += "[check] U2 crossing road_sign=" + place(c(14, 34), stop_sign) + " then rail_signal=" + place(c(14, 34), sig) + "\n";
}
} catch (e) { return "EXC " + e + "\n" + s; }
gui.close_all_windows();
return "ok\n" + s;
