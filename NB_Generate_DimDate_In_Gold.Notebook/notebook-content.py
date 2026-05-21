# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "f86bc9c1-135f-483e-bcf9-25c5ba37274b",
# META       "default_lakehouse_name": "LH_Gold",
# META       "default_lakehouse_workspace_id": "b200716b-df87-4d85-855d-bba1dc5bec4b",
# META       "known_lakehouses": [
# META         {
# META           "id": "f86bc9c1-135f-483e-bcf9-25c5ba37274b"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

from pyspark.sql import functions as F
from pyspark.sql.types import *

df_dates = spark.sql("""
    SELECT explode(sequence(
        to_date('2024-01-01'), 
        to_date('2024-12-31'), 
        interval 1 day
    )) AS full_date
""")

df_dim_date = (
    df_dates
    .withColumn("date_key", F.date_format("full_date", "yyyyMMdd").cast("int"))
    .withColumn("year", F.year("full_date"))
    .withColumn("quarter", F.quarter("full_date"))
    .withColumn("month", F.month("full_date"))
    .withColumn("month_name", F.date_format("full_date", "MMMM"))
    .withColumn("day", F.dayofmonth("full_date"))
    .withColumn("day_of_week", F.dayofweek("full_date"))
    .withColumn("day_name", F.date_format("full_date", "EEEE"))
    .withColumn("week_of_year", F.weekofyear("full_date"))
    .withColumn("is_weekend", F.dayofweek("full_date").isin(1, 7))
    .select(
        "date_key",
        "full_date",
        "year", "quarter", "month", "month_name",
        "day", "day_of_week", "day_name",
        "week_of_year", "is_weekend"
    )
    .orderBy("date_key")
)

df_dim_date.show(10)
df_dim_date.printSchema()
df_dim_date.write.mode("overwrite").format("delta").saveAsTable("LH_Gold.DimDate")
verify = spark.table("LH_Gold.DimDate")
verify.show(5)



# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
