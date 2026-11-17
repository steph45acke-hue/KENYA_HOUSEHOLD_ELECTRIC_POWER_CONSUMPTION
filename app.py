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
    # Loads our immutable parquet asset generated in Phase 1
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
    "📈 Phase 2: Exploratory Data Analysis & Visualizations"
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

# --- MODULE 2: EDA & VISUALIZATIONS ---
elif page == "📈 Phase 2: Exploratory Data Analysis & Visualizations":
    st.title("📈 Exploratory Data Analysis & Chart Literacy")
    st.markdown("### Module 2.3: Distribution Skewness & Hourly Resampled Trends")
    st.markdown("---")

    # Interactive Controls in Sidebar
    st.sidebar.markdown("### Chart Settings")
    show_kde = st.sidebar.checkbox("Show KDE Density Curve", value=True)
    bins_slider = st.sidebar.slider("Histogram Bins", min_value=10, max_value=100, value=50)

    # Automatically identify active power column
    power_col = next((col for col in ['Global_active_power', 'global_active_power'] if col in df.columns), df.columns[0])

    # --- Figure A: Distribution & Skewness ---
    st.subheader("Figure 2.1: Global Active Power Distribution & Skewness Analysis")
    st.markdown("Reveals baseline idle clustering alongside a right-skewed long tail capturing high-draw residential peaks.")
    
    # Configure Professional Style Guide & Subplots matching your tested script
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    fig, axes = plt.subplots(2, 1, figsize=(14, 10), dpi=300)

    sns.histplot(
        df[power_col].dropna(), 
        kde=show_kde, 
        ax=axes[0], 
        color='#1f77b4', 
        bins=bins_slider, 
        stat='density'
    )
    axes[0].set_title('Figure 2.1: Global Active Power Distribution & Skewness Analysis', fontsize=14, fontweight='bold', pad=15)
    axes[0].set_xlabel('Global Active Power (Kilowatts - kW)', fontsize=11)
    axes[0].set_ylabel('Density', fontsize=11)
    axes[0].annotate(
        'Right-skewed long tail\n(High-load residential peaks)', 
        xy=(4.0, 0.15), xytext=(5.5, 0.25),
        arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=6),
        fontsize=10, fontweight='semibold'
    )

    # --- Figure B: Temporal Resampling & Trend Analysis ---
    st.markdown("---")
    st.subheader("Figure 2.2: Hourly Resampled Household Power Consumption Trend")
    st.markdown("Aggregating high-frequency telemetry to an hourly mean grain to isolate macro seasonality and data gaps.")

    print("Resampling time-series data to hourly grain...")
    df_hourly = df[power_col].resample('h').mean()

    axes[1].plot(df_hourly.index, df_hourly.values, color='#ff7f0e', linewidth=0.8, alpha=0.85)
    axes[1].set_title('Figure 2.2: Hourly Resampled Household Power Consumption Trend', fontsize=14, fontweight='bold', pad=15)
    axes[1].set_xlabel('Timeline (Datetime Grain: Hourly Mean)', fontsize=11)
    axes[1].set_ylabel('Active Power (kW)', fontsize=11)

    # Overall layout polish
    plt.tight_layout()
    st.pyplot(fig)

    # Markdown Export Evidence Reference
    st.markdown("---")
    st.markdown("#### 📁 Repository Artifact Confirmation")
    st.success("✅ Module 2.3 visualization pipeline successfully integrated and rendered inside Streamlit.")