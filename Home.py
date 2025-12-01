# -*- coding: utf-8 -*-
# Home.py — Notion Style Dashboard (Centered Layout)

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
from pathlib import Path

# =========================
# 페이지 설정
# =========================
st.set_page_config(
    page_title="HRA Dashboard — Home",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="expanded",
)

# CSS 로드
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# =========================
# 데이터 로더
# =========================
DATA_LABEL = "data/hra_label_total_2025_2028.csv"
DATA_PAIR  = "data/hra_pairwise_2025_2028.csv"

@st.cache_data
def load_csv(path):
    for enc in ("utf-8-sig", "utf-8", "cp949"):
        try:
            return pd.read_csv(path, encoding=enc)
        except:
            pass
    return pd.read_csv(path)


def load_label():
    df = load_csv(DATA_LABEL).copy()

    # region
    r_like = [c for c in df.columns if str(c).lower() in ("region","지역")]
    if r_like:
        df = df.rename(columns={r_like[0]:"region"})

    # year_month
    ym_col = next((c for c in df.columns if "year" in c.lower() or "ym" in c.lower() or "월"==c.lower()), None)
    if ym_col:
        ym = pd.to_datetime(df[ym_col], errors="coerce", infer_datetime_format=True)
        df["year_month"] = ym.dt.to_period("M").dt.to_timestamp("start")

    # risk_level
    if "risk_level" in df.columns:
        df["risk_name"] = df["risk_level"].astype(str).str.title()
    else:
        df["risk_name"] = "Medium"

    return df.dropna(subset=["region","year_month"]).copy()


def load_pair():
    df = load_csv(DATA_PAIR).copy()

    r_like = [c for c in df.columns if str(c).lower() in ("region","지역")]
    if r_like:
        df = df.rename(columns={r_like[0]:"region"})

    ym_col = next((c for c in df.columns if "year" in c.lower() or "ym" in c.lower()), None)
    if ym_col:
        ym = pd.to_datetime(df[ym_col], errors="coerce", infer_datetime_format=True)
        df["year_month"] = ym.dt.to_period("M").to_timestamp("start")

    s_col = next((c for c in df.columns if "stress" in c.lower()), None)
    if s_col:
        df = df.rename(columns={s_col:"stressor"})

    r_col = next((c for c in df.columns if c.lower() in ("r","risk")), None)
    if r_col:
        df = df.rename(columns={r_col:"R"})

    return df


df_label = load_label()
df_pair = load_pair()


# =========================
# UI
# =========================
st.title("🌊 해양 생물다양성 리스크 대시보드 (Home)")

with st.container():
    st.markdown('<div class="block-section">', unsafe_allow_html=True)
    st.markdown("최근 위험도 요약과 주요 지역 동향을 한눈에 볼 수 있습니다.")
    st.markdown("</div>", unsafe_allow_html=True)


# =========================
# KPI — Summary
# =========================
regions = sorted(df_label["region"].unique())
first_dt = df_label["year_month"].min()
last_dt = df_label["year_month"].max()

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown('<div class="kpi-card">지역 수<br><span class="kpi-value">{:,}</span></div>'.format(len(regions)),
                unsafe_allow_html=True)
with c2:
    st.markdown('<div class="kpi-card">전체 레코드<br><span class="kpi-value">{:,}</span></div>'.format(len(df_label)),
                unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="kpi-card">기간 시작<br><span class="kpi-value">{first_dt.strftime("%Y-%m")}</span></div>',
                unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="kpi-card">기간 종료<br><span class="kpi-value">{last_dt.strftime("%Y-%m")}</span></div>',
                unsafe_allow_html=True)

st.divider()


# =========================
# 월 선택
# =========================
years = sorted(df_label["year_month"].dt.year.unique())
colY, colM = st.columns(2)
yr = colY.selectbox("연도 선택", years, index=len(years)-1)
months = sorted(df_label.loc[df_label["year_month"].dt.year==yr, "year_month"].dt.month.unique())
mo = colM.selectbox("월 선택", months, index=len(months)-1)

sel_ts = pd.Timestamp(f"{yr}-{mo:02d}-01")
df_m = df_label[df_label["year_month"] == sel_ts].copy()

st.caption(f"선택 월: {yr}-{mo:02d}")


# =========================
# 위험도 분포
# =========================
ORDER = ["Low","Medium","High"]
COLOR = {"Low":"#4CAF50","Medium":"#FFC107","High":"#F44336"}

dist = (df_m["risk_name"]
        .value_counts()
        .reindex(ORDER)
        .rename_axis("risk_name")
        .reset_index(name="count"))

fig = px.bar(
    dist, x="risk_name", y="count",
    color="risk_name",
    color_discrete_map=COLOR,
    title="이번 달 위험도 분포",
)
st.plotly_chart(fig, use_container_width=True)

st.divider()


# =========================
# High Top-1 Stressor
# =========================
st.subheader("🔎 High 지역 Top-1 Stressor")

high_regions = df_m.loc[df_m["risk_name"]=="High", "region"].unique().tolist()
if not high_regions:
    st.info("High 지역이 없습니다.")
else:
    dfx = df_pair[(df_pair["year_month"]==sel_ts) & (df_pair["region"].isin(high_regions))].copy()
    if dfx.empty:
        st.info("해당 월에 대한 pairwise 정보가 없습니다.")
    else:
        g = (dfx.groupby(["region","stressor"], as_index=False)["R"]
                .mean().rename(columns={"R":"R_mean"}))
        top1 = (g.sort_values(["region","R_mean"], ascending=[True,False])
                  .groupby("region").head(1))
        top1["R_mean"] = top1["R_mean"].round(3)
        st.dataframe(top1.rename(columns={"region":"지역","stressor":"최대 R 요인","R_mean":"R 값"}),
                     use_container_width=True)
