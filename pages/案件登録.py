import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import datetime
import pandas as pd

if st.session_state.get("role") != "admin":
    st.warning("このページは管理者専用です。")
    st.stop()

st.title("案件登録")


SPREADSHEET_KEY = "1tDCn0Io06H2DkDK8qgMBx3l4ff9E2w_uHl3O9xMnkYE"
SHEET_NAME = "案件登録"

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

if "selected_date" not in st.session_state:
    st.session_state.selected_date = datetime.date.today()
selected_date = datetime.date.today()
selected_date = st.session_state.selected_date
st.write(f"選択された日付: {selected_date.strftime('%Y/%m/%d')}")

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

def get_filtered_projects(spreadsheet_key, sheet_name, selected_date):
    client = get_gspread_client()
    sheet = client.open_by_key(spreadsheet_key).worksheet(sheet_name)
    data = sheet.get_all_values()
    headers = data[2]  # 2行目: ヘッダー
    records = data[3:]  # 3行目以2降

    filtered = [
        row for row in records
        if len(row) > 1 and row[1] == selected_date.strftime("%Y/%m/%d")
    ]
    return headers, filtered


# 使用部分（インデント注意）
# headers, filtered_records = get_filtered_projects(SPREADSHEET_KEY, SHEET_NAME , selected_date)

# st.subheader("該当する案件リスト")
# if filtered_records:
#     for row in filtered_records:
#         st.markdown(f"""
#         **案件番号:** {row[0]}  
#         **日付:** {row[1]}  
#         **ゴルフ場:** {row[2]}  
#         **作業内容:** {row[3]}  
#         **名前:** {row[4]}
#         """)
# else:
#     st.info("該当する案件は見つかりませんでした。")

# ここから新しいコード
headers, filtered_records = get_filtered_projects(SPREADSHEET_KEY, SHEET_NAME , selected_date)
# filtered_records: [["240001", "2025/05/18", "ABC", "キャディー", "山田太郎"], ...]
# headers = ["案件番号", "日付", "ゴルフ場", "作業内容", "名前"]
df = pd.DataFrame(filtered_records, columns=headers)

# チェックボックスを表示するための列を作成
if "delete_flags" not in st.session_state or len(st.session_state.delete_flags) != len(df):
    st.session_state.delete_flags = [False] * len(df)

st.subheader("該当する案件リスト（選択して削除）")

# 表示 + チェックボックス
for i, row in df.iterrows():
    cols = st.columns([0.1, 0.9])
    st.session_state.delete_flags[i] = cols[0].checkbox("", value=st.session_state.delete_flags[i], key=f"chk_{i}")
    cols[1].write(
        f"**案件番号:** {row['案件番号']}｜**日付:** {row['日付']}｜**ゴルフ場:** {row['ゴルフ場']}｜"
        f"**作業内容:** {row['作業内容']}｜**名前:** {row['名前']}"
    )

# 削除ボタン
if st.button("チェックされた案件を削除する"):
    selected_indices = [i for i, flag in enumerate(st.session_state.delete_flags) if flag]
    if selected_indices:
        st.warning("以下の案件が削除対象です（※ここでは削除処理は未実装です）")
        st.dataframe(df.iloc[selected_indices])
        # ここに Sheets から削除する処理を追加可能
    else:
        st.info("削除対象が選ばれていません。")

