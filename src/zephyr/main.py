from pyspark.sql import SparkSession

from zephyr.etl.cleaning import clean_data
from zephyr.etl.feature_engineering import add_feature_columns

# run spark locally, not on a cluster, because we ssh into my mac and run the
# container there :)
# * means use all available CPU cores
spark = SparkSession.builder.master("local[*]").getOrCreate()

df = spark.read.csv("data/raw/dataset.csv", header=True)
df = clean_data(df)
df = add_feature_columns(df)
df.write.mode("overwrite").parquet("data/processed")
