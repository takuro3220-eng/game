# ASTRA LEGENDS — Godot iPhone Web Build

このリポジトリは ASTRA LEGENDS v10（Godot 4.7.2）の **iPhone横画面向けWebプレビュー配信** に使います。

## 準備（iPhoneだけで可能）
1. [ASTRA_LEGENDS_V10_SOURCE.zip](https://chatgpt.com/) をChatGPTの会話からiPhoneの「ファイル」にダウンロードする（リンク先はゲームそのものではありません）。
2. このGitHubリポジトリの **Add file → Upload files** から、`ASTRA_LEGENDS_V10_SOURCE.zip` を**解凍せず**にリポジトリ直下へアップロードし、Commit changesする。
3. **Settings → Pages → Build and deployment → Source** を **GitHub Actions** に設定する。
4. **Actions → Build Godot ZIP → Run workflow** またはZIPアップロード直後に始まる自動実行を確認する。
5. チェックがすべて成功すると `https://takuro3220-eng.github.io/game/` で起動できる。

> ソースZIP未配置の間はWeb公開されません。既存のWeb版をそのままNetlifyに置く手順とは異なります。

## 実装と品質
- Godot 4.7.2 GDScript、3D移動／戦闘／NPC／クエスト／タッチUIのソースをZIP内に同梱。
- GitHub Actionsで静的テスト→Godotインポート→ヘッドレス起動→Web書き出しを順次実行。
- **GitHub上でビルドが成功するまで「起動確認済み」とは扱いません。**
- 商用大作レベルのアート・モーション・シナリオとApp Storeネイティブ配信は未完成です。

ゲームはオリジナルです。3D素材ライセンスはソースZIP中の `ASSET_LICENSES.md` を参照してください。
