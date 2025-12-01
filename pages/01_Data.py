# -*- coding: utf-8 -*-
# 01_Data.py — Notion Style EDA + Plotly

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="HRA Dashboard — Data",
    page_icon="📦",
    layout="centered",
)

with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# =========================
# 데이터 로더
# =========================
DATA_RREAL = "data/rrreal_final_ALL_predicted.csv"
DATA_LABEL = "data/hra_label_total_2025_2028.csv"
DATA_PAIR  = "data/hra_pairwise_2025_2028.csv"


@st.cache_data
def load_csv(path):
    for enc in ("utf-8-sig","utf-8","cp949"):
        try:
            return pd.read_csv(path, encoding=enc)
        except:
            pass
    return pd.read_csv(path)


def parse_df(df):
    # region
    r_like = [c for c in df.columns if "region" in c.lower() or c=="지역"]
    if r_like:
        df = df.rename(columns={r_like[0]:"region"})
    # ym
    ym_col = next((c for c in df.columns if "year" in c.lower() or "ym" in c.lower() or c=="월"), None)
    if ym_col:
        ym = pd.to_datetime(df[ym_col], errors="coerce", infer_datetime_format=True)
        df["year_month"] = pd.to_datetime(df["year_month"], format="%Y_%m")
    return df


df_r = parse_df(load_csv(DATA_RREAL)).dropna(subset=["region","year_month"])
df_l = parse_df(load_csv(DATA_LABEL))
df_p = parse_df(load_csv(DATA_PAIR))


# =========================
# UI
# =========================
st.title("📦 Dataset Overview")

with st.container():
    st.markdown('<div class="block-section">', unsafe_allow_html=True)
    st.markdown("통합 데이터 / 위험도 레이블 / 스트레스 pairwise 데이터를 확인할 수 있습니다.")
    st.markdown("</div>", unsafe_allow_html=True)


# =========================
# Tabs
# =========================
tab1, tab2, tab3 = st.tabs(["🔗 Integrated Data", "⚠️ risk_total", "⚠️ risk_stress"])


# =========================
# Integrated Data
# =========================
with tab1:
    st.subheader("Integrated Data")

    with st.expander("원자료 미리보기"):
        n = st.slider("표시 행 수", 5, 50, 10, key="n_r")
        st.dataframe(df_r.head(n), use_container_width=True)

    numeric = [c for c in df_r.columns if pd.api.types.is_numeric_dtype(df_r[c])]
    regions = sorted(df_r["region"].unique())

    colA, colB = st.columns(2)
    var = colA.selectbox("변수 선택", numeric)
    sel_regions = colB.multiselect("지역 선택", regions, default=regions[:3])

    df_f = df_r[df_r["region"].isin(sel_regions)].copy()
    df_g = df_f.groupby(["region","year_month"], as_index=False)[var].mean()

    fig = px.line(
        df_g, x="year_month", y=var, color="region",
        title=f"{var} — 월별 평균",
    )
    st.plotly_chart(fig, use_container_width=True)


# =========================
# risk_total
# =========================
with tab2:
    st.subheader("risk_total")

    with st.expander("원자료 미리보기"):
        n = st.slider("행 수", 5, 50, 10, key="n_l")
        st.dataframe(df_l.head(n), use_container_width=True)

    if "risk_level" in df_l.columns:
        df_l["risk_name"] = df_l["risk_level"].astype(str).str.title()
    else:
        df_l["risk_name"] = "Medium"

    ORDER = ["Low","Medium","High"]
    COLOR = {"Low":"#4CAF50","Medium":"#FFC107","High":"#F44336"}

    dist = (df_l["risk_name"].value_counts()
            .reindex(ORDER)
            .rename_axis("risk_name")
            .reset_index(name="count"))

    fig = px.bar(
        dist, x="risk_name", y="count",
        color="risk_name",
        color_discrete_map=COLOR,
        title="전체 위험도 건수"
    )
    st.plotly_chart(fig, use_container_width=True)


# =========================
# risk_stress
# =========================
with tab3:
    st.subheader("risk_stress")

    with st.expander("원자료 미리보기"):
        n = st.slider("행 수", 5, 50, 10, key="n_p")
        st.dataframe(df_p.head(n), use_container_width=True)

    s_col = next((c for c in df_p.columns if "stress" in c.lower()), None)
    r_col = next((c for c in df_p.columns if c.lower() in ("r","risk")), None)

    if s_col and r_col:
        regions = sorted(df_p["region"].unique())
        sel_r = st.multiselect("지역 선택", regions, default=regions[:3])

        df_f = df_p[df_p["region"].isin(sel_r)].copy()
        df_g = df_f.groupby(["region",s_col], as_index=False)[r_col].mean()
        df_g = df_g.rename(columns={s_col:"stressor", r_col:"R_value"})

        fig = px.bar(
            df_g, x="stressor", y="R_value",
            color="region",
            title="지역별 Stressor 평균 R"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("필수 컬럼(stressor/R)이 없어 분석 불가")