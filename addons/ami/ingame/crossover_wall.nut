// 壁つきの線路を並べた間の渡り線（#101）。並べた線の間を階段の形（sample.nut の stair と同じ）の渡り線でつなぎ、
// 壁・架線つきの壁の way-object の絵の出方を見る。ingame/crossover_wall.sh がゲームの写しを起動して流す。
// 組（SETS。南へ SET_DY ずつ）: AMI の壁（ami_wall_rail_<版>）、AMI の架線つきの壁（_catenary）、iss の架線（壁を含む。手本）。
// 組の中の並び（南へ）: back+front・back+center・center+front・back+center+front の線（東西、x=0..14）。
//   渡り線は x=3 から南東へ（上の線 → 下の線）と、x=9 から北東へ（下の線 → 上の線）。
// 壁の敷き方（東へ MODE_DX ずつ）:
//   main … 壁を本線（東西）だけに敷く。渡り線の T字のタイルの壁は東西の向きのまま
//   all  … 本線に敷いた後、渡り線の経路にも同じ版の壁を敷く
//   late … 本線と壁を敷いた後に、上の線の版で渡り線を敷く（敷き直さない。下の線の T字のタイルは上の線の版に置き換わる）
//   plain … 本線と壁を敷いた後に、壁の無い通常の版（ami_rail_ballast。iss は iss_wtg_0240_single）で渡り線を敷く
//   relay … late の後に、本線をそれぞれの版で敷き直す（README の「壁の敷き方」で勧める手順。壁は敷き直さない）
// main・all の way は本線の版。渡り線は先に敷き、本線をそれぞれの版で敷き直す（渡り線を敷くと端のタイルがその way に置き換わる。リファレンスの 6 章）。
// 降雪側（x=256〜）に敷くときは crossover_wall.sh が OX に 256 を足す。降雪側なら敷いた後に一帯を降雪に塗る。
// 返り値: 失敗した所と、T字のタイルの way・壁の名前と向き（[t] の行）
local OX = 20;
local OY = 20;
local SET_DY = 22;
local MODE_DX = 20;
local pl = player_x(0);
local report = "";
function r(name, v) { if (v != null) report += name + "=[" + v + "]\n"; }
function c(x, y) { return coord3d(x, y, 0); }

local SETS = [
  {name = "ami_wall", way = "ami_rail_ballast_base_", wo = "ami_wall_rail_", wosuf = "", plain = "ami_rail_ballast"},
  {name = "ami_cat", way = "ami_rail_ballast_base_", wo = "ami_wall_rail_", wosuf = "_catenary", plain = "ami_rail_ballast"},
  {name = "iss_cat", way = "iss_wtg_0240_", wo = "iss_ot_new_position_catenary_", wosuf = "", plain = "iss_wtg_0240_single"},
];
local GROUPS = [["back", "front"], ["back", "center"], ["center", "front"], ["back", "center", "front"]];
local MODES = ["main", "all", "late", "plain", "relay"];

function stair(w, x, y, n, dy) {
  for (local k = 0; k < n; k++) {
    r("stair", command_x.build_way(pl, c(x + k, y + k * dy), c(x + k, y + (k + 1) * dy), w, true));
    r("stair", command_x.build_way(pl, c(x + k, y + (k + 1) * dy), c(x + k + 1, y + (k + 1) * dy), w, true));
  }
}
function stair_wo(wo, x, y, n, dy) {
  for (local k = 0; k < n; k++) {
    r("stair_wo", command_x.build_wayobj(pl, c(x + k, y + k * dy), c(x + k, y + (k + 1) * dy), wo));
    r("stair_wo", command_x.build_wayobj(pl, c(x + k, y + (k + 1) * dy), c(x + k + 1, y + (k + 1) * dy), wo));
  }
}
function wo_name(t) { local o = t.find_object(mo_wayobj); return o == null ? "-" : o.get_desc().get_name(); }

foreach (si, s in SETS) foreach (mi, m in MODES) {
  local x0 = OX + mi * MODE_DX;
  local y = OY + si * SET_DY;
  foreach (g in GROUPS) {
    local n = g.len();
    local wd = way_desc_x(s.way + g[0]);
    if (m == "main" || m == "all") {
      // 渡り線（上の線の版で敷く）→ 本線を版ごとに敷き直す → 本線に壁
      foreach (i, v in g) r(s.name + " " + v, command_x.build_way(pl, c(x0, y + i), c(x0 + 14, y + i), way_desc_x(s.way + v), true));
      stair(wd, x0 + 3, y, n - 1, 1);
      stair(wd, x0 + 9, y + n - 1, n - 1, -1);
      foreach (i, v in g) r(s.name + " relay " + v, command_x.build_way(pl, c(x0, y + i), c(x0 + 14, y + i), way_desc_x(s.way + v), true));
      foreach (i, v in g) r(s.name + " wo " + v, command_x.build_wayobj(pl, c(x0, y + i), c(x0 + 14, y + i), wayobj_desc_x(s.wo + v + s.wosuf)));
      if (m == "all") {
        stair_wo(wayobj_desc_x(s.wo + g[0] + s.wosuf), x0 + 3, y, n - 1, 1);
        stair_wo(wayobj_desc_x(s.wo + g[n - 1] + s.wosuf), x0 + 9, y + n - 1, n - 1, -1);
      }
    } else {
      // 本線と壁 → 渡り線（敷き直さない）
      foreach (i, v in g) r(s.name + " " + v, command_x.build_way(pl, c(x0, y + i), c(x0 + 14, y + i), way_desc_x(s.way + v), true));
      foreach (i, v in g) r(s.name + " wo " + v, command_x.build_wayobj(pl, c(x0, y + i), c(x0 + 14, y + i), wayobj_desc_x(s.wo + v + s.wosuf)));
      local sw = m == "plain" ? way_desc_x(s.plain) : wd;
      stair(sw, x0 + 3, y, n - 1, 1);
      stair(sw, x0 + 9, y + n - 1, n - 1, -1);
      if (m == "relay") foreach (i, v in g) r(s.name + " relay " + v, command_x.build_way(pl, c(x0, y + i), c(x0 + 14, y + i), way_desc_x(s.way + v), true));
    }
    // T字のタイル（向きが 3 本以上）の way と壁を出す
    for (local i = 0; i < n; i++) for (local x = x0; x <= x0 + 14; x++) {
      local t = square_x(x, y + i).get_ground_tile();
      local w = t.get_way(wt_rail);
      if (w == null) continue;
      local d = w.get_dirs();
      if (d == 7 || d == 11 || d == 13 || d == 14 || d == 15)
        report += "[t] " + s.name + " " + m + " (" + x + "," + (y + i) + ") dirs=" + d + " way=" + w.get_desc().get_name() + " wo=" + wo_name(t) + "\n";
    }
    y += n + 2;
  }
}
if (OX >= 256) r("climate", command_x(tool_set_climate).work(pl, c(OX - 2, OY - 2), c(OX + 5 * MODE_DX, OY + 3 * SET_DY), "7"));
gui.close_all_windows();
return report;
