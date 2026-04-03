import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import google.generativeai as genai
from fpdf import FPDF
import io
import time 
import tempfile
import os

# --- 1. API・モデル設定 ---
# 直接書き込まず、StreamlitのSecretsから安全に読み込む
if "GOOGLE_API_KEY" in st.secrets:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("APIキーが設定されていません。Streamlit CloudのSettings > Secrets に GOOGLE_API_KEY を登録してください。")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)
MODEL_NAME = 'models/gemini-flash-latest' # 最新の推奨名に変更
model = genai.GenerativeModel(MODEL_NAME)


# --- 2. ページ・フォント設定 ---
st.set_page_config(page_title="バドミントン精密診断 Ultra Pro+", layout="wide")
plt.rcParams['font.family'] = 'MS Gothic'
plt.rcParams['axes.unicode_minus'] = False

# --- 3. ロジック関数群 ---
def get_rank_info(score):
    ranks = [(900, "S: 実業団級", "#FF4B4B"), (800, "A: 超上級", "#FF9F4B"), (700, "B: 上級", "#FFDF4B"),
             (600, "C: 中上級", "#4BFF4B"), (500, "D: 中級", "#4BFFFF"), (400, "E: 中級下", "#4B4BFF"),
             (300, "F: 初中級", "#A04BFF"), (200, "G: 初級", "#FF4BFF"), (100, "H: ビギナー", "#BBBBBB")]
    for threshold, name, color in ranks:
        if score >= threshold: return name, color
    return "I: チャレンジャー", "#FFFFFF"

def calculate_gear_impact(r_weight, r_frame, g_thick, g_tension):
    w_num = "".join(filter(str.isdigit, r_weight))
    w_val = int(w_num) if w_num else 4
    p_mod, c_mod = 0, 0
    if w_val <= 3: p_mod += 10
    elif w_val >= 5: p_mod -= 5; c_mod += 10
    if r_frame == "硬い": p_mod += 10; c_mod += 5
    if g_thick <= 0.63: p_mod += 5; c_mod -= 5
    if g_tension >= 26: p_mod += 5; c_mod += 10
    return p_mod, c_mod

# --- 4. PDF生成関数 (ここから差し替え) ---
def create_pdf(sex, age, level, score, rank, ai_text, fig):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # フォント読み込み
    font_path = 'C:/Windows/Fonts/msgothic.ttc'
    f_main = 'Arial' 
    if os.path.exists(font_path):
        pdf.add_font('MS-Gothic', '', font_path, uni=True)
        f_main = 'MS-Gothic'

    # ヘッダーデザイン
    pdf.set_fill_color(30, 30, 30)
    pdf.rect(0, 0, 210, 35, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font(f_main, '', 18)
    pdf.cell(0, 15, txt="🏸 バドミントン精密診断レポート", ln=True, align='C')
    
    # ランク表示
    pdf.set_y(40); pdf.set_text_color(0, 0, 0); pdf.set_font(f_main, '', 16)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 12, txt=f" ランク: {rank} (Score: {int(score)})", ln=True, align='C', fill=True)
    
    # チャート挿入
    img_buf = io.BytesIO()
    fig.savefig(img_buf, format='png', dpi=150, bbox_inches='tight', facecolor='#0e1117')
    img_buf.seek(0)
    pdf.image(img_buf, x=60, y=55, w=90)
    
    # 解析テキスト開始
    pdf.set_y(150); pdf.set_font(f_main, '', 11)
    pdf.set_draw_color(75, 200, 255)
    pdf.cell(0, 10, txt=f" 属性: {sex}/{age}歳  レベル: {level}", border='B', ln=True)
    pdf.ln(5)
    
    # --- 文字切れ対策ロジック ---
    pdf.set_font(f_main, '', 10)
    line_height = 7
    margin_left = 20
    margin_right_limit = 185 # ここで強制改行
    
    content_lines = ai_text.split('\n')
    
    for line in content_lines:
        clean_line = line.strip().replace('\u200b', '')
        if not clean_line:
            pdf.ln(3)
            continue
            
        if clean_line.startswith('###'):
            pdf.ln(2)
            pdf.set_font(f_main, '', 11)
            pdf.set_fill_color(230, 245, 255)
            display_text = clean_line.replace('#', '').strip()
            pdf.set_x(margin_left)
            pdf.cell(170, 9, txt="", ln=False, fill=True) # 背景色
            pdf.set_x(margin_left)
            pdf.write(9, display_text)
            pdf.ln(10)
            pdf.set_font(f_main, '', 10)
        else:
            pdf.set_x(margin_left)
            # 1文字ずつ描画して右端を監視
            for char in clean_line:
                char_w = pdf.get_string_width(char)
                if pdf.get_x() + char_w > margin_right_limit:
                    pdf.ln(line_height)
                    pdf.set_x(margin_left)
                pdf.write(line_height, char)
            pdf.ln(line_height)
            
    return bytes(pdf.output(dest='S'))
# --- (ここまで差し替え) ---

# --- 5. UI構築 ---
st.markdown('<div style="background-color:#1e1e1e; padding:15px; border-radius:10px; text-align:center; margin-bottom:20px;"><h1 style="color:white; margin:0;">🏸 バドミントン精密診断 Ultra Pro+</h1></div>', unsafe_allow_html=True)
col_input, col_chart, col_result = st.columns([1.3, 1, 1.2])

with col_input:
    st.markdown("### 🛠️ 総合パラメータ設定")
    with st.expander("👤 基本・身体データ", expanded=True):
        u_sex = st.radio("性別", ["男性", "女性", "回答しない"], horizontal=True)
        c1, c2 = st.columns(2)
        u_age = c1.number_input("年齢", 5, 100, 35)
        u_years = c2.number_input("経験年数", 0, 80, 5)
        u_height = c1.number_input("身長 (cm)", 100, 250, 170)
        u_weight_val = c2.number_input("体重 (kg)", 30, 150, 65)
        u_hand = st.radio("利き手", ["右利き", "左利き"], horizontal=True)
        u_grip = st.number_input("握力 (kg)", 5, 100, 40)
        u_assets = st.text_area("運動資産・強み", "スポーツ経験歴、フットワークの軽さなど")
        u_extra_note = st.text_area("補足情報（シングルス強化中、怪我の状態など）", "")

    with st.expander("🎾 ギア & 練習環境", expanded=True):
        g1, g2 = st.columns(2)
        r_weight = g1.selectbox("ラケット重さ", ["2U", "3U", "4U", "5U", "6U", "F"])
        r_frame = g2.selectbox("フレーム剛性", ["硬い", "やや硬い", "標準", "柔らかい"])

# ガットの種類を追加
        gut_type = st.selectbox(
            "ガットの種類", 
            [
                "高反発（反発重視）", 
                "コントロール（ホールド重視）", 
                "ハードヒッター（耐久・パワー重視）", 
                "衝撃吸収（ソフト）"
            ]
        )

        g_thick = st.slider("ガット太さ (mm)", 0.55, 0.70, 0.63)
        g_tension = st.number_input("ガットテンション (lbs)", 15, 35, 24)
        
        practice_days = st.slider("週の練習日数", 0, 7, 3)
        practice_hours = st.slider("1日の練習時間 (h)", 0.0, 12.0, 2.0)
        focus_items = st.multiselect("重点項目", ["基礎打ち", "フットワーク", "ノック", "パターン練習", "ゲーム練習", "戦術研究", "サーブ・レシーブ", "シングルス", "ダブルス"], default=["基礎打ち"])

    with st.expander("🩺 コンディション & メディア", expanded=True):
        pain_level = st.select_slider("ケガの状態", options=["なし（絶好調）", "違和感あり", "動くと痛む", "日常生活でも痛む"])
        u_level = st.select_slider("自己レベル", options=["初級", "初中級", "中級", "中上級", "上級", "プロ級"], value="中級")
        up_video = st.file_uploader("動画解析 (10秒制限)", type=["mp4", "mov"])
        up_images = st.file_uploader("写真解析 (最大3枚)", type=["jpg", "png"], accept_multiple_files=True)
        u_custom_issues = st.text_area("現在の悩み", "バックハンドが飛ばない")

    with st.expander("🎓 AI戦略・コーチ設定", expanded=True):
        coach_mode = st.selectbox("コーチ設定", ["全国経験者のコーチ", "冷徹なデータアナリスト", "褒めて伸ばすサポーター"])
        opponent_type = st.selectbox("仮想相手", ["鉄壁のレシーバー", "攻撃的スマッシャー", "テクニシャン"])
        physical_state = st.select_slider("試合中の状態", options=["体力満タン", "やや疲労", "ヘトヘト"])

    analyze_btn = st.button("⚖️ 全データを統合解析する", use_container_width=True, type="primary")

# --- 6. チャート描画 ---
with col_chart:
    st.markdown("### 📊 スキル成分・数値可視化")
    p_mod, c_mod = calculate_gear_impact(r_weight, r_frame, g_thick, g_tension)
    base_tech = ["初級", "初中級", "中級", "中上級", "上級", "プロ級"].index(u_level) * 15 + 20
    
    labels = ['パワー', 'コントロール', 'スタミナ', '技術', '精神力']
    s_power = min(100, (u_grip * 1.2) + p_mod + (practice_hours * 2))
    s_ctrl = min(100, base_tech + c_mod + (practice_days * 2))
    s_stamina = max(10, 80 - (u_age * 0.5) - (["なし", "違和感", "動くと", "日常"].index(pain_level[:2].strip("（")) * 20))
    s_tech = min(100, base_tech + (u_years * 3))
    s_mental = 70 if physical_state == "体力満タン" else (30 if physical_state == "ヘトヘト" else 50)
    stats = [s_power, s_ctrl, s_stamina, s_tech, s_mental]
    
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.set_facecolor('#1e1e1e'); fig.patch.set_facecolor('#0e1117')
    angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist()
    stats_p = np.concatenate((stats, [stats[0]])); angles_p = np.concatenate((angles, [angles[0]]))
    ax.plot(angles_p, stats_p, 'o-', linewidth=2, color="#4BFFFF")
    ax.fill(angles_p, stats_p, alpha=0.3, color="#4BFFFF")
    for i, (angle, label) in enumerate(zip(angles, labels)):
        ax.text(angle, 120, f"{label}\n{int(stats[i])}", color='white', ha='center', weight='bold')
    ax.set_ylim(0, 100)
    st.pyplot(fig)

# --- 7. AI解析 & PDF出力 ---
with col_result:
    if analyze_btn:
        st.markdown("### 🏆 AI精密コーチング")
        total_score = sum(stats) * 2
        r_name, r_color = get_rank_info(total_score)
        st.markdown(f'<div style="border:2px solid {r_color}; padding:10px; border-radius:10px; text-align:center;"><h2 style="color:{r_color};">{r_name}</h2><p>Total Score: {int(total_score)}</p></div>', unsafe_allow_html=True)
        
        with st.spinner("AIコーチが全データを精査中..."):
            prompt_parts = [
                f"あなたはバドミントンコーチ【{coach_mode}】です。以下の内容で具体的かつ専門的に指導してください。\n"
                f"【身体】レベル:{u_level}, 経験:{u_years}年, {u_hand}, 体重:{u_weight_val}kg, 握力:{u_grip}kg\n"
                f"【練習】週{practice_days}日, 重点:{focus_items}, 資産:{u_assets}, 補足:{u_extra_note}\n"
                f"【ギア】{r_weight}/{r_frame}/ガット{g_thick}mm/{g_tension}lbs\n"
                f"【状況】悩み:{u_custom_issues}, 相手:{opponent_type}, 状態:{physical_state}\n\n"
                f"以下の###見出しを必ず含めてください：\n"
                f"### 1. 現状分析\n### 2. 課題の根本原因\n### 3. 即効性のある対策\n### 4. 中長期的な改善点\n### 5. 推奨練習メニュー"
            ]

            if up_video:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
                    tmp.write(up_video.read()); video_path = tmp.name
                v_file = genai.upload_file(path=video_path)
                while v_file.state.name == "PROCESSING": time.sleep(2); v_file = genai.get_file(v_file.name)
                prompt_parts.insert(0, v_file)
            if up_images:
                for img in up_images[:3]: prompt_parts.append(genai.upload_file(io.BytesIO(img.read()), mime_type="image/jpeg"))

try:
                # --- ここから追加・修正 ---
                # 動画や画像などのファイルをAIが読み取れる形式に変換
                processed_parts = []
                for part in prompt_parts:
                    # もし中身がアップロードされたファイル（BytesIOなど）の場合
                    if hasattr(part, "getvalue"):
                        # mime_typeは動画なら "video/mp4"、画像なら "image/jpeg" など適切に設定
                        # ここでは動画と仮定していますが、汎用的に bytes データとして渡します
                        processed_parts.append({
                            "mime_type": "video/mp4", # 動画ファイルの場合
                            "data": part.getvalue()
                        })
                    else:
                        # 普通のテキスト（プロンプトなど）はそのまま追加
                        processed_parts.append(part)

                # 修正した processed_parts を渡す
                response = model.generate_content(processed_parts)
                # --- ここまで修正 ---

                ai_text = response.text
                st.markdown(ai_text)
                
                pdf_data = create_pdf(u_sex, u_age, u_level, total_score, r_name, ai_text, fig)
                st.download_button(label="📄 レポート(PDF)を保存", data=pdf_data, file_name="badminton_report.pdf", mime="application/pdf", use_container_width=True)
                
                if up_video: os.unlink(video_path)
            except Exception as e:
                st.error(f"解析エラー: {e}")