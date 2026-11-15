// AMI の見本（雛形）: 絵を作った way を、直線・カーブ・T字・十字・斜め・坂の十字の並びで敷く。
// 検証用の flat_512.sve に、温暖側 (20,20) と降雪側 (276,20) の 2 か所へ同じ並びで敷く（降雪側は雪の絵が出る）。
// way は WAYS の順に、SPACING タイルずつ南へずらして 1 本ずつ敷く。名札（ASCII）付き。見つからない way は失敗として報告する（WAYS には dat と pak を作った way だけを足す）。
// 使い方: ゲームを -mcp-port 47123 で起動し、flat_512 を開いて
//   python <mcp_client.py> --port 47123 --timeout 300 --run-squirrel "$(cat ingame/sample.nut)"
// 返り値の先頭が ok なら全部敷けた。失敗した所は「名前 場所=[…]」で続く。
local WAYS = ["ami_rail_ballast"];
local ORIGINS = [[20, 20], [276, 20]];
local SPACING = 20;
local pl = player_x(0);
local marker = command_x(tool_set_marker);
local report = "";
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
function stair(w, x, y, n, dy) {
  local e = null;
  for (local k = 0; k < n; k++) {
    local a = command_x.build_way(pl, coord3d(x + k, y + k * dy, 0), coord3d(x + k, y + (k + 1) * dy, 0), w, true);
    local b = command_x.build_way(pl, coord3d(x + k, y + (k + 1) * dy, 0), coord3d(x + k + 1, y + (k + 1) * dy, 0), w, true);
    if (a != null) e = a;
    if (b != null) e = b;
  }
  return e;
}
// 1 本ずつの区画（24x16）。原点 (ox,oy) から:
//   東西の直線 (0,0)-(6,0) / 南北の直線 (8,0)-(8,6) / 直角カーブ (10,0)-(16,0)→(16,6) / T字 (0,4)-(6,4) と (3,4)-(3,8) /
//   十字 (8,10)-(14,10) と (11,8)-(11,12) / 斜め 右下がり (17,0)〜 / 坂の十字 (20,10)（1 段上げて四方を坂にする）
function lay(name, ox, oy) {
  local w = way_desc_x(name);
  if (w == null) return name + " desc=[missing]\n";
  local c = function(x, y) { return coord3d(ox + x, oy + y, 0); };
  local s = r(name + " label", marker.work(pl, c(0, -1), name));
  s += r("ew", command_x.build_way(pl, c(0, 0), c(6, 0), w, true));
  s += r("ns", command_x.build_way(pl, c(8, 0), c(8, 6), w, true));
  s += r("L ew", command_x.build_way(pl, c(10, 0), c(16, 0), w, true));
  s += r("L ns", command_x.build_way(pl, c(16, 0), c(16, 6), w, true));
  s += r("T ew", command_x.build_way(pl, c(0, 4), c(6, 4), w, true));
  s += r("T ns", command_x.build_way(pl, c(3, 4), c(3, 8), w, true));
  s += r("X ew", command_x.build_way(pl, c(8, 10), c(14, 10), w, true));
  s += r("X ns", command_x.build_way(pl, c(11, 8), c(11, 12), w, true));
  s += r("stair", stair(w, ox + 17, oy + 0, 4, 1));
  local cx = 20, cy = 10;
  s += r("hill raise", command_x.set_slope(pl, c(cx, cy), slope.all_up_slope));
  s += r("hill rampN", command_x.set_slope(pl, c(cx, cy - 1), 4));
  s += r("hill rampS", command_x.set_slope(pl, c(cx, cy + 1), 36));
  s += r("hill rampW", command_x.set_slope(pl, c(cx - 1, cy), 12));
  s += r("hill rampE", command_x.set_slope(pl, c(cx + 1, cy), 28));
  s += r("hill ns", command_x.build_way(pl, c(cx, cy - 2), c(cx, cy + 2), w, true));
  s += r("hill ew", command_x.build_way(pl, c(cx - 2, cy), c(cx + 2, cy), w, true));
  return s;
}
foreach (o in ORIGINS) {
  foreach (i, name in WAYS) report += lay(name, o[0], o[1] + i * SPACING);
}
return report == "" ? "ok" : "check\n" + report;
