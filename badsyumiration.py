import streamlit as st
import pandas as pd

# 1. ページ設定
st.set_page_config(page_title="バドミントン物理・機材・更生シミュレーター", layout="wide")
st.title("🏸 決定版：バドミントン物理デバッグ & 機材適合診断")

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
    age = st.slider("現在の年齢", 5, 80, 25)
    years = st.slider("経験年数", 0, 50, 4)
    grip = st.slider("握力 (kg)", 5, 100, 40)
    weight = st.slider("体重 (kg)", 20, 120, 60)
    
    st.header("⚙️ 2. 機材・練習環境")
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
    
    h_checks = [h_western, h_neko, h_teuchi, h_hiji, h_dead, h_hanmi, h_ashi, h_bo, h_atama]
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
def calculate_all_logic(age, years, grip, weight, ten, gauge, vol, h_list, has_bug, pattern):
    # 1. 年齢補正
    age_stiffness_factor = 1.0
    if age < 15:
        age_stiffness_factor = 0.7 + (age / 50)
    elif age > 45:
        age_stiffness_factor = max(0.6, 1.0 - (age - 45) * 0.015)

    # 理想テンション算出
    experience_factor = (years - 5) * 0.2
    ideal_ten = ((grip * 0.4) + 10 + experience_factor) * age_stiffness_factor
    ten_diff = abs(ten - ideal_ten)
    
    # 理想ガット太さ算出
    if age < 13: ideal_gauge = 0.61
    elif age > 50: ideal_gauge = 0.68
    elif grip > 55: ideal_gauge = 0.68
    elif grip < 35: ideal_gauge = 0.61
    else: ideal_gauge = 0.66
    
    gauge_diff = abs(gauge - ideal_gauge)
    gauge_suitability = 8 - (gauge_diff * 120)

    # 2. スコア計算
    suit = 100 - (ten_diff * 5) + gauge_suitability
    suit -= (max(0, 25 - weight/2) * 5)
    
    # 3. 耐久限界
    if age <= 12: recovery_limit = 8 + (age * 0.5)
    elif 18 <= age <= 30: recovery_limit = 25 + (years * 0.5)
    else: recovery_limit = max(8, 25 - (age - 30) * 0.6)

    # ペナルティ
    fatigue_penalty = 0
    if vol > recovery_limit:
        age_impact = 4.0 if (age < 13 or age > 50) else 2.0
        fatigue_penalty += (vol - recovery_limit) * age_impact
        if has_bug: fatigue_penalty += (vol - recovery_limit) * 1.5

    suit -= fatigue_penalty
    if has_bug: suit -= (sum(h_list) * 12)
    suit = max(0, min(100, suit))

    # 更生期間
    rehab_m = 0.0
    if has_bug:
        base_m = (years * 0.8) * (sum(h_list) * 0.5)
        age_learning_factor = 0.4 if age < 15 else (1.0 + (max(0, age-40) * 0.02))
        rehab_m = round(base_m * age_learning_factor * (0.6 if "パターンA" in pattern else 1.5), 1)

    return suit, rehab_m, recovery_limit, ideal_ten, ideal_gauge

# 更生パターンの取得
fix_pattern = "修正不要"
if has_bug:
    st.divider()
    fix_pattern = st.radio("更生アプローチ", ["パターンA：徹底修正", "パターンB：並行修正"])

suit_s, rehab_m, rec_lim, i_ten, i_gauge = calculate_all_logic(age, years, grip, weight, ten, gauge, vol, h_checks, has_bug, fix_pattern)

# --- 結果レポート ---
st.divider()
st.header("📊 診断レポート")
c1, c2, c3 = st.columns(3)
c1.metric("物理システム適合度", f"{int(suit_s)}/100")
if has_bug:
    c2.metric("更生完了まで", f"{rehab_m} ヶ月")
    c3.metric("推奨練習量 (週)", f"{int(rec_lim)} h")
else:
    c2.metric("状態", "ニュートラル")
    c3.metric("耐久限界 (週)", f"{int(rec_lim)} h")

# --- 【新機能】機材不一致（物理的ミスマッチ）診断 ---
st.divider()
st.header("⚙️ 機材不一致（物理的ミスマッチ）の診断")
col_m1, col_m2 = st.columns(2)

with col_m1:
    st.subheader("📌 テンション適合度")
    ten_gap = ten - i_ten
    if abs(ten_gap) < 1.5:
        st.success(f"✅ 完璧な調整（理想値: {i_ten:.1f} lbs）")
    elif ten_gap > 0:
        st.error(f"🚨 テンション過多（+{ten_gap:.1f} lbs）")
        st.write("【物理的リスク】インパクト時にガットがたわみ切らず、衝撃が筋肉を通り越して骨・関節に直撃しています。特にオフセンターショット時の振動はテニス肘の主因となります。")
    else:
        st.warning(f"⚠️ テンション不足（{ten_gap:.1f} lbs）")
        st.write("【物理的リスク】ガットの復元が遅く、スイングエネルギーを吸収してしまっています。飛ばそうとして無理に手首をこねる癖（バグ）を誘発しやすくなります。")

with col_m2:
    st.subheader("📌 ガット太さ適合度")
    if abs(gauge - i_gauge) < 0.02:
        st.success(f"✅ 適正なゲージ（推奨: {i_gauge} mm）")
    elif gauge > i_gauge:
        st.info(f"ℹ️ オーバースペック（推奨: {i_gauge} mm）")
        st.write("【物理的影響】耐久性は高いですが、空気抵抗と重量が増し、繊細なラケットワークを阻害しています。タッチ系のショットで「弾き」の感覚が鈍ります。")
    else:
        st.info(f"ℹ️ アンバースペック（推奨: {i_gauge} mm）")
        st.write("【物理的影響】反発力は高いですが、強打時に面が暴れやすく、コントロールの不確実性が高まっています。あなたのパワーに対して面剛性が不足しています。")

# --- ショット別アドバイス ---
st.divider()
st.header("👨‍🏫 ショット別：深掘りデバッグアドバイス")
shot_logic = {
    "スマッシュ": {"bug": "体幹連動なし。胸の開きで。年齢的に肩の可動域が狭まっている可能性あり。", "neutral": "握り込みのタイミングを追求。年齢に応じた打点位置の微調整を。"},
    "ハイバック": {"bug": "肘を支点にした回外が使えていません。筋力に頼ると肘を壊します。", "neutral": "脱力が鍵。太いガットなら面を当てるだけで飛びます。"},
    "ドライブ": {"bug": "反応遅延。指先の空間不足。加齢による動体視力低下をフォームで補う必要あり。", "neutral": "コンパクトな振り。細いガットの弾きを最大限に利用して。"},
    "クリア": {"bug": "肘が伸びきり、遠心力をロス。下半身の入れ替えで飛距離を稼いで。", "neutral": "最小限の力で奥まで飛ばす効率を重視。"},
    "ヘアピン": {"bug": "タッチが硬い。デッドグリップを解いて指先でコルクを感じて。", "neutral": "ネット前での「静」の操作。"},
    "ドロップ": {"bug": "スマッシュとのフォーム差が顕著。物理的な「減速」を覚えて。", "neutral": "シャトルの軌道をデザインする感覚。"},
    "プッシュ": {"bug": "大振り。ネット前は指の握り込みだけで十分です。", "neutral": "シャトルを「叩く」のではなく「刺す」イメージ。"},
    "レシーブ": {"bug": "重心が高い。低い姿勢が取れないと強打は返せません。", "neutral": "リバウンドを拾う柔軟な面作り。"},
    "バックハンド": {"bug": "手首を折る猫手。前腕の回転（回外）を意識して。", "neutral": "親指の押し出しによるパワー伝達。"}
}
for shot, adv in shot_logic.items():
    with st.expander(f"🎯 {shot} の診断"):
        st.write(f"⚠️ **バグ時:** {adv['bug']}" if has_bug else f"✨ **適正時:** {adv['neutral']}")

# --- 治療師アドバイス ---
st.divider()
st.header("👨‍⚕️ 治療師：年代別コンディショニング指示")
col_coach, col_doc = st.columns(2)

with col_coach:
    st.subheader("👨‍🏫 コーチの総評")
    if age <= 12: st.info("🐣 ジュニア：今は高テンションを避け、多彩なショットを打てる「神経系」を育てる時期です。")
    elif age >= 50: st.warning("👴 シニア：筋力より「効率」。重いラケットや高テンションは関節の敵です。")
    if not has_bug: st.success("✅ フォームに大きな欠陥はありません。機材との同調を高めましょう。")
    else: st.error(f"🚨 {years}年の癖を剥がすには、練習量より「質の高い更生」が必要です。")

with col_doc:
    if has_pain:
        st.subheader("🩹 痛みへの対応")
        st.error("🚨 痛みがある部位は即アイシング。物理的な不適合（年齢・機材）を即修正してください。")
    else:
        st.success("✅ 関節トラブルなし。現在の負荷設定を維持可能。")

    if vol > rec_lim:
        st.error(f"🚨 【摩耗注意】{age}歳の身体にとって週{vol}hは過負荷です。")
    elif age > 45 and ten > 26:
        st.warning("⚠️ 45歳を超えての27lbs以上は、腱鞘炎の物理的リスクが急増します。")