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
# META           "id": "a20c4fee-6f4c-4826-bb20-9f7c6dc1a057"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

from pyspark.sql import functions as F
from pyspark.sql.types import *

file_path = """abfss://b200716b-df87-4d85-855d-bba1dc5bec4b@onelake.dfs.fabric.microsoft.com/a20c4fee-6f4c-4826-bb20-9f7c6dc1a057/Files/nyc_taxi/yellow/yyyy=2024/mm=01/yellow_tripdata_2024-01.parquet"""

df_taxi_raw = spark.read.parquet(file_path)

df_taxi_silver = (
    df_taxi_raw
    .withColumnRenamed("tpep_pickup_datetime", "pickup_ts")
    .withColumnRenamed("tpep_dropoff_datetime", "dropoff_ts")
    
    .withColumn("pickup_date", F.to_date("pickup_ts"))
    .withColumn("trip_duration_min",  F.round((F.unix_timestamp("dropoff_ts") - F.unix_timestamp("pickup_ts")) / 60).cast("int"))
    .filter(F.col("trip_distance") > 0)
    .filter(F.col("trip_distance") < 200)
    .filter(F.col("fare_amount") > 0)
    .filter(F.col("fare_amount") < 1000) 
    .filter(F.col("passenger_count").between(1, 8))
    .filter(F.col("trip_duration_min") > 0)
    .filter(F.col("trip_duration_min") < 600) 
    .filter(F.year("pickup_ts") == 2024)
    
    .select(
        "VendorID",
        "pickup_ts",
        "dropoff_ts",
        "pickup_date",
        "passenger_count",
        "trip_distance",
        "PULocationID",
        "DOLocationID",
        "fare_amount",
        "tip_amount",
        "total_amount",
        "trip_duration_min"
    )
    
    .dropDuplicates(["pickup_ts", "dropoff_ts", "PULocationID", "DOLocationID", "fare_amount"])
)

df_taxi_silver.write.mode("overwrite").format("delta").saveAsTable("LH_Silver.taxi_trips")
verify = spark.table("LH_Silver.taxi_trips")
verify.show(5)



# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
