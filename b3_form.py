import streamlit as st
import pandas as pd
import ast
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 研究室のURLリスト（初期値）
LAB_URLS = {
    "上野研究室": {"公式HP": "https://www.rs.tus.ac.jp/ueno_lab/index.html", "関連URL": "https://dept.tus.ac.jp/st/souiki-journal/6754/"},
    "塚原研究室": {"公式HP": "https://www.rs.tus.ac.jp/~t2lab/index-j.html", "関連URL": "https://www.jsme-fed.org/laboratories/2023_12/001.html"},
    "青野研究室": {"公式HP": "https://sites.google.com/view/hikaruaono/home"},
    "田口研究室": {"公式HP": ""},
    "高橋研究室": {"公式HP": "https://www.rs.tus.ac.jp/takahashi_lab/", "関連URL": "https://dept.tus.ac.jp/st/teachers/3508/"},
    "岡田研究室": {"関連URL": "https://www.rs.noda.tus.ac.jp/okadalab/"},
    "松崎研究室": {"公式HP": "https://www.rs.tus.ac.jp/rmatsuza/"},
    "荻原研究室": {"公式HP": "https://www.rs.tus.ac.jp/~ogihara_lab/"},
    "早瀬研究室": {"公式HP": "https://www.rs.noda.tus.ac.jp/mhayase/"},
    "荒井研究室": {"公式HP": "https://www.rs.tus.ac.jp/ir/index.html"},
    "竹村研究室": {"公式HP": "https://www.rs.tus.ac.jp/brlab/", "関連URL": "https://dept.tus.ac.jp/st/teachers/5193/"},
    "朝倉研究室": {"公式HP": "https://asakura-lab.labby.jp/"}
}

# 10分間（600秒）データを記憶するキャッシュ機能を追加
@st.cache_data(ttl=600)
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
            
        # データ列数の変化に対応（最大13列までパディング）
        padded_records = []
        for r in records:
            while len(r) < 13:
                r.append("")
            padded_records.append(r[:13])
            
        df = pd.DataFrame(padded_records, columns=[
            "Lab_ID", "研究室名", "分野", "キーワードデータ", 
            "公式HP", "関連URL1", "関連URL2", 
            "eval_1", "eval_2", "eval_3", "eval_4", "eval_5", "eval_6"
        ])
        
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
    lab_name = row['研究室名']
    # ここにタップを促す文言を追加しています
    with st.expander(f"【{lab_name}】 Score: {row['Match_Score']} 👈 タップして詳細を見る"):
        fields_str = "，".join(row['分野']) if isinstance(row['分野'], list) else row.get('分野', '未設定')
        st.write(f"【分野】 {fields_str}")
        
        kw_data = row['キーワードデータ']
        if isinstance(kw_data, list):
            grouped = {}
            for kw, cat in kw_data:
                cat = "その他・環境・設備" if cat in ["実験・設備・その他ツール", "その他・環境・設備"] else cat
                if cat not in grouped:
                    grouped[cat] = []
                grouped[cat].append(kw)
            
            st.write("【関連キーワード】")
            for cat, kws in grouped.items():
                st.write(f"・<u>{cat}</u>: {', '.join(kws)}", unsafe_allow_html=True)

        # カルチャー・雰囲気の表示
        if row.get('eval_1'):
            st.write("")
            st.write("【カルチャー・雰囲気】")
            
            def get_indicator(val):
                try:
                    v = int(val)
                    boxes = ["□", "□", "□", "□", "□"]
                    if 1 <= v <= 5:
                        boxes[v-1] = '<span style="color: #4ade80;">■</span>'
                    return " ".join(boxes)
                except:
                    return "□ □ □ □ □"
            
            st.markdown(f"・ 実験メイン {get_indicator(row['eval_1'])} 解析メイン", unsafe_allow_html=True)
            st.markdown(f"・ 学生の自主性に任せる {get_indicator(row['eval_2'])} スケジュール管理が手厚い", unsafe_allow_html=True)
            st.markdown(f"・ 教授指導 {get_indicator(row['eval_3'])} 学生間のサポート中心", unsafe_allow_html=True)
            st.markdown(f"・ 基礎原理の解明(理学) {get_indicator(row['eval_4'])} 社会実装・開発(工学)", unsafe_allow_html=True)
            st.markdown(f"・ 和気あいあい(カジュアル) {get_indicator(row['eval_5'])} 規律・礼儀重視(フォーマル)", unsafe_allow_html=True)
            st.markdown(f"・ 個人作業が中心 {get_indicator(row['eval_6'])} チーム共同作業が中心", unsafe_allow_html=True)

            st.write("")
                
        # URLの動的表示処理
        lab_urls_dict = LAB_URLS.get(lab_name, {}).copy()
        
        if pd.notna(row.get('公式HP')) and str(row['公式HP']).strip():
            lab_urls_dict["公式HP"] = str(row['公式HP']).strip()
        if pd.notna(row.get('関連URL1')) and str(row['関連URL1']).strip():
            lab_urls_dict["関連URL 1"] = str(row['関連URL1']).strip()
        if pd.notna(row.get('関連URL2')) and str(row['関連URL2']).strip():
            lab_urls_dict["関連URL 2"] = str(row['関連URL2']).strip()
            
        valid_links = []
        for title, url in lab_urls_dict.items():
            if url.strip():
                valid_links.append(f"[{title}]({url})")
                
        if valid_links:
            st.write(f"【関連リンク】 {' / '.join(valid_links)}")
        else:
            st.write("【関連リンク】 (URL未設定)")

def main():
    st.set_page_config(page_title="ME研究室マッチング", layout="wide")
    
    st.markdown("""
    <style>
    div[data-testid="stCheckbox"] input[type="checkbox"] { transform: scale(1.3); }
    div[data-testid="stCheckbox"] label { font-size: 1.05em; margin-left: 5px; }
    </style>
    """, unsafe_allow_html=True)

    st.title("ME研究室マッチングシステム")
    st.write("Ｂ４の先輩たちのデータをもとに，あなたにぴったりの研究室を診断します．非公式なサイトのため，情報を鵜呑みにしないようにしましょう．詳細は各研究室に訪問することをおすすめします．")

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
                        if cat in ["実験・設備・その他ツール", "その他・環境・設備"]:
                            cat = "その他・環境・設備"
                        
                        if cat not in grouped_keywords: grouped_keywords[cat] = set()
                        grouped_keywords[cat].add(kw)

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
        
        st.info("💡 【参考】機械工学科の公式ページも確認してみましょう\n\n[学科公式HP 研究室一覧はこちら](https://www.rs.tus.ac.jp/me/laboratory.html)")
        
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