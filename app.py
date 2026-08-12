import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# 1. 기본 설정
# ============================================================

st.set_page_config(
    page_title="서울 편의점 상권 분석",
    page_icon="🏪",
    layout="wide"
)


# ============================================================
# 2. 데이터 불러오기
# ============================================================

OUTPUT_DIR = "output"


market = pd.read_csv(
    f"{OUTPUT_DIR}/market_summary.csv"
)

region = pd.read_csv(
    f"{OUTPUT_DIR}/region_store_change.csv"
)

commercial = pd.read_csv(
    f"{OUTPUT_DIR}/commercial_summary.csv"
)

candidate = pd.read_csv(
    f"{OUTPUT_DIR}/startup_candidates.csv"
)

analysis = pd.read_csv(
    f"{OUTPUT_DIR}/final_analysis_dataset.csv"
)


# ============================================================
# 3. 데이터 정리
# ============================================================

# 연도 컬럼 숫자로 변환
for col in ["2023", "2024", "2025"]:
    if col in region.columns:
        region[col] = pd.to_numeric(
            region[col],
            errors="coerce"
        )

# 숫자 컬럼
number_columns = [
    "3년_증감",
    "총_상주인구_수",
    "총_직장_인구_수",
    "총_유동인구_수",
    "활동인구",
    "활동인구_대비_편의점"
]

for col in number_columns:
    if col in analysis.columns:
        analysis[col] = pd.to_numeric(
            analysis[col],
            errors="coerce"
        )


# ============================================================
# 4. 제목
# ============================================================

st.title("🏪 서울 편의점 상권 분석 대시보드")

st.write(
    "서울 행정동별 편의점 점포 변화와 "
    "상권 특성을 바탕으로 지역별 경쟁 수준과 "
    "창업 후보지역을 탐색합니다."
)


# ============================================================
# 5. 사이드바 필터
# ============================================================

st.sidebar.header("🔎 분석 조건")

# ------------------------------------------------------------
# 자치구 필터
# ------------------------------------------------------------

gu_list = sorted(
    analysis["자치구_명"].dropna().unique()
)

selected_gu = st.sidebar.multiselect(
    "자치구 선택",
    options=gu_list,
    default=[]
)


# ------------------------------------------------------------
# 상권 특성 필터
# ------------------------------------------------------------

zone_list = sorted(
    analysis["상권특성"].dropna().unique()
)

selected_zone = st.sidebar.multiselect(
    "상권 특성",
    options=zone_list,
    default=[]
)


# ------------------------------------------------------------
# 경쟁 수준 필터
# ------------------------------------------------------------

competition_list = sorted(
    analysis["경쟁수준_1차"].dropna().unique()
)

selected_competition = st.sidebar.multiselect(
    "경쟁 수준",
    options=competition_list,
    default=[]
)


# ------------------------------------------------------------
# 최소 편의점 수
# ------------------------------------------------------------

min_store = st.sidebar.slider(
    "2025년 최소 편의점 수",
    min_value=0,
    max_value=int(
        analysis["2025"].max()
    ),
    value=0
)


# ------------------------------------------------------------
# 3년 증감 범위
# ------------------------------------------------------------

change_min = int(
    analysis["3년_증감"].min()
)

change_max = int(
    analysis["3년_증감"].max()
)

selected_change = st.sidebar.slider(
    "3년간 점포수 증감",
    min_value=change_min,
    max_value=change_max,
    value=(change_min, change_max)
)


# ============================================================
# 6. 필터 적용
# ============================================================

filtered = analysis.copy()


# 자치구
if selected_gu:
    filtered = filtered[
        filtered["자치구_명"].isin(selected_gu)
    ]


# 상권 특성
if selected_zone:
    filtered = filtered[
        filtered["상권특성"].isin(selected_zone)
    ]


# 경쟁 수준
if selected_competition:
    filtered = filtered[
        filtered["경쟁수준_1차"].isin(selected_competition)
    ]


# 최소 편의점
filtered = filtered[
    filtered["2025"] >= min_store
]


# 3년 증감
filtered = filtered[
    filtered["3년_증감"].between(
        selected_change[0],
        selected_change[1]
    )
]


# ============================================================
# 7. KPI
# ============================================================

st.subheader("📌 현재 조건의 지역 현황")

col1, col2, col3, col4 = st.columns(4)


with col1:
    st.metric(
        "분석 행정동 수",
        f"{len(filtered):,}"
    )


with col2:
    st.metric(
        "편의점 수",
        f"{filtered['2025'].sum():,.0f}"
    )


with col3:
    st.metric(
        "평균 편의점 수",
        f"{filtered['2025'].mean():.1f}"
    )


with col4:
    st.metric(
        "3년 점포 증감",
        f"{filtered['3년_증감'].sum():+,.0f}"
    )


# ============================================================
# 8. 서울 전체 편의점 추이
# ============================================================

st.subheader("📈 서울 편의점 시장 3개년 추이")

fig, ax = plt.subplots(
    figsize=(10, 4)
)

ax.plot(
    market["연도"],
    market["점포_수"],
    marker="o"
)

ax.set_xlabel("연도")
ax.set_ylabel("편의점 점포수")
ax.set_title("서울 편의점 점포수 변화")

st.pyplot(fig)


# ============================================================
# 9. 필터 지역 편의점 TOP 10
# ============================================================

st.subheader("🏪 현재 조건에서 편의점이 많은 지역")

top_region = (
    filtered
    .sort_values(
        "2025",
        ascending=False
    )
    .head(10)
)

fig, ax = plt.subplots(
    figsize=(10, 5)
)

ax.barh(
    top_region["지역명"].iloc[::-1],
    top_region["2025"].iloc[::-1]
)

ax.set_xlabel("2025년 편의점 수")
ax.set_ylabel("지역")

st.pyplot(fig)


# ============================================================
# 10. 3년간 증가 / 감소 지역
# ============================================================

st.subheader("📊 편의점 점포 변화")

change_region = (
    filtered
    .sort_values(
        "3년_증감",
        ascending=False
    )
    .head(10)
)

fig, ax = plt.subplots(
    figsize=(10, 5)
)

ax.barh(
    change_region["지역명"].iloc[::-1],
    change_region["3년_증감"].iloc[::-1]
)

ax.set_xlabel("2023 → 2025 점포수 변화")
ax.set_ylabel("지역")

st.pyplot(fig)


# ============================================================
# 11. 상권 특성별 편의점 현황
# ============================================================

st.subheader("🏙️ 상권 특성별 편의점 현황")

zone_summary = (
    filtered
    .groupby("상권특성")
    .agg(
        지역수=("지역명", "count"),
        편의점수=("2025", "sum"),
        평균편의점수=("2025", "mean")
    )
    .reset_index()
    .sort_values(
        "편의점수",
        ascending=False
    )
)

st.dataframe(
    zone_summary,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# 12. 상권 특성별 그래프
# ============================================================

fig, ax = plt.subplots(
    figsize=(10, 5)
)

ax.bar(
    zone_summary["상권특성"],
    zone_summary["편의점수"]
)

ax.set_xlabel("상권 특성")
ax.set_ylabel("2025년 편의점 수")
ax.set_title("상권 특성별 편의점 수")

plt.xticks(rotation=20)

st.pyplot(fig)


# ============================================================
# 13. 상세 지역 분석
# ============================================================

st.subheader("🔎 지역 상세 분석")

detail_columns = [
    "지역명",
    "상권특성",
    "경쟁수준_1차",
    2023,
    2025,
    "3년_증감",
    "총_상주인구_수",
    "총_직장_인구_수",
    "총_유동인구_수"
]

detail_columns = [
    col
    for col in detail_columns
    if col in filtered.columns
]

st.dataframe(
    filtered[
        detail_columns
    ].sort_values(
        "2025",
        ascending=False
    ),
    use_container_width=True,
    hide_index=True
)


# ============================================================
# 14. 창업 후보지역
# ============================================================

st.subheader("🎯 창업 후보지역")

candidate_filtered = candidate.copy()


# 후보지역에도 자치구 필터 적용
if selected_gu:
    candidate_filtered = candidate_filtered[
        candidate_filtered["자치구_명"].isin(
            selected_gu
        )
    ] if "자치구_명" in candidate_filtered.columns else candidate_filtered


# 상권 특성 필터
if selected_zone:
    candidate_filtered = candidate_filtered[
        candidate_filtered["상권특성"].isin(
            selected_zone
        )
    ]


candidate_columns = [
    "지역명",
    "상권특성",
    2023,
    2025,
    "3년_증감",
    "총_상주인구_수",
    "총_직장_인구_수",
    "총_유동인구_수",
    "활동인구_대비_편의점",
    "후보점수"
]

candidate_columns = [
    col
    for col in candidate_columns
    if col in candidate_filtered.columns
]

st.dataframe(
    candidate_filtered[
        candidate_columns
    ].head(20),
    use_container_width=True,
    hide_index=True
)


# ============================================================
# 15. 안내
# ============================================================

st.info(
    "※ 창업 후보지역은 편의점 점포수, 3년간 변화, "
    "활동인구 등을 활용한 1차 후보 탐색 결과입니다. "
    "실제 창업 가능성을 확정하는 결과는 아닙니다."
)