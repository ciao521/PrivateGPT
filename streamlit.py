import os
import shutil
from dotenv import load_dotenv
import streamlit as st
from embedchain import App
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from utilities import refresh_file
from drive_operations import upload_file_to_drive, fetch_files_from_drive

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


def main():
    st.set_page_config(page_title="Private ChatGPT", layout="wide")
    st.title("Private ChatGPT on Local Data or Google Drive")

    mode = st.sidebar.radio("データソース", ("ローカルデータ", "Google Drive"))
    if mode == "Google Drive":
        drive_mode()
    else:
        local_mode()


def drive_mode():
    if 'creds' not in st.session_state:
        st.info("まずは Google Drive 認証を行ってください。")
        if st.button("認証開始"):
            flow = Flow.from_client_config(
                client_config={
                    'web': {
                        'client_id': os.getenv('CLIENT_ID'),
                        'client_secret': os.getenv('CLIENT_SECRET'),
                        'redirect_uris': [os.getenv('REDIRECT_URI')],
                        'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                        'token_uri': 'https://oauth2.googleapis.com/token'
                    }
                },
                scopes=SCOPES,
                redirect_uri=os.getenv('REDIRECT_URI')
            )
            auth_url, _ = flow.authorization_url(
                prompt='consent',
                include_granted_scopes='true'
            )
            st.write(f"[認証用リンクを開く]({auth_url})")
            code = st.text_input("認証コードをここに貼り付け", key='drive_code')
            if code:
                flow.fetch_token(code=code)
                creds = flow.credentials
                st.session_state.creds = creds_to_dict(creds)
    else:
        creds = dict_to_creds(st.session_state.creds)
        service = build('drive', 'v3', credentials=creds)

        st.subheader("Drive ファイル一覧")
        files = fetch_files_from_drive(service)
        for f in files:
            st.write(f"{f['name']} ({f['mimeType']})")

        uploaded = st.file_uploader("Drive にアップロード", type=['pdf','txt','docx'])
        if uploaded:
            upload_file_to_drive(service, uploaded)

        chat_section(creds=creds, mode='drive')


def local_mode():
    st.subheader("ローカルデータモード")
    # sandbox フォルダへのアップロード機能
    uploaded_local = st.file_uploader("ローカルにアップロード (sandbox)", type=['pdf','txt','docx'])
    if uploaded_local:
        os.makedirs('sandbox', exist_ok=True)
        save_path = os.path.join('sandbox', uploaded_local.name)
        with open(save_path, 'wb') as f:
            f.write(uploaded_local.getbuffer())
        st.success(f"{uploaded_local.name} を sandbox に保存しました。")

    sandbox_files = refresh_file()
    selected = st.multiselect("対話に使用するファイルを選択", sandbox_files)
    chat_section(selected_files=selected, mode='local')


def chat_section(creds=None, selected_files=None, mode='local'):
    st.subheader("チャット")
    if 'emb_app' not in st.session_state:
        st.session_state.emb_app = App()
    emb_app = st.session_state.emb_app

    if mode == 'local' and selected_files:
        for f in selected_files:
            emb_app.add(file_path=os.path.join('sandbox', f), data_type='pdf')
    if mode == 'drive' and creds:
        service = build('drive', 'v3', credentials=creds)
        files = fetch_files_from_drive(service)
        for f in files:
            emb_app.add(file_id=f['id'], data_type='gdrive')

    query = st.text_input("質問を入力", key='query')
    if st.button("送信"):
        answer = emb_app.query(query)
        st.write(answer)


if __name__ == '__main__':
    main()