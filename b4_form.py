import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

ROMAJI_DICT = {
    "上野研究室": "ueno", "塚原研究室": "tsukahara", "青野研究室": "aono",
    "田口研究室": "taguchi", "高橋研究室": "takahashi", "岡田研究室": "okada",
    "松崎研究室": "matsuzaki", "荻原研究室": "ogihara", "早瀬研究室": "hayase",
    "荒井研究室": "arai", "竹村研究室": "takemura", "朝倉研究室": "asakura"
}

CATEGORY_LIST = [
    "流体・熱・エネルギー", "航空・宇宙", "材料・構造・固体力学", 
    "ロボティクス・制御・機械要素", "解析・シミュレーション・情報", 
    "生体・医療・バイオメカニクス", "設備・実験手法・ツール"
]

def save_data(data_dict):
    sheet_id = st.secrets["sheet_id"]
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    sheet = client.open_by_key(sheet_id).sheet1
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
        data_dict.get("eval_6", "")
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
        "流体・熱・エネルギー": ["流体", "低Re数", "無次元化", "層流", "表面張力", "マランゴニ対流", "沸騰現象", "気液混相流", "伝熱", "エネルギー効率", "マイクロ流路", "濡れ現象", "乱流", "流体力学", "熱流体", "ナビエ・ストークス方程式", "流れの遷移", "粘弾性流体", "熱交換器", "境界層", "複雑な流れ現象", "高レイノルズ数流れ", "亜音速", "プラントのガス漏洩検知"],
        "航空・宇宙": ["スペースプレーン", "極超音速エンジン", "ターボジェットエンジン", "複合サイクルエンジン", "エンジン制御", "エンジン設計", "流路切替機構設計", "航空機設計", "離陸飛行実験", "風洞実験", "航空機翼", "翼の空力設計", "翼の最適化設計", "航空機", "宇宙環境", "火星利用", "NASA", "JAXA", "生命維持", "水電解"],
        "材料・構造・固体力学": ["複合材料", "CFRP", "GFRP", "セラミックス", "引張試験", "破壊力学", "DCB試験", "リサイクルCFRP", "フラン樹脂", "衝撃強度試験", "コンプライアンス", "走査電子顕微鏡", "破面観察", "プラズマ照射", "ダイヤモンド", "銅メッキ", "白金触媒", "成膜", "材料力学", "連続体力学", "弾塑性力学", "損傷力学", "材料強度学", "非線形破壊力学", "繰り返し荷重", "溶接", "強度評価", "疲労", "亀裂進展", "J積分"],
        "ロボティクス・制御・機械要素": ["ロボット", "ロボットアーム", "自動化", "センサ", "ドローン", "人工筋肉", "設計", "モーションキャプチャ", "羽ばたき", "マイクロ航空機", "自立飛行", "飛行制御", "ロバスト制御", "電子工作", "ギア", "MEMS", "レーザー加工", "小型ロボットヘリコプター", "流量計開発・評価"],
        "解析・シミュレーション・情報": ["CFD解析", "数値解析", "画像解析", "MATLAB", "プログラミング", "フーリエ解析", "人工知能", "機械学習", "有限要素法", "サンプリングモアレ法", "強化学習", "CAE", "IGA", "FPM", "重合メッシュ法", "プログラム実装", "fortran", "c言語", "python", "テンソル解析", "領域積分法", "Simulink", "統計", "marc", "深層学習・CNN", "情報理論・データサイエンス", "解析手法構築"],
        "生体・医療・バイオメカニクス": ["生体機械", "バイオメカニクス", "脳波", "介護支援", "内視鏡", "生物模倣", "生体工学", "がん細胞", "血流・血管の解析", "人工心臓・人工弁", "アクティブマター・自己駆動粒子"],
        "設備・実験手法・ツール": ["実験", "実験装置設計", "ハイスピードカメラ", "電子顕微鏡", "真空装置", "着磁", "3Dプリンタ", "Fusion", "理学", "Mac", "リモート", "VR", "共同研究", "Claude", "Notion", "フォトリソグラフィー", "電気化学", "小型燃料電池"]
    }

    selected_kw_pairs = []

    for category, keywords in categorized_keywords.items():
        st.write(f"▼ 【{category}】")
        cols = st.columns(3)
        for i, kw in enumerate(keywords):
            if cols[i % 3].checkbox(kw, key=f"kw_{kw}"):
                selected_kw_pairs.append((kw, category))
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
            selected_kw_pairs.append((kw_text.strip(), cat_select))

    if st.button("＋ 欄を追加", key="add_kw"):
        st.session_state.custom_kw_ids.append(st.session_state.next_kw_id)
        st.session_state.next_kw_id += 1
        st.rerun()

    st.markdown("---")

    st.header("3. 研究室のカルチャー・雰囲気 (5段階評価)")
    st.write("研究室のスタイルに近いものを選んでください．")
    
    q1 = st.radio("■ 実験か解析か (1: 実験メイン ⇔ 5: 解析・シミュレーションメイン)", options=[1, 2, 3, 4, 5], index=2, horizontal=True)
    q2 = st.radio("■ スケジュール・拘束度 (1: 学生の自主性に任せられる ⇔ 5: 研究室側によるスケジュール管理が手厚い)", options=[1, 2, 3, 4, 5], index=2, horizontal=True)
    q3 = st.radio("■ サポート体制 (1: 教授の手厚い指導 ⇔ 5: 先輩を中心とした学生間のサポート)", options=[1, 2, 3, 4, 5], index=2, horizontal=True)
    q4 = st.radio("■ 研究アプローチ (1: 基礎原理の解明・理学寄り ⇔ 5: 社会実装・モノづくり・工学寄り)", options=[1, 2, 3, 4, 5], index=2, horizontal=True)
    q5 = st.radio("■ 研究室の雰囲気 (1: 和気あいあい・カジュアル ⇔ 5: 規律や礼儀を重んじる・フォーマル)", options=[1, 2, 3, 4, 5], index=2, horizontal=True)
    q6 = st.radio("■ 研究の進め方 (1: 個人作業が中心 ⇔ 5: チームでの共同作業が中心)", options=[1, 2, 3, 4, 5], index=2, horizontal=True)

    st.markdown("---")
    
    st.header("4. 研究室の関連URLの登録（任意）")
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
                "eval_6": str(q6)
            }
            save_data(data_to_save)
            st.success(f"「{lab_name}」のデータを登録しました！")

if __name__ == "__main__":
    main()