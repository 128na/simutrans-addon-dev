// AMI の転車台・遷車台（ami_rail_turntable。#314）の見本。在来線（ami_rail_ballast）の行き止まりの隣に敷く。
// 検証用の flat_512_left_v64.sve に、温暖側 (20,20) と降雪側 (276,20) の 2 か所へ同じ並びで敷き、降雪側は一帯を降雪に塗り直す。
// 使い方（アドオンのディレクトリで）: sample_parallel.sh に NUT=ingame/turntable_sample.nut を付ける（撮る場所は sample_spots.sh の TURNTABLE_SPOTS）。
// 返り値の先頭が ok なら全部敷けて、[check] で比べた向きと絵も期待どおり（敷いたタイルの絵が空でない）。違えば先頭が check で、「名前=[…]」が続く。
// [info] の行は、線路を横切らせた試し（踏切になる。期待の値は決めない）。最後に確かめた値（[check] の行）が続く。
//
// 区画（原点 (ox,oy) から）:
//   TT 転車台: (3,2) の東西に線路の行き止まり（x 0〜2・4〜6）。(9,2) の南北に線路の行き止まり（桁は東西なので向きが合わない例）。(12,2) は単独
//   VN 南北の遷車台: x=17 の y 0〜6。西から東西の線路（x 13〜16）を y 0・2・4・6 に、東から（x 18〜21）を y 0・3・6 に突き当てる。台車は北の端 (17,0)
//   VE 東西の遷車台: y=11 の x 0〜8。北から南北の線路（y 7〜10）を x 0・3・6 に、南から（y 12〜15）を x 0・4・8 に。台車は西の端 (0,11)
//   VX 分かれ目: 十字（中心 (30,4)、腕 4 マス）・T 字（中心 (40,4)、南へ枝）・カーブ（(48,0)〜(48,4)〜(52,4)）
//   VC 試し: 南北の遷車台 x=56（y 0〜6）を、東西の線路（y=3、x 54〜58）で横切る
//   TI iss と並べる（#331）: 転車台を AMI (66,2)・iss (66,6) に、それぞれ東西の線路の行き止まり（x 64〜65・67〜68）の間に置く。
//     南北の遷車台を AMI x=71・iss x=73（y 0〜6）に置き、AMI の西（x 69〜70）と iss の東（x 74〜75）から y 0・3・6 に線路を突き当てる。
//     iss（iss_util_rail_misc.pak の iss_wrg_turntable_traverser）が無ければ iss の分は敷かず、[info] に書く（sample_parallel.sh の EXTRA_PAKS で足す）
// ラウンドの版（#56・#331）: SUFFIX を転車台の名前の末尾に付ける。線路には付けない（sample_parallel.sh の SUFFIX が置き換える）
local SUFFIX = "";
local ORIGINS = [[20, 20], [276, 20]];
local SNOW = 1;
local AREA = [[-3, -4], [78, 18]];
local TT = "ami_rail_turntable" + SUFFIX;
local ISS_TT = "iss_wrg_turntable_traverser";
local RAIL = "ami_rail_ballast";
local pl = player_x(0);
local report = "";
local checks = "";
local infos = "";
local OX = 0, OY = 0;
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
function c(x, y) { return coord3d(OX + x, OY + y, 0); }
function way(tag, n, x0, y0, x1, y1) {
  local w = way_desc_x(n);
  if (!w.is_valid()) { report += n + " desc=[missing]\n"; return; }
  report += r(tag + " " + n, command_x.build_way(pl, c(x0, y0), c(x1, y1), w, true));
}
// タイルの転車台の向き（get_dirs）が dirs で、絵が空でないか。違えば返り値に足す
function expect(tag, x, y, dirs) {
  local w = square_x(OX + x, OY + y).get_ground_tile().get_way(wt_road);
  local got = w == null ? "-" : w.get_desc().get_name() + " dirs=" + w.get_dirs() + " img=" + (w.get_image_id() == 4294967295 ? "empty" : "ok");
  checks += "[check] " + tag + " (" + x + "," + y + ") " + got + "\n";
  if (got != TT + " dirs=" + dirs + " img=ok") report += tag + " (" + x + "," + y + ")=[" + got + "]\n";
}

function lay() {
  // TT
  way("TT", RAIL, 0, 2, 2, 2); way("TT", RAIL, 4, 2, 6, 2);
  way("TT", TT, 3, 2, 3, 2);
  way("TT", RAIL, 9, 0, 9, 1); way("TT", RAIL, 9, 3, 9, 4);
  way("TT", TT, 9, 2, 9, 2);
  way("TT", TT, 12, 2, 12, 2);
  expect("TT", 3, 2, 0); expect("TT", 9, 2, 0); expect("TT", 12, 2, 0);
  // VN
  way("VN", TT, 17, 0, 17, 6);
  foreach (y in [0, 2, 4, 6]) way("VN w", RAIL, 13, y, 16, y);
  foreach (y in [0, 3, 6]) way("VN e", RAIL, 18, y, 21, y);
  expect("VN", 17, 0, 4); expect("VN", 17, 3, 5); expect("VN", 17, 6, 1);
  // VE
  way("VE", TT, 0, 11, 8, 11);
  foreach (x in [0, 3, 6]) way("VE n", RAIL, x, 7, x, 10);
  foreach (x in [0, 4, 8]) way("VE s", RAIL, x, 12, x, 15);
  expect("VE", 0, 11, 2); expect("VE", 4, 11, 10); expect("VE", 8, 11, 8);
  // VX
  way("VX+", TT, 26, 4, 34, 4); way("VX+", TT, 30, 0, 30, 8);
  way("VXT", TT, 36, 4, 44, 4); way("VXT", TT, 40, 4, 40, 8);
  way("VXL", TT, 48, 0, 48, 4); way("VXL", TT, 48, 4, 52, 4);
  expect("VX+", 30, 4, 15); expect("VXT", 40, 4, 14); expect("VXL", 48, 4, 3);
  // VC（試し）
  way("VC", TT, 56, 0, 56, 6);
  local e = command_x.build_way(pl, c(54, 3), c(58, 3), way_desc_x(RAIL), true);
  local t = square_x(OX + 56, OY + 3).get_ground_tile();
  local rw = t.get_way(wt_rail);
  infos += "[info] VC rail across (56,3): " + (e == null ? "built" : e) + " crossing=" + (rw == null ? "-" : rw.is_crossing()) + "\n";
  // TI（iss と並べる）
  local iss = way_desc_x(ISS_TT).is_valid();  // 無い名前でも null にならない（way-addon.md の 8.2）
  if (!iss) infos += "[info] TI " + ISS_TT + " desc=[missing]\n";
  foreach (i, n in iss ? [TT, ISS_TT] : [TT]) {
    local y = 2 + 4 * i, x = 71 + 2 * i;
    way("TI", RAIL, 64, y, 65, y); way("TI", RAIL, 67, y, 68, y);
    way("TI", n, 66, y, 66, y);
    way("TI", n, x, 0, x, 6);
    foreach (yy in [0, 3, 6]) way("TI", RAIL, i == 0 ? 69 : 74, yy, i == 0 ? 70 : 75, yy);
  }
  expect("TI", 66, 2, 0); expect("TI", 71, 0, 4);
}

foreach (n, o in ORIGINS) {
  OX = o[0]; OY = o[1];
  try { lay(); } catch (err) { report += "error=[" + err + "]\n"; }
  if (n == SNOW)
    report += r("climate", command_x(tool_set_climate).work(pl, coord3d(OX + AREA[0][0], OY + AREA[0][1], 0), coord3d(OX + AREA[1][0], OY + AREA[1][1], 0), "7"));
}
gui.close_all_windows();
return (report == "" ? "ok\n" : "check\n" + report) + infos + checks;
