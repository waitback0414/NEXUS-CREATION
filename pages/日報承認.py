# import streamlit as st
# import gspread
# import pandas as pd
# from google.oauth2.service_account import Credentials
# import datetime

# # 管理者のみアクセス可
# if st.session_state.get("role") != "admin":
#     st.error("このページは管理者のみアクセス可能です。")
#     st.stop()

# # 認証設定
# SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
# SPREADSHEET_KEY = "1tDCn0Io06H2DkDK8qgMBx3l4ff9E2w_uHl3O9xMnkYE"
# SHEET_NAME = "予約一覧"

# @st.cache_resource
# def get_gspread_client():
#     credentials = Credentials.from_service_account_info(
#         st.secrets["gcp_service_account"],
#         scopes=SCOPES
#     )
#     return gspread.authorize(credentials)

# # データ取得関数
# def fetch_pending_reports():
#     client = get_gspread_client()
#     sheet = client.open_by_key(SPREADSHEET_KEY).worksheet(SHEET_NAME)
#     data = sheet.get_all_values()

#     if len(data) < 3:
#         return pd.DataFrame(), sheet

#     headers = data[2]
#     records = data[3:]

#     df = pd.DataFrame(records, columns=headers)
    
#     # 必要な列だけ抜粋 & T列（"承認"）が空欄の行のみ
#     cols_to_display = ["ID", "登録日", "登録者", "ゴルフ場", "業務", "報告", "ラウンド数", "チェック", "エラー箇所"]
#     column_indices = [0, 10, 11, 13, 14, 15, 16, 18, 20]
    
#     filtered = [row for row in records if len(row) > 19 and row[19].strip() != "承認"]
#     df_filtered = pd.DataFrame(filtered, columns=headers).iloc[:, column_indices]

#     # 日付ソート（登録日列が18列目→index=17）
#     df_filtered["登録日"] = pd.to_datetime(df_filtered["登録日"], errors='coerce')
#     df_filtered = df_filtered.sort_values(by="登録日", ascending=False).reset_index(drop=True)

#     return df_filtered, sheet

# # ページUI
# st.title("📝 日報承認（管理者専用）")

# # 日付フィルター
# selected_date = st.date_input("日付で絞り込む（登録日）", value=None)
# df, sheet = fetch_pending_reports()

# if selected_date:
#     df = df[df["登録日"].dt.date == selected_date]

# if df.empty:
#     st.info("承認待ちの日報はありません。")
#     st.stop()

# # 承認チェックボックス列
# if "approval_flags" not in st.session_state or len(st.session_state.approval_flags) != len(df):
#     st.session_state.approval_flags = [False] * len(df)

# st.write("以下は未承認の日報一覧です：")

# df, sheet = fetch_pending_reports()
# st.session_state.approval_flags = [False] * len(df)  # ← ここで確実に初期化


# # 表 + チェックボックス表示
# for i, row in df.iterrows():
#     cols = st.columns([0.05, 0.95])
#     st.session_state.approval_flags[i] = cols[0].checkbox("", value=st.session_state.approval_flags[i], key=f"chk_{i}")
#     cols[1].markdown(
#         f"""
#         **ID:** {row[0]}｜**登録日:** {row[1]}｜**登録者:** {row[2]}  
#         **ゴルフ場:** {row[3]}｜**業務:** {row[4]}｜**報告:** {row[5]}  
#         **ラウンド数:** {row[6]}｜**報告事項:** {row[7]}
#         """
#     )

# # ✅ 初期化
# data = sheet.get_all_values()
# headers = data[2]      # 3行目をヘッダー
# records = data[3:]     # 4行目以降をデータ
# df = pd.DataFrame(records, columns=headers)
# df = df[df["承認"] != "承認"]  # T列（インデックス=19）の列名に応じて修正
# df, sheet = fetch_pending_reports()  # ← この関数で T列 != "承認" をフィルターしてる前提
# st.session_state.approval_flags = [False] * len(df)  # 行数に合わせてフラグ初期化

# # ✅ 表示部分
# for i, row in df.iterrows():
#     cols = st.columns([0.05, 0.95])
#     st.session_state.approval_flags[i] = cols[0].checkbox(
#         "", value=st.session_state.approval_flags[i], key=f"chk_{i}"
#     )
#     cols[1].markdown(
#         f"**予約番号:** {row[0]}｜**登録者:** {row[2]}｜**登録日:** {row[7]}"
#     )

# # ✅ 全データ（ヘッダー除いた 4行目以降）取得して実行対象の行番号を特定
# all_data = sheet.get_all_values()[3:]

# # ✅ ボタン処理
# col1, col2 = st.columns(2)
# with col1:
#     if st.button("✅ 承認する"):
#         for i, flag in enumerate(st.session_state.approval_flags):
#             if flag:
#                 target_id = df.iloc[i, 0]
#                 for idx, row in enumerate(all_data):
#                     if row[0] == target_id:
#                         sheet.update_cell(idx + 4, 20, "承認")  # 4行目以降
#                         break
#         st.success("承認を完了しました。")
#         st.rerun()  # ✅ ページを再読み込み → T列="承認" が除外されて消える

# with col2:
#     if st.button("❌ 却下する"):
#         for i, flag in enumerate(st.session_state.approval_flags):
#             if flag:
#                 target_id = df.iloc[i, 0]
#                 for idx, row in enumerate(all_data):
#                     if row[0] == target_id:
#                         sheet.update_cell(idx + 4, 20, "却下")
#                         break
#         st.warning("却下を完了しました。")
#         st.rerun()  # ✅ 同様に再読み込み


import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime

# ====== 認証とクライアント取得 ======
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

SPREADSHEET_KEY = "1tDCn0Io06H2DkDK8qgMBx3l4ff9E2w_uHl3O9xMnkYE"
SHEET_NAME = "予約一覧"

@st.cache_resource
def get_gspread_client():
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )
    return gspread.authorize(credentials)


# ====== データ取得関数 ======
def load_pending_approvals(spreadsheet_key, sheet_name):
    client = get_gspread_client()
    sheet = client.open_by_key(spreadsheet_key).worksheet(sheet_name)
    data = sheet.get_all_values()

    headers = data[2]  # 3行目がヘッダー
    records = data[3:]  # 4行目以降がデータ

    df = pd.DataFrame(records, columns=headers)
    df["行番号"] = range(4, 4 + len(df))  # 実際のスプレッドシートの行番号を記録

    # T列が承認済みでないもののみフィルター（列名を確認して正確に）
    status_col = "承認状態" if "承認状態" in df.columns else df.columns[19]  # T列
    df = df[df[status_col] != "承認"]

    # 日付列で並び替え（B列 = 日付）
    try:
        df["日付"] = pd.to_datetime(df["日付"])
        df = df.sort_values("日付", ascending=False)
    except:
        pass

    return df, sheet, status_col

# ====== UIと処理 ======
def main():
    if st.session_state.get("role") != "admin":
        st.warning("このページは管理者専用です。ログインしてください。")
        st.stop()

    st.title("日報承認ページ")
    SPREADSHEET_KEY = "1tDCn0Io06H2DkDK8qgMBx3l4ff9E2w_uHl3O9xMnkYE"
    SHEET_NAME = "予約一覧"

    # 日付フィルター（オプション）
    selected_date = st.date_input("表示する日付でフィルター（省略可）")

    df, sheet, status_col = load_pending_approvals(SPREADSHEET_KEY, SHEET_NAME)

    if selected_date:
        df = df[df["日付"] == pd.to_datetime(selected_date)]

    if df.empty:
        st.info("未承認の日報はありません。")
        return


# フラグの初期化
    if "approval_flags" not in st.session_state or len(st.session_state.approval_flags) != len(df):
        st.session_state.approval_flags = [False] * len(df)
    
    st.subheader("承認待ち一覧")



    for i, row in df.reset_index(drop=True).iterrows():
        unique_key = f"chk_{row['案件番号']}_{i}"
        cols = st.columns([0.05, 0.95])
        st.session_state.approval_flags[i] = cols[0].checkbox("", key=unique_key)
        cols[1].markdown(
            f"**予約番号:** {row['案件番号']}｜**日付:** {row['日付'].strftime('%Y/%m/%d')}｜"
            f"**名前:** {row['名前']}｜**報告:** {row['報告内容']}"
        )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ 承認する"):
            for i, flag in enumerate(st.session_state.approval_flags):
                if flag:
                    row_num = df.iloc[i]["行番号"]
                    sheet.update_cell(int(row_num), 20, "承認")  # T列 = index 19 + 1
            st.success("承認が完了しました。")
            st.rerun()

    with col2:
        if st.button("❌ 却下する"):
            for i, flag in enumerate(st.session_state.approval_flags):
                if flag:
                    row_num = df.iloc[i]["行番号"]
                    sheet.update_cell(int(row_num), 20, "却下")
            st.warning("却下が完了しました。")
            st.rerun()

if __name__ == "__main__":
    main()


