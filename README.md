# html_update_notifier

このプロジェクトは、GitHubリポジトリ内の`site/`ディレクトリを監視し、重要な変更があった場合にDiscordに通知を送信するツールです。Google Generative AIを使用して変更内容を要約し、自然な文章で通知します。

---

## 機能概要

- **GitHubリポジトリ監視**: 指定したリポジトリ内の`site/`ディレクトリを監視します。
- **AIによる要約**: Google Generative AIを使用して変更内容を要約します。
- **重要性の判定**: AIが「重要ではない」と判断した変更は通知しません。
- **Discord通知**: 重要な変更があった場合に自然な文章で通知を送信します。

---

## 必要な環境

- Python 3.10以上
- GitHubリポジトリ
- Discord Webhook URL
- Google Generative AI APIキー

---

## トークンの取得方法

### 1. **Google Generative AI APIキーの取得**

1. [Google Cloud Console](https://console.cloud.google.com/)にアクセスします。
2. プロジェクトを作成または選択します。
3. **APIとサービス > 認証情報**に移動します。
4. **認証情報を作成 > APIキー**を選択し、APIキーを生成します。
5. 生成されたAPIキーをコピーし、`.env`ファイルの`GOOGLE_API_KEY`に設定します。

---

### 2. **Discord Webhook URLの取得**

1. Discordサーバーを開き、通知を送信したいチャンネルを選択します。
2. チャンネル名の横にある歯車アイコンをクリックします。
3. **インテグレーション > Webhook**に移動します。
4. **Webhookを作成**をクリックし、Webhook URLをコピーします。
5. コピーしたURLを`.env`ファイルの`DISCORD_WEBHOOK_URL`に設定します。

---

### 3. **GitHub Personal Access Tokenの取得**

1. [GitHubの設定ページ](https://github.com/settings/tokens)にアクセスします。
2. **トークン (クラシック) > トークンを生成**をクリックします。
3. 必要なスコープを選択します（`repo`スコープを推奨）。
4. 生成されたトークンをコピーし、GitHub Actionsのシークレットに設定します。

---

## 設定方法

### 1. **リポジトリのクローン**

```bash
git clone https://github.com/Altairu/html_update_notifier.git
cd html_update_notifier
```

### 2. **依存関係のインストール**

```bash
pip install -r requirements.txt
```

### 3. **`.env`ファイルの作成**

`.env.sample`をコピーして`.env`ファイルを作成し、以下のように設定します。

```plaintext
GOOGLE_API_KEY=あなたのGoogle APIキー
DISCORD_WEBHOOK_URL=あなたのDiscord Webhook URL
```

### 4. **GitHub Actionsのシークレット設定**

GitHubリポジトリの「Settings > Secrets and variables > Actions」に以下を追加します。

- `GOOGLE_API_KEY`: Google Generative AI APIキー
- `DISCORD_WEBHOOK_URL`: Discord Webhook URL
- `GITHUB_TOKEN`: GitHub Personal Access Token

---

## 使用方法

### 1. **ローカルでの実行**

以下のコマンドでスクリプトを実行します。

```bash
python main.py
```

### 2. **GitHub Actionsでの自動実行**

GitHub Actionsは、`.github/workflows/notify.yml`に基づいて毎時自動実行されます。

---

## ファイル構成

```
html_update_notifier/
├── main.py               # メインスクリプト
├── requirements.txt      # 必要なPythonパッケージ
├── .env.sample           # 環境変数のサンプル
├── LICENSE               # ライセンス情報
├── README.md             # このドキュメント
└── .github/
    └── workflows/
        └── notify.yml    # GitHub Actionsの設定
```

---

## ライセンス

このプロジェクトは[MITライセンス](LICENSE)の下で公開されています。
