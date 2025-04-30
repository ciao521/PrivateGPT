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
```dotenv
# OpenAI APIキー
OPENAI_API_KEY=sk-xxxxxxxxxxxx
# Google OAuth2
CLIENT_ID=あなたのクライアントID
CLIENT_SECRET=あなたのクライアントシークレット
REDIRECT_URI=http://localhost:8000/login/callback/
# Redis (セッション管理用、不要ならコメントアウト)
REDIS_URL=redis://localhost:6379/0
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
