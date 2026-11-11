// pak128 標準の線路と並べて敷く（直線3本・斜め3本）。flat.sve で使う。
local pl = player_x(0);
local names = ["bpoc_track", "Rail_100_Tracks", "Rail_200_Tracks"];
local out = "";
foreach (i, n in names) {
  local w = way_desc_x(n);
  out += n + " ns=" + command_x.build_way(pl, coord3d(100 + i*2, 100, 0), coord3d(100 + i*2, 107, 0), w, true);
  out += " diag=" + command_x.build_way(pl, coord3d(108 + i*3, 100, 0), coord3d(114 + i*3, 106, 0), w, false) + "\n";
}
gui.close_all_windows(); gui.set_zoom(2); gui.jump(coord3d(108,103,0));
return out;
