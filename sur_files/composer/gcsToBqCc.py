from airflow import models
from airflow.providers.google.cloud.operators.gcs import GCSListObjectsOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from airflow.providers.google.cloud.transfers.gcs_to_gcs import GCSToGCSOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.operators.python import BranchPythonOperator
from airflow.operators.email import EmailOperator
from airflow.utils.dates import days_ago
from datetime import timedelta

# Constants
BUCKET_NAME = "sur_test_bkt"
SUB_FOLDER_NAME = "sub_folder/"
FILE_PATTERN = "file1_"
GCP_PROJECT_ID = "powerful-layout-445408-p5"
DATASET_NAME = "sur_test_ds"
TABLE_NAME = "sur_table02"
BQ_PROCEDURE = "sur_proc01"
DEST_BUCKET_NAME = "sur_arc_bkt"
DEST_SUBFOLDER_NAME = "arc_folder/"

def check_file(ti):
    """Check if files exist in GCS and return the appropriate next task."""
    files = ti.xcom_pull(task_ids='list_files')  # Correct task ID
    print(f"Files Found: {files}")

    # Filter files matching the pattern
    matching_files = [f for f in files if f.startswith(SUB_FOLDER_NAME + FILE_PATTERN)]

    if matching_files:
        return "gcs_to_bq_ti"
    return "send_email_alert_ti"

# Define DAG
with models.DAG(
    dag_id="gcs_bigquery_cc44",
    description="DAG to load data into BigQuery if files exist in GCS",
    schedule_interval="30 10 * * *",
    start_date=days_ago(1),
    catchup=False,
    default_args={
        'depends_on_past': True,
        'retries': 2,
        'retry_delay': timedelta(seconds=10),
        'email_on_retry': False
    }
) as dag:
    
    # List all files in the GCS folder
    list_files = GCSListObjectsOperator(
        task_id='list_files',  # Fixed task ID
        bucket=BUCKET_NAME,
        prefix=SUB_FOLDER_NAME,  # List all files in the sub-folder
        gcp_conn_id='google_cloud_storage_default'
    )

    # Check file existence and decide next step
    check_file_exist = BranchPythonOperator(
        task_id='check_file_exist_ti',
        python_callable=check_file
    )

    gcs_to_bq_ti = GCSToBigQueryOperator(
        task_id='gcs_to_bq_ti',
        bucket=BUCKET_NAME,
        source_objects=[SUB_FOLDER_NAME + "file1_*.csv"],
        source_format="CSV",
        field_delimiter=",",
        destination_project_dataset_table=f"{GCP_PROJECT_ID}.{DATASET_NAME}.{TABLE_NAME}",
        autodetect=True,
        write_disposition="WRITE_APPEND",
        skip_leading_rows=1,
        gcp_conn_id="google_cloud_default"
    )

    send_email_alert_ti = EmailOperator(
        task_id='send_email_alert_ti',
        to=["seshumachavapu@gmail.com", "suresh.machavarapu91@gmail.com"],
        subject="GCS File Missing Alert",
        html_content=f"""
        <p>No files matching <b>{SUB_FOLDER_NAME}{FILE_PATTERN}*.csv</b> 
        found in GCS bucket <b>{BUCKET_NAME}</b>. Data load skipped.</p>
        """
    )

    # Move files from one GCS subfolder to another
    move_gcs_files = GCSToGCSOperator(
        task_id="move_gcs_files",
        source_bucket=BUCKET_NAME,
        source_objects=[SUB_FOLDER_NAME + "file1_*.csv"],  # Move matching files only
        destination_bucket=DEST_BUCKET_NAME,
        destination_object=f"{DEST_SUBFOLDER_NAME}file1_*.csv",  # Corrected destination path
        move_object=True,  # Set to True to delete from source after copying
        gcp_conn_id="google_cloud_storage_default",
    )

    # Run BigQuery Stored Procedure
    run_bq_procedure = BigQueryInsertJobOperator(
        task_id="run_bq_procedure",
        configuration={
            "query": {
                "query": f"CALL `{GCP_PROJECT_ID}.{DATASET_NAME}.{BQ_PROCEDURE}`();",
                "useLegacySql": False,
            }
        },
        location="us-central1",
        gcp_conn_id="google_cloud_default",
    )

    # Task dependencies
    list_files >> check_file_exist
    check_file_exist >> [gcs_to_bq_ti, send_email_alert_ti]
    gcs_to_bq_ti >> move_gcs_files >> run_bq_procedure
