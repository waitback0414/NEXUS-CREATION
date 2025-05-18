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

@st.cache_resource
def get_gspread_client():
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )
    return gspread.authorize(credentials)

def get_project_list(spreadsheet_key, sheet_name):
    client = get_gspread_client()
    sheet = client.open_by_key(spreadsheet_key).worksheet(sheet_name)
    data = sheet.get_all_values()
    headers = data[1]  # 2行目をヘッダーとする
    records = data[2:]  # 3行目以降がデータ

    # 案件ID（A列）で降順ソート
    valid_records = []
    for row in records:
        try:
            valid_records.append((int(row[0]), row))
        except:
            continue
    valid_records.sort(key=lambda x: x[0], reverse=True)
    sorted_records = [r for _, r in valid_records]

    df = pd.DataFrame(sorted_records, columns=headers)
    return df

def main():
    st.title("案件一覧")

    headers = data[1]  # 2行目をヘッダーとする
    records = data[2:]  # 3行目以降がデータ
    
    SPREADSHEET_KEY = "1tDCn0Io06H2DkDK8qgMBx3l4ff9E2w_uHl3O9xMnkYE"
    SHEET_NAME = "案件登録"

    df = get_project_list(SPREADSHEET_KEY, SHEET_NAME)
    # 変更後


# データの取得
df = pd.DataFrame(records, columns=headers)

# # ページネーションの設定
# items_per_page = 60
# total_items = len(df)
# total_pages = (total_items - 1) // items_per_page + 1

# if "current_page" not in st.session_state:
#     st.session_state.current_page = 1

# # ページ切り替えボタン
# col1, col2, col3 = st.columns([1, 2, 1])
# with col1:
#     if st.button("⬅️ 前へ") and st.session_state.current_page > 1:
#         st.session_state.current_page -= 1
# with col3:
#     if st.button("次へ ➡️") and st.session_state.current_page < total_pages:
#         st.session_state.current_page += 1

# start_idx = (st.session_state.current_page - 1) * items_per_page
# end_idx = min(start_idx + items_per_page, total_items)
# current_df = df.iloc[start_idx:end_idx]

# スタイルの適用
styled_df = current_df.style.set_table_styles([
    {'selector': 'table', 'props': [('background-color', 'white'), ('color', 'black'), ('border', '1px solid black')]},
    {'selector': 'th', 'props': [('background-color', 'white'), ('color', 'black'), ('border', '1px solid black')]},
    {'selector': 'td', 'props': [('background-color', 'white'), ('color', 'black'), ('border', '1px solid black')]}
])

# テーブルの表示
st.table(styled_df)



    # # ページネーション設定
    # items_per_page = 60
    # total_items = len(df)
    # total_pages = (total_items - 1) // items_per_page + 1

    # if "current_page" not in st.session_state:
    #     st.session_state.current_page = 1

    # if "selected_rows" not in st.session_state or len(st.session_state.selected_rows) != total_items:
    #     st.session_state.selected_rows = [False] * total_items

    # # ページ切替ボタン
    # col1, col2, col3 = st.columns([1, 2, 1])
    # with col1:
    #     if st.button("⬅️ 前へ") and st.session_state.current_page > 1:
    #         st.session_state.current_page -= 1
    # with col3:
    #     if st.button("次へ ➡️") and st.session_state.current_page < total_pages:
    #         st.session_state.current_page += 1

    # start_idx = (st.session_state.current_page - 1) * items_per_page
    # end_idx = min(start_idx + items_per_page, total_items)
    # current_df = styled_df.iloc[start_idx:end_idx]

    # # 表ヘッダー
    # cols = st.columns(len(df.columns) + 1)
    # cols[0].markdown("**選択**")
    # for i, h in enumerate(df.columns):
    #     cols[i+1].markdown(f"**{h}**")

    # # 表データ + チェックボックス
    # for idx, row in current_df.iterrows():
    #     cols = st.columns(len(df.columns) + 1)
    #     st.session_state.selected_rows[idx] = cols[0].checkbox(
    #         "", value=st.session_state.selected_rows[idx], key=f"cb_{idx}"
    #     )
    #     for j, val in enumerate(row):
    #         cols[j+1].write(val)

    # st.markdown(f"**📄 ページ {st.session_state.current_page} / {total_pages}**")

    # # 選択結果の表示
    # st.markdown("### ✅ 選択された案件")
    # selected_df = df[[selected for selected in st.session_state.selected_rows]]
    # st.dataframe(selected_df)

if __name__ == "__main__":
    main()


# # Streamlitアプリ

# df = pd.DataFrame(records, columns=headers)

# def main():
#     st.title("案件一覧")

#     SPREADSHEET_KEY = "1tDCn0Io06H2DkDK8qgMBx3l4ff9E2w_uHl3O9xMnkYE"
#     SHEET_NAME = "案件登録"

#     headers, records = get_project_list(SPREADSHEET_KEY, SHEET_NAME)

#     # ページネーション設定
#     items_per_page = 60
#     total_items = len(records)
#     total_pages = (total_items - 1) // items_per_page + 1

#     if "current_page" not in st.session_state:
#         st.session_state.current_page = 1

#     if "selected_rows" not in st.session_state or len(st.session_state.selected_rows) != total_items:
#         st.session_state.selected_rows = [False] * total_items

#     # ページ切替ボタン
#     col1, col2, col3 = st.columns([1, 2, 1])
#     with col1:
#         if st.button("⬅️ 前へ") and st.session_state.current_page > 1:
#             st.session_state.current_page -= 1
#     with col3:
#         if st.button("次へ ➡️") and st.session_state.current_page < total_pages:
#             st.session_state.current_page += 1

#     start_idx = (st.session_state.current_page - 1) * items_per_page
#     end_idx = min(start_idx + items_per_page, total_items)
#     current_records = records[start_idx:end_idx]

#     # 表スタイル（罫線）
   
#     st.markdown("""
#     <style>
#     .styled-table {
#         border-collapse: collapse;
#         margin: 10px 0;
#         font-size: 14px;
#         width: 100%;
#         background-color: #ffffff; /* 背景色を白に設定 */
#         color: #000000; 
#         border: 1px solid #000000;
#     }
#     .styled-table th, .styled-table td {
#         border: 1px solid #000000;
#         padding: 6px 10px;
#         text-align: left;
#     }
#     </style>
#     """, unsafe_allow_html=True)

#     # 表ヘッダー
#     cols = st.columns(len(headers) + 1)
#     cols[0].markdown("**選択**")
#     for i, h in enumerate(headers):
#         cols[i+1].markdown(f"**{h}**")

#     # 表データ + チェックボックス
#     for idx, row in enumerate(current_records):
#         global_idx = start_idx + idx
#         cols = st.columns(len(headers) + 1)
#         st.session_state.selected_rows[global_idx] = cols[0].checkbox(
#             "", value=st.session_state.selected_rows[global_idx], key=f"cb_{global_idx}"
#         )
#         for j, val in enumerate(row):
#             cols[j+1].write(val)

#     st.markdown(f"**📄 ページ {st.session_state.current_page} / {total_pages}**")

#     # 選択結果の表示
#     st.markdown("### ✅ 選択された案件")
#     for i, selected in enumerate(st.session_state.selected_rows):
#         if selected:
#             st.write(records[i])

# if __name__ == "__main__":
#     main()


