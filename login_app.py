import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# Google Sheets の情報
SPREADSHEET_KEY = "1tDCn0Io06H2DkDK8qgMBx3l4ff9E2w_uHl3O9xMnkYE"  # ←ここを自分のキーに置き換える
SHEET_NAME = "従業員情報"  # ←タブ名

# 認証して gspread クライアントを返す
@st.cache_resource
def get_gspread_client():
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    return gspread.authorize(credentials)

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
