# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

st.set_page_config(
    page_title="HRA Dashboard — Data",
    page_icon="📦",
    layout="centered",
)

with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

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
    r_like = [c for c in df.columns if "region" in c.lower()]
    if r_like:
        df = df.rename(columns={r_like[0]:"region"})

    ym_col = next((c for c in df.columns if "year" in c.lower() or "ym" in c.lower()), None)
    if ym_col:
        df["year_month"] = pd.to_datetime(df[ym_col].astype(str), format="%Y_%m")
        df["year_month"] = df["year_month"].dt.to_period("M").dt.to_timestamp("start")

    return df

df_r = parse_df(load_csv(DATA_RREAL)).dropna(subset=["region","year_month"])
df_l = parse_df(load_csv(DATA_LABEL))
df_p = parse_df(load_csv(DATA_PAIR))

st.title("📦 Dataset Overview")

tab1, tab2, tab3 = st.tabs(["🔗 Integrated Data", "⚠️ risk_total", "⚠️ risk_stress"])


# =========================
# Integrated Data
# =========================
with tab1:
    st.subheader("Integrated Data")
    st.dataframe(df_r.head(20), use_container_width=True)

    numeric = [c for c in df_r.columns if pd.api.types.is_numeric_dtype(df_r[c])]
    regions = sorted(df_r["region"].unique())

    colA, colB = st.columns(2)
    var = colA.selectbox("변수 선택", numeric, key="var_rreal")
    sel_regions = colB.multiselect("지역 선택", regions, default=regions[:3], key="region_rreal")

    df_f = df_r[df_r["region"].isin(sel_regions)]
    df_g = df_f.groupby(["region","year_month"], as_index=False)[var].mean()

    fig = px.line(df_g, x="year_month", y=var, color="region",
                  title=f"{var} — 월별 평균")
    st.plotly_chart(fig, use_container_width=True)


# =========================
# risk_total
# =========================
with tab2:
    st.subheader("risk_total")
    st.dataframe(df_l.head(20), use_container_width=True)

    df_l["risk_name"] = df_l["risk_level"].astype(str).str.title()

    ORDER = ["Low","Medium","High"]
    COLOR = {"Low":"#4CAF50","Medium":"#FFC107","High":"#F44336"}

    dist = df_l["risk_name"].value_counts().reindex(ORDER).fillna(0)
    dist = dist.rename_axis("risk_name").reset_index(name="count")

    fig = px.bar(dist, x="risk_name", y="count",
                 color="risk_name", color_discrete_map=COLOR)
    st.plotly_chart(fig, use_container_width=True)


# =========================
# risk_stress
# =========================
with tab3:
    st.subheader("risk_stress")
    st.dataframe(df_p.head(20), use_container_width=True)

    s_col = "stressor"
    r_col = "R"

    regions = sorted(df_p["region"].unique())
    sel_r = st.multiselect("지역 선택", regions, default=regions[:3], key="region_pair")

    df_f = df_p[df_p["region"].isin(sel_r)]
    df_g = df_f.groupby(["region", s_col], as_index=False)[r_col].mean()

    fig = px.bar(df_g, x=s_col, y=r_col, color="region",
                 title="지역별 Stressor 평균 R")
    st.plotly_chart(fig, use_container_width=True)