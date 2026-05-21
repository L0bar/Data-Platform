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

df_gdp = spark.table("LH_Silver.gdp_yearly")

df_fact_gdp = df_gdp.select(
    "year",
    "gdp_usd",
    "gdp_billion_usd",
    "gdp_trillion_usd"
)

df_fact_gdp.write.mode("overwrite").format("delta").saveAsTable("LH_Gold.FactGDPYearly")

df_fact_gdp.show(5)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
