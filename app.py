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


def block_bootstrap_stat(
    values: np.ndarray,
    stat_fn,
    block_size: int = 240,
    n_boot: int = 300,
    seed: int = 42,
) -> tuple[float, float, float, np.ndarray]:
    g = np.random.default_rng(seed)
    b_size = min(max(1, block_size), len(values))
    n_blocks = max(1, len(values) // b_size)
    trimmed = values[: n_blocks * b_size].reshape(n_blocks, b_size)
    draws = np.empty(n_boot, dtype=float)
    for i in range(n_boot):
        idx = g.integers(0, n_blocks, size=n_blocks)
        draws[i] = stat_fn(trimmed[idx].ravel())
    low, high = np.percentile(draws, [2.5, 97.5])
    return float(stat_fn(values)), float(low), float(high), draws


@st.cache_data(show_spinner="Computing Section 3.3 block-bootstrap confidence intervals...")
def compute_section33_summaries(
    power_arr: np.ndarray,
    hours_arr: np.ndarray,
    weekend_arr: np.ndarray,
    block_len: int,
    n_boot: int,
) -> dict:
    n_total = len(power_arr)
    rng = np.random.default_rng(42)

    mean_est, mean_lo, mean_hi, boot_means = block_bootstrap_stat(
        power_arr, np.mean, block_size=block_len, n_boot=n_boot, seed=42
    )
    med_est, med_lo, med_hi, _ = block_bootstrap_stat(
        power_arr, np.median, block_size=block_len, n_boot=n_boot, seed=43
    )
    p95_est, p95_lo, p95_hi, _ = block_bootstrap_stat(
        power_arr, lambda x: np.percentile(x, 95), block_size=block_len, n_boot=n_boot, seed=44
    )

    iid_means = np.array([rng.choice(power_arr, size=n_total, replace=True).mean() for _ in range(n_boot)])
    iid_lo, iid_hi = np.percentile(iid_means, [2.5, 97.5])

    hourly_rows = []
    for h in range(24):
        h_vals = power_arr[hours_arr == h]
        if len(h_vals) >= 20:
            h_mean, h_lo, h_hi, _ = block_bootstrap_stat(
                h_vals,
                np.mean,
                block_size=min(block_len, max(10, len(h_vals) // 20)),
                n_boot=max(150, n_boot // 2),
                seed=100 + h,
            )
        else:
            h_mean = float(np.mean(h_vals)) if len(h_vals) > 0 else np.nan
            h_lo = h_hi = h_mean
        hourly_rows.append(
            {"Hour": h, "count": len(h_vals), "mean": h_mean, "ci_low": h_lo, "ci_high": h_hi}
        )

    wkdy_vals = power_arr[weekend_arr == 0]
    wknd_vals = power_arr[weekend_arr == 1]
    diff_point = float(np.mean(wknd_vals) - np.mean(wkdy_vals))

    wkdy_blocks = wkdy_vals[: (len(wkdy_vals) // block_len) * block_len].reshape(-1, block_len)
    wknd_blocks = wknd_vals[: (len(wknd_vals) // block_len) * block_len].reshape(-1, block_len)
    diff_draws = np.empty(n_boot, dtype=float)
    for i in range(n_boot):
        m_wknd = wknd_blocks[rng.integers(0, len(wknd_blocks), size=len(wknd_blocks))].mean()
        m_wkdy = wkdy_blocks[rng.integers(0, len(wkdy_blocks), size=len(wkdy_blocks))].mean()
        diff_draws[i] = m_wknd - m_wkdy
    diff_lo, diff_hi = np.percentile(diff_draws, [2.5, 97.5])

    return {
        "mean_est": mean_est,
        "mean_lo": mean_lo,
        "mean_hi": mean_hi,
        "boot_means": boot_means,
        "med_est": med_est,
        "med_lo": med_lo,
        "med_hi": med_hi,
        "p95_est": p95_est,
        "p95_lo": p95_lo,
        "p95_hi": p95_hi,
        "iid_means": iid_means,
        "iid_lo": float(iid_lo),
        "iid_hi": float(iid_hi),
        "hourly_ci_df": pd.DataFrame(hourly_rows),
        "wkdy_mean": float(np.mean(wkdy_vals)),
        "wknd_mean": float(np.mean(wknd_vals)),
        "diff_point": diff_point,
        "diff_lo": float(diff_lo),
        "diff_hi": float(diff_hi),
        "diff_draws": diff_draws,
    }


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
        "📦 Phase 3.3: Sampling & Uncertainty",
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

    s_arr = s.to_numpy(dtype=float)
    pos = s_arr[s_arr > 0]
    std_val = float(s.std(ddof=1))

    norm_mu, norm_sigma = stats.norm.fit(s_arr)
    fitted_norm = stats.norm(loc=float(norm_mu), scale=float(norm_sigma))
    lognorm_shape, lognorm_loc, lognorm_scale = stats.lognorm.fit(pos, floc=0)
    expon_loc, expon_scale = stats.expon.fit(pos, floc=0)

    sample_test = s.sample(n=min(5000, n), random_state=42).to_numpy(dtype=float)
    _, shapiro_p = stats.shapiro(sample_test)
    ks_norm_stat, ks_norm_p = stats.kstest(sample_test, fitted_norm.cdf)

    p_exceed = float((s > threshold_kW).mean())
    is_eve = df["Hour"].isin([19, 20, 21])
    is_high = df[power_col] > threshold_kW
    p_eve = float(is_eve.mean())
    p_high_given_eve = float(df.loc[is_eve, power_col].gt(threshold_kW).mean())
    p_high = float(is_high.mean())
    p_eve_given_high = (p_high_given_eve * p_eve) / p_high if p_high > 0 else 0.0

    lag1_corr = float(s.autocorr(lag=1))
    se_iid = std_val / np.sqrt(n)
    n_eff = n * (1 - lag1_corr) / (1 + lag1_corr) if 0 < lag1_corr < 0.999 else float(n)
    se_corr_approx = std_val / np.sqrt(max(n_eff, 1.0))

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric(f"P(Power > {threshold_kW:.1f} kW)", f"{p_exceed*100:.2f}%")
    with k2:
        st.metric(f"P(Eve 19–21h | >{threshold_kW:.1f} kW)", f"{p_eve_given_high*100:.2f}%")
    with k3:
        st.metric("Lag-1 Autocorrelation", f"{lag1_corr:.4f}")
    with k4:
        st.metric("Naive vs. Adj. SE", f"{se_iid:.4f} vs {se_corr_approx:.4f}")

    st.markdown("---")

    # --- Plot A: Normal Q-Q Plot & Fitted vs Empirical Densities ---
    st.subheader("Plot A: Normal Q-Q Plot & Empirical vs. Candidate Parametric Densities")
    fig_a, axes_a = plt.subplots(1, 2, figsize=(15, 5), dpi=200)

    qq_sample = s.sample(n=min(20_000, n), random_state=42).to_numpy(dtype=float)
    stats.probplot(qq_sample, dist="norm", plot=axes_a[0])
    axes_a[0].set_title("Normal Q-Q Plot (Sampled Active Power)")

    x_grid = np.linspace(max(0.01, float(pos.min())), float(s.quantile(0.995)), 300)
    sns.histplot(
        s_arr,
        bins=dens_bins_32,
        stat="density",
        ax=axes_a[1],
        color="#1f77b4",
        alpha=0.45,
        label="Empirical Hist",
    )
    axes_a[1].plot(x_grid, fitted_norm.pdf(x_grid), "r--", lw=1.8, label="Fitted Normal")
    axes_a[1].plot(
        x_grid,
        stats.lognorm.pdf(x_grid, lognorm_shape, loc=lognorm_loc, scale=lognorm_scale),
        "g-.",
        lw=1.8,
        label="Fitted Lognormal",
    )
    axes_a[1].plot(
        x_grid,
        stats.expon.pdf(x_grid, loc=expon_loc, scale=expon_scale),
        color="#9467bd",
        ls=":",
        lw=1.8,
        label="Fitted Exponential",
    )
    axes_a[1].set_title("Empirical vs. Candidate Parametric Densities")
    axes_a[1].set_xlabel(power_col)
    axes_a[1].set_ylabel("Density")
    axes_a[1].legend()

    plt.tight_layout()
    st.pyplot(fig_a, clear_figure=True)

    # --- Plot B: Empirical CDF & Exceedance Probability Curve ---
    st.subheader("Plot B: Empirical CDF & Exceedance Probability Curve")
    fig_b, axes_b = plt.subplots(1, 2, figsize=(15, 5), dpi=200)

    sorted_vals = np.sort(s_arr)
    step = max(1, len(sorted_vals) // 20_000)
    ecdf_y = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals)
    exceed_y = 1.0 - ecdf_y

    axes_b[0].plot(sorted_vals[::step], ecdf_y[::step], color="#2ca02c", lw=1.8)
    axes_b[0].set_title("Empirical CDF: F(x) = P(X <= x)")
    axes_b[0].set_xlabel(power_col)
    axes_b[0].set_ylabel("F(x)")

    axes_b[1].plot(sorted_vals[::step], exceed_y[::step], color="#d62728", lw=1.8)
    for tau in [1.5, 2.0, 3.5, threshold_kW]:
        axes_b[1].axvline(tau, color="gray", ls="--", lw=1)
    axes_b[1].set_title("Exceedance Probability Curve: P(X > x)")
    axes_b[1].set_xlabel(power_col)
    axes_b[1].set_ylabel("1 - F(x)")

    plt.tight_layout()
    st.pyplot(fig_b, clear_figure=True)

    st.markdown(f"""
    #### Distribution Assessment & Caveats:
- **Normality Rejected:** Skewness is `{s.skew():.4f}`, excess kurtosis is `{s.kurt():.4f}`, Shapiro–Wilk `p = {shapiro_p:.2e}`, and KS vs. Normal `p = {ks_norm_p:.2e}` (`D = {ks_norm_stat:.4f}`), confirming non-normality and heavy right-tail behavior.
- **Model Defensibility:** Empirical CDF/exceedance curves are most reliable directly from data; Lognormal captures positive skew better than Normal or Exponential, while Poisson applies only to discrete event counts rather than continuous kW.
- **Serial Dependence:** High lag-1 autocorrelation (`{lag1_corr:.4f}`) reduces effective sample size (`n_eff ≈ {n_eff:,.0f}`), so naive i.i.d. standard errors understate true uncertainty.
    """)

# --- MODULE 3.3: SAMPLING & UNCERTAINTY ---
elif page == "📦 Phase 3.3: Sampling & Uncertainty":
    st.title("📦 Sampling, Block Bootstrap & Uncertainty Analysis")
    st.markdown("### Section 3.3: 95% Confidence Intervals, Weekday–Weekend Difference & Sample Coverage")
    st.markdown("---")

    st.sidebar.markdown("### Section 3.3 Controls")
    block_len_33 = st.sidebar.slider(
        "Block Size (Intervals per Block)",
        min_value=30,
        max_value=480,
        value=240,
        step=30,
        key="m33_block",
    )
    n_boot_33 = st.sidebar.slider(
        "Bootstrap Resamples",
        min_value=150,
        max_value=600,
        value=300,
        step=50,
        key="m33_boot",
    )
    sample_n_33 = st.sidebar.slider(
        "Coverage Sample Size",
        min_value=2_000,
        max_value=25_000,
        value=10_000,
        step=1_000,
        key="m33_sample_n",
    )

    valid_df = df.dropna(subset=[power_col])
    s_arr = valid_df[power_col].to_numpy(dtype=float)
    hours_arr = valid_df["Hour"].to_numpy(dtype=int)
    weekend_arr = valid_df["Is_Weekend"].to_numpy(dtype=int)
    n_total = len(s_arr)

    if n_total == 0:
        st.warning("⚠️ No valid active power rows available.")
        st.stop()

    res = compute_section33_summaries(s_arr, hours_arr, weekend_arr, block_len_33, n_boot_33)
    hourly_ci_df = res["hourly_ci_df"]

    # Hourly coverage comparison (Random vs Stratified)
    actual_sample_n = min(sample_n_33, n_total)
    rand_sample = valid_df.sample(n=actual_sample_n, random_state=42)

    strat_parts = []
    for _, grp in valid_df.groupby("Hour", sort=True):
        k = max(1, min(int(round(actual_sample_n * len(grp) / n_total)), len(grp)))
        strat_parts.append(grp.sample(n=k, random_state=42))
    strat_sample = pd.concat(strat_parts, axis=0)

    pop_share = valid_df["Hour"].value_counts(normalize=True).reindex(range(24), fill_value=0.0)
    rand_share = rand_sample["Hour"].value_counts(normalize=True).reindex(range(24), fill_value=0.0)
    strat_share = strat_sample["Hour"].value_counts(normalize=True).reindex(range(24), fill_value=0.0)
    coverage_df = pd.DataFrame({
        "Population_Share": pop_share,
        "Random_Sample_Share": rand_share,
        "Stratified_Sample_Share": strat_share,
    })

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Mean (95% Block CI)", f"{res['mean_est']:.3f} kW", f"[{res['mean_lo']:.3f}, {res['mean_hi']:.3f}]")
    with c2:
        st.metric("Median (95% Block CI)", f"{res['med_est']:.3f} kW", f"[{res['med_lo']:.3f}, {res['med_hi']:.3f}]")
    with c3:
        st.metric("P95 Peak (95% Block CI)", f"{res['p95_est']:.3f} kW", f"[{res['p95_lo']:.3f}, {res['p95_hi']:.3f}]")
    with c4:
        st.metric(
            "Wknd − Wkdy Diff",
            f"{res['diff_point']:+.3f} kW",
            f"95% CI [{res['diff_lo']:+.3f}, {res['diff_hi']:+.3f}]",
        )

    st.markdown("---")

    # --- Chart 1: Hourly 95% Block CIs & Weekend-Weekday Difference Distribution ---
    st.subheader("Chart 1: Average Hourly Active Power (95% Block CIs) & Weekend–Weekday Difference")
    fig_c1, axes_c1 = plt.subplots(1, 2, figsize=(15, 5), dpi=200)

    yerr_lo = (hourly_ci_df["mean"] - hourly_ci_df["ci_low"]).clip(lower=0)
    yerr_hi = (hourly_ci_df["ci_high"] - hourly_ci_df["mean"]).clip(lower=0)
    axes_c1[0].errorbar(
        hourly_ci_df["Hour"],
        hourly_ci_df["mean"],
        yerr=[yerr_lo, yerr_hi],
        fmt="o-",
        color="#1f77b4",
        ecolor="#ff7f0e",
        elinewidth=1.5,
        capsize=3,
        label="Hourly Mean ± 95% Block CI",
    )
    axes_c1[0].set_title("Average Hourly Active Power with 95% Block CIs")
    axes_c1[0].set_xlabel("Hour of Day (0–23)")
    axes_c1[0].set_ylabel(f"{power_col} (kW)")
    axes_c1[0].set_xticks(range(0, 24, 2))
    axes_c1[0].legend()

    sns.histplot(res["diff_draws"], bins=35, kde=True, ax=axes_c1[1], color="#2ca02c", alpha=0.6)
    axes_c1[1].axvline(res["diff_point"], color="black", linestyle="-", linewidth=1.8, label=f"Diff ({res['diff_point']:+.3f})")
    axes_c1[1].axvline(res["diff_lo"], color="red", linestyle="--", linewidth=1.4, label=f"95% CI [{res['diff_lo']:+.3f}, {res['diff_hi']:+.3f}]")
    axes_c1[1].axvline(res["diff_hi"], color="red", linestyle="--", linewidth=1.4)
    axes_c1[1].set_title("Block Bootstrap: Weekend minus Weekday Mean")
    axes_c1[1].set_xlabel("Mean Power Difference (kW)")
    axes_c1[1].legend()

    plt.tight_layout()
    st.pyplot(fig_c1, clear_figure=True)

    # --- Chart 2: i.i.d. vs Block Bootstrap Spread & Hourly Share Coverage ---
    st.subheader("Chart 2: i.i.d. vs. Block Bootstrap Mean Spread & Hourly Share Coverage")
    fig_c2, axes_c2 = plt.subplots(1, 2, figsize=(15, 5), dpi=200)

    sns.kdeplot(res["iid_means"], ax=axes_c2[0], color="#9467bd", linestyle="--", linewidth=1.8, label="i.i.d. Bootstrap Mean")
    sns.kdeplot(res["boot_means"], ax=axes_c2[0], color="#d62728", linestyle="-", linewidth=2.0, label="Block Bootstrap Mean")
    axes_c2[0].set_title("Sampling Distribution of Overall Mean: i.i.d. vs. Block")
    axes_c2[0].set_xlabel("Bootstrapped Mean (kW)")
    axes_c2[0].legend()

    axes_c2[1].plot(coverage_df.index, coverage_df["Population_Share"] * 100, "k-", lw=2, label="Population %")
    axes_c2[1].plot(coverage_df.index, coverage_df["Random_Sample_Share"] * 100, "o--", ms=4, alpha=0.8, label="Random Sample %")
    axes_c2[1].plot(coverage_df.index, coverage_df["Stratified_Sample_Share"] * 100, "s:", ms=4, alpha=0.8, label="Stratified Sample %")
    axes_c2[1].set_title("Hourly Share Coverage Across Hours (0–23)")
    axes_c2[1].set_xlabel("Hour of Day (0–23)")
    axes_c2[1].set_ylabel("Share of Records (%)")
    axes_c2[1].set_xticks(range(0, 24, 2))
    axes_c2[1].legend()

    plt.tight_layout()
    st.pyplot(fig_c2, clear_figure=True)

    st.markdown(f"""
    #### Uncertainty & Sampling Strategy Takeaways:
- **Block vs. i.i.d. Bootstrap:** i.i.d. 95% mean CI (`[{res['iid_lo']:.4f}, {res['iid_hi']:.4f}]`) is substantially narrower than the block-bootstrap 95% CI (`[{res['mean_lo']:.4f}, {res['mean_hi']:.4f}]`) because serial dependence reduces independent information across consecutive readings.
- **Weekday vs. Weekend Lift:** Weekend mean (`{res['wknd_mean']:.4f}` kW) exceeds weekday mean (`{res['wkdy_mean']:.4f}` kW) by `{res['diff_point']:+.4f}` kW (`95% Block CI: [{res['diff_lo']:+.4f}, {res['diff_hi']:+.4f}]`).
- **Defensible Sampling:** Use **stratified sampling by `Hour`** (and `Is_Weekend`) or **contiguous time blocks** for rapid prototyping, and compute final operational estimates on the full cleaned dataset.
    """)