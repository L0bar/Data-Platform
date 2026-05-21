# NYC Mobility, Air Quality & Economic Analytics

A Microsoft Fabric data engineering project implementing a medallion architecture (Bronze → Silver → Gold) to integrate mobility, environmental, and economic data sources for cross-domain analytics.

---

## Project Overview

This project ingests, transforms, and analyzes data from four heterogeneous sources to deliver business-ready dashboards. The pipeline demonstrates end-to-end data engineering practices on Microsoft Fabric, from raw ingestion through dimensional modeling to interactive visualization.

### Business Questions Answered

- How does taxi mobility vary across days, months, and pickup zones in NYC?
- What are the daily trends in air quality (PM2.5, NO2, O3) in the NYC metro area?
- Is there a relationship between air pollution levels and taxi traffic patterns?
- How does taxi revenue compare when converted between USD and EUR?
- What is the economic context (GDP) surrounding the analysis period?

---

## Architecture

The solution follows the **medallion architecture** pattern with three Lakehouse layers and a SQL Warehouse for analytics:

```
┌─────────────────────────────────────────────────────────────┐
│  External Sources                                           │
│  ─ NYC TLC (Parquet)  ─ ECB FX (CSV)                        │
│  ─ OpenAQ (JSON API)  ─ World Bank (JSON API)               │
└──────────────────────────┬──────────────────────────────────┘
                           │
       ┌───────────────────┴────────────────────┐
       │                                        │
   Data Pipeline                          Dataflow Gen2
   (Copy Data)                            (Power Query)
       │                                        │
       └───────────────────┬────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  LH_Bronze (Lakehouse)                                      │
│  Raw data in original format                                │
│  Files: Parquet, CSV │ Tables: Delta (from JSON sources)    │
└──────────────────────────┬──────────────────────────────────┘
                           │ PySpark Notebooks
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  LH_Silver (Lakehouse)                                      │
│  Cleaned, typed, deduplicated Delta tables                  │
└──────────────────────────┬──────────────────────────────────┘
                           │ PySpark Notebooks
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  LH_Gold (Lakehouse)                                        │
│  Star schema: Fact + Dimension tables                       │
│  Pre-aggregated, business-ready datasets                    │
└──────────────────────────┬──────────────────────────────────┘
                           │ T-SQL Views (cross-database)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  WH_Analytics (Warehouse)                                   │
│  Views over Gold + business join views                      │
└──────────────────────────┬──────────────────────────────────┘
                           │ Direct Lake mode
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Power BI Report                                            │
│  4 dashboards: Mobility, Air Quality, Correlation, Economic │
└─────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Component | Technology |
|---|---|
| **Cloud platform** | Microsoft Fabric (Azure) |
| **Capacity SKU** | F2 (Fabric capacity) |
| **Region** | East Asia |
| **Storage** | OneLake (Delta Lake format) |
| **Ingestion (files)** | Data Pipelines — Copy Data activity |
| **Ingestion (APIs)** | Dataflow Gen2 — Power Query (M language) |
| **Transformation** | PySpark Notebooks |
| **Analytics layer** | Fabric Warehouse (T-SQL) |
| **Visualization** | Power BI Direct Lake mode |

---

## Data Sources

### 1. NYC Taxi Trips (Mobility)
- **Source:** NYC TLC public dataset via CloudFront
- **URL pattern:** `https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_YYYY-MM.parquet`
- **Format:** Parquet
- **Frequency:** Monthly files
- **Coverage:** Full year 2024 (Yellow taxi)
- **Volume:** ~3 million trips
- **Ingestion:** Data Pipeline (Copy Data, Binary mode)

### 2. OpenAQ Air Quality
- **Source:** OpenAQ v3 REST API
- **URL pattern:** `https://api.openaq.org/v3/sensors/{id}/days`
- **Format:** JSON
- **Authentication:** API key (X-API-Key header)
- **Coverage:** NYC metro area, 44 sensors, parameters PM2.5 / NO2 / O3
- **Frequency:** Daily aggregates for 2024
- **Volume:** ~10,000 measurements
- **Ingestion:** Dataflow Gen2 with paginated M-language query

### 3. ECB Foreign Exchange (USD/EUR)
- **Source:** European Central Bank Statistical Data Warehouse
- **URL:** `https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?format=csvdata&startPeriod=2024-01-01&endPeriod=2024-12-31`
- **Format:** CSV
- **Coverage:** Daily USD/EUR exchange rates for 2024
- **Volume:** ~250 business days
- **Ingestion:** Data Pipeline (Copy Data)

### 4. World Bank GDP
- **Source:** World Bank Open Data API
- **URL:** `https://api.worldbank.org/v2/country/USA/indicator/NY.GDP.MKTP.CD?format=json&per_page=200`
- **Format:** JSON
- **Indicator:** NY.GDP.MKTP.CD (GDP current US$)
- **Coverage:** United States, 1960–2024
- **Volume:** ~65 annual records
- **Ingestion:** Dataflow Gen2

---

## Project Structure

### Workspace: `Data Platform`

```
Data Platform/
├── Lakehouses/
│   ├── LH_Bronze              # Raw data
│   ├── LH_Silver              # Cleaned data
│   └── LH_Gold                # Star schema
├── Warehouse/
│   └── WH_Analytics           # SQL views over Gold
├── Pipelines/
│   ├── PL_Bronze_Taxi         # NYC Taxi ingestion
│   └── PL_Bronze_ECB          # ECB FX ingestion
├── Dataflows/
│   ├── DF_Bronze_OpenAQ       # OpenAQ ingestion
│   └── DF_Bronze_WorldBank    # World Bank ingestion
├── Notebooks/
│   ├── NB_Silver_Taxi
│   ├── NB_Silver_FX
│   ├── NB_Silver_OpenAQ
│   ├── NB_Silver_GDP
│   ├── NB_Gold_DimDate
│   ├── NB_Gold_FactTaxi
│   ├── NB_Gold_FactAirQuality
│   └── NB_Gold_FactGDP
├── Semantic model/
│   └── SM_Analytics           # Direct Lake model
└── Reports/
    └── NYC_Analytics_Dashboard
```

---

## Bronze Layer — Raw Ingestion

Raw data is landed in `LH_Bronze` with no schema enforcement, preserving the original format from each source.

```
LH_Bronze/
├── Files/
│   ├── nyc_taxi/yellow/yyyy=2024/mm=01..12/*.parquet
│   └── exchange_rate_euro_usd/euro_usd_daily.csv
└── Tables/
    ├── openaq_measurements_raw
    └── worldbank_gdp_raw
```

**Design choice:** File-based sources (Parquet, CSV) are stored in `Files/` to preserve binary fidelity. API sources (JSON) are stored as Delta `Tables/` because Dataflow Gen2 already parses the JSON during ingestion.

---

## Silver Layer — Cleaned & Standardized

Each Silver notebook reads from Bronze, applies cleaning rules, type casting, and deduplication, then writes a Delta table to `LH_Silver`.

```
LH_Silver/Tables/
├── taxi_trips_clean   
├── fx_daily           
├── air_quality_clean  
└── gdp_yearly         
```

### Key transformations

| Source | Operations |
|---|---|
| **taxi_trips_clean** | Renamed timestamp columns, derived `pickup_date` and `trip_duration_min`, filtered invalid rows (negative/zero distance & fare, passenger count out of 1–8, trips outside 0–600 min, year ≠ 2024), deduplicated |
| **fx_daily** | Date parsing, numeric cast, null/negative filter, dedup by date |
| **air_quality_clean** | Date cast, derived `year` / `month`, filtered to PM2.5/NO2/O3 only, removed negative readings, dedup by (sensor, date, parameter) |
| **gdp_yearly** | Year cast, USA filter, added derived columns `gdp_billion_usd` and `gdp_trillion_usd` |

---

## Gold Layer — Star Schema

Gold contains dimensional models optimized for analytics. Tables are pre-aggregated to the grain required by reporting.

```
LH_Gold/Tables/
├── DimDate                # Synthetic date dimension (366 rows for 2024)
├── FactTaxiDaily          # Daily × zone aggregates, enriched with FX
├── FactAirQualityDaily    # Daily NYC averages, pivoted by parameter
└── FactGDPYearly          # Annual GDP context
```

### Notable design decisions

- **DimDate** is a generated dimension (Spark `sequence()`) containing year, quarter, month, day name, week, and weekend flag — enabling time-intelligence in Power BI.
- **FactTaxiDaily** joins Silver taxi aggregates with `fx_daily` to add `total_fare_eur`. Null FX values on non-business days are preserved (no forward-fill in Gold).
- **FactAirQualityDaily** pivots the long-format Silver table into wide format with one row per day and columns `pm25_avg`, `no2_avg`, `o3_avg`, `sensor_count`.

---

## Warehouse Layer

`WH_Analytics` contains T-SQL views over the Gold Lakehouse. No tables are duplicated — views act as pointers that Power BI consumes through Direct Lake mode.

| Object | Type | Purpose |
|---|---|---|
| `vw_DimDate` | View | Exposes Gold DimDate |
| `vw_FactTaxiDaily` | View | Exposes taxi fact |
| `vw_FactAirQuality` | View | Exposes air quality fact |
| `vw_FactGDP` | View | Exposes GDP fact |
| `vw_TaxiWithAirQuality` | **Business view** | Pre-joined wide table: taxi + air quality + date attributes for Power BI |

---

## Semantic Model & Reporting

A semantic model `SM_Analytics` is built on top of the Warehouse using Direct Lake mode. The Power BI report contains four pages:

| Page | Visuals | Key insight |
|---|---|---|
| **Mobility** | KPI cards (trips, revenue), daily trips line chart, top zones bar chart | Traffic intensity by time and zone |
| **Air Quality** | PM2.5 KPI, trend lines for 3 parameters, monthly column chart | Pollution patterns over 2024 |
| **Correlation** | Dual-axis line (trips + PM2.5), heatmap by day × month | Relationship between mobility and pollution |
| **Economic** | Revenue USD vs EUR cards, FX rate trend, GDP context | Multi-currency revenue and macro context |
