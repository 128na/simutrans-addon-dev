// 旧描画位置の基盤・壁・架線つきの壁の見本（#26。ingame/old_base.sh が撮る）。flat_512_left_v64.sve の温暖側 (20,20) 〜 で使う。
// 旧の線路 ami_rail_<TRACK>_old の基盤の版に、旧用の壁（ami_wall_rail_old_<版>）か架線つきの壁（..._catenary）を重ねる。
//   区画 1（y=20〜）: 単線 single + 壁 single（東西 12 タイル、行き止まり）
//   区画 2（y=30〜）: 複線 back（y=30）+ front（y=31）+ 壁 back・front（東西 12 タイル）
//   区画 3（y=40〜）: 区画 2 と同じ並びの架線つきの壁
//   区画 4・5（y=50〜・y=60〜）: 区画 2・3 の新描画位置の版（ami_rail_ballast_base_* と ami_wall_rail_*。新の pak を入れたときだけ。見比べる用）
// 1 行の文字列だけを使う（old_base.sh は行頭の空白と // の行を消して渡す）
local TRACK = "ami_rail_ballast_old";
local pl = player_x(0);
local out = "";
function r(name, v) { return name + "=" + (v == null ? "ok" : "[" + v + "]") + "\n"; }
function line(variant, y, wall, track = TRACK) {
  local w = way_desc_x(track + "_base_" + variant);
  local o = wayobj_desc_x(wall);
  if (!w.is_valid() || !o.is_valid()) return variant + " " + y + " missing\n";
  local s = "";
  s += r(variant + " way y=" + y, command_x.build_way(pl, coord3d(20, y, 0), coord3d(32, y, 0), w, true));
  s += r(variant + " wall y=" + y, command_x.build_wayobj(pl, coord3d(20, y, 0), coord3d(32, y, 0), o));
  return s;
}
out += line("single", 20, "ami_wall_rail_old_single");
out += line("back", 30, "ami_wall_rail_old_back");
out += line("front", 31, "ami_wall_rail_old_front");
out += line("back", 40, "ami_wall_rail_old_back_catenary");
out += line("front", 41, "ami_wall_rail_old_front_catenary");
out += line("back", 50, "ami_wall_rail_back", "ami_rail_ballast");
out += line("front", 51, "ami_wall_rail_front", "ami_rail_ballast");
out += line("back", 60, "ami_wall_rail_back_catenary", "ami_rail_ballast");
out += line("front", 61, "ami_wall_rail_front_catenary", "ami_rail_ballast");
gui.close_all_windows();
return out;
