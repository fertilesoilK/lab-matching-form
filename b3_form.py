import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import glob
import ast

def load_all_csv_data():
    # アプリと同じフォルダにあるすべてのCSVファイルを読み込みます．
    csv_files = glob.glob("*.csv")
    
    if not csv_files:
        return pd.DataFrame()
        
    all_dataframes = []
    
    for file in csv_files:
        try:
            df = pd.read_csv(file)
            
            # リスト形式のデータを文字列からPythonのリストに変換します．
            for col in ["分野", "大キーワード", "中キーワード", "小キーワード"]:
                if col in df.columns:
                    df[col] = df[col].apply(lambda x: ast.literal_eval(x) if pd.notna(x) and isinstance(x, str) and x.startswith('[') else [])
            
            all_dataframes.append(df)
            
        except Exception as e:
            st.error(f"ファイル {file} の読み込み中にエラーが発生しました: {e}")
            
    if all_dataframes:
        # すべてのCSVを縦に結合します．
        combined_df = pd.concat(all_dataframes, ignore_index=True)
        return combined_df
    else:
        return pd.DataFrame()

def main():
    st.set_page_config(page_title="研究室マッチング", layout="wide")
    st.title("研究室マッチングシステム")
    st.write("Ｂ４の先輩たちのデータをもとに，あなたにぴったりの研究室を診断します．")

    # CSVからデータを読み込みます．
    df = load_all_csv_data()

    if df.empty:
        st.warning("研究室のデータ（CSVファイル）が見つかりません．アプリと同じフォルダにCSVファイルを配置してください．")
        return

    st.markdown("---") 

    st.header("希望条件を入力してください")
    
    # １．診断対象（絞り込み）の選択
    st.write("■ 診断の対象")
    target_mode = st.radio(
        "研究室をどの範囲から探しますか？", 
        ["全ての研究室から診断する", "分野を絞って診断する"],
        label_visibility="collapsed"
    )

    all_fields_set = set()
    for fields_list in df["分野"]:
        if isinstance(fields_list, list):
            all_fields_set.update(fields_list)
    available_fields = sorted(list(all_fields_set))

    if target_mode == "分野を絞って診断する":
        selected_fields = st.multiselect("診断したい分野を選択してください（複数可）", available_fields)
        
        if len(selected_fields) > 0:
            target_df = df[df["分野"].apply(lambda x: any(field in x for field in selected_fields))]
        else:
            target_df = pd.DataFrame(columns=df.columns)
    else:
        target_df = df

    st.write("") 

    # ２．キーワードの選択
    st.write("■ 気になるキーワードを選択（複数可）")
    
    if not target_df.empty:
        all_keywords = set()
        for col in ["大キーワード", "中キーワード", "小キーワード"]:
            if col in target_df.columns:
                for themes in target_df[col]:
                    if isinstance(themes, list):
                        all_keywords.update(themes)
        all_keywords = sorted(list(all_keywords))

        cols = st.columns(4)
        selected_themes = []
        for i, theme in enumerate(all_keywords):
            if cols[i % 4].checkbox(theme, key=theme):
                selected_themes.append(theme)
    else:
        st.write("※上の選択欄で分野を選ぶと，該当する研究室のキーワードが表示されます．")
        selected_themes = []

    st.markdown("---") 

    # 診断ボタン
    if st.button("診断する", type="primary", disabled=target_df.empty): 
        st.subheader("診断結果")

        scores = []
        for index, row in target_df.iterrows():
            score = 0
            
            b3_themes = set(selected_themes)
            
            lab_large = set(row["大キーワード"]) if "大キーワード" in row and isinstance(row["大キーワード"], list) else set()
            lab_medium = set(row["中キーワード"]) if "中キーワード" in row and isinstance(row["中キーワード"], list) else set()
            lab_small = set(row["小キーワード"]) if "小キーワード" in row and isinstance(row["小キーワード"], list) else set()
            
            # キーワードの一致によるスコア計算
            score += len(b3_themes.intersection(lab_large)) * 15
            score += len(b3_themes.intersection(lab_medium)) * 10
            score += len(b3_themes.intersection(lab_small)) * 5
                
            scores.append(score)
            
        result_df = target_df.copy()
        result_df["Match_Score"] = scores
        result_df = result_df.sort_values(by="Match_Score", ascending=False)

        # グラフの描画（タイトル，ラベルなどはすべて英語）
        st.write("### Matching Score Distribution")
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(result_df["Lab_ID"], result_df["Match_Score"], color="skyblue")
        ax.set_title("Matching Score by Laboratory", fontsize=14)
        ax.set_xlabel("Laboratory", fontsize=12)
        ax.set_ylabel("Score", fontsize=12)
        plt.xticks(rotation=45) 
        st.pyplot(fig)

        # おすすめの研究室を詳細表示
        st.write("### おすすめの研究室詳細")
        for index, row in result_df.iterrows():
            if row["Match_Score"] > 0 or len(selected_themes) == 0:
                with st.expander(f"【{row['研究室名']}】 スコア: {row['Match_Score']}点"):
                    fields_str = "，".join(row['分野']) if isinstance(row['分野'], list) else row.get('分野', '未設定')
                    st.write(f"【分野】 {fields_str}")
                    
                    large_str = "，".join(row['大キーワード']) if isinstance(row['大キーワード'], list) else ""
                    st.write(f"【大キーワード】 {large_str}")
                    
                    medium_str = "，".join(row['中キーワード']) if isinstance(row['中キーワード'], list) else ""
                    st.write(f"【中キーワード】 {medium_str}")
                    
                    small_str = "，".join(row['小キーワード']) if isinstance(row['小キーワード'], list) else ""
                    st.write(f"【小キーワード】 {small_str}")

if __name__ == "__main__":
    main()