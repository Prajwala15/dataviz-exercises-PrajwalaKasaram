"""
Amsterdam Airbnb Dashboard
Run locally:  streamlit run app.py
Deploy:       push to a public GitHub repo, then deploy on
              https://share.streamlit.io (Streamlit Community Cloud)

Expects a `data/listings.csv` and `data/reviews.csv` from
https://insideairbnb.com/amsterdam/ in the same repo.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Amsterdam Airbnb Story", layout="wide")

CVD_SAFE = ['#0072B2', '#E69F00', '#009E73', '#D55E00', '#CC79A7', '#56B4E9']
GREY = '#B0B0B0'
HIGHLIGHT = '#0072B2'


@st.cache_data
def load_data():
    listings = pd.read_csv('data/listings.csv')
    reviews = pd.read_csv('data/reviews.csv')

    listings['price'] = (
        listings['price'].astype(str).replace('[\\$,]', '', regex=True).astype(float)
    )
    listings = listings[listings['price'] > 0]
    if 'host_is_superhost' in listings.columns:
        listings['host_is_superhost'] = listings['host_is_superhost'].map({'t': True, 'f': False})

    reviews['date'] = pd.to_datetime(reviews['date'], errors='coerce')

    keep_cols = ['id', 'neighbourhood_cleansed', 'latitude', 'longitude', 'room_type',
                 'price', 'minimum_nights', 'number_of_reviews', 'review_scores_rating',
                 'availability_365', 'host_id', 'calculated_host_listings_count',
                 'host_is_superhost']
    keep_cols = [c for c in keep_cols if c in listings.columns]
    listings = listings.dropna(subset=['price', 'neighbourhood_cleansed'])[keep_cols]

    return listings, reviews


listings, reviews = load_data()

st.title("Amsterdam Airbnb: Price, Regulation & the Tourist City")
st.caption("Data: Inside Airbnb (CC BY 4.0) · insideairbnb.com/amsterdam")

# ---- Top-level metrics ----
c1, c2, c3, c4 = st.columns(4)
c1.metric("Listings", f"{len(listings):,}")
c2.metric("Median price / night", f"€{listings['price'].median():.0f}")
c3.metric("Neighbourhoods", listings['neighbourhood_cleansed'].nunique())
c4.metric("Superhost share",
          f"{listings['host_is_superhost'].mean():.0%}" if 'host_is_superhost' in listings.columns else "n/a")

tab1, tab2, tab3 = st.tabs(["Where & How Much", "Hosts & Regulation", "Seasonality"])

# ---------------- TAB 1 ----------------
with tab1:
    hoods = sorted(listings['neighbourhood_cleansed'].unique())
    selected_hoods = st.multiselect("Neighbourhood", hoods, default=hoods)
    room_types = st.multiselect(
        "Room type", sorted(listings['room_type'].unique()),
        default=sorted(listings['room_type'].unique())
    )

    filtered = listings[
        listings['neighbourhood_cleansed'].isin(selected_hoods)
        & listings['room_type'].isin(room_types)
    ]

    col_a, col_b = st.columns([1, 1])

    with col_a:
        region_avg = (filtered.groupby('neighbourhood_cleansed')['price']
                      .mean().reset_index().sort_values('price'))
        top_hood = region_avg.iloc[-1]['neighbourhood_cleansed'] if len(region_avg) else None
        colors = [HIGHLIGHT if n == top_hood else GREY for n in region_avg['neighbourhood_cleansed']]

        fig = go.Figure(go.Bar(
            x=region_avg['price'], y=region_avg['neighbourhood_cleansed'],
            orientation='h', marker_color=colors
        ))
        fig.update_layout(
            title="Average price by neighbourhood", height=500,
            xaxis_title='EUR / night', yaxis_title=None,
            plot_bgcolor='white', paper_bgcolor='white'
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        fig_map = px.scatter_mapbox(
            filtered, lat='latitude', lon='longitude', color='price',
            color_continuous_scale='Blues', zoom=11, mapbox_style='carto-positron',
            range_color=(filtered['price'].quantile(0.05), filtered['price'].quantile(0.95))
                if len(filtered) else None
        )
        fig_map.update_layout(title="Price by location", margin=dict(l=0, r=0, t=40, b=0), height=500)
        st.plotly_chart(fig_map, use_container_width=True)

# ---------------- TAB 2 ----------------
with tab2:
    col_a, col_b = st.columns(2)

    with col_a:
        listings['host_type'] = np.where(
            listings['calculated_host_listings_count'] > 1,
            'Multi-listing host', 'Single-listing host'
        )
        host_price = listings.groupby('host_type')['price'].mean().reset_index()
        fig = go.Figure(go.Bar(
            x=host_price['host_type'], y=host_price['price'],
            marker_color=[HIGHLIGHT, GREY]
        ))
        fig.update_layout(title="Avg price: multi-listing vs. single-listing hosts",
                           plot_bgcolor='white', paper_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        fig = px.histogram(listings, x='availability_365', nbins=50,
                            color_discrete_sequence=[GREY])
        fig.add_vline(x=335, line_dash='dash', line_color=HIGHLIGHT,
                      annotation_text='30-night cap threshold')
        fig.update_layout(title="Availability vs. the 30-night regulatory cap",
                           plot_bgcolor='white', paper_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)

# ---------------- TAB 3 ----------------
with tab3:
    monthly = reviews.set_index('date').resample('ME').size().reset_index(name='reviews')
    fig = px.line(monthly, x='date', y='reviews', color_discrete_sequence=[HIGHLIGHT])
    fig.update_layout(title="Review volume over time (proxy for bookings)",
                       plot_bgcolor='white', paper_bgcolor='white')
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.caption("Built for the Data Visualization final project · Summer 2026")
