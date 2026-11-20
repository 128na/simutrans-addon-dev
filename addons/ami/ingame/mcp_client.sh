# ingame/ のスクリプトが source して、MCP のクライアント（mcp_client.py）の場所を MCP_CLIENT に決める。
# 渡されていなければ、このリポジトリの隣の simutrans/（OTRP 本体の fork）の中を指す。
# worktree（.claude/worktrees/<名前>/）の中から動かしても届くように、git の共有のディレクトリ（本体の checkout の .git）から辿る。
# git が使えないときは、このスクリプトの場所からリポジトリの根を辿る（worktree の中では届かないので MCP_CLIENT を渡す）。
if [ -z "$MCP_CLIENT" ]; then
  _ingame=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
  _common=$(git -C "$_ingame" rev-parse --path-format=absolute --git-common-dir 2> /dev/null)
  if [ -n "$_common" ]; then _repo=$(dirname "$_common"); else _repo=$(cd "$_ingame/../../.." && pwd); fi
  MCP_CLIENT="$(dirname "$_repo")/simutrans/.agents/skills/simutrans-mcp-gui-debug/scripts/mcp_client.py"
  unset _ingame _common _repo
fi
[ -f "$MCP_CLIENT" ] || { echo "[mcp] MCP のクライアントが無い: $MCP_CLIENT（MCP_CLIENT で渡す）" >&2; exit 1; }
