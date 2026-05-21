# Governance Policies

Operational policies and standards governing the NYC Mobility, Air Quality & Economic Analytics platform.

---

## Table of Contents

1. [Access Control](#1-access-control)
2. [Data Sensitivity & Classification](#2-data-sensitivity--classification)
3. [Data Retention](#3-data-retention)
4. [Refresh & Update Schedule](#4-refresh--update-schedule)
5. [Data Quality Standards](#5-data-quality-standards)
6. [Naming Conventions](#6-naming-conventions)
7. [Change Management](#7-change-management)
8. [Cost Management](#8-cost-management)
9. [Security & Secrets](#9-security--secrets)
10. [Monitoring & Auditing](#10-monitoring--auditing)

---

## 1. Access Control

Role-based access aligned with the medallion layers. Permissions are managed through Fabric Workspace roles.

### Workspace roles

| Role | Permissions | Typical user |
|---|---|---|
| **Admin** | Full control: manage members, capacity, all artifacts | Project owner / data platform lead |
| **Member** | Create, edit, delete artifacts; cannot manage workspace settings | Data engineers |
| **Contributor** | Edit existing artifacts; cannot delete | Data analysts |
| **Viewer** | Read-only access to all artifacts | Business stakeholders, reviewers |

### Layer-specific access (recommended)

| Layer | Who can read | Who can write |
|---|---|---|
| **LH_Bronze** | Data engineers only | Pipelines / Dataflows / Admins |
| **LH_Silver** | Data engineers, analysts | Data engineers only |
| **LH_Gold** | All workspace users | Data engineers only |
| **WH_Analytics** | All workspace users | Data engineers only |
| **Power BI Report** | All workspace users + invited stakeholders | Report authors |

### Implementation

Access is configured per workspace via **Manage access**. For external stakeholders without Fabric licenses, share read-only links to the Power BI report through Fabric's sharing capabilities.

---

## 2. Data Sensitivity & Classification

All data sources used in this project are **publicly available** and contain no PII (personally identifiable information).

### Source classification

| Source | Classification | Notes |
|---|---|---|
| NYC Taxi | **Public** | Anonymized trips, no rider/driver identifiers |
| OpenAQ | **Public** | Open environmental data |
| ECB FX | **Public** | Official ECB statistics |
| World Bank | **Public** | Open development indicators |

### Sensitivity labels (recommended)

If integrating with Microsoft Purview Information Protection, apply the following labels:

- **All artifacts** in this workspace: `Public` or `General`
- No `Confidential` or `Restricted` data is present

### API keys and credentials

The **OpenAQ API key** is the only credential in the system. It is:
- Stored as a literal string inside the Dataflow Gen2 M code (current implementation)
- **Should be migrated to Azure Key Vault** or Fabric workspace identity for production use
- Rotated immediately if exposed in screenshots, logs, or version control

---

## 3. Data Retention

Retention policies balance analytical needs with storage costs.

| Layer | Retention | Rationale |
|---|---|---|
| **Bronze (Files)** | 90 days | Source data is re-downloadable; only recent files needed for re-processing |
| **Bronze (Tables)** | 90 days | API responses can be re-fetched if needed |
| **Silver** | 1 year | Supports troubleshooting and audit trails |
| **Gold** | Indefinite (current implementation: overwrite) | Aggregated, business-critical |
| **Warehouse views** | Indefinite | Virtual, no storage cost |
| **Power BI reports** | Indefinite | Final deliverable |

### Delta time travel

Delta Lake retains historical versions for 7 days by default. For longer history:
- Use `VACUUM` command sparingly to preserve audit history
- Configure `delta.deletedFileRetentionDuration` per table if regulatory requirements arise

### Cleanup procedure

Monthly cleanup of Bronze files older than 90 days using a scheduled notebook (not yet implemented; recommended for production).

---

## 4. Refresh & Update Schedule

### Current state

All ingestion is **on-demand** (manually triggered). Suitable for the academic/learning scope of this project.

### Recommended production schedule

| Source | Recommended frequency | Reason |
|---|---|---|
| NYC Taxi | **Monthly** (5th day of each month) | TLC publishes monthly with ~2-month lag |
| OpenAQ | **Daily** (early morning UTC) | Daily aggregates become stable after midnight UTC |
| ECB FX | **Daily** (after ECB publish time, ~16:00 CET) | New rate published each business day |
| World Bank GDP | **Annually** (Q3) | GDP data updates yearly |

### Implementation paths

- **Schedule on individual artifacts:** Right-click pipeline/dataflow → Settings → Schedule
- **Orchestrate end-to-end:** Build a master pipeline (`PL_Master_Orchestration`) that triggers Bronze → Silver → Gold notebooks in order
- **Notifications on failure:** Configure pipeline activities to send email or Teams alerts on failure

### Refresh dependencies

```
Bronze ingestion → Silver notebooks → Gold notebooks → (Warehouse auto-refreshes via views)
```

Silver and Gold notebooks must run **after** their corresponding Bronze sources have completed.

---

## 5. Data Quality Standards

Data quality rules applied at the Silver layer prevent invalid data from propagating downstream.

### Quality rules — by source

#### Taxi trips
- `trip_distance > 0` and `< 200` miles
- `fare_amount > 0` and `< 1000` USD
- `passenger_count` between 1 and 8
- `trip_duration_min > 0` and `< 600` minutes (10 hours)
- `year(pickup_ts) = 2024`
- Duplicates removed on natural key (pickup_ts, dropoff_ts, PULocationID, DOLocationID, fare_amount)

#### Air quality
- `value >= 0` (negative readings rejected as sensor errors)
- `parameter_name` restricted to known pollutants (pm25, no2, o3)
- `measurement_date` not null
- Duplicates removed on (sensor_id, measurement_date, parameter_name)

#### FX rates
- `usd_eur_rate` not null and positive
- `fx_date` not null
- Duplicates removed on fx_date

#### GDP
- `gdp_usd` not null and positive
- `country_code = 'USA'`
- `year` not null

### Monitoring (recommended)

In production, add row count assertions to each Silver notebook:

```python
expected_min_rows = 100_000
actual_count = df_silver.count()
assert actual_count >= expected_min_rows, f"Row count {actual_count} below threshold"
```

### Data quality issues to track

- Null FX rates on weekends and holidays — by design, no forward-fill applied
- Sensor downtime in OpenAQ — handled by `try ... otherwise` in Dataflow Gen2
- Year filter on Taxi data — discards trips with corrupted timestamps

---

## 6. Naming Conventions

Consistent naming across the workspace prevents confusion as artifacts grow.

### Artifact prefixes

| Prefix | Type | Example |
|---|---|---|
| `LH_` | Lakehouse | `LH_Bronze`, `LH_Silver`, `LH_Gold` |
| `WH_` | Warehouse | `WH_Analytics` |
| `PL_` | Pipeline | `PL_Bronze_Taxi`, `PL_Master_Orchestration` |
| `DF_` | Dataflow | `DF_Bronze_OpenAQ`, `DF_Bronze_WorldBank` |
| `NB_` | Notebook | `NB_Silver_Taxi`, `NB_Gold_DimDate` |
| `SM_` | Semantic Model | `SM_Analytics` |

### Table prefixes

| Prefix | Type | Example |
|---|---|---|
| `Dim` | Dimension table | `DimDate` |
| `Fact` | Fact table | `FactTaxiDaily`, `FactGDPYearly` |
| `vw_` | View | `vw_FactTaxiDaily`, `vw_TaxiWithAirQuality` |
| `_raw` | Bronze raw table | `openaq_measurements_raw` |
| `_clean` | Silver cleaned table | `taxi_trips_clean`, `air_quality_clean` |

### Column conventions

- Lower snake_case for derived columns: `pickup_date`, `trip_duration_min`, `total_fare_eur`
- Original column names preserved when not transformed: `PULocationID`, `VendorID`
- Aggregated columns use suffix: `_count`, `_avg`, `_sum`, `_total`

---

## 7. Change Management

### Schema changes

Any change to Silver or Gold table schemas (add/remove/rename columns) must be:

1. **Documented** in the data dictionary (`DATA_DICTIONARY.md`)
2. **Communicated** to downstream consumers (Power BI report authors)
3. **Versioned** if breaking — append `_v2` suffix to the table name and deprecate the old version

### Notebook changes

- Use **markdown cells** to document intent before each major transformation block
- Test changes on a small sample before running on full dataset
- For F2 capacity: stop any running Spark session before re-running modified notebooks

### Version control (recommended for production)

Currently, code lives only in Fabric notebooks. For production:

- Enable **Fabric Git integration** at the workspace level
- Connect to an Azure DevOps or GitHub repository
- Use feature branches and pull requests for non-trivial changes
- Tag releases when promoting changes to a production workspace

---

## 8. Cost Management

### Capacity model

The project runs on **F2 Fabric capacity** (~$0.36 / hour active, $0 paused).

### Cost-saving practices

1. **Pause capacity when not in use:** Azure portal → fabriclearning → Pause
2. **Stop Spark sessions** between notebook runs (F2 supports only 1 concurrent Spark job)
3. **Limit data scope** during development (e.g., 1 month of Taxi data instead of 12)
4. **Use OPTIMIZE and VACUUM** sparingly on Delta tables to control storage growth

### Budget alerts

A monthly budget of **$20 USD** is configured in Azure Cost Management with alerts at:
- 50% ($10) — informational email
- 80% ($16) — warning email
- 100% ($20) — critical email

### Capacity sizing

F2 is sufficient for this scope but limits concurrency. For scenarios with multiple users or scheduled workloads:
- F4 doubles the compute (~$0.72 / hour)
- F64 enables Power BI Premium features (~$11.50 / hour, not needed here)

---

## 9. Security & Secrets

### Current state

- **OpenAQ API key** is hardcoded in the Dataflow Gen2 M script — acceptable for academic use but **not production-grade**
- All other sources are anonymous (no authentication)
- Workspace is hosted in a personal tenant (`*.onmicrosoft.com`) created via Azure

### Recommended improvements

1. **Move API keys to Azure Key Vault**
   - Create a Key Vault in `rg-dataplatform`
   - Store `openaq-api-key` as a secret
   - Reference it from Dataflow Gen2 via Fabric workspace identity

2. **Enable workspace identity**
   - Allows Fabric to access Azure resources without user credentials
   - Configured under Workspace settings → Workspace identity

3. **Rotate API keys quarterly**
   - OpenAQ keys do not expire automatically but should be rotated as a best practice

4. **Avoid exposing secrets**
   - Never commit keys to Git
   - Never include keys in screenshots, exported notebooks, or shared queries
   - Rotate immediately if accidentally exposed

---

## 10. Monitoring & Auditing

### Built-in Fabric monitoring

- **Monitoring hub** (left navigation): shows pipeline and dataflow run history
- **Capacity metrics app**: tracks CU usage, throttling events
- **Activity log** (Admin portal): audit who did what

### Recommended monitoring practices

1. **Check pipeline run status** after each scheduled execution
2. **Monitor capacity usage** to ensure F2 SKU is not throttled regularly
3. **Track data freshness** by querying `MAX(date_key)` from Gold facts daily

### Alerting (production extension)

For production, configure:
- **Email alerts** on pipeline failures
- **Microsoft Teams notifications** for SLA breaches
- **Azure Monitor** integration for capacity-level metrics

---

## Compliance & Future Considerations

### Regulatory

This project uses only publicly available datasets and is not subject to GDPR, HIPAA, or other personal-data regulations.

### Audit trail

Delta Lake provides time-travel for 7 days, enabling point-in-time recovery and audit of all writes to Silver and Gold tables.

### Disaster recovery

OneLake data is replicated across availability zones within the East Asia region by default. For multi-region recovery:
- Configure Azure Backup on OneLake (Fabric feature, when available in preview region)
- Export critical tables to Azure Blob Storage as Parquet snapshots

### Future governance enhancements

- **Microsoft Purview integration** for cross-tenant lineage and classification
- **Row-Level Security (RLS)** in Power BI if multi-tenant reporting becomes a requirement
- **Sensitivity labels** propagated from source to consumption
- **Endorsement** of certified datasets via Fabric's promotion features
