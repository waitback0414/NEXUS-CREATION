import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import datetime

# ページ設定（スマホ表示を意識して centered に）
st.set_page_config(page_title="案件登録", layout="centered")

# カスタムCSS
st.markdown("""
    <style>
    /* 全体のフォントとサイズ調整 */
    html, body, [class*="css"]  {
        font-family: 'Arial', sans-serif;
        font-size: 16px;
    }

    /* 入力フォーム、ボタンなどを画面幅にフィットさせる */
    input, textarea, select {
        width: 100% !important;
        font-size: 16px !important;
    }

    /* Streamlitのボタンを横幅いっぱいに広げる */
    button[kind="primary"] {
        width: 100% !important;
        font-size: 16px !important;
    }

    /* テーブルのスタイルをスマホ対応に */
    .dataframe {
        width: 100% !important;
        overflow-x: auto;
        font-size: 14px;
    }

    /* チェックボックスのラベルも読みやすく */
    label[data-baseweb="checkbox"] > div {
        font-size: 16px;
    }

    /* モバイルでのパディング調整 */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# 管理者チェック
if st.session_state.get("role") != "admin":
    st.warning("このページは管理者専用です。")
    st.stop()

st.title("案件登録")

# 認証スコープ
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SPREADSHEET_KEY = "1tDCn0Io06H2DkDK8qgMBx3l4ff9E2w_uHl3O9xMnkYE"
SHEET_NAME = "案件登録"


@st.cache_resource
def get_gspread_client():
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES,
    )
    return gspread.authorize(credentials)


@st.cache_data(ttl=300)
def get_list_from_sheet(spreadsheet_key: str, sheet_name: str, column_index: int):
    """
    指定シートの指定列（0始まり）からリストを取得。
    ttl=300 により、同じ引数で5分以内の再呼び出しはキャッシュから返る。
    """
    client = get_gspread_client()
    sheet = client.open_by_key(spreadsheet_key).worksheet(sheet_name)
    data = sheet.get_all_values()
    if len(data) < 3:
        return []
    records = data[2:]  # 3行目以降がデータ
    return [
        row[column_index]
        for row in records
        if len(row) > column_index and row[column_index] != ""
    ]


def generate_new_id(spreadsheet_key: str, sheet_name: str) -> str:
    """
    A列の最大値+1で新しい案件IDを生成。
    呼び出しのたびにシートを1回だけ読み、A列3行目以降を対象にする。
    """
    client = get_gspread_client()
    sheet = client.open_by_key(spreadsheet_key).worksheet(sheet_name)
    # A列の3行目以降
    data = sheet.col_values(1)[2:]
    if not data:
        # データがない場合は「西暦下2桁0001」から開始
        return f"{datetime.datetime.now().year % 100:02d}0001"
    # 数字だけを対象に最大値を取得
    numeric_ids = [int(id_str) for id_str in data if id_str.isdigit()]
    if not numeric_ids:
        return f"{datetime.datetime.now().year % 100:02d}0001"
    last_id = max(numeric_ids)
    new_id = last_id + 1
    return str(new_id)


# 各マスタの取得（キャッシュされる）
golf_courses = get_list_from_sheet(SPREADSHEET_KEY, "ゴルフ場一覧", 1)  # B列
tasks = get_list_from_sheet(SPREADSHEET_KEY, "作業一覧", 1)            # B列
employees = get_list_from_sheet(SPREADSHEET_KEY, "従業員一覧", 1)      # B列

# 日付選択の状態管理
if "selected_date" not in st.session_state:
    st.session_state.selected_date = datetime.date.today()

# 日付ショートカットボタン
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("今日"):
        st.session_state.selected_date = datetime.date.today()
with col2:
    if st.button("明日"):
        st.session_state.selected_date = datetime.date.today() + datetime.timedelta(
            days=1
        )
with col3:
    if st.button("明後日"):
        st.session_state.selected_date = datetime.date.today() + datetime.timedelta(
            days=2
        )

selected_date = st.session_state.selected_date
st.write(f"選択された日付: {selected_date.strftime('%Y/%m/%d')}")

# 案件登録フォーム
with st.form("案件登録フォーム"):
    # IDは登録時に採番するので、ここでは表示だけにしておく
    st.write("新しいID: 登録時に自動採番されます")

    date_input = st.date_input(
        "日付を選択してください", value=st.session_state.selected_date
    )
    golf_course = st.selectbox("ゴルフ場を選択してください", golf_courses)
    task = st.selectbox("作業内容を選択してください", tasks)
    employee = st.selectbox("名前を選択してください", employees)

    submitted = st.form_submit_button("登録")

    if submitted:
        # ここでだけ ID を発行（＝無駄な read を減らす）
        new_id = generate_new_id(SPREADSHEET_KEY, SHEET_NAME)

        client = get_gspread_client()
        sheet = client.open_by_key(SPREADSHEET_KEY).worksheet(SHEET_NAME)

        # date_input は datetime.date オブジェクト
        date_str = date_input.strftime("%Y/%m/%d")

        # データを追加
        sheet.append_row(
            [int(new_id), date_str, golf_course, task, employee],
            value_input_option="USER_ENTERED",
        )

        # 次回の初期値として選択した日付を保持
        st.session_state.selected_date = date_input

        st.success(f"案件 {new_id} が登録されました。")

# import streamlit as st
# import gspread
# from google.oauth2.service_account import Credentials
# import datetime
# import pandas as pd



# import streamlit as st

# # ページ設定（スマホ表示を意識して centered に）
# st.set_page_config(page_title="案件登録", layout="centered")

# # カスタムCSS
# st.markdown("""
#     <style>
#     /* 全体のフォントとサイズ調整 */
#     html, body, [class*="css"]  {
#         font-family: 'Arial', sans-serif;
#         font-size: 16px;
#     }

#     /* 入力フォーム、ボタンなどを画面幅にフィットさせる */
#     input, textarea, select {
#         width: 100% !important;
#         font-size: 16px !important;
#     }

#     /* Streamlitのボタンを横幅いっぱいに広げる */
#     button[kind="primary"] {
#         width: 100% !important;
#         font-size: 16px !important;
#     }

#     /* テーブルのスタイルをスマホ対応に */
#     .dataframe {
#         width: 100% !important;
#         overflow-x: auto;
#         font-size: 14px;
#     }

#     /* チェックボックスのラベルも読みやすく */
#     label[data-baseweb="checkbox"] > div {
#         font-size: 16px;
#     }

#     /* モバイルでのパディング調整 */
#     .block-container {
#         padding-top: 1rem;
#         padding-bottom: 1rem;
#         padding-left: 1rem;
#         padding-right: 1rem;
#     }
#     </style>
# """, unsafe_allow_html=True)



# if st.session_state.get("role") != "admin":
#     st.warning("このページは管理者専用です。")
#     st.stop()

# st.title("案件登録")


# SPREADSHEET_KEY = "1tDCn0Io06H2DkDK8qgMBx3l4ff9E2w_uHl3O9xMnkYE"
# SHEET_NAME = "案件登録"

# #st.cacheは先に
# @st.cache_resource
# def get_gspread_client():
#     credentials = Credentials.from_service_account_info(
#         st.secrets["gcp_service_account"],
#         scopes=SCOPES
#     )
#     return gspread.authorize(credentials)


# def get_list_from_sheet(spreadsheet_key, sheet_name, column_index):
#     client = get_gspread_client()
#     sheet = client.open_by_key(spreadsheet_key).worksheet(sheet_name)
#     data = sheet.get_all_values()
#     headers = data[1]  # 2行目をヘッダーとする
#     records = data[2:]  # 3行目以降がデータ
#     return [row[column_index] for row in records if len(row) > column_index]

# golf_courses = get_list_from_sheet(SPREADSHEET_KEY, "ゴルフ場一覧", 1)  # B列
# tasks = get_list_from_sheet(SPREADSHEET_KEY, "作業一覧", 1)  # B列
# employees = get_list_from_sheet(SPREADSHEET_KEY, "従業員一覧", 1)  # B列:contentReference[oaicite:26]{index=26}



# # 認証情報の設定
# SCOPES = [
#     "https://www.googleapis.com/auth/spreadsheets",
#     "https://www.googleapis.com/auth/drive"
# ]

# # 案件一覧のデータを取得
# def get_project_list(spreadsheet_key, sheet_name):
#     client = get_gspread_client()
#     sheet = client.open_by_key(spreadsheet_key).worksheet(sheet_name)
#     data = sheet.get_all_values()
#     headers = data[1]  # 2行目をヘッダーとする
#     records = data[2:]  # 3行目以降がデータ

#     # 案件番号（ID）で降順にソート
#     records.sort(key=lambda x: int(x[0]), reverse=True)

#     return headers, records



# def generate_new_id(spreadsheet_key, sheet_name):
#     client = get_gspread_client()
#     sheet = client.open_by_key(spreadsheet_key).worksheet(sheet_name)
#     data = sheet.col_values(1)[2:]  # A列の3行目以降
#     if not data:
#         return f"{datetime.datetime.now().year % 100}0001"
#     last_id = max(int(id_str) for id_str in data if id_str.isdigit())
#     new_id = last_id + 1
#     return str(new_id)

# new_id = generate_new_id(SPREADSHEET_KEY, "案件登録")

# if "selected_date" not in st.session_state:
#     st.session_state.selected_date = datetime.date.today()
# selected_date = datetime.date.today()
# selected_date = st.session_state.selected_date
# st.write(f"選択された日付: {selected_date.strftime('%Y/%m/%d')}")

# col1, col2, col3 = st.columns(3)
# with col1:
#     if st.button("今日"):
#         selected_date = datetime.date.today()
# with col2:
#     if st.button("明日"):
#         selected_date = datetime.date.today() + datetime.timedelta(days=1)
# with col3:
#     if st.button("明後日"):
#         selected_date = datetime.date.today() + datetime.timedelta(days=2)

# with st.form("案件登録フォーム"):
#     st.write(f"新しいID: {new_id}")
#     date_input = st.date_input("日付を選択してください", selected_date)
#     golf_course = st.selectbox("ゴルフ場を選択してください", golf_courses)
#     task = st.selectbox("作業内容を選択してください", tasks)
#     employee = st.selectbox("名前を選択してください", employees)
#     submitted = st.form_submit_button("登録")



#     if submitted:
#         client = get_gspread_client()
#         sheet = client.open_by_key(SPREADSHEET_KEY).worksheet("案件登録")

#   # 日付オブジェクトを取得
#         date_input = datetime.date.today()

#     # 文字列に変換
#         date_str = date_input.strftime("%Y/%m/%d")

#     # データを追加
#         sheet.append_row([int(new_id), date_str, golf_course, task, employee],value_input_option='USER_ENTERED')


        
#         st.success("案件が登録されました。")
