// 分岐の絵（OTRP の switch 画像）の見本。7x7 の輪に十字を入れて T字 4 つと十字 1 つを作り、分岐の絵を固定する。
// 固定の道具（tool_set_switch_image）がある OTRP のビルドで、flat.sve で使う。
// way ごとに 2 区画（左: 選択 1 = image[...1]、右: 選択 2 = image[...2]）。x=125 から 9 ずつ、way ごとに y=100 から 9 ずつ。
// 撮るときは gui.jump(coord3d(128 + 9 * k, 103 + 9 * i, 0))（k: 選択 0/1、i: way の番号）。
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
local WAYS = ["bpoc_track", "bpoc_track_wall_single"];
local pl = player_x(0);
local tool = command_x(tool_set_switch_image);
local out = "";
foreach (i, name in WAYS) {
  local w = way_desc_x(name);
  for (local k = 0; k < 2; k++) {
    local ox = 125 + 9 * k, oy = 100 + 9 * i;
    local c = function(x, y) { return coord3d(ox + x, oy + y, 0); };
    out += r(name + " ring1", command_x.build_way(pl, c(0, 0), c(6, 0), w, true));
    out += r(name + " ring2", command_x.build_way(pl, c(6, 0), c(6, 6), w, true));
    out += r(name + " ring3", command_x.build_way(pl, c(6, 6), c(0, 6), w, true));
    out += r(name + " ring4", command_x.build_way(pl, c(0, 6), c(0, 0), w, true));
    out += r(name + " ns", command_x.build_way(pl, c(3, 0), c(3, 6), w, true));
    out += r(name + " ew", command_x.build_way(pl, c(0, 3), c(6, 3), w, true));
    // T字 4 つ（輪と十字の交わる所）と真ん中の十字を、選択 k+1 に固定する
    foreach (p in [[3, 0], [6, 3], [3, 6], [0, 3], [3, 3]]) {
      out += r(name + " pin" + (k + 1) + " " + p[0] + "," + p[1], tool.work(pl, c(p[0], p[1]), "" + wt_rail + "," + (k + 1)));
    }
  }
}
gui.close_all_windows();
return out == "" ? "ok" : out;
