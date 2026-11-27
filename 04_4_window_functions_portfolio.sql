USE kenya_power_dw;

-- 1. Rank Top 10 Highest-Consumption Days in Each Month
WITH daily_energy AS (
    SELECT
        d.year_num,
        d.month_num,
        d.calendar_date,
        ROUND(SUM(f.global_active_power_kw) / 60.0, 2) AS daily_kwh,
        ROUND(MAX(f.global_active_power_kw), 4) AS peak_kw
    FROM fact_power_readings f
    INNER JOIN dim_date d ON f.date_key = d.date_key
    GROUP BY d.year_num, d.month_num, d.calendar_date
),
ranked_days AS (
    SELECT
        *,
        DENSE_RANK() OVER (
            PARTITION BY year_num, month_num
            ORDER BY daily_kwh DESC
        ) AS mth_day_rank,
        NTILE(4) OVER (
            PARTITION BY year_num, month_num
            ORDER BY daily_kwh DESC
        ) AS load_quartile
    FROM daily_energy
)
SELECT *
FROM ranked_days
WHERE mth_day_rank <= 10
ORDER BY year_num, month_num, mth_day_rank;

-- 2. Rank All Hours Within Each Month & Find Highest-Load Hour
WITH hourly_load AS (
    SELECT
        d.year_num,
        d.month_num,
        HOUR(f.reading_ts) AS hour_of_day,
        ROUND(AVG(f.global_active_power_kw), 4) AS avg_kw
    FROM fact_power_readings f
    INNER JOIN dim_date d ON f.date_key = d.date_key
    GROUP BY d.year_num, d.month_num, HOUR(f.reading_ts)
)
SELECT
    *,
    RANK() OVER (
        PARTITION BY year_num, month_num
        ORDER BY avg_kw DESC
    ) AS hr_rank_in_month
FROM hourly_load
ORDER BY year_num, month_num, hr_rank_in_month;

-- 3. Minute Change, 60-Min Moving Avg, Cumulative Monthly Energy & Share
SELECT
    f.reading_ts,
    d.year_num,
    d.month_num,
    f.global_active_power_kw AS power_kw,
    ROUND(f.global_active_power_kw - LAG(f.global_active_power_kw, 1) OVER (ORDER BY f.reading_ts), 4) AS diff_from_prev_min_kw,
    ROUND(AVG(f.global_active_power_kw) OVER (
        ORDER BY f.reading_ts
        ROWS BETWEEN 59 PRECEDING AND CURRENT ROW
    ), 4) AS ma_60m_kw,
    ROUND(SUM(f.global_active_power_kw / 60.0) OVER (
        PARTITION BY d.year_num, d.month_num
        ORDER BY f.reading_ts
        ROWS UNBOUNDED PRECEDING
    ), 3) AS cum_month_kwh,
    ROUND(
        100.0 * (f.global_active_power_kw / 60.0) /
        NULLIF(SUM(f.global_active_power_kw / 60.0) OVER (PARTITION BY d.year_num, d.month_num), 0),
        6
    ) AS pct_of_month_kwh
FROM fact_power_readings f
INNER JOIN dim_date d ON f.date_key = d.date_key
ORDER BY f.reading_ts
LIMIT 200;

-- 4. Hourly Series: Prev Hour, Same Hour Yesterday (LAG 24), Same Hour Last Week (LAG 168), 24h MA
WITH hourly_ts AS (
    SELECT
        DATE_FORMAT(f.reading_ts, '%Y-%m-%d %H:00:00') AS hour_ts,
        AVG(f.global_active_power_kw) AS avg_kw
    FROM fact_power_readings f
    GROUP BY DATE_FORMAT(f.reading_ts, '%Y-%m-%d %H:00:00')
)
SELECT
    hour_ts,
    ROUND(avg_kw, 4) AS avg_kw,
    ROUND(avg_kw - LAG(avg_kw, 1) OVER (ORDER BY hour_ts), 4) AS delta_1h_kw,
    ROUND(avg_kw - LAG(avg_kw, 24) OVER (ORDER BY hour_ts), 4) AS delta_24h_same_hr_kw,
    ROUND(avg_kw - LAG(avg_kw, 168) OVER (ORDER BY hour_ts), 4) AS delta_7d_same_hr_kw,
    ROUND(AVG(avg_kw) OVER (ORDER BY hour_ts ROWS BETWEEN 23 PRECEDING AND CURRENT ROW), 4) AS ma_24h_kw
FROM hourly_ts
ORDER BY hour_ts;

-- 5. Gaps & Islands: Consecutive High-Load Periods (e.g., avg_kw > 3.5 kW)
WITH flagged AS (
    SELECT
        reading_ts,
        global_active_power_kw,
        CASE WHEN global_active_power_kw > 3.5 THEN 1 ELSE 0 END AS is_high_load,
        CASE
            WHEN global_active_power_kw > 3.5
             AND COALESCE(LAG(global_active_power_kw) OVER (ORDER BY reading_ts), 0) <= 3.5
            THEN 1 ELSE 0
        END AS spell_start_flag
    FROM fact_power_readings
),
islands AS (
    SELECT
        *,
        SUM(spell_start_flag) OVER (ORDER BY reading_ts ROWS UNBOUNDED PRECEDING) AS spell_id
    FROM flagged
    WHERE is_high_load = 1
)
SELECT
    spell_id,
    MIN(reading_ts) AS spell_start_ts,
    MAX(reading_ts) AS spell_end_ts,
    COUNT(*) AS duration_minutes,
    ROUND(AVG(global_active_power_kw), 4) AS spell_avg_kw,
    ROUND(MAX(global_active_power_kw), 4) AS spell_peak_kw
FROM islands
GROUP BY spell_id
HAVING COUNT(*) >= 10
ORDER BY duration_minutes DESC, spell_start_ts;

-- 6. Gaps & Islands: Continuous Missing-Data Intervals (Gap > 1 Minute)
WITH ordered_ts AS (
    SELECT
        reading_ts,
        LAG(reading_ts) OVER (ORDER BY reading_ts) AS prev_ts,
        TIMESTAMPDIFF(MINUTE, LAG(reading_ts) OVER (ORDER BY reading_ts), reading_ts) AS gap_mins
    FROM fact_power_readings
)
SELECT
    prev_ts AS missing_window_start,
    reading_ts AS missing_window_end,
    gap_mins - 1 AS missing_minutes_count
FROM ordered_ts
WHERE gap_mins > 1
ORDER BY missing_minutes_count DESC, missing_window_start;

-- 7. First Peak & Last Peak Timestamp per Date
WITH daily_peaks AS (
    SELECT
        d.calendar_date,
        f.reading_ts,
        f.global_active_power_kw,
        MAX(f.global_active_power_kw) OVER (PARTITION BY d.calendar_date) AS day_max_kw
    FROM fact_power_readings f
    INNER JOIN dim_date d ON f.date_key = d.date_key
),
peak_events AS (
    SELECT
        calendar_date,
        reading_ts,
        global_active_power_kw,
        FIRST_VALUE(reading_ts) OVER (
            PARTITION BY calendar_date
            ORDER BY reading_ts ASC
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS first_peak_ts,
        LAST_VALUE(reading_ts) OVER (
            PARTITION BY calendar_date
            ORDER BY reading_ts ASC
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS last_peak_ts
    FROM daily_peaks
    WHERE global_active_power_kw = day_max_kw
)
SELECT DISTINCT
    calendar_date,
    global_active_power_kw AS peak_kw,
    first_peak_ts,
    last_peak_ts
FROM peak_events
ORDER BY calendar_date;