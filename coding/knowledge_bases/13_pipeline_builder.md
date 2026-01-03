---
domain: pipeline_builder
difficulty: intermediate
tags: pipeline, etl, transforms, data, ingestion
---
# Pipeline Builder Mastery

## OVERVIEW
Pipeline Builder is Palantir Foundry's visual interface for creating data transformation pipelines. It enables data engineers to build complex ETL workflows without writing code, while still supporting custom Python/Java transforms when needed.

Key capabilities:
- **Visual Pipeline Design**: Drag-and-drop pipeline construction
- **Transform Library**: 100+ built-in transforms (filter, join, aggregate)
- **Schema Management**: Automatic schema inference and validation
- **Incremental Processing**: Built-in support for incremental builds
- **Code Generation**: Export pipelines to Python/Java for advanced customization

## PREREQUISITES
Before building pipelines:
1. **Data Access**: Read/write access to source and target datasets
2. **SQL Basics**: Understanding of SQL-like operations
3. **Data Modeling**: Knowledge of data schemas and types
4. **Foundry Navigation**: Familiarity with Foundry file system

Recommended prior learning:
- Foundry Platform Essentials (KB-01)
- Data Connection patterns

## CORE_CONTENT

### Pipeline Structure
```
Pipeline: CustomerDataPipeline
├── Sources (Input Datasets)
│   ├── raw_customers (CSV import)
│   └── transactions (API sync)
├── Transforms
│   ├── FilterInactive: Remove status='inactive'
│   ├── JoinTransactions: Left join on customer_id
│   ├── Aggregate: Group by region, sum revenue
│   └── DeriveColumns: Add calculated fields
└── Outputs (Target Datasets)
    └── customer_summary
```

### Common Transforms
| Transform | Description | Use Case |
|-----------|-------------|----------|
| Filter | Row-level filtering | Remove nulls, filter by date |
| Join | Combine datasets | Enrich with lookup data |
| Aggregate | Group and summarize | Calculate totals, averages |
| Derive | Create new columns | Add calculated fields |
| Union | Stack datasets | Combine similar sources |
| Sort | Order rows | Prepare for windowing |
| Window | Row-relative calculations | Running totals, ranks |

### Build Configuration
```yaml
# Pipeline build settings
incremental: true
partitionBy: [date, region]
scheduling:
  cron: "0 2 * * *"  # Daily at 2 AM
  dependencies:
    - upstream_dataset_1
    - upstream_dataset_2
```

## EXAMPLES

### Customer 360 Pipeline
```
Sources:
  - CRM Export (daily)
  - Transactions (streaming)
  - Support Tickets (hourly)

Steps:
1. Filter: Remove test accounts
2. Join: CRM ← Transactions (on customer_id)
3. Join: Result ← Tickets (on customer_id)
4. Aggregate: Group by customer, count tickets
5. Derive: Calculate customer_health_score
6. Output: customer_360_dataset
```

### Incremental Update Pattern
```
Configure:
  - Incremental column: updated_at
  - Partition key: date(updated_at)
  
Logic:
  - First run: Process all historical data
  - Subsequent runs: Only new/updated rows
  - Merge strategy: Replace partition
```

## COMMON_PITFALLS

1. **Schema Drift**: Source schema changes break pipelines; use schema pinning
2. **Cartesian Joins**: Missing join keys cause data explosion
3. **Memory Limits**: Large aggregations can OOM; use incremental processing
4. **Null Handling**: Nulls in join keys cause lost rows
5. **Type Mismatches**: String vs. Integer comparisons fail silently

## BEST_PRACTICES

1. **Naming Convention**: Use descriptive names (filter_inactive_customers, not filter_1)
2. **Modular Design**: Break complex pipelines into reusable sub-pipelines
3. **Documentation**: Add comments to each transform explaining business logic
4. **Testing**: Create test branches with sample data before production
5. **Monitoring**: Set up data quality checks and alerts

## REFERENCES
- [Pipeline Builder Documentation](https://www.palantir.com/docs/foundry/pipeline-builder/)
- [Transform Reference](https://www.palantir.com/docs/foundry/transforms/)
- [Incremental Processing Guide](https://www.palantir.com/docs/foundry/data-integration/incremental/)
