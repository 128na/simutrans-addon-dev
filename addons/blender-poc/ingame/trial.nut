// 試作の線路（bpoc_track_trial: 車止め・さび色・雪の絵・カーソル）の見本。y=70〜 に、行き止まり4方向・輪・坂を敷く。flat.sve で使う。
// 撮るときは gui.jump(coord3d(24, 74, 0))。
function r(name, v) { return name + "=" + (v == null ? "ok" : "[" + v + "]") + "\n"; }
local pl = player_x(0);
local w = way_desc_x("bpoc_track_trial");
local c = function(x, y, z = 0) { return coord3d(20 + x, 70 + y, z); };
local s = "";
s += r("ew", command_x.build_way(pl, c(0, 0), c(3, 0), w, true));
s += r("ns", command_x.build_way(pl, c(5, 0), c(5, 3), w, true));
s += r("loop1", command_x.build_way(pl, c(0, 5), c(4, 5), w, true));
s += r("loop2", command_x.build_way(pl, c(4, 5), c(4, 9), w, true));
s += r("loop3", command_x.build_way(pl, c(4, 9), c(0, 9), w, true));
s += r("loop4", command_x.build_way(pl, c(0, 9), c(0, 5), w, true));
s += r("dg", command_x.build_way(pl, c(7, 0), c(10, 3), w, false));
gui.close_all_windows();
return s;
