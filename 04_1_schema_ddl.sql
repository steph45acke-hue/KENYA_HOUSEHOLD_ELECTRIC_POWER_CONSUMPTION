CREATE DATABASE IF NOT EXISTS kenya_power_dw
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;
USE kenya_power_dw;

-- 1. Staging Table (Raw / Pre-Validation Landing)
CREATE TABLE IF NOT EXISTS stg_power_readings (
    stg_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    source_file VARCHAR(255) NOT NULL,
    raw_datetime_str VARCHAR(64) NOT NULL,
    reading_ts DATETIME NULL,
    global_active_power DOUBLE NULL,
    global_reactive_power DOUBLE NULL,
    voltage DOUBLE NULL,
    global_intensity DOUBLE NULL,
    sub_metering_1 DOUBLE NULL,
    sub_metering_2 DOUBLE NULL,
    sub_metering_3 DOUBLE NULL,
    ingested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_stg_reading_ts (reading_ts)
);

-- 2. Ingestion Batch Control Table
CREATE TABLE IF NOT EXISTS etl_ingestion_batch (
    batch_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    source_name VARCHAR(255) NOT NULL,
    started_at DATETIME NOT NULL,
    finished_at DATETIME NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'RUNNING',
    rows_read BIGINT UNSIGNED NOT NULL DEFAULT 0,
    rows_loaded BIGINT UNSIGNED NOT NULL DEFAULT 0,
    rows_rejected BIGINT UNSIGNED NOT NULL DEFAULT 0,
    CONSTRAINT chk_batch_status CHECK (status IN ('RUNNING', 'SUCCESS', 'FAILED', 'PARTIAL'))
);

-- 3. Calendar Date Dimension
CREATE TABLE IF NOT EXISTS dim_date (
    date_key INT UNSIGNED PRIMARY KEY,
    calendar_date DATE NOT NULL,
    year_num SMALLINT UNSIGNED NOT NULL,
    quarter_num TINYINT UNSIGNED NOT NULL,
    month_num TINYINT UNSIGNED NOT NULL,
    month_name VARCHAR(16) NOT NULL,
    day_of_month TINYINT UNSIGNED NOT NULL,
    day_of_week TINYINT UNSIGNED NOT NULL,
    day_name VARCHAR(16) NOT NULL,
    is_weekend TINYINT(1) NOT NULL,
    CONSTRAINT uq_dim_date UNIQUE (calendar_date),
    CONSTRAINT chk_is_weekend CHECK (is_weekend IN (0, 1))
);

-- 4. Fact Table: 1-Minute Household Power Readings
CREATE TABLE IF NOT EXISTS fact_power_readings (
    reading_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    reading_ts DATETIME NOT NULL,
    date_key INT UNSIGNED NOT NULL,
    batch_id BIGINT UNSIGNED NOT NULL,
    global_active_power_kw DECIMAL(10, 4) NOT NULL,
    global_reactive_power_kvar DECIMAL(10, 4) NULL,
    voltage_v DECIMAL(8, 3) NULL,
    global_intensity_a DECIMAL(8, 3) NULL,
    sub_metering_1_wh DECIMAL(10, 3) NULL,
    sub_metering_2_wh DECIMAL(10, 3) NULL,
    sub_metering_3_wh DECIMAL(10, 3) NULL,
    CONSTRAINT uq_fact_reading_ts UNIQUE (reading_ts),
    CONSTRAINT chk_active_power_nonneg CHECK (global_active_power_kw >= 0),
    CONSTRAINT chk_voltage_pos CHECK (voltage_v IS NULL OR voltage_v > 0),
    CONSTRAINT fk_fact_date FOREIGN KEY (date_key) REFERENCES dim_date (date_key),
    CONSTRAINT fk_fact_batch FOREIGN KEY (batch_id) REFERENCES etl_ingestion_batch (batch_id),
    KEY idx_fact_date_ts (date_key, reading_ts),
    KEY idx_fact_batch (batch_id)
);

-- 5. Data Quality Issue Log
CREATE TABLE IF NOT EXISTS etl_data_quality_issue (
    issue_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    batch_id BIGINT UNSIGNED NOT NULL,
    date_key INT UNSIGNED NULL,
    reading_ts DATETIME NULL,
    column_name VARCHAR(64) NULL,
    rule_code VARCHAR(64) NOT NULL,
    severity VARCHAR(16) NOT NULL DEFAULT 'WARN',
    issue_detail VARCHAR(500) NULL,
    detected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_dq_severity CHECK (severity IN ('INFO', 'WARN', 'ERROR')),
    CONSTRAINT fk_dq_batch FOREIGN KEY (batch_id) REFERENCES etl_ingestion_batch (batch_id),
    CONSTRAINT fk_dq_date FOREIGN KEY (date_key) REFERENCES dim_date (date_key),
    KEY idx_dq_batch_rule (batch_id, rule_code),
    KEY idx_dq_date (date_key)
);

-- 6. Daily Aggregate Table (One Row per Calendar Day)
CREATE TABLE IF NOT EXISTS agg_daily_power_summary (
    date_key INT UNSIGNED PRIMARY KEY,
    reading_count INT UNSIGNED NOT NULL,
    mean_active_power_kw DECIMAL(10, 4) NOT NULL,
    max_active_power_kw DECIMAL(10, 4) NOT NULL,
    total_energy_kwh DECIMAL(12, 4) NOT NULL,
    mean_voltage_v DECIMAL(8, 3) NULL,
    total_sub_meter_1_wh DECIMAL(12, 3) NULL,
    total_sub_meter_2_wh DECIMAL(12, 3) NULL,
    total_sub_meter_3_wh DECIMAL(12, 3) NULL,
    CONSTRAINT fk_agg_date FOREIGN KEY (date_key) REFERENCES dim_date (date_key)
);