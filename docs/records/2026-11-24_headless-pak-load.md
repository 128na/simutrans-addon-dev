# 調査/作業ログ: 画面を出さない OTRP 本体で pak が読めるかを確かめる検査（#225）

（2026-11-24）

## 目的 / 発端

[#206](https://github.com/128na/simutrans-addon-dev/issues/206) の調査（`2026-11-24_blender-kit-survey.md`）で、外部の kit は headless の Simutrans で pak を読む自動テストを持つと分かった。今の AMI の確認は `addon_check` のゲーム（画面あり）でしか行っていない。
OTRP 本体（fork の `OTRP-KUTAv6`）を画面なしでビルドし、pak を読み込ませて、読み込みの誤り（足りない絵・壊れた pak）を見つけられるかを調べた。見た目とつなぎ目の確認は `addon_check` のまま。ここは「読めるか」だけ（[#225](https://github.com/128na/simutrans-addon-dev/issues/225)）。この issue では検査を入れず、作るなら別 issue にする。

調べた本体は fork の `OTRP-KUTAv6` の先端（`0ef69091f`）。本体のチェックアウトは触らず、`git worktree add` の一時の場所でビルドして、終わりに消した。読ませた pak は AMI の `dist/`（`ami*.pak` の 9 本。152 MB）と、`addon_check` の pak128 の写し。検証環境（`addon_check` など）には書いていない（pak128 を一時の場所に写した）。ゲームの MCP のポートは使っていない。

## 先に結論

- **できる。** 画面なしの本体は、Makefile の `BACKEND=posix` で作れる（Windows の MinGW で約 50 秒、`-j16`）。CMake の `SIMUTRANS_BACKEND=none` は、今は構成の段階で止まり使えない（下の「ビルド」）。
- **pak の読み込みは 3 秒で終わる**（pak128 と AMI の 8 本。`sim` が自分で終わる。終了コードは 0 で、誤りがあっても変わらない）。判定は終了コードでなく、出力の文字列と、読み込めた物の一覧で行う。
- **見つけられる誤り**: 空の pak・pak でないファイル、版の違うヘッダー、壊れたノードの種類（`skipping unknown -node`。makeobj が絵を読めなかった物も同じ）、名前の重複（`is overlaid`）、解決できない参照（`cannot resolve`、致命的）、pak そのものが読めない、など。
- **見つけられるが、出力の文字列だけでは足りない誤り**: 途中で切れた pak・バイトの壊れた pak。本体は **何も出さずに、その物を捨てる**（`read_file` の戻り値を呼び出し側が使わない）。読み込めた物の一覧（スクリプトの API。scenario）を、期待する一覧と比べると見つかる。
- **見つけられない誤り**: 絵の画素の破損、末尾が数バイト欠けた pak、必須の絵の書き忘れ（`image[ns][0]` を消した way）、空（透明）の絵、タイルの大きさの取り違え（pak64 の大きさで作った pak）。これらは読み込みでは通る。絵の見た目は `addon_check` に残す。
- **CI でも動かせそう。** 道具の置き場は、今ある `otrp:<ref>` の仕組み（`tools/ci/setup-makeobj.sh`）と同じ形にできる。pakset は fork の `tests/simutrans-test-base.zip`（16 MB）で足りる。Linux でのビルドの時間は下の表。
- **作る価値はある（中）。** 手元で 3 秒、CI で本体のビルド（キャッシュすれば 0）に pak の読み込み。ただし見つかるのは「読めない・名前の重複・参照切れ」で、AMI の `check.sh` と `makeobj` の ERROR 検査で通っていない物を見つける余地は小さい。別 issue の案は末尾。

## やったこと

1. 一時の worktree に `OTRP-KUTAv6` を取り出し、`config.default` に `BACKEND = posix`・`OSTYPE = mingw` を書いて、PowerShell から `make -j16`（`C:\msys64\mingw64\bin;C:\msys64\usr\bin` を `PATH` の先頭に足す）。
2. 検証用の作業フォルダを一時の場所に作り、`addon_check` の `pak128/`・`text/`・`font/`・`config/`・`script/` と DLL を写し、できた `sim.exe` と AMI の `dist/*.pak` を `addons/pak128/` に置いた。
3. `sim.exe -use_workdir -singleuser -objects pak128/ -addons -nosound -debug 3` を、標準入力を閉じて（`< /dev/null`）、`timeout 60` を付けて実行。出力は `-debug 3` の Message・Warning・ERROR。
4. 壊した pak を作って同じに実行（下の表）。壊し方は、AMI の `ami_canal`（way 1 本）を makeobj で pak にして、バイトを書き換える・切る・混ぜる。makeobj の入力（dat）を壊す物（絵のファイルが無い・絵の番号が範囲外・必須の絵のキーが無い・空の絵）と、参照切れの船（存在しない積荷）も作った。
5. 本体のスクリプトの API（scenario）で、読み込めた way の一覧を出し、`makeobj list` の一覧と比べた。
6. Linux でのビルドの時間は、Docker の `ubuntu:24.04`（`build-essential`・`libbz2-dev`・`libpng-dev`・`zlib1g-dev`・`libzstd-dev`）で測った。

## 分かったこと（事実）

### ビルド

| 項目 | 結果 |
|---|---|
| `make BACKEND=posix`（Windows の MinGW、`-j16`） | 成功。**50 秒**（きれいな worktree からの全部。`sim.exe` は約 11 MB）。`config.default` は `BACKEND=posix`・`OSTYPE=mingw`・`MULTI_THREAD=1`・`USE_ZSTD=1`・`USE_FREETYPE=0`。SDL・FreeType・フォントは要らない |
| Linux（`ubuntu:24.04` の Docker、`BACKEND=posix`、`OSTYPE=linux`） | 成功。`make -j24` が **28 秒**（apt の導入が別に 20 秒）。`sim` は約 9.7 MB。必要な物は `build-essential`・`libbz2-dev`・`libpng-dev`・`zlib1g-dev`・`libzstd-dev`・`pkg-config` だけ。`config.default` は `BACKEND=posix`・`OSTYPE=linux`・`MULTI_THREAD=1`・`USE_ZSTD=1`・`USE_FREETYPE=0` |
| CMake の `SIMUTRANS_BACKEND=none` | `none` の分岐は `CMakeLists.txt` にある（`display/simgraph0.cc`・`sys/simsys_posix.cc`・`COLOUR_DEPTH=0`）。ただし構成（`cmake -G "Unix Makefiles"`）が `No SOURCES given to target` で止まる。`build.md` 3 章の「CMake の一覧が実ファイルと合っていない」と同じ原因とみられる（原因の個所までは見ていない）。**`cmake/` は管理対象外**なので、CMake は使わず Make の `posix` を使う |
| 本体の CI | `otrp-automated-tests.yml` は `BACKEND=sdl2` でビルドする（SDL2・FreeType・miniupnpc・zstd 1.4.4 を入れる）。headless の検査には要らない |

### 実行（pak128 と AMI の `dist/` の 8 本。全部入りの `ami.pak` は除く）

- 所要 3 秒。出力は約 16,200 行。Warning も ERROR も出ない（`ami_rail_old.pak` を `ami_rail.pak` と同時に読んでも重複しない）。
- 最後は、`ERROR: modal_dialogue: called without a display driver => nothing will be shown!` が 1 行出て、世界を作り直して終わる。**これは正常な終わり方**（バナーを出せないため）。この行は無視する。終了コードは 0。
- 全部入りの `ami.pak` と種類別の pak を一緒に読むと、`Warning: object way::ami_canal is overlaid!` のような行が 180 行ほど出る（way 99・wayobj 27・crossing 19・tunnel 8・bridge 7・roadsign 6・building 6）。`ami.pak` は種類別の pak の全部入りなので当然。**重複の検査になる**（`dist/` を丸ごと読ませるときは、全部入りか種類別のどちらかに分ける）。
- AMI の way は、scenario の `way_desc_x.get_available_ways(wt, st)` で 137 本が出た。`makeobj list` の way 137 本と一致した。

### 壊した pak の結果

「読み込みの文字列」は、`-debug 3` の標準出力を探して見つかるか。「一覧の比較」は、scenario で way の一覧を出して期待と比べて見つかるか。

| 壊し方 | 読み込みの文字列 | 一覧の比較 |
|---|---|---|
| 空のファイル（0 バイト） | 見つかる: `ERROR: obj_reader_t::read_file(): unexpected end of file after 1 bytes while reading '…'!` | — |
| pak でないファイル（文字列） | 見つかる: 同じ `unexpected end of file` | — |
| ヘッダーの先頭 64 バイトを 0 に | 見つかる（弱い）: **`Message:` の行** `version of '…' is too old, … instead of 1003`。Warning でも ERROR でもない | 物が消える |
| ROOT ノードの大きさを壊す | 見つかる: `FATAL ERROR: obj_reader_t::read_node() - node of type ROOT must have size 0`。**そのあと終わらない**（60 秒の `timeout` で止めた。終了コード 124） | — |
| 存在しない積荷を参照する船（xref） | 見つかる: `FATAL ERROR: obj_reader_t::resolve_xrefs - cannot resolve 'GOOD-NoSuchGood_xyz'`。同じく終わらない | — |
| ランダムに 200 バイト書き換え | 見つかる（運しだい）: `Warning: obj_reader_t::read_nodes(): skipping unknown MG-node` | 物が消える |
| **ファイルの半分で切る** | **見つからない（何も出ない）** | **物が消える（見つかる）** |
| 末尾を 10 バイト切る | 見つからない | 見つからない（物は残る） |
| 中ほどの 16 バイトを反転（絵のデータ） | 見つからない | 見つからない（物は残る） |
| dat が指す絵のファイルが無い（makeobj が `ERROR: image_writer_t: cannot open …` を出して、小さい pak を書く） | 見つかる: `Warning: … skipping unknown -node`（名前なし） | — |
| dat の絵の番号が範囲外（makeobj が `invalid image number` を出す） | 見つかる: 同じ `skipping unknown -node` | — |
| dat から必須の絵（`image[ns][0]`）を消す | 見つからない | 見つからない（物は残る） |
| 絵の 1 マスを全部透明に | 見つからない | 見つからない（物は残る） |
| pak64 の大きさ（`makeobj pak64`）で作った pak を pak128 で読む | 見つからない | 見つからない |

### 本体の挙動（コードで確かめた）

- `descriptor/reader/obj_reader.cc` の `obj_reader_t::load` は、ディレクトリを読むとき `read_file(i);` の戻り値を使わない。`read_nodes`・`read_node_info` は、途中で読めなくなると **ログを出さずに `false` を返す**。子のノードの読み込みに失敗すると、その物は `delete` されて**登録されない**。これが「半分で切ると何も出ずに物が消える」理由。
- `finish_loading` の「Checking … objects」の `successfully_loaded()` は、種類ごとの必須物（積荷の `Passagiere` など）を見る。AMI の pak だけを読ませると `FATAL ERROR: successfully_loaded() - … goods_desc_t-object Passagiere not found.` で止まる。**pakset が要る。**
- OTRP は、起動のたびに前回の使用状況を外部へ送る（`network/otrp_log_sender.cc`。`settings.xml` に前回の記録が残っているときに送る）。headless の検査では、`settings.xml` を毎回消してから起動する（消せば `statistics log is not send.` と出て送らない）。**これを怠ると、検査のたびに外へ通信する。** この調査の 2 回目以降の実行で気づいた。1 回目から消すようにした後は送っていない（それまでに十数回、記録を付けた起動で送った）。
- `FATAL ERROR` の後、Windows の `sim.exe` は終わらず待つ（標準入力を閉じても）。**Linux（Docker の `ubuntu:24.04`）では `abort` で終わる（終了コード 134）**。どちらでも `timeout` は付ける。MSYS の `timeout` はまれに子の `sim.exe` を残した（手で消した）。CI の Linux では `timeout` が子を殺す。
- 「読み込めた物の一覧」を出す API はある（`way_desc_x.get_available_ways`、`get_available_tunnels`・`get_available_bridges`・`get_available_wayobjs`・`get_available_signs`・`get_available_stations`・`get_available_vehicles`）。scenario は、画面なしでも動く（`-scenario <名前>`。`pak/scenario/<名前>/scenario.nut` と地図 `empty-16x16.sve`。後者は fork の `tests/automated-tests/` にある）。**ゲームは終わらない**（`-until` は効かなかった）ので、出力の合図（例: `PAKCHK done`）を待って、外から止める。出力は `script-scenario.log` と標準出力の両方に出る。
- 一覧で見えない種類もある。crossing（踏切）・building（車庫・駅の建物）・embankment（盛土）などには、一覧の API が無いか、条件が要る。一覧の比較で守れるのは way・橋・トンネル・架線・標識・車両・駅。それ以外は、読み込みの文字列だけ。

### pakset の最小

- pak128 全体（409 MB）を使わなくても読める。fork の `tests/simutrans-test-base.zip` の `pak/`（785 ファイル、16 MB。リポジトリに入っている）に AMI の pak を足すと、`ami_canal.pak` が読めて、AMI に関係する警告が出なかった（結果: `exit 0`。川の数・工場の警告は pakset の足りなさ）。
- この pakset は、絵の大きさが pak128 と同じか未確認（`ground.Outside.pak` の大きさを見ていない）。タイルの大きさの取り違えは見つけられない検査なので、この差は結果に響かないが、「pak128 で読めること」の保証にはならない。

## 推測・未確認事項

- GitHub Actions の runner でのビルドの時間（実機では測っていない。手元は 16 並列で 50 秒、Docker は 24 コアで 28 秒）。`actions/cache` に載せれば、本体のコミットが変わらない限りビルドは要らない。
- `tests/simutrans-test-base.zip` の pakset は、fork の更新で変わる。`otrp:<ref>` と同じく、タグかコミットで固定する。
- 一覧の比較を、way 以外（橋・トンネル・架線・標識・車両・駅）にも広げたときの手間。API はある。
- 壊れ方のうち、画素・欠け・空の絵を見つけるには、pak 自体の解析（ノードの木を読んで、絵のノードの大きさを見る Python）が要る。ゲームの出番ではないので、この issue では調べなかった。

## 結果どうしたか

この issue（#225）では検査を入れない。結論は「できる。ただし見つかるのは読めない・重複・参照切れ・（一覧と比べると）捨てられた物。見た目は `addon_check`」。

### 手元での作り方の案

1. 本体（`BACKEND=posix`）は 1 回ビルドして `sim` を置く（`otrp:<ref>` と同じく、コミットかタグで固定する）。`ci.env` に `SIM_HEADLESS=otrp:<ref>` のように書く。
2. 一時の作業フォルダを作り、pakset（`tests/simutrans-test-base.zip`）を展開して、AMI の `dist/` の pak（`ami.pak` と種類別の pak のどちらか）を `addons/pak/` に置く。`settings.xml` は置かない（置いてあれば消す）。
3. `sim -use_workdir -singleuser -objects pak/ -addons -nosound -debug 3 < /dev/null` を `timeout 60` 付きで実行し、出力を次の文字列で探す。1 つでもあれば失敗: `^FATAL ERROR`・`^ERROR: obj_reader`・`skipping unknown`・`is overlaid`・`too old`・`Reading addon object data failed`・`cannot resolve`・タイムアウト。`ERROR: modal_dialogue: called without a display driver` は期待する行。
4. 第 2 段（任意）: scenario で way（と橋など）の一覧を出し、`makeobj list` の一覧と比べる。足りない物があれば失敗。

### CI での作り方の案

- `addon-ami.yml` に、`check.sh` の後（pak ができた後）の段を足す。本体のビルドは `actions/cache`（キーは本体のコミット）に載せ、当たれば飛ばす。
- 本体のビルドに要る物: `build-essential`・`libbz2-dev`・`libpng-dev`・`zlib1g-dev`・`libzstd-dev`・`pkg-config`（SDL・FreeType は要らない）。上の Docker での確認が通っている（コンテナは 24 コアで測った。GitHub の runner は 4 コア前後なので、数分を見込む。未測定）。
- 検査は `addons/ami/` の下にスクリプトを 1 本置き、`check.sh` から呼ぶ（手元と CI が同じ検査になる、という今の作りを守る）。

### 別 issue の案（`next`）

1. **「AMI の pak を headless の本体で読む検査を `check.sh` に足す」**（作る。上の手元・CI の案 1〜3。第 2 段の一覧の比較は、way だけでまず足す）。受け入れ条件: 壊した pak 3 種（空・ROOT の大きさ・参照切れ）で失敗し、`dist/` の標準の 8 本で通る。CI の所要時間（キャッシュ当たり・外れ）を PR に書く。
2. **fork（`128na/simutrans`）に小さな PR を出す案**: `obj_reader_t::load` で `read_file` が `false` を返したとき `dbg->warning` を出す（3 行）。これで「半分で切れた pak」が、一覧の比較なしで文字列で見つかる。`cmake/` は触らない。**起票は fork の issue**（本体の変更なので、ユーザーに確認してから）。
3. **（低）** pak のノードの木を読む Python の検査で、空の絵・欠けた絵・末尾の欠けを見つける。headless の本体とは別の道具。必要が出てから。
