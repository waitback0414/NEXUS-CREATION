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
SHEET_NAME = "予約一覧"

# ログインユーザー確認
user_email = st.session_state.get("user_email")
username = st.session_state.get("username")
if not username:
    st.warning("ログインしてください。")
    st.stop()

client = get_gspread_client()
sheet = client.open_by_key(SPREADSHEET_KEY).worksheet(SHEET_NAME)
data = sheet.get_all_values()
headers = data[1]
records = data[2:]

# 必要な列インデックス
col_indices = {
    "A": 0, "B": 1, "D": 3, "E": 4,
    "G": 6, "K": 10, "T": 19, "AJ": 35
}

# 未報告フィルタ
filtered_records = []
for i, row in enumerate(records):
    row_number = i + 3
    if len(row) > col_indices["T"]:  # ★ T列まであればOKに修正
        is_user = row[col_indices["G"]] == username
        is_k_empty = row[col_indices["K"]] == ""
        is_t_rejected = row[col_indices["T"]].strip() == "却下"
        if is_user and (is_k_empty or is_t_rejected):
            filtered_records.append({"row": row, "row_number": row_number})

st.title("業務報告")
st.write(f"いつもご苦労様です、{username} さん！")

if not filtered_records:
    st.info("未報告の予約はありません。")
else:
    for idx, item in enumerate(filtered_records):
        row = item["row"]
        row_number = item["row_number"]

        with st.expander(f"案件 {idx + 1}"):
            st.markdown(f"""
            <div style='border:1px solid #ccc;border-radius:8px;padding:10px;background:#f9f9f9;margin-bottom:10px;color:black;'>
            <p><strong>案件番号:</strong> {row[col_indices["A"]]}</p>
            <p><strong>日付:</strong> {row[col_indices["B"]]}</p>
            <p><strong>ゴルフ場:</strong> {row[col_indices["D"]]}</p>
            <p><strong>作業内容:</strong> {row[col_indices["E"]]}</p>
            </div>
            """, unsafe_allow_html=True)

            if row[col_indices["T"]].strip() == "却下":
                st.warning("却下されたので修正してください。")
                # AJ列が存在する場合のみコメントを参照
                comment = ""
                if len(row) > col_indices["AJ"]:
                    comment = row[col_indices["AJ"]].strip()
                if comment:
                    st.info(f"却下コメント：{comment}")

            key_suffix = f"{idx}"

            # ▼ 日報登録フォーム
            if st.button("日報を登録する", key=f"btn_{key_suffix}"):
                st.session_state[f"show_form_{key_suffix}"] = True

            if st.session_state.get(f"show_form_{key_suffix}", False):
                with st.form(f"form_{key_suffix}"):
                    selected_date = st.date_input("勤務日を選択", value=datetime.date.today(), key=f"date_{key_suffix}")
                    report_date = selected_date.strftime("%Y/%m/%d")

                    golf_course = st.selectbox("勤務したゴルフ場", [row[col_indices["D"]]], key=f"golf_{key_suffix}")
                    work_type = st.selectbox("本日の実績業務", [
                        "キャディー", "作業", "キャディー_休祝日", "作業_休祝日",
                        "研修", "研修_休祝日", "その他", "有休", "公休"
                    ], key=f"type_{key_suffix}")
                    status = st.selectbox("業務状況", [
                        "a:予定通り完了", "b:途中で帰宅（ゴルフ場都合）",
                        "c:途中で帰宅（本人都合）", "d:その他業務完了報"
                    ], key=f"status_{key_suffix}")
                    round_count = st.number_input("本日のラウンド数", min_value=0, step=1, key=f"round_{key_suffix}")
                    remarks = st.text_area("報告事項", key=f"remarks_{key_suffix}")

                    # ▼ 登録ボタンと案件取消ボタンを横並びに配置
                    col1, col2 = st.columns(2)
                    with col1:
                        submit_report = st.form_submit_button("登録")
                    with col2:
                        cancel_request = st.form_submit_button("案件取消")

                # ▼ 登録ボタンが押されたときの処理（既存動作）
                if submit_report:
                    report_sheet = client.open_by_key(SPREADSHEET_KEY).worksheet("日報回答")
                    report_data = report_sheet.get_all_values()

                    # 同一案件がすでにあるか確認
                    target_index = None
                    for i_r, r in enumerate(report_data[1:], start=2):
                        if r[2] == row[col_indices["A"]]:
                            target_index = i_r
                            break

                    report_row = [
                        report_date,
                        user_email,
                        int(row[col_indices["A"]]),
                        golf_course,
                        work_type,
                        status,
                        round_count,
                        "", "",  # 空欄
                        remarks
                    ]

                    if target_index:
                        report_sheet.update(f"A{target_index}:J{target_index}", [report_row])
                    else:
                        report_sheet.append_row(report_row, value_input_option="USER_ENTERED")

                    # 「承認」列（T）を空に戻す
                    sheet.update_cell(row_number, col_indices["T"] + 1, "")

                    st.success("✅ 日報が登録されました")
                    time.sleep(1)
                    st.session_state[f"show_form_{key_suffix}"] = False
                    st.rerun()

                # ▼ 案件取消ボタンが押されたとき：確認フラグをON
                if cancel_request:
                    st.session_state[f"confirm_cancel_{key_suffix}"] = True

            # ▼ 案件取消の確認ダイアログ（YES/NO）
            if st.session_state.get(f"confirm_cancel_{key_suffix}", False):
                st.warning("本当に取り消しますか？")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("YES", key=f"yes_cancel_{key_suffix}"):
                        # シート「案件登録」から該当案件番号を検索し、G列に「取消」を入力
                       案件番号 = str(row[col_indices["A"]])

                        register_sheet = client.open_by_key(SPREADSHEET_KEY).worksheet("案件登録")
                        register_data = register_sheet.get_all_values()

                        target_row_idx = None
                        # 2行目以降を検索（1行目はヘッダー想定）
                        for i_r, r in enumerate(register_data[1:], start=2):
                            # 行内のどこかのセルが案件番号と一致すればその行を対象とする
                            if any(cell == 案件番号 for cell in r):
                                target_row_idx = i_r
                                break

                        if target_row_idx is not None:
                            # G列は7列目
                            register_sheet.update_cell(target_row_idx, 7, "取消")
                            st.success(f"案件番号 {案件番号} を『取消』に更新しました。")
                        else:
                            st.error("対応する案件番号がシート『案件登録』内に見つかりませんでした。")

                        # 確認フラグをリセット
                        st.session_state[f"confirm_cancel_{key_suffix}"] = False
                        # 必要に応じて再描画
                        time.sleep(1)
                        st.rerun()

                with c2:
                    if st.button("NO", key=f"no_cancel_{key_suffix}"):
                        st.session_state[f"confirm_cancel_{key_suffix}"] = False
                        st.info("取消処理を中止しました。")




# import streamlit as st
# import gspread
# from google.oauth2.service_account import Credentials
# import datetime
# import time

# # Google Sheets認証
# SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# @st.cache_resource
# def get_gspread_client():
#     credentials = Credentials.from_service_account_info(
#         st.secrets["gcp_service_account"],
#         scopes=SCOPES
#     )
#     return gspread.authorize(credentials)

# # スプレッドシートのキー
# SPREADSHEET_KEY = "1tDCn0Io06H2DkDK8qgMBx3l4ff9E2w_uHl3O9xMnkYE"
# SHEET_NAME = "予約一覧"

# # ログインユーザー確認
# user_email = st.session_state.get("user_email")
# username = st.session_state.get("username")
# if not username:
#     st.warning("ログインしてください。")
#     st.stop()

# client = get_gspread_client()
# sheet = client.open_by_key(SPREADSHEET_KEY).worksheet(SHEET_NAME)
# data = sheet.get_all_values()
# headers = data[1]
# records = data[2:]

# # 必要な列インデックス
# col_indices = {
#     "A": 0, "B": 1, "D": 3, "E": 4,
#     "G": 6, "K": 10, "T": 19, "AJ": 35
# }

# # 未報告フィルタ
# filtered_records = []
# for i, row in enumerate(records):
#     row_number = i + 3
#     if len(row) > max(col_indices.values()):
#         is_user = row[col_indices["G"]] == username
#         is_k_empty = row[col_indices["K"]] == ""
#         is_t_rejected = row[col_indices["T"]].strip() == "却下"
#         if is_user and (is_k_empty or is_t_rejected):
#             filtered_records.append({"row": row, "row_number": row_number})

# st.title("業務報告")
# st.write(f"いつもご苦労様です、{username} さん！")

# if not filtered_records:
#     st.info("未報告の予約はありません。")
# else:
#     for idx, item in enumerate(filtered_records):
#         row = item["row"]
#         row_number = item["row_number"]

#         with st.expander(f"案件 {idx + 1}"):
#             st.markdown(f"""
#             <div style='border:1px solid #ccc;border-radius:8px;padding:10px;background:#f9f9f9;margin-bottom:10px;color:black;'>
#             <p><strong>案件番号:</strong> {row[col_indices["A"]]}</p>
#             <p><strong>日付:</strong> {row[col_indices["B"]]}</p>
#             <p><strong>ゴルフ場:</strong> {row[col_indices["D"]]}</p>
#             <p><strong>作業内容:</strong> {row[col_indices["E"]]}</p>
#             </div>
#             """, unsafe_allow_html=True)

#             if row[col_indices["T"]].strip() == "却下":
#                 st.warning("却下されたので修正してください。")
#                 comment = row[col_indices["AJ"]].strip()
#                 if comment:
#                     st.info(f"却下コメント：{comment}")

#             key_suffix = f"{idx}"
#             if st.button("日報を登録する", key=f"btn_{key_suffix}"):
#                 st.session_state[f"show_form_{key_suffix}"] = True

#             if st.session_state.get(f"show_form_{key_suffix}", False):
#                 with st.form(f"form_{key_suffix}"):
#                     selected_date = st.date_input("勤務日を選択", value=datetime.date.today(), key=f"date_{key_suffix}")
#                     report_date = selected_date.strftime("%Y/%m/%d")

#                     golf_course = st.selectbox("勤務したゴルフ場", [row[col_indices["D"]]], key=f"golf_{key_suffix}")
#                     work_type = st.selectbox("本日の実績業務", [
#                         "キャディー", "作業", "キャディー_休祝日", "作業_休祝日",
#                         "研修", "研修_休祝日", "その他", "有休", "公休"
#                     ], key=f"type_{key_suffix}")
#                     status = st.selectbox("業務状況", [
#                         "a:予定通り完了", "b:途中で帰宅（ゴルフ場都合）",
#                         "c:途中で帰宅（本人都合）", "d:その他業務完了報"
#                     ], key=f"status_{key_suffix}")
#                     round_count = st.number_input("本日のラウンド数", min_value=0, step=1, key=f"round_{key_suffix}")
#                     remarks = st.text_area("報告事項", key=f"remarks_{key_suffix}")

#                     if st.form_submit_button("登録"):
#                         report_sheet = client.open_by_key(SPREADSHEET_KEY).worksheet("日報回答")
#                         report_data = report_sheet.get_all_values()

#                         # 同一案件がすでにあるか確認
#                         target_index = None
#                         for i, r in enumerate(report_data[1:], start=2):
#                             if r[2] == row[col_indices["A"]]:
#                                 target_index = i
#                                 break

#                         report_row = [
#                             report_date,
#                             user_email,
#                             int(row[col_indices["A"]]),
#                             golf_course,
#                             work_type,
#                             status,
#                             round_count,
#                             "", "",  # 空欄
#                             remarks
#                         ]

#                         if target_index:
#                             report_sheet.update(f"A{target_index}:J{target_index}", [report_row])
#                         else:
#                             report_sheet.append_row(report_row, value_input_option="USER_ENTERED")

#                         # 「承認」列（T）を空に戻す
#                         sheet.update_cell(row_number, col_indices["T"] + 1, "")

#                         st.success("✅ 日報が登録されました")
#                         time.sleep(1)
#                         st.session_state[f"show_form_{key_suffix}"] = False
#                         st.rerun()
