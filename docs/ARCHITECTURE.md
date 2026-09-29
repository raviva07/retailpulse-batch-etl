> Scope: consult [README](../README.md) and [REVIEW](REVIEW.md) for tested local behavior. Cloud/distributed mappings in these learning notes are illustrative and unvalidated.

# Architecture
## Layers
- **Source**: immutable sample sales CSV.
- **Bronze**: byte-for-byte raw landing copy.
- **Silver**: validated and normalized records with derived revenue/order_date.
- **Warehouse**: star schema (`fact_sales`, customer/product/date dimensions).
- **Gold**: business-facing daily/category/city aggregates.
- **Metadata**: source SHA-256 in `pipeline_runs` implements idempotent reprocessing.

## Production evolution
Replace local CSV with S3/ADLS/GCS, SQLite with PostgreSQL/Redshift/Snowflake, and the CLI scheduler with Airflow while preserving the same contracts and layer boundaries.
