// 全方位の確認: 線路（新・旧）・道路・高速道路のそれぞれに、同じ形の見本を敷く。
//   行き止まり4方向・直線2方向・カーブ4方向・T字4方向・十字・斜め（2系統）・坂4方向
// 料金所は4つの向きで置く。flat.sve（256x256 の平地）の x=20〜, y=20〜 を使う。
// 見本1組は 24x16 タイル。種類ごとに x を 26 ずつずらして並べる。
function r(name, v) { return name + "=" + (v == null ? "ok" : "[" + v + "]") + "\n"; }
local pl = player_x(0);

function pattern(label, w, x0, y0) {
  local pl = player_x(0);
  local s = "";
  local c = function(x, y, z = 0) { return coord3d(x0 + x, y0 + y, z); };
  // 行き止まり（東西・南北）と直線
  s += r(label + " ew", command_x.build_way(pl, c(0, 0), c(4, 0), w, true));
  s += r(label + " ns", command_x.build_way(pl, c(6, 0), c(6, 4), w, true));
  // カーブ4方向: 四角い輪
  s += r(label + " loop1", command_x.build_way(pl, c(0, 6), c(4, 6), w, true));
  s += r(label + " loop2", command_x.build_way(pl, c(4, 6), c(4, 10), w, true));
  s += r(label + " loop3", command_x.build_way(pl, c(4, 10), c(0, 10), w, true));
  s += r(label + " loop4", command_x.build_way(pl, c(0, 10), c(0, 6), w, true));
  // T字4方向と十字: 輪の中に十字を入れる
  s += r(label + " box1", command_x.build_way(pl, c(8, 6), c(14, 6), w, true));
  s += r(label + " box2", command_x.build_way(pl, c(14, 6), c(14, 12), w, true));
  s += r(label + " box3", command_x.build_way(pl, c(14, 12), c(8, 12), w, true));
  s += r(label + " box4", command_x.build_way(pl, c(8, 12), c(8, 6), w, true));
  s += r(label + " plus1", command_x.build_way(pl, c(11, 6), c(11, 12), w, true));
  s += r(label + " plus2", command_x.build_way(pl, c(8, 9), c(14, 9), w, true));
  // 斜め2系統（右下がり・右上がり）
  s += r(label + " dg1", command_x.build_way(pl, c(8, 0), c(12, 4), w, false));
  s += r(label + " dg2", command_x.build_way(pl, c(14, 4), c(18, 0), w, false));
  // 坂4方向: 中央1タイルを1段上げ、四方を坂にして十字に越える
  local cx = 20, cy = 9;
  s += r(label + " raise", command_x.set_slope(pl, c(cx, cy), slope.all_up_slope));
  s += r(label + " rampN", command_x.set_slope(pl, c(cx, cy - 1), 4));
  s += r(label + " rampS", command_x.set_slope(pl, c(cx, cy + 1), 36));
  s += r(label + " rampW", command_x.set_slope(pl, c(cx - 1, cy), 12));
  s += r(label + " rampE", command_x.set_slope(pl, c(cx + 1, cy), 28));
  // 斜め隣は中央側の角だけ上げて崖を無くす（北西・北東・南西・南東）
  s += r(label + " cornerNW", command_x.set_slope(pl, c(cx - 1, cy - 1), 3));
  s += r(label + " cornerNE", command_x.set_slope(pl, c(cx + 1, cy - 1), 1));
  s += r(label + " cornerSW", command_x.set_slope(pl, c(cx - 1, cy + 1), 9));
  s += r(label + " cornerSE", command_x.set_slope(pl, c(cx + 1, cy + 1), 27));
  s += r(label + " upNS", command_x.build_way(pl, c(cx, cy - 3), c(cx, cy + 3), w, true));
  s += r(label + " upEW", command_x.build_way(pl, c(cx - 3, cy), c(cx + 3, cy), w, true));
  return s;
}

local out = "";
local x = 20;
foreach (name in ["bpoc_track", "bpoc_track_old", "bpoc_road", "bpoc_expressway"]) {
  out += pattern(name, way_desc_x(name), x, 20);
  x += 26;
}

// 料金所4方向: 一般道の停留所の隣に置く（向きは 南・東・北・西）
local road = way_desc_x("Road_030");
local stop = building_desc_x("small_classic_bus_stop");
local b = building_desc_x("bpoc_tollbooth");
local rots = [dir.south, dir.east, dir.north, dir.west];
foreach (i, rot in rots) {
  local bx = 20 + i * 6;
  out += r("road" + i, command_x.build_way(pl, coord3d(bx, 42, 0), coord3d(bx + 3, 42, 0), road, true));
  out += r("stop" + i, command_x.build_station(pl, coord3d(bx + 1, 42, 0), stop));
  out += r("toll" + i, command_x.build_station(pl, coord3d(bx + 1, 43, 0), b, rot));
}
gui.close_all_windows();
gui.set_zoom(4);
gui.jump(coord3d(40, 30, 0));
return out;
