// 高速道路のトンネル（bpoc_expressway_tunnel）の見本。pak128 では坑口は 2 段の坂にしか置けないので、2 段の尾根を作って掘る。flat.sve・flat_snow.sve で使う。
// 今の検証用マップ flat_512.sve でも、この座標（温暖側）にそのまま敷ける。雪は x を 256 ずらす。道路の全種類をまとめて見るときは ingame/road_review.nut
// 東西は x=220〜224, y=120、南北は x=235, y=116〜120（ingame/tunnel.nut の線路の見本の 20 タイル南）。撮るときは gui.jump(coord3d(222, 120, 0))・(235, 118, 0)。
function r(name, v) { return name + "=" + (v == null ? "ok" : "[" + v + "]") + "\n"; }
local pl = player_x(0);
local w = way_desc_x("bpoc_expressway");
local tool = command_x(tool_build_tunnel);
local s = "";
for (local x = 221; x <= 223; x++) for (local k = 0; k < 2; k++) s += r("raise", command_x.set_slope(pl, coord3d(x, 120, k), slope.all_up_slope));
s += r("rampW", command_x.set_slope(pl, coord3d(220, 120, 0), 24));
s += r("rampE", command_x.set_slope(pl, coord3d(224, 120, 0), 56));
s += r("tunnelEW", tool.work(pl, coord3d(220, 120, 0), "bpoc_expressway_tunnel"));
s += r("wayW", command_x.build_way(pl, coord3d(217, 120, 0), coord3d(220, 120, 0), w, true));
s += r("wayE", command_x.build_way(pl, coord3d(224, 120, 0), coord3d(227, 120, 0), w, true));
for (local y = 117; y <= 119; y++) for (local k = 0; k < 2; k++) s += r("raise", command_x.set_slope(pl, coord3d(235, y, k), slope.all_up_slope));
s += r("rampN", command_x.set_slope(pl, coord3d(235, 116, 0), 8));
s += r("rampS", command_x.set_slope(pl, coord3d(235, 120, 0), 72));
s += r("tunnelNS", tool.work(pl, coord3d(235, 116, 0), "bpoc_expressway_tunnel"));
s += r("wayN", command_x.build_way(pl, coord3d(235, 113, 0), coord3d(235, 116, 0), w, true));
s += r("wayS", command_x.build_way(pl, coord3d(235, 120, 0), coord3d(235, 123, 0), w, true));
gui.close_all_windows();
return s;
