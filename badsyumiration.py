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
    
    gauge = st.slider(
        "ガットの太さ (mm)", 
        min_value=0.58, 
        max_value=0.70, 
        value=0.66,
        step=0.01
    )
    vol = st.slider("練習量 (h/週)", 0, 84, 10)

# --- 演算エンジン ---
def calculate_all_logic(age, years, grip, weight, ten, gauge, vol, h_list, h_severity, has_bug, pattern, r_weight_class, pain_count, has_pain):
    weight_map = {"F (超軽量)": 73, "5U": 78, "4U": 83, "3U": 88, "2U (重量級)": 93}
    current_w = weight_map[r_weight_class]
    
    if grip < 25: ideal_w = 78
    elif grip > 50: ideal_w = 88
    else: ideal_w = 83
    
    age_stiffness_factor = 1.0
    if age < 15:
        age_stiffness_factor = 0.7 + (age / 50)
    elif age > 45:
        age_stiffness_factor = max(0.6, 1.0 - (age - 45) * 0.015)

    experience_factor = (years - 5) * 0.2
    if grip <= 20:
        ideal_gauge = 0.61 
    elif grip < 35:
        ideal_gauge = 0.66 if years >= 8 else 0.61
    elif grip > 55:
        ideal_gauge = 0.68
    else:
        ideal_gauge = 0.66

    ideal_ten = ((grip * 0.4) + 10 + experience_factor) * age_stiffness_factor
    
    if has_pain:
        ideal_ten -= 2.0
    
    weight_diff = current_w - ideal_w
    ten_diff = ten - ideal_ten 
    gauge_diff = gauge - ideal_gauge
    
    base_power = (grip * 1.5) + (weight * 0.2)
    weight_p_bonus = (current_w - 83) * 1.8
    gauge_p_impact = (0.66 - gauge) * 100 
    
    if ten_diff > 0:
        ten_p_impact = -(ten_diff ** 1.3) * 1.5
    else:
        ten_p_impact = abs(ten_diff) * 1.2 if abs(ten_diff) < 5 else 6.0 - (abs(ten_diff)-5)

    power_score = max(10, min(100, base_power + weight_p_bonus + gauge_p_impact + ten_p_impact))

    weight_diff_penalty = abs(weight_diff) * 3.0
    effective_ten_diff = max(0, abs(ten_diff) - 0.5)
    ten_mismatch_penalty = effective_ten_diff * 5.0
    effective_gauge_diff = max(0, abs(gauge_diff) - 0.01)
    gauge_mismatch_penalty = effective_gauge_diff * 150.0

    suit = 100 - (weight_diff_penalty + ten_mismatch_penalty + gauge_mismatch_penalty)
    suit -= (max(0, 25 - weight/2) * 5)
    
    if age <= 12: recovery_limit = 8 + (age * 0.5)
    elif 18 <= age <= 30: recovery_limit = 25 + (years * 0.5)
    else: recovery_limit = max(8, 25 - (age - 30) * 0.6)

    weight_fatigue_mult = 1.0 + (current_w - 83) * 0.04 
    effective_recovery_limit = recovery_limit / max(0.8, weight_fatigue_mult)
    
    if vol > effective_recovery_limit:
        age_impact = 4.0 if (age < 13 or age > 50) else 2.0
        suit -= (vol - effective_recovery_limit) * age_impact
    
    if has_bug: suit -= (h_severity * 10)
    
    suit = max(0, min(100, suit))

    rehab_m = 0.0
    if has_bug:
        base_m = (years * 0.7) * (h_severity * 0.4)
        age_learning_factor = 0.4 if age < 15 else (1.0 + (max(0, age-40) * 0.02))
        vol_factor = 1.8 if vol < 3 else (0.8 if vol <= effective_recovery_limit else 1.3)
        gear_obs_factor = 1.0 + (abs(weight_diff) * 0.07)
        rehab_m = round(base_m * age_learning_factor * vol_factor * gear_obs_factor * (0.6 if "パターンA" in pattern else 1.5), 1)

    s_score = max(10, min(100, 100 - (vol / effective_recovery_limit * 35 if vol > 0 else 0)))
    
    weight_injury_risk = abs(weight_diff) * 1.5
    pain_impact = pain_count * 15
    ir_score = max(10, min(100, 100 - (h_severity * 12) - pain_impact - weight_injury_risk))

    return suit, rehab_m, effective_recovery_limit, ideal_ten, ideal_gauge, power_score, s_score, ir_score, ideal_w

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
    pain_count = sum(p_checks)
    has_pain = pain_count > 0 and not p_none

# --- ロジック実行 ---
fix_pattern = "修正不要"
if has_bug:
    st.divider()
    fix_pattern = st.radio("更生アプローチ", ["パターンA：徹底修正（物理矯正）", "パターンB：並行修正（妥協案）"])

suit_s, rehab_m, rec_lim, i_ten, i_gauge, p_score, s_score, ir_score, i_w = calculate_all_logic(
    age, years, grip, weight, ten, gauge, vol, h_checks, h_severity_sum, has_bug, fix_pattern, r_weight_class, pain_count, has_pain
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
    - **推奨テンション:** {i_ten:.1f} lbs {"(⚠️補正済)" if has_pain else ""}
    - **練習キャパ:** 週 {int(rec_lim)} 時間以内
    """)
    
    weight_map = {"F (超軽量)": 73, "5U": 78, "4U": 83, "3U": 88, "2U (重量級)": 93}
    current_w = weight_map[r_weight_class]
    if current_w > i_w + 5:
        st.warning(f"⚠️ 重量過多：現在の{r_weight_class}は重すぎます。")
    elif current_w < i_w - 5:
        st.info(f"ℹ️ 重量不足：{r_weight_class}は軽すぎます。")

# --- 詳細診断レポート ---
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
    if abs(ten_gap) <= 0.5:
        st.success(f"✅ 理想的（{i_ten:.1f} lbs）")
    elif ten_gap > 0: st.error(f"🚨 硬すぎ（+{ten_gap:.1f}）")
    else: st.warning(f"⚠️ 緩すぎ（{ten_gap:.1f}）")

with col_m2:
    st.subheader("📌 ガット太さ")
    if abs(gauge - i_gauge) <= 0.01:
        st.success(f"✅ 適正（{i_gauge} mm）")
    else: st.info(f"ℹ️ 推奨: {i_gauge} mm")

with col_m3:
    st.subheader("📌 ラケット重量")
    if r_weight_class == i_w_class: st.success(f"✅ 適正（{r_weight_class}）")
    else:
        diff_g = weight_map[r_weight_class] - weight_map[i_w_class]
        st.warning(f"⚠️ 理想は {i_w_class} ({'+' if diff_g>0 else ''}{diff_g}gの乖離)")

# --- 治療師アドバイス（動的修正版） ---
st.divider()
st.header("👨‍⚕️ 専門家によるコンディショニング指示")
col_coach, col_doc = st.columns(2)

with col_coach:
    st.subheader("👨‍🏫 コーチの総評")
    if age <= 12:
        st.info("🐣 ジュニア期：骨格が成長中です。今はパワーより「シャトルの芯を捉える感覚」を養ってください。")
    elif age >= 55:
        st.warning("👴 シニア期：筋力よりも「効率的な脱力」が武器になります。無理な強打は避けましょう。")
    
    if not has_bug:
        st.success("✅ フォームに目立ったバグはありません。現在のOSをベースに精度を高めましょう。")
    else:
        st.error("🚨 警告：技術的な癖によるエネルギーロスが発生しています。")
        # 選択されたバグに応じたアドバイス
        if h_western: st.write("- **ウエスタン対策:** バック側の打球で手首を痛めるリスク大。グリップの矯正が急務。")
        if h_teuchi: st.write("- **手打ち対策:** 遠心力が使えていません。下半身からのパワー伝達が必要です。")
        if h_hiji: st.write("- **肘の伸び対策:** 肩甲骨の可動域が制限されています。打点を少し前へ。")
        if h_neko: st.write("- **猫手対策:** 手首の柔軟性が死んでいます。リラックスした構えを。")

with col_doc:
    st.subheader("🏥 身体管理")
    # 痛みがある場合
    if has_pain:
        st.error(f"🚨 警告：身体の {pain_count} 箇所に痛みがあります。")
        st.warning(f"💡 【処方】関節保護のため、推奨テンションを通常より **2.0 lbs 下げた {i_ten:.1f} lbs** に補正しました。")
        if p_hiji or p_tekubi:
            st.write("- **上肢管理:** インパクト時の振動が直接関節に届いています。太いガットへの変更も検討。")
        if p_koshi or p_ashi:
            st.write("- **下肢・体幹管理:** フットワークの着地衝撃が吸収できていません。インソールの見直しを。")
    # 痛みはないがバグがある場合（潜在的なリスク）
    elif has_bug:
        st.warning("⚠️ 潜在的リスク：現在は痛みがないようですが、フォームのバグが関節に負担をかけています。")
        if h_teuchi or h_dead:
            st.write("- 肩や肘への負荷を逃がすために、テンションを1〜2lbs下げる「予防的措置」も有効です。")
        if h_bo or h_ashi:
            st.write("- 足が止まっているため、上半身だけでシャトルを追う癖がついています。膝への負担に注意。")
    # 痛みもバグもない場合
    else:
        st.success("✅ 身体の連動・コンディション共に良好です。現在の強度で練習を継続可能です。")
    
    # 練習量に関する警告
    if vol > rec_lim:
        st.error(f"🚨 オーバーワーク（週 {vol}h）：リカバリー限界（週 {int(rec_lim)}h）を超過しています。")
    elif vol > rec_lim * 0.8:
        st.warning("⚠️ 負荷高め：練習量が限界に近いです。積極的休養（睡眠・ストレッチ）を優先してください。")

# --- ショット別アドバイス ---
st.divider()
st.header("👨‍🏫 ショット別：深掘りデバッグアドバイス")
shot_logic = {
    "スマッシュ": {"bug": "体幹連動なし。腕力に頼りすぎです。", "neutral": "ラケットの重量とガットの反発を同期させて。"},
    "ハイバック": {"bug": "回外が使えていません。無理は禁物。", "neutral": "肩の入れ替えと脱力を意識。"},
    "ドライブ": {"bug": "反応遅れ。コンパクトなスイングを。", "neutral": "指先の弾きでコースを打ち分けて。"},
    "クリア": {"bug": "打点が低い。物理ロス大。", "neutral": "最高打点で腹筋を使って。"},
    "ヘアピン": {"bug": "タッチが硬い。指先の柔軟性を。", "neutral": "コルクを撫でるイメージ。"},
    "ドロップ": {"bug": "フォームでバレています。", "neutral": "インパクト直前の減速を隠して。"},
    "プッシュ": {"bug": "振り回しすぎ。握り込みで加速。", "neutral": "フォロースルーを抑えて「刺す」。"},
    "レシーブ": {"bug": "重心が高い。股関節を使って。", "neutral": "面の角度だけで返球。"},
    "バックハンド": {"bug": "親指の使い方が甘い。", "neutral": "前腕の回転と同期させて。"}
}
for shot, adv in shot_logic.items():
    with st.expander(f"🎯 {shot} の診断"):
        st.write(f"⚠️ **バグ発生時:** {adv['bug']}" if has_bug else f"✨ **適正状態:** {adv['neutral']}")