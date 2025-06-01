import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import date, datetime

# 認証スコープ
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# 認証とクライアント取得
@st.cache_resource
def get_gspread_client():
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )
    return gspread.authorize(credentials)

client = get_gspread_client()

# スプレッドシートキー（あなたのスプレッドシートIDに変更してください）
SPREADSHEET_KEY = "1tDCn0Io06H2DkDK8qgMBx3l4ff9E2w_uHl3O9xMnkYE"

# シートからB列3行目以降を取得する関数
def get_list(sheet_name):
    sheet = client.open_by_key(SPREADSHEET_KEY).worksheet(sheet_name)
    values = sheet.col_values(2)[2:]  # B列、3行目以降
    return [v for v in values if v.strip() != ""]

# IDを年度ごとに自動採番する関数
def generate_new_id(spreadsheet_key, sheet_name):
    sheet = client.open_by_key(spreadsheet_key).worksheet(sheet_name)
    data = sheet.col_values(1)[2:]  # A列、3行目以降
    year_prefix = datetime.now().strftime("%y")
    year_ids = [int(d) for d in data if d.isdigit() and d.startswith(year_prefix)]
    if not year_ids:
        return f"{year_prefix}0001"
    return str(max(year_ids) + 1)

# 各リストを取得
employees = get_list("従業員一覧")
golf_courses = get_list("ゴルフ場一覧")
work_types = get_list("作業一覧")

# UI表示
st.title("📋 案件一括登録")

# カレンダー日付選択
selected_date = st.date_input("登録日を選択してください", value=date.today())

# マトリックス入力
st.write("### ⛳ 従業員別 案件入力")

input_data = []
for i, name in enumerate(employees):
    cols = st.columns([0.3, 0.35, 0.35])
    cols[0].markdown(f"**{name}**")
    work = cols[1].selectbox("業務内容", work_types, key=f"work_{i}")
    golf = cols[2].selectbox("ゴルフ場", golf_courses, key=f"golf_{i}")
    input_data.append((name, work, golf))

if st.button("一括登録"):
    try:
        sheet = client.open_by_key(SPREADSHEET_KEY).worksheet("案件登録")
        last_row = len(sheet.get_all_values())

        # ★ 1回だけIDを取得
        base_id = generate_new_id(SPREADSHEET_KEY, "案件登録")
        base_id_int = int(base_id)

        # 一括登録データを構築
        new_rows = []
        for i, (name, work, golf) in enumerate(input_data):
            new_id = str(base_id_int + i)
            new_rows.append([
                new_id,
                selected_date.strftime("%Y/%m/%d"),
                name,
                work,
                golf
            ])

        insert_range = f"A{last_row+1}:E{last_row+len(new_rows)}"
        sheet.update(insert_range, new_rows, value_input_option="USER_ENTERED")

        st.success("一括登録が完了しました ✅")
    except Exception as e:
        st.error("登録中にエラーが発生しました。")
        st.exception(e)

