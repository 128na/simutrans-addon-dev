// くどさを測る見本の、壁・橋脚を重ねた版用（#79）: ingame/calib_struct.nut と同じ並び（平行な 2 本・輪と十字）に、
// 基盤の版は同じ版の壁の way-object を、高架の版は同じ版の壁の way-object（高架の高さ）と真下の橋脚の way を重ねる。
// 壁と橋脚の名前は way の名前から決める: ami_<rail|road>_<種類>_<base|elev>_<版> → ami_wall_<rail|road>_<版>、橋脚は ami_pier_<rail|road>。
// 通常の版（_base_・_elev_ を含まない名前）は壁を重ねない（比べる相手）。画像の名前は calib_struct.nut で撮ったものと同じになるので、
// 出力のフォルダを分ける（壁なしの画像と並べて測るときは、名前を替えて同じフォルダに写す。記録 2026-11-21_ami-busyness-ranges.md）。
// center の壁は行き止まりの端の壁だけ（壁の way-object の絵の決まり。ingame/sample.nut と同じ）。
// flat_512.sve の温暖側 (20,20) と降雪側 (276,20) に敷く。降雪側は敷いた後に一帯を降雪に塗り直す。
// 撮る場所は区画の (5,5)（ingame/calib_capture.sh に NUT=ingame/calib_wall.nut で渡す）。1 回に並べるのは 14 本まで
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
local LINES = [[0, 0, 9, 0], [0, 1, 9, 1], [0, 3, 6, 3], [6, 3, 6, 9], [6, 9, 0, 9], [0, 9, 0, 3], [3, 3, 3, 9], [0, 6, 6, 6]];
function lay(name, ox, oy) {
  local w = way_desc_x(name);
  if (w == null) return name + " desc=[missing]\n";
  local elev = name.find("_elev_") != null, onbase = name.find("_base_") != null;
  local kindw = name.find("ami_road_") == 0 ? "road" : "rail";
  local v = (elev || onbase) ? name.slice(name.find(elev ? "_elev_" : "_base_") + 6) : null;
  local wo = v == null ? null : wayobj_desc_x("ami_wall_" + kindw + "_" + v);
  local pier = elev ? way_desc_x("ami_pier_" + kindw) : null;
  if (v != null && wo == null) return name + " wall desc=[missing]\n";
  if (elev && pier == null) return name + " pier desc=[missing]\n";
  local c = function(x, y, z = 0) { return coord3d(ox + x, oy + y, z); };
  local s = "";
  foreach (q in LINES) {
    s += r(name + " line", command_x.build_way(pl, c(q[0], q[1]), c(q[2], q[3]), w, true));
    if (wo != null) {
      local z = elev ? ELEV_UP : 0;
      s += r(name + " wall", command_x.build_wayobj(pl, c(q[0], q[1], z), c(q[2], q[3], z), wo));
    }
    if (pier != null) s += r(name + " pier", command_x.build_way(pl, c(q[0], q[1]), c(q[2], q[3]), pier, true));
  }
  // 敷けた物の名前を確かめる（高架の版は高架の高さのタイル、橋脚は地面のタイル）
  local g = elev ? square_x(ox + 1, oy).get_tile_at_height(ELEV_UP) : square_x(ox + 1, oy).get_ground_tile();
  local t = g == null ? null : g.get_way(w.get_waytype());
  if (t == null || t.get_desc().get_name() != name) s += name + " check=[" + (t == null ? "none" : t.get_desc().get_name()) + "]\n";
  if (wo != null) {
    local o = g == null ? null : g.find_object(mo_wayobj);
    if (o == null || o.get_desc().get_name() != wo.get_name()) s += name + " wall check=[" + (o == null ? "none" : o.get_desc().get_name()) + "]\n";
  }
  if (pier != null) {
    local p = square_x(ox + 1, oy).get_ground_tile().get_way(pier.get_waytype());
    if (p == null || p.get_desc().get_name() != pier.get_name()) s += name + " pier check=[" + (p == null ? "none" : p.get_desc().get_name()) + "]\n";
  }
  return s;
}
foreach (n, o in ORIGINS) {
  foreach (i, name in WAYS) report += lay(name, o[0] + i * DX, o[1]);
  if (n == SNOW) report += r("climate", command_x(tool_set_climate).work(pl, coord3d(o[0] - 3, o[1] - 3, 0),
                                                      coord3d(o[0] + WAYS.len() * DX + 3, o[1] + 15, 0), "7"));
}
return report == "" ? "ok" : report;
