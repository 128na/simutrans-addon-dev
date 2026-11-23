"""AMI のカタログ（見て回るための保存データ。#203）の配置。動いているゲーム（catalog.sh で起動）に、棚の 1 マスずつ流して敷く。

使い方（アドオンのディレクトリで。MCP_CLIENT は ingame/mcp_client.sh が決める）:
    python -X utf8 ingame/catalog.py --port 47500 [--only rail_new,road] [--side temperate|snow] [--list]
区画の割り付けは docs/reference/ami-catalog.md。温暖側は x=8〜、降雪側は同じ配置を x+512（土台の降雪側は x≥512）。
Squirrel のコードは長くなるので、MCP のクライアントの関数を直接呼び、棚の 1 マスずつ別の呼び出しで流す。
"""
import argparse
import importlib.util
import os
import re
import subprocess
import sys

SNOW_DX = 512
X0 = 8  # 棚の左端
PITCH = 14  # 棚の 1 マスの幅（マス）
CELL_H = 10

PRELUDE = r"""
local pl = player_x(0);
local report = "";
function r(n, v) { return v == null ? "" : n + "=[" + v + "]\n"; }
function wy(n) { local d = way_desc_x(n); if (d == null) report += "missing way " + n + "\n"; return d; }
function wo(n) { local d = wayobj_desc_x(n); if (d == null) report += "missing wayobj " + n + "\n"; return d; }
local SNOW = %(snow)d;
local OX = %(ox)d, OY = %(oy)d;
function c(x, y, z = 0) { return coord3d(OX + x, OY + y, z); }
function snow_fix(x0, y0, x1, y1) { if (SNOW) report += r("snow", command_x(tool_set_climate).work(pl, c(x0, y0), c(x1, y1), "7")); }
function set_slope(x, y, z, s) { local e = command_x.set_slope(pl, c(x, y, z), s); if (e == null && SNOW) snow_fix(x - 1, y - 1, x + 1, y + 1); return e; }
// 東西の直線 (0..n, y=4) に way を敷き、壁 wl（null なら無し）を重ねる。z は壁の高さ（高架は 2）。pier があれば真下に橋脚の way
function line(w, wall, n = 10, z = 0, pier = null, y = 4) {
  if (w == null) return;
  report += r("way " + w.get_name(), command_x.build_way(pl, c(0, y), c(n, y), w, true));
  if (wall != null) report += r("wall " + wall.get_name(), command_x.build_wayobj(pl, c(0, y, z), c(n, y, z), wall));
  if (pier != null) report += r("pier", command_x.build_way(pl, c(0, y), c(n, y), pier, true));
}
"""

# 棚の 1 マスの中身（Squirrel）。変数: w… は way_desc_x、wl… は way-object。
BRIDGE_NUT = r"""
local br = bridge_desc_x("%(bridge)s");
if (br == null) report += "missing bridge %(bridge)s\n";
else {
  report += r("bridge", command_x.build_bridge(pl, c(3, 4), c(9, 4), br));
  line(wy("%(way)s"), wo("%(wall)s"), 13);
}
"""
# トンネル（pak128 の坑口は 2 段の坂だけ）。尾根を 2 段上げ、両端を 2 段の坂にして掘り、前後に地上の way を敷く
TUNNEL_NUT = r"""
for (local x = 3; x <= 5; x++) for (local k = 0; k < 2; k++) report += r("raise", set_slope(x, 4, k, slope.all_up_slope));
report += r("rampW", set_slope(2, 4, 0, 24));
report += r("rampE", set_slope(6, 4, 0, 56));
report += r("tunnel", command_x(tool_build_tunnel).work(pl, c(2, 4), "%(tunnel)s"));
local d = wy("%(way)s");
if (d != null) {
  report += r("wayW", command_x.build_way(pl, c(0, 4), c(2, 4), d, true));
  report += r("wayE", command_x.build_way(pl, c(6, 4), c(8, 4), d, true));
  report += r("wall", command_x.build_wayobj(pl, c(0, 4), c(8, 4), wo("%(wall)s")));
}
"""


def line_nut(way, wall=None, n=10, z=0, pier=None):
    return 'line(wy("%s"), %s, %d, %d, %s);' % (
        way,
        'wo("%s")' % wall if wall else "null",
        n,
        z,
        'wy("%s")' % pier if pier else "null",
    )


def rail_cells(style, old):
    """線路 1 種類の棚（way・基盤 4 版＋壁・架線つき 4 版・高架 4 版・橋・トンネル・複線の壁）"""
    s = "ami_rail_" + style + ("_old" if old else "")
    wall = "ami_wall_rail_" + ("old_" if old else "")
    pier = "ami_pier_rail" + ("_old" if old else "")
    cells = [(s, line_nut(s))]
    for v in ("single", "back", "center", "front"):
        cells.append((f"{s}_base_{v}", line_nut(f"{s}_base_{v}", wall + v)))
    for v in ("single", "back", "center", "front"):
        cells.append((f"{s}_base_{v}+catenary", line_nut(f"{s}_base_{v}", wall + v + "_catenary")))
    for v in ("single", "back", "center", "front"):
        cells.append((f"{s}_elev_{v}", line_nut(f"{s}_elev_{v}", wall + v, 10, 2, pier)))
    cells.append((f"{s}_bridge", BRIDGE_NUT % {"bridge": s + "_bridge", "way": s + "_base_single", "wall": wall + "single"}))
    cells.append((f"{s}_tunnel", TUNNEL_NUT % {"tunnel": s + "_tunnel", "way": s + "_base_single", "wall": wall + "single_catenary"}))
    cells.append((f"{s}_twin", line_nut(f"{s}_base_single", wall + "twin")))
    cells.append((f"{s}_twin+catenary", line_nut(f"{s}_base_single", wall + "twin_catenary")))
    return cells


def road_cells(kind):
    s = "ami_road_" + kind
    cells = [(s, line_nut(s))]
    for v in ("single", "back", "center", "front", "twin"):
        cells.append((f"{s}_base_{v}" if v != "twin" else f"{s}_base_single+twin", line_nut(f"{s}_base_single" if v == "twin" else f"{s}_base_{v}", "ami_wall_road_" + v)))
    for v in ("center", "front", "twin"):
        base = "single" if v == "twin" else v
        cells.append((f"{s}_base_{base}+{v}_divider", line_nut(f"{s}_base_{base}", f"ami_wall_road_{v}_divider")))
    for v in ("single", "back", "center", "front"):
        cells.append((f"{s}_elev_{v}", line_nut(f"{s}_elev_{v}", "ami_wall_road_" + v, 10, 2, "ami_pier_road")))
    cells.append((f"{s}_bridge", BRIDGE_NUT % {"bridge": s + "_bridge", "way": s + "_base_single", "wall": "ami_wall_road_single"}))
    cells.append((f"{s}_tunnel", TUNNEL_NUT % {"tunnel": s + "_tunnel", "way": s + "_base_single", "wall": "ami_wall_road_single"}))
    return cells


# 帯（名前 → (y の原点, 棚の中身のリスト)）。1 帯 = CELL_H 行
def bands():
    out = {}
    y = 8
    for old in (False, True):
        for st in ("ballast", "concrete", "ladder", "slab"):
            out["rail_%s%s" % (st, "_old" if old else "")] = (y, rail_cells(st, old))
            y += CELL_H + 4
    for k in ("local", "general", "expressway"):
        out["road_" + k] = (y, road_cells(k))
        y += CELL_H + 4
    return out


def load_client():
    p = os.environ.get("MCP_CLIENT")
    if not p:
        common = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], capture_output=True, text=True).stdout.strip()
        repo = os.path.dirname(common)
        p = os.path.join(os.path.dirname(repo), "simutrans", ".agents", "skills", "simutrans-mcp-gui-debug", "scripts", "mcp_client.py")
    spec = importlib.util.spec_from_file_location("mcp_client", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def run_squirrel(m, port, code, timeout=300):
    sock = m.connect(["::1", "127.0.0.1"], port, 8.0)
    m.send(sock, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "catalog", "version": "1"}}})
    m.send(sock, {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "run_squirrel", "arguments": {"code": code, "player_nr": 0}}})
    resp = m.read_responses(sock, {1, 2}, timeout)
    sock.close()
    return m.content_text(resp[2])


def compact(code):
    return "\n".join(l.strip() for l in code.splitlines() if l.strip() and not l.strip().startswith("//"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--only", default="", help="帯の名前の前方一致（カンマ区切り）")
    ap.add_argument("--side", default="both", choices=["both", "temperate", "snow"])
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    bs = bands()
    if a.list:
        for name, (y, cells) in bs.items():
            for i, (cn, _) in enumerate(cells):
                print(f"{name}\ty={y}\tx={X0 + i * PITCH}\t{cn}")
        return 0
    only = [s for s in a.only.split(",") if s]
    m = load_client()
    fails = 0
    for side in (["temperate", "snow"] if a.side == "both" else [a.side]):
        for name, (y, cells) in bs.items():
            if only and not any(name.startswith(o) for o in only):
                continue
            for i, (cn, body) in enumerate(cells):
                ox = X0 + i * PITCH + (SNOW_DX if side == "snow" else 0)
                code = compact((PRELUDE % {"snow": 1 if side == "snow" else 0, "ox": ox, "oy": y}) + body + "\nsnow_fix(-1, 0, 13, 8);\nreturn report;")
                out = run_squirrel(m, a.port, code)
                ok = '"result":""' in out or out.strip() in ('{"result":""}', "")
                if not ok:
                    fails += 1
                print(("[ok] " if ok else "[NG] ") + f"{side} {name} {cn} ({ox},{y})" + ("" if ok else " " + out[:400]))
    print("failures:", fails)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
