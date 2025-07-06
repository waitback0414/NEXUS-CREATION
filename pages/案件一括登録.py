import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import date, datetime

# --- 認証スコープ ---
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# --- gspread クライアント取得（キャッシュ可） ---
@st.cache_resource
def get_gspread_client():
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )
    return gspread.authorize(credentials)

client = get_gspread_client()

# --- スプレッドシートキーを設定（自分のに差し替えてください） ---
SPREADSHEET_KEY = "1tDCn0Io06H2DkDK8qgMBx3l4ff9E2w_uHl3O9xMnkYE"

# --- マスター情報を一括取得（キャッシュされる） ---
@st.cache_data
def get_master_lists():
    client = get_gspread_client()
    sheet_emp = client.open_by_key(SPREADSHEET_KEY).worksheet("従業員一覧")
    sheet_golf = client.open_by_key(SPREADSHEET_KEY).worksheet("ゴルフ場一覧")
    sheet_work = client.open_by_key(SPREADSHEET_KEY).worksheet("作業一覧")

    employees = sheet_emp.col_values(2)[2:]  # B列3行目以降
    golf_courses = sheet_golf.col_values(2)[2:]
    work_types = sheet_work.col_values(2)[2:]

    return (
        [e for e in employees if e.strip()],
        [g for g in golf_courses if g.strip()],
        [w for w in work_types if w.strip()]
    )

# --- ID発番関数（年度ごとの連番） ---
def generate_new_id(spreadsheet_key, sheet_name):
    sheet = client.open_by_key(spreadsheet_key).worksheet(sheet_name)
    data = sheet.col_values(1)[2:]  # A列3行目以降
    year_prefix = datetime.now().strftime("%y")
    year_ids = [int(d) for d in data if d.isdigit() and d.startswith(year_prefix)]
    if not year_ids:
        return f"{year_prefix}0001"
    return str(max(year_ids) + 1)

# --- アプリ本体 ---
def main():
    if st.session_state.get("role") != "admin":
        st.error("このページは管理者専用です。")
        st.stop()

    st.title("📝 案件一括登録")

    # --- マスター取得（1回だけ） ---
    employees, golf_courses, work_types = get_master_lists()

    # --- カレンダーで日付指定 ---
    selected_date = st.date_input("登録日を選択してください", value=date.today())

    st.write("### ✅ 対象者を選択してください")

    # input_data = []
    # for i, name in enumerate(employees):
    #     cols = st.columns([0.1, 0.25, 0.3, 0.35])
    #     checked = cols[0].checkbox(" ", value=False, key=f"check_{i}")
    #     cols[1].markdown(f"**{name}**")
    #     work = cols[2].selectbox("業務内容", work_types, key=f"work_{i}")
    #     golf = cols[3].selectbox("ゴルフ場", golf_courses, key=f"golf_{i}")
    #     input_data.append({
    #         "checked": checked,
    #         "name": name,
    #         "work": work,
    #         "golf": golf
    #     })
    # input_data = []
    # for i, name in enumerate(employees):
    #     with st.expander(f"👤 {name}", expanded=False):
    #         checked = st.checkbox("登録対象にする", key=f"check_{i}")
    #         work = st.selectbox("業務内容を選択", work_types, key=f"work_{i}")
    #         golf = st.selectbox("ゴルフ場を選択", golf_courses, key=f"golf_{i}")
            
    #         input_data.append({
    #             "checked": checked,
    #             "name": name,
    #             "work": work,
    #             "golf": golf
    #         })
        input_data = []
        for i, name in enumerate(employees):
            with st.expander(f"👤 {name}", expanded=False):
                checked = st.checkbox("✅ この人を登録する", key=f"check_{i}")
                work = st.selectbox("📋 業務内容", work_types, key=f"work_{i}")
                golf = st.selectbox("⛳ ゴルフ場", golf_courses, key=f"golf_{i}")
        
                input_data.append({
                    "checked": checked,
                    "name": name,
                    "work": work,
                    "golf": golf
                })

    # --- 登録ボタン処理 ---
    if st.button("一括登録"):
        try:
            sheet = client.open_by_key(SPREADSHEET_KEY).worksheet("案件登録")
            last_row = len(sheet.get_all_values())

            # IDは1回だけ取得して加算方式で生成
            base_id = generate_new_id(SPREADSHEET_KEY, "案件登録")
            base_id_int = int(base_id)

            new_rows = []
            counter = 0
            for item in input_data:
                if item["checked"]:
                    new_id = str(base_id_int + counter)
                    counter += 1
                    new_rows.append([
                        new_id,
                        selected_date.strftime("%Y/%m/%d"),
                        item["golf"],
                        item["work"],
                        item["name"]
                    ])

            if not new_rows:
                st.warning("チェックされた対象がありません。")
            else:
                insert_range = f"A{last_row+1}:E{last_row+len(new_rows)}"
                sheet.update(insert_range, new_rows, value_input_option="USER_ENTERED")
                st.success("一括登録が完了しました ✅")

        except Exception as e:
            st.error("登録中にエラーが発生しました。")
            st.exception(e)

# --- 実行 ---
if __name__ == "__main__":
    main()
