import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import date, datetime

# --- 認証とクライアント取得 ---
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
@st.cache_resource
def get_gspread_client():
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )
    return gspread.authorize(credentials)

client = get_gspread_client()

# --- スプレッドシートキーと関数定義 ---
SPREADSHEET_KEY = "1tDCn0Io06H2DkDK8qgMBx3l4ff9E2w_uHl3O9xMnkYE"  # ← 必要に応じて変更

def get_list(sheet_name):
    sheet = client.open_by_key(SPREADSHEET_KEY).worksheet(sheet_name)
    values = sheet.col_values(2)[2:]  # B列の3行目以降
    return [v for v in values if v.strip() != ""]

def generate_new_id(spreadsheet_key, sheet_name):
    sheet = client.open_by_key(spreadsheet_key).worksheet(sheet_name)
    data = sheet.col_values(1)[2:]  # A列の3行目以降

    year_prefix = datetime.now().strftime("%y")
    year_ids = [int(id_str) for id_str in data if id_str.isdigit() and id_str.startswith(year_prefix)]

    if not year_ids:
        return f"{year_prefix}0001"

    last_id = max(year_ids)
    new_id = last_id + 1
    return str(new_id)

# --- データ取得 ---
employees = get_list("従業員一覧")
golf_courses = get_list("ゴルフ場一覧")
work_types = get_list("作業一覧")

# --- UI表示 ---
st.title("📋 案件一括登録")

# 📅 日付入力
selected_date = st.date_input("登録日を選択してください", value=date.today())

# 🧑‍🤝‍🧑 案件入力マトリックス
st.write("### ⛳ 従業員別 案件入力")

input_data = []
for i, name in enumerate(employees):
    cols = st.columns([0.3, 0.35, 0.35])
    cols[0].markdown(f"**{name}**")
    work = cols[1].selectbox("業務内容", work_types, key=f"work_{i}")
    golf = cols[2].selectbox("ゴルフ場", golf_courses, key=f"golf_{i}")
    input_data.append((name, work, golf))

# 📤 登録処理
if st.button("一括登録"):
    sheet = client.open_by_key(SPREADSHEET_KEY).worksheet("案件登録")
    for name, work, golf in input_data:
        new_id = generate_new_id(SPREADSHEET_KEY, "案件登録")
        sheet.append_row([
            new_id,  # A列: ID
            selected_date.strftime("%Y/%m/%d"),  # B列: 日付
            name,  # C列: 氏名
            work,  # D列: 業務内容
            golf   # E列: ゴルフ場
        ], value_input_option="USER_ENTERED")
    st.success("一括登録が完了しました ✅")
