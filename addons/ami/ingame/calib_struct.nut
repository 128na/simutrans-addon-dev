// くどさを測る見本の、基盤・高架の版用（#72）: 通常の版・基盤の版・高架の版を、calib.nut と同じ並び（斜め C を除く）で横に並べる。
// 線路と道路のどちらも敷ける（waytype は way の desc から取る）。高架の版（system_type=1）は、地面の座標で敷くと高架の高さ（ELEV_UP 段）に乗る。
// 壁の way-object と橋脚の way は敷かない（way の絵だけを測る）。
// flat_512_left_v64.sve の温暖側 (20,20) と降雪側 (276,20) に敷く。降雪側は敷いた後に一帯を降雪に塗り直す。
// way は WAYS の順に、DX タイルずつ東へずらす。区画（DX x 12）の中の並び（原点から）:
//   P 平行な 2 本: (0,0)-(9,0) と (0,1)-(9,1)
//   B 輪と十字: (0,3)-(6,9) の輪に (3,3)-(3,9) と (0,6)-(6,6)（直線・カーブ・T字・十字）
//   斜め C は敷かない（基盤・高架の版は近い斜めの絵を持たないので、通常の版も同じ並びにそろえる）
// 撮る場所は区画の (5,5)（ingame/calib_capture.sh に NUT=ingame/calib_struct.nut で渡す）。並べる way は calib_capture.sh の WAYS_NUT で替える。
// 1 回に並べるのは 14 本まで（温暖側の区画が降雪側の原点 276 に届かないように）
// 返り値の先頭が ok なら全部敷けた
// WAYS は 1 行に書く（calib_capture.sh が WAYS_NUT で行ごと置き換える）
local WAYS = ["ami_rail_ballast", "ami_rail_ballast_base_single", "ami_rail_ballast_elev_single"];
local ORIGINS = [[20, 20], [276, 20]];
local SNOW = 1;
local DX = 16;
local ELEV_UP = 2;  // 高架の床の高さ（段。pak128 の既定）
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
  // 敷けた way の名前を確かめる（無い名前でも way_desc_x が null にならないことがあるため）。高架の版は高架の高さのタイルを見る
  local elev = name.find("_elev_") != null;
  local g = elev ? square_x(ox + 1, oy).get_tile_at_height(ELEV_UP) : square_x(ox + 1, oy).get_ground_tile();
  local t = g == null ? null : g.get_way(w.get_waytype());
  if (t == null || t.get_desc().get_name() != name) s += name + " check=[" + (t == null ? "none" : t.get_desc().get_name()) + "]\n";
  return s;
}
foreach (n, o in ORIGINS) {
  foreach (i, name in WAYS) report += lay(name, o[0] + i * DX, o[1]);
  if (n == SNOW) report += r("climate", command_x(tool_set_climate).work(pl, coord3d(o[0] - 3, o[1] - 3, 0),
                                                      coord3d(o[0] + WAYS.len() * DX + 3, o[1] + 15, 0), "7"));
}
return report == "" ? "ok" : report;
