-- Auto Generated (Do not modify) 209206A5CE8FB8B483264B7FC2DC00BB45FECE6940B57A9711A53E35CA54494F
CREATE   VIEW dbo.vw_TaxiWithAirQuality AS
SELECT 
    t.date_key,
    d.full_date,
    d.year,
    d.month,
    d.month_name,
    d.day_name,
    d.is_weekend,
    t.PULocationID AS zone_id,
    t.trip_count,
    t.total_fare_usd,
    t.total_fare_eur,
    t.usd_eur_rate,
    t.avg_duration_min,
    t.total_distance_mi,
    aq.pm25_avg,
    aq.no2_avg,
    aq.o3_avg,
    aq.sensor_count AS aq_sensor_count
FROM [LH_Gold].[dbo].[facttaxidaily] t
LEFT JOIN [LH_Gold].[dbo].[dimdate] d 
    ON t.date_key = d.date_key
LEFT JOIN [LH_Gold].[dbo].[factairqualitydaily] aq 
    ON t.date_key = aq.date_key WHERE MONTH(t.pickup_date) = 1;