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

df_aq = spark.table("LH_Silver.air_quality")

df_fact_aq = (
    df_aq
    .groupBy("measurement_date")
    .pivot("parameter_name", ["pm25", "no2", "o3"])
    .agg(F.round(F.avg("value"), 3))
)

df_fact_aq = (
    df_fact_aq
    .withColumnRenamed("pm25", "pm25_avg")
    .withColumnRenamed("no2", "no2_avg")
    .withColumnRenamed("o3", "o3_avg")
)

df_sensor_count = (
    df_aq
    .groupBy("measurement_date")
    .agg(F.countDistinct("sensor_id").alias("sensor_count"))
)

df_fact_aq = df_fact_aq.join(df_sensor_count, "measurement_date", "left")


df_fact_aq = df_fact_aq.withColumn(
    "date_key", F.date_format("measurement_date", "yyyyMMdd").cast("int")
)

df_fact_aq = df_fact_aq.select(
    "date_key", "measurement_date",
    "pm25_avg", "no2_avg", "o3_avg", "sensor_count"
)

df_fact_aq.write.mode("overwrite").format("delta").saveAsTable("LH_Gold.FactAirQualityDaily")

df_fact_aq.show(5)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
