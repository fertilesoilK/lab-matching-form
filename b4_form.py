import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import datetime

ROMAJI_DICT = {
    "上野研究室": "ueno", "塚原研究室": "tsukahara", "青野研究室": "aono",
    "田口研究室": "taguchi", "高橋研究室": "takahashi", "岡田研究室": "okada",
    "松崎研究室": "matsuzaki", "荻原研究室": "ogihara", "早瀬研究室": "hayase",
    "荒井研究室": "arai", "竹村研究室": "takemura", "朝倉研究室": "asakura"
}

CATEGORY_LIST = [
    "流体工学", "熱工学・エネルギー", "航空工学・飛行システム", "宇宙工学・推進エンジン",
    "材料科学・新素材", "固体力学・構造・強度", "ロボット工学・メカトロニクス",
    "制御工学・振動・機械要素", "数値解析・シミュレーション", "AI・情報・プログラミング",
    "バイオメカニクス・生体工学", "医療福祉・人間工学", "実験設備・ツール・その他"
]

def save_data(data_dict):
    sheet_id = st.secrets["sheet_id"]
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    sheet = client.open_by_key(sheet_id).sheet1
    
    # 既存の13項目に加え、コアタイム関連の3項目を末尾に追加
    row_values = [
        data_dict["Lab_ID"],
        data_dict["研究室名"],
        data_dict["分野"],
        data_dict["キーワードデータ"],
        data_dict.get("公式HP", ""),
        data_dict.get("関連URL1", ""),
        data_dict.get("関連URL2", ""),
        data_dict.get("eval_1", ""),
        data_dict.get("eval_2", ""),
        data_dict.get("eval_3", ""),
        data_dict.get("eval_4", ""),
        data_dict.get("eval_5", ""),
        data_dict.get("eval_6", ""),
        data_dict.get("core_time", ""),
        data_dict.get("core_start", ""),
        data_dict.get("core_end", "")
    ]
    sheet.append_row(row_values)

def main():
    st.markdown("""
    <style>
    div[data-testid="stCheckbox"] input[type="checkbox"] {
        transform: scale(1.5);
    }
    div[data-testid="stCheckbox"] label {
        font-size: 1.1em;
        margin-left: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.set_page_config(page_title="【B4向け】研究室情報登録フォーム", layout="wide")
    st.title("B4向け研究室情報 登録フォーム")
    st.write("必要不可欠な単語を除き，できる限りB3が理解可能な単語を入力してください．選んだキーワードがそのままB3のもとへ届きます．選択肢以上に適切なキーワードがある場合は，該当する選択肢にチェックは入れず，「選択肢にないワードを追加」の欄でキーワードを追加してください．")

    st.markdown("---")

    st.header("1. 基本情報")
    lab_name = st.selectbox("■ 研究室名", ["選択してください"] + list(ROMAJI_DICT.keys()))
    fields = st.multiselect("■ 研究室全体の分野（複数選択可）", ["熱", "流体", "材料", "制御", "振動学"])

    st.markdown("---")
    st.header("2. 研究キーワードの登録")
    
    categorized_keywords = {
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

    selected_kw_pairs = []

    st.markdown("### ■ 主要キーワードから選ぶ")
    for category, groups in categorized_keywords.items():
        if groups["主要"]:
            st.write(f"▼ 【{category}】")
            cols = st.columns(3)
            for i, kw in enumerate(groups["主要"]):
                if cols[i % 3].checkbox(kw, key=f"main_{category}_{kw}"):
                    selected_kw_pairs.append((kw, category, "主要"))
    st.write("")

    st.markdown("### ■ 専門・詳細キーワードから選ぶ")
    for category, groups in categorized_keywords.items():
        if groups["専門・詳細"]:
            st.write(f"▼ 【{category}】")
            cols = st.columns(3)
            for i, kw in enumerate(groups["専門・詳細"]):
                if cols[i % 3].checkbox(kw, key=f"adv_{category}_{kw}"):
                    selected_kw_pairs.append((kw, category, "専門"))
    st.write("")

    st.markdown("---")
    st.write("■ 選択肢にないキーワードを追加")

    if "custom_kw_ids" not in st.session_state:
        st.session_state.custom_kw_ids = [0]
        st.session_state.next_kw_id = 1

    def remove_row(row_id):
        st.session_state.custom_kw_ids.remove(row_id)

    for row_id in st.session_state.custom_kw_ids:
        col_c1, col_c2, col_c3 = st.columns([2, 1, 0.5])
        with col_c1:
            kw_text = st.text_input(f"追加キーワード", key=f"custom_kw_{row_id}")
        with col_c2:
            cat_select = st.selectbox(f"分野", CATEGORY_LIST, key=f"custom_cat_{row_id}")
        with col_c3:
            st.write("##")
            if st.button("－", key=f"del_{row_id}"):
                remove_row(row_id)
                st.rerun()
        
        if kw_text.strip():
            selected_kw_pairs.append((kw_text.strip(), cat_select, "専門"))

    if st.button("＋ 欄を追加", key="add_kw"):
        st.session_state.custom_kw_ids.append(st.session_state.next_kw_id)
        st.session_state.next_kw_id += 1
        st.rerun()

    st.markdown("---")

    st.header("3. 研究室のカルチャー・雰囲気 (5段階評価)")
    st.write("研究室のスタイルに近いものを選んでください．")
    
    q1 = st.radio("■ 実験か解析か (1: 実験中心 ⇔ 5: 解析・計算中心)", options=[1, 2, 3, 4, 5], index=2, horizontal=True)
    q2 = st.radio("■ スケジュール・拘束度 (1: 自主性重視 ⇔ 5: 進捗管理あり)", options=[1, 2, 3, 4, 5], index=2, horizontal=True)
    q3 = st.radio("■ サポート体制 (1: 教授指導 ⇔ 5: 学生間サポート)", options=[1, 2, 3, 4, 5], index=2, horizontal=True)
    q4 = st.radio("■ 研究アプローチ (1: 理学(原理解明) ⇔ 5: 工学(社会実装))", options=[1, 2, 3, 4, 5], index=2, horizontal=True)
    q5 = st.radio("■ 研究室の雰囲気 (1: にぎやか ⇔ 5: 落ち着いた)", options=[1, 2, 3, 4, 5], index=2, horizontal=True)
    q6 = st.radio("■ 研究の進め方 (1: 個人作業中心 ⇔ 5: チーム作業中心)", options=[1, 2, 3, 4, 5], index=2, horizontal=True)

    st.markdown("---")
    
    st.header("4. コアタイムについて")
    has_core_time = st.radio("■ コアタイムはありますか？", ["なし", "あり"], horizontal=True)
    
    core_start_str = ""
    core_end_str = ""
    
    if has_core_time == "あり":
        col1, col2 = st.columns(2)
        with col1:
            core_start = st.time_input("開始時刻", value=datetime.time(9, 0))
        with col2:
            core_end = st.time_input("終了時刻", value=datetime.time(17, 0))
        
        # 時刻を文字列(HH:MM)に変換
        core_start_str = core_start.strftime("%H:%M")
        core_end_str = core_end.strftime("%H:%M")

    st.markdown("---")
    
    st.header("5. 研究室の関連URLの登録（任意）")
    st.write("B3向けに案内したい研究室の公式HPや，関連するURLを入力してください．")
    official_url = st.text_input("■ 公式HPのURL（任意）")
    related_url_1 = st.text_input("■ 関連URL 1（任意）")
    related_url_2 = st.text_input("■ 関連URL 2（任意）")
    
    st.markdown("---")

    if st.button("この内容で登録する", type="primary"):
        if lab_name == "選択してください" or len(fields) == 0:
            st.error("研究室名と分野は必須項目です．")
        elif not selected_kw_pairs:
            st.error("少なくとも1つのキーワードを選択または入力してください．")
        else:
            final_kw_data = list(set(selected_kw_pairs))
            data_to_save = {
                "Lab_ID": f"{ROMAJI_DICT[lab_name]}",
                "研究室名": lab_name,
                "分野": str(fields),
                "キーワードデータ": str(final_kw_data),
                "公式HP": official_url.strip(),
                "関連URL1": related_url_1.strip(),
                "関連URL2": related_url_2.strip(),
                "eval_1": str(q1),
                "eval_2": str(q2),
                "eval_3": str(q3),
                "eval_4": str(q4),
                "eval_5": str(q5),
                "eval_6": str(q6),
                "core_time": has_core_time,
                "core_start": core_start_str,
                "core_end": core_end_str
            }
            save_data(data_to_save)
            st.success(f"「{lab_name}」のデータを登録しました！")

if __name__ == "__main__":
    main()