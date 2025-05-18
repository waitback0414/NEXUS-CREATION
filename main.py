import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import time

# 必要なスコープ（Google Sheets + Drive）
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Streamlit secrets から認証 + スコープ設定
@st.cache_resource
def get_gspread_client():
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )
    return gspread.authorize(credentials)

# Google Sheets の情報
SPREADSHEET_KEY = "1tDCn0Io06H2DkDK8qgMBx3l4ff9E2w_uHl3O9xMnkYE"
SHEET_NAME = "従業員一覧"

# ログイン情報を取得
def get_login_data():
    client = get_gspread_client()
    sheet = client.open_by_key(SPREADSHEET_KEY).worksheet(SHEET_NAME)

    data = sheet.get_all_values()
    headers = data[1]  # 2行目をヘッダーに
    records = data[2:]  # 3行目以降がデータ

    return [{headers[i]: row[i] for i in range(len(headers))} for row in records]

# ログイン認証関数
def authenticate(user_id, password, login_data):
    for record in login_data:
        if record.get("MAIL") == user_id and record.get("PASS") == password:
            st.session_state["role"] = record.get("AUTHORITY", "user")  # 権限を記録（なければ user）
            return True
    return False

# アプリ本体
def main():
    st.title("ログインフォーム")

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        user_id = st.text_input("ログインID（メール）")
        password = st.text_input("パスワード", type="password")

        if st.button("ログイン"):
            try:
                login_data = get_login_data()
                if authenticate(user_id, password, login_data):
                    st.session_state.logged_in = True
                    st.success("ログイン成功！")
                    time.sleep(1)  # 成功メッセージを表示するための待機
                    # ユーザーの権限に応じてリダイレクト
                    st.session_state["username"] = record.get("NAME", "")
                    role = st.session_state.get("role", "user")
                    if role == "admin":
                        st.switch_page("pages/案件登録.py")
                    else:
                        st.switch_page("pages/業務報告.py")
                else:
                    st.error("ログインID または パスワードが間違っています。")
            except Exception as e:
                st.error(f"ログインエラー: {e}")
    else:
        st.success("ログイン済みです。")
        st.write("✅ ここにスプレッドシートの閲覧・編集機能を実装できます。")

        if st.button("ログアウト"):
            st.session_state.logged_in = False
            st.session_state.role = "user"

if __name__ == "__main__":
    main()
