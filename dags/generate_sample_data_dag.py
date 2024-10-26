from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import sys
import os

# Add scripts directory to Python path
sys.path.append('/opt/airflow/scripts')

from generate_data import main as generate_data

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'generate_sample_data',
    default_args=default_args,
    description='Generate sample data in CSV, JSON, and XML formats',
    schedule_interval='@daily',
    catchup=False,
    tags=['data_generation'],
) as dag:

    # Create required directories
    create_directories = BashOperator(
        task_id='create_directories',
        bash_command='mkdir -p /opt/airflow/{data,logs} && chmod -R 777 /opt/airflow/{data,logs}',
    )

    # Generate sample data
    generate_data_task = PythonOperator(
        task_id='generate_sample_data',
        python_callable=generate_data,
        retries=3,
        retry_delay=timedelta(minutes=1),
    )

    create_directories >> generate_data_task