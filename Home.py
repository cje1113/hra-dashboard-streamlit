# -*- coding: utf-8 -*-
# Home.py — Notion Style Dashboard (FULL WIDTH)

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

st.set_page_config(
    page_title="HRA Dashboard",
    page_icon="🏠",
    layout="wide",
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
    # region
    r_like = [c for c in df.columns if "region" in c.lower()]
    if r_like:
        df = df.rename(columns={r_like[0]:"region"})

    # year_month
    ym_col = next((c for c in df.columns if "year" in c.lower() or "ym" in c.lower()), None)
    if ym_col:
        df["year_month"] = pd.to_datetime(df[ym_col], format="%Y_%m", errors="coerce")

    return df.dropna(subset=["region","year_month"]).copy()

df_label = parse_df(load_csv(DATA_LABEL))
df_pair  = parse_df(load_csv(DATA_PAIR))

# =========================
# UI
# =========================
st.title("🌊 해양 생물다양성 리스크 대시보드")
st.caption("전국 해양 위험도를 시계열 기반으로 분석합니다.")

regions = sorted(df_label["region"].unique())
first_dt = df_label["year_month"].min()
last_dt  = df_label["year_month"].max()

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("지역 수", len(regions))
with c2:
    st.metric("전체 레코드", len(df_label))
with c3:
    st.metric("기간 시작", first_dt.strftime("%Y-%m"))
with c4:
    st.metric("기간 종료", last_dt.strftime("%Y-%m"))

st.divider()

# =========================
# 연/월 선택
# =========================
years = sorted(df_label["year_month"].dt.year.unique())
colY, colM = st.columns(2)
yr = colY.selectbox("연도", years, key="home_year")
months = sorted(df_label[df_label["year_month"].dt.year==yr]["year_month"].dt.month.unique())
mo = colM.selectbox("월", months, key="home_month")

sel_ts = pd.Timestamp(f"{yr}-{mo:02d}-01")
df_m = df_label[df_label["year_month"] == sel_ts]

# =========================
# 위험 분포
# =========================
ORDER = ["Low","Medium","High"]
COLOR = {"Low":"#4CAF50","Medium":"#FFC107","High":"#F44336"}

df_m["risk_name"] = df_m["risk_level"].astype(str).str.title()

dist = df_m["risk_name"].value_counts().reindex(ORDER).reset_index()
dist.columns = ["risk_name","count"]

fig = px.bar(
    dist, x="risk_name", y="count",
    color="risk_name", color_discrete_map=COLOR,
    title="해당 월 위험도 분포"
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# =========================
# HIGH 지역 Top-1 Stressor
# =========================
st.subheader("🔎 High 지역 Top-1 Stressor")

high_regions = df_m[df_m["risk_name"]=="High"]["region"].unique().tolist()

if not high_regions:
    st.info("High 지역 없음")
else:
    dfx = df_pair[(df_pair["year_month"]==sel_ts) & (df_pair["region"].isin(high_regions))]
    if dfx.empty:
        st.info("pairwise 데이터 없음")
    else:
        g = dfx.groupby(["region","stressor"], as_index=False)["R"].mean()
        top1 = g.sort_values(["region","R"], ascending=[True,False]).groupby("region").head(1)
        st.dataframe(top1, use_container_width=True)
