import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Google Sheets 認証
def get_login_data():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
    client = gspread.authorize(credentials)

    sheet = client.open("ログイン管理シート名").worksheet("ログイン情報")
    data = sheet.get_all_values()
    headers = data[0]
    records = data[1:]
    return [{headers[i]: row[i] for i in range(len(headers))} for row in records]

# ログインチェック関数
def authenticate(user_id, password, login_data):
    for record in login_data:
        if record.get('ID') == user_id and record.get('パスワード') == password:
            return True
    return False

# Streamlitアプリ
def main():
    st.title("ログインフォーム")

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        user_id = st.text_input("ID")
        password = st.text_input("パスワード", type="password")

        if st.button("ログイン"):
            login_data = get_login_data()
            if authenticate(user_id, password, login_data):
                st.session_state.logged_in = True
                st.success("ログイン成功！")
            else:
                st.error("IDまたはパスワードが間違っています")
    else:
        st.success("ログイン済みです。")
        st.write("ここにスプレッドシートの閲覧・編集機能を追加できます。")
        if st.button("ログアウト"):
            st.session_state.logged_in = False

if __name__ == "__main__":
    main()
