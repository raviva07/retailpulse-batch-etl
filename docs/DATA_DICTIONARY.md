> Scope: consult [README](../README.md) and [REVIEW](REVIEW.md) for tested local behavior. Cloud/distributed mappings in these learning notes are illustrative and unvalidated.

# Data Dictionary
- `order_id`: business transaction identifier; unique.
- `order_ts`: event timestamp.
- `customer_id`: stable customer business key.
- `product_id`: stable product business key.
- `quantity`: positive integer.
- `unit_price`: positive numeric unit price.
- `revenue`: derived `quantity * unit_price`.
- `date_key`: `YYYYMMDD` surrogate-style calendar key used by fact table.
