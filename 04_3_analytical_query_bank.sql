USE kenya_power_dw;

-- View: Daily Telemetry Summary
CREATE OR REPLACE VIEW v_daily_power_summary AS
SELECT
    d.date_key,
    d.calendar_date,
    d.year_num,
    d.month_num,
    d.day_name,
    d.is_weekend,
    COUNT(*) AS n_readings,
    ROUND(AVG(f.global_active_power_kw), 4) AS avg_kw,
    ROUND(MAX(f.global_active_power_kw), 4) AS peak_kw,
    ROUND(SUM(f.global_active_power_kw) / 60.0, 2) AS total_kwh
FROM fact_power_readings f
INNER JOIN dim_date d ON f.date_key = d.date_key
GROUP BY d.date_key, d.calendar_date, d.year_num, d.month_num, d.day_name, d.is_weekend;

-- 1. Monthly Average, Peak, and Total Energy from Daily CTE
WITH daily_energy AS (
    SELECT * FROM v_daily_power_summary
)
SELECT
    year_num,
    month_num,
    COUNT(*) AS active_days,
    ROUND(AVG(avg_kw), 4) AS mean_daily_kw,
    ROUND(MAX(peak_kw), 4) AS max_kw,
    ROUND(SUM(total_kwh), 2) AS total_monthly_kwh
FROM daily_energy
GROUP BY year_num, month_num
ORDER BY year_num, month_num;

-- 2. Top 10 Peak-Consumption Dates by Total Daily kWh
SELECT calendar_date, day_name, n_readings, peak_kw, total_kwh
FROM v_daily_power_summary
ORDER BY total_kwh DESC
LIMIT 10;

-- 3. Hours Above Threshold (> 1.50 kW) with Conditional Weekday/Weekend Averages
SELECT
    HOUR(f.reading_ts) AS hour_of_day,
    COUNT(*) AS n_readings,
    ROUND(AVG(f.global_active_power_kw), 4) AS avg_kw,
    ROUND(AVG(CASE WHEN d.is_weekend = 0 THEN f.global_active_power_kw END), 4) AS weekday_avg_kw,
    ROUND(AVG(CASE WHEN d.is_weekend = 1 THEN f.global_active_power_kw END), 4) AS weekend_avg_kw
FROM fact_power_readings f
INNER JOIN dim_date d ON f.date_key = d.date_key
GROUP BY HOUR(f.reading_ts)
HAVING AVG(f.global_active_power_kw) > 1.50
ORDER BY avg_kw DESC;

-- 4. Calendar Anti-Join: Dates with No Readings
SELECT d.calendar_date, d.day_name, d.is_weekend
FROM dim_date d
LEFT JOIN fact_power_readings f ON d.date_key = f.date_key
WHERE f.date_key IS NULL
ORDER BY d.calendar_date;

-- 5. Unmatched Dimension / Batch Check via NOT EXISTS
SELECT f.reading_id, f.reading_ts, f.date_key, f.batch_id
FROM fact_power_readings f
WHERE NOT EXISTS (SELECT 1 FROM dim_date d WHERE d.date_key = f.date_key)
   OR NOT EXISTS (SELECT 1 FROM etl_ingestion_batch b WHERE b.batch_id = f.batch_id);

-- 6. Sub-Meter Share of Total Active Energy (%)
WITH energy_totals AS (
    SELECT
        SUM(COALESCE(sub_metering_1_wh, 0)) / 1000.0 AS sm1_kwh,
        SUM(COALESCE(sub_metering_2_wh, 0)) / 1000.0 AS sm2_kwh,
        SUM(COALESCE(sub_metering_3_wh, 0)) / 1000.0 AS sm3_kwh,
        SUM(global_active_power_kw) / 60.0 AS total_kwh
    FROM fact_power_readings
)
SELECT
    ROUND(100.0 * sm1_kwh / NULLIF(total_kwh, 0), 2) AS sm1_pct,
    ROUND(100.0 * sm2_kwh / NULLIF(total_kwh, 0), 2) AS sm2_pct,
    ROUND(100.0 * sm3_kwh / NULLIF(total_kwh, 0), 2) AS sm3_pct,
    ROUND(100.0 * (total_kwh - (sm1_kwh + sm2_kwh + sm3_kwh)) / NULLIF(total_kwh, 0), 2) AS unmetered_pct
FROM energy_totals;