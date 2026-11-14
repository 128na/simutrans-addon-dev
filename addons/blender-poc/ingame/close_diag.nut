// 近い斜め（1 タイルずらして並べた斜め。間隔はタイルの 1/√2）を見る見本。空の平らなマップ（flat2.sve など）の x=105 から右で使う。
// 行ごとに（y = 8 + 10 * i）、x=110 から南東へ下る組、x=160 から北東へ上る組。どちらも 1 本目が奥、x を 1 ずつずらした線が手前。
// - 壁の無い版（本体・旧・試作）: 近い斜めの絵（diagonal[close1]・[close2]）があるので、分け合うタイルは十字 1 本の way になる。
//   十字は東西と南北の直線を 1 本ずつ通して作る（カーブのタイルから 3 本目を足すと、つながりが崩れるため）。
//   南東へ下る組は、k ごとに東西 (k,k)→(k+2,k) と南北 (k+1,k-1)→(k+1,k+1)。(k+1,k) が十字になる
// - 道路・高速道路: 近い斜めの絵があるので、壁の無い線路と同じく十字で作る
// - 側壁・高架の版: 近い斜めの絵を持たないので、本体は分け合うタイルに 2 本の way を置く。奥の線を back、手前の線を front、
//   3 本なら真ん中を center にして、斜めの階段をそのまま build_way で敷く
// 名札は ASCII（MCP 経由の日本語は崩れる）
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
// [名札, 奥から順の way（1 つなら同じ way で 2 本、十字の作り）]
local ROWS = [["track", ["bpoc_track"]], ["old", ["bpoc_track_old"]], ["trial", ["bpoc_track_trial"]],
              ["wall back+front", ["bpoc_track_wall_back", "bpoc_track_wall_front"]],
              ["wall back+center+front", ["bpoc_track_wall_back", "bpoc_track_wall_center", "bpoc_track_wall_front"]],
              ["elev back+front", ["bpoc_track_elev_back", "bpoc_track_elev_front"]],
              ["elev back+center+front", ["bpoc_track_elev_back", "bpoc_track_elev_center", "bpoc_track_elev_front"]],
              ["road", ["bpoc_road"]], ["expressway", ["bpoc_expressway"]]];
local N = 6;
local pl = player_x(0);
local marker = command_x(tool_set_marker);
local out = "";
foreach (i, row in ROWS) {
  local oy = 8 + 10 * i;
  foreach (j, sy in [1, -1]) {
    local ox = 110 + 50 * j;
    local y0 = sy > 0 ? oy : oy + 7;
    if (row[1].len() == 1) {
      local w = way_desc_x(row[1][0]);
      local line = function(x0, y0, x1, y1) { return command_x.build_way(pl, coord3d(x0, y0, 0), coord3d(x1, y1, 0), w, true); };
      for (local k = 0; k < N; k++) {
        out += r(row[0] + " h" + k, line(ox + k, y0 + sy * k, ox + k + 2, y0 + sy * k));
        out += r(row[0] + " v" + k, line(ox + k + 1, y0 + sy * (k - 1), ox + k + 1, y0 + sy * (k + 1)));
      }
    }
    else {
      foreach (m, name in row[1]) {
        out += r(row[0] + " " + name, command_x.build_way(pl, coord3d(ox + m, y0, 0), coord3d(ox + m + N, y0 + sy * N, 0), way_desc_x(name), true));
      }
    }
  }
  out += r(row[0] + " label", marker.work(pl, coord3d(104, oy + 2, 0), row[0]));
}
gui.close_all_windows();
return out == "" ? "ok" : out;
