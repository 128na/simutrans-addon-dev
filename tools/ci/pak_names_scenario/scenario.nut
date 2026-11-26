// 登録された物の名前を出すだけの scenario（tools/ci/check_pak_load.py が使う。#245）。
// 出力は「PAKNAMES <種類> <名前>」の行。種類は makeobj list の種類名（way・way-object・tunnel・bridge・roadsign・building）。
// 最後に「PAKNAMES done」を出す（check_pak_load.py が終わりの合図に使う）。地図 empty-16x16.sve は、128na/simutrans の 0ef69091f の tests/automated-tests/empty-16x16.sve の写し（Simutrans 本体と同じ Artistic License）。
map.file = "empty-16x16.sve"
scenario.short_description = "pak names"
scenario.author = "simutrans-addon-dev"
scenario.version = "0.1"
function get_rule_text(pl) { return ttext("x") }
function get_goal_text(pl) { return ttext("x") }
function get_info_text(pl) { return ttext("x") }
function get_result_text(pl) { return ttext("x") }
function is_tool_allowed(pl, tool_id, wt) { return true }

local done = false

function dump() {
  if (done) return
  done = true
  // 一覧は年表（timeline）で絞られる。年表が有効だと intro_year が先の物が出ないので、有効かを出して、検査の側で失敗にする
  print("PAKNAMES timeline " + (world.use_timeline() ? "on" : "off"))
  local wts = [wt_road, wt_rail, wt_water, wt_monorail, wt_maglev, wt_tram, wt_narrowgauge, wt_air, wt_power]
  foreach (wt in wts) {
    foreach (st in [st_flat, st_elevated, st_tram]) {
      foreach (d in way_desc_x.get_available_ways(wt, st)) print("PAKNAMES way " + d.get_name())
    }
    foreach (d in wayobj_desc_x.get_available_wayobjs(wt)) print("PAKNAMES way-object " + d.get_name())
    foreach (d in tunnel_desc_x.get_available_tunnels(wt)) print("PAKNAMES tunnel " + d.get_name())
    foreach (d in bridge_desc_x.get_available_bridges(wt)) print("PAKNAMES bridge " + d.get_name())
    foreach (d in sign_desc_x.get_available_signs(wt)) print("PAKNAMES roadsign " + d.get_name())
  }
  // 駅・車庫・桟橋・駅の拡張の建物は、どの種類を渡しても同じ一覧（station_building）が出る
  foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) print("PAKNAMES building " + d.get_name())
  // 名所の建物（AMI の盛土の建物は type=cur。#372）は、駅の一覧には出ない
  foreach (bt in [building_desc_x.attraction_land, building_desc_x.attraction_city]) {
    foreach (d in building_desc_x.get_building_list(bt)) print("PAKNAMES building " + d.get_name())
  }
  print("PAKNAMES done")
}

function start() { dump() }
function resume_game() { dump() }
