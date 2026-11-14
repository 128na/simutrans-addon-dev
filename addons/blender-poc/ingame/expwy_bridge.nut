// 高速道路の橋（bpoc_expressway_bridge）の見本。x=200〜, y=100〜 に架ける。flat_snow.sve・flat.sve で使う（坂を作るのにお金が要る。flat2 では坂が作れない）。
// 今の検証用マップ flat_512.sve でも、この座標（温暖側）にそのまま敷ける。雪は x を 256 ずらす。道路の全種類をまとめて見るときは ingame/road_review.nut
//   y=100 の東西: 平地から平地へ（両端は端の坂 Ramp）。x=212 の南北も同じ
//   y=110 の東西: 両端を 1 段上げた谷に架ける（両端は坂のタイルから始まる Start）
// 撮る所: (204,100)・(212,100)・(204,110)
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
local pl = player_x(0);
local s = "";
local w = way_desc_x("bpoc_expressway");
local b = bridge_desc_x("bpoc_expressway_bridge");
s += r("road W", command_x.build_way(pl, coord3d(197, 100, 0), coord3d(200, 100, 0), w, true));
s += r("road E", command_x.build_way(pl, coord3d(207, 100, 0), coord3d(210, 100, 0), w, true));
s += r("bridge EW", command_x.build_bridge(pl, coord3d(200, 100, 0), coord3d(207, 100, 0), b));
s += r("road N", command_x.build_way(pl, coord3d(212, 93, 0), coord3d(212, 96, 0), w, true));
s += r("road S", command_x.build_way(pl, coord3d(212, 103, 0), coord3d(212, 106, 0), w, true));
s += r("bridge NS", command_x.build_bridge(pl, coord3d(212, 96, 0), coord3d(212, 103, 0), b));
// 谷: (200,110) と (208,110) を 1 段上げ、内側を坂にして (201)〜(207) を渡す
s += r("raiseW", command_x.set_slope(pl, coord3d(200, 110, 0), slope.all_up_slope));
s += r("raiseE", command_x.set_slope(pl, coord3d(208, 110, 0), slope.all_up_slope));
s += r("rampW", command_x.set_slope(pl, coord3d(201, 110, 0), 28));
s += r("rampE", command_x.set_slope(pl, coord3d(207, 110, 0), 12));
s += r("bridge valley", command_x.build_bridge(pl, coord3d(201, 110, 0), coord3d(207, 110, 0), b));
gui.close_all_windows();
return s == "" ? "ok" : s;
