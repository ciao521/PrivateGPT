# PrivateGPT
## プロジェクト概要

このリポジトリは、ローカルのPDFファイルやGoogle Drive上のドキュメントをソースにした“Private ChatGPT”アプリケーションです。ユーザーはOAuth2でGoogleアカウントにログインし、Driveのファイルリストを取得・アップロードできるほか、ローカルの`sandbox`フォルダ内のファイルを埋め込み検索・対話できます。

主要機能:
- **ローカルデータモード**: `sandbox`フォルダ内のPDFを読み込み、Embedchainで埋め込みを作成
- **Google Driveモード**: OAuth2認証後、Drive APIを用いてファイル一覧取得およびアップロード
- **Web UI**: FastAPI + Jinja2テンプレート + TailwindCSS + Prelineによるシンプルなフロントエンド
- **WebSocketチャット**: ブラウザからメッセージを受け取り、埋め込み検索結果を返答

## 動作環境・前提条件

- Python 3.9以上
- Node.js (npm) 16以上
- Google Cloud Platform プロジェクト（Drive API 有効化済み）
- Google OAuth2 クライアントID／シークレット、リダイレクトURIの設定
- OpenAI APIキー（`embedchain`で利用）

## インストール手順
### 0.Google Cloud Console での準備
1. プロジェクトを作成
Google Cloud Console（https://console.cloud.google.com/ ）で新規プロジェクトを作成します。

2.Drive API を有効化
「API とサービス」→「ライブラリ」で “Google Drive API” を検索して有効化。

3.認証情報の作成
「認証情報」→「認証情報を作成」→「OAuth クライアント ID」を選択。
名前はわかりやすいものを。
「キーを追加」→ 「新しい鍵を作成」保存。その後、outhでwebapplicationからリダイレクトURLを設定する。そこで、環境変数に必要なCLIENT_ID,CLIENT_SECRETが画面に表示される。

### 1. リポジトリをクローン
```bash
git clone <このリポジトリのURL>
cd pp-main/pp-main
```

### 2. Python依存ライブラリのインストール
必要なパッケージを直接`pip`でインストールします。
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn google-auth google-auth-oauthlib google-api-python-client redis python-dotenv embedchain
```
> ※`requirements.txt`でもよい。
### 3. Node.js依存ライブラリのインストール
フロントエンドのビルドツール（TailwindCSS、Prelineなど）をインストールします。
```bash
npm install html2canvas preline tailwindcss
npx tailwindcss init
```

### 4. TailwindCSSのビルド設定
- `tailwind.config.js` は既にプロジェクト内にあります。入力ファイル（例: `static/styles.css`）を変える場合は適宜調整してください。
- ビルドコマンド例:
```bash
npx tailwindcss -i ./static/styles.css -o ./static/output.css --watch
```

## 環境変数の設定
ルートディレクトリに`.env`ファイルを作成し、以下を定義してください:
**フロントからも設定可能**
```dotenv
# OpenAI APIキー
OPENAI_API_KEY=sk-xxxxxxxxxxxx
# Google OAuth2
CLIENT_ID=あなたのクライアントID("client_id")
CLIENT_SECRET=あなたのクライアントシークレット("private_key")
REDIRECT_URI=http://localhost:8000/login/callback/
```

## ディレクトリ構造
```
pp-main/
├── app.py              # FastAPIアプリケーション定義
├── chat.py             # Embedchainを用いたローカル埋め込みロード
├── drive_operations.py # Google Drive API操作
├── file_list.py        # ローカルフォルダ一覧取得
├── google_auth_helpers.py # OAuth2フロー定義・セッション連携
├── utilities.py        # ユーティリティ関数（サイズ変換、フォルダパス等）
├── views.py            # HTTPルートでDriveデータ取得ロジック
├── templates/          # Jinja2テンプレート一式
├── static/             # CSS/JS/画像などの静的ファイル
└── tailwind.config.js  # TailwindCSS設定
```

## 起動方法
```bash
# Python 仮想環境を有効化した上で
streamlit run streamlit_app.py
```
もし認証時に問題が続く場合は、Google Cloud Consoleで以下の点も確認してください：

OAuth同意画面が正しく設定されているか
リダイレクトURIとして「http://localhost:8501」または「urn:ietf:wg:oauth:2.0:oob」が登録されているか
outhのリダイレクトが設定できれば、以下のような構成のjsonファイルを手に入れることができ。登録できる。
```
{"web":{"client_id":"758244136499-epb75q3ag32grpji8cfu4uf4sr3fiesg.apps.googleusercontent.com","project_id":"docs-455810","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"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","redirect_uris":["http://localhost:8500","http://localhost:8501","http://localhost:8501/api/outh/google-oauth/callback","http://localhost:8500/api/outh/google-oauth/callback"],"javascript_origins":["http://localhost:8501","http://localhost:8500"]}}
```

API有効化の状態（Google Drive APIが有効化されているか