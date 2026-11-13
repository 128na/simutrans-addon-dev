// 坂の手本: seam.nut の坂（x=152）と同じ並びを、x=156 に Rail_100 だけで敷く。こちらの坂と画面で並べて比べる
local pl = player_x(0);
local ref = way_desc_x("Rail_100_Tracks");
local y0 = 120;
local s = "";
function r(name, v) { return name + "=" + (v == null ? "ok" : "[" + v + "]") + "\n"; }
s += r("raise1", command_x.set_slope(pl, coord3d(156, y0, 0), slope.all_up_slope));
s += r("raise2", command_x.set_slope(pl, coord3d(156, y0 + 1, 0), slope.all_up_slope));
s += r("ramp", command_x.set_slope(pl, coord3d(156, y0 + 2, 0), 36));
s += r("up1", command_x.build_way(pl, coord3d(156, y0 + 6, 0), coord3d(156, y0 + 1, 1), ref, true));
s += r("up2", command_x.build_way(pl, coord3d(156, y0 + 1, 1), coord3d(156, y0, 1), ref, true));
gui.close_all_windows();
return s;
