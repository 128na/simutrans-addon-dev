// 汚し（ウェザリング。#154）の見本: 第 2 弾の物と、同じ素材の色の第 1 弾の物（高架の躯体・橋脚・壁）を隣り合わせに敷く。
// 等倍の画面（約 4 タイル四方）に 1 組が入るよう、組ごとに 5 タイル四方に収め、PITCH タイルずつ離して並べる。
// 検証用の flat_512_left_v64.sve に、温暖側 (20,20) と降雪側 (276,20) の 2 か所へ同じ並びで敷き、降雪側は敷いた後に一帯を降雪に塗り直す。
// 使い方（アドオンのディレクトリで）: sample_parallel.sh に NUT=ingame/weathering_lineup.nut と、SPOTS に下の「撮る場所」を渡す。
//   直す前と直した後を同じ nut・同じ SPOTS で撮る。汚しの案の pak（名前の後ろに SUFFIX）を撮るときは SUFFIX を替える。
// 返り値の先頭が ok なら全部敷けた。違えば先頭が check で、「組 名前=[…]」が続く。
//
// 組（原点 (ox + 列 * PITCH, oy + 行 * PITCH) から。どの組も y=1・3 の 2 本（と y=5）を東西に x=0〜4 で敷く）:
//   行 0  MS 跨座式の高架（y=3）と線路の高架・橋脚（y=1）  MU 懸垂式の高架（y=3）と線路の高架・橋脚（y=1）
//         MG 懸垂式の地上の版（y=1）と線路の基盤・壁（y=3）  MR 跨座式の高架（y=3）と道路の高架・橋脚（y=1）
//   行 1  DP 線路・モノレールの車庫（y=1・3）と線路の高架・橋脚（y=5）  DR 道路・運河の車庫（y=1・3）と線路の高架・橋脚（y=5）
//         YD 操車場（y=1）と線路の高架・橋脚（y=3）  CN 運河（y=1）と線路の基盤・壁（y=3）
//   行 2  SW 歩道・柵・電柱（y=1・3。道路は y=2）と道路の高架・橋脚（y=5）  DV 中央分離帯と標識（y=1）と道路の高架・橋脚（y=3）
//         EM 盛土（y=1 back・y=3 front）と線路の高架・橋脚（y=2）
// 撮る場所（SPOTS。名前:原点からの x:y。組の中ほど）:
//   MS:2:2 MU:10:2 MG:18:2 MR:26:2 DP:2:10 DR:10:10 YD:18:10 CN:26:10 SW:2:18 DV:10:18 EM:18:18
local SUFFIX = "";   // 汚しの案の pak を撮るとき、第 2 弾と第 1 弾の物の名前の後ろに付ける（例: _wA）。sample_parallel.sh の SUFFIX で替わる
local ORIGINS = [[20, 20], [276, 20]];
local SNOW = 1;
local PITCH = 8;
local AREA = [32, 24];
local ELEV_UP = 2;
local pl = player_x(0);
local marker = command_x(tool_set_marker);
local report = "";
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
// 案の pak に入っていない物（SUFFIX を付けた名前が無い物）は元の名前で探す
// （名前の無い desc はインスタンスが返り、is_valid() が false。本体 script/api/api_obj_desc.cc の export_is_valid）
function ok(d) { return d != null && d.is_valid(); }
function wd(n) { local d = way_desc_x(n + SUFFIX); return ok(d) ? d : way_desc_x(n); }
function od(n) { local d = wayobj_desc_x(n + SUFFIX); return ok(d) ? d : wayobj_desc_x(n); }
function depot_desc(n) {
  local hit = null;
  foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) {
    if (d.get_name() == n + SUFFIX) return d;
    if (d.get_name() == n) hit = d;
  }
  return hit;
}
function yard_desc() { local d = building_desc_x("ami_rail_yard" + SUFFIX); return ok(d) ? d : building_desc_x("ami_rail_yard"); }

function lay(ox, oy) {
  local s = "";
  local need = {};
  local W = {
    rail = wd("ami_rail_ballast"), rail_elev = wd("ami_rail_ballast_elev_single"), rail_base = wd("ami_rail_ballast_base_single"),
    pier = wd("ami_pier_rail"), road = wd("ami_road_general"), road_elev = wd("ami_road_general_elev_single"), road_pier = wd("ami_pier_road"),
    straddle = wd("ami_monorail_straddle"), straddle_elev = wd("ami_monorail_straddle_elev_center"),
    susp = wd("ami_monorail_suspended_center"), susp_elev = wd("ami_monorail_suspended_elev_center"),
    canal = wd("ami_canal"), sidewalk = wd("ami_sidewalk"), emb_front = wd("ami_embankment_front"), emb_back = wd("ami_embankment_back")
  };
  local O = {
    rail_wall = od("ami_wall_rail_single"), road_wall = od("ami_wall_road_single"), divider = od("ami_wall_road_center_divider"),
    fence = od("ami_wall_sidewalk_back"), pole = od("ami_wall_sidewalk_front_pole")
  };
  local D = {rail = depot_desc("ami_rail_depot"), mono = depot_desc("ami_monorail_depot"), road = depot_desc("ami_road_depot"),
             canal = depot_desc("ami_canal_depot")};
  foreach (n, d in W) if (!ok(d)) return n + " desc=[missing]\n";
  foreach (n, d in O) if (!ok(d)) return n + " desc=[missing]\n";
  foreach (n, d in D) if (d == null) return n + " depot desc=[missing]\n";
  local yd = yard_desc();
  if (!ok(yd)) return "yard desc=[missing]\n";
  local signs = {};
  foreach (d in sign_desc_x.get_available_signs(wt_road)) signs[d.get_name()] <- d;
  foreach (n in ["ami_sign_stop", "ami_sign_speed_60"]) if (!(n in signs)) return n + " desc=[missing]\n";

  // 組の原点 (gx, gy) からの東西の 1 本（x=0〜4）
  local g = {x = 0, y = 0, tag = ""};
  local c = function(x, y, z = 0) { return coord3d(ox + g.x + x, oy + g.y + y, z); };
  local way = function(name, d, y, x0 = 0, x1 = 4) { return r(g.tag + " " + name, command_x.build_way(pl, c(x0, y), c(x1, y), d, true)); };
  local obj = function(name, d, y, z = 0, x0 = 0, x1 = 4) { return r(g.tag + " " + name, command_x.build_wayobj(pl, c(x0, y, z), c(x1, y, z), d)); };
  // 線路・道路の高架: way、高架の高さに壁、真下の地面に橋脚
  local elev = function(kind, y) {
    if (kind == "rail") return way("rail elev", W.rail_elev, y) + obj("rail wall", O.rail_wall, y, ELEV_UP) + way("pier", W.pier, y);
    return way("road elev", W.road_elev, y) + obj("road wall", O.road_wall, y, ELEV_UP) + way("road pier", W.road_pier, y);
  };
  local bed = function(y) { return way("rail base", W.rail_base, y) + obj("base wall", O.rail_wall, y); };
  local depot = function(name, d, w, y) { return way(name + " way", w, y, 0, 4) + r(g.tag + " " + name, command_x.build_depot(pl, c(0, y), d)); };
  local group = function(tag, col, row) { g.tag = tag; g.x = col * PITCH; g.y = row * PITCH; return r(tag + " label", marker.work(pl, c(0, -1), tag)); };

  // 行 0: モノレール
  s += group("MS", 0, 0) + elev("rail", 1) + way("straddle elev", W.straddle_elev, 3);
  s += group("MU", 1, 0) + elev("rail", 1) + way("susp elev", W.susp_elev, 3);
  s += group("MG", 2, 0) + way("susp", W.susp, 1) + bed(3);
  s += group("MR", 3, 0) + elev("road", 1) + way("straddle elev", W.straddle_elev, 3);
  // 行 1: 車庫・操車場・運河
  s += group("DP", 0, 1) + depot("rail depot", D.rail, W.rail, 1) + depot("mono depot", D.mono, W.straddle, 3) + elev("rail", 5);
  s += group("DR", 1, 1) + depot("road depot", D.road, W.road, 1) + depot("canal depot", D.canal, W.canal, 3) + elev("rail", 5);
  s += group("YD", 2, 1) + way("yard rail", W.rail, 1);
  foreach (x in [1, 2, 3]) s += r("YD yard " + x, command_x.build_station(pl, c(x, 1), yd));
  s += elev("rail", 3);
  s += group("CN", 3, 1) + way("canal", W.canal, 1) + bed(3);
  // 行 2: 歩道・中央分離帯・標識・盛土
  s += group("SW", 0, 2) + way("road", W.road, 2) + way("side N", W.sidewalk, 1) + way("side S", W.sidewalk, 3);
  s += obj("pole", O.pole, 1) + obj("fence", O.fence, 3) + elev("road", 5);
  s += group("DV", 1, 2) + way("road", W.road, 1) + obj("divider", O.divider, 1);
  s += r("DV stop", command_x.build_sign_at(pl, c(0, 1), signs["ami_sign_stop"]));
  s += r("DV speed", command_x.build_sign_at(pl, c(4, 1), signs["ami_sign_speed_60"]));
  s += elev("road", 3);
  s += group("EM", 2, 2) + elev("rail", 2) + way("emb back", W.emb_back, 1) + way("emb front", W.emb_front, 3);
  return s;
}

foreach (n, o in ORIGINS) {
  try { report += lay(o[0], o[1]); } catch (err) { report += "error=[" + err + "]\n"; }
  if (n == SNOW)
    report += r("climate", command_x(tool_set_climate).work(pl, coord3d(o[0] - 2, o[1] - 3, 0), coord3d(o[0] + AREA[0], o[1] + AREA[1], 0), "7"));
}
gui.close_all_windows();
return report == "" ? "ok\n" : "check\n" + report;
