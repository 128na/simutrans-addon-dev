// くどさの物差しを合わせる見本（#56 の C）: 描き込みの度合いを分けた在来線（blender/calib.py）と手本の線路を、同じ並びで横に並べる。
// flat_512_left_v64.sve の温暖側 (20,20) と降雪側 (276,20) に敷く。降雪側は敷いた後に一帯を降雪に塗り直す。
// way は WAYS の順に、DX タイルずつ東へずらす。区画（DX x 12）の中の並び（原点から）:
//   P 平行な複線: (0,0)-(9,0) と (0,1)-(9,1)
//   B 輪と十字: (0,3)-(6,9) の輪に (3,3)-(3,9) と (0,6)-(6,6)（直線・カーブ・T字・十字）
//   C 斜め（階段）: (8,3) から南東へ 4 段
// 撮る場所は区画の (5,5)（ingame/calib_capture.sh）。並べる way は calib_capture.sh の WAYS_NUT で替える。
// 返り値の先頭が ok なら全部敷けた
// WAYS は 1 行に書く（calib_capture.sh が WAYS_NUT で行ごと置き換える）
local WAYS = ["ami_rail_ballast_calib0", "ami_rail_ballast_calib1", "ami_rail_ballast_calib2", "ami_rail_ballast_calib3", "ami_rail_ballast_calib4", "Rail_160_Tracks", "SIS_ST_TGbl_E01-999S"];
local ORIGINS = [[20, 20], [276, 20]];
local SNOW = 1;
local DX = 16;
local pl = player_x(0);
local report = "";
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
function lay(name, ox, oy) {
  local w = way_desc_x(name);
  if (!w.is_valid()) return name + " desc=[missing]\n";
  local c = function(x, y) { return coord3d(ox + x, oy + y, 0); };
  local line = function(x0, y0, x1, y1) { return command_x.build_way(pl, c(x0, y0), c(x1, y1), w, true); };
  local s = "";
  s += r(name + " P0", line(0, 0, 9, 0));
  s += r(name + " P1", line(0, 1, 9, 1));
  s += r(name + " B1", line(0, 3, 6, 3));
  s += r(name + " B2", line(6, 3, 6, 9));
  s += r(name + " B3", line(6, 9, 0, 9));
  s += r(name + " B4", line(0, 9, 0, 3));
  s += r(name + " B5", line(3, 3, 3, 9));
  s += r(name + " B6", line(0, 6, 6, 6));
  for (local k = 0; k < 4; k++) {
    s += r(name + " C", command_x.build_way(pl, c(8 + k, 3 + k), c(8 + k, 4 + k), w, true));
    s += r(name + " C", command_x.build_way(pl, c(8 + k, 4 + k), c(9 + k, 4 + k), w, true));
  }
  // 敷けた way の名前を確かめる（無い名前でも way_desc_x が null にならないことがあるため）
  local t = square_x(ox + 1, oy).get_ground_tile().get_way(wt_rail);
  if (t == null || t.get_desc().get_name() != name) s += name + " check=[" + (t == null ? "none" : t.get_desc().get_name()) + "]\n";
  return s;
}
foreach (n, o in ORIGINS) {
  foreach (i, name in WAYS) report += lay(name, o[0] + i * DX, o[1]);
  if (n == SNOW) report += r("climate", command_x(tool_set_climate).work(pl, coord3d(o[0] - 3, o[1] - 3, 0),
                                                      coord3d(o[0] + WAYS.len() * DX + 3, o[1] + 15, 0), "7"));
}
return report == "" ? "ok" : report;
