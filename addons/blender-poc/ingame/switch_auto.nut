// 分岐の絵の自動選択の見本。本線の途中に分岐を作り、枝を隣のタイルで曲げる。本体（weg_t::select_switch_image）は
// 隣のカーブの向きから分岐の絵の 1 か 2 を選ぶので、分岐のタイルのカーブが隣のカーブへなめらかにつながれば、絵の向きが合っている。
// flat.sve で使う。y=120 の行に 8 つ（x=150 から 8 ずつ）。撮るときは gui.jump(coord3d(153 + 8 * j, 123, 0))。
//   j: 0 nse→北（2） 1 nse→南（1） 2 nsw→南（2） 3 nsw→北（1） 4 new→東（2） 5 new→西（1） 6 sew→西（2） 7 sew→東（1）
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
local pl = player_x(0);
local w = way_desc_x("bpoc_track");
local out = "";
// 本線の向き（ns / ew）、枝の出る向き（dx, dy）、枝が曲がる向き（dx, dy）
local cases = [["ns", 1, 0, 0, -1], ["ns", 1, 0, 0, 1], ["ns", -1, 0, 0, 1], ["ns", -1, 0, 0, -1],
               ["ew", 0, -1, 1, 0], ["ew", 0, -1, -1, 0], ["ew", 0, 1, -1, 0], ["ew", 0, 1, 1, 0]];
foreach (j, cs in cases) {
  local jx = 153 + 8 * j, jy = 123;
  local p = function(x, y) { return coord3d(x, y, 0); };
  if (cs[0] == "ns") out += r(j + " main", command_x.build_way(pl, p(jx, jy - 3), p(jx, jy + 3), w, true));
  else out += r(j + " main", command_x.build_way(pl, p(jx - 3, jy), p(jx + 3, jy), w, true));
  local bx = jx + cs[1], by = jy + cs[2];
  out += r(j + " out", command_x.build_way(pl, p(jx, jy), p(bx, by), w, true));
  out += r(j + " turn", command_x.build_way(pl, p(bx, by), p(bx + 3 * cs[3], by + 3 * cs[4]), w, true));
}
gui.close_all_windows();
return out == "" ? "ok" : out;
