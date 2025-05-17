import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import datetime

if st.session_state.get("role") != "admin":
    st.warning("このページは管理者専用です。")
    st.stop()

st.title("案件登録")


SPREADSHEET_KEY = "1tDCn0Io06H2DkDK8qgMBx3l4ff9E2w_uHl3O9xMnkYE"

#st.cacheは先に
@st.cache_resource
def get_gspread_client():
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )
    return gspread.authorize(credentials)


def get_list_from_sheet(spreadsheet_key, sheet_name, column_index):
    client = get_gspread_client()
    sheet = client.open_by_key(spreadsheet_key).worksheet(sheet_name)
    data = sheet.get_all_values()
    headers = data[1]  # 2行目をヘッダーとする
    records = data[2:]  # 3行目以降がデータ
    return [row[column_index] for row in records if len(row) > column_index]

golf_courses = get_list_from_sheet(SPREADSHEET_KEY, "ゴルフ場一覧", 1)  # B列
tasks = get_list_from_sheet(SPREADSHEET_KEY, "作業一覧", 1)  # B列
employees = get_list_from_sheet(SPREADSHEET_KEY, "従業員一覧", 1)  # B列:contentReference[oaicite:26]{index=26}



# 認証情報の設定
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# 案件一覧のデータを取得
def get_project_list(spreadsheet_key, sheet_name):
    client = get_gspread_client()
    sheet = client.open_by_key(spreadsheet_key).worksheet(sheet_name)
    data = sheet.get_all_values()
    headers = data[1]  # 2行目をヘッダーとする
    records = data[2:]  # 3行目以降がデータ

    # 案件番号（ID）で降順にソート
    records.sort(key=lambda x: int(x[0]), reverse=True)

    return headers, records

def generate_new_id(spreadsheet_key, sheet_name):
    client = get_gspread_client()
    sheet = client.open_by_key(spreadsheet_key).worksheet(sheet_name)
    data = sheet.col_values(1)[2:]  # A列の3行目以降
    if not data:
        return f"{datetime.datetime.now().year % 100}0001"
    last_id = max(int(id_str) for id_str in data if id_str.isdigit())
    new_id = last_id + 1
    return str(new_id)

new_id = generate_new_id(SPREADSHEET_KEY, "案件登録")

selected_date = datetime.date.today()

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("今日"):
        selected_date = datetime.date.today()
with col2:
    if st.button("明日"):
        selected_date = datetime.date.today() + datetime.timedelta(days=1)
with col3:
    if st.button("明後日"):
        selected_date = datetime.date.today() + datetime.timedelta(days=2)

with st.form("案件登録フォーム"):
    st.write(f"新しいID: {new_id}")
    date_input = st.date_input("日付を選択してください", selected_date)
    golf_course = st.selectbox("ゴルフ場を選択してください", golf_courses)
    task = st.selectbox("作業内容を選択してください", tasks)
    employee = st.selectbox("名前を選択してください", employees)
    submitted = st.form_submit_button("登録")

    if submitted:
        client = get_gspread_client()
        sheet = client.open_by_key(SPREADSHEET_KEY).worksheet("案件登録")

  # 日付オブジェクトを取得
        date_input = datetime.date.today()

    # 文字列に変換
        date_str = date_input.strftime("%Y/%m/%d")

    # データを追加
        sheet.append_row([int(new_id), date_str, golf_course, task, employee],value_input_option='USER_ENTERED')


        
        st.success("案件が登録されました。")


st.title("案件閲覧")
# Streamlitアプリ
def main():
    st.title("案件一覧")

    SPREADSHEET_KEY = "1tDCn0Io06H2DkDK8qgMBx3l4ff9E2w_uHl3O9xMnkYE"
    SHEET_NAME = "案件登録"

    headers, records = get_project_list(SPREADSHEET_KEY, SHEET_NAME)

    # チェックボックスの状態を保持するためのセッションステート
    if "selected_rows" not in st.session_state:
        st.session_state.selected_rows = [False] * len(records)

    # テーブルのヘッダーを表示
    cols = st.columns(len(headers) + 1)
    cols[0].write("選択")
    for idx, header in enumerate(headers):
        cols[idx + 1].write(header)

    # 各行を表示
    for i, row in enumerate(records):
        cols = st.columns(len(headers) + 1)
        st.session_state.selected_rows[i] = cols[0].checkbox("", value=st.session_state.selected_rows[i], key=f"checkbox_{i}")
        for j, cell in enumerate(row):
            cols[j + 1].write(cell)

    # 選択された行の情報を表示
    st.write("選択された案件:")
    for i, selected in enumerate(st.session_state.selected_rows):
        if selected:
            st.write(records[i])

if __name__ == "__main__":
    main()

