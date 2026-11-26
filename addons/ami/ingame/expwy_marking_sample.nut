// AMI の高速道路の分岐・合流の路面表示（ami_mark_diverge_*・ami_mark_merge_*。#188）の見本。高速道路（ami_road_expressway）を敷き、表示を重ねる。
// 検証用の flat_512_left_v64.sve に、温暖側 (20,20) と降雪側 (276,20) の 2 か所へ同じ並びで敷き、降雪側は一帯を降雪に塗り直す。
// 使い方（アドオンのディレクトリで）: sample_parallel.sh に NUT=ingame/expwy_marking_sample.nut を付ける（撮る場所は sample_spots.sh の EXPWY_MARKING_SPOTS）。
// 返り値の先頭が ok なら全部敷けて、[check] で比べた名前と、表示のつながる向き（docs/objects/marking.md の「高速道路の分岐・合流の路面表示の作り」の形の表から導いた値）も期待どおり。違えば先頭が check で、「名前 場所=[…]」が続く。最後に [check] の行が続く。
// 敷き方は docs/objects/marking.md の「高速道路の分岐・合流の路面表示の作り」と同じ（f は進む向き、l は左。本線の列が l=0、ランプの列が l=1）:
//   分岐: 1. 本線を高速道路で敷く（反対の車道も l=-1 に） 2. ランプの道路を、分かれのマス（f=L）の本線から横の l=1 へ、そこから進む向き（直線か斜め）へ
//         3. 本線の列の f=0〜L を diverge_main で区間 4. ランプの列の f=0〜L を diverge_ramp で区間
//         5. f=1〜L の各マスで、本線とランプの列を diverge_ramp で横につなぐ 6. 本線の列の f=1〜L を diverge_main で 1 マスずつ敷き直す
//   合流: 分かれが f=0、テーパーが f=L。ランプの道路は後ろ（直線か斜め）から l=1 の f=0 へ来て、本線の f=0 へ横につなぐ。
//         表示は同じ順で、横につなぐのは f=0〜L-1、敷き直すのも本線の列の f=0〜L-1
// 区画（原点から。どれも、本線の列の f=0 のマスを中心 (x,y) に置く）:
//   DE・DS・DW・DN: 分岐（平行 1 マス、ランプは直線）。進む向きが東・南・西・北
//   ME・MS・MW・MN: 合流（同じ）
//   D0: 分岐の平行 0 マス、D2: 平行 2 マスでランプが斜め、M0: 合流の平行 0 マスでランプが斜め（どれも東行き）
local ORIGINS = [[20, 20], [276, 20]];
local SNOW = 1;
local AREA = [[-2, -2], [92, 70]];
// ラウンドの版（#56）: ami_mark_ で始まる名前の末尾に付ける。例: "_round1"。空なら今の名前（sample_parallel.sh の SUFFIX が置き換える）
local SUFFIX = "";
local X = "ami_road_expressway";
local DM = "ami_mark_diverge_main", DR = "ami_mark_diverge_ramp", MM = "ami_mark_merge_main", MR = "ami_mark_merge_ramp";
local pl = player_x(0);
local report = "";
local checks = "";
local OX = 0, OY = 0;
// 進む向き（地図の座標。y は南が正）と、その左
local FWD = {e = [1, 0], s = [0, 1], w = [-1, 0], n = [0, -1]};
function left(f) { return [f[1], -f[0]]; }
function r(name, v) { return v == null ? "" : name + "=[" + v + "]\n"; }
function c(x, y) { return coord3d(OX + x, OY + y, 0); }
function way(tag, n, p0, p1) {
  local w = way_desc_x(n.find("ami_mark_") == 0 ? n + SUFFIX : n);
  if (w == null) { report += n + " desc=[missing]\n"; return; }
  report += r(tag + " " + n, command_x.build_way(pl, c(p0[0], p0[1]), c(p1[0], p1[1]), w, true));
}
// 向き（地図の座標の単位ベクトル）を ribi（n=1, e=2, s=4, w=8）に
function rb(v) { return v[1] < 0 ? 1 : v[0] > 0 ? 2 : v[1] > 0 ? 4 : 8; }
function expect(tag, p, road, mark, dirs) {
  local t = square_x(OX + p[0], OY + p[1]).get_ground_tile();
  local w = t.get_way(wt_road), m = t.get_way(wt_rail);
  local rn = w == null ? "-" : w.get_desc().get_name(), mn = m == null ? "-" : m.get_desc().get_name();
  checks += "[check] " + tag + " (" + p[0] + "," + p[1] + ") " + rn + "/d" + (w == null ? "-" : w.get_dirs()) + " + " + mn + "/d" + (m == null ? "-" : m.get_dirs()) + "\n";
  if (rn != road || mn != mark) report += tag + " (" + p[0] + "," + p[1] + ") want=[" + road + " + " + mark + "] got=[" + rn + " + " + mn + "]\n";
  else if (dirs != null && m.get_dirs() != dirs) report += tag + " (" + p[0] + "," + p[1] + ") want=[d" + dirs + "] got=[d" + m.get_dirs() + "]\n";
}

// 分岐か合流を 1 つ。中心 (cx, cy)、進む向き d、平行のマスの数 npar、ランプが斜めなら diag
local CX = 0, CY = 0, FV = [1, 0], LV = [0, -1];
function P(f, l) { return [CX + FV[0] * f + LV[0] * l, CY + FV[1] * f + LV[1] * l]; }
function lay(tag, cx, cy, d, merge, npar, diag) {
  CX = cx; CY = cy; FV = FWD[d]; LV = left(FV);
  local L = npar + 1;                  // 分岐は分かれが f=L、合流はテーパーが f=L
  local split = merge ? 0 : L;
  local main = merge ? MM : DM, ramp = merge ? MR : DR;
  way(tag + " main", X, P(-4, 0), P(L + 4, 0));
  way(tag + " opposite", X, P(-4, -1), P(L + 4, -1));
  // ランプの道路: 分かれの本線 → 横 → 進む向き（合流は戻る向き）へ。斜めは横と進む向きを 1 マスずつ交互に
  local s = merge ? -1 : 1;
  way(tag + " ramp", X, P(split, 0), P(split, 1));
  if (diag) {
    local f = split, l = 1;
    for (local i = 0; i < 3; i++) {
      way(tag + " ramp", X, P(f, l), P(f + s, l)); f += s;
      way(tag + " ramp", X, P(f, l), P(f, l + 1)); l += 1;
    }
  } else {
    way(tag + " ramp", X, P(split, 1), P(split + s * 4, 1));
  }
  // 表示
  way(tag + " mark", main, P(0, 0), P(L, 0));
  way(tag + " mark", ramp, P(0, 1), P(L, 1));
  local f0 = merge ? 0 : 1, f1 = merge ? L - 1 : L;   // 横につなぐマス（テーパーのマスを除く）
  for (local f = f0; f <= f1; f++) way(tag + " link", ramp, P(f, 0), P(f, 1));
  for (local f = f0; f <= f1; f++) way(tag + " relay", main, P(f, 0), P(f, 0));
  // 表示のつながる向き（docs/objects/marking.md の「高速道路の分岐・合流の路面表示の作り」の形の表）: 前後のマスへ（区間の端は片側だけ）と、横につないだマスは本線の列が左・ランプの列が右
  local bk = rb([-FV[0], -FV[1]]), fw = rb(FV), lf = rb(LV), rt = rb([-LV[0], -LV[1]]);
  for (local f = 0; f <= L; f++) {
    local dd = (f > 0 ? bk : 0) | (f < L ? fw : 0), linked = f >= f0 && f <= f1;
    expect(tag + " main", P(f, 0), X, main, dd | (linked ? lf : 0));
    expect(tag + " ramp", P(f, 1), f == split ? X : "-", ramp, dd | (linked ? rt : 0));
  }
  expect(tag + " before", P(-1, 0), X, "-", null);
  expect(tag + " after", P(L + 1, 0), X, "-", null);
}

foreach (n, o in ORIGINS) {
  OX = o[0]; OY = o[1];
  lay("DE", 6, 8, "e", false, 1, false);
  lay("DS", 30, 4, "s", false, 1, false);
  lay("DW", 58, 8, "w", false, 1, false);
  lay("DN", 76, 14, "n", false, 1, false);
  lay("ME", 6, 30, "e", true, 1, false);
  lay("MS", 30, 26, "s", true, 1, false);
  lay("MW", 58, 30, "w", true, 1, false);
  lay("MN", 76, 36, "n", true, 1, false);
  lay("D0", 6, 54, "e", false, 0, false);
  lay("D2", 30, 54, "e", false, 2, true);
  lay("M0", 60, 54, "e", true, 0, true);
  if (n == SNOW)
    report += r("climate", command_x(tool_set_climate).work(pl, c(AREA[0][0], AREA[0][1]), c(AREA[1][0], AREA[1][1]), "7"));
}
gui.close_all_windows();
return (report == "" ? "ok\n" : "check\n" + report) + checks;
