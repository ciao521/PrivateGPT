import os
import shutil
from dotenv import load_dotenv
import streamlit as st
import asyncio

# ChromaDB SQLite3バージョンの問題を解決するためのコード
# これはembedchainをインポートする前に実行する必要があります
import sys
import subprocess
import importlib

def fix_sqlite():
    try:
        import sqlite3
        # SQLite3バージョンをチェック
        if sqlite3.sqlite_version_info < (3, 35, 0):
            st.warning(f"現在のSQLite3バージョンは{sqlite3.sqlite_version}です。ChromaDBには3.35.0以上が必要です。")
            st.info("pysqlite3-binaryをインストールしています...")
            
            # pysqlite3-binaryをインストール
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "pysqlite3-binary", "--quiet", "--disable-pip-version-check"
            ])
            
            # pysqlite3をインポートして標準ライブラリのsqlite3を置き換え
            __import__("pysqlite3")
            sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
            
            # 確認
            import sqlite3
            st.success(f"SQLite3バージョンが{sqlite3.sqlite_version}に更新されました。")
    except Exception as e:
        st.error(f"SQLite3の更新中にエラーが発生しました: {e}")
        st.info("代替の方法でアプリを実行します。一部の機能が制限される可能性があります。")

# Streamlit Cloudでの実行時のみSQLite問題を修正
if os.environ.get("IS_STREAMLIT_CLOUD", "false").lower() == "true":
    fix_sqlite()
elif not os.path.exists("/.dockerenv"):  # ローカル環境でのみ実行
    try:
        fix_sqlite()
    except:
        pass

# embedchainのAppクラスをインポート
try:
    from embedchain import App
except ImportError as e:
    st.error(f"embedchainライブラリのインポートに失敗しました: {e}")
    st.info("アプリの一部機能が利用できません。")
    
    # ダミーのAppクラスを定義してエラーを回避
    class App:
        def __init__(self, *args, **kwargs):
            pass
        
        def add(self, *args, **kwargs):
            st.error("embedchainライブラリが利用できないため、ドキュメントを追加できません。")
            return False
        
        def query(self, *args, **kwargs):
            st.error("embedchainライブラリが利用できないため、クエリを実行できません。")
            return "エラー: embedchainライブラリが利用できません。システム管理者に連絡してください。"

from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build
from utilities import refresh_file
from drive_operations import upload_file_to_drive, fetch_files_from_drive
import json
import traceback

# .env の読み込み
load_dotenv()

# Drive API のスコープ
SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive.readonly'
]

# クレデンシャルのシリアライズ／デシリアライズ関数
def creds_to_dict(creds):
    return {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    }

from google.oauth2.credentials import Credentials
def dict_to_creds(d):
    return Credentials(
        token=d['token'],
        refresh_token=d['refresh_token'],
        token_uri=d['token_uri'],
        client_id=d['client_id'],
        client_secret=d['client_secret'],
        scopes=d['scopes']
    )


def initialize_session_state():
    """Initialize session state variables if they don't exist yet"""
    if 'openai_api_key' not in st.session_state:
        st.session_state.openai_api_key = os.getenv("OPENAI_API_KEY", "")
    if 'google_client_id' not in st.session_state:
        st.session_state.google_client_id = os.getenv("CLIENT_ID", "")
    if 'google_client_secret' not in st.session_state:
        st.session_state.google_client_secret = os.getenv("CLIENT_SECRET", "")
    if 'google_redirect_uri' not in st.session_state:
        # ローカル開発用のリダイレクトURIをデフォルトに設定
        st.session_state.google_redirect_uri = os.getenv("REDIRECT_URI", "http://localhost:8501")
    if 'show_settings' not in st.session_state:
        st.session_state.show_settings = False
    if 'auth_flow' not in st.session_state:
        st.session_state.auth_flow = None

def save_settings_to_env():
    """Save the current settings to the .env file"""
    env_content = f"""OPENAI_API_KEY={st.session_state.openai_api_key}
CLIENT_ID={st.session_state.google_client_id}
CLIENT_SECRET={st.session_state.google_client_secret}
REDIRECT_URI={st.session_state.google_redirect_uri}"""
    
    # Streamlit Cloudでは.envファイルの書き込みをスキップ
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
    except Exception as e:
        st.warning("環境設定ファイルの保存に失敗しました。Streamlit Cloudでは設定は一時的にのみ保持されます。")
        print(f"Error saving .env file: {e}")
    
    # 現在のセッションの環境変数を直接設定
    os.environ["OPENAI_API_KEY"] = st.session_state.openai_api_key
    os.environ["CLIENT_ID"] = st.session_state.google_client_id
    os.environ["CLIENT_SECRET"] = st.session_state.google_client_secret
    os.environ["REDIRECT_URI"] = st.session_state.google_redirect_uri
    
    # 環境変数を強制的に再ロード
    load_dotenv(override=True)
    
    # すべてのモジュールで環境変数が利用可能になるよう、グローバルに設定
    import sys
    for module in list(sys.modules.values()):
        if hasattr(module, 'os') and hasattr(module.os, 'environ'):
            try:
                module.os.environ.update({
                    "OPENAI_API_KEY": st.session_state.openai_api_key,
                    "CLIENT_ID": st.session_state.google_client_id,
                    "CLIENT_SECRET": st.session_state.google_client_secret,
                    "REDIRECT_URI": st.session_state.google_redirect_uri
                })
            except Exception as e:
                print(f"Error updating environment variables in module: {e}")
    
    st.success("設定が保存され、環境変数に反映されました。")
    
def settings_section():
    """Render the settings section in the sidebar"""
    st.sidebar.title("設定")
    
    # Toggle button to show/hide settings
    if st.sidebar.button("設定を表示/非表示"):
        st.session_state.show_settings = not st.session_state.show_settings
    
    if st.session_state.show_settings:
        with st.sidebar.expander("API キー設定", expanded=True):
            st.session_state.openai_api_key = st.text_input(
                "OpenAI API キー", 
                value=st.session_state.openai_api_key,
                type="password"
            )
            
            st.session_state.google_client_id = st.text_input(
                "Google Client ID", 
                value=st.session_state.google_client_id,
                type="password"
            )
            
            st.session_state.google_client_secret = st.text_input(
                "Google Client Secret", 
                value=st.session_state.google_client_secret,
                type="password"
            )
            
            st.session_state.google_redirect_uri = st.text_input(
                "Google Redirect URI", 
                value=st.session_state.google_redirect_uri
            )
            
            if st.button("設定を保存"):
                save_settings_to_env()
                # 認証情報が変更されたので、認証状態をリセット
                if 'creds' in st.session_state:
                    del st.session_state['creds']
                if 'auth_flow' in st.session_state:
                    del st.session_state['auth_flow']
                st.experimental_rerun()

def main():
    st.set_page_config(page_title="Private ChatGPT", layout="wide")
    st.title("Private ChatGPT on Local Data or Google Drive")
    
    # Initialize session state for settings
    initialize_session_state()
    
    # Display settings section in sidebar
    settings_section()
    
    # Main mode selection
    mode = st.sidebar.radio("データソース", ("ローカルデータ", "Google Drive"))
    if mode == "Google Drive":
        drive_mode()
    else:
        local_mode()


def drive_mode():
    if 'creds' not in st.session_state:
        st.info("まずは Google Drive 認証を行ってください。")
        
        # Check if Google credentials are set
        if not st.session_state.google_client_id or not st.session_state.google_client_secret:
            st.warning("Google OAuth 認証情報を設定してください。")
            return
        
        auth_method = st.radio(
            "認証方法を選択してください",
            ["Webブラウザ認証", "認証コード入力"]
        )
            
        if st.button("認証開始"):
            try:
                client_config = {
                    'installed': {
                        'client_id': st.session_state.google_client_id,
                        'client_secret': st.session_state.google_client_secret,
                        'redirect_uris': ['urn:ietf:wg:oauth:2.0:oob', 'http://localhost'],
                        'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                        'token_uri': 'https://oauth2.googleapis.com/token'
                    }
                }

                if auth_method == "Webブラウザ認証":
                    # Webブラウザでの認証フローを環境変数のリダイレクトURIに合わせて設定
                    redirect_uri = st.session_state.google_redirect_uri
                    flow = Flow.from_client_config(
                        client_config={
                            'web': {
                                'client_id': st.session_state.google_client_id,
                                'client_secret': st.session_state.google_client_secret,
                                'redirect_uris': [redirect_uri],
                                'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                                'token_uri': 'https://oauth2.googleapis.com/token'
                            }
                        },
                        scopes=SCOPES,
                        redirect_uri=redirect_uri
                    )
                    auth_url, _ = flow.authorization_url(
                        access_type='offline',
                        prompt='consent',
                        include_granted_scopes='true'
                    )
                    st.session_state.auth_flow = flow
                    st.write(f"[認証用リンクを開く]({auth_url})")
                    st.info("上記リンクをクリックして認証を行ってください。認証後、指定されたリダイレクトURIにリダイレクトされます。")
                else:
                    # 手動認証コード入力フロー
                    flow = Flow.from_client_config(
                        client_config={
                            'web': {
                                'client_id': st.session_state.google_client_id,
                                'client_secret': st.session_state.google_client_secret,
                                'redirect_uris': ['urn:ietf:wg:oauth:2.0:oob', st.session_state.google_redirect_uri],
                                'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                                'token_uri': 'https://oauth2.googleapis.com/token'
                            }
                        },
                        scopes=SCOPES
                    )
                    auth_url, _ = flow.authorization_url(
                        access_type='offline',
                        prompt='consent',
                        include_granted_scopes='true'
                    )
                    st.session_state.auth_flow = flow
                    st.write(f"[認証用リンクを開く]({auth_url})")
                    st.info("上記リンクをクリックして認証を行い、表示される認証コードをコピーしてください。")
            except Exception as e:
                st.error(f"認証プロセスでエラーが発生しました: {str(e)}")
                st.write("詳細なエラー情報:")
                st.code(traceback.format_exc())

        if 'auth_flow' in st.session_state and st.session_state.auth_flow:
            code = st.text_input("認証コードをここに貼り付け", key='drive_code')
            if code:
                try:
                    st.session_state.auth_flow.fetch_token(code=code)
                    creds = st.session_state.auth_flow.credentials
                    st.session_state.creds = creds_to_dict(creds)
                    st.success("認証に成功しました！")
                    # クリーンアップ
                    del st.session_state.auth_flow
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"認証コードの処理でエラーが発生しました: {str(e)}")
                    st.write("詳細なエラー情報:")
                    st.code(traceback.format_exc())
    else:
        try:
            creds = dict_to_creds(st.session_state.creds)
            service = build('drive', 'v3', credentials=creds)

            st.subheader("Drive ファイル一覧")
            files = fetch_files_from_drive(service)
            if files:
                for f in files:
                    st.write(f"{f['name']} ({f['mimeType']})")
            else:
                st.info("アクセス可能なファイルがありません。")

            uploaded = st.file_uploader("Drive にアップロード", type=['pdf','txt','docx'])
            if uploaded:
                # Create a synchronous wrapper for the async function
                def sync_upload_to_drive(service, file):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        return loop.run_until_complete(upload_file_to_drive(service, file))
                    finally:
                        loop.close()
                
                file_id = sync_upload_to_drive(service, uploaded)
                st.success(f"ファイルがアップロードされました (ID: {file_id})")

            chat_section(creds=creds, mode='drive')
        except Exception as e:
            st.error(f"Google Drive接続エラー: {str(e)}")
            st.write("認証情報が無効になっているか、期限切れの可能性があります。再認証を行ってください。")
            # 認証情報をクリア
            if 'creds' in st.session_state:
                del st.session_state['creds']
            if st.button("再認証"):
                st.experimental_rerun()


def local_mode():
    st.subheader("ローカルデータモード")
    # Make sure sandbox directory exists
    try:
        os.makedirs('sandbox', exist_ok=True)
    except Exception as e:
        st.warning("sandboxディレクトリの作成に失敗しました。Streamlit Cloudではファイルアップロード機能が制限される場合があります。")
        print(f"Error creating sandbox directory: {e}")
    
    # sandbox フォルダへのアップロード機能
    uploaded_local = st.file_uploader("ローカルにアップロード (sandbox)", type=['pdf','txt','docx'])
    if uploaded_local:
        try:
            save_path = os.path.join('sandbox', uploaded_local.name)
            with open(save_path, 'wb') as f:
                f.write(uploaded_local.getbuffer())
            st.success(f"{uploaded_local.name} を sandbox に保存しました。")
            # Force session state refresh to show the new file
            if 'last_refresh' not in st.session_state:
                st.session_state.last_refresh = 0
            st.session_state.last_refresh += 1
        except Exception as e:
            st.error(f"ファイルの保存中にエラーが発生しました: {str(e)}")
            st.info("Streamlit Cloudでは一時的なファイル保存のみが可能です。")

    # Get the file list from sandbox directory
    try:
        sandbox_files = refresh_file()
        
        # Only show selection UI if there are files available
        if sandbox_files and len(sandbox_files) > 0:
            selected = st.multiselect("対話に使用するファイルを選択", sandbox_files)
            if selected:
                chat_section(selected_files=selected, mode='local')
        else:
            st.info("sandboxディレクトリにファイルをアップロードしてください。")
    except Exception as e:
        st.error(f"ファイル一覧の取得中にエラーが発生しました: {str(e)}")
        st.info("Streamlit Cloudでは、セッションごとに新しいファイルをアップロードする必要があります。")

def chat_section(creds=None, selected_files=None, mode='local'):
    st.subheader("チャット")
    
    # Check if OpenAI API key is set
    if not st.session_state.openai_api_key:
        st.warning("OpenAI API キーを設定してください。")
        return
        
    # Set OpenAI API key in environment for this session
    os.environ["OPENAI_API_KEY"] = st.session_state.openai_api_key
    
    # Initialize or update the embedchain App
    try:
        if 'emb_app' not in st.session_state:
            st.session_state.emb_app = App()
        emb_app = st.session_state.emb_app
    except Exception as e:
        st.error(f"Embedchain Appの初期化中にエラーが発生しました: {str(e)}")
        st.info("OpenAI API キーが正しく設定されているか確認してください。")
        return

    try:
        if mode == 'local' and selected_files:
            for f in selected_files:
                try:
                    # Using 'pdf_file' data type which is the correct type for embedchain
                    file_path = os.path.join('sandbox', f)
                    if not os.path.exists(file_path):
                        st.warning(f"ファイル {f} が見つかりません。")
                        continue
                    emb_app.add(source=file_path, data_type='pdf_file')
                except Exception as e:
                    st.warning(f"ファイル '{f}' の処理中にエラーが発生しました: {str(e)}")
        
        if mode == 'drive' and creds:
            try:
                service = build('drive', 'v3', credentials=creds)
                files = fetch_files_from_drive(service)
                if files:
                    for f in files:
                        try:
                            # Using 'google_drive_file' instead of 'gdrive'
                            emb_app.add(source=f['id'], data_type='google_drive_file')
                        except Exception as e:
                            st.warning(f"ファイル '{f['name']}' (ID: {f['id']}) の処理中にエラーが発生しました: {str(e)}")
                else:
                    st.info("処理するファイルがありません。")
            except Exception as e:
                st.error(f"Google Driveファイルの取得中にエラーが発生しました: {str(e)}")
                st.code(traceback.format_exc())
    except Exception as e:
        st.error(f"ファイル処理中にエラーが発生しました: {str(e)}")
        st.code(traceback.format_exc())

    query = st.text_input("質問を入力", key='query')
    if st.button("送信") and query:
        try:
            with st.spinner("回答を生成中..."):
                # Remove character limit by setting max_tokens parameter to a high value
                answer = emb_app.query(query, citations=False, max_tokens=4000)
                # Use a text area with expanded height to display the full response
                st.markdown("### 回答")
                st.markdown(answer)
        except Exception as e:
            st.error(f"クエリ処理中にエラーが発生しました: {str(e)}")
            st.write("詳細なエラー情報:")
            st.code(traceback.format_exc())
            st.info("OpenAI API キーが正しく設定されているか、また十分なクレジットがあるか確認してください。")

if __name__ == "__main__":
    main()
