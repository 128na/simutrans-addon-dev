// 基盤・高架の面の描き込みの段を見比べる見本（#78。blender/surface_calib.py の段）。
// 段ごとに同じ並びを DX タイルずつ東へずらして敷く。way は ami_rail_ballast_base_<版>_surf<段>・_elev_<版>_surf<段>（rounds/ami_surface_calib.pak）、
// 壁の way-object（ami_wall_rail_<版>）と橋脚の way（ami_pier_rail）は dist/ami.pak の今の版を重ねる。
// flat_512_left_v64.sve の温暖側 (20,20) と降雪側 (276,20) に敷く。降雪側は敷いた後に一帯を降雪に塗り直す。
// 区画（段ごと。原点 (ox + i * DX, oy) から）:
//   G 地上（基盤の版）: 東西の 3 線 (0,0)-(9,0) back・(0,1)-(9,1) center・(0,2)-(9,2) front、1 本 (0,4)-(9,4) single、
//     南北の 3 線 (12,0)-(12,9) back・(13,..) center・(14,..) front、斜めの 1 本 (17,0) から南東へ 4 段 single
//   V 高架（高架の版）: G と同じ並びを (0, VY) から。壁は高架の高さ（ELEV_UP 段）に重ね、真下の地面に橋脚の way を敷く
// 撮る場所は ingame/surface_capture.sh の SPOTS
// 返り値の先頭が ok なら全部敷けた
local STEPS = ["0", "1", "2", "3", "j"];
local TRACK = "ami_rail_ballast";
local PIER = "ami_pier_rail";
local ORIGINS = [[20, 20], [276, 20]];
local SNOW = 1;
local DX = 26;
local VY = 14;
local ELEV_UP = 2;
local pl = player_x(0);
local marker = command_x(tool_set_marker);
local report = "";
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
local mode = {z = 0, pier = null};
function up(p) { return coord3d(p.x, p.y, p.z + mode.z); }
function way2(w, wo, a, b) {
  local e = command_x.build_way(pl, a, b, w, true);
  if (e == null && wo != null) e = command_x.build_wayobj(pl, up(a), up(b), wo);
  if (e == null && mode.pier != null) e = command_x.build_way(pl, a, b, mode.pier, true);
  return e;
}
function stair(w, x, y, n, dy, wo) {
  local e = null;
  for (local k = 0; k < n; k++) {
    local a = way2(w, wo, coord3d(x + k, y + k * dy, 0), coord3d(x + k, y + (k + 1) * dy, 0));
    local b = way2(w, wo, coord3d(x + k, y + (k + 1) * dy, 0), coord3d(x + k + 1, y + (k + 1) * dy, 0));
    if (a != null) e = a;
    if (b != null) e = b;
  }
  return e;
}
function lay(step, kind, ox, oy) {
  local wd = {}, od = {};
  foreach (v in ["single", "back", "center", "front"]) {
    local n = TRACK + "_" + kind + "_" + v + "_surf" + step;
    wd[v] <- way_desc_x(n);
    if (!wd[v].is_valid()) return n + " desc=[missing]\n";
    od[v] <- wayobj_desc_x("ami_wall_rail_" + v);
    if (!od[v].is_valid()) return "ami_wall_rail_" + v + " desc=[missing]\n";
  }
  local c = function(x, y) { return coord3d(ox + x, oy + y, 0); };
  local tag = kind + step;
  local s = r(tag + " label", marker.work(pl, c(0, -2), (kind == "elev" ? "elevated" : "ground") + " surf" + step));
  foreach (k, v in ["back", "center", "front"]) {
    s += r(tag + " ew " + v, way2(wd[v], od[v], c(0, k), c(9, k)));
    s += r(tag + " ns " + v, way2(wd[v], od[v], c(12 + k, 0), c(12 + k, 9)));
  }
  s += r(tag + " single", way2(wd["single"], od["single"], c(0, 4), c(9, 4)));
  s += r(tag + " diag", stair(wd["single"], ox + 17, oy, 4, 1, od["single"]));
  // 敷けた way の名前を確かめる（高架の版は高架の高さのタイルを見る）
  local g = mode.z ? square_x(ox + 1, oy + 1).get_tile_at_height(mode.z) : square_x(ox + 1, oy + 1).get_ground_tile();
  local t = g == null ? null : g.get_way(wt_rail);
  local want = TRACK + "_" + kind + "_center_surf" + step;
  if (t == null || t.get_desc().get_name() != want) s += tag + " check=[" + (t == null ? "none" : t.get_desc().get_name()) + "]\n";
  return s;
}
foreach (n, o in ORIGINS) {
  foreach (i, step in STEPS) {
    mode.z = 0;
    mode.pier = null;
    report += lay(step, "base", o[0] + i * DX, o[1]);
    mode.z = ELEV_UP;
    mode.pier = way_desc_x(PIER);
    if (!mode.pier.is_valid()) { report += PIER + " desc=[missing]\n"; mode.pier = null; }
    report += lay(step, "elev", o[0] + i * DX, o[1] + VY);
  }
  mode.z = 0;
  mode.pier = null;
  if (n == SNOW) report += r("climate", command_x(tool_set_climate).work(pl, coord3d(o[0] - 3, o[1] - 4, 0),
                                                      coord3d(o[0] + STEPS.len() * DX + 3, o[1] + VY + 14, 0), "7"));
}
gui.close_all_windows();
return report == "" ? "ok" : report;
