import re
from google.cloud import storage
from google.cloud import bigquery
import os


bucket_name = 'sur-test-bucket91'
stag_table_id = 'sur-cloud-fun.sur_test_ds.sur_bq_stag'
tar_table_id = 'sur-cloud-fun.sur_test_ds.sur_bq_tar'
job_config = bigquery.LoadJobConfig(schema = [bigquery.SchemaField("name", "STRING", "NULLABLE"),
                                            bigquery.SchemaField("sales", "INTEGER", "NULLABLE"),
                                            bigquery.SchemaField("city", "STRING", "NULLABLE"),
          ],
                                    source_format=bigquery.SourceFormat.CSV,
                                    skip_leading_rows=1,
)


# load data into bigquery from gcs uri
def gcs_to_bq():
    # initilize client object
    s_client = storage.Client()
    b_client = bigquery.Client()
    # list matching file from the gcs bucket
    bucket = s_client.get_bucket(bucket_name)
    blobs = bucket.list_blobs()
    for blob in blobs:
        if re.search(r'sur_test_\d{8}.csv', blob.name):
            file_name = blob.name
            print(file_name)
            gcs_uri = f'gs://{bucket_name}/{file_name}'

            # loading data into bigquery staging from uri
            load_job = b_client.load_table_from_uri(gcs_uri, stag_table_id, job_config=job_config)
            load_job.result()
            stag_table_row_count = b_client.get_table(stag_table_id)
            print(f'loaded {stag_table_row_count.num_rows} rows into stagging "{stag_table_id}" table.')

            # loading data into bigquery target from staging
            sql_query_tar = f'''INSERT INTO `{tar_table_id}`
            SELECT name, sales, city, 
                '{file_name}' as file_name,
                PARSE_DATE('%Y%m%d', regexp_extract('{file_name}' , r'sur_test_(\d{8}).csv')) as file_date,
                current_timestamp() as receive_timestamp
                FROM `{stag_table_id}`
            '''
            load_job_tar = b_client.query(sql_query_tar)
            load_job_tar.result()
            print('loaded data into target "{}" table.'.format(tar_table_id))

            # truncate stagging table
            sql_query_trun = f'''TRUNCATE TABLE `{stag_table_id}`'''
            trun_job = b_client.query(sql_query_trun)
            trun_job.result()
            print(f'stagging table "{stag_table_id}" has truncated.')
    return None
    

if __name__ == '__main':
    gcs_to_bq()

