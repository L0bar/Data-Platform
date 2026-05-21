# Data Dictionary

Complete reference for all tables, views, and columns in the NYC Mobility, Air Quality & Economic Analytics project.

---

## Table of Contents

1. [Bronze Layer (LH_Bronze)](#bronze-layer-lh_bronze)
2. [Silver Layer (LH_Silver)](#silver-layer-lh_silver)
3. [Gold Layer (LH_Gold)](#gold-layer-lh_gold)
4. [Warehouse (WH_Analytics)](#warehouse-wh_analytics)

---

## Bronze Layer (LH_Bronze)

Raw data preserved in source format. Files-based sources are stored as Parquet/CSV; API sources are stored as Delta tables.

### Files: nyc_taxi/yellow/yyyy=YYYY/mm=MM/*.parquet

NYC Yellow Taxi trip records. Original schema from NYC TLC. Approximately 3 million rows for 2024.

| Column | Type | Description |
|---|---|---|
| VendorID | int | Provider code (1 = Creative Mobile Technologies, 2 = VeriFone) |
| tpep_pickup_datetime | timestamp | Meter engagement timestamp |
| tpep_dropoff_datetime | timestamp | Meter disengagement timestamp |
| passenger_count | bigint | Number of passengers (driver-entered) |
| trip_distance | double | Trip distance in miles |
| RatecodeID | bigint | Rate code (1 = standard, 2 = JFK, 3 = Newark, etc.) |
| store_and_fwd_flag | string | Y/N flag for stored-and-forwarded records |
| PULocationID | int | TLC pickup zone ID |
| DOLocationID | int | TLC drop-off zone ID |
| payment_type | bigint | Payment method (1 = credit card, 2 = cash, etc.) |
| fare_amount | double | Time-and-distance fare in USD |
| extra | double | Extra charges (rush hour, overnight) |
| mta_tax | double | MTA tax (auto-triggered) |
| tip_amount | double | Tip amount (credit card only) |
| tolls_amount | double | Total tolls paid |
| improvement_surcharge | double | Improvement surcharge |
| total_amount | double | Total amount charged to passenger |
| congestion_surcharge | double | Congestion surcharge |
| Airport_fee | double | Airport pickup fee |

### Files: exchange_rate_euro_usd/euro_usd_daily.csv

ECB daily USD/EUR exchange rates. Full ECB SDMX CSV format with many metadata columns; only `TIME_PERIOD` and `OBS_VALUE` are used downstream.

| Column | Type | Description |
|---|---|---|
| KEY | string | ECB series identifier |
| FREQ | string | Frequency code (D = daily) |
| CURRENCY | string | Source currency (USD) |
| CURRENCY_DENOM | string | Quote currency (EUR) |
| EXR_TYPE | string | Exchange rate type (SP00 = spot) |
| EXR_SUFFIX | string | Series suffix (A = average) |
| TIME_PERIOD | string | Observation date (YYYY-MM-DD) |
| OBS_VALUE | string | Exchange rate value |
| ... | string | Additional ECB metadata columns |

### Tables: openaq_measurements_raw

OpenAQ daily air quality measurements for NYC sensors. Created by Dataflow Gen2 from JSON API.

| Column | Type | Description |
|---|---|---|
| sensor_id | bigint | OpenAQ sensor identifier |
| value | double | Measurement value |
| parameter_name | string | Pollutant code (pm25, no2, o3) |
| parameter_units | string | Measurement units (µg/m³, ppm) |
| measurement_date | string | Date of measurement (YYYY-MM-DD) |
| lat | double | Sensor latitude (often null in /days endpoint) |
| lon | double | Sensor longitude (often null in /days endpoint) |

### Tables: worldbank_gdp_raw

USA GDP yearly data from World Bank API. Created by Dataflow Gen2.

| Column | Type | Description |
|---|---|---|
| indicator_id | string | Indicator code (NY.GDP.MKTP.CD) |
| indicator_name | string | Human-readable indicator name |
| country_code | string | ISO3 country code (USA) |
| country_name | string | Country name (United States) |
| year | bigint | Year of observation |
| gdp_value | double | GDP in current USD |

---

## Silver Layer (LH_Silver)

Cleaned, standardized, and deduplicated Delta tables. One source = one table.

### taxi_trips_clean

Filtered and enriched taxi trips, approximately 2.7 million rows after cleaning.

| Column | Type | Description |
|---|---|---|
| VendorID | int | Provider code (preserved from Bronze) |
| pickup_ts | timestamp | Pickup timestamp (renamed from tpep_pickup_datetime) |
| dropoff_ts | timestamp | Dropoff timestamp (renamed from tpep_dropoff_datetime) |
| pickup_date | date | Derived: date portion of pickup_ts |
| passenger_count | bigint | Number of passengers (validated to 1–8) |
| trip_distance | double | Trip distance in miles (validated > 0 and < 200) |
| PULocationID | int | Pickup zone ID |
| DOLocationID | int | Drop-off zone ID |
| fare_amount | double | Base fare USD (validated > 0 and < 1000) |
| tip_amount | double | Tip amount USD |
| total_amount | double | Total amount USD |
| trip_duration_min | double | Derived: minutes between pickup_ts and dropoff_ts, rounded to 2 decimals |

**Cleaning rules applied:**
- `trip_distance > 0` and `< 200`
- `fare_amount > 0` and `< 1000`
- `passenger_count` between 1 and 8
- `trip_duration_min > 0` and `< 600` (10 hours)
- `year(pickup_ts) = 2024`
- Deduplication on (pickup_ts, dropoff_ts, PULocationID, DOLocationID, fare_amount)

### fx_daily

Daily USD/EUR exchange rate from ECB, approximately 250 business-day rows for 2024.

| Column | Type | Description |
|---|---|---|
| fx_date | date | Observation date |
| usd_eur_rate | double | USD/EUR exchange rate |

**Cleaning rules applied:**
- Null and negative rate filter
- Deduplication on fx_date
- Sorted by date ascending

### air_quality_clean

NYC daily air quality measurements for PM2.5, NO2, O3.

| Column | Type | Description |
|---|---|---|
| sensor_id | bigint | OpenAQ sensor identifier |
| measurement_date | date | Date of measurement |
| year | int | Derived from measurement_date |
| month | int | Derived from measurement_date |
| parameter_name | string | Pollutant: pm25, no2, or o3 |
| parameter_units | string | Unit of measure |
| value | double | Daily mean measurement (rounded to 3 decimals) |

**Cleaning rules applied:**
- `value >= 0` (negative readings excluded as sensor errors)
- `year = 2024`
- Parameter restricted to (pm25, no2, o3)
- Deduplication on (sensor_id, measurement_date, parameter_name)

### gdp_yearly

USA annual GDP records.

| Column | Type | Description |
|---|---|---|
| country_code | string | ISO3 code (USA) |
| country_name | string | Country name (United States) |
| year | int | Year of observation |
| gdp_usd | double | GDP in current USD |
| gdp_billion_usd | double | Derived: gdp_usd / 1e9, rounded to 2 decimals |
| gdp_trillion_usd | double | Derived: gdp_usd / 1e12, rounded to 3 decimals |
| indicator_id | string | World Bank indicator code |
| indicator_name | string | Indicator description |

**Cleaning rules applied:**
- Null and negative GDP filter
- USA filter (`country_code = 'USA'`)
- Sorted by year descending

---

## Gold Layer (LH_Gold)

Dimensional model: facts and dimensions optimized for analytics.

### DimDate

Synthetic date dimension covering 2024 (366 rows). Built using Spark `sequence()` function.

| Column | Type | Description |
|---|---|---|
| date_key | int | Surrogate key in YYYYMMDD format (e.g., 20240115) — primary key |
| full_date | date | Calendar date |
| year | int | Calendar year |
| quarter | int | Calendar quarter (1–4) |
| month | int | Calendar month (1–12) |
| month_name | string | Full month name (January, February, ...) |
| day | int | Day of month (1–31) |
| day_of_week | int | Day of week (1 = Sunday, 7 = Saturday) |
| day_name | string | Day name (Monday, Tuesday, ...) |
| week_of_year | int | ISO week number |
| is_weekend | boolean | True if Saturday or Sunday |

### FactTaxiDaily

Daily taxi aggregates by pickup zone, enriched with FX rates from `fx_daily`.

| Column | Type | Description |
|---|---|---|
| date_key | int | Foreign key to DimDate (YYYYMMDD format) |
| pickup_date | date | Pickup date |
| PULocationID | int | TLC pickup zone ID |
| trip_count | bigint | Number of trips on date × zone |
| total_fare_usd | double | Sum of fare_amount in USD |
| total_fare_eur | double | Derived: total_fare_usd × usd_eur_rate (null on non-business days) |
| usd_eur_rate | double | FX rate for the date (null on non-business days) |
| avg_duration_min | double | Average trip duration in minutes |
| total_distance_mi | double | Total trip distance in miles |

**Grain:** one row per (date, pickup zone).

### FactAirQualityDaily

NYC daily air quality averages, pivoted from long to wide format.

| Column | Type | Description |
|---|---|---|
| date_key | int | Foreign key to DimDate (YYYYMMDD format) |
| measurement_date | date | Measurement date |
| pm25_avg | double | Mean PM2.5 across all NYC sensors (µg/m³) |
| no2_avg | double | Mean NO2 across all NYC sensors |
| o3_avg | double | Mean O3 across all NYC sensors |
| sensor_count | int | Number of sensors reporting on this date |

**Grain:** one row per date.

### FactGDPYearly

USA annual GDP for macro-economic context.

| Column | Type | Description |
|---|---|---|
| year | int | Year of observation |
| gdp_usd | double | GDP in current USD |
| gdp_billion_usd | double | GDP in billions USD |
| gdp_trillion_usd | double | GDP in trillions USD |
| country_code | string | ISO3 code (USA) |
| country_name | string | Country name |

**Grain:** one row per year.

---

## Warehouse (WH_Analytics)

T-SQL views over Gold tables, accessible via the Warehouse SQL endpoint. Power BI consumes these via Direct Lake mode.

### vw_DimDate

Pass-through view of `LH_Gold.dbo.DimDate`. Same columns as the Gold table.

### vw_FactTaxiDaily

Pass-through view of `LH_Gold.dbo.FactTaxiDaily`. Same columns as the Gold table.

### vw_FactAirQuality

Pass-through view of `LH_Gold.dbo.FactAirQualityDaily`. Same columns as the Gold table.

### vw_FactGDP

Pass-through view of `LH_Gold.dbo.FactGDPYearly`. Same columns as the Gold table.

### vw_TaxiWithAirQuality

Business view that pre-joins taxi facts with air quality facts and date attributes. Designed as the primary source for Power BI cross-source visualizations.

| Column | Type | Source | Description |
|---|---|---|---|
| date_key | int | FactTaxiDaily | Date surrogate key |
| full_date | date | DimDate | Calendar date |
| year | int | DimDate | Calendar year |
| month | int | DimDate | Calendar month |
| month_name | string | DimDate | Full month name |
| day_name | string | DimDate | Day name |
| is_weekend | boolean | DimDate | Weekend indicator |
| zone_id | int | FactTaxiDaily | PULocationID renamed |
| trip_count | bigint | FactTaxiDaily | Trip count for date × zone |
| total_fare_usd | double | FactTaxiDaily | Revenue USD |
| total_fare_eur | double | FactTaxiDaily | Revenue EUR (FX-enriched) |
| usd_eur_rate | double | FactTaxiDaily | Daily FX rate |
| avg_duration_min | double | FactTaxiDaily | Average trip duration |
| total_distance_mi | double | FactTaxiDaily | Total trip distance |
| pm25_avg | double | FactAirQualityDaily | NYC mean PM2.5 |
| no2_avg | double | FactAirQualityDaily | NYC mean NO2 |
| o3_avg | double | FactAirQualityDaily | NYC mean O3 |
| aq_sensor_count | int | FactAirQualityDaily | Sensor count |

**Join logic:**
```sql
FactTaxiDaily t
LEFT JOIN DimDate d ON t.date_key = d.date_key
LEFT JOIN FactAirQualityDaily aq ON t.date_key = aq.date_key
```

`LEFT JOIN` is used so that taxi rows without matching air quality data (e.g., sensors offline) are preserved.

---

## Naming Conventions

| Prefix | Meaning | Example |
|---|---|---|
| `LH_` | Lakehouse | `LH_Bronze`, `LH_Silver`, `LH_Gold` |
| `WH_` | Warehouse | `WH_Analytics` |
| `PL_` | Pipeline | `PL_Bronze_Taxi` |
| `DF_` | Dataflow | `DF_Bronze_OpenAQ` |
| `NB_` | Notebook | `NB_Silver_Taxi` |
| `SM_` | Semantic Model | `SM_Analytics` |
| `Dim` | Dimension table | `DimDate` |
| `Fact` | Fact table | `FactTaxiDaily` |
| `vw_` | View | `vw_FactTaxiDaily` |

---

## Data Refresh Behavior

The semantic model uses **Direct Lake mode**, which means:

- Power BI queries Delta files in OneLake directly (no data import or copy)
- Changes to Gold tables are reflected in reports within seconds of the next visual interaction
- New columns require a semantic model refresh; existing columns refresh automatically
- The Warehouse views are virtual — no manual refresh needed when Gold tables update

For incremental updates in future iterations, change the notebook write mode from `overwrite` to `merge` or `append` and add appropriate partition pruning.
