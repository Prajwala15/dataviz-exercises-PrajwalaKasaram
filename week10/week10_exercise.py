from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="CO2 Dashboard", page_icon="🌱", layout="wide")

METRICS = {"Total CO2 (Mt)": "CO2_Mt", "CO2 per capita": "CO2_per_capita"}

@st.cache_data
def load_data():
    df = pd.read_csv(Path(__file__).resolve().parent.parent / "data" / "co2_emissions.csv")
    df["Date"] = pd.to_datetime(df["Year"].astype(str) + "-01-01")
    return df

df = load_data()

st.title("🌱 CO2 Emissions Explorer")
st.caption("Source: Our World in Data — ourworldindata.org/co2-emissions")