// 配る pak の読み込みの確認（#91）: pak に入っている全部の物（way・way-object・橋・トンネル）を、1 つずつ道具で敷けるかを確かめる。
// ingame/beta_check.sh が src/*.dat から ITEMS の行を作って差し替え、flat_512_left_v64 の温暖側に敷く。見た目は見ない（敷けたかと、敷いた物の名前だけ）。
// ITEMS: [名前, obj（way・way-object・bridge・tunnel・crossing・building・roadsign）, waytype（dat の値）, system_type（way だけ。1 は高架）, type（building だけ。depot・stop）]
// 並べ方（原点 (OX, OY)。1 つの物に 1 行、ROW タイルずつ南へ）:
//   way: (0)-(5) を東西に敷き、(2) のタイル（高架は 2 段上）の way の名前を読む
//   way-object: 同じ waytype の運び手の way（CARRIER）を (0)-(5) に敷いてから重ね、(2) のタイルの way-object の名前を読む。架線つきは電化も読む
//   橋: 平地の (1)-(7) に架け、(1) の端のタイルの橋の名前を読む
//   車庫（building の depot）: 同じ waytype の運び手の way を (0)-(5) に敷き、(0) に建てる。(0) の車庫の名前を読む
//   操車場（building の stop）: 在来線の運び手を (0)-(5) に敷き、(2) に建てる。(2) の建物の名前を読む
//   道路標識: 一般道路を (0)-(5) に敷き、(2) に置く。(2) の標識の名前を読む
//   水路の踏切（ami_crossing_<線路・道路>_canal）: 運河を (0)-(5) に東西に、線路・道路を (2) の南北に横切らせる
//   トンネル: 別の列（原点 (OX + TUNNEL_DX, OY)。TUNNEL_ROW タイルずつ南へ）で、(3)-(5) を 2 段上げて両端を 2 段の坂にし、(2) から掘る。(2) の坑口のトンネルの名前を読む
// way の行が 1 列に収まらないときは、東（COL_DX）へ列を増やす（flat_512_left_v64 は 512 タイル四方。1 列は MAX_Y まで。#177）。
// 返り値の先頭が ok なら全部敷けた。NG の行に名前と理由が続く。
local ITEMS = [];
local OX = 20, OY = 20, ROW = 4;
local MAX_Y = 500, COL_DX = 12;
local TUNNEL_DX = 40, TUNNEL_ROW = 8;
local ELEV_UP = 2;  // 高架の床の高さ（段。pak128 の既定）
local CARRIER = {track = "ami_rail_ballast", road = "ami_road_general", tram_track = "ami_tram", monorail_track = "ami_monorail_straddle", water = "ami_canal"};
local DEPOT_OBJ = {track = mo_depot_rail, road = mo_depot_road, tram_track = mo_depot_tram, monorail_track = mo_depot_monorail, water = mo_depot_water};
// 路面軌道（橋脚も）の way は、タイルの上では track の way として読む（本体の tram_track は track_wt の system_type 7）
local WT = {track = wt_rail, road = wt_road, tram_track = wt_rail, water = wt_water, monorail_track = wt_monorail};
local pl = player_x(0);

function c(x, y, z = 0) { return coord3d(x, y, z); }
function err(v) { return v == null ? null : "" + v; }
function at(x, y, z = 0) { return z == 0 ? square_x(x, y).get_ground_tile() : square_x(x, y).get_tile_at_height(z); }
function name_of(o) { return o == null ? "-" : o.get_desc().get_name(); }

function check_way(n, wt, st, x, y) {
  local d = way_desc_x(n);
  if (!d.is_valid()) return "desc missing";
  local e = err(command_x.build_way(pl, c(x, y), c(x + 5, y), d, true));
  if (e != null) return "build_way: " + e;
  local t = at(x + 2, y, st == 1 ? ELEV_UP : 0);
  if (t == null) return "no tile";
  local got = name_of(t.get_way(WT[wt]));
  return got == n ? null : "tile has " + got;
}

function check_wayobj(n, wt, x, y) {
  local d = wayobj_desc_x(n);
  if (!d.is_valid()) return "desc missing";
  // 旧描画位置の壁（名前に _old。#26）は、旧の way（ami_rail_old.pak）に重ねる。歩道の壁・柵は歩道（water の way）、懸垂式の電化は懸垂式の way に重ねる
  local carrier = CARRIER[wt] + (n.find("_old") != null ? "_old" : "");
  if (wt == "water" && n.find("sidewalk") != null) carrier = "ami_sidewalk";
  if (wt == "monorail_track" && n.find("suspended") != null) carrier = "ami_monorail_suspended_center";
  local cd = way_desc_x(carrier);
  if (!cd.is_valid()) return "carrier desc missing: " + carrier;
  local e = err(command_x.build_way(pl, c(x, y), c(x + 5, y), cd, true));
  if (e != null) return "carrier: " + e;
  e = err(command_x.build_wayobj(pl, c(x, y), c(x + 5, y), d));
  if (e != null) return "build_wayobj: " + e;
  local t = at(x + 2, y);
  local got = name_of(t.find_object(mo_wayobj));
  if (got != n) return "tile has " + got;
  if ((n.find("_catenary") != null || n.find("_power") != null) && !t.get_way(WT[wt]).is_electrified()) return "not electrified";
  return null;
}

function check_bridge(n, x, y) {
  local d = bridge_desc_x(n);
  if (!d.is_valid()) return "desc missing";
  local e = err(command_x.build_bridge(pl, c(x + 1, y), c(x + 7, y), d));
  if (e != null) return "build_bridge: " + e;
  local got = name_of(at(x + 1, y).find_object(mo_bridge));
  return got == n ? null : "tile has " + got;
}

// 踏切（#111）: 名前 ami_crossing_<線路>_<道路> の線路を (0)-(5) に東西に、道路を (2) の南北に (-1)-(1) で横切らせ、
// (2) のタイルの両方の way が踏切になっているかを読む。どの踏切が選ばれたかは script から読めない（crossing_t の get_name は固定）
function check_crossing(n, x, y) {
  local rest = n.slice("ami_crossing_".len());
  // 水路の踏切（#117）: ami_crossing_<線路・道路>_canal は運河を東西に、線路・道路を南北に横切らせる
  local canal = rest.len() > 6 && rest.slice(rest.len() - 6) == "_canal";
  local cut = canal ? rest.len() - 6 : rest.find("_road_");
  if (cut == null) return "name not ami_crossing_<track>_<road> or ami_crossing_<way>_canal";
  local td = way_desc_x(canal ? "ami_canal" : "ami_" + rest.slice(0, cut));
  local rd = way_desc_x("ami_" + (canal ? rest.slice(0, cut) : rest.slice(cut + 1)));
  if (!td.is_valid() || !rd.is_valid()) return "way desc missing";
  local e = err(command_x.build_way(pl, c(x, y), c(x + 5, y), td, true));
  if (e == null) e = err(command_x.build_way(pl, c(x + 2, y - 1), c(x + 2, y + 1), rd, true));
  if (e != null) return "build_way: " + e;
  local t = at(x + 2, y), a = t.get_way(canal ? wt_water : wt_rail);
  local b = t.get_way(canal ? (rest.slice(0, 4) == "rail" ? wt_rail : wt_road) : wt_road);
  if (a == null || b == null) return "ways missing";
  return a.is_crossing() && b.is_crossing() ? null : "no crossing";
}

// 車庫（#112 ほか）: 運び手の way の端に建てる。建てた所の車庫の名前を読む
function check_depot(n, wt, x, y) {
  local d = building_desc_x(n);
  if (!d.is_valid()) return "desc missing";
  if (!(wt in CARRIER)) return "no carrier for " + wt;
  local e = err(command_x.build_way(pl, c(x, y), c(x + 5, y), way_desc_x(CARRIER[wt]), true));
  if (e != null) return "build_way: " + e;
  e = err(command_x.build_depot(pl, c(x, y), d));
  if (e != null) return "build_depot: " + e;
  local got = name_of(at(x, y).find_object(DEPOT_OBJ[wt]));
  return got == n ? null : "tile has " + got;
}

// 操車場（#115。在来線の上に建てる駅の建物）
function check_stop(n, wt, x, y) {
  local d = building_desc_x(n);
  if (!d.is_valid()) return "desc missing";
  local e = err(command_x.build_way(pl, c(x, y), c(x + 5, y), way_desc_x(CARRIER[wt]), true));
  if (e != null) return "build_way: " + e;
  e = err(command_x.build_station(pl, c(x + 2, y), d));
  if (e != null) return "build_station: " + e;
  local got = name_of(at(x + 2, y).find_object(mo_building));
  return got == n ? null : "tile has " + got;
}

// 道路標識（#122）: 一般道路の上に置く
function check_sign(n, x, y) {
  local sd = null;
  foreach (s in sign_desc_x.get_available_signs(wt_road)) if (s.get_name() == n) sd = s;
  if (sd == null) return "desc missing";
  local e = err(command_x.build_way(pl, c(x, y), c(x + 5, y), way_desc_x(CARRIER.road), true));
  if (e != null) return "build_way: " + e;
  e = err(command_x.build_sign_at(pl, c(x + 2, y), sd));
  if (e != null) return "build_sign_at: " + e;
  local got = name_of(at(x + 2, y).find_object(mo_roadsign));
  return got == n ? null : "tile has " + got;
}

function check_tunnel(n, x, y) {
  if (!tunnel_desc_x(n).is_valid()) return "desc missing";
  for (local k = 3; k <= 5; k++) for (local h = 0; h < 2; h++) {
    local e = err(command_x.set_slope(pl, c(x + k, y, h), slope.all_up_slope));
    if (e != null) return "raise: " + e;
  }
  local e = err(command_x.set_slope(pl, c(x + 2, y), 24));
  if (e == null) e = err(command_x.set_slope(pl, c(x + 6, y), 56));
  if (e != null) return "ramp: " + e;
  e = err(command_x(tool_build_tunnel).work(pl, c(x + 2, y), n));
  if (e != null) return "build_tunnel: " + e;
  local got = name_of(at(x + 2, y).find_object(mo_tunnel));
  return got == n ? null : "tile has " + got;
}

local ng = "", count = 0, row = 0, trow = 0, col = 0;
foreach (it in ITEMS) {
  local n = it[0], obj = it[1], wt = it[2], st = it[3];
  local r = null;
  try {
    if (obj == "tunnel") { r = check_tunnel(n, OX + TUNNEL_DX, OY + trow * TUNNEL_ROW); trow++; }
    else {
      if (OY + row * ROW + ROW > MAX_Y) { row = 0; col++; }
      local y = OY + row * ROW, ox = OX + col * COL_DX;
      row++;
      if (obj == "way") r = check_way(n, wt, st, ox, y);
      else if (obj == "way-object") r = check_wayobj(n, wt, ox, y);
      else if (obj == "bridge") r = check_bridge(n, ox, y);
      else if (obj == "crossing") r = check_crossing(n, ox, y);
      else if (obj == "building" && it[4] == "depot") r = check_depot(n, wt, ox, y);
      else if (obj == "building" && it[4] == "stop") r = check_stop(n, wt, ox, y);
      else if (obj == "roadsign") r = check_sign(n, ox, y);
      else r = "unknown obj " + obj;
    }
  } catch (ex) { r = "exception: " + ex; }
  count++;
  if (r != null) ng += "NG " + n + " (" + obj + "): " + r + "\n";
}
return (ng == "" ? "ok " : "ng ") + count + " items\n" + ng;
