# import streamlit as st
# import gspread
# from google.oauth2.service_account import Credentials

# SCOPES = [
#     "https://www.googleapis.com/auth/spreadsheets",
#     "https://www.googleapis.com/auth/drive"
# ]

# SPREADSHEET_KEY = "1tDCn0Io06H2DkDK8qgMBx3l4ff9E2w_uHl3O9xMnkYE"
# SHEET_NAME = "従業員一覧"

# try:
#     credentials = Credentials.from_service_account_info(
#         st.secrets["gcp_service_account"],
#         scopes=SCOPES
#     )
#     client = gspread.authorize(credentials)
#     sheet = client.open_by_key(SPREADSHEET_KEY).worksheet(SHEET_NAME)
#     st.success("認証と読み込みに成功しました！")
#     st.write(sheet.get_all_values())
# except Exception as e:
#     st.error(f"ログインエラー: {e}")

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

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
        scopes=SCOPES  # ← 🔴これが重要
    )
    return gspread.authorize(credentials)


# Google Sheets の情報
SPREADSHEET_KEY = "1tDCn0Io06H2DkDK8qgMBx3l4ff9E2w_uHl3O9xMnkYE"  # ←ここを自分のキーに置き換える
SHEET_NAME = "従業員一覧"  # ←タブ名


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
            st.session_state["role"] = record.get("AUTHORITY", "user")  # ← 権限を記録（なければ user）
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
                else:
                    st.error("ログインID または パスワードが間違っています。")
            except Exception as e:
                st.error(f"ログインエラー: {e}")
    else:
        st.success("ログイン済みです。")
        st.write("✅ ここにスプレッドシートの閲覧・編集機能を実装できます。")

        if st.button("ログアウト"):
            st.session_state.logged_in = False

if __name__ == "__main__":
    main()
