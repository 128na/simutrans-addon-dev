// signal_sample.nut が走らせた列車と信号の状態を読む（#278）。値は signal_sample.nut と同じ（温暖側の原点 (20,20)、信号は P 線 (35,22)、Q 線 (35,28)）。
local out = "";
foreach (l in [["P", 35, 22], ["Q", 35, 28]]) {
  local sg = sign_x(l[1], l[2], 0);
  out += "[sig] " + l[0] + " state=" + (sg == null ? "none" : sg.get_state()) + "\n";
}
foreach (cnv in world.get_convoy_list()) {
  local p = cnv.get_pos();
  out += "[cnv] id=" + cnv.id + " pos=" + p.x + "," + p.y + " speed=" + cnv.get_speed() + " state=" + cnv.get_state() + "\n";
}
return out;
