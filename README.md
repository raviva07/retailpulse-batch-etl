# RetailPulse

**Batch ETL and a retail analytics warehouse** · Beginner

Turn retail sales CSVs into validated records, a SQLite star schema, and revenue reports.

## What runs in this repository

- CSV ingestion and raw landing copies
- Required-field and positive-value checks
- Pandas transformations and dimensional SQL modeling
- SHA-256 batch identity and repeat-run deduplication
- Daily, city, and category revenue marts

## Data flow

`data/input/sales.csv` → `data/bronze/` → `data/silver/` → `warehouse/retailpulse.db` → `data/gold/`

## Quick start

Use Python 3.12. From this repository's root:

```bash
python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python src/pipeline.py
python -m pytest -q
```

No API keys or cloud credentials are required for the local demo. Run the pipeline again to inspect its repeat-run behavior. Tests use temporary project copies and do not erase your working outputs.

## Expected first run

8 sales facts · 5 customers · 5 products · total revenue 12,100.

Generated databases, models, logs, and checkpoints are intentionally excluded from Git. Build them with the quick-start command; a fresh clone must not inherit an old checkpoint or pre-trained binary.

## Configuration and operation

`config.json` defines the input and output locations relative to the repository. Change it to use another CSV with the same schema.

## Repository guide

| Path | Purpose |
| --- | --- |
| `src/` | Runnable local implementation |
| `tests/` | Isolated functional and regression tests |
| `data/` | Example inputs; generated layers are ignored |
| `sql/` | Queries to inspect the warehouse or feature store |
| `docs/` | Architecture, setup, operations, and review notes |
| `.github/workflows/tests.yml` | Python test workflow on pushes and pull requests |

## Scope and trade-offs

Facts are append-only: an existing order ID is not corrected by a later file. Customer and product dimensions use Type 1 updates. Raw landing files are overwritten on each run; this is not an immutable archive. SQLite and Pandas are intended for local-sized datasets.

## Portfolio presentation

Demonstrate a clean run, inspect the SQL tables and output files, then rerun and explain the state handling. Show a failure/regression test and describe the trade-offs above. Describe this as a local portfolio implementation; do not claim distributed throughput, production SLAs, or cloud deployment from the reference files.

See [review and validation](docs/REVIEW.md) for the fixes and test scope. The local implementation and this README define the tested behavior; production mappings in older learning notes are future work.
