from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.utils.task_group import TaskGroup
from datetime import timedelta
from airflow.operators.empty import EmptyOperator

default_args = {
    "owner": "data-platform",
}

with DAG(
    dag_id="task_group_dag22",
    default_args=default_args,
    schedule_interval="0 14 * * *",  # 2 PM daily
    start_date=days_ago(1),
    catchup=False,
) as dag:

    start = EmptyOperator(task_id="start")
    # a = EmptyOperator(task_id="task_a")
    # a1 = EmptyOperator(task_id="task_a1")
    # b = EmptyOperator(task_id="task_b")
    # c = EmptyOperator(task_id="task_c")
    # d = EmptyOperator(task_id="task_d")
    # e = EmptyOperator(task_id="task_e")
    # f = EmptyOperator(task_id="task_f")
    # g = EmptyOperator(task_id="g")
    end = EmptyOperator(task_id="end")

    # start >> a >> a1 >> b >> c >> d >> e >> f >> g >> end

    with TaskGroup("group1", tooltip="Tasks in group 1") as group1:
        a = EmptyOperator(task_id="task_a")
        a1 = EmptyOperator(task_id="task_a1")
        b = EmptyOperator(task_id="task_b")
        c = EmptyOperator(task_id="task_c")
        a >> a1

    with TaskGroup("d-e-f", tooltip="Tasks in group 2") as group2:
        d = EmptyOperator(task_id="task_d")

        with TaskGroup("e-f-g", tooltip="Tasks in group 3") as subgroup2:
            e = EmptyOperator(task_id="task_e")
            f = EmptyOperator(task_id="task_f")
            g = EmptyOperator(task_id="task_g")
            e >> f
            e >> g

    start >> group1 >> group2 >> end





