// 道路の見た目の最終確認用パターン: 1〜9 で作った道路の全種類を 1 か所に並べる。名札（ASCII）付き。
// flat.sve（夏）・flat_snow.sve（雪）の南東 x=176〜251, y=193〜242 に敷く（どちらも空いている所）。
// flat2.sve では坂が作れない（残高が足りず set_slope が失敗する）ので、坂・坂から始まる橋・トンネルは敷けない。
// 座標の一覧は README の「道路の確認用パターン」。原点 OX, OY を変えると全体が動く。
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
local OX = 176, OY = 194;
local pl = player_x(0);
local marker = command_x(tool_set_marker);
local out = "";
local label = function(x, y, text) { return r(text + " label", marker.work(pl, coord3d(x, y, 0), text)); };
local way = function(name) { return way_desc_x(name); };
// 階段の形の斜め（1 タイルずつ東西・南北を交互に敷く。経路探索に任せると L 字になる）。dy=1 で右下がり、-1 で右上がり
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
// 坂の十字: (cx,cy) を n 段上げ、四方を坂にして十字に越える（full.nut の区画 D・E と同じ）
function hill(w, name, cx, cy, n) {
  local s = "";
  for (local k = 0; k < n; k++) s += r(name + " raise", command_x.set_slope(pl, coord3d(cx, cy, k), slope.all_up_slope));
  s += r(name + " rampN", command_x.set_slope(pl, coord3d(cx, cy - 1, 0), 4 * n));
  s += r(name + " rampS", command_x.set_slope(pl, coord3d(cx, cy + 1, 0), 36 * n));
  s += r(name + " rampW", command_x.set_slope(pl, coord3d(cx - 1, cy, 0), 12 * n));
  s += r(name + " rampE", command_x.set_slope(pl, coord3d(cx + 1, cy, 0), 28 * n));
  s += r(name + " upNS", command_x.build_way(pl, coord3d(cx, cy - 2, 0), coord3d(cx, cy + 2, 0), w, true));
  s += r(name + " upEW", command_x.build_way(pl, coord3d(cx - 2, cy, 0), coord3d(cx + 2, cy, 0), w, true));
  return s;
}

// 1 本ずつの区画（20x11）。原点 (ox,oy) から:
//   行き止まり (0,0)-(2,0)・(4,0)-(4,2) / 輪と十字・T字・カーブ (0,4)-(6,10) / 斜め 右下がり (7,0)〜・右上がり (11,3)〜 /
//   近い斜め (15,0)〜 と (16,0)〜（1 タイルずらした 2 本） / 坂の十字 (11,7) 1 段・急坂の十字 (17,7) 2 段（高架は作らない）
function single(name, ox, oy, slopes) {
  local w = way(name);
  local c = function(x, y) { return coord3d(ox + x, oy + y, 0); };
  local s = label(ox, oy - 1, name);
  s += r(name + " end ew", command_x.build_way(pl, c(0, 0), c(2, 0), w, true));
  s += r(name + " end ns", command_x.build_way(pl, c(4, 0), c(4, 2), w, true));
  s += r(name + " B1", command_x.build_way(pl, c(0, 4), c(6, 4), w, true));
  s += r(name + " B2", command_x.build_way(pl, c(6, 4), c(6, 10), w, true));
  s += r(name + " B3", command_x.build_way(pl, c(6, 10), c(0, 10), w, true));
  s += r(name + " B4", command_x.build_way(pl, c(0, 10), c(0, 4), w, true));
  s += r(name + " B5", command_x.build_way(pl, c(3, 4), c(3, 10), w, true));
  s += r(name + " B6", command_x.build_way(pl, c(0, 7), c(6, 7), w, true));
  s += r(name + " diag down", stair(w, ox + 7, oy + 0, 3, 1));
  s += r(name + " diag up", stair(w, ox + 11, oy + 3, 3, -1));
  s += r(name + " close 1", stair(w, ox + 15, oy + 0, 3, 1));
  s += r(name + " close 2", stair(w, ox + 16, oy + 0, 3, 1));
  if (slopes) {
    s += hill(w, name + " hill", ox + 11, oy + 7, 1);
    s += hill(w, name + " steep", ox + 17, oy + 7, 2);
  }
  return s;
}

// 3 車線の組（back・center・front）の区画（29x14）。原点 (ox,oy) から:
//   東西の直線 (0,0)-(6,2) / 南北の直線 (9,0)-(11,6) / 直角カーブ (13,0)-(20,7) / 斜め 右下がり (22,0)〜 /
//   奥向き・手前向きの T字 back (0,10)・front (10,10) / 近い斜め back (20,9)〜 と front (21,9)〜
function lanes(prefix, ox, oy) {
  local B = way(prefix + "back"), C = way(prefix + "center"), F = way(prefix + "front");
  local c = function(x, y) { return coord3d(ox + x, oy + y, 0); };
  local s = label(ox, oy - 1, prefix + "back/center/front");
  // 東西は北が奥、南北は西が奥
  s += r("ew b", command_x.build_way(pl, c(0, 0), c(6, 0), B, true));
  s += r("ew c", command_x.build_way(pl, c(0, 1), c(6, 1), C, true));
  s += r("ew f", command_x.build_way(pl, c(0, 2), c(6, 2), F, true));
  s += r("ns b", command_x.build_way(pl, c(9, 0), c(9, 6), B, true));
  s += r("ns c", command_x.build_way(pl, c(10, 0), c(10, 6), C, true));
  s += r("ns f", command_x.build_way(pl, c(11, 0), c(11, 6), F, true));
  // 直角カーブ（wall.nut と同じ）: 外側の線は角から先を front に、内側の線は back に切り替える
  s += r("L outer ew", command_x.build_way(pl, c(13, 0), c(19, 0), B, true));
  s += r("L outer ns", command_x.build_way(pl, c(20, 0), c(20, 7), F, true));
  s += r("L outer join", command_x.build_way(pl, c(19, 0), c(20, 0), F, true));
  s += r("L mid", command_x.build_way(pl, c(13, 1), c(19, 1), C, true));
  s += r("L mid2", command_x.build_way(pl, c(19, 1), c(19, 7), C, true));
  s += r("L inner ew", command_x.build_way(pl, c(13, 2), c(17, 2), F, true));
  s += r("L inner ns", command_x.build_way(pl, c(18, 2), c(18, 7), B, true));
  s += r("L inner join", command_x.build_way(pl, c(17, 2), c(18, 2), B, true));
  // 斜め（右下がりは東寄りが手前）
  s += r("st f", stair(F, ox + 24, oy + 0, 4, 1));
  s += r("st c", stair(C, ox + 23, oy + 1, 4, 1));
  s += r("st b", stair(B, ox + 22, oy + 2, 4, 1));
  // T字: 分岐が奥向き・手前向き
  s += r("t back", command_x.build_way(pl, c(0, 11), c(8, 11), B, true));
  s += r("t back up", command_x.build_way(pl, c(2, 11), c(2, 9), B, true));
  s += r("t back down", command_x.build_way(pl, c(6, 11), c(6, 13), B, true));
  s += r("t front", command_x.build_way(pl, c(10, 11), c(18, 11), F, true));
  s += r("t front up", command_x.build_way(pl, c(12, 11), c(12, 9), F, true));
  s += r("t front down", command_x.build_way(pl, c(16, 11), c(16, 13), F, true));
  // 近い斜め: 1 タイルずらした 2 本（分け合うタイルに 2 本の way が入る。西の線が奥）
  s += r("close b", stair(B, ox + 21, oy + 9, 4, 1));
  s += r("close f", stair(F, ox + 22, oy + 9, 4, 1));
  return s;
}

// 橋とトンネルの区画（28x17）。原点 (ox,oy) から:
//   平地からの橋 東西 (2,0)-(9,0)・南北 (14,0)-(14,9) / 谷の橋 東西 1 段 (1,4)-(7,4)・2 段 (1,8)-(7,8)・南北 1 段 (24,1)-(24,7) /
//   トンネル 東西 (1,14)-(5,14)・南北 (20,1)-(20,5)
function structures(ox, oy) {
  local w = way("bpoc_expressway");
  local b = bridge_desc_x("bpoc_expressway_bridge");
  local tool = command_x(tool_build_tunnel);
  local c = function(x, y, z = 0) { return coord3d(ox + x, oy + y, z); };
  local s = label(ox, oy - 1, "bridge / tunnel");
  s += r("br ew road W", command_x.build_way(pl, c(0, 0), c(2, 0), w, true));
  s += r("br ew road E", command_x.build_way(pl, c(9, 0), c(11, 0), w, true));
  s += r("br ew", command_x.build_bridge(pl, c(2, 0), c(9, 0), b));
  s += r("br ns road N", command_x.build_way(pl, c(14, -1), c(14, 0), w, true));
  s += r("br ns road S", command_x.build_way(pl, c(14, 9), c(14, 11), w, true));
  s += r("br ns", command_x.build_bridge(pl, c(14, 0), c(14, 9), b));
  // 谷 1 段（東西）
  s += r("v1 raiseW", command_x.set_slope(pl, c(0, 4), slope.all_up_slope));
  s += r("v1 raiseE", command_x.set_slope(pl, c(8, 4), slope.all_up_slope));
  s += r("v1 rampW", command_x.set_slope(pl, c(1, 4), 28));
  s += r("v1 rampE", command_x.set_slope(pl, c(7, 4), 12));
  s += r("v1 bridge", command_x.build_bridge(pl, c(1, 4), c(7, 4), b));
  // 谷 2 段（東西）
  foreach (x in [0, 8]) for (local k = 0; k < 2; k++) s += r("v2 raise", command_x.set_slope(pl, c(x, 8, k), slope.all_up_slope));
  s += r("v2 rampW", command_x.set_slope(pl, c(1, 8), 56));
  s += r("v2 rampE", command_x.set_slope(pl, c(7, 8), 24));
  s += r("v2 bridge", command_x.build_bridge(pl, c(1, 8), c(7, 8), b));
  // 谷 1 段（南北）
  s += r("vn raiseN", command_x.set_slope(pl, c(24, 0), slope.all_up_slope));
  s += r("vn raiseS", command_x.set_slope(pl, c(24, 8), slope.all_up_slope));
  s += r("vn rampN", command_x.set_slope(pl, c(24, 1), 36));
  s += r("vn rampS", command_x.set_slope(pl, c(24, 7), 4));
  s += r("vn bridge", command_x.build_bridge(pl, c(24, 1), c(24, 7), b));
  // トンネル 東西: 2 段の尾根 (2,14)〜(4,14) を掘る
  for (local x = 2; x <= 4; x++) for (local k = 0; k < 2; k++) s += r("tn raise", command_x.set_slope(pl, c(x, 14, k), slope.all_up_slope));
  s += r("tn rampW", command_x.set_slope(pl, c(1, 14), 24));
  s += r("tn rampE", command_x.set_slope(pl, c(5, 14), 56));
  s += r("tn ew", tool.work(pl, c(1, 14), "bpoc_expressway_tunnel"));
  s += r("tn road W", command_x.build_way(pl, c(-2, 14), c(1, 14), w, true));
  s += r("tn road E", command_x.build_way(pl, c(5, 14), c(8, 14), w, true));
  // トンネル 南北: 2 段の尾根 (20,2)〜(20,4)
  for (local y = 2; y <= 4; y++) for (local k = 0; k < 2; k++) s += r("tn raise", command_x.set_slope(pl, c(20, y, k), slope.all_up_slope));
  s += r("tn rampN", command_x.set_slope(pl, c(20, 1), 8));
  s += r("tn rampS", command_x.set_slope(pl, c(20, 5), 72));
  s += r("tn ns", tool.work(pl, c(20, 1), "bpoc_expressway_tunnel"));
  s += r("tn road N", command_x.build_way(pl, c(20, -1), c(20, 1), w, true));
  s += r("tn road S", command_x.build_way(pl, c(20, 5), c(20, 8), w, true));
  return s;
}

out += single("bpoc_road", OX, OY, true);
out += single("bpoc_expressway", OX + 22, OY, true);
out += single("bpoc_expressway_wall_single", OX, OY + 14, true);
out += single("bpoc_expressway_elev_single", OX + 22, OY + 14, false);
out += lanes("bpoc_expressway_wall_", OX + 46, OY);
out += lanes("bpoc_expressway_elev_", OX + 46, OY + 16);
out += structures(OX + 2, OY + 31);
gui.close_all_windows();
return out == "" ? "ok" : out;
