from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# SQL pour créer les dimensions et la table de faits
CREATE_DIM_TIME_SQL = """
CREATE TABLE IF NOT EXISTS dim_time (
    time_id SERIAL PRIMARY KEY,
    date_complete DATE NOT NULL,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    week INTEGER NOT NULL,
    day INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    is_weekend BOOLEAN NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_dim_time_date ON dim_time(date_complete);
"""

CREATE_DIM_CLIENT_SQL = """
CREATE TABLE IF NOT EXISTS dim_client (
    client_key SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL,
    nom VARCHAR(100),
    prenom VARCHAR(100),
    email VARCHAR(150),
    segment VARCHAR(50),
    ville VARCHAR(100),
    code_postal VARCHAR(10),
    region VARCHAR(100),
    date_inscription DATE,
    valid_from DATE NOT NULL,
    valid_to DATE NOT NULL,
    is_current BOOLEAN NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_dim_client_segment ON dim_client(segment);
CREATE INDEX IF NOT EXISTS idx_dim_client_ville ON dim_client(ville);
"""

CREATE_DIM_PRODUIT_SQL = """
CREATE TABLE IF NOT EXISTS dim_produit (
    produit_key SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    nom_produit VARCHAR(200),
    categorie VARCHAR(100),
    prix_unitaire DECIMAL(10,2),
    valid_from DATE NOT NULL,
    valid_to DATE NOT NULL,
    is_current BOOLEAN NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_dim_produit_categorie ON dim_produit(categorie);
"""

CREATE_FACT_VENTES_SQL = """
CREATE TABLE IF NOT EXISTS fact_ventes (
    vente_id SERIAL PRIMARY KEY,
    client_key INTEGER REFERENCES dim_client(client_key),
    produit_key INTEGER REFERENCES dim_produit(produit_key),
    time_id INTEGER REFERENCES dim_time(time_id),
    transaction_id BIGINT,
    quantite INTEGER,
    prix_unitaire DECIMAL(10,2),
    montant_total DECIMAL(10,2),
    moyen_paiement VARCHAR(50)
);

CREATE INDEX IF NOT EXISTS idx_fact_ventes_client ON fact_ventes(client_key);
CREATE INDEX IF NOT EXISTS idx_fact_ventes_produit ON fact_ventes(produit_key);
CREATE INDEX IF NOT EXISTS idx_fact_ventes_time ON fact_ventes(time_id);

-- Create staging table for transactions
CREATE TABLE IF NOT EXISTS staging_transactions (
    transaction_id BIGINT,
    client_id INTEGER,
    product_id INTEGER,
    date_transaction TIMESTAMP,
    quantite INTEGER,
    prix_unitaire DECIMAL(10,2),
    montant_total DECIMAL(10,2),
    moyen_paiement VARCHAR(50)
);
"""

# Création des vues pour Superset
CREATE_SUPERSET_VIEWS_SQL = """
-- Vue pour l'analyse temporelle
CREATE OR REPLACE VIEW v_analyse_temporelle AS
SELECT 
    dt.date_complete,
    dt.year,
    dt.month,
    dt.quarter,
    dt.is_weekend,
    SUM(fv.montant_total) as ventes_totales,
    COUNT(DISTINCT fv.transaction_id) as nb_transactions,
    AVG(fv.montant_total) as panier_moyen,
    COUNT(DISTINCT fv.client_key) as nb_clients_uniques
FROM fact_ventes fv
JOIN dim_time dt ON fv.time_id = dt.time_id
GROUP BY dt.date_complete, dt.year, dt.month, dt.quarter, dt.is_weekend;

-- Vue pour l'analyse géographique
CREATE OR REPLACE VIEW v_analyse_geo AS
SELECT 
    dc.ville,
    dc.code_postal,
    dc.segment,
    SUM(fv.montant_total) as ventes_totales,
    COUNT(DISTINCT fv.client_key) as nb_clients,
    AVG(fv.montant_total) as panier_moyen,
    COUNT(DISTINCT fv.transaction_id) as nb_transactions
FROM fact_ventes fv
JOIN dim_client dc ON fv.client_key = dc.client_key
GROUP BY dc.ville, dc.code_postal, dc.segment;

-- Vue pour l'analyse produits
CREATE OR REPLACE VIEW v_analyse_produits AS
SELECT 
    dp.categorie,
    dp.nom_produit,
    SUM(fv.quantite) as quantite_vendue,
    SUM(fv.montant_total) as ca_total,
    COUNT(DISTINCT fv.transaction_id) as nb_ventes,
    AVG(fv.prix_unitaire) as prix_moyen,
    COUNT(DISTINCT fv.client_key) as nb_clients_uniques
FROM fact_ventes fv
JOIN dim_produit dp ON fv.produit_key = dp.produit_key
GROUP BY dp.categorie, dp.nom_produit;

-- Vue pour l'analyse des segments clients
CREATE OR REPLACE VIEW v_analyse_segments AS
SELECT 
    dc.segment,
    dt.year,
    dt.month,
    COUNT(DISTINCT fv.client_key) as nb_clients,
    SUM(fv.montant_total) as ventes_totales,
    AVG(fv.montant_total) as panier_moyen,
    COUNT(DISTINCT fv.transaction_id) as nb_transactions
FROM fact_ventes fv
JOIN dim_client dc ON fv.client_key = dc.client_key
JOIN dim_time dt ON fv.time_id = dt.time_id
GROUP BY dc.segment, dt.year, dt.month;
"""

with DAG(
    'dw_create_schema',
    default_args=default_args,
    description='Création du schéma du Data Warehouse',
    schedule_interval='@once',
    catchup=False,
    tags=['warehouse', 'schema']
) as dag:

    create_dim_time = PostgresOperator(
        task_id='create_dim_time',
        postgres_conn_id='warehouse_conn',
        sql=CREATE_DIM_TIME_SQL
    )

    create_dim_client = PostgresOperator(
        task_id='create_dim_client',
        postgres_conn_id='warehouse_conn',
        sql=CREATE_DIM_CLIENT_SQL
    )

    create_dim_produit = PostgresOperator(
        task_id='create_dim_produit',
        postgres_conn_id='warehouse_conn',
        sql=CREATE_DIM_PRODUIT_SQL
    )

    create_fact_ventes = PostgresOperator(
        task_id='create_fact_ventes',
        postgres_conn_id='warehouse_conn',
        sql=CREATE_FACT_VENTES_SQL
    )

    create_superset_views = PostgresOperator(
        task_id='create_superset_views',
        postgres_conn_id='warehouse_conn',
        sql=CREATE_SUPERSET_VIEWS_SQL
    )

    [create_dim_time, create_dim_client, create_dim_produit] >> create_fact_ventes >> create_superset_views
