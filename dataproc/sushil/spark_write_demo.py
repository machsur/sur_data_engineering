from pyspark.sql import SparkSession

spark = SparkSession.builder.enableHiveSupport().getOrCreate()

print('Storing random numbers in a hive table')
spark.range(100).write.saveAsTable("random_numbers")
print('complete')
