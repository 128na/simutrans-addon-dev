// iss と AMI の版ごとのカーブ・分岐の絵を、同じ配置で敷いて並べる検討用の見本（#88）。使い方は ingame/curve_switch_study.sh。
// SETS の 1 組（[名札, single, back, center, front の way]）ごとに、区画の原点 (OX, OY + 番号 * SPACING) から次を敷く:
//   corner y=2〜7: single の版。東へ 5、角を曲がって南へ 3、階段状の斜め 3 段、東へ 4（カーブの絵と斜めの絵）
//   x3     y=12 back・y=13 center・y=14 front の 3 本を東西に x=0〜16。x=4 で back↔center、x=8 で center↔front の渡り線（T字どうしを 1 タイルでつなぐ）
//   sid    x=12 で front から南へ側線（(12,15) で東へ曲がる）、x=14 で back から北へ側線（(14,11) で東へ曲がる）
//   dc     y=20 back・y=21 front の 2 本を東へ x=0〜6・0〜5、そこから南へ y=28 まで（複線のカーブ）
// 分岐の絵の判定は curve_switch_study.sh の CLASSIFY=1（固定の道具の効き目は次の呼び出しまで絵に出ないので、呼び出しを分ける）
// 名札は ASCII。行頭の空白と // で始まる行は curve_switch_study.sh が消して渡す
local SETS = [["iss", "iss_wtg_0240_single", "iss_wtg_0240_back", "iss_wtg_0240_center", "iss_wtg_0240_front"], ["ami", "ami_rail_ballast_base_single", "ami_rail_ballast_base_back", "ami_rail_ballast_base_center", "ami_rail_ballast_base_front"], ["amin", "ami_rail_ballast", "ami_rail_ballast", "ami_rail_ballast", "ami_rail_ballast"]];
local OX = 150;
local OY = 20;
local SPACING = 34;
local pl = player_x(0);
local marker = command_x(tool_set_marker);
local report = "";
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }

foreach (i, set in SETS) {
  local ox = OX;
  local oy = OY + i * SPACING;
  local ws = [];
  local missing = false;
  for (local k = 1; k <= 4; k++) { local d = way_desc_x(set[k]); if (d == null) missing = true; ws.append(d); }
  if (missing) { report += set[0] + " desc=[missing]\n"; continue; }
  local single = ws[0];
  local back = ws[1];
  local center = ws[2];
  local front = ws[3];
  local line = function(w, x0, y0, x1, y1) { return command_x.build_way(pl, coord3d(ox + x0, oy + y0, 0), coord3d(ox + x1, oy + y1, 0), w, true); };
  local s = "";
  s += r("label", marker.work(pl, coord3d(ox, oy, 0), set[0] + " " + set[1]));
  // corner
  s += r("c1", line(single, 0, 2, 5, 2));
  s += r("c2", line(single, 5, 2, 5, 4));
  foreach (st in [[5, 4, 6, 4], [6, 4, 6, 5], [6, 5, 7, 5], [7, 5, 7, 6], [7, 6, 8, 6], [8, 6, 8, 7], [8, 7, 12, 7]]) s += r("c3", line(single, st[0], st[1], st[2], st[3]));
  // x3: 先に 3 本を通してから、渡り線と側線を足す
  s += r("back", line(back, 0, 12, 16, 12));
  s += r("center", line(center, 0, 13, 16, 13));
  s += r("front", line(front, 0, 14, 16, 14));
  s += r("xbc", line(center, 4, 12, 4, 13));
  s += r("xcf", line(center, 8, 13, 8, 14));
  s += r("sid s", line(front, 12, 14, 12, 15));
  s += r("sid s2", line(front, 12, 15, 16, 15));
  s += r("sid n", line(back, 14, 12, 14, 11));
  s += r("sid n2", line(back, 14, 11, 17, 11));
  // 渡り線を敷くと両端のタイルがその way に置き換わるので、3 本を自分の way で敷き直す（つながりは残る）
  s += r("back again", line(back, 0, 12, 16, 12));
  s += r("center again", line(center, 0, 13, 16, 13));
  s += r("front again", line(front, 0, 14, 16, 14));
  s += r("label", marker.work(pl, coord3d(ox, oy + 10, 0), "back/center/front"));
  // dc
  s += r("dcb", line(back, 0, 20, 6, 20));
  s += r("dcb2", line(back, 6, 20, 6, 28));
  s += r("dcf", line(front, 0, 21, 5, 21));
  s += r("dcf2", line(front, 5, 21, 5, 28));
  report += s;
}
gui.close_all_windows();
return report == "" ? "ok" : report;
