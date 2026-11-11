// ゲーム内確認用: 平らな空き地 (214,94)〜(227,107) に検証用の線路と建物を置く。
// OTRP 版を -mcp-port 付きで起動し、MCP の run_squirrel で実行する。
// flat.sve（平地だけ）と test1.sve で動作確認済み。地形のあるマップでは置き場所を変えること。
local pl = player_x(0);
local w = way_desc_x("bpoc_track");
local b = building_desc_x("bpoc_tollbooth");
local out = "";
function r(name, v) { return name + "=" + (v == null ? "ok" : "[" + v + "]") + "\n"; }
// 直線と端
out += r("ns", command_x.build_way(pl, coord3d(216,95,0), coord3d(216,106,0), w, true));
// 分岐・カーブ・斜め: 直線の途中から斜めに
out += r("branch", command_x.build_way(pl, coord3d(216,99,0), coord3d(221,104,0), w, false));
out += r("ew", command_x.build_way(pl, coord3d(218,106,0), coord3d(226,106,0), w, true));
// 坂: 2タイルを1段上げ、その南を北上がり(36 = 北東+北西の角が上)にして上る
out += r("raise1", command_x.set_slope(pl, coord3d(225,95,0), slope.all_up_slope));
out += r("raise2", command_x.set_slope(pl, coord3d(225,96,0), slope.all_up_slope));
out += r("ramp", command_x.set_slope(pl, coord3d(225,97,0), 36));
out += r("slope_way", command_x.build_way(pl, coord3d(225,95,1), coord3d(225,102,0), w, true));
// 付属建物は停留所の隣にしか置けないので、道路とバス停を先に置く
out += r("road", command_x.build_way(pl, coord3d(218,95,0), coord3d(223,95,0), way_desc_x("Road_030"), true));
out += r("stop", command_x.build_station(pl, coord3d(220,95,0), building_desc_x("small_classic_bus_stop")));
out += r("tollbooth", command_x.build_station(pl, coord3d(220,96,0), b));
gui.close_all_windows();
gui.set_zoom(4);
gui.jump(coord3d(221,100,0));
return out;
