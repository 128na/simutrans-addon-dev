// 高架の高速道路（bpoc_expressway_elev_{single,back,center,front}）の見本。空の平らなマップ（flat2.sve・flat_snow.sve）の x=200〜, y=40〜 に敷く。
//   (200,40)〜 single の輪と行き止まり
//   (200,50)〜 3 車線（back + center + front）の東西の直線。両端は行き止まり
//   (212,40)〜 3 車線の南北の直線
//   (200,60)〜 3 車線の斜め（右下がり。階段の形で 1 タイルずつ敷く）
// 撮る所: (204,44) 輪・(204,51) 東西・(213,44) 南北・(203,64) 斜め
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
local pl = player_x(0);
local W = {};
foreach (v in ["single", "back", "center", "front"]) W[v] <- way_desc_x("bpoc_expressway_elev_" + v);
local c = function(x, y) { return coord3d(x, y, 0); };
local s = "";
s += r("loop1", command_x.build_way(pl, c(200, 40), c(204, 40), W.single, true));
s += r("loop2", command_x.build_way(pl, c(204, 40), c(204, 44), W.single, true));
s += r("loop3", command_x.build_way(pl, c(204, 44), c(200, 44), W.single, true));
s += r("loop4", command_x.build_way(pl, c(200, 44), c(200, 40), W.single, true));
s += r("end", command_x.build_way(pl, c(206, 40), c(209, 40), W.single, true));
s += r("ew back", command_x.build_way(pl, c(200, 50), c(207, 50), W.back, true));
s += r("ew center", command_x.build_way(pl, c(200, 51), c(207, 51), W.center, true));
s += r("ew front", command_x.build_way(pl, c(200, 52), c(207, 52), W.front, true));
s += r("ns back", command_x.build_way(pl, c(212, 40), c(212, 47), W.back, true));
s += r("ns center", command_x.build_way(pl, c(213, 40), c(213, 47), W.center, true));
s += r("ns front", command_x.build_way(pl, c(214, 40), c(214, 47), W.front, true));
function stair(pl, w, x, y, n) {
  local e = null;
  for (local k = 0; k < n; k++) {
    local a = command_x.build_way(pl, coord3d(x + k, y + k, 0), coord3d(x + k, y + k + 1, 0), w, true);
    local b = command_x.build_way(pl, coord3d(x + k, y + k + 1, 0), coord3d(x + k + 1, y + k + 1, 0), w, true);
    if (a != null) e = a;
    if (b != null) e = b;
  }
  return e;
}
// 右下がりは東寄りが手前
s += r("st front", stair(pl, W.front, 202, 60, 5));
s += r("st center", stair(pl, W.center, 201, 61, 5));
s += r("st back", stair(pl, W.back, 200, 62, 5));
gui.close_all_windows();
return s == "" ? "ok" : s;
