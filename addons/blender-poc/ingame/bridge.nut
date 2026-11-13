// 試作の橋（bpoc_track_bridge）の見本。y=100 の x=60〜 に、両端を 1 段上げた谷を作って橋を架ける。flat.sve で使う。
// 撮るときは gui.jump(coord3d(64, 100, 0))。南北の橋は x=75, y=96〜。
function r(name, v) { return name + "=" + (v == null ? "ok" : "[" + v + "]") + "\n"; }
local pl = player_x(0);
local s = "";
local w = way_desc_x("bpoc_track");
local b = bridge_desc_x("bpoc_track_bridge");
// 東西: (60,100) と (68,100) を 1 段上げ、内側を坂にして (61)〜(67) を橋で渡す
s += r("raiseW", command_x.set_slope(pl, coord3d(60, 100, 0), slope.all_up_slope));
s += r("raiseE", command_x.set_slope(pl, coord3d(68, 100, 0), slope.all_up_slope));
s += r("rampW", command_x.set_slope(pl, coord3d(61, 100, 0), 12));
s += r("rampE", command_x.set_slope(pl, coord3d(67, 100, 0), 28));
s += r("bridgeEW", command_x.build_bridge(pl, coord3d(61, 100, 0), coord3d(67, 100, 0), b));
// 南北
s += r("raiseN", command_x.set_slope(pl, coord3d(75, 96, 0), slope.all_up_slope));
s += r("raiseS", command_x.set_slope(pl, coord3d(75, 104, 0), slope.all_up_slope));
s += r("rampN", command_x.set_slope(pl, coord3d(75, 97, 0), 36));
s += r("rampS", command_x.set_slope(pl, coord3d(75, 103, 0), 4));
s += r("bridgeNS", command_x.build_bridge(pl, coord3d(75, 97, 0), coord3d(75, 103, 0), b));
gui.close_all_windows();
return s;
