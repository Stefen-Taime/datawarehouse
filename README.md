# Data Warehouse E-commerce Project

## Overview

This project implements a complete data warehouse solution for e-commerce analytics using Apache Airflow, PostgreSQL, and Apache Superset. It includes automated data generation, ETL processes, and analytics dashboards.

## Architecture

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
git clone <repository-url>
cd ecommerce-dw
```

2. Create required directories:
```bash
mkdir -p ./dags ./logs ./scripts ./data
```

3. Start the services:
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

### Adding New Data Sources

1. Create data generator in `scripts/`
2. Add extraction logic in `dw_etl_dag.py`
3. Update schema in `dw_create_schema.py`
4. Add transformations in `dw_etl_dag.py`

### Creating New Reports

1. Add materialized view in `dw_reporting_dag.py`
2. Create corresponding Superset dashboard

## Monitoring

### Airflow UI

- DAG status
- Task execution
- Logs and history

### Database Monitoring

- Connection status
- Query performance
- Storage usage

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