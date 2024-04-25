from pyspark.sql import SparkSession

spark = SparkSession.builder.enableHiveSupport().getOrCreate()

print('Storing random numbers in a GCS bucket')
spark.range(100).write.mode("overwrite").parquet("gs://apt-task-314904/random")
print('complete')