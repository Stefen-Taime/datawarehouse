# Data Warehouse E-commerce Project

## Overview

This project implements a complete data warehouse solution for e-commerce analytics using Apache Airflow, PostgreSQL, and Apache Superset. It includes automated data generation, ETL processes, and analytics dashboards.

## Architecture
### System Architecture Diagram
```mermaid
flowchart TB
    subgraph Sources["Data Sources"]
        direction TB
        S1[("CSV File\nCustomers")] 
        S2[("JSON File\nProducts")]
        S3[("XML File\nTransactions")]
    end

    subgraph DataGen["Data Generation"]
        direction TB
        DG[/"Apache Airflow DAG\nGenerate Data"/]
        PG["Python Script\nGenerator"]
    end

    subgraph Storage["Data Storage"]
        direction TB
        VS[("Volume\n/opt/airflow/data")]
        LOG[("Volume\n/opt/airflow/logs")]
    end

    subgraph ETLLayer["ETL Layer"]
        direction TB
        subgraph Airflow["Apache Airflow"]
            direction TB
            DAG1["DAG\nSchema Creation"]
            DAG2["DAG\nETL Process"]
            DAG3["DAG\nReporting"]
        end
        
        subgraph Process["ETL Process"]
            direction TB
            E["Extraction\nPython Operators"]
            T["Transformation\nPython/SQL"]
            L["Loading\nPostgres Operators"]
        end
    end

    subgraph Warehouse["Data Warehouse"]
        direction TB
        subgraph Dimensions["Dimension Tables"]
            D1["DIM_TIME"]
            D2["DIM_CUSTOMER"]
            D3["DIM_PRODUCT"]
        end
        
        subgraph Facts["Fact Tables"]
            F1["FACT_SALES"]
        end
        
        subgraph Views["Views Layer"]
            V1["Superset\nViews"]
            V2["Materialized\nViews"]
        end
    end

    subgraph Analytics["Analytics Layer"]
        direction TB
        SUP["Apache Superset\nVisualization"]
        BI["BI Tools\nDashboards"]
    end

    %% Connections
    DataGen --> Storage
    S1 & S2 & S3 --> ETLLayer
    ETLLayer --> Warehouse
    Warehouse --> Analytics
    
    %% Detailed Flow
    DG --> PG --> VS
    VS --> E --> T --> L
    DAG1 & DAG2 & DAG3 --> Process
    D1 & D2 & D3 --> F1
    F1 --> V1 & V2
    V1 & V2 --> SUP --> BI

    classDef sourceSystem fill:#e6f3ff,stroke:#333,stroke-width:2px
    classDef storageSystem fill:#f9f3ff,stroke:#333,stroke-width:2px
    classDef processSystem fill:#fff3e6,stroke:#333,stroke-width:2px
    classDef warehouseSystem fill:#e6ffe6,stroke:#333,stroke-width:2px
    classDef analyticsSystem fill:#ffe6e6,stroke:#333,stroke-width:2px

    class S1,S2,S3 sourceSystem
    class VS,LOG storageSystem
    class ETLLayer,Process processSystem
    class Warehouse,Dimensions,Facts,Views warehouseSystem
    class Analytics,SUP,BI analyticsSystem

```plaintext
project/
├── dags/                    # Airflow DAG definitions
│   ├── generate_sample_data.py
│   ├── dw_create_schema.py
│   ├── dw_etl_dag.py
│   └── dw_reporting_dag.py
├── scripts/                 # Python scripts
│   └── generate_data.py
├── data/                    # Generated data files
├── logs/                    # Airflow logs
├── docker-compose.yml       # Docker services configuration
├── requirements.txt         # Python dependencies
└── .env                    # Environment variables
```

## Prerequisites

- Docker and Docker Compose
- 4GB RAM minimum
- 10GB free disk space

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/Stefen-Taime/datawarehouse/
cd datawarehouse
```

2. Create required directories:
```bash
mkdir -p ./dags ./logs ./scripts ./data
```

3. Create .env:
```bash
AIRFLOW_UID=50000
AIRFLOW_GID=50000
AIRFLOW_FERNET_KEY=46BKJoQYlPPOexq0OhDZnIlNepKFf87WFwLbfzqDDho=
```

4. Start the services:
```bash
docker-compose up -d
```

4. Access the services:

- Airflow UI: http://localhost:8080 (admin/admin)
- Adminer: http://localhost:8081
- Data Warehouse: localhost:5433

## Data Pipeline

The project consists of four main DAGs:

1. `generate_sample_data`: Generates sample data
   - Customers (CSV)
   - Products (JSON)
   - Transactions (XML)

2. `dw_create_schema`: Creates warehouse schema
   - Dimension tables
   - Fact tables
   - OLAP views

3. `dw_etl`: Performs ETL operations
   - Extracts from source files
   - Transforms data
   - Loads into warehouse

4. `dw_reporting`: Creates analytics views
   - Materialized views for reporting
   - OLAP cubes
   - Performance optimizations

## Data Model

### Dimension Tables

- `dim_time`: Time dimension
  - Date hierarchies
  - Weekend indicators
  - Fiscal periods

- `dim_client`: Customer dimension (SCD Type 2)
  - Demographics
  - Segments
  - Location

- `dim_produit`: Product dimension (SCD Type 2)
  - Categories
  - Pricing
  - Attributes

### Fact Table

- `fact_ventes`: Sales transactions
  - Foreign keys to dimensions
  - Measures (quantity, amount)
  - Transaction metadata

## Analytics Views

- `mv_ventes_par_segment`: Sales by customer segment
- `mv_ventes_par_categorie`: Sales by product category
- `mv_ventes_temporel`: Time-based sales analysis

## Development

## Troubleshooting

### Common Issues

1. Connection errors:
   ```bash
   # Check network
   docker network ls
   # Verify services
   docker-compose ps
   ```

2. Data loading failures:
   ```bash
   # Check logs
   docker-compose logs airflow-scheduler
   # Verify files
   ls -l ./data/
   ```

3. Permission issues:
   ```bash
   # Fix permissions
   sudo chown -R 50000:50000 ./logs ./data
   ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License

## Contact

For support or questions, please open an issue in the repository.
