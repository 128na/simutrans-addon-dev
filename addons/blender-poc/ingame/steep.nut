// 坂の十字の確認（ingame/steep_check.sh が撮って測る）。flat.sve で使う。y=60 に、x=20 から 10 ずつずらして並べる。
//   x=20 線路（新）の急坂 / x=30 線路（旧）の急坂 / x=40 pak128 標準 Rail_100 の急坂 / x=50 Rail_100 の1段の坂（手本）
// 急坂: 中央1タイルを2段上げ、四方を2段の坂にして十字に越える。1段の坂は 1 段だけ上げる（このアドオンの1段の坂は all_dirs.nut の見本にある）。
// 斜め隣の4タイルは角だけ上げた坂にする（崖にすると、崖の岩の色が道床と区別できず、縁が測れない）。
// Rail_100 は急坂の絵を持たないので、x=40 は見比べるだけ（1段の坂の絵が出て、線路がつながらない）。
function r(name, v) { return name + "=" + (v == null ? "ok" : "[" + v + "]") + "\n"; }
local pl = player_x(0);
local out = "";
local cy = 60;
// [x, 道, 段数]
foreach (spec in [[20, "bpoc_track", 2], [30, "bpoc_track_old", 2], [40, "Rail_100_Tracks", 2], [50, "Rail_100_Tracks", 1]]) {
  local cx = spec[0], name = spec[1], n = spec[2];
  local w = way_desc_x(name);
  local c = function(x, y, z = 0) { return coord3d(cx + x, cy + y, z); };
  for (local i = 0; i < n; i++) out += r(name + " raise" + i, command_x.set_slope(pl, c(0, 0, i), slope.all_up_slope));
  // 坂の番号は3進で、桁が角の高さ（sw=1, se=3, ne=9, nw=27）。n 段なら各桁が n
  out += r(name + " rampN", command_x.set_slope(pl, c(0, -1), n * 4));
  out += r(name + " rampS", command_x.set_slope(pl, c(0, 1), n * 36));
  out += r(name + " rampW", command_x.set_slope(pl, c(-1, 0), n * 12));
  out += r(name + " rampE", command_x.set_slope(pl, c(1, 0), n * 28));
  out += r(name + " cornerNW", command_x.set_slope(pl, c(-1, -1), n * 3));
  out += r(name + " cornerNE", command_x.set_slope(pl, c(1, -1), n * 1));
  out += r(name + " cornerSW", command_x.set_slope(pl, c(-1, 1), n * 9));
  out += r(name + " cornerSE", command_x.set_slope(pl, c(1, 1), n * 27));
  out += r(name + " upNS", command_x.build_way(pl, c(0, -3), c(0, 3), w, true));
  out += r(name + " upEW", command_x.build_way(pl, c(-3, 0), c(3, 0), w, true));
}
gui.close_all_windows();
return out;
