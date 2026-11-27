// AMI の盛土の見本（#123）: ami_embankment_front・ami_embankment_back を、高架の脇・台の輪・窪みの輪・坂・斜めに敷く。名札（ASCII）付き。
// 検証用の flat_512_left_v64.sve に、温暖側 (20,24) と降雪側 (276,24) の 2 か所へ同じ並びで敷く。降雪側は敷いた後に一帯を降雪に塗り直す。
// 使い方（アドオンのディレクトリで）: sample_parallel.sh に NUT=ingame/embankment_sample.nut を付ける（撮る場所は sample_spots.sh の EMBANKMENT_SPOTS）。
// 返り値の先頭が ok なら全部敷けて、[check] で比べた値も期待どおり。違えば先頭が check で、「名前 場所=[…]」が続く。最後に確かめた値（[check] の行）が続く。
//
// 区画（原点 (ox,oy) から）:
//   A 線路の高架（東西）: 高架 (2,4)-(14,4)（ami_rail_ballast_elev_single に壁 single）。北の (·,3) に back、南の (·,5) に front
//   B 線路の高架（南北）: 高架 (20,0)-(20,10)。西の (19,·) に back、東の (21,·) に front
//   R 道路の高架（東西）: 高架 (2,10)-(14,10)（ami_road_general_elev_single に壁 single）。北の (·,9) に back、南の (·,11) に front
//   M 台の輪: (26,1)-(30,5) の外周。北・西の辺に back、南・東の辺に front（後に敷く。北東・南西の角は front の外の角になる）
//   P 窪みの輪: (34,1)-(38,5) の外周。北・西の辺に front、南・東の辺に back（後に敷く。北東・南西の角は back の内の角になる）
//   S 坂: (45,·) の南北の高架と、両脇 (44,·) に back、(46,·) に front。(·,4) を 1 段上げた坂。T は急坂（2 段。(50〜52,·)）
//   D 斜め: (56,1) から南東への階段の front と、その北東 (57,0) からの階段の back
//   X 橋脚と同じタイル: 東西の橋脚 ami_pier_rail (34,9)-(40,9) を、南北の front (37,7)-(37,11) が横切る
local FRONT = "ami_embankment_front";
local BACK = "ami_embankment_back";
local RAIL_ELEV = "ami_rail_ballast_elev_single";
local RAIL_WALL = "ami_wall_rail_single";
local ROAD_ELEV = "ami_road_general_elev_single";
local ROAD_WALL = "ami_wall_road_single_arc";  // 一般道路の高架（#260）
local PIER = "ami_pier_rail";
local ORIGINS = [[20, 24], [276, 24]];
local SNOW = 1;
local AREA = [64, 14];
local ELEV_UP = 2;
local pl = player_x(0);
local marker = command_x(tool_set_marker);
local report = "";
local checks = "";
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
function way_at(x, y, wt) { return square_x(x, y).get_ground_tile().get_way(wt); }
function name_at(x, y, wt) { local w = way_at(x, y, wt); return w == null ? "-" : w.get_desc().get_name(); }

function lay(ox, oy) {
  local fd = way_desc_x(FRONT), bd = way_desc_x(BACK);
  local re = way_desc_x(RAIL_ELEV), rw = wayobj_desc_x(RAIL_WALL), de = way_desc_x(ROAD_ELEV), dw = wayobj_desc_x(ROAD_WALL);
  local pd = way_desc_x(PIER);
  foreach (n, d in {front = fd, back = bd, rail_elev = re, rail_wall = rw, road_elev = de, road_wall = dw, pier = pd})
    if (!d.is_valid()) return n + " desc=[missing]\n";
  local wt = fd.get_waytype();
  local c = function(x, y, z = 0) { return coord3d(ox + x, oy + y, z); };
  local way = function(d, x0, y0, x1, y1) { return command_x.build_way(pl, c(x0, y0), c(x1, y1), d, true); };
  local elev = function(d, w, x0, y0, x1, y1) {
    local e = command_x.build_way(pl, c(x0, y0), c(x1, y1), d, true);
    if (e != null) return e;
    return command_x.build_wayobj(pl, c(x0, y0, ELEV_UP), c(x1, y1, ELEV_UP), w);
  };
  local stair = function(d, x, y, n) {
    local e = null;
    for (local k = 0; k < n; k++) {
      local a = way(d, x + k, y + k, x + k + 1, y + k);
      local b = way(d, x + k + 1, y + k, x + k + 1, y + k + 1);
      if (a != null) e = a;
      if (b != null) e = b;
    }
    return e;
  };
  local s = r("label", marker.work(pl, c(0, -3), "embankment: A rail / B rail ns / R road / M mound / P pit / S T slope / D diag / X pier"));
  // A・B・R
  s += r("A elev", elev(re, rw, 2, 4, 14, 4));
  s += r("A back", way(bd, 2, 3, 14, 3));
  s += r("A front", way(fd, 2, 5, 14, 5));
  s += r("B elev", elev(re, rw, 20, 0, 20, 10));
  s += r("B back", way(bd, 19, 0, 19, 10));
  s += r("B front", way(fd, 21, 0, 21, 10));
  s += r("R elev", elev(de, dw, 2, 10, 14, 10));
  s += r("R back", way(bd, 2, 9, 14, 9));
  s += r("R front", way(fd, 2, 11, 14, 11));
  // M・P（輪）
  s += r("M n", way(bd, 26, 1, 30, 1)); s += r("M w", way(bd, 26, 1, 26, 5));
  s += r("M s", way(fd, 26, 5, 30, 5)); s += r("M e", way(fd, 30, 1, 30, 5));
  s += r("P n", way(fd, 34, 1, 38, 1)); s += r("P w", way(fd, 34, 1, 34, 5));
  s += r("P s", way(bd, 34, 5, 38, 5)); s += r("P e", way(bd, 38, 1, 38, 5));
  // S・T（坂・急坂）
  foreach (h in [[45, 1], [51, 2]]) {
    local cx = h[0], n = h[1];
    for (local x = cx - 1; x <= cx + 1; x++) {
      for (local j = 0; j < n; j++) s += r("hill raise", command_x.set_slope(pl, c(x, 4, j), slope.all_up_slope));
      s += r("hill rampN", command_x.set_slope(pl, c(x, 3), 4 * n));
      s += r("hill rampS", command_x.set_slope(pl, c(x, 5), 36 * n));
    }
    s += r("hill elev", elev(re, rw, cx, 0, cx, 8));
    s += r("hill back", way(bd, cx - 1, 0, cx - 1, 8));
    s += r("hill front", way(fd, cx + 1, 0, cx + 1, 8));
  }
  // D
  s += r("D front", stair(fd, 56, 1, 4));
  s += r("D back", stair(bd, 57, 0, 4));
  // X
  s += r("X pier", way(pd, 34, 9, 40, 9));
  s += r("X front", way(fd, 37, 7, 37, 11));
  // [check]: 輪の角に残った版と、橋脚を横切ったタイル
  local expect = function(tag, x, y, want) {
    local got = name_at(ox + x, oy + y, wt);
    checks += "[check] " + tag + " (" + x + "," + y + ")=" + got + "\n";
    return got == want ? "" : tag + " (" + x + "," + y + ")=[" + got + " want " + want + "]\n";
  };
  s += expect("M nw", 26, 1, BACK) + expect("M ne", 30, 1, FRONT) + expect("M sw", 26, 5, FRONT) + expect("M se", 30, 5, FRONT);
  s += expect("P nw", 34, 1, FRONT) + expect("P ne", 38, 1, BACK) + expect("P sw", 34, 5, BACK) + expect("P se", 38, 5, BACK);
  local xw = way_at(ox + 37, oy + 9, wt);
  checks += "[check] X cross (37,9)=" + (xw == null ? "-" : xw.get_desc().get_name() + "/d" + xw.get_dirs())
            + " west(36,9)=" + name_at(ox + 36, oy + 9, wt) + " east(38,9)=" + name_at(ox + 38, oy + 9, wt) + "\n";
  return s;
}

foreach (n, o in ORIGINS) {
  report += lay(o[0], o[1]);
  if (n == SNOW)
    report += r("climate", command_x(tool_set_climate).work(pl, coord3d(o[0] - 2, o[1] - 5, 0),
                                                             coord3d(o[0] + AREA[0], o[1] + AREA[1], 0), "7"));
}
gui.close_all_windows();
return (report == "" ? "ok\n" : "check\n" + report) + checks;
