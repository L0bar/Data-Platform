# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "8f579e92-09f3-4bec-9775-b62c86147853",
# META       "default_lakehouse_name": "LH_Silver",
# META       "default_lakehouse_workspace_id": "b200716b-df87-4d85-855d-bba1dc5bec4b",
# META       "known_lakehouses": [
# META         {
# META           "id": "8f579e92-09f3-4bec-9775-b62c86147853"
# META         },
# META         {
# META           "id": "f86bc9c1-135f-483e-bcf9-25c5ba37274b"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************


from pyspark.sql import functions as F

df_taxi = spark.table("LH_Silver.taxi_trips")
df_fx = spark.table("LH_Silver.exchange_rates_daily")

df_fact_taxi = (
    df_taxi
    .groupBy("pickup_date", "PULocationID")
    .agg(
        F.count("*").alias("trip_count"),
        F.round(F.sum("fare_amount"), 2).alias("total_fare_usd"),
        F.round(F.avg("trip_duration_min"), 2).alias("avg_duration_min"),
        F.round(F.sum("trip_distance"), 2).alias("total_distance_mi")
    )
)

df_fx_clean = df_fx.select(
    F.col("fx_date"),
    F.col("usd_eur_rate")
)

df_fact_taxi = (
    df_fact_taxi
    .join(df_fx_clean, df_fact_taxi.pickup_date == df_fx_clean.fx_date, "left")
    .withColumn(
        "total_fare_eur",
        F.round(F.col("total_fare_usd") * F.col("usd_eur_rate"), 2)
    )
    .drop("fx_date")
)

df_fact_taxi = df_fact_taxi.withColumn(
    "date_key",
    F.date_format("pickup_date", "yyyyMMdd").cast("int")
)

df_fact_taxi = df_fact_taxi.select(
    "date_key",
    "pickup_date",
    "PULocationID",
    "trip_count",
    "total_fare_usd",
    "total_fare_eur",
    "usd_eur_rate",
    "avg_duration_min",
    "total_distance_mi"
)

df_fact_taxi.write.mode("overwrite").format("delta").saveAsTable("LH_Gold.FactTaxiDaily")

df_fact_taxi.show(5)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
