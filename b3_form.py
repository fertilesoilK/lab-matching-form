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
    "流体・熱・エネルギー": {
        "基本・一般": ["流体力学",  "熱流体", "伝熱", "沸騰現象", "エネルギー効率化"],
        "専門・詳細": ["ナビエ・ストークス方程式", "無次元化", "層流", "乱流", "低Re数", "高レイノルズ数流れ", "流れの遷移", "複雑な流れ現象", "亜音速", "粘弾性流体", "境界層", "気液混相流", "表面張力", "濡れ現象", "マランゴニ対流", "マイクロ流路", "プラントのガス漏洩検知", "有害物質拡散源推定", "熱交換器"]
    },
    "航空・宇宙": {
        "基本・一般": ["航空機", "航空機設計", "宇宙環境", "JAXA", "エンジン設計","羽ばたき飛行","火星飛行探索機"],
        "専門・詳細": ["航空機翼", "翼の空力設計", "翼の最適化設計", "風洞実験", "離陸飛行実験", "ターボジェットエンジン", "極超音速エンジン", "複合サイクルエンジン", "スペースプレーン", "エンジン制御", "流路切替機構設計", "火星利用", "生命維持", "水電解"]
    },
    "材料・構造・固体力学": {
        "基本・一般": ["材料力学", "疲労", "複合材料", "CFRP", "炭素繊維・連続繊維", "セラミックス", "破壊力学", "連続体力学", "弾塑性力学", "損傷力学", "材料強度学", "非線形破壊力学", "強度評価", "計算固体力学", "計算破壊力学","微細加工"],
        "専門・詳細": ["繰り返し荷重", "溶接", "ダイヤモンド", "亀裂進展解析", "J積分", "コンプライアンス", "引張試験", "曲げ試験", "衝撃強度試験", "DCB試験", "破面観察", "走査電子顕微鏡", "知的材料・構造", "リサイクルCFRP", "GFRP", "VARTM", "フラン樹脂", "成膜", "銅メッキ", "白金触媒", "プラズマ照射", "固体力学解析手法構築", "分子動力学", "転位動力学"]
    },
    "ロボティクス・制御・機械要素": {
        "基本・一般": ["振動工学", "音響シミュレーション", "ロボット工学", "産業用ロボット", "ドローン", "自動車への応用", "自動化", "センサ", "ギア"],
        "専門・詳細": ["ロボット視覚機能付与","協働ロボット(UR等)", "ロボットアーム", "ロボットマニピュレーション", "ロボット制御", "人工筋肉", "モーションキャプチャ", "小型ロボットヘリコプター", "マイクロ航空機", "自立飛行", "飛行制御", "ロバスト制御", "設計", "ロボットビジョン", "ビジュアルサーボ", "電子工作", "MEMS", "レーザー加工", "流量計開発・評価", "警告音設計(自転車等)"]
    },
    "解析・シミュレーション・情報": {
        "基本・一般": ["プログラミング", "人工知能", "機械学習", "画像解析","数値解析", "有限要素法"],
        "専門・詳細": ["python", "c言語","CFD解析", "CAE", "分子シミュレーション", "IGA", "FPM", "重合メッシュ法", "領域積分法", "サンプリングモアレ法", "marc", "解析手法構築", "フーリエ解析", "テンソル解析", "統計解析", "情報理論・データサイエンス", "最適化", "フィジカルAI", "深層学習・CNN", "強化学習", "画像処理・物体認識", "点群処理", "プログラム実装", "fortran", "MATLAB", "Simulink", "サウンドスケープ評価"]
    },
    "生体・医療・バイオメカニクス": {
        "基本・一般": ["バイオメカニクス", "医療工学","生体工学", "医療・福祉支援技術", "介護支援", "感性工学", "生物模倣"],
        "専門・詳細": ["生体機械", "耳鼻咽喉科学", "アクティブマター・自己駆動粒子", "血流・血管の解析", "人工心臓・人工弁", "内視鏡", "がん細胞", "脳波解析(睡眠・音楽)", "嚥下(えんげ)音解析", "聴力評価(DINテスト)", "病院の音環境"]
    },
    "設備・実験手法・その他ツール": {
        "基本・一般": [ "3Dプリンタ", "VR音響評価"],
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
        if not records: return pd.DataFrame()
        padded_records = [r[:13] + [""]*(13-len(r)) for r in records]
        df = pd.DataFrame(padded_records, columns=["Lab_ID", "研究室名", "分野", "キーワードデータ", "公式HP", "関連URL1", "関連URL2", "eval_1", "eval_2", "eval_3", "eval_4", "eval_5", "eval_6"])
        df["分野"] = df["分野"].apply(lambda x: ast.literal_eval(x) if x.startswith('[') else [])
        df["キーワードデータ"] = df["キーワードデータ"].apply(lambda x: ast.literal_eval(x) if x.startswith('[') else [])
        return df
    except Exception as e:
        st.error(f"スプレッドシートの読み込みエラー: {e}")
        return pd.DataFrame()

def display_lab_details(row):
    with st.expander(f"【{row['研究室名']}】 Score: {row['Match_Score']}"):
        st.write(f"【分野】 {'，'.join(row['分野'])}")
        kw_data = row['キーワードデータ']
        if isinstance(kw_data, list):
            grouped = {}
            for kw, cat in kw_data:
                cat = "設備・実験手法・その他ツール" if "ツール" in cat or "実験" in cat else cat
                grouped.setdefault(cat, []).append(kw)
            st.write("【関連キーワード】")
            for cat, kws in grouped.items():
                st.write(f"・<u>{cat}</u>: {', '.join(kws)}", unsafe_allow_html=True)
        # (評価やリンク表示処理は前回と同様のため省略)

def main():
    st.set_page_config(page_title="ME研究室マッチング", layout="wide")
    st.title("ME研究室マッチングシステム")
    df = load_spreadsheet_data()
    if df.empty: return

    # キーワード選択 UI
    selected_themes = []
    # ... (キーワード選択のUIロジックは前回と同様) ...

    if st.button("診断する", type="primary"): 
        all_basic_kws = {kw for cat in PREDEFINED_KEYWORDS.values() for kw in cat.get("基本・一般", [])}
        scores = []
        for _, row in df.iterrows():
            lab_kws = {kw[0] for kw in row["キーワードデータ"]} if isinstance(row["キーワードデータ"], list) else set()
            score = sum(30 if kw in all_basic_kws else 10 for kw in set(selected_themes) if kw in lab_kws)
            scores.append(score)
        
        df["Match_Score"] = scores
        df = df.sort_values(by="Match_Score", ascending=False)

        st.subheader("診断結果")
        st.info("""
        **💡 診断の仕組み**
        あなたが選択したキーワードと、各研究室が登録したキーワードが一致した場合、以下の基準で加点を行っています。
        ・基本・一般キーワード：30点
        ・専門・詳細キーワード：10点
        
        ※各研究室で登録キーワード数に差があるため、総数が多い研究室ほど点数が高くなる傾向があります。このスコアはあくまで一つの目安ですので、詳細は各研究室のホームページを必ず確認してください。
        """)
        
        for _, row in df[df["Match_Score"] > 0].iterrows():
            display_lab_details(row)

if __name__ == "__main__":
    main()