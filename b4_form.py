import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# 研究室名とIDの対応表
ROMAJI_DICT = {
    "上野研究室": "ueno", "塚原研究室": "tsukahara", "青野研究室": "aono",
    "田口研究室": "taguchi", "高橋研究室": "takahashi", "岡田研究室": "okada",
    "松崎研究室": "matsuzaki", "荻原研究室": "ogihara", "早瀬研究室": "hayase",
    "荒井研究室": "arai", "竹村研究室": "takemura", "朝倉研究室": "asakura"
}

# 分野リスト
CATEGORY_LIST = ["熱・流体", "材料・構造", "制御・機械・ロボット", "生体・医療", "解析・プログラミング・情報", "その他・環境・設備"]

def save_data(data_dict):
    """Googleスプレッドシートへデータを追記する関数"""
    # secrets.toml から情報を読み込む
    sheet_id = st.secrets["sheet_id"]
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    
    # Googleへの接続
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    # シートを開いて最終行に追加
    sheet = client.open_by_key(sheet_id).sheet1
    row_values = [
        data_dict["Lab_ID"], 
        data_dict["研究室名"], 
        data_dict["分野"], 
        data_dict["キーワードデータ"]
    ]
    sheet.append_row(row_values)

def main():
    st.set_page_config(page_title="【B4向け】研究室情報登録フォーム", layout="wide")
    st.title("研究室情報 登録フォーム")
    st.write("B3向けマッチングシステム用：キーワードと分野を紐付けて登録してください．")

    st.markdown("---")

    st.header("1. 基本情報")
    lab_name = st.selectbox("■ 研究室名", ["選択してください"] + list(ROMAJI_DICT.keys()))
    fields = st.multiselect("■ 研究室全体の分野（複数選択可）", ["熱", "流体", "材料", "制御", "振動学"])

    st.markdown("---")
    st.header("2. 研究キーワードの登録")
    
    categorized_keywords = {
        "熱・流体": ["流体", "N-Sの式", "低Re数", "無次元化", "層流", "表面張力", "マランゴニ対流", "沸騰現象", "気液混相流", "伝熱", "エネルギー効率", "低レイノルズ数", "低密度", "風洞", "低真空"],
        "材料・構造": ["複合材料", "CFRP", "GFRP", "オートクレープ", "セラミックス", "熱可塑性", "引張試験", "破壊力学", "DCB試験", "リサイクルCFRP", "フラン樹脂", "衝撃強度試験", "コンプライアンス", "走査電子顕微鏡", "破面観察"],
        "制御・機械・ロボット": ["ロボット", "ロボットアーム", "自動化", "センサ（IMU）", "ドローン", "人工筋肉", "設計", "モーションキャプチャ", "航空機", "羽ばたき", "FWMAV", "自立飛行", "飛行制御", "SMC", "ロバスト制御", "電子工作", "ギア"],
        "生体・医療": ["生体機械", "バイオメカニクス", "脳波", "介護支援", "内視鏡", "ブタの肝臓", "医科歯科大学", "慈恵医大学", "生命維持", "生物模倣", "ハチドリ", "チョウ"],
        "解析・プログラミング・情報": ["ハイスピードカメラ", "画像解析", "MATLAB", "プログラミング", "数値解析", "フーリエ解析", "人工知能", "機械学習", "有限要素法", "サンプリングモアレ法", "強化学習", "Fusion", "MCP", "3Dプリンタ", "Claude", "Notion"],
        "その他・環境・設備": ["実験", "宇宙環境", "JAXA", "Mac", "21号館", "3号館", "リモート", "統計", "産総研", "理化学研究所", "VR", "プラズマ商社", "火星", "Ingenuity", "高速度カメラ", "葛飾キャンパス", "信州大", "NASA", "広い"]
    }

    selected_kw_pairs = []

    for category, keywords in categorized_keywords.items():
        st.write(f"▼ 【{category}】")
        cols = st.columns(4)
        for i, kw in enumerate(keywords):
            if cols[i % 4].checkbox(kw, key=f"kw_{kw}"):
                selected_kw_pairs.append((kw, category))
        st.write("") 

    st.markdown("---")
    st.write("■ 選択肢にない独自の言葉を追加")
    
    if "custom_kw_count" not in st.session_state:
        st.session_state.custom_kw_count = 1

    for i in range(st.session_state.custom_kw_count):
        col_c1, col_c2 = st.columns([2, 1])
        with col_c1:
            kw_text = st.text_input(f"追加キーワード {i+1}", key=f"custom_kw_{i}")
        with col_c2:
            cat_select = st.selectbox(f"所属分野 {i+1}", CATEGORY_LIST, key=f"custom_cat_{i}")
        
        if kw_text.strip():
            selected_kw_pairs.append((kw_text.strip(), cat_select))
        
    if st.button("＋ 欄を追加", key="add_kw"):
        st.session_state.custom_kw_count += 1
        st.rerun()

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
                "キーワードデータ": str(final_kw_data)
            }
            save_data(data_to_save)
            st.success(f"「{lab_name}」のデータをスプレッドシートに登録しました！")

if __name__ == "__main__":
    main()