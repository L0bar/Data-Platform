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

df_gdp_raw = spark.table("LH_Bronze.worldbank_gdp_raw")
df_gdp_raw.printSchema()
df_gdp_raw.show(10)

df_gdp_silver = (
    df_gdp_raw
    .select(
        F.col("country_code").alias("country_code"),
        F.col("country_name").alias("country_name"),
        F.col("year").cast("int").alias("year"),
        F.col("gdp_value").alias("gdp_usd"),
        F.col("indicator_id").alias("indicator_id"),
        F.col("indicator_name").alias("indicator_name")
    )
    
    .filter(F.col("gdp_usd").isNotNull())
    .filter(F.col("gdp_usd") > 0)
    .filter(F.col("year").isNotNull())
    
    .withColumn("gdp_billion_usd", F.round(F.col("gdp_usd") / 1000000000, 2))
    .withColumn("gdp_trillion_usd", F.round(F.col("gdp_usd") / 1000000000000, 3))
    
    .filter(F.col("country_code") == "USA")
    
    .orderBy(F.col("year").desc())
)

silver_count = df_gdp_silver.count()
df_gdp_silver.show(10)
df_gdp_silver.printSchema()

df_gdp_silver.write.mode("overwrite").format("delta").saveAsTable("LH_Silver.gdp_yearly")

verify = spark.table("LH_Silver.gdp_yearly")
verify.show(10)


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
