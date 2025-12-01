# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

st.set_page_config(
    page_title="HRA Dashboard",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="expanded",
)

with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# =========================
# 데이터 로더
# =========================
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

    # year_month (문자열 그대로 '%Y_%m' 로 파싱)
    ym_col = next((c for c in df.columns if "year" in c.lower() or "ym" in c.lower()), None)
    if ym_col:
        df["year_month"] = pd.to_datetime(df[ym_col].astype(str), format="%Y_%m")
        df["year_month"] = df["year_month"].dt.to_period("M").dt.to_timestamp("start")

    return df


df_label = parse_df(load_csv(DATA_LABEL))
df_pair  = parse_df(load_csv(DATA_PAIR))


# =========================
# risk_level 표준화
# =========================
if "risk_level" in df_label.columns:
    df_label["risk_name"] = df_label["risk_level"].astype(str).str.title()
else:
    df_label["risk_name"] = "Medium"

ORDER = ["Low","Medium","High"]
COLOR = {"Low":"#4CAF50","Medium":"#FFC107","High":"#F44336"}

df_label = df_label.dropna(subset=["region","year_month"])


# =========================
# UI
# =========================
st.title("🌊 해양 생물다양성 리스크 대시보드")

regions = sorted(df_label["region"].unique())
first_dt = df_label["year_month"].min()
last_dt = df_label["year_month"].max()

c1, c2, c3, c4 = st.columns(4)
c1.write(f"지역 수: **{len(regions)}**")
c2.write(f"전체 레코드: **{len(df_label)}**")
c3.write(f"기간 시작: **{first_dt.strftime('%Y-%m')}**")
c4.write(f"기간 종료: **{last_dt.strftime('%Y-%m')}**")

st.divider()


# =========================
# 연월 선택
# =========================
years = sorted(df_label["year_month"].dt.year.unique())
colY, colM = st.columns(2)
yr = colY.selectbox("연도 선택", years, key="home_year")
months = sorted(df_label.loc[df_label["year_month"].dt.year==yr, "year_month"].dt.month.unique())
mo = colM.selectbox("월 선택", months, key="home_month")

sel_ts = pd.Timestamp(f"{yr}-{mo:02d}-01")
df_m = df_label[df_label["year_month"] == sel_ts].copy()


# =========================
# 위험도 분포
# =========================
dist = df_m["risk_name"].value_counts().reindex(ORDER).fillna(0)
dist = dist.rename_axis("risk_name").reset_index(name="count")

fig = px.bar(dist, x="risk_name", y="count",
             color="risk_name", color_discrete_map=COLOR,
             title="이번 달 위험도 분포")
st.plotly_chart(fig, use_container_width=True)

st.divider()


# =========================
# High Top-1 Stressor
# =========================
st.subheader("🔎 High 지역 Top-1 Stressor")

high_regions = df_m.loc[df_m["risk_name"]=="High", "region"].unique()

if len(high_regions)==0:
    st.info("High 지역 없음")
else:
    dfx = df_pair[(df_pair["year_month"]==sel_ts) & (df_pair["region"].isin(high_regions))]
    if dfx.empty:
        st.info("해당 월 pairwise 데이터 없음")
    else:
        g = dfx.groupby(["region","stressor"], as_index=False)["R"].mean()
        g["R"] = g["R"].round(3)
        top1 = g.sort_values(["region","R"], ascending=[True,False]).groupby("region").head(1)

        st.dataframe(top1.rename(columns={"region":"지역","stressor":"최대 요인","R":"R값"}),
                     use_container_width=True)
