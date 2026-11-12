# blender-poc

iss（Illustrator で作ったインフラアドオン）の作り方を Blender に置き換えられるかを確かめる検証用アドオンです。配布用ではありません。

- 対象: Simutrans 125.0 以降 / pak128（画像は iss と同じ 256px セルで作り、タイルの外へはみ出せる）
- ライセンス: 未定（検証用）。sis（CC BY-NC-SA）からはカメラの数値だけを参考にし、形状・素材・画像は使っていない

## 中身

| ファイル | 内容 |
|---|---|
| `blender/render.py` | Blender をコマンドで動かし、形状をスクリプトで組み立てて描画し、シート画像を作る |
| `blender/check.py` | 描画位置の検証。タイル菱形の位置と、iss の既存画像との描画範囲を比べる |
| `blender/preview.py` | 確認用の拡大画像 `work/preview.png` を作る |
| `src/track.dat` | 線路・新描画位置（道床が低い。今の pak128・iss）。セル配置は iss の線路と同じ |
| `src/track_old.dat` | 線路・旧描画位置（道床が高い。古い pak128・SIS）。形は `track.dat` と同じで、名前は `bpoc_track_old` |
| `src/tollbooth.dat` | 料金所風の建物（駅の付属建物扱い）。屋根がタイルからはみ出す |

## 必要なもの

- Blender 4.5 LTS（`D:\bin\blender\blender.exe` で確認）
- makeobj（PATH 上。60.12 で確認）

## ビルド

アドオンのディレクトリで:

```powershell
D:\bin\blender\blender.exe -b --factory-startup --python blender/render.py
cd src; makeobj pak256 ..\dist\bpoc.pak track.dat track_old.dat tollbooth.dat; cd ..
```

iss と同じく `pak256` で 256px セルとして切り出す（ゲームは pak128）。

位置の検証:

```powershell
D:\bin\blender\blender.exe -b --factory-startup --python blender/check.py -- ..\..\..\iss\src\way\rail\standard_slab.png
```

## 描画の決まりごと

- カメラ: 正投影、回転 X60° / Z45°（sis と同じ向き）。`ortho_scale = 20√2`、256px でタイル1辺10 → 菱形 128×64px
- 高さ1段 16px = Blender で約 2.041
- Blender の向き: +Y が北（画面右上）、+X が東（画面右下）
- タイル中心をセルの (128,128) に映す → dat オフセット `-64,-32`（線路）
  建物はカメラをずらして (128,192) に映す → `-64,-96`
- 線路はタイルの範囲で切り抜いて（Boolean）、隣のタイルとの継ぎ目をそろえる
- 線路の形はほぼ平ら（道床の厚み 0.12 ≈ 1px、レール上面 0.30 ≈ 2px）で、新・旧の描画位置で共通
- レールの間隔は iss・SIS と同じく画面上 6px（直線）。レール中心の間隔 0.934（1単位 ≈ 6.4px）
- 新描画位置と旧描画位置は、画面上の上下位置だけが違う。カメラを整数 px ずらして描き分ける（`render.py` の `TRACK_PROFILES`）。
  タイル中心を基準にして、新は 3px 下げ（iss に合わせる）、旧は 1px 上げ（SIS に合わせる）。
  iss と SIS のレールの位置を比べると、直線・斜め・坂のどの方位でも、画面上で 4〜4.5px 上下にずれているだけだった
- 斜めのタイルはレール・まくらぎの横幅を 2/√10（≈0.63）倍、道床を 0.8 倍にする。
  3D のまま描くと斜めは横幅が縮まずに映り、直線の約1.6倍太く見えるため（pak128 標準も斜めはレール間隔を細く描く）
- 後処理は iss と同じ: 特殊色にたまたま一致した画素は +1 ずらす。アルファ25未満は `#E7FFFF`、それ以外は不透明にする

## 検証結果（2026-11-12）

- タイル菱形の描画範囲 x64–191 / y96–159、坂は上端がちょうど 16px 上がる（期待どおり）
- 線路24セルを iss と照合（`check.py`）: 重心のずれ 12px 以内・傾きの向き一致で全セル OK。
  端の4セルは iss より端が短いぶん重心が 8〜10px ずれる（基準 12px 以内）
- カーブは描き方が違う: iss のカーブはタイル菱形の外まで描いている（x56〜199 / y92〜164）。
  隣のタイルにはみ出してマスクで消す作りなので、合わせるにははみ出しとマスクの仕組みが要る
- 分岐（T字）`nse`/`new`/`nsw`/`sew` は「直線＋枝へ両側から入るカーブ」、十字 `nsew` は「直線2本＋4方向のカーブ」。
  どちら側へ分かれても線がつながって見える。分岐部でまくらぎが交差する。
  田の字・菱形・十字の確認パターン（`flat.sve`）でゲーム内表示を確認（`docs/ingame_junctions*.png`）
- 全セル（線路29×2（新・旧）+ 建物4 + アイコン3）の描画からシート化まで約8秒
- makeobj で pak 化成功（警告なし）
- ゲーム内で表示を確認（Simutrans OTRP v62.4 / pak128、`docs/ingame.png`・`docs/ingame_detail.png`）:
  直線・端・分岐とカーブ・斜めの連続・坂（1段上げた土地への上り）が途切れずにつながる。
  料金所は屋根がタイルからはみ出して描かれる。iss と同じ `pak256` で作った pak がそのまま使える
- アイコンは iss に合わせた作り（緑のグラデーション背景＋大きめの絵＋線路は最高速度の数字）。
  128px で描いて 32px に縮小し、文字は Arial Bold（無ければ Blender 標準の字体）。
  ゲーム内のツールバーで確認済み（`docs/ingame_icon_track.png`・`docs/ingame_icon_tollbooth.png`）
- `ingame/place.nut` は `flat.sve`（平地だけのマップ）でも全項目成功
- pak128 標準の線路（Rail_100 / Rail_200）と並べて比較（`ingame/compare.nut`）:
  斜めのレール間隔はほぼ同じになった（`docs/compare_straight.png`・`docs/compare_diagonal.png`、
  直す前は `docs/compare_diagonal_before.png`）。標準より道床がやや狭く、砂利の質感が無い。
  並べて敷いただけでは上下位置のずれは分からない（下の「描画位置の描き分け」で確かめ直した）

### 描画位置の描き分け（2026-11-12）

- 描き分ける前の線路は、レールが SIS より 1px 低く、iss より約 3px 高かった。ほぼ旧描画位置にあった
- 描き分けの後、レールの間隔が基準より約 1.1px 広かった（直線 7.1px と 6.0px）ので、6px に詰めた。
  列ごとにレール2本の位置を比べると、旧と SIS・新と iss の差は直線・坂・斜めのどれも 0.4px 以内
- 描き分けた後、iss と照合（`check.py`）: 直線・端・坂・斜め・分岐は重心のずれ 0.7〜3.5px（端は 8.6〜9.8px）。
  カーブ `curve_sw`/`curve_ne` だけ 12.1px で基準の 12px をわずかに超えた。
  iss のカーブはタイルの外まで描く別の作りで、もともと差が大きいところ（上の「カーブは描き方が違う」）
- ゲーム内のつなぎ目（`ingame/seam.nut`。比べる線路 → 検証用の線路 → 比べる線路 の順に1本につなぐ）:
  - 旧描画位置と SIS（`way.SIS_ShinkansenTrack_Ballast_E01_ds.pak`）: 東西・南北の直線、斜め（SIS のカーブとの境目）、
    坂の下の境目で、2本のレールが段差なくつながった（`docs/seam_old.png`・`docs/seam_old_straight.png`・`docs/seam_old_detail.png`）。
    違いはレールの色合い（SIS は赤茶色）と、SIS が新幹線用でタイル全体が道床なこと
  - 新描画位置と pak128 標準 Rail_100: 目立つ段差は無い。ただし Rail_100 は道床の幅も模様も違い、
    レールも暗くて見分けにくいので、1〜2px の差までは判定できていない（`docs/seam_new.png`・`docs/seam_new_detail.png`）
  - 検証用のカーブが pak128 標準の斜めとつながる所では、カーブの丸みが大きく張り出して見える（`docs/seam_new.png` の中央）
- SIS は 1959 年登場だが、`flat.sve`（1930 年）でもスクリプトからは敷けた

## ゲーム内での確認

`addons/pak128/` に pak を置き、MCP 対応の OTRP 版をセーブ読み込みで起動して、`ingame/place.nut` を実行する。
手順は `simutrans` リポジトリの `simutrans-mcp-gui-debug` スキルと同じ。

```powershell
Copy-Item dist\bpoc.pak <Simutrans>\addons\pak128\
<OTRP版の実行ファイル> -objects pak128/ -addons -load flat -mcp-port 47123
python <simutrans>\.agents\skills\simutrans-mcp-gui-debug\scripts\mcp_client.py --port 47123 --run-squirrel (Get-Content -Raw ingame\place.nut) --capture work\ingame.png
```

- 付属建物（type=extension）は停留所の隣にしか置けない
- 昼夜が短い周期で切り替わるので、数秒おきに撮って明るいものを使う

未対応・未検証:

- iss の `*_ec.png`（赤 `#FF0000` を透過にするマスク）は移植していない。タイル外の切り落としは Boolean で代わりにした
- iss の奥／手前／中央／単線の作り分け（マスクで作っていたもの）。経路の横ずらしや切り抜き範囲の変更で作れる見込みだが未確認
- ポイントの向き別画像 `nse1`/`nse2` など（iss の4〜5行目）。OTRP は隣の線路の形を見て使い分ける（`weg_t::select_switch_image`）。
  無くても基本の分岐画像で表示される
- 雪景色、夜間の発光色、建物の前面画像（frontimage）
- 建物の向き0〜3と Simutrans の回転の対応
