from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.models.baseoperator import chain
import pandas as pd
import json
import xml.etree.ElementTree as ET
from sqlalchemy import create_engine

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

def get_warehouse_engine():
    """Create SQLAlchemy engine for warehouse connection"""
    return create_engine(
        'postgresql://admin:adminpassword@warehouse:5432/myapp'
    )

def extract_and_load_clients():
    """Extract clients data from CSV and load into warehouse"""
    try:
        # Lecture du CSV
        df = pd.read_csv('/opt/airflow/data/clients.csv')
        
        # Transformation
        df['valid_from'] = datetime.now().date()
        df['valid_to'] = '9999-12-31'
        df['is_current'] = True
        
        # Sélectionner uniquement les colonnes nécessaires
        columns = [
            'client_id', 'nom', 'prenom', 'email', 'segment',
            'ville', 'code_postal', 'date_inscription',
            'valid_from', 'valid_to', 'is_current'
        ]
        df = df[columns]
        
        # Chargement dans la dimension client
        engine = get_warehouse_engine()
        df.to_sql('dim_client', engine, if_exists='append', index=False)
        
    except Exception as e:
        print(f"Error in extract_and_load_clients: {str(e)}")
        raise

def extract_and_load_products():
    """Extract products data from JSON and load into warehouse"""
    try:
        # Lecture du JSON
        with open('/opt/airflow/data/products.json', 'r') as f:
            products = json.load(f)
        
        df = pd.DataFrame(products)
        
        # Transformation
        df['valid_from'] = datetime.now().date()
        df['valid_to'] = '9999-12-31'
        df['is_current'] = True
        
        # Sélectionner uniquement les colonnes nécessaires
        columns = [
            'product_id', 'nom_produit', 'categorie', 'prix_unitaire',
            'valid_from', 'valid_to', 'is_current'
        ]
        df = df[columns]
        
        # Chargement dans la dimension produit
        engine = get_warehouse_engine()
        df.to_sql('dim_produit', engine, if_exists='append', index=False)
        
    except Exception as e:
        print(f"Error in extract_and_load_products: {str(e)}")
        raise

def extract_and_load_transactions():
    """Extract transactions data from XML and load into warehouse"""
    try:
        # Lecture du XML
        tree = ET.parse('/opt/airflow/data/transactions.xml')
        root = tree.getroot()
        
        transactions = []
        for trans in root.findall('transaction'):
            transaction = {}
            for child in trans:
                transaction[child.tag] = child.text
            transactions.append(transaction)
        
        df = pd.DataFrame(transactions)
        
        # Transformation des dates pour la dimension temps
        df['date_transaction'] = pd.to_datetime(df['date_transaction'])
        dates_df = pd.DataFrame({
            'date_complete': df['date_transaction'].dt.date.unique()
        })
        
        dates_df['year'] = pd.to_datetime(dates_df['date_complete']).dt.year
        dates_df['quarter'] = pd.to_datetime(dates_df['date_complete']).dt.quarter
        dates_df['month'] = pd.to_datetime(dates_df['date_complete']).dt.month
        dates_df['week'] = pd.to_datetime(dates_df['date_complete']).dt.isocalendar().week
        dates_df['day'] = pd.to_datetime(dates_df['date_complete']).dt.day
        dates_df['day_of_week'] = pd.to_datetime(dates_df['date_complete']).dt.dayofweek
        dates_df['is_weekend'] = dates_df['day_of_week'].isin([5, 6])
        
        # Chargement des dimensions et faits
        engine = get_warehouse_engine()
        dates_df.to_sql('dim_time', engine, if_exists='append', index=False)
        
        # Sélectionner uniquement les colonnes nécessaires pour le staging
        staging_columns = [
            'transaction_id', 'client_id', 'product_id', 'date_transaction',
            'quantite', 'prix_unitaire', 'montant_total', 'moyen_paiement'
        ]
        df = df[staging_columns]
        df.to_sql('staging_transactions', engine, if_exists='replace', index=False)
        
    except Exception as e:
        print(f"Error in extract_and_load_transactions: {str(e)}")
        raise

# SQL pour charger la table de faits depuis le staging
LOAD_FACT_VENTES_SQL = """
INSERT INTO fact_ventes (
    client_key, produit_key, time_id, transaction_id,
    quantite, prix_unitaire, montant_total, moyen_paiement
)
SELECT 
    dc.client_key,
    dp.produit_key,
    dt.time_id,
    st.transaction_id::bigint,
    st.quantite::integer,
    st.prix_unitaire::decimal(10,2),
    st.montant_total::decimal(10,2),
    st.moyen_paiement
FROM staging_transactions st
JOIN dim_client dc ON st.client_id::integer = dc.client_id
JOIN dim_produit dp ON st.product_id::integer = dp.product_id
JOIN dim_time dt ON DATE(st.date_transaction) = dt.date_complete
WHERE dc.is_current = true AND dp.is_current = true;

-- Clean up staging table
TRUNCATE TABLE staging_transactions;
"""

with DAG(
    'dw_etl',
    default_args=default_args,
    description='ETL pour le Data Warehouse',
    schedule_interval='@daily',
    catchup=False,
    tags=['warehouse', 'etl']
) as dag:

    load_clients = PythonOperator(
        task_id='load_clients',
        python_callable=extract_and_load_clients,
        retries=3,
        retry_delay=timedelta(minutes=1),
    )

    load_products = PythonOperator(
        task_id='load_products',
        python_callable=extract_and_load_products,
        retries=3,
        retry_delay=timedelta(minutes=1),
    )

    load_transactions = PythonOperator(
        task_id='load_transactions',
        python_callable=extract_and_load_transactions,
        retries=3,
        retry_delay=timedelta(minutes=1),
    )

    load_fact_ventes = PostgresOperator(
        task_id='load_fact_ventes',
        postgres_conn_id='warehouse_conn',
        sql=LOAD_FACT_VENTES_SQL,
        retries=3,
        retry_delay=timedelta(minutes=1),
    )

    # Define dependencies
    chain(
        [load_clients, load_products],
        load_transactions,
        load_fact_ventes
    )
