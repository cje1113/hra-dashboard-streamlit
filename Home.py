# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

st.set_page_config(
    page_title="HRA Dashboard — Home",
    page_icon="🏠",
    layout="wide",          # 전체 화면 꽉 채우기
    initial_sidebar_state="expanded",
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


def parse_label(df):
    df = df.copy()

    if "region" not in df.columns:
        r_col = next((c for c in df.columns if "region" in c.lower() or c=="지역"), None)
        if r_col:
            df = df.rename(columns={r_col:"region"})

    if "year_month" in df.columns:
        df["year_month"] = pd.to_datetime(df["year_month"], format="%Y_%m")
        df["year_month"] = df["year_month"].dt.to_period("M").dt.to_timestamp()

    if "risk_level" in df.columns:
        df["risk_name"] = df["risk_level"].astype(str).str.title()
    else:
        df["risk_name"] = "Medium"

    df = df.dropna(subset=["region", "year_month"])
    return df


def parse_pair(df):
    df = df.copy()

    if "region" not in df.columns:
        r_col = next((c for c in df.columns if "region" in c.lower() or c=="지역"), None)
        if r_col:
            df = df.rename(columns={r_col:"region"})

    if "year_month" in df.columns:
        df["year_month"] = pd.to_datetime(df["year_month"], format="%Y_%m")
        df["year_month"] = df["year_month"].dt.to_period("M").dt.to_timestamp()

    # stressor rename
    s_col = next((c for c in df.columns if "stress" in c.lower()), None)
    if s_col:
        df = df.rename(columns={s_col:"stressor"})

    # risk numeric
    r_col = next((c for c in df.columns if c.lower() in ("r","risk")), None)
    if r_col:
        df = df.rename(columns={r_col:"R"})

    return df


df_label = parse_label(load_csv(DATA_LABEL))
df_pair  = parse_pair(load_csv(DATA_PAIR))


# ========= UI =========
st.title("🌊 해양 생물다양성 리스크 대시보드")

# 월 선택
years = sorted(df_label["year_month"].dt.year.unique())
colY, colM = st.columns(2)
yr = colY.selectbox("연도 선택", years)
months = sorted(df_label.loc[df_label["year_month"].dt.year == yr, "year_month"].dt.month.unique())
mo = colM.selectbox("월 선택", months)

sel_ts = pd.Timestamp(f"{yr}-{mo:02d}-01")
df_m = df_label[df_label["year_month"] == sel_ts].copy()

# ======== y축을 지역으로 바꾼 막대그래프 ========
st.subheader("해당 월 위험도 (지역 기준)")

ORDER = ["Low","Medium","High"]
COLOR = {"Low":"#4CAF50","Medium":"#FFC107","High":"#F44336"}

df_bar = df_m[["region", "risk_name"]].copy()

fig = px.histogram(
    df_bar,
    y="region",               # 요구사항: y축=지역
    color="risk_name",
    color_discrete_map=COLOR,
    category_orders={"risk_name": ORDER},
    title="지역별 위험도 분포"
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# High 지역 Top-1 stressor
st.subheader("🔎 High 지역 Top-1 Stressor")

high_regions = df_m.loc[df_m["risk_name"]=="High", "region"].unique().tolist()
if not high_regions:
    st.info("High 지역이 없습니다.")
else:
    dfx = df_pair[(df_pair["year_month"]==sel_ts) & (df_pair["region"].isin(high_regions))]
    if dfx.empty:
        st.info("해당 월 pairwise 정보 없음")
    else:
        g = dfx.groupby(["region","stressor"], as_index=False)["R"].mean()
        top1 = g.sort_values(["region","R"], ascending=[True,False]).groupby("region").head(1)
        st.dataframe(top1, use_container_width=True)