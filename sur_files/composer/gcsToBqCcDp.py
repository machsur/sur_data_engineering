from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.providers.google.cloud.operators.dataproc import DataprocCreateClusterOperator, DataprocDeleteClusterOperator, DataprocSubmitJobOperator

default_args = {
    'start_date': days_ago(1),
    'project_id': 'powerful-layout-445408-p5',
    'region': 'us-central1',
    'cluster_name': 'sur-dp-cl2',
    'bucket_name': 'surretail',
    'pyspark_file': 'test.py'
}

with DAG(
    'dataproc_workflow111',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False
) as dag:
    
    create_cluster = DataprocCreateClusterOperator(
        task_id='create_cluster',
        cluster_name=default_args['cluster_name'],
        project_id=default_args['project_id'],
        region=default_args['region'],
        num_workers=2,
        master_machine_type='n1-standard-2',
        worker_machine_type='n1-standard-2'
    )

    submit_job = DataprocSubmitJobOperator(
        task_id='submit_job',
        job={
            'reference': {'project_id': default_args['project_id']},
            'placement': {'cluster_name': default_args['cluster_name']},
            'pyspark_job': {'main_python_file_uri': f'gs://{default_args["bucket_name"]}/scripts/{default_args["pyspark_file"]}'}  # refere dp job
        },
        region=default_args['region'],
        project_id=default_args['project_id']
    )



    delete_cluster = DataprocDeleteClusterOperator(
        task_id='delete_cluster',
        cluster_name=default_args['cluster_name'],
        project_id=default_args['project_id'],
        region=default_args['region']
    )

    create_cluster >> submit_job >> delete_cluster
