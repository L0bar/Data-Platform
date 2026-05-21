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

df_fx_raw = spark.read.option("header", True).csv(
    "abfss://b200716b-df87-4d85-855d-bba1dc5bec4b@onelake.dfs.fabric.microsoft.com/a20c4fee-6f4c-4826-bb20-9f7c6dc1a057/Files/exchange_rate_euro_usd/euro_usd_daily.csv"
)

df_fx_silver = (
    df_fx_raw
    .select(
        F.to_date(F.col("TIME_PERIOD"), "yyyy-MM-dd").alias("fx_date"),
        F.col("OBS_VALUE").cast("double").alias("usd_eur_rate")
    )
    
    .filter(F.col("fx_date").isNotNull())
    .filter(F.col("usd_eur_rate").isNotNull())
    .filter(F.col("usd_eur_rate") > 0)
    
    .dropDuplicates(["fx_date"])
    
    .orderBy("fx_date")
)

silver_count = df_fx_silver.count()

df_fx_silver.show(10)
df_fx_silver.printSchema()

df_fx_silver.write.mode("overwrite").format("delta").saveAsTable("LH_Silver.exchange_rates_daily")


verify = spark.table("LH_Silver.exchange_rates_daily")
verify.show(10)



# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
