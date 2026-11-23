# ⚡ Kenya Household Electric Power Consumption Analytics & Forecasting Engine

<div align="center">

[![Status](https://img.shields.io/badge/Status-Active%20Development-success.svg)]()
[![Context](https://img.shields.io/badge/Context-Kenyan%20Energy%20Landscape-orange.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

</div>

---

## 📄 Project Overview

The **Kenya Household Electric Power Consumption Analytics Engine** is an end-to-end data analytics and economic telemetry pipeline designed to model domestic electrical load patterns within the Kenyan energy landscape. As urban and peri-urban households navigate evolving power tariffs, grid stability challenges, and the transition toward smart metering infrastructure, understanding granular energy dynamics is vital. This project ingests high-volume, minute-level electrical telemetry, cleans missing sensor data, engineers behavioral consumption features, and translates raw power logs into actionable economic and household utility insights.

---

## 💡 The Rationale & Motivation

Energy security, household budgeting, and grid reliability are pressing socio-economic priorities in Kenya. With electricity forming a significant portion of monthly household expenditures and the national grid experiencing shifting load demands, data-driven energy management is more critical than ever. 

This initiative demonstrates professional capability in tackling complex economic and operational challenges through data:
* **Translating Telemetry to Economics:** Bridging raw electrical measurements with consumer utility budgeting, cost optimization, and demand forecasting.
* **Robust Data Pipeline Design:** Managing millions of high-frequency records to eliminate noise, handle sensor dropouts, and extract clean temporal trends.
* **Empirical Decision Support:** Empowering consumers and energy planners with granular visibility into peak consumption windows and unmetered power draws.

---

## 🎯 The Core Problem We Are Solving

Domestic energy consumers and local grid observers face recurring hurdles when trying to optimize power utilization without clear empirical visibility:

1. **Tariff Pressure & Peak Load Blindness:** Households face fluctuating utility costs and peak-hour pressures without knowing *when* and *where* energy is being heavily drawn. Without structured hourly and daily aggregation, identifying inefficient usage habits or planning around peak tariffs is nearly impossible.
2. **Sensor Noise & Missing Telemetry:** Raw smart-meter logs are prone to dropouts, corrupt timestamps, and missing values represented by placeholder characters. Left unaddressed, these anomalies corrupt economic trend analysis and forecasting models.
3. **Unaccounted Energy & Hidden Baselines:** Standard meters track total active power alongside specific sub-meters (such as kitchen appliances or laundry systems), but a substantial portion of household draw often falls outside dedicated monitoring. Quantifying this unmetered remainder is essential for realistic energy auditing and waste reduction.

---
---

## 🔬 Core Research Questions & Data Science Objectives

To move beyond basic descriptive summaries, this project is structured around answering four complex, empirically driven data science questions:

### 1. Non-Stationary Time-Series Forecasting & Peak Load Prediction
* **The Question:** Can we accurately predict hourly and daily aggregate active power demand 24 to 72 hours in advance under conditions of high temporal volatility and non-stationary consumption patterns?
* **Data Science Approach:** Implementing advanced time-series modeling (such as seasonal decomposition, gradient boosting regressors, or recurrent architectures) by engineering lag features, rolling window statistics, and cyclical time encodings (hour-of-day, day-of-week, seasonality indicators).

### 2. Behavioral Clustering & Household Load Profile Typology
* **The Question:** Can unsupervised machine learning algorithms cluster individual consumer days into distinct operational profiles (e.g., heavy daytime baseline vs. evening peak-heavy) to reveal structural household behaviors?
* **Data Science Approach:** Utilizing dimensionality reduction (PCA) followed by density-based or centroid clustering (e.g., K-Means, DBSCAN) on normalized daily load curves to segment usage archetypes and identify atypical anomaly days.

### 3. Anomaly Detection & Sensor Telemetry Reliability
* **The Question:** How can we robustly distinguish between genuine high-appliance usage spikes and anomalous sensor dropouts, missing telemetry, or meter miscalibrations in high-frequency streams?
* **Data Science Approach:** Constructing isolation forests and rolling statistical bounds (Z-scores over moving medians) to flag anomalous electrical dropouts and evaluate imputation fidelity without introducing synthetic bias.

### 4. Economic Disaggregation & Unmetered Power Auditing
* **The Question:** What percentage of total active power consumption remains unaccounted for by dedicated sub-meters (kitchen, laundry, water heating), and how does this "remainder" fluctuate relative to voltage sags and grid intensity changes?
* **Data Science Approach:** Deriving residual energy bounds through vectorised feature engineering, and analyzing multivariate correlations between voltage drops, reactive power imbalances, and unallocated baseline draws.

## 🔍 Phase 1: Data Understanding, Cleaning & Data Quality

### Step 1.1: Source Verification & Data Contract Execution

Before performing any data transformations, Phase 1 establishes a strict data contract by verifying file integrity, size, encoding, and delimiter structures directly from the raw data source.

* **File Name & Footprint:** Verified that `household_power_consumption.csv` sits correctly in the workspace directory with a total file size of **47.03 MB**.
* **Delimiter Analysis:** Inspected raw bytes to confirm that fields are separated using semicolons (`;`) rather than standard commas, establishing the parsing schema for downstream pipeline ingestion.
* **Initial Telemetry Inspection:** Successfully captured the raw header layout and baseline sample row without loading the full ~2 million rows into memory prematurely.

#### Execution Output Snapshot
Below is the verification output captured during the execution of the source inspection module in the Jupyter Notebook environment:

![Source Verification Output Snapshot](Screenshot%20(337).png)

### Step 1.2: Parsing, Types & Timestamp Construction

Following source verification, Phase 1.2 ingested the minute-level telemetry using flexible delimiter detection, parsed datetime structures, and enforced strict data type constraints.

* **Schema Ingestion:** Successfully loaded **1,048,575 observations** across all 9 expected electrical telemetry columns.
* **Timestamp Construction:** Combined the raw `Date` and `Time` text fields into a standardized, timezone-independent datetime index (`%d/%m/%Y %H:%M:%S`) with **0 unparseable failures**.
* **Type Conversion & Memory Hygiene:** Converted all electrical load variables (`Global_active_power`, `Voltage`, `Sub_metering_*`, etc.) into explicit 64-bit floating-point arrays (`float64`), dropping redundant string columns to optimize memory efficiency.

#### Execution Output Snapshot
Below is the parsing verification and dtype profile captured during the execution of Step 1.2:

![Parsing and Types Output Snapshot](Screenshot%20(339).png)

### Phase 1.3: Rigorous Missingness Analysis & Telemetry Treatment

In high-frequency electrical telemetry systems, missing values are rarely random; they reflect physical grid failures, sensor communication drops, or local brownouts. Rather than applying blind global imputations that destroy variance, Phase 1.3 implemented a context-aware data hygiene protocol.

#### Key Analytical Findings
* **Uniform Sensor Dropouts:** Quantified null distributions across all features, revealing an identical 4,069 missing records (`0.38805%` data loss) uniformly synchronized across every electrical sensor column.
* **Contiguous Outage Profiling:** Isolated 39 distinct contiguous missing blocks. The analysis surfaced a maximum contiguous outage duration of **3,723 minutes (62.0 hours)**, mapping directly to severe grid blackout events.
* **Treatment Architecture:** 
  * **Short Gaps ($\le 60$ mins):** 36 short sensor dropouts were successfully addressed via bounded linear time-interpolation.
  * **Long Outages ($> 60$ mins):** 3 major outages were strictly quarantined as `NaN` values rather than blindly fabricated, paired with an engineered binary `GAP_Indicator` feature to preserve missingness topology for downstream machine learning models.

#### Execution Output Snapshot
Below is the missingness quantification and treatment audit trail captured during the execution of Phase 1.3:

![Missingness Analysis and Treatment Output](Screenshot%20(340).png)

### Phase 1.4: Duplicate, Invalid, and Inconsistent Records Audit

To guarantee absolute data integrity before building downstream forecasting models, Phase 1.4 executed a rigorous audit covering duplicate keys, temporal continuity, and physical range plausibility.

#### Key Audit Findings & Solutions
* **Row Duplicate Bloat:** Detected **80,281 exact duplicate rows** caused by telemetry logger re-transmissions. 
  * *Solution:* Implemented automated deduplication filters to strip redundant state logs while safeguarding unique sequence timestamps.
* **Temporal Monotonicity & Frequency:** Verified a strictly monotonic increasing datetime index (`True`) across **1,048,575 total expected steps** with zero index timestamp collisions.
* **Physical Range Sanity:** Audited all electrical columns for impossible states. Confirmed **0 negative values** and **0 invalid voltage readings ($\le 0$V)**, verifying that sensor calibration remained intact throughout recording intervals.

#### Execution Output Snapshot
Below is the integrity audit trail captured during the execution of Phase 1.4:

![Data Integrity Audit Output](Screenshot%20(344).png)

### Phase 1.5: Outlier Detection, Investigation, and Temporal Profiling

To prevent the destruction of valid high-load events, Phase 1.5 deployed a robust `3.0 * IQR` upper-fence policy alongside behavioral and temporal profiling.

#### Key Findings & Insights
* **Distribution Fences:** Established a baseline $Q_1$ of **0.312 kW**[cite: 2] and $Q_3$ of **1.608 kW** ($IQR = 1.296$ kW)[cite: 2], isolating extreme values safely above conservative upper bounds.
* **Behavioral Validation:** Isolated peak extreme outlier counts at **Hour 21 (9:00 PM)** (logging **866 extreme events**)[cite: 2], confirming that structural power spikes map directly to household evening routines (e.g., cooking, heating, high-draw appliances) rather than equipment malfunction.
* **Integrity Safeguard:** Retained raw telemetry values intact while logging binary outlier indicators (`Outlier_Flag_Extreme`), ensuring reproducible modeling and unbiased forecasting sensitivity audits.

#### Execution Output Snapshot
Below is the execution log verifying the Phase 1.5 statistical metrics and peak hour concentration:

![Outlier Detection Output](Screenshot%20(346).png)
### Phase 1.6: Electrical Consistency, Unit Conversions, and Derived Measures

Phase 1.6 translated raw kilowatt metrics into standardized interval-safe energy totals and audited the household sub-metering reconciliation balance across the 1-minute telemetry stream.

#### Key Engineering Findings & Metrics
* **Energy Unit Conversion:** Successfully converted instantaneous active power into interval energy, recording a mean derived active energy of **19.57 Wh/min** across **968,294 valid records**[cite: 3].
* **Sub-Metering Reconciliation:** Compared total energy against explicit sub-meter circuits (mean sum of **9.17 Wh/min**)[cite: 3] to isolate unmeasured residual loads (Sub-metering 4).
* **Residual Sanity Audit:** Detected only **935 negative residual anomalies (0.10%)**[cite: 3], confirming exceptional internal consistency well within acceptable multi-phase residential meter rounding limits.

#### Execution Output Snapshot
Below is the verification log capturing the Phase 1.6 derivation and reconciliation metrics:

![Electrical Consistency Audit Output](Screenshot%20(347).png)
### Phase 1.7: Automated Cleaning Pipeline, Quality Gates, and Parquet Export

The final phase of the data understanding and cleaning module engineered an idempotent, modular Python pipeline. This pipeline orchestrates Phases 1.2 through 1.6 into a single end-to-end execution stream, enforcing strict automated quality gates and serializing the results into high-performance columnar storage.

#### Pipeline Architecture & Transformation Lineage
* **Modular & Idempotent Execution:** Designed to be rerun seamlessly from raw CSV inputs without state corruption or duplicate index collisions.
* **Automated Quality Gates:** Programmatically enforced strict assertions verifying temporal monotonicity (`is_monotonic_increasing == True`) and physical sensor safety limits (`Voltage > 0`).
* **Optimized Columnar Storage:** Serialized the final validated dataset into an industry-standard **Apache Parquet** file (`cleaned_household_power.parquet`) using snappy compression for rapid downstream data science and modeling workflows.

#### Execution Lineage Summary
* **Raw Input Rows:** 1,048,575 records ingested[cite: 4]
* **Rows After Datetime Parse:** 1,048,575 records[cite: 4]
* **Missing Gaps Flagged & Treated:** 4,069 gaps isolated and interpolated[cite: 4]
* **Exact Duplicates Removed:** 80,281 duplicate records stripped[cite: 4]
* **Final Cleaned Rows Retained:** 968,294 records[cite: 4]
* **Extreme Outliers Flagged:** 6,996 high-load anomalies tagged with raw values preserved[cite: 4]

#### Pipeline Execution Output Snapshot
Below is the execution log verifying the successful completion of the master cleaning pipeline, quality gates, and Parquet export:

![Phase 1.7 Master Cleaning Pipeline Output](Screenshot%20(348).png)

### Executive Summary: Data Cleaning & Telemetry Quality Scorecard

In enterprise data science and smart grid infrastructure, deploying machine learning forecasting models or capacity-planning algorithms on raw, unvalidated telemetry introduces severe risks—ranging from phantom load errors and skewed rolling averages to model collapse caused by timestamp duplicates and sensor drift. 

This scorecard establishes an institutional **Data Quality Assurance (QA) framework** for Kenyan household electrical telemetry. By applying a **"Do No Harm" engineering methodology**, we transformed raw, high-frequency smart meter logs into an enterprise-ready, immutable Apache Parquet asset without destroying valid residential usage peaks or introducing artificial bias.

---

### Visual Evidence: Quality Scorecard & Pipeline Impact

![Data Cleaning Quality Scorecard](cleaning_pipeline_quality_scorecard.png)

---

### Comprehensive Breakdown of Business Solutions & Visual Insights

#### 1. Cleaning Impact Waterfall (Row Counts & Ingestion Integrity)
* **The Business Problem:** Raw IoT and smart-meter streams frequently suffer from systemic data loss, transmission packet duplication, and incomplete logging blocks that corrupt aggregations.
* **The Solution:** We tracked the exact lifecycle of every record across four rigorous processing gates:
  1. **Raw Ingested:** Initial ingestion stream capturing raw multi-sensor telemetry.
  2. **After Null Drop:** Removal of invalid timestamp anomalies and unrecoverable null blocks.
  3. **After Deduplication:** Elimination of **80,281 exact duplicate rows** and timestamp index collisions to ensure strict temporal uniqueness.
  4. **Final Cleaned:** A pristine, high-integrity dataset of **968,294 rows** optimized for downstream time-series forecasting.
* **Business Impact:** Prevents double-counting of power consumption metrics, ensuring financial and billing audits reconcile with absolute mathematical precision.

#### 2. Outlier Proportion Ratio ($3.0 \times IQR$ Robust Fencing)
* **The Business Problem:** Standard automated pipelines use aggressive $1.5 \times IQR$ fences or blind deletion, which mistakenly flags heavy legitimate appliance usage (e.g., electric water heaters, heavy cookers) as "errors" and deletes critical high-load training data.
* **The Solution:** We deployed a conservative **$3.0 \times IQR$ upper fence**, separating normal household baseline fluctuations from extreme sensor anomalies while **preserving raw values** and appending a binary tracking flag (`Outlier_Flag_Extreme`).
* **Business Impact:** The chart proves that **99.3%** of records represent normal operational load, while only **0.7%** are flagged as extreme anomalies[cite: 5]. This guarantees that our machine learning models retain peak load behavior without being distorted by erratic spikes.

#### 3. Energy Distribution Analysis ($\text{Wh/min}$)
* **The Business Problem:** Raw telemetry provides instantaneous active power in kilowatts ($kW$). Directly summing or averaging $kW$ across intervals leads to fundamental unit errors and distorted energy billing models.
* **The Solution:** We standardized electrical units by converting instantaneous power into interval energy ($\text{Wh/min} = \frac{\text{kW} \times 1000}{60}$) and cross-audited sub-metering circuit reconciliation.
* **Business Impact:** Establishes a unimodal, right-skewed energy distribution typical of residential consumption profiles, verifying that baseline household power consumption clusters safely within expected physical boundaries.

#### 4. Extreme Outliers Concentration by Hour (Behavioral Profiling)
* **The Business Problem:** Are extreme spikes caused by sensor malfunctions (which happen randomly across time), or do they reflect actual human behavior and household routines?
* **The Solution:** Grouping extreme outliers by hour of the day ($0–23$) revealed a massive concentration during **Hours 19, 20, and 21 (7:00 PM – 9:00 PM)**, peaking near **1,000 extreme occurrences**[cite: 5].
* **Business Impact:** This proves that extreme power events are **not sensor errors**, but rather structural human activity patterns (residents returning home, simultaneously powering cooking appliances, lighting, and entertainment systems). Understanding this temporal clustering allows utility providers and predictive models to accurately forecast evening peak-load grid demands.

### Module 2.1: Core Python and Project Engineering Architecture

To transition away from monolithic, ad-hoc notebook scripting toward professional software engineering standards, Module 2.1 establishes a reproducible project structure, decouples execution paths from local hardware environments, and encapsulates core data operations into robust, typed, and exception-handled Python functions.

#### Key Architectural Highlights & Specifications
- **Cross-Platform Pathing:** Utilized Python’s native `pathlib` library (`Path().resolve()`) to dynamically compute absolute project directories, ensuring seamless cross-platform compatibility across Windows, macOS, and Linux without fragile hardcoded paths.
- **Centralized Logging Framework:** Replaced standard `print()` statements with a configured `logging` pipeline (`PowerTelemetryPipeline`) capturing precise timestamps, severity levels (`INFO`), and execution states.
- **Modular Ingestion (`load_telemetry_data`):** Validates file existence prior to execution, safely handles semicolon-delimited CSV payloads (`sep=';'`), maps unknown value markers (`?`) to standard nulls (`NaN`), and incorporates structured `try/except` exception safety with critical error reporting.
- **Vectorized Timestamp Parsing (`parse_timestamps`):** Combines raw `Date` and `Time` string columns into a unified datetime series (`%d/%m/%Y %H:%M:%S`) with error coercion (`errors='coerce'`), promotes `DateTime` to an immutable DataFrame index, and purges redundant raw text columns.

#### Detailed Explanation of Execution Output & Logs
The terminal outputs captured during runtime validate three critical pillars of institutional software engineering:
1. **Absolute Traceability & Transparency:** The logging framework timestamps every execution phase down to the millisecond (`[INFO]`), providing clear visibility into file system lookups and ingestion progress without relying on opaque `print()` statements.
2. **Mass-Scale Memory Handling:** The `load_telemetry_data` function successfully ingests **1,048,575 raw records** from the high-frequency smart meter dataset in seconds, handling semicolon boundaries and missing-value flags safely without buffer overflows.
3. **Time-Series Index Readiness:** The execution shape verification `(1048575, 7)` confirms that raw text columns were successfully transformed into a vectorized, immutable Datetime Index, establishing the exact temporal grid required for advanced modeling and forecasting pipelines.

#### Execution Output Snapshots
Below are the runtime verification logs capturing environment initialization, logging setup, and high-performance ingestion:

##### 1. Environment & Logger Initialization
![Module 2.1 Environment and Logging Setup](Screenshot%20(349).png)

##### 2. Modular Ingestion & Datetime Indexing Output
![Module 2.1 Runtime Verification & Execution Logs](Screenshot%20(350).png)

---
### Module 2.2: NumPy, Pandas, and Efficient Computation

To scale data pipelines beyond ad-hoc scripting, Module 2.2 transitions our architecture into high-performance, memory-optimized computation. This phase masters hardware-level vectorization, vectorized time-series resampling, leakage-free rolling windows, and rigorous memory profiling to eliminate RAM bottlenecks when processing large-scale telemetry.

#### Key Architectural Focus & Trade-Offs
- **Vectorized Operations vs. Python Loops:** Bypassed slow, row-by-row Python interpreter `for` loops by leveraging contiguous memory arrays and compiled C-routines via NumPy and Pandas vectorization.
- **`groupby` vs. `resample` Mechanics:** Utilized categorical `groupby` for discrete attribute partitioning while deploying specialized temporal `resample` engines for continuous time-series frequency conversion and automated bin filling.
- **Leakage Prevention in Windows:** Enforced strict chronological sorting, historical shifting (`.shift(1)`), and bounded window configurations (`closed='left'`) to prevent future data leakage in rolling calculations.
- **Memory Profiling & Dtype Optimization:** Audited RAM allocation across data types, demonstrating how object-dtype string overhead and float precision choices impact large-scale memory footprints.

#### Detailed Explanation of Memory Benchmark Output
The execution output captured in the memory profiling benchmark reveals critical insights into dataframe memory allocation:
1. **Initial Memory Baseline:** Loading the raw telemetry dataset established a base memory footprint of **53.03 MB**. 
2. **Dtype Profiling & Allocation Reality:** While downcasting continuous numerical variables from `float64` to `float32` cuts numeric precision storage in half, the output demonstrates that string-based `object` dtypes (such as raw `Date` and `Time` columns prior to datetime parsing) often dominate the initial RAM overhead. 
3. **Engineering Takeaway:** True memory optimization in large-scale data engineering requires a combined strategy: downcasting numerical arrays *alongside* converting repetitive string columns into efficient `category` dtypes and parsing temporal fields into datetime indexes.

#### Execution Output Snapshot
Below is the live memory benchmark and dtype optimization log captured during execution:
### Module 2.3: Visualization Libraries, Chart Literacy, and Exploratory Telemetry Analysis

To bridge raw data engineering pipelines with executive-ready decision-making, Module 2.3 establishes an institutional-grade visualization framework using `matplotlib` and `seaborn`. This module moves beyond basic plotting to enforce strict chart literacy standards: pairing distribution metrics with KDE skewness curves, handling continuous time-series resampling at hourly grain, and embedding explicit annotations to communicate both statistical findings and data caveats.

#### 1. Architectural & Visual Design Standards
- **Multi-Panel Analytical Layouts:** Designed synchronized subplots separating distribution density from temporal trajectories.
- **Explicit SI Unit Labeling & Metadata:** Enforced standard metric units (Kilowatts - kW) and datetime grain annotations across all axes to eliminate ambiguity for stakeholders.
- **Annotation & Caveat Integration:** Embedded explicit text callouts directly onto graphical canvases to highlight structural distribution tails and macro-trend volatility.

#### 2. Deep-Dive Analysis of Visualization Output
The generated output artifact captures two vital dimensions of the household electrical telemetry dataset:

* **Figure 2.1: Global Active Power Distribution & Skewness Analysis**
  - *Statistical Insight:* The histogram and Kernel Density Estimation (KDE) plot reveal a heavily right-skewed distribution. The primary concentration of residential power draw clusters tightly between $0.2\text{ kW}$ and $1.0\text{ kW}$, representing baseline idle and low-appliance loads.
  - *The Long Tail & Business Meaning:* A pronounced positive skew extends past $4.0\text{ kW}$ and up to $10\text{ kW}$. As annotated on the chart, this long tail captures high-load residential peak events (such as heavy heating, water boiling, or multi-appliance concurrency), signaling critical capacity thresholds for local microgrid planning.

* **Figure 2.2: Hourly Resampled Household Power Consumption Trend**
  - *Temporal Mechanics:* High-frequency 1-minute telemetry was resampled to an hourly mean grain (`.resample('h').mean()`) to eliminate high-frequency noise while preserving macro-trend seasonality.
  - *Trend & Anomaly Detection:* The timeline exposes pronounced seasonal shifts across the multi-year span (2007–2009), alongside visible data gaps and drops during mid-2008. This visual proof enables engineers to verify resampling integrity and isolate telemetry dropout windows prior to predictive modeling.

#### 3. Execution Artifact & Visual Evidence
Below is the production-ready visualization output generated from the pipeline and committed directly to the repository:

![Module 2.3 Visualization Gallery - Distribution Skewness and Hourly Trends](output%201.png)


### Module 2.4: Correlation Matrices, Multi-Collinearity Diagnostics, and Feature Engineering

Raw electrical telemetry often contains redundant signals, physical constraints, and subtle load-voltage interactions that can distort statistical models or cause severe multi-collinearity in linear and regression-based forecasting. Module 2.4 pairs cyclical time-based feature engineering (`Hour`, `Month`, `DayOfWeek`, `Is_Weekend`) with a Pearson correlation matrix to diagnose feature relationships, validate electrical physics, and guide smart feature selection before modeling[cite: 2].

---

#### 1. The Engineering Problem & Why Correlation Analysis Matters
When building predictive load or energy-consumption models from smart-meter telemetry, feeding every numeric column blindly into a model creates two major problems:
1. **Redundancy & Multi-Collinearity:** Variables driven by the same underlying physical process can carry nearly identical information, inflating variance in linear models and obscuring true feature importance.
2. **Misinterpreting Grid & Appliance Behavior:** Without checking how sub-circuits and line voltage respond to rising household demand, analysts risk mistaking normal voltage sag or independent appliance cycles for sensor faults or anomalies[cite: 2].

---

#### 2. Deep-Dive Output Analysis: Why the Numbers Look This Way

##### A. Near-Perfect Coupling Between `Global_active_power` and `Global_intensity` ($r = 1.00$ rounded)
* **What the Matrix Shows:** `Global_active_power` and `Global_intensity` display a correlation of `1.00` (at two-decimal precision)[cite: 2].
* **Why This Happens (Physical & Statistical Reason):** Active electrical power ($P$) is directly governed by current ($I$) and voltage ($V$) ($P = V \cdot I \cdot \cos\theta$). Because household supply voltage stays within a relatively narrow operating band compared to wide swings in appliance current, current (`Global_intensity`) tracks `Global_active_power` almost lockstep.
* **Modeling Solution:** Using both `Global_active_power` and `Global_intensity` simultaneously as predictors creates strong multi-collinearity. In forecasting or regression tasks, retain the target/primary load metric and avoid redundant collinear inputs unless regularized or dimensionally reduced.

##### B. Sub-Metering Drivers: Why `Sub_metering_3` Leads ($r = 0.61$) While Sub-Meters Stay Independent ($r \approx 0.06\text{--}0.11$)
* **What the Matrix Shows:** Among the three sub-metered zones, `Sub_metering_3` has the strongest linear relationship with `Global_active_power` ($r = 0.61$), followed by `Sub_metering_1` ($r = 0.48$) and `Sub_metering_2` ($r = 0.46$)[cite: 2]. Meanwhile, correlations *between* `Sub_metering_1`, `Sub_metering_2`, and `Sub_metering_3` are all weak (`0.06` to `0.11`)[cite: 2].
* **Why This Happens (Behavioral & Circuit Reason):** Heavy fixed loads (such as water heating, climate/space conditioning, or major continuous circuits represented by sub-meter 3) account for a large share of total kW draw when active. Conversely, different household zones are used at different times or for distinct tasks rather than turning on identically together, keeping cross-sub-meter linear correlation low.
* **Modeling Solution:** Each sub-meter captures distinct appliance/zone behavior and adds complementary signal rather than duplicating another sub-meter—making sub-meter aggregates and lagged values useful features for peak-load profiling.

##### C. Negative Correlation with `Voltage` ($r = -0.40$ with `Global_active_power`, $-0.41$ with `Global_intensity`)
* **What the Matrix Shows:** `Voltage` correlates negatively with `Global_active_power` ($r = -0.40$) and `Global_intensity` ($r = -0.41$), and mildly negatively with the sub-meters ($-0.18$ to $-0.28$)[cite: 2].
* **Why This Happens (Grid Load & Voltage Drop Reason):** In real distribution networks with non-zero line impedance, heavier current draw across feeders and household circuits increases voltage drop along the line, causing measured voltage to dip slightly during high-load periods.
* **Modeling Solution:** A moderate negative correlation with voltage is physically expected during heavy demand—it is a real grid load effect, not automatically a data-cleaning error. Including `Voltage` alongside demand/time features helps models distinguish high-load stress periods from quiet baseline periods.

##### D. Weak Link with `Global_reactive_power` ($r = 0.21$ with `Global_active_power`)
* **What the Matrix Shows:** `Global_reactive_power` shows only a modest positive correlation (`0.21`) with `Global_active_power` and near-zero correlation (`0.04`) with `Sub_metering_3`[cite: 2].
* **Why This Happens:** Reactive power reflects phase shift from inductive/capacitive loads rather than real energy transferred for work, so active kW and reactive kVAR do not scale identically across all household appliances.
* **Modeling Solution:** Keep `Global_reactive_power` as a separate diagnostic signal for power-quality/inductive-load context rather than assuming it moves proportionally with active power.

---

#### 3. Visual Artifact: Telemetry Feature Correlation Matrix

![Figure 2.3: Telemetry Feature Correlation Matrix](correlation_matrix_heatmap.png)

### Phase 3, Section 3.1: Descriptive Statistics Setup & Feature Enrichment (`03_1_descriptive_statistics_and_load_profiles.ipynb`)

Before computing formal descriptive statistics, probability distributions, and conditional load profiles, raw telemetry records need structured temporal context and consistent load-tier labels. In `03_1_descriptive_statistics_and_load_profiles.ipynb`, the cleaned Parquet dataset is loaded, chronologically indexed, enriched with calendar/time features, and segmented into quartile-based load regimes[cite: 2].

---

#### 1. Problem Solved by This Initialization Step
1. **Chronological & Type Consistency:** Reading from the cleaned Parquet pipeline preserves high-volume telemetry (`968,294` rows across `18` columns) while ensuring timestamps are sorted along a `DatetimeIndex` and active power (`Global_active_power`) is numeric[cite: 2].
2. **Actionable Grouping Dimensions:** Extracting `Hour`, `DayOfWeek`, `Weekday_Name`, `Month`, and `Month_Name` enables direct comparison across daily demand cycles, weekdays vs. weekends, and seasonal shifts[cite: 2].
3. **Quantile Load Regimes (`Load_Regime`):** Partitioning active power into four equal-frequency quartile tiers (`Q1: Low/Idle`, `Q2: Moderate`, `Q3: Elevated`, and `Q4: Peak Draw`) establishes a clear baseline for comparing baseline idle behavior against high-demand draw periods[cite: 2].

---

#### 2. Output Walkthrough & Engineering Interpretation
From the executed notebook cell[cite: 2]:
* **Dataset Scale & Target Column:** The DataFrame loads with shape `(968294, 18)` and resolves `'Global_active_power'` as the primary target telemetry column in `17.4s`[cite: 2].
* **Sample Evening Peak Observations:** The preview table shows Saturday evening readings around `17:24`–`17:28` in `Dec` (`2006-12-16`) with `Global_active_power` values between `3.666` and `5.388` kW—all automatically classified under `Q4: Peak Draw`[cite: 2].
* **Why This Matters for Downstream Analysis:** Labeling observations by `Hour` and `Load_Regime` upfront prevents mixing quiet overnight draws with heavy evening/weekend demand spikes when summarizing central tendency, spread, skewness, and tail behavior[cite: 2].

---

#### 3. Visual Evidence: Notebook Execution & Feature Preview

![Section 3.1 Setup and Output Preview in VS Code](Screenshot%20(353).png)

### Phase 3, Section 3.1 (Step 2): Baseline Descriptive Statistics & Distribution Shape (`Global_active_power`)

Raw household power series often look deceptively simple when summarized by a single average, yet electrical load demand is shaped by idle baselines, intermittent heavy appliances, and high-draw spikes[cite: 3]. Step 2 computes a complete baseline statistical profile across `967,828` valid `Global_active_power` observations to establish typical demand, spread, asymmetry, and tail behavior[cite: 3].

---

#### 1. Problem Solved & Analytical Purpose
1. **Avoiding Single-Metric Distortion:** Relying only on the mean can overstate typical household draw when high-power spikes pull the average upward[cite: 3].
2. **Quantifying Real Spread vs. Extreme Spikes:** Comparing parametric spread (`Std Deviation`, `Variance`, `Range`) against resistant/robust spread (`IQR`, `MAD` around median) separates routine fluctuations from peak events[cite: 3].
3. **Diagnosing Distribution Shape Before Modeling:** Measuring `Skewness`, `Excess Kurtosis`, `Pearson Kurtosis`, and `Coefficient of Variation (CV)` tells us whether load data is symmetric or skewed and how heavily tails behave before building forecasts or load regimes[cite: 3].

---

#### 2. Output Breakdown & Why the Numbers Behave This Way

| Metric | Value | Analytical Meaning |
| :--- | :--- | :--- |
| **Count (Valid)** | `967828.0000`[cite: 3] | Non-null active power observations evaluated[cite: 3]. |
| **Mean** | `1.1744`[cite: 3] | Arithmetic average active power[cite: 3]. |
| **Median (Q2)** | `0.6880`[cite: 3] | Middle (50th percentile) active power; typical routine draw[cite: 3]. |
| **Mode (1st)** | `0.3220`[cite: 3] | Most frequent single active power reading[cite: 3]. |
| **Min / Max / Range** | `0.0760` / `10.6700` / `10.5940`[cite: 3] | Full observed span from near-idle draw to peak load[cite: 3]. |
| **Q1 (25th) / Q3 (75th)** | `0.3120` / `1.6080`[cite: 3] | Bounds of the middle 50% of observations[cite: 3]. |
| **IQR (`Q3 - Q1`)** | `1.2960`[cite: 3] | Interquartile spread across the central half of the data[cite: 3]. |
| **Variance / Std Deviation** | `1.3096` / `1.1444`[cite: 3] | Overall dispersion around the mean (`ddof=1`)[cite: 3]. |
| **MAD (Mean / Median)** | `0.8801` / `0.4880`[cite: 3] | Average absolute deviation from mean vs. median absolute deviation[cite: 3]. |
| **Skewness** | `1.7022`[cite: 3] | Strong positive (right) skew[cite: 3]. |
| **Excess / Pearson Kurtosis** | `3.5745` / `6.5745`[cite: 3] | Leptokurtic (heavy upper tail / sharp peak relative to normal)[cite: 3]. |
| **Coeff. of Variation (CV)** | `0.9745`[cite: 3] | Standard deviation is nearly equal (`~97.5%`) to the mean[cite: 3]. |
| **95th / 99th Percentile** | `3.5700` / `5.1680`[cite: 3] | High-demand thresholds reached in the top 5% and top 1% of intervals[cite: 3]. |

##### Why Mean (`1.1744`) Is Much Higher Than Median (`0.6880`) and Mode (`0.3220`)
* **Reason:** Household electricity usage has a natural floor near low/idle consumption (`Min = 0.0760`, `Mode = 0.3220`, `Median = 0.6880`), while high-wattage appliances and peak periods push readings up to `10.6700`[cite: 3]. Because the arithmetic mean weights every value linearly, those upper-tail spikes pull the mean (`1.1744`) well above the median (`0.6880`), producing a positive skewness of `1.7022`[cite: 3].
* **Solution:** Use the **median** (`0.6880`) and **IQR** (`1.2960`) / **median MAD** (`0.4880`) to represent typical day-to-day baseline load, while keeping the **mean**, **95th percentile** (`3.5700`), and **99th percentile** (`5.1680`) in mind for capacity and peak-load planning[cite: 3].

##### Why Kurtosis (`Excess = 3.5745`, `Pearson = 6.5745`) and CV (`0.9745`) Are High
* **Reason:** A normal distribution has `Excess Kurtosis = 0` (`Pearson = 3`). Values of `3.5745` and `6.5745` confirm heavier tails and sharper concentration/peakedness than a Gaussian curve—consistent with frequent low-to-moderate baseline intervals punctuated by concentrated bursts of heavy appliance draw[cite: 3]. A `CV` of `0.9745` further shows that dispersion is large relative to average load[cite: 3].
* **Solution:** Avoid assuming normality for raw `Global_active_power` in parametric tests or naive linear assumptions; rely on quantile/regime segmentation (`Q1`–`Q4`), non-parametric/robust summaries, or appropriate transformations/time-aware models in later steps[cite: 3].

---

#### 3. Visual Evidence: Step 2 Descriptive Statistics Table

![Step 2 Descriptive Statistics Summary Output in VS Code](Screenshot%20(354).png)

### Phase 3, Section 3.1 (Step 3): Conditional Load Profiles & Sub-Metering Behavior

Overall descriptive statistics summarize total power demand, but household consumption shifts strongly across time of day, calendar days, and individual circuit branches[cite: 3]. Step 3 breaks `Global_active_power` down by `Hour` and `Weekday_Name` while evaluating zero-load intermittency across `Sub_metering_1`, `Sub_metering_2`, and `Sub_metering_3`[cite: 3].

---

#### 1. Problem Solved & Analytical Purpose
1. **Pinpointing High-Demand Windows:** Identifying top hours by `mean` and `max_peak` shows when sustained household demand and sharp spikes occur rather than averaging everything into a single daily figure[cite: 3].
2. **Comparing Central Tendency vs. Spread:** Tracking `median`, `std`, `var`, `iqr`, and `CV` reveals how consistent or volatile each hour and weekday is[cite: 3].
3. **Measuring Circuit Intermittency:** Calculating `zero_share_pct` across sub-meters distinguishes continuous/recurring loads from appliances that sit idle most of the time[cite: 3].

---

#### 2. Output Breakdown, Reasons & Solutions

##### A. Top 5 Hours by MEAN Active Power (`Global_active_power`)
* **Hour 21 (`9 PM`):** `mean = 2.051`, `median = 1.868`, `std = 1.385`, `iqr = 1.874`, `max_peak = 9.410` across `42,208` observations[cite: 3].
* **Hour 20 (`8 PM`):** `mean = 2.038`, `median = 1.776`, `std = 1.461`, `iqr = 2.088`, `max_peak = 10.348` across `42,285` observations[cite: 3].
* **Hour 19 (`7 PM`):** `mean = 1.883`, `median = 1.612`, `std = 1.449`, `iqr = 2.118`, `max_peak = 10.670` across `42,169` observations[cite: 3].
* **Hour 7 (`7 AM`):** `mean = 1.557`, `median = 1.498`, `std = 1.128`, `iqr = 1.842`, `max_peak = 9.486` across `40,873` observations[cite: 3].
* **Hour 22 (`10 PM`):** `mean = 1.546`, `median = 1.330`, `std = 1.185`, `iqr = 1.594`, `max_peak = 9.272` across `42,064` observations[cite: 3].
* **Reason:** Evening hours (`19:00`–`22:00`) combine occupancy, lighting, entertainment/cooking, and domestic routines, while `07:00` captures morning start-up activity[cite: 3].
* **Solution:** Treat `19:00`–`21:00` (and `07:00`) as primary peak/shoulder windows for load profiling, anomaly checks, and downstream forecasting features[cite: 3].

##### B. Top 5 Hours by PEAK (`MAX`) Active Power
* **Highest Single Peaks:** Hour `19` (`10.670`), Hour `20` (`10.348`), Hour `1` (`10.290`), Hour `17` (`9.590`), and Hour `7` (`9.486`)[cite: 3].
* **Reason:** Even when average load is modest—such as Hour `1` (`mean = 0.591`, `median = 0.328`, `iqr = 0.252`)—an occasional high-draw event (`max_peak = 10.290`) can push the maximum very high[cite: 3].
* **Solution:** Evaluate peak capacity and outlier/spike behavior alongside `median` and `iqr` so rare extreme readings do not distort typical hourly expectations[cite: 3].

##### C. Daily Variability & Central Tendency (`Weekday_Name`)
* **Visible Weekdays (`Monday`–`Thursday`):**
  * **Monday:** `mean = 1.058`, `median = 0.562`, `std = 1.017`, `var = 1.035`, `iqr = 1.178`, `max_peak = 9.486`, `CV = 0.961`[cite: 3].
  * **Tuesday:** `mean = 1.166`, `median = 0.660`, `std = 1.146`, `var = 1.314`, `iqr = 1.292`, `max_peak = 8.944`, `CV = 0.983`[cite: 3].
  * **Wednesday:** `mean = 1.132`, `median = 0.670`, `std = 1.075`, `var = 1.156`, `iqr = 1.258`, `max_peak = 8.974`, `CV = 0.950`[cite: 3].
  * **Thursday:** `mean = 1.040`, `median = 0.504`, `std = 1.038`, `var = 1.078`, `iqr = 1.164`, `max_peak = 9.410`, `CV = 0.998`[cite: 3].
* **Reason:** Across all four days, `mean` is substantially higher than `median` and `CV` stays close to `1.0` (`0.950`–`0.998`), reflecting right-skewed daily profiles where baseline periods are punctuated by higher-load intervals[cite: 3].
* **Solution:** Pair `median` and `iqr` with `std` and `CV` when comparing days, and ensure the full `Monday`–`Sunday` table (including Friday–Sunday) is inspected in full output[cite: 3].

##### D. Sub-Metering Zero Share (`zero_share_pct`)
* **`Sub_metering_1`:** `91.103%` zero readings (active only ~8.9% of intervals)[cite: 3].
* **`Sub_metering_2`:** `69.362%` zero readings (active ~30.6% of intervals)[cite: 3].
* **`Sub_metering_3`:** `51.967%` zero readings (active ~48.0% of intervals)[cite: 3].
* **Reason:** Different sub-metered circuits have different usage duty cycles—some are triggered intermittently while others operate more frequently across the dataset[cite: 3].
* **Solution:** Account for high zero-inflation (`52%`–`91%` zeros) when analyzing or modeling sub-metering series rather than treating them like continuous, always-on loads[cite: 3].

---

#### 3. Visual Evidence: Step 3 Conditional & Sub-Metering Output

![Step 3 Hourly, Daily, and Sub-Metering Output in VS Code](Screenshot%20(355).png)

### Phase 3, Section 3.1 (Visualizations): Distribution Shape, Weekly Load Regimes & Hourly Demand Profiles

Visualizing active power (`Global_active_power`) across density curves, cumulative distributions, weekday comparisons, quantile curves, and hourly profiles turns raw telemetry into operational intelligence[cite: 4, 5, 6]. Together, these three diagnostic plots address core business problems in **baseline tariff/usage estimation, peak-load capacity planning, weekend vs. weekday demand shifting, and time-of-day load management**.

---

#### 1. Active Power Density (Histogram + KDE) & Empirical CDF (`output 2.png`)

##### Business Problem Solved
Utilities, energy service providers, and household energy planners often misallocate capacity or misread typical customer consumption when relying solely on averages or assuming normal (bell-shaped) load behavior[cite: 4]. This view separates **everyday baseline load** from **high-demand tail events**[cite: 4].

##### Output Explanation
* **Left Panel — Histogram + KDE:** The distribution is strongly right-skewed with a prominent low-load cluster near `~0.25–0.35` kW and a secondary hump around `~1.3–1.5` kW, while a long right tail stretches past `6–10` kW[cite: 4]. The **Median (`0.69`)** sits well below the **Mean (`1.17`)**[cite: 4].
* **Right Panel — Empirical CDF (ECDF):** The cumulative curve climbs steeply at low power—crossing `0.50` (the median) well below `1.0` kW—before flattening gradually as it approaches `0.95` (the 95th percentile around `~3.5–3.6` kW) and `1.00`[cite: 4].

##### Why This Happens & Business Solution
* **Reason:** Households spend most intervals in low/idle or moderate multi-appliance states, while occasional heavy appliances or concurrent peak draws create a right-skewed upper tail that pulls the arithmetic mean (`1.17`) upward[cite: 4].
* **Business Solution:** Use the **median (`0.69`)** and **ECDF thresholds** (such as the 50th and 95th percentiles) rather than the mean alone to define normal baseline consumption, set realistic tier/alert thresholds, and size reserve/peak headroom for upper-tail demand spikes[cite: 4].

![Active Power Density and Empirical CDF](output%202.png)

---

#### 2. Day-of-Week Boxplots & Violins (`output 3.png`)

##### Business Problem Solved
Treating every day of the week as identical can mask higher weekend household demand and shift-driven load dispersion, leading to inaccurate weekly load schedules, maintenance windows, or demand-response targeting[cite: 5].

##### Output Explanation
* **Left Panel — Boxplots (Excluding Extreme Outliers):** Weekday medians (`Monday`–`Friday`) sit lower (roughly `~0.50–0.70` kW) with tighter upper whiskers, whereas **Saturday** and **Sunday** show higher medians (`~0.85–1.00` kW), wider boxes (`IQR`), and higher upper whiskers (`> 4.0` kW)[cite: 5].
* **Right Panel — Violin + Quartiles (Sampled):** Every day displays a wide base at low power with a secondary bulge higher up and a long, narrow upper tail extending toward `~8–9+` kW, confirming multi-regime appliance usage across the week[cite: 5].

##### Why This Happens & Business Solution
* **Reason:** On weekdays, daytime household occupancy and heavy appliance use are often lower or more concentrated into specific windows, whereas weekends (`Saturday` and `Sunday`) bring extended home presence, cooking, cleaning, and leisure load[cite: 5].
* **Business Solution:** Build **day-type-aware load profiles** (separating weekdays from weekends) for feeder scheduling, customer usage insights, and targeted off-peak/time-of-use nudges rather than applying a flat 7-day average[cite: 5].

![Active Power by Day of Week Boxplot and Violin Plot](output%203.png)

---

#### 3. Quantile Function & Hourly Mean Profile (`output 4.png`)

##### Business Problem Solved
Peak grid stress and household bill spikes are driven by specific hours of the day and extreme upper percentiles rather than uniform 24-hour demand[cite: 6]. Identifying exact high-load hours and percentile inflection points enables targeted peak management[cite: 6].

##### Output Explanation
* **Left Panel — Quantile Function (1st to 99th Percentile):** Power rises gently from the 1st to roughly the 50th percentile, steps up through moderate load, and curves sharply upward above the ~80th–90th percentiles up to `~5.17` kW at the 99th percentile[cite: 6].
* **Right Panel — Mean Active Power by Hour (`0–23`):** Demand is lowest overnight/early morning (`Hours 1–5`, around `~0.47–0.59` kW), rises sharply in the morning peak at **Hour 7 (`~1.56` kW)** and **Hour 8**, moderates through midday/afternoon (`~1.01–1.35` kW), and surges to a pronounced evening peak across **Hours 19–21 (`~1.88–2.05` kW)** before tapering off[cite: 6].

##### Why This Happens & Business Solution
* **Reason:** Daily human routines—waking/morning prep around `07:00`, daytime away/light load, and evening return/cooking/lighting around `19:00–21:00`—drive predictable diurnal waves, while simultaneous heavy loads create steep upper-quantile jumps[cite: 6].
* **Business Solution:** Focus peak-load mitigation, time-of-use tariff design, and high-load alerts on the **evening peak window (`19:00–21:00`)** and **morning ramp (`07:00–08:00`)**, while using **upper-percentile thresholds (90th–99th)** to trigger surge/overload safeguards[cite: 6].

![Quantile Function and Hourly Mean Active Power](output%204.png)