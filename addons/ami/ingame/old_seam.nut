// 旧描画位置の線路（#26）と SIS の新幹線の線路（SIS_ST_TGbl_E01-999B）の継ぎ目の見本。blender-poc の seam.nut と同じ並びで、
// 比べる線路 → AMI の線路 → 比べる線路 の順に 1 本につなぐ。flat_512_left_v64.sve の降雪でない側（x=130〜152）で使う。
// y0=100 から 20 ずつ、在来線・直結・ラダー・スラブの順に、新（ami_rail_*）を 4 行、旧（ami_rail_*_old）を 4 行（y0=200〜）。
// 直線（東西・南北）、斜め、坂を 1 組ずつ。SIS は way.SIS_ShinkansenTrack_Ballast_E01_ds.pak を addons/pak128 に入れておく。
local pl = player_x(0);
local out = "";
function r(name, v) { return name + "=" + (v == null ? "ok" : "[" + v + "]") + "\n"; }

function set(label, ref_name, mine_name, y0) {
  local ref = way_desc_x(ref_name);
  local mine = way_desc_x(mine_name);
  local pl = player_x(0);
  local s = "";
  // 東西の直線
  s += r(label + " ew1", command_x.build_way(pl, coord3d(130, y0, 0), coord3d(134, y0, 0), ref, true));
  s += r(label + " ew2", command_x.build_way(pl, coord3d(134, y0, 0), coord3d(138, y0, 0), mine, true));
  s += r(label + " ew3", command_x.build_way(pl, coord3d(138, y0, 0), coord3d(142, y0, 0), ref, true));
  // 南北の直線
  s += r(label + " ns1", command_x.build_way(pl, coord3d(146, y0, 0), coord3d(146, y0 + 4, 0), ref, true));
  s += r(label + " ns2", command_x.build_way(pl, coord3d(146, y0 + 4, 0), coord3d(146, y0 + 8, 0), mine, true));
  s += r(label + " ns3", command_x.build_way(pl, coord3d(146, y0 + 8, 0), coord3d(146, y0 + 12, 0), ref, true));
  // 斜め
  s += r(label + " dg1", command_x.build_way(pl, coord3d(130, y0 + 4, 0), coord3d(133, y0 + 7, 0), ref, false));
  s += r(label + " dg2", command_x.build_way(pl, coord3d(133, y0 + 7, 0), coord3d(136, y0 + 10, 0), mine, false));
  s += r(label + " dg3", command_x.build_way(pl, coord3d(136, y0 + 10, 0), coord3d(139, y0 + 13, 0), ref, false));
  // 坂: 2タイルを1段上げ、その南を北上がり(36)にする。坂だけ検証用の線路にする
  s += r(label + " raise1", command_x.set_slope(pl, coord3d(152, y0, 0), slope.all_up_slope));
  s += r(label + " raise2", command_x.set_slope(pl, coord3d(152, y0 + 1, 0), slope.all_up_slope));
  s += r(label + " ramp", command_x.set_slope(pl, coord3d(152, y0 + 2, 0), 36));
  s += r(label + " up1", command_x.build_way(pl, coord3d(152, y0 + 6, 0), coord3d(152, y0 + 3, 0), ref, true));
  s += r(label + " up2", command_x.build_way(pl, coord3d(152, y0 + 3, 0), coord3d(152, y0 + 1, 1), mine, true));
  s += r(label + " up3", command_x.build_way(pl, coord3d(152, y0 + 1, 1), coord3d(152, y0, 1), ref, true));
  return s;
}

local kinds = ["ballast", "concrete", "ladder", "slab"];
for (local i = 0; i < 4; i++) {
  out += set("new_" + kinds[i], "SIS_ST_TGbl_E01-999B", "ami_rail_" + kinds[i], 100 + 20 * i);
  out += set("old_" + kinds[i], "SIS_ST_TGbl_E01-999B", "ami_rail_" + kinds[i] + "_old", 200 + 20 * i);
}
gui.close_all_windows();
return out;
