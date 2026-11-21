// AMI の踏切の見本（#111）: 線路 4 種 × 道路 3 種の 12 組の踏切を、道路が南北の向き（H 線）と東西の向き（V 線）で敷く。
// 検証用の flat_512.sve に、温暖側 ORIGINS[0] と降雪側 ORIGINS[1] の 2 か所へ同じ並びで敷く。降雪側は敷いた後に一帯を降雪に塗り直す。
// 使い方（アドオンのディレクトリで）: ingame/crossing_sample.sh が流す。返り値の先頭が ok なら全部敷けた。続けて [check] の行。
//
// 区画（原点 (ox, oy)）:
//   H 線: 東西の線路 (0, 2)-(LEN, 2)。k 番目（k = 道路 × 4 + 線路）の踏切は x = START + k * SP で、南北の道路 (x, 0)-(x, 4) が横切る。
//         線路の種類は踏切の前後 (x - 3)-(x + 3) をその組の線路にする（踏切は線路と道路の速さで選ばれる）。名札は (x, -2)
//   V 線: 南北の線路 (VX, VY)-(VX, VY + LEN)。踏切は y = VY + START + k * SP で、東西の道路 (VX - 2, y)-(VX + 2, y) が横切る。名札は (VX + 3, y)
//   どちらの線も、始まりの端に車庫、START - 4 と LEN - 2 に駅を置く（閉じた絵を撮る列車は ingame/crossing_train.nut が走らせる）
// [check] の行: 踏切ごとに、線路と道路の way の名前と、両方が踏切になっているか（is_crossing）。踏切の物の名前は script から読めない
//   （crossing_t の get_name は固定の "Kreuzung"）ので、どの踏切が選ばれたかは画面で見る
local TRACKS = ["ami_rail_ballast", "ami_rail_concrete", "ami_rail_ladder", "ami_rail_slab"];
local ROADS = ["ami_road_local", "ami_road_general", "ami_road_expressway"];
local ORIGINS = [[20, 24], [276, 24]];
local SNOW = 1;
local START = 10, SP = 6;
local LEN = START + 12 * SP + 4;
local VX = 4, VY = 12;
local pl = player_x(0);
local marker = command_x(tool_set_marker);
local report = "";
local checks = "";
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
function short(n) { return n.slice(n.find("_", 4) + 1); }
function way_at(x, y, wt) { return square_x(x, y).get_ground_tile().get_way(wt); }
function state(x, y) {
  local t = way_at(x, y, wt_rail), d = way_at(x, y, wt_road);
  if (t == null || d == null) return "missing rail=" + (t != null) + " road=" + (d != null);
  return t.get_desc().get_name() + " x " + d.get_desc().get_name() + " crossing=" + (t.is_crossing() && d.is_crossing());
}

// 線を敷く。p(i) は線に沿って i 番目のタイルの座標（i = 0〜LEN）、q(i, s) はその i で横へ s ずらした座標
function lay_line(tag, p, q) {
  local s = "";
  local first = way_desc_x(TRACKS[0]);
  s += r(tag + " head", command_x.build_way(pl, p(0), p(START - 3), first, true));
  for (local k = 0; k < 12; k++) {
    local i = START + k * SP;
    local td = way_desc_x(TRACKS[k % 4]), rd = way_desc_x(ROADS[k / 4]);
    if (td == null || rd == null) { s += tag + " desc=[missing " + TRACKS[k % 4] + " " + ROADS[k / 4] + "]\n"; continue; }
    s += r(tag + " track " + k, command_x.build_way(pl, p(i - 3), p(k == 11 ? LEN : i + 3), td, true));
    s += r(tag + " road " + k, command_x.build_way(pl, q(i, -2), q(i, 2), rd, true));
  }
  return s;
}

function lay(ox, oy) {
  local s = "";
  local h = function(i) { return coord3d(ox + i, oy + 2, 0); };
  local hq = function(i, d) { return coord3d(ox + i, oy + 2 + d, 0); };
  local v = function(i) { return coord3d(ox + VX, oy + VY + i, 0); };
  local vq = function(i, d) { return coord3d(ox + VX + d, oy + VY + i, 0); };
  s += lay_line("H", h, hq);
  s += lay_line("V", v, vq);
  for (local k = 0; k < 12; k++) {
    local i = START + k * SP;
    local label = short(TRACKS[k % 4]) + "/" + short(ROADS[k / 4]);
    s += r("label H " + k, marker.work(pl, hq(i, -4), label));
    s += r("label V " + k, marker.work(pl, vq(i, 4), label));
    checks += "[check] H " + k + " (" + (ox + i) + "," + (oy + 2) + ") " + state(ox + i, oy + 2) + "\n";
    checks += "[check] V " + k + " (" + (ox + VX) + "," + (oy + VY + i) + ") " + state(ox + VX, oy + VY + i) + "\n";
  }
  return s;
}

foreach (n, o in ORIGINS) {
  report += lay(o[0], o[1]);
  if (n == SNOW)
    report += r("climate", command_x(tool_set_climate).work(pl, coord3d(o[0] - 4, o[1] - 6, 0),
                                                            coord3d(o[0] + LEN + 4, o[1] + VY + LEN + 4, 0), "7"));
}
gui.close_all_windows();
return (report == "" ? "ok\n" : "ng\n" + report) + checks;
