import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

#JSONを見に行く
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
client = gspread.authorize(credentials)

# Google Sheets の情報（🔴ここを設定）
SPREADSHEET_KEY = "1tDCn0Io06H2DkDK8qgMBx3l4ff9E2w_uHl3O9xMnkYE"  # あなたのスプレッドシートIDに置き換えてください
SHEET_NAME = ""  # タブの名前（例: "ログイン情報"）

# Google Sheets 認証 & データ取得
def get_login_data():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
    client = gspread.authorize(credentials)

    sheet = client.open_by_key(SPREADSHEET_KEY).worksheet(SHEET_NAME)
    data = sheet.get_all_values()
    headers = data[1]
    records = data[2:]
    return [{headers[i]: row[i] for i in range(len(headers))} for row in records]

# ログインチェック
def authenticate(user_id, password, login_data):
    for record in login_data:
        if record.get('MAIL') == user_id and record.get('PASS') == password:
            return True
    return False

# Streamlit アプリ本体
def main():
    st.title("ログインフォーム")

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        user_id = st.text_input("MAIL")
        password = st.text_input("PASS", type="password")

        if st.button("ログイン"):
            try:
                login_data = get_login_data()
                if authenticate(user_id, password, login_data):
                    st.session_state.logged_in = True
                    st.success("ログイン成功！")
                else:
                    st.error("IDまたはパスワードが間違っています")
            except Exception as e:
                st.error(f"ログインエラー: {e}")
    else:
        st.success("ログイン済みです。")
        st.write("ここにスプレッドシートの閲覧・編集機能を追加できます。")
        if st.button("ログアウト"):
            st.session_state.logged_in = False

if __name__ == "__main__":
    main()
