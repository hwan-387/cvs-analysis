import platform
from pathlib import Path

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd


# ============================================================
# 1. 페이지 설정 및 한글 폰트
# ============================================================

st.set_page_config(
    page_title="서울 편의점 상권 분석 대시보드",
    page_icon="🏪",
    layout="wide"
)


system_name = platform.system()

if system_name == "Windows":
    plt.rcParams["font.family"] = "Malgun Gothic"

elif system_name == "Darwin":
    plt.rcParams["font.family"] = "AppleGothic"

else:
    plt.rcParams["font.family"] = "NanumGothic"

plt.rcParams["axes.unicode_minus"] = False


# ============================================================
# 2. 경로
# ============================================================

OUTPUT_DIR = Path("output")
DATA_DIR = Path("data")

GEOJSON_PATH = (
    DATA_DIR / "HangJeongDong_ver20260701.geojson"
)


# ============================================================
# 3. 데이터 불러오기
# ============================================================

@st.cache_data
def load_data():

    market = pd.read_csv(
        OUTPUT_DIR / "market_summary.csv"
    )

    analysis = pd.read_csv(
        OUTPUT_DIR / "final_analysis_dataset.csv"
    )

    candidate = pd.read_csv(
        OUTPUT_DIR / "startup_candidates.csv"
    )

    # --------------------------------------------------------
    # 수치형 컬럼 변환
    # --------------------------------------------------------

    num_cols = [
        "2023",
        "2024",
        "2025",
        "3년_증감",
        "총_상주인구_수",
        "총_직장_인구_수",
        "총_유동인구_수",
        "1인_가구_수",
        "1인_가구_비중",
        "직장인구_상주인구_비",
        "유동인구_상주인구_비",
        "학원_매출",
        "학원_매출_비중",
        "활동인구",
        "활동인구_대비_편의점",
        "후보점수"
    ]

    for col in num_cols:

        if col in analysis.columns:

            analysis[col] = pd.to_numeric(
                analysis[col],
                errors="coerce"
            )

        if col in candidate.columns:

            candidate[col] = pd.to_numeric(
                candidate[col],
                errors="coerce"
            )

    # --------------------------------------------------------
    # 경쟁 수준 컬럼 보완
    # --------------------------------------------------------

    if (
        "경쟁수준" in analysis.columns
        and
        "경쟁수준_1차" not in analysis.columns
    ):

        analysis["경쟁수준_1차"] = (
            analysis["경쟁수준"]
        )

    # --------------------------------------------------------
    # 자치구명 보완
    # --------------------------------------------------------

    for df in [analysis, candidate]:

        if (
            "자치구_명" not in df.columns
            and
            "지역명" in df.columns
        ):

            df["자치구_명"] = (
                df["지역명"]
                .astype(str)
                .str.split()
                .str[0]
            )

    return market, analysis, candidate


# ============================================================
# 4. 지도 데이터 불러오기
# ============================================================

@st.cache_data
def load_map():

    geo = gpd.read_file(
        GEOJSON_PATH
    )

    # 서울시 행정동만 추출

    geo = geo[
        geo["adm_nm"]
        .astype(str)
        .str.startswith("서울특별시")
    ].copy()

    # 지도용 지역명 정리

    geo["지역명_지도용"] = (
        geo["adm_nm"]
        .astype(str)
        .str.replace(
            "서울특별시 ",
            "",
            regex=False
        )
        .str.replace(
            "·",
            ".",
            regex=False
        )
        .str.replace(
            "ㆍ",
            ".",
            regex=False
        )
        .str.replace(
            "‧",
            ".",
            regex=False
        )
        .str.replace(
            "･",
            ".",
            regex=False
        )
        .str.strip()
    )

    return geo


# ============================================================
# 5. 데이터 로드
# ============================================================

try:

    market, analysis, candidate = load_data()

except Exception as e:

    st.error(
        f"⚠️ 데이터 파일 로드 중 오류가 발생했습니다.\n\n{e}"
    )

    st.stop()


try:

    geo = load_map()

except Exception as e:

    geo = None

    st.warning(
        f"⚠️ 지도 데이터를 불러오지 못했습니다.\n\n{e}"
    )


# ============================================================
# 6. 대시보드 제목
# ============================================================

st.title(
    "🏪 서울시 편의점 상권 분석 대시보드"
)

st.caption(
    "서울시 행정동별 편의점 분포와 상권 특성을 바탕으로 "
    "최적의 출점 우수 후보지를 스크리닝합니다."
)

st.write(" ")


# ============================================================
# 7. 서울시 편의점 시장 핵심 지표
# ============================================================

st.markdown(
    "### 📊 서울시 편의점 시장 핵심 지표"
)

st.write(" ")


# ------------------------------------------------------------
# KPI 계산
# ------------------------------------------------------------

total_stores = (
    analysis["2025"].sum()
)

total_change = (
    analysis["3년_증감"].sum()
)

top_row = (
    analysis
    .sort_values(
        "2025",
        ascending=False
    )
    .iloc[0]
)

avg_store = (
    analysis["2025"].mean()
)


# ------------------------------------------------------------
# KPI 4개
# ------------------------------------------------------------

k1, k2, k3, k4 = st.columns(4)


with k1:

    st.metric(
        "🏛️ 서울시 총 편의점 수 (2025)",
        f"{total_stores:,.0f}개"
    )


with k2:

    st.metric(
        "📉 3개년 서울시 점포 순증감",
        f"{total_change:+,.0f}개"
    )


with k3:

    st.metric(
        "🔥 편의점 최다 행정동",
        top_row["지역명"],
        delta=f"{int(top_row['2025'])}개 점포"
    )


with k4:

    st.metric(
        "📍 행정동당 평균 점포수",
        f"{avg_store:.1f}개"
    )


st.write(" ")

st.markdown("---")


# ============================================================
# 8. 사이드바
# ============================================================

st.sidebar.header(
    "🎛️ 상권 분석 필터"
)


# ------------------------------------------------------------
# 자치구 선택
# ------------------------------------------------------------

gu_list = sorted(
    analysis["자치구_명"]
    .dropna()
    .unique()
)


selected_gu = st.sidebar.multiselect(
    "자치구 선택",

    options=gu_list,

    help=(
        "분석할 자치구를 선택합니다.\n\n"
        "선택하지 않으면 서울시 전체를 대상으로 합니다."
    )
)


# ------------------------------------------------------------
# 행정동 선택
# ------------------------------------------------------------

dong_source = analysis.copy()


if selected_gu:

    dong_source = dong_source[
        dong_source["자치구_명"]
        .isin(selected_gu)
    ]


dong_list = sorted(
    dong_source["지역명"]
    .dropna()
    .unique()
)


selected_dong = st.sidebar.selectbox(
    "📍 행정동 선택",

    options=[
        "전체 행정동"
    ] + dong_list,

    help=(
        "특정 행정동을 선택하면 지도에서 해당 지역이 "
        "진한 파란색으로 강조됩니다.\n\n"
        "선택한 행정동의 주요 상권 지표도 함께 확인할 수 있습니다."
    )
)


# ------------------------------------------------------------
# 상권 특성
# ------------------------------------------------------------

zone_list = sorted(
    analysis["상권특성"]
    .dropna()
    .unique()
)


selected_zone = st.sidebar.multiselect(
    "🏙️ 상권 특성",

    options=zone_list,

    help=(
        "행정동별 인구 및 활동 특성을 기준으로 분류한 "
        "상권 유형입니다.\n\n"
        "원하는 상권 유형만 선택하여 비교할 수 있습니다."
    )
)


# ------------------------------------------------------------
# 경쟁 수준
# ------------------------------------------------------------

comp_col = (
    "경쟁수준_1차"
    if "경쟁수준_1차" in analysis.columns
    else "경쟁수준"
)


if comp_col in analysis.columns:

    comp_list = sorted(
        analysis[comp_col]
        .dropna()
        .unique()
    )

else:

    comp_list = []


selected_competition = st.sidebar.multiselect(
    "⚔️ 경쟁 수준",

    options=comp_list,

    help=(
        "행정동별 편의점 경쟁 정도를 나타내는 "
        "분류 결과입니다.\n\n"
        "특정 경쟁 수준의 지역만 선택하여 확인할 수 있습니다."
    )
)


st.sidebar.markdown("---")


# ============================================================
# 최소 활동인구
# ============================================================

if "활동인구" in analysis.columns:

    activity_max = int(
        analysis["활동인구"].max()
    )

    min_activity = st.sidebar.slider(
        "👥 최소 활동인구",

        min_value=0,

        max_value=activity_max,

        value=0,

        step=1000,

        help=(
            "잠재적인 소비 수요 규모를 확인하기 위한 필터입니다.\n\n"
            "설정한 값보다 활동인구가 적은 행정동은 "
            "분석 대상에서 제외합니다.\n\n"
            "값을 높이면 활동인구가 많은 지역을 중심으로 "
            "출점 후보지를 좁혀볼 수 있습니다."
        )
    )

else:

    min_activity = 0


st.sidebar.markdown("---")


# ============================================================
# 창업 후보지 최소 점수
# ============================================================

st.sidebar.markdown(
    "### 🎯 창업 후보지 최소 점수"
)

st.sidebar.caption(
    "출점 검토 조건을 얼마나 많이 만족했는지 보여주는 점수입니다."
)


score_options = {
    "0점 — 조건 0개 만족": 0,
    "1점 — 조건 1개 만족": 1,
    "2점 — 조건 2개 만족": 2,
    "3점 — 조건 3개 만족": 3
}


selected_score_label = st.sidebar.radio(
    "최소 기준",

    options=list(
        score_options.keys()
    ),

    index=2,

    help=(
        "후보점수는 3개의 출점 검토 조건으로 구성됩니다.\n\n"
        "① 점포 밀도·경쟁 여건\n"
        "② 최근 3년 점포 변화\n"
        "③ 활동인구 수요\n\n"
        "각 조건을 만족하면 1점씩 부여합니다."
    )
)


min_score = score_options[
    selected_score_label
]


# ============================================================
# 9. 필터 적용
# ============================================================

filtered = analysis.copy()


if selected_gu:

    filtered = filtered[
        filtered["자치구_명"]
        .isin(selected_gu)
    ]


if selected_zone:

    filtered = filtered[
        filtered["상권특성"]
        .isin(selected_zone)
    ]


if selected_competition:

    filtered = filtered[
        filtered[comp_col]
        .isin(selected_competition)
    ]


if selected_dong != "전체 행정동":

    filtered = filtered[
        filtered["지역명"]
        == selected_dong
    ]


if "활동인구" in filtered.columns:

    filtered = filtered[
        filtered["활동인구"]
        >= min_activity
    ]


# ============================================================
# 10. 현재 선택 조건 현황
# ============================================================

st.subheader(
    "📌 현재 선택 조건 현황"
)

st.write(" ")


f1, f2, f3, f4 = st.columns(4)


f1.metric(
    "분석 대상 행정동",
    f"{len(filtered):,}개"
)


f2.metric(
    "2025년 편의점",
    f"{filtered['2025'].sum():,.0f}개"
)


if len(filtered) > 0:

    f3.metric(
        "행정동당 평균 편의점",
        f"{filtered['2025'].mean():.1f}개"
    )

else:

    f3.metric(
        "행정동당 평균 편의점",
        "-"
    )


if (
    len(filtered) > 0
    and
    "활동인구" in filtered.columns
):

    f4.metric(
        "평균 활동인구",
        f"{filtered['활동인구'].mean():,.0f}명"
    )

else:

    f4.metric(
        "평균 활동인구",
        "-"
    )


st.markdown("---")


# ============================================================
# 11. 지도 + 행정동 상세정보
# ============================================================

st.subheader(
    "🗺️ 행정동별 편의점 분포"
)

st.caption(
    "전체 조회 시 편의점이 많은 지역일수록 진한 파란색으로 "
    "표시됩니다. 행정동을 선택하면 해당 지역이 진한 파란색으로 "
    "강조됩니다."
)

st.write(" ")


map_col, info_col = st.columns(
    [1.15, 0.85]
)


# ============================================================
# 11-1. 지도
# ============================================================

with map_col:

    if geo is not None:

        map_data = (
            analysis[
                [
                    "지역명",
                    "2025"
                ]
            ]
            .drop_duplicates()
            .copy()
        )


        map_data["2025"] = pd.to_numeric(
            map_data["2025"],
            errors="coerce"
        )


        map_data["지역명_지도용"] = (
            map_data["지역명"]
            .astype(str)
            .str.strip()
            .str.replace(
                "·",
                ".",
                regex=False
            )
            .str.replace(
                "ㆍ",
                ".",
                regex=False
            )
            .str.replace(
                "‧",
                ".",
                regex=False
            )
            .str.replace(
                "･",
                ".",
                regex=False
            )
        )


        geo_map = geo.merge(
            map_data[
                [
                    "지역명_지도용",
                    "2025"
                ]
            ],
            on="지역명_지도용",
            how="left"
        )


        fig, ax = plt.subplots(
            figsize=(6, 5)
        )


        # ----------------------------------------------------
        # 전체 조회
        # ----------------------------------------------------

        if selected_dong == "전체 행정동":

            geo_map.plot(
                column="2025",

                cmap="Blues",

                linewidth=0.8,

                edgecolor="#888888",

                ax=ax,

                legend=False,

                missing_kwds={
                    "color": "#EEEEEE",
                    "edgecolor": "#888888"
                }
            )


        # ----------------------------------------------------
        # 행정동 선택
        # ----------------------------------------------------

        else:

            geo_map.plot(
                ax=ax,

                color="#EEEEEE",

                edgecolor="#999999",

                linewidth=0.8
            )


            selected_area = geo_map[
                geo_map["지역명_지도용"]
                == selected_dong
            ]


            selected_area.plot(
                ax=ax,

                color="#2F3C7E",

                edgecolor="white",

                linewidth=1.5
            )


        # ----------------------------------------------------
        # 지도 범위
        # ----------------------------------------------------

        minx, miny, maxx, maxy = (
            geo_map.total_bounds
        )


        margin_x = (
            maxx - minx
        ) * 0.03


        margin_y = (
            maxy - miny
        ) * 0.03


        ax.set_xlim(
            minx - margin_x,
            maxx + margin_x
        )


        ax.set_ylim(
            miny - margin_y,
            maxy + margin_y
        )


        # ----------------------------------------------------
        # 지도 외곽선 제거
        # ----------------------------------------------------

        ax.set_axis_off()

        ax.set_xticks([])
        ax.set_yticks([])

        ax.set_frame_on(False)


        for spine in ax.spines.values():

            spine.set_visible(False)


        plt.tight_layout()


        st.pyplot(
            fig,
            use_container_width=True
        )


        plt.close(fig)


    else:

        st.warning(
            "⚠️ 지도 데이터를 불러오지 못했습니다."
        )


# ============================================================
# 11-2. 선택 행정동 상세정보
# ============================================================

with info_col:

    if selected_dong != "전체 행정동":

        selected_info = analysis[
            analysis["지역명"]
            == selected_dong
        ]


        if len(selected_info) > 0:

            row = selected_info.iloc[0]


            st.markdown(
                f"### 📍 {selected_dong}"
            )


            st.write(" ")


            st.markdown(
                "##### 핵심 지표"
            )


            st.metric(
                "🏪 2025년 편의점",
                f"{int(row['2025']):,}개"
            )


            if (
                "활동인구" in row.index
                and
                pd.notna(row["활동인구"])
            ):

                st.metric(
                    "👥 활동인구",
                    f"{int(row['활동인구']):,}명"
                )


            if (
                "활동인구_대비_편의점" in row.index
                and
                pd.notna(
                    row["활동인구_대비_편의점"]
                )
            ):

                st.metric(
                    "📊 활동인구 대비 편의점",
                    f"{row['활동인구_대비_편의점']:.2f}"
                )


            st.markdown("---")


            st.markdown(
                "##### 상권 특성 보조지표"
            )


            if (
                "상권특성" in row.index
                and
                pd.notna(row["상권특성"])
            ):

                st.markdown(
                    f"**🏙️ 상권 특성**  \n"
                    f"{row['상권특성']}"
                )


            if (
                "1인_가구_비중" in row.index
                and
                pd.notna(row["1인_가구_비중"])
            ):

                st.markdown(
                    f"**👤 1인 가구 비중**  \n"
                    f"{row['1인_가구_비중']:.1f}%"
                )


            if (
                "직장인구_상주인구_비" in row.index
                and
                pd.notna(
                    row["직장인구_상주인구_비"]
                )
            ):

                st.markdown(
                    f"**💼 직장인구 / 상주인구**  \n"
                    f"{row['직장인구_상주인구_비']:.2f}"
                )


            if (
                "유동인구_상주인구_비" in row.index
                and
                pd.notna(
                    row["유동인구_상주인구_비"]
                )
            ):

                st.markdown(
                    f"**🚶 유동인구 / 상주인구**  \n"
                    f"{row['유동인구_상주인구_비']:.2f}"
                )


            if (
                row.get("상권특성")
                == "학원·교육형"
                and
                "학원_매출" in row.index
                and
                pd.notna(row["학원_매출"])
            ):

                st.markdown(
                    f"**📚 학원 매출**  \n"
                    f"{row['학원_매출']:,.0f}"
                )


        else:

            st.info(
                "선택한 행정동의 상세 데이터가 없습니다."
            )


    else:

        st.markdown(
            "### 📍 행정동을 선택하세요"
        )

        st.write(" ")

        st.caption(
            "사이드바에서 행정동을 선택하면 "
            "지도에서 해당 지역이 강조되고 "
            "핵심 상권 정보를 확인할 수 있습니다."
        )


st.markdown("---")


# ============================================================
# 12. 상권 특성 및 경쟁 수준 현황
# ============================================================

st.subheader(
    "🏙️ 상권 특성 및 경쟁 수준 현황"
)

st.write(" ")


col_left, col_right = st.columns(
    [1, 1]
)


# ------------------------------------------------------------
# 상권 특성별 현황
# ------------------------------------------------------------

with col_left:

    st.markdown(
        "##### 📋 상권 특성별 현황"
    )


    if len(filtered) > 0:

        zone_sum = (
            filtered
            .groupby(
                "상권특성",
                as_index=False
            )
            .agg(
                지역수=(
                    "지역명",
                    "count"
                ),

                편의점수=(
                    "2025",
                    "sum"
                ),

                평균편의점수=(
                    "2025",
                    "mean"
                )
            )
            .sort_values(
                "편의점수",
                ascending=False
            )
        )


        st.dataframe(
            zone_sum,

            use_container_width=True,

            hide_index=True,

            height=280
        )


    else:

        st.info(
            "조건을 만족하는 지역이 없습니다."
        )


# ------------------------------------------------------------
# 경쟁 수준별 현황
# ------------------------------------------------------------

with col_right:

    st.markdown(
        "##### ⚔️ 경쟁 수준별 현황"
    )


    if len(filtered) > 0:

        comp_sum = (
            filtered
            .groupby(
                comp_col,
                as_index=False
            )
            .agg(
                지역수=(
                    "지역명",
                    "count"
                ),

                편의점수=(
                    "2025",
                    "sum"
                ),

                평균편의점수=(
                    "2025",
                    "mean"
                )
            )
        )


        st.dataframe(
            comp_sum,

            use_container_width=True,

            hide_index=True,

            height=280
        )


    else:

        st.info(
            "조건을 만족하는 지역이 없습니다."
        )


st.markdown("---")


# ============================================================
# 13. 창업 우수 후보지
# ============================================================

st.subheader(
    "🎯 창업 우수 후보지"
)

st.caption(
    "활동인구 수요와 편의점 경쟁 및 최근 점포 변화 등을 "
    "종합하여 우선 검토할 지역을 보여줍니다."
)

st.write(" ")


cand_df = candidate.copy()


# ------------------------------------------------------------
# 자치구 필터
# ------------------------------------------------------------

if selected_gu:

    cand_df = cand_df[
        cand_df["자치구_명"]
        .isin(selected_gu)
    ]


# ------------------------------------------------------------
# 상권 특성 필터
# ------------------------------------------------------------

if selected_zone:

    cand_df = cand_df[
        cand_df["상권특성"]
        .isin(selected_zone)
    ]


# ------------------------------------------------------------
# 최소 활동인구
# ------------------------------------------------------------

if "활동인구" in cand_df.columns:

    cand_df = cand_df[
        cand_df["활동인구"]
        >= min_activity
    ]


# ------------------------------------------------------------
# 최소 후보점수
# ------------------------------------------------------------

if "후보점수" in cand_df.columns:

    cand_df = cand_df[
        cand_df["후보점수"]
        >= min_score
    ]


# ------------------------------------------------------------
# 후보지 표시 컬럼
# ------------------------------------------------------------

cand_cols = [
    "지역명",
    "상권특성",
    "2023",
    "2025",
    "3년_증감",
    "총_상주인구_수",
    "총_직장_인구_수",
    "총_유동인구_수",
    "활동인구",
    "활동인구_대비_편의점",
    "후보점수"
]


valid_cand_cols = [
    col
    for col in cand_cols
    if col in cand_df.columns
]


if len(cand_df) > 0:

    cand_table = (
        cand_df[
            valid_cand_cols
        ]
        .sort_values(
            [
                "후보점수",
                "활동인구"
            ],
            ascending=[
                False,
                False
            ]
        )
    )


    st.dataframe(
        cand_table,

        use_container_width=True,

        hide_index=True,

        height=350
    )


else:

    st.warning(
        "⚠️ 현재 조건을 만족하는 창업 후보지역이 없습니다."
    )


# ------------------------------------------------------------
# 후보점수 설명
# ------------------------------------------------------------

st.info(
    "💡 **후보점수란?** "
    "점포 밀도·경쟁 여건, 최근 3년간 점포 변화, "
    "활동인구 수요를 종합해 출점 후보지를 평가한 "
    "3점 만점의 1차 스크리닝 점수입니다. "
    "각 조건을 만족하면 1점씩 부여합니다."
)


st.markdown("---")


# ============================================================
# 14. 상권 분석 요약 리포트
# ============================================================

st.subheader(
    "📄 상권 분석 요약 리포트"
)

st.caption(
    "현재 설정된 사이드바 필터 조건을 기반으로 "
    "분석 결과를 요약합니다."
)


if st.button(
    "📑 상권 분석 리포트 생성하기",
    type="primary"
):

    if len(cand_df) > 0:

        cand_table = (
            cand_df[
                valid_cand_cols
            ]
            .sort_values(
                [
                    "후보점수",
                    "활동인구"
                ],
                ascending=[
                    False,
                    False
                ]
            )
        )


        top_cand_name = (
            cand_table.iloc[0]["지역명"]
        )


        top_cand_score = (
            cand_table.iloc[0]["후보점수"]
        )


    else:

        top_cand_name = "없음"

        top_cand_score = 0


    report_text = f"""
=======================================================
[ 서울시 편의점 상권 분석 요약 보고서 ]
=======================================================

1. 분석 조건

- 선택 자치구:
  {', '.join(selected_gu) if selected_gu else '서울시 전체'}

- 선택 행정동:
  {selected_dong}

- 선택 상권 특성:
  {', '.join(selected_zone) if selected_zone else '전체'}

- 최소 활동인구:
  {min_activity:,.0f}명 이상

- 최소 후보점수:
  {min_score}점


2. 서울시 편의점 현황

- 2025년 총 편의점:
  {total_stores:,.0f}개

- 3개년 순증감:
  {total_change:+,.0f}개


3. 분석 대상

- 조건을 만족하는 행정동:
  {len(filtered)}개

- 조건을 만족하는 창업 후보지:
  {len(cand_df)}개


4. 최우선 후보지

- 지역:
  {top_cand_name}

- 후보점수:
  {top_cand_score}점


5. 분석 해석

활동인구를 기반으로 기본 수요 규모를 확인하고,
편의점 분포와 상권 특성 및 경쟁 수준을 종합하여
출점 후보지역을 1차적으로 스크리닝하였습니다.

※ 본 결과는 행정동 단위 공공데이터를 기반으로 한
1차 분석이며, 실제 출점 의사결정에는 점포 주변
유동동선, 경쟁점포 위치, 임대료, 가시성 등
현장조사가 추가로 필요합니다.

=======================================================
"""


    st.success(
        "✅ 리포트가 생성되었습니다."
    )


    st.code(
        report_text,
        language="text"
    )


    st.download_button(
        label="📥 리포트 파일(.txt) 다운로드",

        data=report_text,

        file_name="commercial_area_report.txt",

        mime="text/plain"
    )


# ============================================================
# 15. 하단 안내
# ============================================================

st.caption(
    "※ 본 대시보드는 행정동 단위 공공데이터를 기반으로 한 "
    "1차 스크리닝 결과이며, 실제 출점 시에는 현장조사 및 "
    "입지 분석이 병행되어야 합니다."
)