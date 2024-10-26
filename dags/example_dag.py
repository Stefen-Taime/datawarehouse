from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import pandas as pd
import psycopg2

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def example_pandas_operation():
    # Example pandas operation
    df = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
    print(df.head())
    return "Success"

with DAG(
    'example_dag',
    default_args=default_args,
    description='Example DAG with Pandas',
    schedule_interval=timedelta(days=1),
) as dag:

    task = PythonOperator(
        task_id='example_task',
        python_callable=example_pandas_operation,
    )