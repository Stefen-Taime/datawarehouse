from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

# SQL pour les rapports d'analyse
CREATE_REPORTS_SQL = """
-- Rapport des ventes par segment client
DROP MATERIALIZED VIEW IF EXISTS mv_ventes_par_segment CASCADE;
CREATE MATERIALIZED VIEW mv_ventes_par_segment AS
SELECT 
    COALESCE(dc.segment, 'Non défini') as segment,
    COUNT(DISTINCT fv.transaction_id) as nb_transactions,
    COUNT(DISTINCT dc.client_id) as nb_clients,
    CAST(SUM(fv.montant_total) AS DECIMAL(15,2)) as total_ventes,
    CAST(AVG(fv.montant_total) AS DECIMAL(15,2)) as panier_moyen,
    CAST(SUM(fv.montant_total) / NULLIF(COUNT(DISTINCT dc.client_id), 0) AS DECIMAL(15,2)) as valeur_client_moyenne,
    CAST(COUNT(DISTINCT fv.transaction_id)::float / NULLIF(COUNT(DISTINCT dc.client_id), 0) AS DECIMAL(15,2)) as frequence_achat
FROM fact_ventes fv
JOIN dim_client dc ON fv.client_key = dc.client_key
GROUP BY dc.segment;

-- Rapport des ventes par catégorie de produit
DROP MATERIALIZED VIEW IF EXISTS mv_ventes_par_categorie CASCADE;
CREATE MATERIALIZED VIEW mv_ventes_par_categorie AS
WITH total_ventes AS (
    SELECT SUM(montant_total) as total_global
    FROM fact_ventes
)
SELECT 
    COALESCE(dp.categorie, 'Non catégorisé') as categorie,
    COUNT(DISTINCT fv.transaction_id) as nb_transactions,
    SUM(fv.quantite) as quantite_totale,
    CAST(SUM(fv.montant_total) AS DECIMAL(15,2)) as total_ventes,
    CAST(AVG(fv.prix_unitaire) AS DECIMAL(15,2)) as prix_moyen_unitaire,
    CAST(SUM(fv.montant_total) / NULLIF(SUM(fv.quantite), 0) AS DECIMAL(15,2)) as valeur_moyenne_par_article,
    CAST((SUM(fv.montant_total) / NULLIF(tv.total_global, 0) * 100) AS DECIMAL(15,2)) as part_ca_total
FROM fact_ventes fv
JOIN dim_produit dp ON fv.produit_key = dp.produit_key
CROSS JOIN total_ventes tv
GROUP BY dp.categorie, tv.total_global;

-- Rapport des ventes temporel
DROP MATERIALIZED VIEW IF EXISTS mv_ventes_temporel CASCADE;
CREATE MATERIALIZED VIEW mv_ventes_temporel AS
WITH monthly_sales AS (
    SELECT 
        dt.year,
        dt.month,
        COUNT(DISTINCT fv.transaction_id) as nb_transactions,
        COUNT(DISTINCT dc.client_id) as nb_clients,
        SUM(fv.montant_total) as total_ventes,
        AVG(fv.montant_total) as panier_moyen,
        CONCAT(dt.year, '-', LPAD(dt.month::text, 2, '0')) as mois_annee
    FROM fact_ventes fv
    JOIN dim_time dt ON fv.time_id = dt.time_id
    JOIN dim_client dc ON fv.client_key = dc.client_key
    GROUP BY dt.year, dt.month
),
prev_month_sales AS (
    SELECT 
        year,
        month,
        total_ventes,
        LAG(total_ventes) OVER (ORDER BY year, month) as prev_month_ventes
    FROM monthly_sales
)
SELECT 
    ms.year,
    ms.month,
    ms.mois_annee,
    ms.nb_transactions,
    ms.nb_clients,
    CAST(ms.total_ventes AS DECIMAL(15,2)) as total_ventes,
    CAST(ms.panier_moyen AS DECIMAL(15,2)) as panier_moyen,
    CAST(((ms.total_ventes - pms.prev_month_ventes) / 
          NULLIF(pms.prev_month_ventes, 0) * 100) AS DECIMAL(15,2)) as croissance_mensuelle,
    CAST(ms.total_ventes / NULLIF(ms.nb_clients, 0) AS DECIMAL(15,2)) as revenu_par_client,
    CAST(ms.nb_transactions::float / NULLIF(ms.nb_clients, 0) AS DECIMAL(15,2)) as transactions_par_client
FROM monthly_sales ms
LEFT JOIN prev_month_sales pms ON ms.year = pms.year AND ms.month = pms.month
ORDER BY ms.year, ms.month;

-- Création des index pour optimiser les performances
CREATE INDEX IF NOT EXISTS idx_mv_ventes_segment ON mv_ventes_par_segment(segment);
CREATE INDEX IF NOT EXISTS idx_mv_ventes_categorie ON mv_ventes_par_categorie(categorie);
CREATE INDEX IF NOT EXISTS idx_mv_ventes_temporel_date ON mv_ventes_temporel(year, month);

-- Refresh des vues matérialisées
REFRESH MATERIALIZED VIEW mv_ventes_par_segment;
REFRESH MATERIALIZED VIEW mv_ventes_par_categorie;
REFRESH MATERIALIZED VIEW mv_ventes_temporel;
"""

with DAG(
    'dw_reporting',
    default_args=default_args,
    description='Génération des rapports du Data Warehouse',
    schedule_interval='@daily',
    catchup=False,
    tags=['warehouse', 'reporting']
) as dag:

    create_reports = PostgresOperator(
        task_id='create_reports',
        postgres_conn_id='warehouse_conn',
        sql=CREATE_REPORTS_SQL,
        retries=3,
        retry_delay=timedelta(minutes=1)
    )

    # Définition des dépendances
    create_reports
