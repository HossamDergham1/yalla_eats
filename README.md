# yalla_eats
Yalla eats is a repo ti show case a food ordering business data analytics, etl, modeling,  A/B testing and visualization 


## Yalla Eats Analytics Platform:
An end-to-end containerized data platform built to ingest operational food-delivery data from MySQL into ClickHouse,
supporting high-throughput product reporting and statistical A/B test evaluation.

## Stack 
- MySQL (mysql): Operational OLTP source database containing core business entities (users, orders, order_items, products, restaurants) and experiment tracking tables (experiment_assignments, experiment_exposures).
- Data Generator (data-generator): Python service seeding MySQL with scalable synthetic datasets, injecting realistic data noise (casing/spaces in cities) and an embedded experiment treatment signal.
- ETL Engine (etl): Automated pipeline extracting raw tables into ClickHouse using ReplacingMergeTree engines for idempotent execution.
- ClickHouse (clickhouse): OLAP analytical engine structured into raw landing tables, staging data cleaning views, and a denormalized marts.fct_order_items One Big Table (OBT).

## Deployment
- Start the complete stack:
  Bash docker compose up --build -d

## A/B Test Summary (xsell_reco_v1) recommendation: 
- Ship Cross-Sell Conversion: Increased from 35.38% to 80.01% ).
- Average Revenue / User: Rose from 65 to 115 .
- Statistical Significance: Z = 18.5, p-value < 0.0001 .
