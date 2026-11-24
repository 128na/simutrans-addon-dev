// つなぎ目と坂の判定の見本（ingame/seam_slope_check.sh が撮り、tools/blender/seam_judge.py・slope_measure.py で測る）。flat_512_left_v64.sve で使う。
// AMI の線路の種類ごとに、REF（pak128 標準の線路）→ AMI → REF の順に 1 本につなげて敷く（blender-poc の seam.nut と同じ並び）。
//   y = 100 + 30 * i（i は TRACKS の順）: x=130〜 東西の直線・x=146 南北の直線・x=130〜 斜め・x=152 坂（坂だけ AMI）
// 坂の十字（blender-poc の steep.nut と同じ形）: y=40 に、種類ごとに x を 20 ずつずらして急坂（2 段）、y=60 に 1 段の坂。
// 1 行の文字列だけを使う（seam_slope_check.sh は行頭の空白と // の行を消して渡す）
local TRACKS = ["ami_rail_ballast", "ami_rail_concrete", "ami_rail_ladder", "ami_rail_slab"];
local REF = "Rail_160_Tracks";
local pl = player_x(0);
local out = "";
function r(name, v) { return name + "=" + (v == null ? "ok" : "[" + v + "]") + "\n"; }

function seam(label, ref, mine, y0) {
  local s = "";
  s += r(label + " ew1", command_x.build_way(pl, coord3d(130, y0, 0), coord3d(134, y0, 0), ref, true));
  s += r(label + " ew2", command_x.build_way(pl, coord3d(134, y0, 0), coord3d(138, y0, 0), mine, true));
  s += r(label + " ew3", command_x.build_way(pl, coord3d(138, y0, 0), coord3d(142, y0, 0), ref, true));
  s += r(label + " ns1", command_x.build_way(pl, coord3d(146, y0, 0), coord3d(146, y0 + 4, 0), ref, true));
  s += r(label + " ns2", command_x.build_way(pl, coord3d(146, y0 + 4, 0), coord3d(146, y0 + 8, 0), mine, true));
  s += r(label + " ns3", command_x.build_way(pl, coord3d(146, y0 + 8, 0), coord3d(146, y0 + 12, 0), ref, true));
  s += r(label + " dg1", command_x.build_way(pl, coord3d(130, y0 + 4, 0), coord3d(133, y0 + 7, 0), ref, false));
  s += r(label + " dg2", command_x.build_way(pl, coord3d(133, y0 + 7, 0), coord3d(136, y0 + 10, 0), mine, false));
  s += r(label + " dg3", command_x.build_way(pl, coord3d(136, y0 + 10, 0), coord3d(139, y0 + 13, 0), ref, false));
  s += r(label + " raise1", command_x.set_slope(pl, coord3d(152, y0, 0), slope.all_up_slope));
  s += r(label + " raise2", command_x.set_slope(pl, coord3d(152, y0 + 1, 0), slope.all_up_slope));
  s += r(label + " ramp", command_x.set_slope(pl, coord3d(152, y0 + 2, 0), 36));
  s += r(label + " up1", command_x.build_way(pl, coord3d(152, y0 + 6, 0), coord3d(152, y0 + 3, 0), ref, true));
  s += r(label + " up2", command_x.build_way(pl, coord3d(152, y0 + 3, 0), coord3d(152, y0 + 1, 1), mine, true));
  s += r(label + " up3", command_x.build_way(pl, coord3d(152, y0 + 1, 1), coord3d(152, y0, 1), ref, true));
  return s;
}

// 坂の十字: 中央を n 段上げ、四方を n 段の坂、斜め隣を角だけ上げた坂にして、十字に越える（坂の番号は 3 進で、桁が角の高さ）
function cross(label, w, cx, cy, n) {
  local s = "";
  local c = function(x, y, z = 0) { return coord3d(cx + x, cy + y, z); };
  for (local i = 0; i < n; i++) s += r(label + " raise" + i, command_x.set_slope(pl, c(0, 0, i), slope.all_up_slope));
  s += r(label + " rampN", command_x.set_slope(pl, c(0, -1), n * 4));
  s += r(label + " rampS", command_x.set_slope(pl, c(0, 1), n * 36));
  s += r(label + " rampW", command_x.set_slope(pl, c(-1, 0), n * 12));
  s += r(label + " rampE", command_x.set_slope(pl, c(1, 0), n * 28));
  s += r(label + " cornerNW", command_x.set_slope(pl, c(-1, -1), n * 3));
  s += r(label + " cornerNE", command_x.set_slope(pl, c(1, -1), n * 1));
  s += r(label + " cornerSW", command_x.set_slope(pl, c(-1, 1), n * 9));
  s += r(label + " cornerSE", command_x.set_slope(pl, c(1, 1), n * 27));
  s += r(label + " upNS", command_x.build_way(pl, c(0, -3), c(0, 3), w, true));
  s += r(label + " upEW", command_x.build_way(pl, c(-3, 0), c(3, 0), w, true));
  return s;
}

local ref = way_desc_x(REF);
foreach (i, name in TRACKS) {
  local w = way_desc_x(name);
  out += seam(name, ref, w, 100 + 30 * i);
  out += cross(name + " steep", w, 20 + 20 * i, 40, 2);
  out += cross(name + " slope", w, 20 + 20 * i, 60, 1);
}
gui.close_all_windows();
return out;
