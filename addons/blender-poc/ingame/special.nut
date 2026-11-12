// 特殊色の確認: 料金所を会社ごと（プレーヤー0 と 公共事業 = プレーヤー1）に置いて、
// 屋根の帯がそれぞれの会社の色になるか、夜に窓と照明が光るかを見る。flat.sve で使う。
function r(name, v) { return name + "=" + (v == null ? "ok" : "[" + v + "]") + "\n"; }
local road = way_desc_x("Road_030");
local stop = building_desc_x("small_classic_bus_stop");
local b = building_desc_x("bpoc_tollbooth");
local out = "";
foreach (i, y in [180, 184]) {
  local pl = player_x(i);
  out += r("road" + i, command_x.build_way(pl, coord3d(130, y, 0), coord3d(136, y, 0), road, true));
  out += r("stop" + i, command_x.build_station(pl, coord3d(132, y, 0), stop));
  out += r("toll" + i, command_x.build_station(pl, coord3d(132, y + 1, 0), b));
  out += r("toll" + i + "b", command_x.build_station(pl, coord3d(133, y + 1, 0), b));
}
gui.close_all_windows();
gui.set_zoom(1);
gui.jump(coord3d(133, 183, 0));
return out;
