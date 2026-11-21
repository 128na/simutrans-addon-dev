// AMI の道路標識の見本（#122）: 6 種を、南北と東西の一般道路（ami_road_general）に置く。一方通行は 1 回・2 回置いて向きを変える。
// 検証用の flat_512.sve に、温暖側 (20,24) と降雪側 (276,24) の 2 か所へ同じ並びで置く。降雪側は置いた後に一帯を降雪に塗り直す。
// 使い方（アドオンのディレクトリで）: GAME_DIR=<検証用のフォルダ> EXE=OTRPv64_3.exe PORT=47300 EXTRA_TEXTS=release/text/ja_ami.tab bash ingame/game.sh で起動し、
// PORT=47300 NUT=ingame/roadsign_sample.nut bash ingame/game.sh RUN で流す。撮る場所は README の「道路標識の作り」。
// 返り値の先頭が ok なら全部置けて、[check] で比べた値も期待どおり。違えば先頭が check で、「名前 場所=[…]」が続く。最後に確かめた値（[check] の行）が続く。
//
// 区画（原点 (ox,oy) から）:
//   N 南北の道路: (2+3i, 0)-(2+3i, 6) の 6 本。(2+3i, 3) に標識 i（SIGNS の順）
//   E 東西の道路: (0, 10)-(18, 10)。(2+3i, 10) に標識 i
//   O 一方通行の向き: 南北の道路 (22,0)-(22,6) の (22,2) に 1 回・(22,4) に 2 回、東西の道路 (20,10)-(28,10) の (22,10) に 1 回・(26,10) に 2 回
local SIGNS = ["ami_sign_one_way", "ami_sign_stop", "ami_sign_speed_40", "ami_sign_speed_60", "ami_sign_speed_80", "ami_sign_min_50"];
local ONE_WAY = "ami_sign_one_way";
local ROAD = "ami_road_general";
local ORIGINS = [[20, 24], [276, 24]];
local SNOW = 1;
local AREA = [30, 12];
local pl = player_x(0);
local marker = command_x(tool_set_marker);
local report = "";
local checks = "";
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }

function lay(ox, oy) {
  local road = way_desc_x(ROAD);
  if (road == null) return "road desc=[missing]\n";
  local desc = {};
  foreach (d in sign_desc_x.get_available_signs(wt_road)) desc[d.get_name()] <- d;
  foreach (n in SIGNS) if (!(n in desc)) return n + " desc=[missing]\n";
  local c = function(x, y) { return coord3d(ox + x, oy + y, 0); };
  local way = function(x0, y0, x1, y1) { return command_x.build_way(pl, c(x0, y0), c(x1, y1), road, true); };
  local sign = function(n, x, y, times = 1) {
    local e = null;
    for (local k = 0; k < times; k++) {
      local v = command_x.build_sign_at(pl, c(x, y), desc[n]);
      if (v != null) e = v;
    }
    return e;
  };
  local s = r("label", marker.work(pl, c(0, -3), "roadsign: N ns / E ew / O one way 1x 2x"));
  foreach (i, n in SIGNS) {
    s += r("N way " + i, way(2 + 3 * i, 0, 2 + 3 * i, 6));
    s += r("N " + n, sign(n, 2 + 3 * i, 3));
  }
  s += r("E way", way(0, 10, 18, 10));
  foreach (i, n in SIGNS) s += r("E " + n, sign(n, 2 + 3 * i, 10));
  s += r("O way ns", way(22, 0, 22, 6));
  s += r("O way ew", way(20, 10, 28, 10));
  s += r("O ns 1", sign(ONE_WAY, 22, 2, 1)) + r("O ns 2", sign(ONE_WAY, 22, 4, 2));
  s += r("O ew 1", sign(ONE_WAY, 22, 10, 1)) + r("O ew 2", sign(ONE_WAY, 26, 10, 2));
  // [check]: 置いた標識の名前・一方通行か、道の向き（dirs）と標識で絞った向き（masked）
  local expect = function(tag, x, y, want_name, want_masked) {
    local t = square_x(ox + x, oy + y).get_ground_tile();
    local w = t.get_way(wt_road);
    local o = t.find_object(mo_roadsign);
    local name = o == null ? "-" : o.get_desc().get_name();
    local masked = w == null ? -1 : w.get_dirs_masked();
    checks += "[check] " + tag + " (" + x + "," + y + ") sign=" + name + " one_way=" + (o == null ? "-" : o.get_desc().is_one_way())
              + " dirs=" + (w == null ? "-" : w.get_dirs()) + " masked=" + masked + "\n";
    local e = "";
    if (name != want_name) e += tag + " (" + x + "," + y + ") sign=[" + name + " want " + want_name + "]\n";
    if (masked != want_masked) e += tag + " (" + x + "," + y + ") masked=[" + masked + " want " + want_masked + "]\n";
    return e;
  };
  // 南北の道路は dirs=5（北 1 + 南 4）、東西は 10（東 2 + 西 8）。飾りの標識は向きを絞らない
  foreach (i, n in SIGNS) {
    s += expect("N", 2 + 3 * i, 3, n, n == ONE_WAY ? 4 : 5);
    s += expect("E", 2 + 3 * i, 10, n, n == ONE_WAY ? 8 : 10);
  }
  // 一方通行は 2 回置くと向きが逆になる（本体の試しで pak128 の NoEntry も同じ: 5→4・1、10→8・2）
  s += expect("O ns 1", 22, 2, ONE_WAY, 4) + expect("O ns 2", 22, 4, ONE_WAY, 1);
  s += expect("O ew 1", 22, 10, ONE_WAY, 8) + expect("O ew 2", 26, 10, ONE_WAY, 2);
  return s;
}

// 訳（release/text/ja_ami.tab を game.sh の EXTRA_TEXTS で入れたとき日本語になる。入れなければ名前のまま。比べずに出すだけ）
foreach (n in SIGNS) checks += "[check] tr " + n + "=" + translate(n) + "\n";
foreach (n, o in ORIGINS) {
  report += lay(o[0], o[1]);
  if (n == SNOW)
    report += r("climate", command_x(tool_set_climate).work(pl, coord3d(o[0] - 2, o[1] - 5, 0),
                                                             coord3d(o[0] + AREA[0], o[1] + AREA[1], 0), "7"));
}
gui.close_all_windows();
return (report == "" ? "ok\n" : "check\n" + report) + checks;
