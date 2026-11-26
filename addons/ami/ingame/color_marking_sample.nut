// AMI の路面の色と黄色の中央線（ami_mark_paving_*・ami_mark_center_yellow。#313）の見本。一般道路（ami_road_general）を敷き、表示を重ねる。
// 検証用の flat_512_left_v64.sve に、温暖側 (20,20) と降雪側 (276,20) の 2 か所へ同じ並びで敷き、降雪側は一帯を降雪に塗り直す。
// 使い方（アドオンのディレクトリで）: sample_parallel.sh に NUT=ingame/color_marking_sample.nut を付ける（撮る場所は sample_spots.sh の COLOR_MARKING_SPOTS）。
// 返り値の先頭が ok なら全部敷けて、[check] で比べた名前も期待どおり。違えば先頭が check で、「名前 場所=[…]」が続く。最後に [check] の行が続く。
// 区画（原点から）:
//   PE: 東西の道路 5 本（y 2・5・8・11・14、x 0〜12）に、北から赤・青・緑・赤の縞・黄線を x 3〜9 に重ねる（直線と、区間の両端の行き止まり）
//   PN: 南北の道路 5 本（x 16・19・22・25・28、y 0〜14）に、西から同じ順で y 3〜10 に重ねる
//   PX: 十字（中心 (40,5)）に赤を十字に重ねる（腕は 3 マス）
//   PT: T字（中心 (55,5)、南へ枝）に青を重ねる（腕は 3 マス）
//   PI: iss の同じ物と並べる（#331）。東西の道路 5 本（y 2・5・8・11・14、x 62〜78）に、同じ順で AMI を x 64〜69、iss（iss_util_road_misc.pak）を
//     x 71〜76 に重ねる。iss の pak が無ければ iss の分は敷かず、[info] に書く（sample_parallel.sh の EXTRA_PAKS で iss の pak を足す）
// ラウンドの版（#56・#331）: SUFFIX を AMI の表示の名前（KINDS）の末尾に付ける。下の道路には付けない（sample_parallel.sh の SUFFIX が置き換える）
local SUFFIX = "";
local ORIGINS = [[20, 20], [276, 20]];
local SNOW = 1;
local AREA = [[-3, -4], [80, 18]];
local G = "ami_road_general";
local KINDS = ["ami_mark_paving_red", "ami_mark_paving_blue", "ami_mark_paving_green", "ami_mark_paving_red_striped", "ami_mark_center_yellow"];
foreach (i, k in KINDS) KINDS[i] = k + SUFFIX;
local ISS = ["iss_wsg_red_pavement", "iss_wsg_blue_pavement", "iss_wsg_green_pavement", "iss_wsg_red_striped_pavement", "iss_wsg_yellow_line"];
local pl = player_x(0);
local report = "";
local checks = "";
local infos = "";
local OX = 0, OY = 0;
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
function c(x, y) { return coord3d(OX + x, OY + y, 0); }
function way(tag, n, x0, y0, x1, y1) {
  local w = way_desc_x(n);
  if (w == null) { report += n + " desc=[missing]\n"; return; }
  report += r(tag + " " + n, command_x.build_way(pl, c(x0, y0), c(x1, y1), w, true));
}
// タイルの道路と表示の名前が want でなければ、返り値に足す
function expect(tag, x, y, road, mark) {
  local t = square_x(OX + x, OY + y).get_ground_tile();
  local w = t.get_way(wt_road), m = t.get_way(wt_rail);
  local rn = w == null ? "-" : w.get_desc().get_name(), mn = m == null ? "-" : m.get_desc().get_name();
  checks += "[check] " + tag + " (" + x + "," + y + ") " + rn + "/d" + (w == null ? "-" : w.get_dirs()) + " + " + mn + "/d" + (m == null ? "-" : m.get_dirs()) + "\n";
  if (rn != road || mn != mark) report += tag + " (" + x + "," + y + ") want=[" + road + " + " + mark + "] got=[" + rn + " + " + mn + "]\n";
}

foreach (n, o in ORIGINS) {
  OX = o[0]; OY = o[1];
  foreach (i, k in KINDS) {
    local y = 2 + 3 * i, x = 16 + 3 * i;
    way("PE", G, 0, y, 12, y);
    way("PE", k, 3, y, 9, y);
    foreach (p in [3, 6, 9]) expect("PE", p, y, G, k);
    expect("PE road", 1, y, G, "-");
    way("PN", G, x, 0, x, 14);
    way("PN", k, x, 3, x, 10);
    foreach (p in [3, 6, 10]) expect("PN", x, p, G, k);
    expect("PN road", x, 1, G, "-");
  }
  way("PX", G, 35, 5, 45, 5);
  way("PX", G, 40, 0, 40, 10);
  way("PX", KINDS[0], 37, 5, 43, 5);
  way("PX", KINDS[0], 40, 2, 40, 8);
  foreach (p in [[40, 5], [37, 5], [43, 5], [40, 2], [40, 8]]) expect("PX", p[0], p[1], G, KINDS[0]);
  way("PT", G, 50, 5, 60, 5);
  way("PT", G, 55, 5, 55, 10);
  way("PT", KINDS[1], 52, 5, 58, 5);
  way("PT", KINDS[1], 55, 5, 55, 8);
  foreach (p in [[55, 5], [52, 5], [58, 5], [55, 8]]) expect("PT", p[0], p[1], G, KINDS[1]);
  foreach (i, k in KINDS) {
    local y = 2 + 3 * i;
    way("PI", G, 62, y, 78, y);
    way("PI", k, 64, y, 69, y);
    expect("PI", 66, y, G, k);
    if (way_desc_x(ISS[i]) == null) { infos += "[info] PI " + ISS[i] + " desc=[missing]\n"; continue; }
    way("PI iss", ISS[i], 71, y, 76, y);
    expect("PI iss", 73, y, G, ISS[i]);
  }
  if (n == SNOW)
    report += r("climate", command_x(tool_set_climate).work(pl, c(AREA[0][0], AREA[0][1]), c(AREA[1][0], AREA[1][1]), "7"));
}
gui.close_all_windows();
return (report == "" ? "ok\n" : "check\n" + report) + infos + checks;
