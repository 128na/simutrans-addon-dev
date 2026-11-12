// 道路のつなぎ目の確認: SIS → 検証用 → SIS の順に1本につなげて敷く。
//   y=140〜: 一般道 SIS_L_RG1-1_01S と bpoc_road
//   y=160〜: 高速道路 SIS_E_RG1-1_01S と bpoc_expressway
//   y=180〜: pak128 標準の道路 Road_050 と bpoc_road
// 直線（東西・南北）、斜め、坂、分岐（SIS の直線から検証用の道路が分かれる）を1組ずつ。flat.sve で使う。
// SIS は way.SIS_LocalStreet_CityRoad_ds.pak と way.SIS_ExpressWay_1-1lane_01_ds.pak を addons/pak128 に入れておく。
function r(name, v) { return name + "=" + (v == null ? "ok" : "[" + v + "]") + "\n"; }

function set(label, ref_name, mine_name, y0) {
  local pl = player_x(0);
  local ref = way_desc_x(ref_name);
  local mine = way_desc_x(mine_name);
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
  // 坂: 2タイルを1段上げ、その南を北上がり(36)にする。坂だけ検証用の道路にする
  s += r(label + " raise1", command_x.set_slope(pl, coord3d(152, y0, 0), slope.all_up_slope));
  s += r(label + " raise2", command_x.set_slope(pl, coord3d(152, y0 + 1, 0), slope.all_up_slope));
  s += r(label + " ramp", command_x.set_slope(pl, coord3d(152, y0 + 2, 0), 36));
  s += r(label + " up1", command_x.build_way(pl, coord3d(152, y0 + 6, 0), coord3d(152, y0 + 3, 0), ref, true));
  s += r(label + " up2", command_x.build_way(pl, coord3d(152, y0 + 3, 0), coord3d(152, y0 + 1, 1), mine, true));
  s += r(label + " up3", command_x.build_way(pl, coord3d(152, y0 + 1, 1), coord3d(152, y0, 1), ref, true));
  // 分岐: SIS の東西の道路から、検証用の道路が南へ分かれ、さらに SIS へつながる
  s += r(label + " t1", command_x.build_way(pl, coord3d(156, y0 + 6, 0), coord3d(162, y0 + 6, 0), ref, true));
  s += r(label + " t2", command_x.build_way(pl, coord3d(159, y0 + 6, 0), coord3d(159, y0 + 9, 0), mine, true));
  s += r(label + " t3", command_x.build_way(pl, coord3d(159, y0 + 9, 0), coord3d(159, y0 + 12, 0), ref, true));
  return s;
}

local out = set("road", "SIS_L_RG1-1_01S", "bpoc_road", 140);
out += set("expwy", "SIS_E_RG1-1_01S", "bpoc_expressway", 160);
out += set("def", "Road_050", "bpoc_road", 180);
gui.close_all_windows();
return out;
