import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import datetime

# Google Sheets認証
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def get_gspread_client():
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )
    return gspread.authorize(credentials)

# スプレッドシートのキー
SPREADSHEET_KEY = "1tDCn0Io06H2DkDK8qgMBx3l4ff9E2w_uHl3O9xMnkYE"
SHEET_NAME =  "予約一覧"

# ログインユーザーの情報（セッションステートから取得）
# # ユーザー名の取得（ログイン時にセッションステートに保存されていると仮定）
user_email = st.session_state.get("user_email")
username = st.session_state.get("username", None)

if not username:
    st.warning("ログインしてください。")
    st.stop()



client = get_gspread_client()
sheet = client.open_by_key(SPREADSHEET_KEY).worksheet(SHEET_NAME)
data = sheet.get_all_values()
headers = data[1]  # 2行目
records = data[2:]  # 3行目以降

# 必要な列インデックス（列A:0, B:1, ..., K:10）
col_indices = {
    "A": 0,
    "B": 1,
    "D": 3,
    "E": 4,
    "G": 6,
    "K": 10
}

# --- ここで filtered_records を定義 ---
filtered_records = [
    row for row in records
    if len(row) > max(col_indices.values()) and
       row[col_indices["G"]] == username and
       row[col_indices["K"]] == ""
]

st.write(f"いつもご苦労様です、{st.session_state['username']} さん！")
# st.write(st.session_state)>>>バグ出し用。これはめっちゃ使える！
st.title("業務報告")

if not filtered_records:
    st.info("未報告の予約はありません。")
else:
    for idx, row in enumerate(filtered_records):
        with st.expander(f"予約 {idx + 1}"):
            # 構造化して予約情報を表示
            st.markdown(f"""
            <div style='
                border: 1px solid #ccc; 
                border-radius: 8px; 
                padding: 10px;
                background-color: #f9f9f9;
                margin-bottom: 10px;
            '>
            <p><strong>案件番号:</strong> {row[col_indices["A"]]}</p>
            <p><strong>日付:</strong> {row[col_indices["B"]]}</p>
            <p><strong>ゴルフ場:</strong> {row[col_indices["D"]]}</p>
            <p><strong>作業内容:</strong> {row[col_indices["E"]]}</p>
            </div>
            """, unsafe_allow_html=True)

            # 各予約に一意なキー
            key_suffix = f"{idx}"
            button_key = f"report_button_{key_suffix}"
            form_key = f"report_form_{key_suffix}"

            if st.button("日報を登録する", key=button_key):
                st.session_state[f"show_text_{key_suffix}"] = True

            if st.session_state.get(f"show_text_{key_suffix}", False):
                with st.form(form_key):
                    timestamp = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                    golf_course = st.selectbox(
                        "本日のゴルフ場", 
                        options=[row[col_indices["D"]]], 
                        index=0,
                        key=f"golf_{key_suffix}"
                    )
                    work_type = st.selectbox(
                        "本日の実績業務", 
                        ["キャディー", "作業", "キャディー_休祝日", "作業_休祝日", 
                         "研修", "研修_休祝日", "その他", "有休", "公休"],
                        key=f"type_{key_suffix}"
                    )
                    status = st.selectbox(
                        "業務状況", 
                        ["a:予定通り完了", "b:途中で帰宅（ゴルフ場都合）", 
                         "c:途中で帰宅（本人都合）", "d:その他業務完了報"],
                        key=f"status_{key_suffix}"
                    )
                    round_count = st.number_input("本日のラウンド数は？", min_value=0, step=1, key=f"round_{key_suffix}")
                    remarks = st.text_area("報告事項", key=f"remarks_{key_suffix}")

                    submitted = st.form_submit_button("登録")

                    if submitted:
                        report_sheet = client.open_by_key(SPREADSHEET_KEY).worksheet("日報回答")
                        report_sheet.append_row([
                            timestamp,                            # A: タイムスタンプ
                            user_email,                           # B: メールアドレス
                            row[col_indices["A"]],                # C: 案件番号
                            golf_course,                          # D: ゴルフ場
                            work_type,                            # E: 実績業務
                            status,                               # F: ステータス
                            round_count,                          # G: ラウンド数
                            "", "",                               # H, I: 空欄
                            remarks                               # J: 報告事項
                        ], value_input_option="USER_ENTERED")

                        # K列に「報告済み」フラグ（任意）
                        row_number = idx + 3  # データは3行目から
                        sheet.update_cell(row_number, col_indices["K"] + 1, "報告済み")

                        st.success("日報が登録されました ✅")
                        time.sleep(1)
                        st.session_state[f"show_text_{key_suffix}"] = False
                        st.experimental_rerun()

