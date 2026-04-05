import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. ページ設定
st.set_page_config(page_title="バドミントン物理・機材・更生シミュレーター", layout="wide")
st.title("🏸 決定版：バドミントン物理デバッグ & プロ機材診断")

# --- スコア評価基準表 ---
with st.expander("📊 スコア評価基準表（この数値が表すもの）"):
    score_data = {
        "ランク": ["SSS", "A", "B", "C", "E"],
        "スコア": ["90 - 100", "75 - 89", "50 - 74", "25 - 49", "0 - 24"],
        "状態の定義": [
            "達人級。身体の質量と機材の反発が完全同期。最小の力で最大効率の打球が可能。",
            "上級。基礎OSが安定。微細な癖はあるが、戦術的な対応でカバーできるレベル。",
            "中級。物理ロス発生中。パワー不足や精度の波を、筋力でねじ伏せている状態。",
            "初心者。致命的なバグ（癖）により、努力が結果に結びつきにくい停滞期。",
            "破綻。機材不一致かつ重度のバグ。打つほどに怪我のリスクが高まる危険状態。"
        ]
    }
    st.table(pd.DataFrame(score_data))

# --- サイドバー：入力セクション ---
with st.sidebar:
    st.header("👤 1. プレイヤー属性")
    age = st.slider("現在の年齢", 5, 80, 35)
    years = st.slider("経験年数", 0, 50, 10)
    grip = st.slider("握力 (kg)", 5, 100, 32)
    weight = st.slider("体重 (kg)", 20, 120, 60)
    
    st.header("⚙️ 2. 機材・練習環境")
    r_weight_class = st.select_slider(
        "ラケットの重さ (重量クラス)",
        options=["F (超軽量)", "5U", "4U", "3U", "2U (重量級)"],
        value="4U"
    )
    ten = st.slider("テンション (lbs)", 12, 35, 24)
    gauge = st.select_slider(
        "ガットの太さ (mm)", 
        options=[0.58, 0.61, 0.63, 0.65, 0.66, 0.68, 0.70],
        value=0.66
    )
    vol = st.slider("練習量 (h/週)", 0, 84, 10)

# --- メイン画面：チェックリスト ---
st.header("🔍 デバッグ項目：バグと身体の状態")
col_h, col_p = st.columns(2)

with col_h:
    st.subheader("❌ 技術・フォームのバグ（癖）")
    h_none = st.checkbox("【重要】特に変な癖はない（ニュートラル）", value=True)
    h_western = st.checkbox("ウエスタン打ち（フライパン握り）")
    h_neko = st.checkbox("猫手（手首の固定）")
    h_teuchi = st.checkbox("手打ち（体幹連動なし）")
    h_hiji = st.checkbox("肘が伸びきった打点")
    h_dead = st.checkbox("デッドグリップ（握りすぎ）")
    h_hanmi = st.checkbox("半身になれない")
    h_ashi = st.checkbox("足が1歩しか出ない")
    h_bo = st.checkbox("棒立ち")
    h_atama = st.checkbox("打つ瞬間に頭が上がる")
    
    h_weights = [1.8, 1.2, 1.4, 2.0, 1.3, 1.1, 1.0, 1.0, 1.1]
    h_checks = [h_western, h_neko, h_teuchi, h_hiji, h_dead, h_hanmi, h_ashi, h_bo, h_atama]
    h_severity_sum = sum([w for c, w in zip(h_checks, h_weights) if c])
    has_bug = any(h_checks) and not h_none

with col_p:
    st.subheader("🏥 身体の状態（痛み・違和感）")
    p_none = st.checkbox("特になし（良好）", value=True)
    p_tekubi = st.checkbox("手首が痛い")
    p_hiji = st.checkbox("肘が痛い")
    p_koshi = st.checkbox("腰が痛い")
    p_kubi = st.checkbox("首・肩が痛い")
    p_ashi = st.checkbox("膝・足首が痛い")
    
    p_checks = [p_tekubi, p_hiji, p_koshi, p_kubi, p_ashi]
    has_pain = any(p_checks) and not p_none

# --- 演算エンジン ---
def calculate_all_logic(age, years, grip, weight, ten, gauge, vol, h_list, h_severity, has_bug, pattern, r_weight_class):
    # 年齢補正
    age_stiffness_factor = 1.0
    if age < 15:
        age_stiffness_factor = 0.7 + (age / 50)
    elif age > 45:
        age_stiffness_factor = max(0.6, 1.0 - (age - 45) * 0.015)

    # ガット太さロジックの改善（ここが重要）
    experience_factor = (years - 5) * 0.2
    
    if grip <= 20:
        ideal_gauge = 0.61 
    elif grip < 35:
        # 経験が長い（8年以上）場合は、細ガットに頼りすぎない標準的な太さを推奨
        ideal_gauge = 0.66 if years >= 8 else 0.61
    elif grip > 55:
        ideal_gauge = 0.68
    else:
        ideal_gauge = 0.66

    # 理想テンション算出
    ideal_ten = ((grip * 0.4) + 10 + experience_factor) * age_stiffness_factor
    
    # ラケット重量
    weight_map = {"F (超軽量)": 73, "5U": 78, "4U": 83, "3U": 88, "2U (重量級)": 93}
    current_w = weight_map[r_weight_class]
    if grip < 25: ideal_w = 78
    elif grip > 50: ideal_w = 88
    else: ideal_w = 83
    
    # スコア計算
    weight_diff_penalty = abs(current_w - ideal_w) * 0.5
    ten_diff = abs(ten - ideal_ten)
    gauge_diff = abs(gauge - ideal_gauge)
    gauge_suitability = 8 - (gauge_diff * 100) 

    suit = 100 - (ten_diff * 6) + gauge_suitability - weight_diff_penalty
    suit -= (max(0, 25 - weight/2) * 5)
    
    # 耐久限界・練習量
    if age <= 12: recovery_limit = 8 + (age * 0.5)
    elif 18 <= age <= 30: recovery_limit = 25 + (years * 0.5)
    else: recovery_limit = max(8, 25 - (age - 30) * 0.6)

    weight_fatigue_mult = 1.0 + (current_w - 83) * 0.02
    fatigue_penalty = 0
    if vol > recovery_limit:
        age_impact = 4.0 if (age < 13 or age > 50) else 2.0
        fatigue_penalty += (vol - recovery_limit) * age_impact * weight_fatigue_mult
    
    suit -= fatigue_penalty
    if has_bug: suit -= (h_severity * 10)
    suit = max(0, min(100, suit))

    # 更生期間
    rehab_m = 0.0
    if has_bug:
        base_m = (years * 0.7) * (h_severity * 0.4)
        age_learning_factor = 0.4 if age < 15 else (1.0 + (max(0, age-40) * 0.02))
        vol_factor = 1.8 if vol < 3 else (0.8 if vol <= recovery_limit else 1.3)
        gear_obs_factor = 1.0 + (max(0, current_w - ideal_w) * 0.05)
        rehab_m = round(base_m * age_learning_factor * vol_factor * gear_obs_factor * (0.6 if "パターンA" in pattern else 1.5), 1)

    # サブスコア
    power_score = max(10, min(100, (grip * 1.5) + (weight * 0.2) + ((current_w - 83) * 0.8)))
    s_score = max(10, min(100, 100 - (vol / recovery_limit * 30 if vol > 0 else 0)))
    ir_score = max(10, min(100, 100 - (h_severity * 12) - (20 if has_pain else 0)))

    return suit, rehab_m, recovery_limit, ideal_ten, ideal_gauge, power_score, s_score, ir_score, ideal_w

# --- ロジック実行 ---
fix_pattern = "修正不要"
if has_bug:
    st.divider()
    fix_pattern = st.radio("更生アプローチ", ["パターンA：徹底修正（物理矯正）", "パターンB：並行修正（妥協案）"])

suit_s, rehab_m, rec_lim, i_ten, i_gauge, p_score, s_score, ir_score, i_w = calculate_all_logic(
    age, years, grip, weight, ten, gauge, vol, h_checks, h_severity_sum, has_bug, fix_pattern, r_weight_class
)

# --- ビジュアルセクション ---
st.divider()
col_graph, col_rec = st.columns([1.2, 1])

with col_graph:
    st.subheader("📊 プレイヤー能力・適正バランス")
    categories = ['機材一致度', '推定パワー', '回復余裕度', '怪我耐性', 'フォーム精度']
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[suit_s, p_score, s_score, ir_score, 100 - (h_severity_sum * 8)],
        theta=categories, fill='toself', name='能力値', line_color='#00FFAA'
    ))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col_rec:
    st.subheader("🛠️ プロ機材レコメンド")
    w_rev_map = {73: "F", 78: "5U", 83: "4U", 88: "3U", 93: "2U"}
    i_w_class = w_rev_map.get(i_w, "4U")
    
    st.success(f"""
    **あなたへの最適解:**
    - **ラケット重量:** {i_w_class}
    - **推奨ガット:** {i_gauge} mm
    - **推奨テンション:** {i_ten:.1f} lbs
    - **練習キャパ:** 週 {int(rec_lim)} 時間以内
    """)
    
    if has_bug:
        st.subheader("⏳ 更生プロセス予測")
        if vol < 3: st.warning("⚠️ 練習不足により、新しい動きが定着しにくい状態です。")
        elif vol > rec_lim: st.error("⚠️ 疲労により、悪い癖が強調されるリスクがあります。")
        else: st.info("✨ 効率的なフォーム修正が可能な練習量です。")

# --- 結果レポート ---
st.divider()
st.header("📋 詳細診断レポート")
c1, c2, c3 = st.columns(3)
c1.metric("物理システム適合度", f"{int(suit_s)}/100")
if has_bug:
    c2.metric("更生完了まで", f"{rehab_m} ヶ月")
    c3.metric("推奨練習量 (週)", f"{int(rec_lim)} h")
else:
    c2.metric("状態", "ニュートラル")
    c3.metric("耐久限界 (週)", f"{int(rec_lim)} h")

# --- ミスマッチ診断 ---
st.divider()
st.header("⚙️ 機材ミスマッチの診断")
col_m1, col_m2, col_m3 = st.columns(3)

with col_m1:
    st.subheader("📌 テンション")
    ten_gap = ten - i_ten
    if abs(ten_gap) < 1.5: st.success(f"✅ 理想的（{i_ten:.1f} lbs）")
    elif ten_gap > 0: st.error(f"🚨 硬すぎ（+{ten_gap:.1f}）")
    else: st.warning(f"⚠️ 緩すぎ（{ten_gap:.1f}）")

with col_m2:
    st.subheader("📌 ガット太さ")
    if abs(gauge - i_gauge) < 0.02: st.success(f"✅ 適正（{i_gauge} mm）")
    else: st.info(f"ℹ️ 推奨: {i_gauge} mm")

with col_m3:
    st.subheader("📌 ラケット重量")
    if r_weight_class == i_w_class: st.success(f"✅ 適正（{r_weight_class}）")
    else: st.warning(f"⚠️ 理想は {i_w_class}")

# --- ショット別アドバイス（全記載） ---
st.divider()
st.header("👨‍🏫 ショット別：深掘りデバッグアドバイス")
shot_logic = {
    "スマッシュ": {"bug": "体幹連動なし。胸の開きが不十分で、腕力に頼りすぎています。", "neutral": "握り込みのタイミングを追求。ラケットの重量をシャトルに伝える感覚を磨いて。"},
    "ハイバック": {"bug": "肘を支点にした回外が使えていません。無理に打つと肘を壊します。", "neutral": "脱力が鍵。肩の入れ替えとラケットの重みを利用したスイングを。"},
    "ドライブ": {"bug": "反応が遅れ気味。テイクバックを最小限にし、コンパクトに。", "neutral": "面の角度と指先の弾きだけでコースを打ち分けてください。"},
    "クリア": {"bug": "打点が低く、肘が伸びきった状態で打っています。物理ロスが大きいです。", "neutral": "最高打点で。腹筋の収縮をスイングの始点に。"},
    "ヘアピン": {"bug": "タッチが硬い。指先でコルクを撫でるような柔軟性を。", "neutral": "ネットギリギリを通過する軌道をイメージして「静」の操作を。"},
    "ドロップ": {"bug": "スマッシュとフォームが変わりすぎているため、相手に読まれています。", "neutral": "スイングスピードを維持しつつ、インパクト直前で力を抜く「隠し」を。"},
    "プッシュ": {"bug": "振り回しすぎてオーバー。ネット前は指の握り込みだけで加速させます。", "neutral": "「刺す」イメージ。フォロースルーは不要です。"},
    "レシーブ": {"bug": "重心が高い。股関節を使い、ラケットを立てた状態で待ち構えて。", "neutral": "相手のパワーを利用し、面の角度だけで返球する効率性を。"},
    "バックハンド": {"bug": "親指の使い方が甘く、面のコントロールを失っています。", "neutral": "親指の押し出しによるパワー伝達と、前腕の回転を同期させて。"}
}
for shot, adv in shot_logic.items():
    with st.expander(f"🎯 {shot} の診断"):
        st.write(f"⚠️ **バグ発生時:** {adv['bug']}" if has_bug else f"✨ **適正状態:** {adv['neutral']}")

# --- 治療師アドバイス（全記載） ---
st.divider()
st.header("👨‍⚕️ 専門家によるコンディショニング指示")
col_coach, col_doc = st.columns(2)

with col_coach:
    st.subheader("👨‍🏫 コーチの総評")
    if age <= 12: st.info("🐣 ジュニア期：高テンションは関節の成長を阻害します。今はコントロール重視で。")
    elif age >= 50: st.warning("👴 シニア期：筋力低下を補うため、軽量ラケットと高反発ガットで効率化を。")
    if not has_bug: st.success("✅ 基礎は安定しています。次は「意図的なミスマッチ」で球質を変える段階です。")
    else: st.error(f"🚨 現在のバグは、重すぎる機材や高すぎるテンションで「力み」を誘発している可能性があります。")

with col_doc:
    st.subheader("🏥 身体管理")
    if has_pain:
        st.error("🚨 警告：現在の痛みは、物理的な不一致による代償動作（無理な動き）のサインです。")
        st.write("- 痛みが引くまでテンションを2lbs下げることを強く推奨。")
    else:
        st.success("✅ 身体の連動が保たれています。")
    
    if vol > rec_lim:
        st.error(f"🚨 練習過多：現在のリカバリー能力（週{int(rec_lim)}h）を超えています。休養も練習の一部です。")