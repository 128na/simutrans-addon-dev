// 試作の線路（bpoc_track_wall: 側壁）の全パターンの見本。all_dirs.nut と同じ形を x=20〜, y=120〜 に敷く。flat.sve で使う。
// 撮るときは gui.jump で (22,122) 行き止まり・(22,128) 輪・(31,129) 十字・(30,122) 斜め・(40,129) 坂。
function r(name, v) { return name + "=" + (v == null ? "ok" : "[" + v + "]") + "\n"; }
function pattern(label, w, x0, y0) {
  local pl = player_x(0);
  local s = "";
  local c = function(x, y, z = 0) { return coord3d(x0 + x, y0 + y, z); };
  // 行き止まり（東西・南北）と直線
  s += r(label + " ew", command_x.build_way(pl, c(0, 0), c(4, 0), w, true));
  s += r(label + " ns", command_x.build_way(pl, c(6, 0), c(6, 4), w, true));
  // カーブ4方向: 四角い輪
  s += r(label + " loop1", command_x.build_way(pl, c(0, 6), c(4, 6), w, true));
  s += r(label + " loop2", command_x.build_way(pl, c(4, 6), c(4, 10), w, true));
  s += r(label + " loop3", command_x.build_way(pl, c(4, 10), c(0, 10), w, true));
  s += r(label + " loop4", command_x.build_way(pl, c(0, 10), c(0, 6), w, true));
  // T字4方向と十字: 輪の中に十字を入れる
  s += r(label + " box1", command_x.build_way(pl, c(8, 6), c(14, 6), w, true));
  s += r(label + " box2", command_x.build_way(pl, c(14, 6), c(14, 12), w, true));
  s += r(label + " box3", command_x.build_way(pl, c(14, 12), c(8, 12), w, true));
  s += r(label + " box4", command_x.build_way(pl, c(8, 12), c(8, 6), w, true));
  s += r(label + " plus1", command_x.build_way(pl, c(11, 6), c(11, 12), w, true));
  s += r(label + " plus2", command_x.build_way(pl, c(8, 9), c(14, 9), w, true));
  // 斜め2系統（右下がり・右上がり）
  s += r(label + " dg1", command_x.build_way(pl, c(8, 0), c(12, 4), w, false));
  s += r(label + " dg2", command_x.build_way(pl, c(14, 4), c(18, 0), w, false));
  // 坂4方向: 中央1タイルを1段上げ、四方を坂にして十字に越える
  local cx = 20, cy = 9;
  s += r(label + " raise", command_x.set_slope(pl, c(cx, cy), slope.all_up_slope));
  s += r(label + " rampN", command_x.set_slope(pl, c(cx, cy - 1), 4));
  s += r(label + " rampS", command_x.set_slope(pl, c(cx, cy + 1), 36));
  s += r(label + " rampW", command_x.set_slope(pl, c(cx - 1, cy), 12));
  s += r(label + " rampE", command_x.set_slope(pl, c(cx + 1, cy), 28));
  // 斜め隣は中央側の角だけ上げて崖を無くす（北西・北東・南西・南東）
  s += r(label + " cornerNW", command_x.set_slope(pl, c(cx - 1, cy - 1), 3));
  s += r(label + " cornerNE", command_x.set_slope(pl, c(cx + 1, cy - 1), 1));
  s += r(label + " cornerSW", command_x.set_slope(pl, c(cx - 1, cy + 1), 9));
  s += r(label + " cornerSE", command_x.set_slope(pl, c(cx + 1, cy + 1), 27));
  s += r(label + " upNS", command_x.build_way(pl, c(cx, cy - 3), c(cx, cy + 3), w, true));
  s += r(label + " upEW", command_x.build_way(pl, c(cx - 3, cy), c(cx + 3, cy), w, true));
  return s;
}

local out = pattern("wall", way_desc_x("bpoc_track_wall"), 20, 120);
// 複線・3線: 奥だけ壁（back）・壁なし（bpoc_track）・手前だけ壁（front）を並べる。カメラは南東なので、東西の線路は北が奥、南北の線路は西が奥
local pl = player_x(0);
local wb = way_desc_x("bpoc_track_wall_back");
local wf = way_desc_x("bpoc_track_wall_front");
local wn = way_desc_x("bpoc_track");
out += r("dbl ew back", command_x.build_way(pl, coord3d(20, 140, 0), coord3d(26, 140, 0), wb, true));
out += r("dbl ew front", command_x.build_way(pl, coord3d(20, 141, 0), coord3d(26, 141, 0), wf, true));
out += r("dbl ns back", command_x.build_way(pl, coord3d(30, 138, 0), coord3d(30, 144, 0), wb, true));
out += r("dbl ns front", command_x.build_way(pl, coord3d(31, 138, 0), coord3d(31, 144, 0), wf, true));
out += r("tri ew back", command_x.build_way(pl, coord3d(20, 146, 0), coord3d(26, 146, 0), wb, true));
out += r("tri ew none", command_x.build_way(pl, coord3d(20, 147, 0), coord3d(26, 147, 0), wn, true));
out += r("tri ew front", command_x.build_way(pl, coord3d(20, 148, 0), coord3d(26, 148, 0), wf, true));
gui.close_all_windows();
return out;
