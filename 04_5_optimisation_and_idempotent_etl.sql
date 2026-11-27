USE kenya_power_dw;

-- A. Composite Index for Range + Grouped Telemetry Queries
CREATE INDEX IF NOT EXISTS idx_fact_date_ts_power
    ON fact_power_readings (date_key, reading_ts, global_active_power_kw);

-- B. Inspect Execution Plan (Sargable Range Filter vs. Non-Sargable Function)
EXPLAIN ANALYZE
SELECT
    date_key,
    COUNT(*) AS n_readings,
    ROUND(AVG(global_active_power_kw), 4) AS avg_kw,
    ROUND(SUM(global_active_power_kw) / 60.0, 2) AS total_kwh
FROM fact_power_readings
WHERE reading_ts >= '2007-01-01 00:00:00'
  AND reading_ts <  '2007-04-01 00:00:00'
GROUP BY date_key
ORDER BY date_key;

-- C. Idempotent Incremental Upsert Pattern (Safe to Rerun Without Duplicates)
START TRANSACTION;

INSERT INTO etl_ingestion_batch (source_name, started_at, status, rows_read)
VALUES ('cleaned_household_power.parquet', NOW(), 'RUNNING', 0);
SET @batch_id = LAST_INSERT_ID();

INSERT INTO fact_power_readings (
    reading_ts,
    date_key,
    batch_id,
    global_active_power_kw,
    global_reactive_power_kvar,
    voltage_v,
    global_intensity_a,
    sub_metering_1_wh,
    sub_metering_2_wh,
    sub_metering_3_wh
)
SELECT
    reading_ts,
    CAST(DATE_FORMAT(reading_ts, '%Y%m%d') AS UNSIGNED) AS date_key,
    @batch_id,
    global_active_power,
    global_reactive_power,
    voltage,
    global_intensity,
    sub_metering_1,
    sub_metering_2,
    sub_metering_3
FROM stg_power_readings
WHERE reading_ts IS NOT NULL
  AND global_active_power IS NOT NULL
  AND global_active_power >= 0
ON DUPLICATE KEY UPDATE
    batch_id = VALUES(batch_id),
    global_active_power_kw = VALUES(global_active_power_kw),
    voltage_v = VALUES(voltage_v),
    sub_metering_1_wh = VALUES(sub_metering_1_wh),
    sub_metering_2_wh = VALUES(sub_metering_2_wh),
    sub_metering_3_wh = VALUES(sub_metering_3_wh);

UPDATE etl_ingestion_batch
SET finished_at = NOW(),
    status = 'SUCCESS',
    rows_loaded = ROW_COUNT()
WHERE batch_id = @batch_id;

COMMIT;