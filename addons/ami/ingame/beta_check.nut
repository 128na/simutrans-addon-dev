// 配る pak の読み込みの確認（#91）: pak に入っている全部の物（way・way-object・橋・トンネル）を、1 つずつ道具で敷けるかを確かめる。
// ingame/beta_check.sh が src/*.dat から ITEMS の行を作って差し替え、flat_512 の温暖側に敷く。見た目は見ない（敷けたかと、敷いた物の名前だけ）。
// ITEMS: [名前, obj（way・way-object・bridge・tunnel・crossing）, waytype（dat の値）, system_type（way だけ。1 は高架）]
// 並べ方（原点 (OX, OY)。1 つの物に 1 行、ROW タイルずつ南へ）:
//   way: (0)-(5) を東西に敷き、(2) のタイル（高架は 2 段上）の way の名前を読む
//   way-object: 同じ waytype の運び手の way（CARRIER）を (0)-(5) に敷いてから重ね、(2) のタイルの way-object の名前を読む。架線つきは電化も読む
//   橋: 平地の (1)-(7) に架け、(1) の端のタイルの橋の名前を読む
//   トンネル: 別の列（原点 (OX + TUNNEL_DX, OY)。TUNNEL_ROW タイルずつ南へ）で、(3)-(5) を 2 段上げて両端を 2 段の坂にし、(2) から掘る。(2) の坑口のトンネルの名前を読む
// 返り値の先頭が ok なら全部敷けた。NG の行に名前と理由が続く。
local ITEMS = [];
local OX = 20, OY = 20, ROW = 4;
local TUNNEL_DX = 40, TUNNEL_ROW = 8;
local ELEV_UP = 2;  // 高架の床の高さ（段。pak128 の既定）
local CARRIER = {track = "ami_rail_ballast", road = "ami_road_general"};
// 路面軌道（橋脚も）の way は、タイルの上では track の way として読む（本体の tram_track は track_wt の system_type 7）
local WT = {track = wt_rail, road = wt_road, tram_track = wt_rail, water = wt_water};
local pl = player_x(0);

function c(x, y, z = 0) { return coord3d(x, y, z); }
function err(v) { return v == null ? null : "" + v; }
function at(x, y, z = 0) { return z == 0 ? square_x(x, y).get_ground_tile() : square_x(x, y).get_tile_at_height(z); }
function name_of(o) { return o == null ? "-" : o.get_desc().get_name(); }

function check_way(n, wt, st, x, y) {
  local d = way_desc_x(n);
  if (d == null) return "desc missing";
  local e = err(command_x.build_way(pl, c(x, y), c(x + 5, y), d, true));
  if (e != null) return "build_way: " + e;
  local t = at(x + 2, y, st == 1 ? ELEV_UP : 0);
  if (t == null) return "no tile";
  local got = name_of(t.get_way(WT[wt]));
  return got == n ? null : "tile has " + got;
}

function check_wayobj(n, wt, x, y) {
  local d = wayobj_desc_x(n);
  if (d == null) return "desc missing";
  local e = err(command_x.build_way(pl, c(x, y), c(x + 5, y), way_desc_x(CARRIER[wt]), true));
  if (e != null) return "carrier: " + e;
  e = err(command_x.build_wayobj(pl, c(x, y), c(x + 5, y), d));
  if (e != null) return "build_wayobj: " + e;
  local t = at(x + 2, y);
  local got = name_of(t.find_object(mo_wayobj));
  if (got != n) return "tile has " + got;
  if (n.find("_catenary") != null && !t.get_way(WT[wt]).is_electrified()) return "not electrified";
  return null;
}

function check_bridge(n, x, y) {
  local d = bridge_desc_x(n);
  if (d == null) return "desc missing";
  local e = err(command_x.build_bridge(pl, c(x + 1, y), c(x + 7, y), d));
  if (e != null) return "build_bridge: " + e;
  local got = name_of(at(x + 1, y).find_object(mo_bridge));
  return got == n ? null : "tile has " + got;
}

// 踏切（#111）: 名前 ami_crossing_<線路>_<道路> の線路を (0)-(5) に東西に、道路を (2) の南北に (-1)-(1) で横切らせ、
// (2) のタイルの両方の way が踏切になっているかを読む。どの踏切が選ばれたかは script から読めない（crossing_t の get_name は固定）
function check_crossing(n, x, y) {
  local rest = n.slice("ami_crossing_".len());
  local cut = rest.find("_road_");
  if (cut == null) return "name not ami_crossing_<track>_<road>";
  local td = way_desc_x("ami_" + rest.slice(0, cut)), rd = way_desc_x("ami_" + rest.slice(cut + 1));
  if (td == null || rd == null) return "way desc missing";
  local e = err(command_x.build_way(pl, c(x, y), c(x + 5, y), td, true));
  if (e == null) e = err(command_x.build_way(pl, c(x + 2, y - 1), c(x + 2, y + 1), rd, true));
  if (e != null) return "build_way: " + e;
  local t = at(x + 2, y), a = t.get_way(wt_rail), b = t.get_way(wt_road);
  if (a == null || b == null) return "ways missing";
  return a.is_crossing() && b.is_crossing() ? null : "no crossing";
}

function check_tunnel(n, x, y) {
  if (tunnel_desc_x(n) == null) return "desc missing";
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

local ng = "", count = 0, row = 0, trow = 0;
foreach (it in ITEMS) {
  local n = it[0], obj = it[1], wt = it[2], st = it[3];
  local r = null;
  try {
    if (obj == "tunnel") { r = check_tunnel(n, OX + TUNNEL_DX, OY + trow * TUNNEL_ROW); trow++; }
    else {
      local y = OY + row * ROW;
      row++;
      if (obj == "way") r = check_way(n, wt, st, OX, y);
      else if (obj == "way-object") r = check_wayobj(n, wt, OX, y);
      else if (obj == "bridge") r = check_bridge(n, OX, y);
      else if (obj == "crossing") r = check_crossing(n, OX, y);
      else r = "unknown obj " + obj;
    }
  } catch (ex) { r = "exception: " + ex; }
  count++;
  if (r != null) ng += "NG " + n + " (" + obj + "): " + r + "\n";
}
return (ng == "" ? "ok " : "ng ") + count + " items\n" + ng;
