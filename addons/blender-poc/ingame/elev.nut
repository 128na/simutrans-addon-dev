// 高架（bpoc_track_elev_*）と、行き止まりの並びの見本。flat.sve で使う。
//   高架: x=120〜, y=20〜 に、単線の輪・行き止まり、3 線（奥+中+手前）の直線
//   行き止まりの並び（地上の側壁）: x=120〜, y=40〜 に、奥+中+手前の 3 線を両端とも行き止まりで
// 撮るときは gui.jump(coord3d(124, 24, 0))・(124, 32, 0)・(123, 41, 0)。
function r(name, v) { return name + "=" + (v == null ? "ok" : "[" + v + "]") + "\n"; }
local pl = player_x(0);
local s = "";
local es = way_desc_x("bpoc_track_elev_single");
s += r("loop1", command_x.build_way(pl, coord3d(120, 20, 0), coord3d(124, 20, 0), es, true));
s += r("loop2", command_x.build_way(pl, coord3d(124, 20, 0), coord3d(124, 24, 0), es, true));
s += r("loop3", command_x.build_way(pl, coord3d(124, 24, 0), coord3d(120, 24, 0), es, true));
s += r("loop4", command_x.build_way(pl, coord3d(120, 24, 0), coord3d(120, 20, 0), es, true));
s += r("end", command_x.build_way(pl, coord3d(126, 20, 0), coord3d(130, 20, 0), es, true));
s += r("e back", command_x.build_way(pl, coord3d(120, 30, 0), coord3d(127, 30, 0), way_desc_x("bpoc_track_elev_back"), true));
s += r("e center", command_x.build_way(pl, coord3d(120, 31, 0), coord3d(127, 31, 0), way_desc_x("bpoc_track_elev_center"), true));
s += r("e front", command_x.build_way(pl, coord3d(120, 32, 0), coord3d(127, 32, 0), way_desc_x("bpoc_track_elev_front"), true));
s += r("g back", command_x.build_way(pl, coord3d(120, 40, 0), coord3d(125, 40, 0), way_desc_x("bpoc_track_wall_back"), true));
s += r("g center", command_x.build_way(pl, coord3d(120, 41, 0), coord3d(125, 41, 0), way_desc_x("bpoc_track_wall_center"), true));
s += r("g front", command_x.build_way(pl, coord3d(120, 42, 0), coord3d(125, 42, 0), way_desc_x("bpoc_track_wall_front"), true));
gui.close_all_windows();
return s;
