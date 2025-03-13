print('hello world')

from pyspark.sql import SparkSession
from pyspark.sql.functions import *

spark = SparkSession.builder.appName('myApp').getOrCreate()

orders = spark.read.csv(
    'gs://surretail/scripts/mark.csv',
    schema='name STRING, age INT, city STRING',
    header=True
)

orders.show()

orders. \
    write. \
    mode('overwrite'). \
    format('bigquery'). \
    option("temporaryGcsBucket", "dataproc-temp-us-central1-162950414733-s0wab7hf"). \
    option('table', f'powerful-layout-445408-p5:sur_test_ds.sur_table'). \
    save()

print("data loaded into bigquery")
