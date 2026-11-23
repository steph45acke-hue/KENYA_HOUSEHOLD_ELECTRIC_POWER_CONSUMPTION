import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Kenya Household Power Telemetry",
    page_icon="⚡",
    layout="wide",
)


def prepare_dataframe(raw_df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    data = raw_df.copy()

    if not isinstance(data.index, pd.DatetimeIndex):
        if "datetime" in data.columns:
            data["datetime"] = pd.to_datetime(data["datetime"], errors="coerce")
            data = data.set_index("datetime")
        elif "Date" in data.columns and "Time" in data.columns:
            dt = pd.to_datetime(
                data["Date"].astype(str) + " " + data["Time"].astype(str),
                errors="coerce",
            )
            data = data.assign(_dt=dt).set_index("_dt")
            data.index.name = "datetime"
        else:
            data.index = pd.to_datetime(data.index, errors="coerce")

    data = data[~data.index.isna()].sort_index()

    power_col = next(
        (col for col in ["Global_active_power", "global_active_power"] if col in data.columns),
        data.columns[0],
    )
    data[power_col] = pd.to_numeric(data[power_col], errors="coerce")

    if "Hour" not in data.columns:
        data["Hour"] = data.index.hour
    if "DayOfWeek" not in data.columns:
        data["DayOfWeek"] = data.index.dayofweek
    if "Weekday_Name" not in data.columns:
        data["Weekday_Name"] = data.index.day_name()
    if "Month" not in data.columns:
        data["Month"] = data.index.month
    if "Month_Name" not in data.columns:
        data["Month_Name"] = data.index.strftime("%b")
    if "Is_Weekend" not in data.columns:
        data["Is_Weekend"] = data.index.dayofweek.isin([5, 6]).astype(int)

    valid_power = data[power_col].dropna()
    if "Load_Regime" not in data.columns and valid_power.nunique() >= 4:
        data["Load_Regime"] = pd.qcut(
            data[power_col],
            q=4,
            labels=["Q1: Low/Idle", "Q2: Moderate", "Q3: Elevated", "Q4: Peak Draw"],
        )

    return data, power_col


# --- LOAD CLEANED DATA ---
@st.cache_data(show_spinner="Loading household power telemetry...")
def load_data() -> tuple[pd.DataFrame, str]:
    raw_df = pd.read_parquet("cleaned_household_power.parquet")
    return prepare_dataframe(raw_df)


try:
    df, power_col = load_data()
except Exception as e:
    st.error(
        f"⚠️ Could not load parquet file. Make sure 'cleaned_household_power.parquet' is in the directory. Error: {e}"
    )
    st.stop()

plt.style.use(
    "seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default"
)

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("⚡ Navigation & Controls")
st.sidebar.markdown("---")
page = st.sidebar.selectbox(
    "Choose Module Section",
    [
        "📊 Phase 1: Data Cleaning & Quality Scorecard",
        "📈 Phase 2: Exploratory Data Analysis & Visualizations",
        "📐 Phase 3.1: Descriptive Statistics & Load Profiles",
        "🎲 Phase 3.2: Probability & Distributions",
    ],
)

# --- MODULE 1: CLEANING & QUALITY SCORECARD ---
if page == "📊 Phase 1: Data Cleaning & Quality Scorecard":
    st.title("⚡ Household Power Telemetry: Data Engineering & Quality Dashboard")
    st.markdown("### Part 1: Ingestion, Cleaning, Integrity Audits, and Parquet Optimization")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Valid Records", f"{len(df):,}")
    with col2:
        if "Derived_Active_Energy_Wh" in df.columns:
            st.metric("Active Energy (Mean)", f"{df['Derived_Active_Energy_Wh'].mean():.2f} Wh/min")
        else:
            st.metric("Active Power (Mean)", f"{df[power_col].mean():.2f} kW")
    with col3:
        if "Outlier_Flag_Extreme" in df.columns:
            st.metric("Extreme Outliers Flagged", f"{int(df['Outlier_Flag_Extreme'].sum()):,}")
        else:
            st.metric("Peak Active Power", f"{df[power_col].max():.2f} kW")
    with col4:
        st.metric("Storage Format", "Apache Parquet (Snappy)")

    st.markdown("---")

    st.subheader("📊 Phase 1 Quality Scorecard & Pipeline Impact")
    try:
        st.image(
            "cleaning_pipeline_quality_scorecard.png",
            caption="Master Cleaning Pipeline Impact & Outlier Profiling",
            use_container_width=True,
        )
    except Exception:
        st.info("Place `cleaning_pipeline_quality_scorecard.png` in the project folder to display the scorecard image.")

    st.markdown("""
    #### Key Engineering Takeaways:
- **Robust Fencing:** Maintained $99.3\%$ of standard operational data while flagging extreme spikes using a $3.0 \\times IQR$ upper fence without destructive deletion.
- **Temporal Integrity:** Enforced strict monotonicity and stripped all exact duplicate index collisions ($\\approx 80\\text{k}$ records).
- **Unit Standardization:** Successfully converted raw kilowatts into interval-safe energy metrics ($\\text{Wh/min}$).
    """)

# --- MODULE 2: EDA & FEATURE ENGINEERING ---
elif page == "📈 Phase 2: Exploratory Data Analysis & Visualizations":
    st.title("📈 Exploratory Data Analysis & Feature Engineering")
    st.markdown("### Module 2.3 & 2.4: Distribution, Trends, and Feature Correlation")
    st.markdown("---")

    eda_tab = st.radio(
        "Select Analysis Component",
        [
            "📊 2.3 Distribution & Hourly Trends",
            "🔗 2.4 Correlation Matrix & Feature Engineering",
        ],
        horizontal=True,
    )

    if eda_tab == "📊 2.3 Distribution & Hourly Trends":
        st.subheader("Figure 2.1 & 2.2: Power Distribution & Resampled Trends")
        st.markdown(
            "Reveals baseline idle clustering alongside a right-skewed long tail, and aggregates high-frequency telemetry to an hourly mean grain."
        )

        st.sidebar.markdown("### Chart Settings (Module 2.3)")
        show_kde = st.sidebar.checkbox("Show KDE Density Curve", value=True, key="m23_show_kde")
        bins_slider = st.sidebar.slider("Histogram Bins", min_value=10, max_value=100, value=50, key="m23_bins")

        fig, axes = plt.subplots(2, 1, figsize=(14, 10), dpi=200)

        sns.histplot(
            df[power_col].dropna(),
            kde=show_kde,
            ax=axes[0],
            color="#1f77b4",
            bins=bins_slider,
            stat="density",
        )
        axes[0].set_title(
            "Figure 2.1: Global Active Power Distribution & Skewness Analysis",
            fontsize=13,
            fontweight="bold",
            pad=12,
        )
        axes[0].set_xlabel("Global Active Power (Kilowatts - kW)", fontsize=11)
        axes[0].set_ylabel("Density", fontsize=11)

        df_hourly = df[power_col].resample("h").mean()
        axes[1].plot(df_hourly.index, df_hourly.values, color="#ff7f0e", linewidth=0.8, alpha=0.85)
        axes[1].set_title(
            "Figure 2.2: Hourly Resampled Household Power Consumption Trend",
            fontsize=13,
            fontweight="bold",
            pad=12,
        )
        axes[1].set_xlabel("Timeline (Datetime Grain: Hourly Mean)", fontsize=11)
        axes[1].set_ylabel("Active Power (kW)", fontsize=11)

        plt.tight_layout()
        st.pyplot(fig, clear_figure=True)

        st.markdown("---")
        st.markdown("#### 📁 Repository Artifact Confirmation")
        st.success("✅ Module 2.3 visualization pipeline successfully integrated and rendered inside Streamlit.")

    elif eda_tab == "🔗 2.4 Correlation Matrix & Feature Engineering":
        st.subheader("Module 2.4: Multi-Collinearity & Telemetry Correlation Heatmap")
        st.markdown("Analyzing Pearson correlation coefficients across electrical parameters (Voltage, Intensity, Sub-metering).")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Engineered Temporal Features", "Hour, Month, DayOfWeek, Is_Weekend")
        with col2:
            st.metric("Correlation Method", "Pearson Parametric")

        st.markdown("---")

        numeric_cols = [
            "Global_active_power",
            "Global_reactive_power",
            "Voltage",
            "Global_intensity",
            "Sub_metering_1",
            "Sub_metering_2",
            "Sub_metering_3",
        ]
        available_cols = [col for col in numeric_cols if col in df.columns]
        corr_matrix = df[available_cols].corr(method="pearson")

        fig_corr, ax_corr = plt.subplots(figsize=(10, 7), dpi=200)
        sns.heatmap(
            corr_matrix,
            annot=True,
            fmt=".2f",
            cmap="coolwarm",
            vmin=-1,
            vmax=1,
            linewidths=0.5,
            ax=ax_corr,
            cbar_kws={"label": "Pearson Correlation Coefficient"},
        )
        ax_corr.set_title("Telemetry Feature Correlation Matrix", fontsize=13, fontweight="bold", pad=12)
        plt.tight_layout()
        st.pyplot(fig_corr, clear_figure=True)

        st.markdown("""
        #### 💡 Engineering Takeaways from Correlation Analysis:
- **Global Intensity & Active Power:** Show near-perfect positive correlation ($\\approx 0.98$), verifying physical Ohm's law constraints within the household circuit.
- **Voltage Stability:** Exhibits minimal correlation with active power loads, confirming stable grid voltage baseline across varying residential demand cycles.
        """)

# --- MODULE 3.1: DESCRIPTIVE STATISTICS & LOAD PROFILES ---
elif page == "📐 Phase 3.1: Descriptive Statistics & Load Profiles":
    st.title("📐 Descriptive Statistics & Conditional Load Profiles")
    st.markdown("### Section 3.1: Distribution Shape, Weekly Load Regimes & Hourly Demand Profiles")
    st.markdown("---")

    st.sidebar.markdown("### Section 3.1 Filters")
    selected_days = st.sidebar.multiselect(
        "Filter by Day of Week (empty = all days)",
        options=DAY_ORDER,
        default=[],
        key="m31_days",
    )
    hist_bins_31 = st.sidebar.slider(
        "Density Histogram Bins",
        min_value=20,
        max_value=100,
        value=60,
        key="m31_bins",
    )

    view_df = df[df["Weekday_Name"].isin(selected_days)] if selected_days else df
    s = view_df[power_col].dropna()

    if s.empty:
        st.warning("⚠️ No valid active power rows match the selected day filter.")
        st.stop()

    mean_val = float(s.mean())
    median_val = float(s.median())
    iqr_val = float(s.quantile(0.75) - s.quantile(0.25))
    p95_val = float(s.quantile(0.95))

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Mean Active Power", f"{mean_val:.3f} kW")
    with m2:
        st.metric("Median (Q2)", f"{median_val:.3f} kW")
    with m3:
        st.metric("IQR (Q3 - Q1)", f"{iqr_val:.3f} kW")
    with m4:
        st.metric("95th Percentile", f"{p95_val:.3f} kW")

    st.markdown("---")

    # --- Chart 1: Histogram + KDE & ECDF ---
    st.subheader("Chart 1: Active Power Density (Histogram + KDE) & Empirical CDF (ECDF)")
    fig1, axes1 = plt.subplots(1, 2, figsize=(15, 5), dpi=200)

    sns.histplot(s, bins=hist_bins_31, kde=True, stat="density", ax=axes1[0], color="#1f77b4")
    axes1[0].axvline(mean_val, color="red", linestyle="--", linewidth=1.5, label=f"Mean ({mean_val:.2f})")
    axes1[0].axvline(median_val, color="green", linestyle="-.", linewidth=1.5, label=f"Median ({median_val:.2f})")
    axes1[0].set_title("Active Power Density (Histogram + KDE)")
    axes1[0].set_xlabel(power_col)
    axes1[0].legend()

    sns.ecdfplot(s, ax=axes1[1], color="#2ca02c", linewidth=1.8)
    axes1[1].axhline(0.50, color="gray", linestyle=":", linewidth=1)
    axes1[1].axhline(0.95, color="orange", linestyle=":", linewidth=1)
    axes1[1].set_title("Empirical CDF (ECDF) of Active Power")
    axes1[1].set_xlabel(power_col)
    axes1[1].set_ylabel("Cumulative Proportion")

    plt.tight_layout()
    st.pyplot(fig1, clear_figure=True)

    # --- Chart 2: Boxplot & Violin Plot by Day of Week ---
    st.subheader("Chart 2: Day-of-Week Boxplot & Violin Plot")
    active_day_order = selected_days if selected_days else DAY_ORDER
    fig2, axes2 = plt.subplots(1, 2, figsize=(16, 5), dpi=200)

    sns.boxplot(
        data=view_df,
        x="Weekday_Name",
        y=power_col,
        order=active_day_order,
        showfliers=False,
        ax=axes2[0],
    )
    axes2[0].set_title("Active Power by Day of Week (Excl. Extreme Outliers)")
    axes2[0].set_xlabel("")
    axes2[0].tick_params(axis="x", rotation=25)

    sample_df = view_df.sample(n=min(100_000, len(view_df)), random_state=42)
    sns.violinplot(
        data=sample_df,
        x="Weekday_Name",
        y=power_col,
        order=active_day_order,
        inner="quartile",
        cut=0,
        ax=axes2[1],
    )
    axes2[1].set_title("Violin + Quartiles by Day of Week (Sampled)")
    axes2[1].set_xlabel("")
    axes2[1].tick_params(axis="x", rotation=25)

    plt.tight_layout()
    st.pyplot(fig2, clear_figure=True)

    # --- Chart 3: Quantile Function & Hourly Mean Bar Chart ---
    st.subheader("Chart 3: Quantile Function (1st–99th Percentile) & Hourly Mean Active Power")
    hourly_stats = (
        view_df.groupby("Hour", observed=False)[power_col]
        .agg(
            count="count",
            mean="mean",
            median="median",
            std="std",
            iqr=lambda x: x.quantile(0.75) - x.quantile(0.25),
            max_peak="max",
        )
        .reindex(range(24))
        .round(3)
    )

    fig3, axes3 = plt.subplots(1, 2, figsize=(15, 5), dpi=200)

    pct_grid = np.linspace(0.01, 0.99, 99)
    q_vals = s.quantile(pct_grid)
    axes3[0].plot(pct_grid * 100, q_vals.values, color="#9467bd", linewidth=2)
    axes3[0].set_title("Quantile Function (1st to 99th Percentile)")
    axes3[0].set_xlabel("Percentile")
    axes3[0].set_ylabel(power_col)

    hourly_stats["mean"].plot(kind="bar", ax=axes3[1], color="#ff7f0e", alpha=0.85)
    axes3[1].set_title("Mean Active Power by Hour of Day")
    axes3[1].set_xlabel("Hour (0–23)")
    axes3[1].set_ylabel("Mean Power")

    plt.tight_layout()
    st.pyplot(fig3, clear_figure=True)

# --- MODULE 3.2: PROBABILITY & DISTRIBUTIONS ---
elif page == "🎲 Phase 3.2: Probability & Distributions":
    st.title("🎲 Probability, Distributions, Exceedance Risk & Serial Dependence")
    st.markdown("### Section 3.2: Parametric Fits, Threshold Exceedance, Bayes' Rule & Autocorrelation")
    st.markdown("---")

    st.sidebar.markdown("### Section 3.2 Controls")
    threshold_kW = st.sidebar.slider(
        "Primary Exceedance Threshold (kW)",
        min_value=0.5,
        max_value=5.0,
        value=2.0,
        step=0.1,
        key="m32_thresh",
    )
    dens_bins_32 = st.sidebar.slider(
        "Density Histogram Bins",
        min_value=20,
        max_value=100,
        value=60,
        key="m32_bins",
    )

    s = df[power_col].dropna()
    n = len(s)
    if n == 0:
        st.warning("⚠️ No valid active power rows available.")
        st.stop()

    pos = s[s > 0].to_numpy(dtype=float)
    mean_val = float(s.mean())
    std_val = float(s.std(ddof=1))

    norm_mu, norm_sigma = stats.norm.fit(s.to_numpy(dtype=float))
    fitted_norm = stats.norm(loc=float(norm_mu), scale=float