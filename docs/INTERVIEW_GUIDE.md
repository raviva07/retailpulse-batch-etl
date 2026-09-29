> Scope: consult [README](../README.md) and [REVIEW](REVIEW.md) for tested local behavior. Cloud/distributed mappings in these learning notes are illustrative and unvalidated.

# Interview Guide
1. **Why Bronze/Silver/Gold?** Raw replayability, trusted cleaned data, then business-ready aggregates.
2. **How is the pipeline idempotent?** It hashes the source and stores the hash in a metadata table; repeated identical inputs are skipped.
3. **Why a star schema?** It separates measurable facts from descriptive dimensions and simplifies analytical queries.
4. **What would change at scale?** Object storage, distributed compute, a production warehouse/lakehouse, orchestration, observability, and partitioning.
5. **How do you prevent bad records?** Explicit required-column, null, duplicate-key, and positive-value checks fail fast before loading.
