# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

st.set_page_config(
    page_title="HRA Dashboard — Data",
    page_icon="📦",
    layout="wide"
)

with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


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
    df = df.copy()

    if "region" not in df.columns:
        r_col = next((c for c in df.columns if "region" in c.lower() or c=="지역"), None)
        if r_col:
            df = df.rename(columns={r_col:"region"})

    if "year_month" in df.columns:
        df["year_month"] = pd.to_datetime(df["year_month"], format="%Y_%m")
        df["year_month"] = df["year_month"].dt.to_period("M").dt.to_timestamp()

    return df


df_l = parse_df(load_csv(DATA_LABEL))
df_p = parse_df(load_csv(DATA_PAIR))


# UI
st.title("📦 Dataset Overview")

tab2, tab3 = st.tabs(["⚠️ risk_total", "⚠️ risk_stress"])


# ===== risk_total =====
with tab2:
    st.subheader("risk_total")

    st.dataframe(df_l.head(30), use_container_width=True)

    ORDER = ["Low","Medium","High"]
    COLOR = {"Low":"#4CAF50","Medium":"#FFC107","High":"#F44336"}

    df_l["risk_name"] = df_l["risk_level"].astype(str).str.title()

    dist = (df_l["risk_name"].value_counts()
            .reindex(ORDER)
            .rename_axis("risk_name")
            .reset_index(name="count"))

    fig = px.bar(
        dist, x="risk_name", y="count",
        color="risk_name",
        color_discrete_map=COLOR
    )
    st.plotly_chart(fig, use_container_width=True)


# ===== risk_stress =====
with tab3:
    st.subheader("risk_stress")

    st.dataframe(df_p.head(30), use_container_width=True)

    s_col = next((c for c in df_p.columns if "stress" in c.lower()), None)
    r_col = next((c for c in df_p.columns if c.lower() in ("r","risk")), None)

    if s_col and r_col:
        regs = sorted(df_p["region"].unique())
        sel = st.multiselect("지역 선택", regs, default=regs[:3])

        dfx = df_p[df_p["region"].isin(sel)]
        g = dfx.groupby(["region", s_col], as_index=False)[r_col].mean()
        g = g.rename(columns={s_col:"stressor", r_col:"R_value"})

        fig = px.bar(
            g, x="stressor", y="R_value",
            color="region",
            title="지역별 Stressor 평균 R"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("컬럼 구조가 맞지 않습니다.")