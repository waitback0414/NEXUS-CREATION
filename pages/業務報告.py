# import streamlit as st

# if "username" in st.session_state:
#     st.write(f"こんにちは、{st.session_state['username']}さん！")
# else:
#     st.warning("ログインしてください。")
#     st.stop()

# st.title("業務報告")
# st.write("ここに通常ユーザー向けの機能を実装します。")

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# Google Sheetsの認証とクライアントの取得
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=SCOPES
)
client = gspread.authorize(credentials)

# スプレッドシートとシートの指定
SPREADSHEET_KEY = "1tDCn0Io06H2DkDK8qgMBx3l4ff9E2w_uHl3O9xMnkYE"
SHEET_NAME = "予約一覧"

# ユーザー名の取得（ログイン時にセッションステートに保存されていると仮定）
username = st.session_state.get("username", None)

if not username:
    st.warning("ログインしてください。")
    st.stop()

# シートからデータの取得
sheet = client.open_by_key(SPREADSHEET_KEY).worksheet(SHEET_NAME)
data = sheet.get_all_values()

# ヘッダーとデータの分離
headers = data[2]  # 2行目をヘッダーとする
records = data[3:]  # 3行目以降がデータ

# ヘッダーのインデックス取得
header_indices = {header: idx for idx, header in enumerate(headers)}

# 必要な列のインデックス
col_indices = {
    "A": 0,
    "B": 1,
    "D": 3,
    "E": 4,
    "G": 6,
    "K": 10
}

# フィルタリング：G列がusernameと一致し、K列が空白の行
filtered_records = [
    row for row in records
    if len(row) > max(col_indices.values()) and
       row[col_indices["G"]] == username and
       row[col_indices["K"]] == ""
]

st.title("業務報告")

if not filtered_records:
    st.info("未報告の予約はありません。")
else:
    for idx, row in enumerate(filtered_records):
        with st.expander(f"予約 {idx + 1}"):
            st.write(f"予約ID: {row[col_indices['A']]}")
            st.write(f"日付: {row[col_indices['B']]}")
            st.write(f"ゴルフ場: {row[col_indices['D']]}")
            st.write(f"作業内容: {row[col_indices['E']]}")

            # 一意なキーを生成
            key_suffix = f"{idx}"
            button_key = f"report_button_{key_suffix}"
            text_key = f"report_text_{key_suffix}"
            submit_key = f"submit_button_{key_suffix}"

            if st.button("日報を登録する", key=button_key):
                st.session_state[f"show_text_{key_suffix}"] = True

            if st.session_state.get(f"show_text_{key_suffix}", False):
                report_text = st.text_area("日報を入力してください", key=text_key)
                if st.button("送信", key=submit_key):
                    # ここで日報をシートに書き込む処理を追加
                    # 例えば、K列に日報を追加するなど
                    row_number = idx + 3  # データは3行目から始まる
                    sheet.update_cell(row_number, col_indices["K"] + 1, report_text)
                    st.success("日報を登録しました。")
                    # 状態をリセット
                    st.session_state[f"show_text_{key_suffix}"] = False
