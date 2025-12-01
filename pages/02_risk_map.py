# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import json
import urllib.request

st.set_page_config(
    page_title="HRA — Risk Map",
    page_icon="🗺️",
    layout="centered",
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
    r_like = [c for c in df.columns if "region" in c.lower()]
    if r_like:
        df = df.rename(columns={r_like[0]:"region"})

    ym_col = next((c for c in df.columns if "year" in c.lower() or "ym" in c.lower()), None)
    if ym_col:
        df["year_month"] = pd.to_datetime(df[ym_col].astype(str), format="%Y_%m")
        df["year_month"] = df["year_month"].dt.to_period("M").dt.to_timestamp("start")

    return df


df = parse_df(load_csv(DATA_LABEL))
dfp = parse_df(load_csv(DATA_PAIR))


# 좌표
REGION_COORDS = {
    "Incheon": (37.456, 126.705),
    "Geoje": (34.880, 128.620),
    "Ulleungdo": (37.500, 130.900),
    "울릉도": (37.500, 130.900),
    "울릉":   (37.500, 130.900),
    "인천":   (37.456, 126.705),
    "거제":   (34.880, 128.620),
}

df["lat"] = df["region"].map(lambda r: REGION_COORDS.get(str(r),(np.nan,np.nan))[0])
df["lon"] = df["region"].map(lambda r: REGION_COORDS.get(str(r),(np.nan,np.nan))[1])
df = df.dropna(subset=["lat","lon"])


# risk_name
if "risk_level" in df.columns:
    df["risk_name"] = df["risk_level"].astype(str).str.title()
else:
    df["risk_name"] = "Medium"

ORDER = ["Low","Medium","High"]
COLOR = {"Low":"#4CAF50","Medium":"#FFC107","High":"#F44336"}

df["risk_name"] = pd.Categorical(df["risk_name"], categories=ORDER)


# GeoJSON
URL = "https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2013/json/skorea_provinces_geo_simple.json"
with urllib.request.urlopen(URL) as f:
    geojson = json.load(f)


st.title("🗺️ Risk Map (A 타입)")


# 필터
regions = sorted(df["region"].unique())
sel_regions = st.multiselect("지역 선택", regions, default=regions[:3], key="risk_region")

df_v = df[df["region"].isin(sel_regions)]

years = sorted(df_v["year_month"].dt.year.unique())
colY, colM = st.columns(2)

yr = colY.selectbox("연도", years, key="risk_year")
months = sorted(df_v[df_v["year_month"].dt.year==yr]["year_month"].dt.month.unique())
mo = colM.selectbox("월", months, key="risk_month")

df_m = df_v[(df_v["year_month"].dt.year==yr) & (df_v["year_month"].dt.month==mo)].copy()

df_m["ym_str"] = df_m["year_month"].dt.strftime("%Y-%m")


# Plot
fig = px.scatter_mapbox(
    df_m,
    lat="lat",
    lon="lon",
    color="risk_name",
    color_discrete_map=COLOR,
    size=df_m["R_sum"] * 50,   # 버블크기 대폭 증가
    hover_name="region",
    hover_data={"risk_name":True, "ym_str":True},
    zoom=5.4,
    center={"lat":36.2, "lon":128.0},
    height=600,
    opacity=0.85,
)

fig.update_layout(
    mapbox_style="open-street-map",
    mapbox_layers=[
        {"source": geojson, "type":"line", "color":"black", "line":{"width":1}}
    ],
    margin=dict(l=0,r=0,t=0,b=0),
)

st.plotly_chart(fig, use_container_width=True)


# High Stressor
st.subheader("🔎 High 지역 Top-1 Stressor")

high_regions = df_m[df_m["risk_name"]=="High"]["region"].unique()

if len(high_regions)==0:
    st.info("High 지역 없음")
else:
    ts = pd.Timestamp(f"{yr}-{mo:02d}-01")
    dfx = dfp[(dfp["year_month"]==ts) & (dfp["region"].isin(high_regions))]
    if dfx.empty:
        st.info("pairwise 데이터 없음")
    else:
        g = dfx.groupby(["region","stressor"], as_index=False)["R"].mean()
        g["R"] = g["R"].round(3)
        top1 = g.sort_values(["region","R"], ascending=[True,False]).groupby("region").head(1)

        st.dataframe(top1.rename(columns={"region":"지역","stressor":"최대 요인","R":"R값"}),
                     use_container_width=True)
