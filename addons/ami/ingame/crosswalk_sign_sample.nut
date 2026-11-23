// AMI の路面の横断歩道の標識の見本（#162）: 両方向と一方通行を、南北・東西の一般道路（ami_road_general）に置く。
// 検証用の flat_512_left.sve（左側通行）に、温暖側 (20,24) と降雪側 (276,24) へ同じ並びで置く。降雪側は置いた後に一帯を降雪に塗り直す。
// 使い方は roadsign_sample.nut と同じ（sample_parallel.sh に NUT・SPOTS・SAVE を渡して撮る）。
// 区画（原点 (ox,oy) から。標識の位置は道路の中ほど）:
//   A 南北の両方向 (2,0)-(2,6) の (2,3)、B 東西の両方向 (10,3)-(16,3) の (13,3)
//   C 南北の一方通行 (2,10)-(2,16) の (2,13) に 1 回（通れるのは南行き）、D 同 (6,10)-(6,16) の (6,13) に 2 回（北行き）
//   E 東西の一方通行 (10,13)-(16,13) の (13,13) に 1 回（西行き）、F 同 (10,16)-(16,16) の (13,16) に 2 回（東行き）。いずれも標識の向きは車の向きの反対
local TWO = "ami_sign_crosswalk";
local ONE = "ami_sign_crosswalk_one_way";
local ROAD = "ami_road_general";
local ORIGINS = [[20, 24], [276, 24]];
local SNOW = 1;
local AREA = [20, 20];
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
  foreach (n in [TWO, ONE]) if (!(n in desc)) return n + " desc=[missing]\n";
  local c = function(x, y) { return coord3d(ox + x, oy + y, 0); };
  local way = function(x0, y0, x1, y1) { return command_x.build_way(pl, c(x0, y0), c(x1, y1), road, true); };
  local sign = function(n, x, y, times = 1) {
    local e = null;
    for (local k = 0; k < times; k++) { local v = command_x.build_sign_at(pl, c(x, y), desc[n]); if (v != null) e = v; }
    return e;
  };
  local s = r("label", marker.work(pl, c(0, -3), "crosswalk sign: A ns / B ew / C,D ns one way / E,F ew one way"));
  s += r("A way", way(2, 0, 2, 6)) + r("A", sign(TWO, 2, 3));
  s += r("B way", way(10, 3, 16, 3)) + r("B", sign(TWO, 13, 3));
  s += r("C way", way(2, 10, 2, 16)) + r("C", sign(ONE, 2, 13, 1));
  s += r("D way", way(6, 10, 6, 16)) + r("D", sign(ONE, 6, 13, 2));
  s += r("E way", way(10, 13, 16, 13)) + r("E", sign(ONE, 13, 13, 1));
  s += r("F way", way(10, 16, 16, 16)) + r("F", sign(ONE, 13, 16, 2));
  local expect = function(tag, x, y, want_name, want_masked) {
    local t = square_x(ox + x, oy + y).get_ground_tile();
    local w = t.get_way(wt_road);
    local o = t.find_object(mo_roadsign);
    local name = o == null ? "-" : o.get_desc().get_name();
    local masked = w == null ? -1 : w.get_dirs_masked();
    checks += "[check] " + tag + " (" + x + "," + y + ") sign=" + name + " one_way=" + (o == null ? "-" : o.get_desc().is_one_way()) + " masked=" + masked + "\n";
    local e = "";
    if (name != want_name) e += tag + " sign=[" + name + " want " + want_name + "]\n";
    if (masked != want_masked) e += tag + " masked=[" + masked + " want " + want_masked + "]\n";
    return e;
  };
  s += expect("A", 2, 3, TWO, 5) + expect("B", 13, 3, TWO, 10);
  s += expect("C", 2, 13, ONE, 4) + expect("D", 6, 13, ONE, 1);
  s += expect("E", 13, 13, ONE, 8) + expect("F", 13, 16, ONE, 2);
  return s;
}

foreach (n, o in ORIGINS) {
  report += lay(o[0], o[1]);
  if (n == SNOW)
    report += r("climate", command_x(tool_set_climate).work(pl, coord3d(o[0] - 2, o[1] - 5, 0),
                                                             coord3d(o[0] + AREA[0], o[1] + AREA[1], 0), "7"));
}
gui.close_all_windows();
return (report == "" ? "ok\n" : "check\n" + report) + checks;
