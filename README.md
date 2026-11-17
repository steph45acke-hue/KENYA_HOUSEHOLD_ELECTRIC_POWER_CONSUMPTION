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

> *"Empowering sustainable energy decisions through data-driven insight."*

