USE kenya_power_dw;

-- A. Unique timestamps, unique dates, and duplicate check via GROUP BY + HAVING
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT reading_ts) AS unique_timestamps,
    COUNT(DISTINCT DATE(reading_ts)) AS unique_dates,
    COUNT(*) - COUNT(DISTINCT reading_ts) AS duplicate_timestamp_rows
FROM stg_power_readings;

SELECT
    reading_ts,
    COUNT(*) AS occurrence_count
FROM stg_power_readings
WHERE reading_ts IS NOT NULL
GROUP BY reading_ts
HAVING COUNT(*) > 1
ORDER BY occurrence_count DESC, reading_ts;

-- B. Readings per year and month
SELECT
    YEAR(reading_ts) AS yr,
    MONTH(reading_ts) AS mo,
    COUNT(*) AS reading_count,
    COUNT(DISTINCT DATE(reading_ts)) AS active_days,
    ROUND(AVG(global_active_power), 4) AS mean_active_power_kw
FROM stg_power_readings
WHERE reading_ts IS NOT NULL
GROUP BY YEAR(reading_ts), MONTH(reading_ts)
ORDER BY yr, mo;

-- C. Missing or invalid measurements
SELECT
    reading_ts,
    global_active_power,
    voltage,
    global_intensity,
    sub_metering_1,
    sub_metering_2,
    sub_metering_3,
    CASE
        WHEN reading_ts IS NULL THEN 'MISSING_TIMESTAMP'
        WHEN global_active_power IS NULL THEN 'MISSING_ACTIVE_POWER'
        WHEN global_active_power < 0 THEN 'NEGATIVE_ACTIVE_POWER'
        WHEN voltage IS NOT NULL AND voltage <= 0 THEN 'NON_POSITIVE_VOLTAGE'
        WHEN sub_metering_1 < 0 OR sub_metering_2 < 0 OR sub_metering_3 < 0 THEN 'NEGATIVE_SUBMETER'
        ELSE 'VALID'
    END AS validation_status
FROM stg_power_readings
WHERE reading_ts IS NULL
   OR global_active_power IS NULL
   OR global_active_power < 0
   OR (voltage IS NOT NULL AND voltage <= 0)
   OR COALESCE(sub_metering_1, 0) < 0
   OR COALESCE(sub_metering_2, 0) < 0
   OR COALESCE(sub_metering_3, 0) < 0
ORDER BY reading_ts
LIMIT 500;

-- D. Days exceeding a chosen peak threshold (e.g., max active power > 6.0 kW)
SELECT
    DATE(reading_ts) AS reading_date,
    COUNT(*) AS n_readings,
    ROUND(AVG(global_active_power), 4) AS mean_kw,
    ROUND(MAX(global_active_power), 4) AS peak_kw
FROM stg_power_readings
WHERE global_active_power IS NOT NULL
GROUP BY DATE(reading_ts)
HAVING MAX(global_active_power) > 6.0
ORDER BY peak_kw DESC, reading_date;

-- E. Standardise, validate, and promote inside a safe transaction
START TRANSACTION;

INSERT IGNORE INTO fact_power_readings (
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
    CAST(reading_ts AS DATETIME) AS reading_ts,
    CAST(DATE_FORMAT(reading_ts, '%Y%m%d') AS UNSIGNED) AS date_key,
    1 AS batch_id,
    CAST(COALESCE(NULLIF(TRIM(CAST(global_active_power AS CHAR)), ''), 0) AS DECIMAL(10, 4)) AS global_active_power_kw,
    CAST(global_reactive_power AS DECIMAL(10, 4)),
    CAST(voltage AS DECIMAL(8, 3)),
    CAST(global_intensity AS DECIMAL(8, 3)),
    CAST(sub_metering_1 AS DECIMAL(10, 3)),
    CAST(sub_metering_2 AS DECIMAL(10, 3)),
    CAST(sub_metering_3 AS DECIMAL(10, 3))
FROM stg_power_readings
WHERE reading_ts IS NOT NULL
  AND global_active_power IS NOT NULL
  AND global_active_power >= 0;

COMMIT;