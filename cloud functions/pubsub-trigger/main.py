from google.cloud import storage
from google.cloud import bigquery
import os
import re
import base64
import functions_framework


bucket_name = 'sur-test-bucket91'
stag_table_id = 'sur-cloud-fun.sur_test_ds.pubsub_stag'
tar_table_id = 'sur-cloud-fun.sur_test_ds.pubsub_tar'
job_config = bigquery.LoadJobConfig(schema = [
    bigquery.SchemaField("name", "STRING", "NULLABLE"),
    bigquery.SchemaField("sales", "INTEGER", "NULLABLE"),
    bigquery.SchemaField("city", "STRING", "NULLABLE"),
],
    source_format = bigquery.SourceFormat.CSV,
    skip_leading_rows=1,)


def gcs_bq_pubsub():
    # list matching files from the gcs bucket.
    s_client = storage.Client()
    bucket = s_client.get_bucket(bucket_name)
    blobs = bucket.list_blobs()
    for blob in blobs:
        pattern = r'^sur_test_\d{8}.csv'
        if re.search(pattern, blob.name):
            file_name = blob.name
            print(file_name)

            # load data into stagging from gcs bucket
            b_client = bigquery.Client()
            gcs_uri = f'gs://{bucket_name}/{file_name}'
            load_job = b_client.load_table_from_uri(gcs_uri, stag_table_id, job_config=job_config)
            load_job.result()
            stag_table_row_count = b_client.get_table(stag_table_id)
            print(f'loaded {stag_table_row_count.num_rows} into "{stag_table_id}".')

            # load data into target from stagging
            query_target = f'''INSERT INTO `{tar_table_id}`
            SELECT name, sales, city, 
                    '{file_name}' as file_name,
                    parse_date("%Y%m%d", regexp_extract('{file_name}', r'_(\d{8}).csv')) as file_date,
                    current_timestamp() as receive_timestamp
            FROM `{stag_table_id}`
            '''
            load_job_tar = b_client.query(query_target)
            load_job_tar.result()
            print('data has loaded into {}'.format(tar_table_id))

            # truncate data from stagging table
            query_trunc = f'''TRUNCATE TABLE `{stag_table_id}`'''
            job_truncate = b_client.query(query_trunc)
            job_truncate.result()
            print('data has truncated from "{}".'.format(stag_table_id))

            # move file into archive bucket class
            source_bucket = s_client.get_bucket(bucket_name)
            destination_bucket = s_client.get_bucket(bucket_name)
            source_blob_name = f'{file_name}'
            destination_blob_name = f'arc_folder/{file_name}'
            source_blob = source_bucket.blob(source_blob_name)
            new_blob = source_bucket.copy_blob(source_blob, destination_bucket, destination_blob_name)
            print(f'File {source_blob_name} moved to {destination_blob_name}')
            source_blob.delete()
    return None


# Triggered from a message on a Cloud Pub/Sub topic.
@functions_framework.cloud_event
def hello_pubsub(cloud_event):
    # Print out the data from Pub/Sub, to prove that it worked
    print(base64.b64decode(cloud_event.data["message"]["data"]))
    gcs_bq_pubsub()


if __name__ == '__main__':
    hello_pubsub(cloud_event)
