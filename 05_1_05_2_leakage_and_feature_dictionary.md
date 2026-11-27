# Phase 5.1 & 5.2 Leakage Audit & Feature Dictionary
- **Rows:** 17,212 hourly intervals | **Features:** 48
- **Targets:** `target_t_plus_1h_kw` and `target_t_plus_24h_kw` (strictly future relative to origin `t`).

| Feature | Meaning |
| :--- | :--- |
| `mean_kw` | Feature available at or before prediction time `t` |
| `max_kw` | Feature available at or before prediction time `t` |
| `min_kw` | Feature available at or before prediction time `t` |
| `std_kw` | Feature available at or before prediction time `t` |
| `mean_v` | Feature available at or before prediction time `t` |
| `mean_a` | Feature available at or before prediction time `t` |
| `lag_1h_kw` | Feature available at or before prediction time `t` |
| `lag_2h_kw` | Feature available at or before prediction time `t` |
| `lag_3h_kw` | Feature available at or before prediction time `t` |
| `lag_6h_kw` | Feature available at or before prediction time `t` |
| `lag_12h_kw` | Feature available at or before prediction time `t` |
| `lag_24h_kw` | Feature available at or before prediction time `t` |
| `lag_48h_kw` | Feature available at or before prediction time `t` |
| `lag_168h_kw` | Feature available at or before prediction time `t` |
| `roll_mean_3h_kw` | Feature available at or before prediction time `t` |
| `roll_std_3h_kw` | Feature available at or before prediction time `t` |
| `roll_min_3h_kw` | Feature available at or before prediction time `t` |
| `roll_max_3h_kw` | Feature available at or before prediction time `t` |
| `roll_mean_6h_kw` | Feature available at or before prediction time `t` |
| `roll_std_6h_kw` | Feature available at or before prediction time `t` |
| `roll_min_6h_kw` | Feature available at or before prediction time `t` |
| `roll_max_6h_kw` | Feature available at or before prediction time `t` |
| `roll_mean_24h_kw` | Feature available at or before prediction time `t` |
| `roll_std_24h_kw` | Feature available at or before prediction time `t` |
| `roll_min_24h_kw` | Feature available at or before prediction time `t` |
| `roll_max_24h_kw` | Feature available at or before prediction time `t` |
| `roll_mean_168h_kw` | Feature available at or before prediction time `t` |
| `roll_std_168h_kw` | Feature available at or before prediction time `t` |
| `roll_min_168h_kw` | Feature available at or before prediction time `t` |
| `roll_max_168h_kw` | Feature available at or before prediction time `t` |
| `diff_1h_kw` | Feature available at or before prediction time `t` |
| `diff_24h_kw` | Feature available at or before prediction time `t` |
| `pct_chg_1h` | Feature available at or before prediction time `t` |
| `pct_chg_24h` | Feature available at or before prediction time `t` |
| `hour` | Feature available at or before prediction time `t` |
| `day_of_week` | Feature available at or before prediction time `t` |
| `month` | Feature available at or before prediction time `t` |
| `is_weekend` | Feature available at or before prediction time `t` |
| `hour_sin` | Feature available at or before prediction time `t` |
| `hour_cos` | Feature available at or before prediction time `t` |
| `dow_sin` | Feature available at or before prediction time `t` |
| `dow_cos` | Feature available at or before prediction time `t` |
| `sm1_share_t` | Feature available at or before prediction time `t` |
| `sm2_share_t` | Feature available at or before prediction time `t` |
| `sm3_share_t` | Feature available at or before prediction time `t` |
| `residual_share_t` | Feature available at or before prediction time `t` |
| `residual_unmetered_kwh` | Feature available at or before prediction time `t` |
| `high_load_flag_t` | Feature available at or before prediction time `t` |