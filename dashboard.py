import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------
# 1. 페이지 설정 및 데이터 생성 (가상 데이터)
# -----------------------------------------------------------
st.set_page_config(page_title="출석 종합 분석 대시보드", layout="wide")

@st.cache_data
def generate_advanced_data():
    # 500명의 가상 회원 데이터 생성
    np.random.seed(42)
    users = pd.DataFrame({
        'user_id': range(1, 501),
        'name': [f'Member_{i}' for i in range(1, 501)],
        # A. Z-score 데이터 (급격한 변화)
        'z_score': np.random.normal(0, 1.5, 500), 
        # B. 이동평균 데이터 (단기 vs 장기)
        'ma_short': np.random.uniform(40, 90, 500),
        'ma_long': np.random.uniform(50, 95, 500),
        # C. 생존 분석 데이터 (가입 개월 수)
        'months_active': np.random.randint(1, 24, 500),
        # D. RFM 데이터
        'recency': np.random.randint(1, 60, 500), # 며칠 전에 왔는가
        'frequency': np.random.randint(1, 20, 500), # [핵심 지표] 월 몇 회 (1~20)
        'monetary': np.random.randint(1, 100, 500), # 참여 강도 점수
        # E. 로지스틱 회귀 예측값 (이탈 확률)
        'churn_prob': np.random.uniform(0, 1, 500)
    })
    
    # 파생 변수 생성
    # Dead Cross 여부 (단기가 장기보다 10% 이상 낮을 때)
    users['dead_cross'] = users['ma_short'] < (users['ma_long'] * 0.9)
    # RFM 세그먼트 (간단 분류)
    users['rfm_segment'] = np.where((users['recency'] < 14) & (users['frequency'] > 10), '충성 회원',
                             np.where(users['recency'] > 30, '이탈 위험', '일반 회원'))
    
    # 출석 급감 사유 데이터 추가
    reasons = ['건강 문제', '업무 과다/야근', '콘텐츠 난이도', '개인 사정/경조사', '단순 흥미 저하']
    
    # Z-score가 -1.5 이하인 회원들에게 무작위로 사유 할당
    users['last_reason_category'] = np.where(users['z_score'] <= -1.5, 
                                          np.random.choice(reasons, 500, p=[0.25, 0.35, 0.15, 0.15, 0.10]), 
                                          None)
    
    def generate_detail(row):
        if row['last_reason_category'] == '업무 과다/야근':
            return "최근 프로젝트 마감으로 저녁 시간 활용이 어렵습니다."
        elif row['last_reason_category'] == '건강 문제':
            return "독감으로 인해 이번 주 내내 집에서 쉬고 있습니다."
        elif row['last_reason_category'] == '콘텐츠 난이도':
            return "초급반인데 갑자기 어려운 이론이 나와서 흥미를 잃었습니다."
        return None

    users['last_reason_detail'] = users.apply(generate_detail, axis=1)

    return users

df = generate_advanced_data()

# -----------------------------------------------------------
# 2. KPI 계산
# -----------------------------------------------------------
total_members = len(df)
count_8_plus = df[df['frequency'] >= 8].shape[0]
count_4_plus = df[df['frequency'] >= 4].shape[0]
count_1_plus = df[df['frequency'] >= 1].shape[0]

# [MODIFIED] 미출석 인원 카운트 추가
count_0_times = total_members - count_1_plus

# 이전 런 대비 변화량 (가상으로 델타 값 설정)
delta_8_plus = np.random.randint(-10, 10) 
delta_4_plus = np.random.randint(-15, 15)
# 미출석 인원 변화량 (가상)
delta_0_times = np.random.randint(-5, 0)


# -----------------------------------------------------------
# 3. 사이드바 (전역 필터)
# -----------------------------------------------------------
st.sidebar.title("🔍 분석 옵션")
st.sidebar.subheader("경고 기준 설정")
z_threshold = st.sidebar.slider("Z-score 민감도 (표준편차 배수)", -5.0, -1.0, -2.0)
churn_threshold = st.sidebar.slider("이탈 예측 확률 경고 기준", 0.5, 0.9, 0.7)

# -----------------------------------------------------------
# 4. 메인 대시보드 구성
# -----------------------------------------------------------
st.title("📊 통합 출석 분석 시스템 (정량 + 정성 데이터)")
st.markdown("5가지 통계 기법과 출석 사유를 결합하여 이탈 원인을 진단합니다.")

# [MODIFIED] 상단 KPI 배너 (5개 칼럼 구성)
st.subheader("📌 핵심 출석 빈도 현황 (최근 측정 기간 기준)")
# 총 5개의 지표를 위해 5개 칼럼 사용
col_total, col_0, col_8, col_4, col_1 = st.columns(5) 

col_total.metric(label="👥 총 회원 수", value=f"{total_members} 명")

# 미출석 인원 (가장 중요한 위험 지표)
col_0.metric(label="❌ 미출석 인원 (0회)", 
             value=f"{count_0_times} 명", 
             delta=f"{delta_0_times} vs 지난주", 
             delta_color="inverse") # 증가하면 위험하므로 inverse 사용

# 출석 인원 카테고리
col_8.metric(label="✅ 8회 이상 (핵심 활동)", 
             value=f"{count_8_plus} 명", 
             delta=f"{delta_8_plus} vs 지난주", delta_color="normal")
col_4.metric(label="⚠️ 4회 이상 (유지 경계)", 
             value=f"{count_4_plus} 명", 
             delta=f"{delta_4_plus} vs 지난주", delta_color="normal")
col_1.metric(label="➡️ 1회 이상 (최소 참여)", 
             value=f"{count_1_plus} 명")

# [REMOVED] st.markdown("---") : 탭과 KPI 사이의 불필요한 구분선 제거


# 탭 구성 (핵심 전략)
tab1, tab2, tab3 = st.tabs(["🚨 급감 & 원인 분석", "🧩 회원 그룹 (RFM)", "🔮 미래 예측 (Prediction)"])

# --- Tab 1: A. Z-score & B. 이동평균 & 사유 분석 (현상 파악) ---
with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("A. 급락 감지 (Z-score) 및 사유 분포")
        st.info(f"평소 패턴 대비 {z_threshold} 표준편차 이상 떨어진 회원들에게 사유가 접수되었습니다.")
        
        # Z-score가 기준보다 낮은 위험군 필터링
        anomaly_users = df[df['z_score'] <= z_threshold]
        
        # Z-score 차트: 사유 카테고리별로 색상 구분
        fig_z = px.scatter(df, x='user_id', y='z_score', 
                           color='last_reason_category', # 사유 카테고리별로 색상 구분
                           color_discrete_map={None: 'blue', '업무 과다/야근': 'red', '건강 문제': 'orange', '콘텐츠 난이도': 'purple', '개인 사정/경조사': 'green', '단순 흥미 저하': 'brown'},
                           title="전체 회원 Z-score 분포 (색상: 결석 사유)")
        # 기준선 추가
        fig_z.add_hline(y=z_threshold, line_dash="dash", line_color="red")
        st.plotly_chart(fig_z, use_container_width=True)
        
    with col2:
        st.subheader("📊 주요 결석 사유 Top 5")
        # 사유가 있는 데이터만 필터링 후 빈도 분석
        reason_counts = df[df['last_reason_category'].notnull()]['last_reason_category'].value_counts().reset_index()
        reason_counts.columns = ['Category', 'Count']
        
        fig_bar = px.bar(reason_counts, x='Count', y='Category', orientation='h',
                         color='Count', title="카테고리별 빈도",
                         color_continuous_scale='Reds')
        st.plotly_chart(fig_bar, use_container_width=True)
        
        st.info("💡 **가장 큰 문제:** '업무 과다/야근'으로 인한 결석이 가장 많습니다. 저녁 프로그램 시간 조정이 필요할 수 있습니다.")

    st.divider()

    # B. 추세 하락 (Dead Cross) 리스트
    st.subheader("B. 추세 하락 감지 리스트 (이동 평균)")
    dead_cross_users = df[df['dead_cross'] == True]
    st.metric("추세 하락 감지 회원", f"{len(dead_cross_users)} 명")
    st.dataframe(dead_cross_users[['name', 'ma_short', 'ma_long', 'last_reason_category']].sort_values('ma_short'), 
                 hide_index=True, use_container_width=True)


# --- Tab 2: D. RFM 분석 (전략 수립) ---
with tab2:
    st.subheader("D. 회원 세그먼트 분석 (RFM)")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # 3D 산점도 (Recency, Frequency, Monetary)
        fig_rfm = px.scatter_3d(df, x='recency', y='frequency', z='monetary',
                                color='rfm_segment',
                                title="회원 성향 3D 매핑",
                                hover_data=['name'])
        st.plotly_chart(fig_rfm, use_container_width=True)
        
    with col2:
        st.write("### 그룹별 현황")
        group_counts = df['rfm_segment'].value_counts()
        st.write(group_counts)
        st.caption("Recency: 최근 방문일\nFrequency: 방문 빈도\nMonetary: 참여 강도")

# --- Tab 3: C. 생존 분석 & E. 로지스틱 회귀 (예측) ---
with tab3:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("C. 생존 분석 (이탈 시기 패턴)")
        # 가상의 생존 곡선 데이터 생성 (Kaplan-Meier 스타일)
        survival_data = pd.DataFrame({
            'month': range(1, 25),
            'survival_rate': [100 - (i * 3 + np.random.randint(0, 5)) for i in range(24)]
        })
        fig_surv = px.line(survival_data, x='month', y='survival_rate', 
                           markers=True, title="기간별 회원 생존율(유지율) 추이")
        st.plotly_chart(fig_surv, use_container_width=True)
        st.caption("💡 3개월, 6개월 차에 기울기가 급격해지는지 확인 필요")
        
    with col2:
        st.subheader("E. 이탈 확률 예측 (Logistic Regression)")
        st.write(f"이탈 확률이 **{churn_threshold*100:.0f}%** 이상인 고위험군")
        
        high_risk_users = df[df['churn_prob'] >= churn_threshold].sort_values('churn_prob', ascending=False)
        
        # 색상 포맷팅 (확률이 높을수록 붉게 표시하기 위해 pandas style 활용)
        st.dataframe(
            high_risk_users[['name', 'churn_prob', 'z_score', 'rfm_segment', 'last_reason_category']]
            .style.background_gradient(subset=['churn_prob'], cmap='Reds'),
            use_container_width=True
        )

# -----------------------------------------------------------
# 5. 개인 상세 분석 (Drill Down) - 사유 정보 강조
# -----------------------------------------------------------
st.divider()
st.subheader("🔍 개인별 상세 조회 및 사유 히스토리")

# 급감/이탈 위험 회원만 먼저 보이도록 필터링
risk_members = df[(df['z_score'] <= z_threshold) | (df['churn_prob'] >= churn_threshold)]['name'].unique()
selected_user_name = st.selectbox("회원 선택 (급감/고위험군 우선)", risk_members if len(risk_members) > 0 else df['name'].unique())

user_data = df[df['name'] == selected_user_name].iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Z-score (패턴변화)", f"{user_data['z_score']:.2f}", delta_color="inverse")
c2.metric("이탈 예측 확률", f"{user_data['churn_prob']:.1%}", 
          delta="위험" if user_data['churn_prob'] > churn_threshold else "안전", delta_color="inverse")
c3.metric("최근 방문(Recency)", f"{user_data['recency']}일 전")
c4.metric("RFM 등급", user_data['rfm_segment'])

# 사유 정보 블록
st.markdown("---")
st.write("### 📢 최근 급감 사유 및 코멘트")

if user_data['last_reason_category']:
    st.error(f"**🚨 감지된 주 사유:** {user_data['last_reason_category']}")
    if user_data['last_reason_detail']:
        st.warning(f"**💬 회원 코멘트:** {user_data['last_reason_detail']}")
    else:
        st.warning("상세 코멘트는 접수되지 않았습니다.")
else:
    st.info("특정 사유가 접수되지 않았거나 급감하지 않은 회원입니다.")

st.caption("이곳에 선택된 회원의 월별 출석 그래프(Line Chart)를 추가하여 사유 발생 시점과 출석률 변화를 비교하면 좋습니다.")