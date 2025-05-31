import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime

# ===== 認証と設定 =====
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

def fetch_pending_reports():
    client = get_gspread_client()
    sheet = client.open_by_key(SPREADSHEET_KEY).worksheet(SHEET_NAME)
    data = sheet.get_all_values()

    if len(data) < 4:
        return pd.DataFrame(), sheet

    headers = data[2]
    records = data[3:]

    df = pd.DataFrame(records, columns=headers)
    df["行番号"] = range(4, 4 + len(df))  # 実際のシート行番号

    # 日付変換
    df["登録日"] = pd.to_datetime(df["登録日"], errors="coerce")

    if "承認" in df.columns:
        df = df[~df["承認"].fillna("").isin(["承認", "却下"])]


    return df, sheet

# ===== アプリ本体 =====
def main():
    if st.session_state.get("role") != "admin":
        st.error("このページは管理者専用です。")
        st.stop()

    st.title("📝 日報承認ページ")

    df, sheet = fetch_pending_reports()
    if df.empty:
        st.info("未承認の日報はありません。")
        return

    # ===== フィルター =====
    st.sidebar.header("🔎 フィルター")
    date_filter = st.sidebar.date_input("登録日で絞り込み", value=None)
    users = sorted(df["報告者"].dropna().unique())
    user_filter = st.sidebar.selectbox("報告者で絞り込み", ["すべて"] + users)

    if date_filter:
        df = df[df["登録日"].dt.date == date_filter]
    if user_filter != "すべて":
        df = df[df["報告者"] == user_filter]

    if df.empty:
        st.info("絞り込み結果に一致する日報はありません。")
        return

    # ===== チェックボックスとコメント欄の初期化 =====
    if "approval_flags" not in st.session_state or len(st.session_state.approval_flags) != len(df):
        st.session_state.approval_flags = [False] * len(df)
    if "reject_comments" not in st.session_state or len(st.session_state.reject_comments) != len(df):
        st.session_state.reject_comments = [""] * len(df)

    st.subheader("承認待ち一覧")

    for i, row in df.reset_index(drop=True).iterrows():
        unique_key = f"{row['ID']}_{i}"
        cols = st.columns([0.05, 0.7, 0.25])
        st.session_state.approval_flags[i] = cols[0].checkbox("", key=f"chk_{unique_key}")
        date_str = row["登録日"].strftime("%Y/%m/%d") if pd.notnull(row["登録日"]) else "未登録"
        cols[1].markdown(
            f"**ID:** {row['ID']}｜**登録日:** {date_str}｜"
            f"**報告者:** {row['報告者']}｜**ゴルフ場:** {row['ゴルフ場']}｜**報告:** {row['報告']}"
        )
        st.session_state.reject_comments[i] = cols[2].text_input(
            "却下コメント", value=st.session_state.reject_comments[i], key=f"comment_{unique_key}"
        )

    # ===== ボタン処理 =====
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ 承認する"):
            for i, flag in enumerate(st.session_state.approval_flags):
                if flag:
                    row_num = df.iloc[i]["行番号"]
                    sheet.update_cell(int(row_num), 20, "承認")
            st.success("承認が完了しました。")
            st.rerun()

    with col2:
        if st.button("❌ 却下する"):
            for i, flag in enumerate(st.session_state.approval_flags):
                if flag:
                    row_num = df.iloc[i]["行番号"]
                    comment = st.session_state.reject_comments[i]
                    sheet.update_cell(int(row_num), 20, "却下")
                    sheet.update_cell(int(row_num), 36, comment)  # AJ列 (index 35)
            st.warning("却下が完了しました。")
            st.rerun()

if __name__ == "__main__":
    main()






# import streamlit as st
# import gspread
# import pandas as pd
# from google.oauth2.service_account import Credentials
# from datetime import datetime

# # ====== 認証とクライアント取得 ======
# SCOPES = [
#     "https://www.googleapis.com/auth/spreadsheets",
#     "https://www.googleapis.com/auth/drive"
# ]

# SPREADSHEET_KEY = "1tDCn0Io06H2DkDK8qgMBx3l4ff9E2w_uHl3O9xMnkYE"
# SHEET_NAME = "予約一覧"

# @st.cache_resource
# def get_gspread_client():
#     credentials = Credentials.from_service_account_info(
#         st.secrets["gcp_service_account"], scopes=SCOPES
#     )
#     return gspread.authorize(credentials)


# # ====== データ取得関数 ======
# def fetch_pending_reports():
    
#     client = get_gspread_client()
#     sheet = client.open_by_key(SPREADSHEET_KEY).worksheet(SHEET_NAME)
#     data = sheet.get_all_values()

#     if len(data) < 4:
#         return pd.DataFrame(), sheet

#     headers = data[2]  # 3行目
#     records = data[3:]  # 4行目～

#     df = pd.DataFrame(records, columns=headers)
#     df["行番号"] = range(4, 4 + len(df))

#     # 承認ステータスを確認（T列: index 19）
#     if len(df.columns) <= 19:
#         return pd.DataFrame(), sheet

#     df = df[df[df.columns[19]].fillna("") != "承認"]

#     # 登録日を日付型に変換（失敗は NaT）
#     df["登録日"] = pd.to_datetime(df["登録日"], errors="coerce")
#     df = df.sort_values("登録日", ascending=False)

#     return df, sheet


# # ====== UIと処理 ======
# def main():
#     if st.session_state.get("role") != "admin":
#         st.warning("このページは管理者専用です。ログインしてください。")
#         st.stop()

#     st.title("📝 日報承認ページ")

#     df, sheet = fetch_pending_reports()

#     if df.empty:
#         st.info("未承認の日報はありません。")
#         return

#     # ===== フィルターエリア =====
#     st.sidebar.header("🔎 フィルター")
#     date_filter = st.sidebar.date_input("登録日で絞り込み", value=None)
#     users = sorted(df["報告者"].dropna().unique())
#     user_filter = st.sidebar.selectbox("報告者で絞り込み", ["すべて"] + users)

#     if date_filter:
#         df = df[df["登録日"].dt.date == date_filter]
#     if user_filter != "すべて":
#         df = df[df["報告者"] == user_filter]

#     if df.empty:
#         st.info("絞り込み結果に一致する日報はありません。")
#         return

#     # ===== セッション状態初期化 =====
#     if "approval_flags" not in st.session_state or len(st.session_state.approval_flags) != len(df):
#         st.session_state.approval_flags = [False] * len(df)
#     if "reject_comments" not in st.session_state or len(st.session_state.reject_comments) != len(df):
#         st.session_state.reject_comments = [""] * len(df)

#     st.subheader("📋 承認待ち一覧")

#     # ===== 表示と入力欄 =====
#     for i, row in df.reset_index(drop=True).iterrows():
#         unique_key = f"{row['ID']}_{i}"
#         cols = st.columns([0.05, 0.7, 0.25])

#         st.session_state.approval_flags[i] = cols[0].checkbox("", key=f"chk_{unique_key}")

#         date_str = row["登録日"].strftime("%Y/%m/%d") if pd.notnull(row["登録日"]) else "未登録"
#         cols[1].markdown(
#             f"**ID:** {row['ID']}｜**登録日:** {date_str}｜"
#             f"**報告者:** {row['報告者']}｜**報告:** {row['報告']}"
#         )

#         st.session_state.reject_comments[i] = cols[2].text_input(
#             "却下コメント", value=st.session_state.reject_comments[i], key=f"comment_{unique_key}"
#         )

#     # ===== ボタン処理 =====
#     col1, col2 = st.columns(2)
#     with col1:
#         if st.button("✅ 承認する"):
#             for i, flag in enumerate(st.session_state.approval_flags):
#                 if flag:
#                     row_num = df.iloc[i]["行番号"]
#                     sheet.update_cell(int(row_num), 20, "承認")
#             st.success("承認が完了しました。")
#             st.rerun()

#     with col2:
#         if st.button("❌ 却下する"):
#             for i, flag in enumerate(st.session_state.approval_flags):
#                 if flag:
#                     row_num = df.iloc[i]["行番号"]
#                     comment = st.session_state.reject_comments[i]
    
#                     # 空文字対策（任意）
#                     if not comment.strip():
#                         st.warning(f"{df.iloc[i]['ID']} の却下コメントが空です。")
#                         continue
    
#                     # スプレッドシート更新
#                     sheet.update_cell(int(row_num), 20, "却下")  # T列
#                     sheet.update_cell(int(row_num), 36, comment)  # AJ列（36列目）
    
#             st.warning("却下が完了しました。")
#             st.rerun()


# if __name__ == "__main__":
#     main()
