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

df_aq_raw = spark.table("LH_Bronze.openaq_measurements_raw")
df_aq_raw.printSchema()
df_aq_raw.show(5)

df_aq_silver = (
    df_aq_raw
    .withColumn("measurement_date", F.to_date("measurement_date"))
    
    .withColumn("year", F.year("measurement_date"))
    .withColumn("month", F.month("measurement_date"))
    
    .withColumn("value", F.round(F.col("value"), 3))
    
    .filter(F.col("measurement_date").isNotNull())
    .filter(F.col("value").isNotNull())
    .filter(F.col("value") >= 0)
    .filter(F.col("parameter_name").isin("pm25", "no2", "o3"))
    
    .select(
        "sensor_id",
        "measurement_date",
        "year",
        "month",
        "parameter_name",
        "parameter_units",
        "value"
    )
    
    .dropDuplicates(["sensor_id", "measurement_date", "parameter_name"])
        .orderBy("measurement_date", "sensor_id")
)

silver_count = df_aq_silver.count()
df_aq_silver.groupBy("parameter_name").count().show()
df_aq_silver.show(10)
df_aq_silver.write.mode("overwrite").format("delta").saveAsTable("LH_Silver.air_quality")
verify = spark.table("LH_Silver.air_quality")
verify.show(10)



# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
