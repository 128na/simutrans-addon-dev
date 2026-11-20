// くどさを測る道路の見本（#56）: AMI の道路のラウンドの版と、手本の道路を、calib.nut と同じ並びで横に並べる。
// flat_512.sve の温暖側 (20,20) と降雪側 (276,20) に敷く。降雪側は敷いた後に一帯を降雪に塗り直す。
// way は WAYS の順に、DX タイルずつ東へずらす。区画（DX x 12）の中の並び（原点から）:
//   P 平行な 2 本: (0,0)-(9,0) と (0,1)-(9,1)
//   B 輪と十字: (0,3)-(6,9) の輪に (3,3)-(3,9) と (0,6)-(6,6)（直線・カーブ・T字・十字）
//   C 斜め（階段）: (8,3) から南東へ 4 段
// 撮る場所は区画の (5,5)（ingame/calib_capture.sh に NUT=ingame/calib_road.nut で渡す）。並べる way は calib_capture.sh の WAYS_NUT で替える。
// 手本: pak128 の Road_050、iss の iss_wrg_0050・iss_wrg_1200_single（PAKS に iss の iss_road_way.pak を足す）、
//   SIS の一般道 SIS_L_RG1-1_01S・高速道路 SIS_E_RG1-1_01S（検証用のフォルダの addons に入っている）
// 返り値の先頭が ok なら全部敷けた
// WAYS は 1 行に書く（calib_capture.sh が WAYS_NUT で行ごと置き換える）
local WAYS = ["ami_road_local", "ami_road_general", "ami_road_expressway", "Road_050", "iss_wrg_0050", "iss_wrg_1200_single", "SIS_L_RG1-1_01S", "SIS_E_RG1-1_01S"];
local ORIGINS = [[20, 20], [276, 20]];
local SNOW = 1;
local DX = 16;
local pl = player_x(0);
local report = "";
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
function lay(name, ox, oy) {
  local w = way_desc_x(name);
  if (w == null) return name + " desc=[missing]\n";
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
  local t = square_x(ox + 1, oy).get_ground_tile().get_way(w.get_waytype());
  if (t == null || t.get_desc().get_name() != name) s += name + " check=[" + (t == null ? "none" : t.get_desc().get_name()) + "]\n";
  return s;
}
foreach (n, o in ORIGINS) {
  foreach (i, name in WAYS) report += lay(name, o[0] + i * DX, o[1]);
  if (n == SNOW) report += r("climate", command_x(tool_set_climate).work(pl, coord3d(o[0] - 3, o[1] - 3, 0),
                                                      coord3d(o[0] + WAYS.len() * DX + 3, o[1] + 15, 0), "7"));
}
return report == "" ? "ok" : report;
