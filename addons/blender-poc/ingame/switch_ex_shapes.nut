// ex 画像（分岐の絵の 26–35 番）を本体が自動で選ぶ線路の形を敷く見本。空の平らなマップ（flat2.sve など）の y = 130 から下で使う。
// 本体の条件は boden/wege/weg.cc の select_switch_image と boden/grund.cc の is_use_track_wt_ex_image。
// blender-poc には ex 画像が無いので、絵は通常のまま。形を見るためのもの。
//   1 行目（y=135）Y字: T字の両側の隣がそろって同じ側へ曲がる（1 本が 2 本に開く）。ex（T字の向き, nw=false）
//   2 行目（y=155）三方: 十字の両側の隣がそろって同じ側へ曲がる（1 本が 3 本に開く）。ex（曲がる側と反対の T字の向き, nw=true）
//   3 行目（y=175）十字の東隣が西–北のカーブで、信号で西向きだけに絞ったもの。十字は ex（sew, nw=false）、西隣は switch の絵（x=40 は西隣が T字）
// 名札は ASCII（MCP 経由の日本語は崩れる）
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
local pl = player_x(0);
local w = way_desc_x("bpoc_track");
local marker = command_x(tool_set_marker);
local p = function(x, y) { return coord3d(x, y, 0); };
local out = "";
local line = function(x0, y0, x1, y1) { return command_x.build_way(pl, p(x0, y0), p(x1, y1), w, true); };

// [名札, 1 本側の向き dx, dy]。両側は (dy, -dx) と (-dy, dx)
local DIRS = [["E", 1, 0], ["W", -1, 0], ["N", 0, -1], ["S", 0, 1]];
foreach (k, d in DIRS) {
  foreach (row, three in [false, true]) {
    local cx = 20 + 20 * k;
    local cy = 135 + 20 * row;
    local fx = d[1];
    local fy = d[2];
    local sx = fy;
    local sy = -fx;
    // 両側を先に 1 本で通してから枝を足す（カーブになったタイルから 3 本目を足すと、つながりが崩れた）
    out += r("sides", line(cx + sx, cy + sy, cx - sx, cy - sy));
    out += r("single", line(cx, cy, cx + 3 * fx, cy + 3 * fy));
    foreach (sg in [1, -1]) {
      local ax = cx + sg * sx;
      local ay = cy + sg * sy;
      out += r("side run", line(ax, ay, ax - 4 * fx, ay - 4 * fy));
    }
    if (three) out += r("through", line(cx, cy, cx - 4 * fx, cy - 4 * fy));
    out += r("label", marker.work(pl, p(cx + 2 * fx + 2 * sx, cy + 2 * fy + 2 * sy), (three ? "3-way " : "Y ") + d[0]));
  }
}

// 3 行目: 十字 C、北と南へ直線、東隣は西–北のカーブで北へ。東隣に信号を置き、向きの制限を西だけにする。
// 西隣は x=20 では東–南のカーブ、x=40 では南北に通る T字（本体は西隣に switch の絵を付けるので、T字のほうが合う）
local signs = sign_desc_x.get_available_signs(wt_rail);
local sig = null;
foreach (s in signs) if (s.is_signal()) { sig = s; break; }
local sigtool = command_x(tool_build_roadsign);
foreach (k, west_t in [false, true]) {
  local cx = 20 + 20 * k;
  local cy = 175;
  out += r("ns", line(cx, cy - 4, cx, cy + 4));
  out += r("east", line(cx, cy, cx + 1, cy));
  out += r("east run", line(cx + 1, cy, cx + 1, cy - 4));
  if (west_t) out += r("west line", line(cx - 1, cy - 4, cx - 1, cy + 4));
  out += r("west", line(cx, cy, cx - 1, cy));
  if (!west_t) out += r("west run", line(cx - 1, cy, cx - 1, cy + 4));
  local masked = "";
  if (sig != null) {
    for (local i = 0; i < 4; i++) {
      local e = sigtool.work(pl, p(cx + 1, cy), sig.get_name());
      if (e != null) { out += r("signal", e); break; }
      local m = square_x(cx + 1, cy).get_ground_tile().find_object(mo_way).get_dirs_masked();
      masked = "" + m;
      if (m == dir.west) break;
    }
  }
  out += "crossover " + k + ": signal=" + (sig == null ? "none" : sig.get_name()) + " masked=" + masked + "\n";
  out += r("label", marker.work(pl, p(cx + 3, cy + 2), west_t ? "crossover (west T)" : "crossover (west curve)"));
}
gui.close_all_windows();
return out;
