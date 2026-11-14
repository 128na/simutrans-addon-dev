// 分岐の絵（OTRP の switch 画像）を、線路の全アドオンで全部見る見本。空の平らなマップ（flat2.sve など、256x256）で使う。
// 固定の道具（tool_set_switch_image）がある OTRP のビルドが要る。
// way ごとに 1 行（y = 5 + 10 * i）。左から:
//   x=5・13・21   7x7 の輪に十字を入れた区画。T字 4 つと十字 1 つを、標準（固定しない）・選択 1・選択 2 にしたもの
//   x=34 から 8 ずつ 自動選択の 8 通り（本線から枝を出して隣で曲げる。本体が分岐の絵を選ぶ）
// 名札（マーカー）: 区画は輪の内側の角に「way 名 / standard・choice 1・choice 2」、自動選択は分岐のタイルの枝と反対の隣に、選ばれる絵の名前。
// 名札の文字は ASCII にする（MCP 経由で日本語を渡すと u9078 のような形に崩れた）
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
local WAYS = ["bpoc_track", "bpoc_track_old", "bpoc_track_trial",
              "bpoc_track_wall_single", "bpoc_track_wall_back", "bpoc_track_wall_center", "bpoc_track_wall_front",
              "bpoc_track_elev_single", "bpoc_track_elev_back", "bpoc_track_elev_center", "bpoc_track_elev_front"];
// 自動選択: [選ばれる絵, 本線の向き, 枝の出る向き dx, dy, 枝が曲がる向き dx, dy]
local AUTO = [["nse2", "ns", 1, 0, 0, -1], ["nse1", "ns", 1, 0, 0, 1], ["nsw2", "ns", -1, 0, 0, 1], ["nsw1", "ns", -1, 0, 0, -1],
              ["new2", "ew", 0, -1, 1, 0], ["new1", "ew", 0, -1, -1, 0], ["sew2", "ew", 0, 1, -1, 0], ["sew1", "ew", 0, 1, 1, 0]];
local pl = player_x(0);
local pin = command_x(tool_set_switch_image);
local marker = command_x(tool_set_marker);
local p = function(x, y) { return coord3d(x, y, 0); };
local out = "";

// 分岐の絵を固定する。高架は way が地面の 2 段上（pak128）にあるので、地面で通らなければ 2 段上で試す
function set_pin(pl, pin, x, y, choice) {
  local e = pin.work(pl, coord3d(x, y, 0), "" + wt_rail + "," + choice);
  if (e != null) e = pin.work(pl, coord3d(x, y, 2), "" + wt_rail + "," + choice);
  return e;
}

foreach (i, name in WAYS) {
  local w = way_desc_x(name);
  local oy = 5 + 10 * i;
  foreach (k, s in ["standard", "choice 1", "choice 2"]) out += r(name + " label", marker.work(pl, p(6 + 8 * k, oy + 1), name + " / " + s));
  for (local k = 0; k < 3; k++) {
    local ox = 5 + 8 * k;
    local c = function(x, y) { return coord3d(ox + x, oy + y, 0); };
    out += r(name + " ring1", command_x.build_way(pl, c(0, 0), c(6, 0), w, true));
    out += r(name + " ring2", command_x.build_way(pl, c(6, 0), c(6, 6), w, true));
    out += r(name + " ring3", command_x.build_way(pl, c(6, 6), c(0, 6), w, true));
    out += r(name + " ring4", command_x.build_way(pl, c(0, 6), c(0, 0), w, true));
    out += r(name + " ns", command_x.build_way(pl, c(3, 0), c(3, 6), w, true));
    out += r(name + " ew", command_x.build_way(pl, c(0, 3), c(6, 3), w, true));
    if (k > 0) {
      foreach (q in [[3, 0], [6, 3], [3, 6], [0, 3], [3, 3]]) out += r(name + " pin" + k, set_pin(pl, pin, ox + q[0], oy + q[1], k));
    }
  }
  foreach (j, cs in AUTO) {
    local jx = 37 + 8 * j, jy = oy + 3;
    if (cs[1] == "ns") out += r(name + " main", command_x.build_way(pl, p(jx, jy - 3), p(jx, jy + 3), w, true));
    else out += r(name + " main", command_x.build_way(pl, p(jx - 3, jy), p(jx + 3, jy), w, true));
    local bx = jx + cs[2], by = jy + cs[3];
    out += r(name + " out", command_x.build_way(pl, p(jx, jy), p(bx, by), w, true));
    out += r(name + " turn", command_x.build_way(pl, p(bx, by), p(bx + 3 * cs[4], by + 3 * cs[5]), w, true));
    out += r(name + " label", marker.work(pl, p(jx - cs[2], jy - cs[3]), cs[0]));
  }
}
gui.close_all_windows();
return out == "" ? "ok" : out;
