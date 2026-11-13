// 全方位の表示確認: way の絵 28 種類を、周りのタイルとつながった形で全部出す最小のレイアウト。flat.sve・flat_snow.sve で使う。
// 1 つの way につき 20x11 タイル。WAYS の順に、x=5 から 22 ずつ、4 列で折り返して y=130 から 14 ずつ並べる。
//   A 行き止まり 4 方向: 東西の短い線 (0,0)-(2,0) と南北の短い線 (4,0)-(4,2)         … image[w] [e] [n] [s]、直線との継ぎ目
//   B 輪と十字: (0,4)-(6,10) の輪に、(3,4)-(3,10) と (0,7)-(6,7) の十字               … image[ns] [ew]、カーブ 4、T字 4、十字
//   C 斜め 2 本: (7,0)→(10,3) と (11,3)→(14,0)                                      … diagonal 4、斜め↔直線の継ぎ目
//   D 坂の十字: (11,7) を 1 段上げ、四方を坂にして十字に越える                       … imageup 4、坂↔平地の継ぎ目
//   E 急坂の十字: (17,7) を 2 段上げ、四方を 2 段の坂にして十字に越える               … imageup2 4
//   F 1 タイルだけ: (17,1)                                                          … image[-]
// 撮る場所（way ごとの原点 ox, oy から）: A (2,1)・B (3,7)・C (10,2)・D (11,7)・E (17,7)。ingame/full_check.sh が回す。
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
local WAYS = ["bpoc_track", "bpoc_track_old", "bpoc_track_trial",
              "bpoc_track_wall_single", "bpoc_track_wall_back", "bpoc_track_wall_center", "bpoc_track_wall_front",
              "bpoc_track_elev_single", "bpoc_track_elev_back", "bpoc_track_elev_center", "bpoc_track_elev_front"];

function block(name, ox, oy) {
  local pl = player_x(0);
  local w = way_desc_x(name);
  local c = function(x, y, z = 0) { return coord3d(ox + x, oy + y, z); };
  local s = "";
  local elevated = name.find("_elev_") != null;
  // A
  s += r(name + " A ew", command_x.build_way(pl, c(0, 0), c(2, 0), w, true));
  s += r(name + " A ns", command_x.build_way(pl, c(4, 0), c(4, 2), w, true));
  // B
  s += r(name + " B1", command_x.build_way(pl, c(0, 4), c(6, 4), w, true));
  s += r(name + " B2", command_x.build_way(pl, c(6, 4), c(6, 10), w, true));
  s += r(name + " B3", command_x.build_way(pl, c(6, 10), c(0, 10), w, true));
  s += r(name + " B4", command_x.build_way(pl, c(0, 10), c(0, 4), w, true));
  s += r(name + " B5", command_x.build_way(pl, c(3, 4), c(3, 10), w, true));
  s += r(name + " B6", command_x.build_way(pl, c(0, 7), c(6, 7), w, true));
  // C
  s += r(name + " C1", command_x.build_way(pl, c(7, 0), c(10, 3), w, false));
  s += r(name + " C2", command_x.build_way(pl, c(11, 3), c(14, 0), w, false));
  // D・E: 高架は地面の坂の上には敷かない（平地の上を通る）
  if (!elevated) {
    local hills = [[11, 7, 1], [17, 7, 2]];
    foreach (h in hills) {
      local cx = h[0], cy = h[1], n = h[2];
      for (local k = 0; k < n; k++) s += r(name + " raise", command_x.set_slope(pl, c(cx, cy, k), slope.all_up_slope));
      s += r(name + " rampN", command_x.set_slope(pl, c(cx, cy - 1), 4 * n));
      s += r(name + " rampS", command_x.set_slope(pl, c(cx, cy + 1), 36 * n));
      s += r(name + " rampW", command_x.set_slope(pl, c(cx - 1, cy), 12 * n));
      s += r(name + " rampE", command_x.set_slope(pl, c(cx + 1, cy), 28 * n));
      s += r(name + " upNS", command_x.build_way(pl, c(cx, cy - 2), c(cx, cy + 2), w, true));
      s += r(name + " upEW", command_x.build_way(pl, c(cx - 2, cy), c(cx + 2, cy), w, true));
    }
  }
  // F
  s += r(name + " F", command_x.build_way(pl, c(17, 1), c(17, 1), w, true));
  return s;
}

local out = "";
foreach (i, name in WAYS) out += block(name, 5 + (i % 4) * 22, 130 + (i / 4) * 14);
gui.close_all_windows();
return out == "" ? "ok" : out;
