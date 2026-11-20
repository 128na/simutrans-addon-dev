// AMI の分岐の追加画像（ex 画像。Y字分岐 26〜29・三方分岐 31〜34）の見本。本体が ex 画像を自動で選ぶ線路の形を敷き、
// 選ばれた絵が、固定の道具で選んだ ex の絵と同じかを確かめる（#57。決まりは docs/reference/way-addon.md の 9.4）。
// 検証用の flat_512.sve に、温暖側 (OX, OY) と降雪側 (OX + 256, OY) の 2 か所へ同じ並びで敷き、降雪側は敷いた後に降雪に塗り直す。
// 使い方（ゲームを -mcp-port で起動し、flat_512 を開いて）: bash ingame/ex_check.sh（PORT を渡す）
//
// WAYS の 1 組（[way, 重ねる way-object か null]）ごとに 40x36 の区画を、SPACING ずつ南へ敷く。区画の原点 (ox,oy) から:
//   Y   y=4  の行: Y字分岐。根元（1 本側）が東・西・北・南の順に x=4 から 10 ずつ。T字の両隣が、そろって根元と反対の側へ曲がる  … 26〜29
//   3W  y=14 の行: 三方分岐。同じ並びで、十字の両隣がそろって根元と反対の側へ曲がる                                          … 31〜34
//   P   y=24 の行: 固定の道具で選んだ絵（比べる元）。T字 nse・nsw・new・sew と十字を、x=2 から 6 ずつ、y=24 が選択肢 4（26〜30）・y=28 が 3（31〜35）、
//       y=32 は固定しない通常の T字・十字（枝の先が行き止まりなので、分岐の絵は選ばれない）
// 根元の向きと絵の番号: 東 = nse（26・31）、西 = nsw（28・33）、北 = new（27・32）、南 = sew（29・34）。十字は 30・35（標準の十字で埋める）
// 返り値の [check] の行: 自動で選ばれた絵（get_image_id）が、同じ向きの T字を固定した絵と同じで、通常の T字の絵と違えば ok。
// 違えば got/want を、通常の絵と同じなら plain を出す。way-object の絵は番号を読めないので、画面で見る（ex_capture.sh）。
// 名札は ASCII（MCP 経由の日本語は崩れる）。行頭の空白と // で始まる行は ex_check.sh が消して渡すので、複数行の文字列は書かない
// 高架の版は敷かない（way-object を高架の高さで敷く手間を省いた。高架の way は地上の版と同じ dat の作りで、継ぎ足しも同じ）
local WAYS = [["ami_rail_ballast", null], ["ami_rail_concrete", null], ["ami_rail_slab", null], ["ami_tram", null], ["ami_rail_ballast_base_single", "ami_wall_rail_single_catenary"], ["ami_rail_ballast_base_back", "ami_wall_rail_back_catenary"], ["ami_rail_ballast_base_center", "ami_wall_rail_center_catenary"], ["ami_rail_ballast_base_front", "ami_wall_rail_front_catenary"]];
local OX = 150;
local OY = 20;
local SPACING = 40;
local SNOW_DX = 256;
local pl = player_x(0);
local marker = command_x(tool_set_marker);
local report = "";
local checks = "";
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
local pin = null;
try { pin = command_x(tool_set_switch_image); } catch (e) { pin = null; }
function rail_at(x, y) { return square_x(x, y).get_ground_tile().get_way(wt_rail); }
function img(x, y) { local w = rail_at(x, y); return w == null ? -1 : w.get_image_id(); }
// [名札, 根元の向き dx, dy, 固定の T字の列]
local DIRS = [["E", 1, 0, 0], ["W", -1, 0, 1], ["N", 0, -1, 2], ["S", 0, 1, 3]];

function lay(w, wo, ox, oy) {
  local s = "";
  local c = function(x, y) { return coord3d(ox + x, oy + y, 0); };
  local line = function(x0, y0, x1, y1) {
    local e = command_x.build_way(pl, c(x0, y0), c(x1, y1), w, true);
    if (e == null && wo != null) e = command_x.build_wayobj(pl, c(x0, y0), c(x1, y1), wo);
    return e;
  };
  // Y・3W: 両隣を先に 1 本で通してから根元と両隣の曲がりを足す（カーブになったタイルから 3 本目を足すと、つながりが崩れた）
  foreach (k, d in DIRS) {
    foreach (row, three in [false, true]) {
      // 1 つの local に , で並べて宣言すると、添字で読んだ値が狂った（local a = d[1], b = d[2] で b が 2 になる）ので、1 つずつ宣言する
      local cx = 4 + 10 * k;
      local cy = 4 + 10 * row;
      local fx = d[1];
      local fy = d[2];
      local sx = fy;
      local sy = -fx;
      s += r("sides", line(cx + sx, cy + sy, cx - sx, cy - sy));
      s += r("root", line(cx, cy, cx + 3 * fx, cy + 3 * fy));
      foreach (sg in [1, -1]) s += r("side run", line(cx + sg * sx, cy + sg * sy, cx + sg * sx - 3 * fx, cy + sg * sy - 3 * fy));
      if (three) s += r("through", line(cx, cy, cx - 3 * fx, cy - 3 * fy));
      s += r("label", marker.work(pl, c(cx + 2 * fx + 2 * sx, cy + 2 * fy + 2 * sy), (three ? "3W " : "Y ") + d[0]));
    }
  }
  // P: 固定の T字（nse・nsw・new・sew）と十字
  local TEES = [[0, -1, 0, 1, 1, 0], [0, -1, 0, 1, -1, 0], [-1, 0, 1, 0, 0, -1], [-1, 0, 1, 0, 0, 1]];
  foreach (j, v in [4, 3, 0]) {
    local py = 24 + 4 * j;
    foreach (k, t in TEES) {
      local px = 2 + 6 * k;
      s += r("P main", line(px + t[0], py + t[1], px + t[2], py + t[3]));
      s += r("P branch", line(px, py, px + t[4], py + t[5]));
    }
    local qx = 2 + 6 * 4;
    s += r("P ns", line(qx, py - 1, qx, py + 1));
    s += r("P ew", line(qx - 1, py, qx + 1, py));
    if (pin != null && v != 0) for (local k = 0; k <= 4; k++) s += r("pin", pin.work(pl, c(2 + 6 * k, py), "" + wt_rail + "," + v));
    s += r("label", marker.work(pl, c(0, py - 2), v == 0 ? "plain" : "pin " + v));
  }
  return s;
}

function check(name, ox, oy) {
  local s = "";
  if (pin == null) return "[check] " + name + " pin=none\n";
  foreach (k, d in DIRS) {
    // Y は選択肢 4（26〜29）、三方分岐は選択肢 3（31〜34）の同じ向きの T字と比べる
    foreach (row, three in [false, true]) {
      local got = img(ox + 4 + 10 * k, oy + 4 + 10 * row);
      local want = img(ox + 2 + 6 * d[3], oy + 24 + 4 * (three ? 1 : 0));
      local plain = img(ox + 2 + 6 * d[3], oy + 32);
      s += (three ? " 3W" : " Y") + d[0] + "=" + (got == plain ? "plain" : got == want ? "ok" : "got " + got + " want " + want);
    }
  }
  return "[check] " + name + s + "\n";
}

foreach (i, pair in WAYS) {
  local w = way_desc_x(pair[0]);
  local wo = pair[1] == null ? null : wayobj_desc_x(pair[1]);
  if (w == null || (pair[1] != null && wo == null)) { report += pair[0] + " desc=[missing]\n"; continue; }
  foreach (snow in [false, true]) {
    local ox = OX + (snow ? SNOW_DX : 0);
    local oy = OY + i * SPACING;
    report += r(pair[0] + " label", marker.work(pl, coord3d(ox, oy - 2, 0), pair[0] + (pair[1] == null ? "" : " + " + pair[1])));
    report += lay(w, wo, ox, oy);
    if (snow) report += r("climate", command_x(tool_set_climate).work(pl, coord3d(ox - 2, oy - 3, 0), coord3d(ox + 40, oy + SPACING - 4, 0), "7"));
    checks += check(pair[0] + (snow ? " snow" : ""), ox, oy);
  }
}
gui.close_all_windows();
return (report == "" ? "ok\n" : report) + checks;
