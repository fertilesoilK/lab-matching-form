import streamlit as st
import pandas as pd
import ast
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

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

PREDEFINED_KEYWORDS = {
    "流体工学": {
        "主要": ["流体力学"],
        "専門・詳細": ["ナビエ・ストークス方程式", "無次元化", "層流", "乱流", "低Re数", "高レイノルズ数流れ", "流れの遷移", "複雑な流れ現象", "亜音速", "粘弾性流体", "境界層", "気液混相流", "マイクロ流路"]
    },
    "熱工学・エネルギー": {
        "主要": ["熱流体", "伝熱", "エネルギー効率化"],
        "専門・詳細": ["沸騰現象", "表面張力", "濡れ現象", "マランゴニ対流", "プラントのガス漏洩検知", "有害物質拡散源推定", "熱交換器"]
    },
    "航空工学・飛行システム": {
        "主要": ["航空機", "羽ばたき飛行"],
        "専門・詳細": ["航空機翼", "航空機設計", "翼の最適化設計", "翼の空力設計", "風洞実験", "離陸飛行実験"]
    },
    "宇宙工学・推進エンジン": {
        "主要": ["宇宙環境", "エンジン"],
        "専門・詳細": ["エンジン設計", "火星飛行探索機", "JAXA", "ターボジェットエンジン", "極超音速エンジン", "複合サイクルエンジン", "スペースプレーン", "エンジン制御", "流路切替機構設計", "火星利用", "生命維持", "水電解"]
    },
    "材料科学・新素材": {
        "主要": ["複合材料", "CFRP", "炭素繊維・連続繊維", "微細加工"],
        "専門・詳細": ["セラミックス", "ダイヤモンド", "知的材料・構造", "リサイクルCFRP", "GFRP", "VARTM(樹脂注入成形)", "フラン樹脂", "成膜", "銅メッキ", "白金触媒", "プラズマ照射"]
    },
    "固体力学・構造・強度": {
        "主要": ["材料力学", "破壊力学", "材料強度学"],
        "専門・詳細": ["連続体力学", "疲労", "弾塑性力学", "強度評価", "損傷力学", "非線形破壊力学", "計算固体力学", "計算破壊力学", "繰り返し荷重", "溶接", "亀裂進展解析", "J積分", "引張試験", "曲げ試験", "衝撃強度試験", "DCB試験(層間破壊靭性試験)", "破面観察", "走査電子顕微鏡", "固体力学解析手法構築", "分子動力学", "転位動力学"]
    },
    "ロボット工学・メカトロニクス": {
        "主要": ["ロボット工学", "産業用ロボット", "ドローン", "自動化"],
        "専門・詳細": ["ロボット視覚機能付与", "協働ロボット(UR等)", "ロボットアーム", "ロボットマニピュレーション", "人工筋肉", "小型ロボットヘリコプター", "マイクロ航空機", "自立飛行", "機械機構・ロボット設計", "ロボットビジョン"]
    },
    "制御工学・振動・機械要素": {
        "主要": ["振動工学", "音響シミュレーション", "自動車への応用"],
        "専門・詳細": ["ロボット制御", "モーションキャプチャ", "飛行制御", "ロバスト制御", "ビジュアルサーボ", "電子工作", "MEMS", "レーザー加工", "流量計開発・評価", "警告音設計(自転車等)", "センサ", "ギア"]
    },
    "数値解析・シミュレーション": {
        "主要": ["数値解析", "有限要素法"],
        "専門・詳細": ["CFD解析", "CAE", "分子シミュレーション", "IGA(アイソジオメトリック解析)", "FPM(粒子法)", "重合メッシュ法", "領域積分法", "サンプリングモアレ法", "marc(非線形構造解析ソフト)", "独自解析手法の構築", "フーリエ解析", "テンソル解析"]
    },
    "AI・情報・プログラミング": {
        "主要": ["プログラミング", "人工知能", "機械学習", "画像解析"],
        "専門・詳細": ["python", "c言語", "統計解析", "情報理論・データサイエンス", "最適化", "フィジカルAI", "深層学習・CNN", "強化学習", "画像処理・物体認識", "点群処理", "fortran", "MATLAB", "Simulink", "サウンドスケープ評価"]
    },
    "バイオメカニクス・生体工学": {
        "主要": ["バイオメカニクス", "生体工学", "生物模倣"],
        "専門・詳細": ["生体機械", "聴覚・音声メカニズム", "アクティブマター・自己駆動粒子", "血流・血管の解析", "人工心臓・人工弁", "内視鏡", "がん細胞", "嚥下(えんげ)音解析"]
    },
    "医療福祉・人間工学": {
        "主要": ["医療工学", "医療・福祉支援技術", "介護支援", "感性工学"],
        "専門・詳細": ["脳波解析(睡眠・音楽)", "聴力評価(DINテスト)", "病院の音環境"]
    },
    "実験設備・ツール・その他": {
        "主要": ["3Dプリンタ", "VR音響評価"],
        "専門・詳細": ["実験装置設計", "ハイスピードカメラ", "電子顕微鏡", "マイクロスコープ", "真空装置", "着磁", "三次元計測", "フォトリソグラフィー", "電気化学", "小型燃料電池", "ROS", "Fusion", "Mac", "Claude", "Notion", "快適性評価(well-being)", "プラント安全設計"]
    }
}

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
            
        padded_records = []
        for r in records:
            while len(r) < 16:
                r.append("")
            padded_records.append(r[:16])
            
        df = pd.DataFrame(padded_records, columns=[
            "Lab_ID", "研究室名", "分野", "キーワードデータ", 
            "公式HP", "関連URL1", "関連URL2", 
            "eval_1", "eval_2", "eval_3", "eval_4", "eval_5", "eval_6",
            "core_time", "core_start", "core_end"
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
    lab_name = row['研究室名']
    with st.expander(f"【{lab_name}】 Score: {row['Match_Score']} 👈 タップして詳細を見る"):
        fields_str = "，".join(row['分野']) if isinstance(row['分野'], list) else row.get('分野', '未設定')
        
        # コアタイムの表示処理
        core_time = row.get("core_time", "")
        core_str = "未設定"
        if core_time == "あり":
            core_str = f"あり（{row.get('core_start', '')} 〜 {row.get('core_end', '')}）"
        elif core_time == "なし":
            core_str = "なし"
            
        st.write(f"【分野】 {fields_str}")
        st.write(f"【コアタイム】 {core_str}")
        
        kw_data = row['キーワードデータ']
        if isinstance(kw_data, list):
            grouped = {}
            for kw, cat in kw_data:
                if cat in ["実験・設備・その他ツール", "その他・環境・設備", "設備・実験手法・ツール", "設備・実験手法・その他ツール", "実験設備・ツール・その他"]:
                    cat = "実験設備・ツール・その他"
                if cat not in grouped:
                    grouped[cat] = []
                grouped[cat].append(kw)
            
            st.write("【関連キーワード】")
            for cat, kws in grouped.items():
                st.write(f"・<u>{cat}</u>: {', '.join(kws)}", unsafe_allow_html=True)

        if row.get('eval_1'):
            st.write("")
            st.write("【カルチャー・雰囲気】")
            
            def make_eval_row(left_text, val, right_text):
                try:
                    v = int(val)
                    boxes = ["<span style='color: rgba(128,128,128,0.4);'>□</span>"] * 5
                    if 1 <= v <= 5:
                        boxes[v-1] = '<span style="color: #4ade80; font-size: 1.1em;">■</span>'
                    indicator = "&nbsp;&nbsp;".join(boxes)
                except:
                    indicator = "&nbsp;&nbsp;".join(["<span style='color: rgba(128,128,128,0.4);'>□</span>"] * 5)
                
                return (
                    '<div style="display: flex; align-items: center; justify-content: center; margin-bottom: 8px;">'
                    f'<div style="flex: 1; text-align: right; padding-right: 15px; font-size: 0.95em;">{left_text}</div>'
                    f'<div style="flex: 0 0 auto; font-size: 1.2em; letter-spacing: 1px;">{indicator}</div>'
                    f'<div style="flex: 1; text-align: left; padding-left: 15px; font-size: 0.95em;">{right_text}</div>'
                    '</div>'
                )

            eval_html = (
                '<div style="background-color: rgba(128, 128, 128, 0.1); padding: 15px 10px 10px 10px; border-radius: 8px; margin-top: 5px; margin-bottom: 10px;">'
                + make_eval_row("実験中心", row.get('eval_1'), "解析・計算中心")
                + make_eval_row("自主性重視", row.get('eval_2'), "進捗管理あり")
                + make_eval_row("教授指導", row.get('eval_3'), "学生間サポート")
                + make_eval_row("理学(原理解明)", row.get('eval_4'), "工学(社会実装)")
                + make_eval_row("にぎやか", row.get('eval_5'), "落ち着いた")
                + make_eval_row("個人作業中心", row.get('eval_6'), "チーム作業中心")
                + '</div>'
            )
            st.markdown(eval_html, unsafe_allow_html=True)

            st.write("")
                
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
                valid_links.append(f'<a href="{url}" target="_blank">{title}</a>')
                
        if valid_links:
            st.write(f"【関連リンク】 {' / '.join(valid_links)}", unsafe_allow_html=True)
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
    st.markdown("""
    Ｂ４の先輩たちのデータをもとに，あなたの研究室選びをサポートします．
    
    ⚠️ **注意事項（非公式ツールです）**
    本サイトの情報はあくまで参考目安です．情報を鵜呑みにせず，最終的な詳細は必ず各研究室の公式ホームページや見学等で確認してください．
    
    💡 **キーワード選びのコツ**
    専門的な単語も多数含まれています．見慣れない単語がある場合は無理に選ばず，まずは直感的に気になる「主要キーワード」を中心にチェックしてみてください．
    """)

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
                        if cat in ["実験・設備・その他ツール", "その他・環境・設備", "設備・実験手法・ツール", "設備・実験手法・その他ツール", "実験設備・ツール・その他"]:
                            cat = "実験設備・ツール・その他"
                        
                        if cat not in grouped_keywords: grouped_keywords[cat] = set()
                        grouped_keywords[cat].add(kw)

        all_categories = sorted(list(grouped_keywords.keys()))
        if "実験設備・ツール・その他" in all_categories:
            all_categories.remove("実験設備・ツール・その他")
            all_categories.append("実験設備・ツール・その他")

        selected_themes = []

        st.markdown("### ■ 主要キーワードから選ぶ")
        for category in all_categories:
            keywords_set = grouped_keywords[category]
            pref_dict = PREDEFINED_KEYWORDS.get(category, {"主要": [], "専門・詳細": []})
            basic_kws = [kw for kw in pref_dict.get("主要", []) if kw in keywords_set]
            
            if basic_kws:
                st.write(f"▼ 【{category}】")
                cols = st.columns(3)
                for i, kw in enumerate(basic_kws):
                    if cols[i % 3].checkbox(kw, key=f"b3_main_{category}_{kw}"):
                        selected_themes.append(kw)
        st.write("")

        st.markdown("### ■ 専門・詳細キーワードから選ぶ")
        for category in all_categories:
            keywords_set = grouped_keywords[category]
            pref_dict = PREDEFINED_KEYWORDS.get(category, {"主要": [], "専門・詳細": []})
            
            adv_kws = [kw for kw in pref_dict.get("専門・詳細", []) if kw in keywords_set]
            known_kws = set(pref_dict.get("主要", [])) | set(pref_dict.get("専門・詳細", []))
            others = sorted([kw for kw in keywords_set if kw not in known_kws])
            
            combined_adv = adv_kws + others
            
            if combined_adv:
                st.write(f"▼ 【{category}】")
                cols = st.columns(3)
                for i, kw in enumerate(combined_adv):
                    if cols[i % 3].checkbox(kw, key=f"b3_adv_{category}_{kw}"):
                        selected_themes.append(kw)
        st.write("")

    else:
        st.write("※上の選択欄で分野を選ぶと，該当する研究室のキーワードが表示されます．")
        selected_themes = []

    st.markdown("---") 

    if st.button("診断する", type="primary", disabled=target_df.empty): 
        all_basic_kws = set()
        for category, groups in PREDEFINED_KEYWORDS.items():
            all_basic_kws.update(groups.get("主要", []))

        scores = []
        for index, row in target_df.iterrows():
            score = 0
            b3_themes = set(selected_themes)
            
            lab_kws = set()
            if isinstance(row["キーワードデータ"], list):
                for kw_tuple in row["キーワードデータ"]:
                    if len(kw_tuple) >= 1:
                        lab_kws.add(kw_tuple[0])
            
            matched_kws = b3_themes.intersection(lab_kws)
            for kw in matched_kws:
                if kw in all_basic_kws:
                    score += 30
                else:
                    score += 10
                    
            scores.append(score)
            
        result_df = target_df.copy()
        result_df["Match_Score"] = scores
        result_df = result_df.sort_values(by="Match_Score", ascending=False)

        st.subheader("診断結果")
        
        st.info("""
        💡 診断の仕組み
        あなたが選択したキーワードと，各研究室が登録したキーワードが一致した場合，以下の基準で加点を行っています．
        ・主要キーワードが一致：30点
        ・専門・詳細キーワードが一致：10点
        
        ※各研究室で登録キーワード数に差があるため，総数が多い研究室ほど点数が高くなる傾向があります．このスコアはあくまで一つの目安ですので，詳細は各研究室のホームページを必ず確認してください．
        """)
        
        st.info("💡 【参考】機械工学科の公式ページも確認してみましょう\n\n[学科公式HP 研究室一覧はこちら](https://www.rs.tus.ac.jp/me/laboratory.html)", icon="ℹ️")
        
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