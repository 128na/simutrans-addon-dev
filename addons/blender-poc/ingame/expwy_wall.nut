// 高速道路の側壁の版（bpoc_expressway_wall_{single,back,center,front}）の並べ方の見本。空の平らなマップ（flat2.sve・flat_snow.sve）の
// x=150〜, y=40〜 に敷く（flat2 の西側には線路の見本がある）。座標は OX だけ東へずらす。1 本ずつの全パターンは ingame/full.nut（WAYS を選んで full_check.sh）で見る。
// 東西の道は北が奥、南北の道は西が奥（カメラは南東）。斜めは東寄りが手前。
//   (5,40)〜  東西の 2 車線（back + front）と 3 車線（back + center + front）。両端は行き止まり
//   (20,38)〜 南北の 2 車線・3 車線
//   (5,50)〜  back・front の T字（分岐が奥向き・手前向き）
//   (30,62)〜・(30,80)〜 斜めの 3 車線（右下がり・右上がり）。階段の形で 1 タイルずらして並べる
// 撮る所（OX を足す前）: (8,42) 東西・(22,41) 南北・(9,54) T字・(34,67) 右下がり・(34,82) 右上がり
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
local pl = player_x(0);
local W = {};
foreach (v in ["single", "back", "center", "front"]) W[v] <- way_desc_x("bpoc_expressway_wall_" + v);
local OX = 145;
local c = function(x, y) { return coord3d(OX + x, y, 0); };
local s = "";
s += r("dbl ew back", command_x.build_way(pl, c(5, 40), c(11, 40), W.back, true));
s += r("dbl ew front", command_x.build_way(pl, c(5, 41), c(11, 41), W.front, true));
s += r("tri ew back", command_x.build_way(pl, c(5, 43), c(11, 43), W.back, true));
s += r("tri ew center", command_x.build_way(pl, c(5, 44), c(11, 44), W.center, true));
s += r("tri ew front", command_x.build_way(pl, c(5, 45), c(11, 45), W.front, true));
s += r("dbl ns back", command_x.build_way(pl, c(20, 38), c(20, 44), W.back, true));
s += r("dbl ns front", command_x.build_way(pl, c(21, 38), c(21, 44), W.front, true));
s += r("tri ns back", command_x.build_way(pl, c(23, 38), c(23, 44), W.back, true));
s += r("tri ns center", command_x.build_way(pl, c(24, 38), c(24, 44), W.center, true));
s += r("tri ns front", command_x.build_way(pl, c(25, 38), c(25, 44), W.front, true));
s += r("t back", command_x.build_way(pl, c(5, 52), c(15, 52), W.back, true));
s += r("t back up", command_x.build_way(pl, c(8, 52), c(8, 50), W.back, true));
s += r("t back down", command_x.build_way(pl, c(12, 52), c(12, 54), W.back, true));
s += r("t front", command_x.build_way(pl, c(5, 57), c(15, 57), W.front, true));
s += r("t front up", command_x.build_way(pl, c(8, 57), c(8, 55), W.front, true));
s += r("t front down", command_x.build_way(pl, c(12, 57), c(12, 59), W.front, true));
// 斜めの 3 車線: 階段の形を 1 タイルずつ敷く（経路探索に任せると L 字になる。wall.nut と同じ）。右下がりは東寄りが手前、右上がりは南寄りが手前
function stair(pl, w, x, y, n, dy) {
  local e = null;
  for (local k = 0; k < n; k++) {
    local a = command_x.build_way(pl, c(x + k, y + k * dy), c(x + k, y + (k + 1) * dy), w, true);
    local b = command_x.build_way(pl, c(x + k, y + (k + 1) * dy), c(x + k + 1, y + (k + 1) * dy), w, true);
    if (a != null) e = a;
    if (b != null) e = b;
  }
  return e;
}
s += r("st front", stair(pl, W.front, 32, 62, 5, 1));
s += r("st center", stair(pl, W.center, 31, 63, 5, 1));
s += r("st back", stair(pl, W.back, 30, 64, 5, 1));
s += r("st2 back", stair(pl, W.back, 30, 84, 5, -1));
s += r("st2 center", stair(pl, W.center, 31, 85, 5, -1));
s += r("st2 front", stair(pl, W.front, 32, 86, 5, -1));
gui.close_all_windows();
return s == "" ? "ok" : s;
