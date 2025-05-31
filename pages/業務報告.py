import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import datetime
import time

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
    "K": 10,
    "T": 19,
    "AJ": 35
}

# --- ここで filtered_records を定義 ---
# --- フィルタ条件の修正 ---
filtered_records = []
for i, row in enumerate(records):  # ← records はシートの3行目から
    row_number = i + 3  # 実際のスプレッドシート上の行番号（1-based）
    if len(row) > max(col_indices.values()):
        is_user = row[col_indices["G"]] == username
        is_k_empty = row[col_indices["K"]] == ""
        is_t_rejected = row[col_indices["T"]].strip() == "却下"
        if is_user and (is_k_empty or is_t_rejected):
            filtered_records.append({"row": row, "row_number": row_number})


st.write(f"いつもご苦労様です、{st.session_state['username']} さん！")
# st.write(st.session_state)>>>バグ出し用。これはめっちゃ使える！
st.title("業務報告")

if not filtered_records:
    st.info("未報告の予約はありません。")
else:
    for idx, item in enumerate(filtered_records):
        row = item["row"]
        row_number = item["row_number"]  # ← これが予約一覧シートの正確な行番号

        # ここから表示やフォームの処理を記述します
        with st.expander(f"案件 {idx + 1}"):
            st.markdown(f"""
            <div style='
                border: 1px solid #ccc; 
                border-radius: 8px; 
                padding: 10px;
                background-color: #f9f9f9;
                margin-bottom: 10px;
                color: black;
            '>
            <p><strong>案件番号:</strong> {row[col_indices["A"]]}</p>
            <p><strong>日付:</strong> {row[col_indices["B"]]}</p>
            <p><strong>ゴルフ場:</strong> {row[col_indices["D"]]}</p>
            <p><strong>作業内容:</strong> {row[col_indices["E"]]}</p>
            </div>
            """, unsafe_allow_html=True)

            if row[col_indices["T"]].strip() == "却下":
                st.warning("却下されたので修正してください。")
                comment = row[col_indices["AJ"]].strip()
                if comment:
                    st.info(f"却下コメント：{comment}")


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
                        report_data = report_sheet.get_all_values()
                    
                        # 案件番号で該当行を探す（C列）
                        target_row_index = None
                        for i, r in enumerate(report_data[1:], start=2):
                            if r[2] == row[col_indices["A"]]:
                                target_row_index = i
                                break
                    
                        if target_row_index:
                            # 修正：上書きする
                            report_sheet.update(f"A{target_row_index}:J{target_row_index}", [[
                                timestamp,
                                user_email,
                                row[col_indices["A"]],
                                golf_course,
                                work_type,
                                status,
                                round_count,
                                "", "",
                                remarks
                            ]])
                        else:
                            # 新規：追加する
                            report_sheet.append_row([
                                timestamp,
                                user_email,
                                int(row[col_indices["A"]]),  # ← 数値として入力される
                                golf_course,
                                work_type,
                                status,
                                round_count,
                                "", "",
                                remarks
                            ], value_input_option="USER_ENTERED")
                    
                        # T列を空欄に戻す（再承認待ち）
                        # T列（承認）のクリア → 確実に元行を対象に
                        sheet.update_cell(row_number, col_indices["T"] + 1, "")

                    
                        st.success("日報が登録されました ✅")
                        time.sleep(1)
                        st.session_state[f"show_text_{key_suffix}"] = False
                        st.rerun()


                    # if submitted:
                    #     report_sheet = client.open_by_key(SPREADSHEET_KEY).worksheet("日報回答")
                    #     report_sheet.append_row([
                    #         timestamp,                            # A: タイムスタンプ
                    #         user_email,                           # B: メールアドレス
                    #         row[col_indices["A"]],                # C: 案件番号
                    #         golf_course,                          # D: ゴルフ場
                    #         work_type,                            # E: 実績業務
                    #         status,                               # F: ステータス
                    #         round_count,                          # G: ラウンド数
                    #         "", "",                               # H, I: 空欄
                    #         remarks                               # J: 報告事項
                    #     ], value_input_option="USER_ENTERED")

                    #     # K列に「報告済み」フラグ（任意）
                    #     # 報告元の行番号（元データが3行目から始まるため +3）
                    #     row_number = idx + 3
                        
                    #     # 「却下」されていたらT列を空欄に戻す
                    #     if row[col_indices["T"]].strip() == "却下":
                    #         sheet.update_cell(row_number, col_indices["T"] + 1, "")  # T列 = index 19 + 1 = 列番号20
                    #     # else:
                    #     #     sheet.update_cell(row_number, col_indices["K"] + 1, "報告済み")  # 通常はK列に「報告済み」


                    #     st.success("日報が登録されました ✅")
                    #     time.sleep(1)
                    #     st.session_state[f"show_text_{key_suffix}"] = False
                    #     st.rerun()


