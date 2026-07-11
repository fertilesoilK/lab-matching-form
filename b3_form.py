import streamlit as st
import pandas as pd
import ast
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def load_spreadsheet_data():
    try:
        sheet_id = st.secrets["sheet_id"]
        creds_dict = json.loads(st.secrets["gcp_service_account"])
        
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        sheet = client.open_by_key(sheet_id).sheet1
        records = sheet.get_all_values()
        
        if not records:
            return pd.DataFrame()
            
        df = pd.DataFrame(records, columns=["Lab_ID", "研究室名", "分野", "キーワードデータ"])
        
        def safe_eval(val):
            try:
                if isinstance(val, str) and val.startswith('['):
                    return ast.literal_eval(val)
                return []
            except:
                return []

        df["分野"] = df["分野"].apply(safe_eval)
        df["キーワードデータ"] = df["キーワードデータ"].apply(safe_eval)
        
        return df
    except Exception as e:
        st.error(f"スプレッドシートの読み込み中にエラーが発生しました: {e}")
        return pd.DataFrame()

def display_lab_details(row):
    """研究室の詳細を表示する共通関数"""
    with st.expander(f"【{row['研究室名']}】 Score: {row['Match_Score']}"):
        fields_str = "，".join(row['分野']) if isinstance(row['分野'], list) else row.get('分野', '未設定')
        st.write(f"【分野】 {fields_str}")
        
        kw_data = row['キーワードデータ']
        if isinstance(kw_data, list):
            grouped = {}
            for kw, cat in kw_data:
                # データのカテゴリを統一
                cat = "その他・環境・設備" if cat in ["実験・設備・その他ツール", "その他・環境・設備"] else cat
                if cat not in grouped:
                    grouped[cat] = []
                grouped[cat].append(kw)
            
            st.write("【関連キーワード】")
            for cat, kws in grouped.items():
                st.write(f"・**{cat}**: {', '.join(kws)}")

def main():
    st.set_page_config(page_title="研究室マッチング", layout="wide")
    
    st.markdown("""
    <style>
    div[data-testid="stCheckbox"] input[type="checkbox"] { transform: scale(1.3); }
    div[data-testid="stCheckbox"] label { font-size: 1.05em; margin-left: 5px; }
    </style>
    """, unsafe_allow_html=True)

    st.title("研究室マッチングシステム")
    st.write("Ｂ４の先輩たちのデータをもとに，あなたにぴったりの研究室を診断します．非公式なサイトのため，情報をうのみにしないようにしましょう．詳細は各研究室に訪問することをおすすめします．")

    df = load_spreadsheet_data()
    if df.empty:
        st.warning("研究室のデータが見つかりません．スプレッドシートにデータが登録されているか確認してください．")
        return

    st.markdown("---") 
    st.header("希望条件を入力してください")
    
    target_mode = st.radio("研究室をどの範囲から探しますか？", ["全ての研究室から診断する", "分野を絞って診断する"], label_visibility="collapsed")
    all_fields_set = set()
    for fields_list in df["分野"]:
        if isinstance(fields_list, list): all_fields_set.update(fields_list)
    available_fields = sorted(list(all_fields_set))

    if target_mode == "分野を絞って診断する":
        selected_fields = st.multiselect("診断したい分野を選択してください（複数可）", available_fields)
        target_df = df[df["分野"].apply(lambda x: any(field in x for field in selected_fields))] if selected_fields else pd.DataFrame(columns=df.columns)
    else:
        target_df = df

    st.write("") 
    st.write("■ 気になるキーワードを選択（複数可）")
    
    if not target_df.empty:
        grouped_keywords = {}
        for kw_list in target_df["キーワードデータ"]:
            if isinstance(kw_list, list):
                for kw_tuple in kw_list:
                    if len(kw_tuple) >= 2:
                        kw, cat = kw_tuple[0], kw_tuple[1]
                        # データを統一
                        if cat in ["実験・設備・その他ツール", "その他・環境・設備"]:
                            cat = "その他・環境・設備"
                        
                        if cat not in grouped_keywords: grouped_keywords[cat] = set()
                        grouped_keywords[cat].add(kw)

        # カテゴリの並び替え（その他を最後にする）
        all_categories = sorted(list(grouped_keywords.keys()))
        if "その他・環境・設備" in all_categories:
            all_categories.remove("その他・環境・設備")
            all_categories.append("その他・環境・設備")

        selected_themes = []
        for category in all_categories:
            keywords = grouped_keywords[category]
            st.write(f"▼ 【{category}】")
            cols = st.columns(3)
            for i, kw in enumerate(sorted(list(keywords))):
                # ★ここが重要：categoryを含めることで重複を防ぐ
                if cols[i % 3].checkbox(kw, key=f"b3_{category}_{kw}"):
                    selected_themes.append(kw)
            st.write("")
    else:
        st.write("※上の選択欄で分野を選ぶと，該当する研究室のキーワードが表示されます．")
        selected_themes = []

    st.markdown("---") 

    if st.button("診断する", type="primary", disabled=target_df.empty): 
        scores = []
        for index, row in target_df.iterrows():
            score = 0
            b3_themes = set(selected_themes)
            
            lab_kws = set()
            if isinstance(row["キーワードデータ"], list):
                for kw_tuple in row["キーワードデータ"]:
                    if len(kw_tuple) >= 1:
                        lab_kws.add(kw_tuple[0])
            
            score += len(b3_themes.intersection(lab_kws)) * 10
            scores.append(score)
            
        result_df = target_df.copy()
        result_df["Match_Score"] = scores
        result_df = result_df.sort_values(by="Match_Score", ascending=False)

        st.subheader("診断結果")
        if len(selected_themes) == 0:
            for index, row in result_df.iterrows():
                display_lab_details(row)
        else:
            recommended_df = result_df[result_df["Match_Score"] > 0]
            st.write("### おすすめの研究室")
            if recommended_df.empty:
                st.info("条件に一致する研究室はありませんでした．")
            else:
                for index, row in recommended_df.iterrows():
                    display_lab_details(row)
            
            others_df = result_df[result_df["Match_Score"] == 0]
            if not others_df.empty:
                st.markdown("---")
                st.write("### その他の研究室")
                for index, row in others_df.iterrows():
                    display_lab_details(row)

if __name__ == "__main__":
    main()