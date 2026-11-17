import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Kenya Household Power Telemetry",
    page_icon="⚡",
    layout="wide"
)

# --- LOAD CLEANED DATA ---
@st.cache_data
def load_data():
    # Loads our immutable parquet asset generated in Phase 1.7
    df = pd.read_parquet("cleaned_household_power.parquet")
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"⚠️ Could not load parquet file. Make sure 'cleaned_household_power.parquet' is in the directory. Error: {e}")
    st.stop()

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("⚡ Navigation & Controls")
st.sidebar.markdown("---")
page = st.sidebar.selectbox("Choose Module Section", [
    "📊 Phase 1: Data Cleaning & Quality Scorecard", 
    "📈 Phase 2: Exploratory Data Analysis (Coming Soon)"
])

# --- MODULE 1: CLEANING & QUALITY SCORECARD ---
if page == "📊 Phase 1: Data Cleaning & Quality Scorecard":
    st.title("⚡ Household Power Telemetry: Data Engineering & Quality Dashboard")
    st.markdown("### Part 1: Ingestion, Cleaning, Integrity Audits, and Parquet Optimization")
    st.markdown("---")

    # Top Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Valid Records", f"{len(df):,}")
    with col2:
        st.metric("Active Energy (Mean)", f"{df['Derived_Active_Energy_Wh'].mean():.2f} Wh/min")
    with col3:
        st.metric("Extreme Outliers Flagged", f"{df['Outlier_Flag_Extreme'].sum():,}")
    with col4:
        st.metric("Storage Format", "Apache Parquet (Snappy)")

    st.markdown("---")
    
    # Section: Visual Scorecard
    st.subheader("📊 Phase 1 Quality Scorecard & Pipeline Impact")
    st.image("cleaning_pipeline_quality_scorecard.png", caption="Master Cleaning Pipeline Impact & Outlier Profiling", use_container_width=True)

    st.markdown("""
    #### Key Engineering Takeaways:
    * **Robust Fencing:** Maintained $99.3\%$ of standard operational data while flagging extreme spikes using a $3.0 \times IQR$ upper fence without destructive deletion.
    * **Temporal Integrity:** Enforced strict monotonicity and stripped all exact duplicate index collisions ($\approx 80\text{k}$ records).
    * **Unit Standardization:** Successfully converted raw kilowatts into interval-safe energy metrics ($\text{Wh/min}$).
    """)

elif page == "📈 Phase 2: Exploratory Data Analysis (Coming Soon)":
    st.title("📈 Exploratory Data Analysis & Advanced Feature Engineering")
    st.markdown("### Part 2 is staged and ready for development!")
    st.info("ℹ️ As we progress through feature engineering and time-series modeling, interactive charts will appear here automatically.")