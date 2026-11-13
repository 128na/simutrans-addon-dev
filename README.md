# Simutrans Addon Dev

Simutrans向けアドオンを新規開発・公開するためのmonorepoです。新しいアドオンは `addons/` 以下に追加します。

## リポジトリ構成

```text
addons/
  <addon-name>/    # アドオンごとに独立した開発プロジェクト
```

文書の置き場所（スキル・リファレンス・記録・ADR）は [docs/README.md](./docs/README.md) にあります。

各アドオンは、使用するツールやビルド手順に合わせて必要なファイルを持ちます。monorepo全体で特定の言語・パッケージマネージャー・ビルド方法を強制しません。追加時は [addons/README.md](./addons/README.md) の規約を確認してください。

## Makeobj

MakeobjにはPATHを通してあるため、アドオンのディレクトリから `makeobj` コマンドで実行できます。PowerShellで認識されることを確認するには次を実行します。

```powershell
Get-Command makeobj
```

`.dat` 定義からpakを作成する基本形式は次のとおりです。`<サイズ>` は対象のpaksetに合わせて指定してください。

```text
makeobj pak<サイズ> <出力pakファイル> <datファイル...>
```

例（pak128用）:

```powershell
makeobj pak128 .\dist\example.pak .\src\example.dat
```

入力画像など、`.dat` から参照されるファイルもMakeobjが読み込める位置に置いてください。各アドオンのREADMEに記載された個別のビルド手順がある場合は、そちらを優先します。

## 既存アーカイブ

このmonorepoの外にある以下のリポジトリは過去作成分のアーカイブです。

- `../iss` — インフラアドオン集
- `../rtx` — 道路・路面アドオン
- `../rtg` — 道路タイル画像生成ツール

仕様や制作手順の参考にはできますが、通常の開発対象ではありません。内容を移植する場合は、元リポジトリと対象アセットのライセンス、依存関係、互換性を個別に確認してください。

## AIコーディングツール

- **Codex**: リポジトリルートの [AGENTS.md](./AGENTS.md) に従います。
- **Claude Code**: リポジトリルートの [CLAUDE.md](./CLAUDE.md) から同じ `AGENTS.md` を読み込みます。

作業開始時に対象アドオンのREADMEや設定を確認し、そのアドオン固有の手順を優先してください。
