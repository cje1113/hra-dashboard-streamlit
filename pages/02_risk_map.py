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


df = parse_df(load_csv(DATA_LABEL))
dfp = parse_df(load_csv(DATA_PAIR))


# region 좌표
REGION_COORDS = {
    "Incheon": (37.456, 126.705),
    "Geoje": (34.880, 128.620),
    "Ulleungdo": (37.500, 130.900),
    "거제": (34.880, 128.620),
    "인천": (37.456, 126.705),
    "울릉도": (37.500, 130.900)
}

df["lat"] = df["region"].map(lambda r: REGION_COORDS.get(str(r),(np.nan,np.nan))[0])
df["lon"] = df["region"].map(lambda r: REGION_COORDS.get(str(r),(np.nan,np.nan))[1])
df = df.dropna(subset=["lat","lon"])


# risk name
df["risk_name"] = df["risk_level"].astype(str).str.title()

ORDER = ["Low","Medium","High"]
COLOR = {"Low":"#4CAF50","Medium":"#FFC107","High":"#F44336"}
df["risk_name"] = pd.Categorical(df["risk_name"], categories=ORDER)


# GeoJSON
URL = "https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2013/json/skorea_provinces_geo_simple.json"
with urllib.request.urlopen(URL) as f:
    geojson = json.load(f)


# UI
st.title("🗺️ Risk Map — Full Width")
st.caption("전국 GeoJSON + 위험도 버블")


regions = sorted(df["region"].unique())
sel_regions = st.multiselect("지역", regions, default=regions[:3])

df_v = df[df["region"].isin(sel_regions)]

years = sorted(df_v["year_month"].dt.year.unique())
colY, colM = st.columns(2)
yr = colY.selectbox("연도", years)
months = sorted(df_v[df_v["year_month"].dt.year == yr]["year_month"].dt.month.unique())
mo = colM.selectbox("월", months)

df_m = df_v[(df_v["year_month"].dt.year==yr) & (df_v["year_month"].dt.month==mo)].copy()
df_m["ym_str"] = df_m["year_month"].dt.strftime("%Y-%m")


fig = px.scatter_mapbox(
    df_m,
    lat="lat",
    lon="lon",
    size=df_m["R_sum"] * 40,    # 버블 크게 조정
    color="risk_name",
    color_discrete_map=COLOR,
    hover_name="region",
    hover_data={"risk_name": True, "ym_str": True},
    zoom=5.4,
    height=680,
)


fig.update_layout(
    mapbox_style="open-street-map",
    mapbox_layers=[
        {"source": geojson, "type":"line", "color":"black", "line":{"width":1}}
    ],
    margin=dict(l=0,r=0,t=0,b=0)
)

st.plotly_chart(fig, use_container_width=True)