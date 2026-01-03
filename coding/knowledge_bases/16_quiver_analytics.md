---
domain: quiver
difficulty: intermediate
tags: quiver, analytics, objects, aggregations, exploration
---
# Quiver Analytics

## OVERVIEW
Quiver is Palantir Foundry's self-service analytics tool for exploring Ontology Objects. It provides a spreadsheet-like interface for business users to analyze, aggregate, and visualize data without technical expertise.

Key capabilities:
- **Object Exploration**: Browse and filter Ontology Objects
- **Aggregations**: Group, count, sum, and compute metrics
- **Data Export**: Export results to CSV or datasets
- **Saved Analyses**: Save and share exploration configurations
- **Object Actions**: Execute Actions directly from results

Quiver bridges the gap between raw data and business insights, enabling non-technical users to answer ad-hoc questions.

## PREREQUISITES
Before using Quiver:
1. **Ontology Access**: Permission to view Object Types
2. **Business Context**: Understanding of data semantics
3. **Basic Analytics**: Familiarity with filtering and grouping concepts

Recommended prior learning:
- Foundry Platform Essentials (KB-01)
- Ontology Design Patterns (KB-03)

## CORE_CONTENT

### Quiver Interface
```
Quiver Analysis
├── Object Type Selector
│   └── Select: Employee, Transaction, etc.
├── Filters Panel
│   ├── department = "Engineering"
│   └── startDate >= 2024-01-01
├── Results Table
│   ├── Columns: name, email, department
│   ├── Sorting: By startDate (desc)
│   └── Pagination: 100 per page
└── Aggregations
    ├── Group by: department
    └── Metrics: COUNT, AVG(salary)
```

### Filter Types
| Filter | Description | Example |
|--------|-------------|---------|
| Equals | Exact match | status = "ACTIVE" |
| Contains | Substring search | name contains "John" |
| Range | Between values | salary BETWEEN 50000 AND 100000 |
| In | Multiple values | department IN ("Eng", "Sales") |
| Is Null | Missing values | manager IS NULL |
| Relative Date | Dynamic dates | created >= "7 days ago" |

### Aggregation Operations
| Operation | Description |
|-----------|-------------|
| COUNT | Number of objects |
| SUM | Total of numeric field |
| AVG | Average value |
| MIN/MAX | Extreme values |
| DISTINCT | Unique values |
| GROUP BY | Segment by field(s) |

### Saved Analysis
```json
{
  "name": "Engineering Headcount by Level",
  "objectType": "Employee",
  "filters": [
    { "field": "department", "op": "=", "value": "Engineering" },
    { "field": "isActive", "op": "=", "value": true }
  ],
  "groupBy": ["level"],
  "aggregations": [
    { "metric": "COUNT", "as": "headcount" },
    { "metric": "AVG", "field": "yearsExperience", "as": "avgExperience" }
  ]
}
```

## EXAMPLES

### Sales Analysis
```
1. Select: Transaction object type
2. Filter: date >= "2024-01-01" AND status = "COMPLETED"
3. Group by: productCategory
4. Aggregate: SUM(amount) as totalSales, COUNT as transactions
5. Sort: totalSales DESC
6. Save as: "Q1 2024 Sales by Category"
```

### Employee Directory Search
```
1. Select: Employee object type
2. Filter: name contains "Smith"
3. Columns: name, email, department, manager
4. Export: CSV for HR team
```

## COMMON_PITFALLS

1. **Large Result Sets**: Avoid loading 100K+ objects at once
2. **Missing Permissions**: Some fields may be hidden due to access
3. **Stale Data**: Quiver shows data as of last sync
4. **Complex Joins**: Quiver supports single Object Type; use Workshop for joins
5. **Date Ranges**: Always specify bounded date filters

## BEST_PRACTICES

1. **Start Narrow**: Begin with restrictive filters, then expand
2. **Save Frequently**: Save analyses to avoid losing work
3. **Name Clearly**: Use descriptive names for saved analyses
4. **Share Wisely**: Consider who should have access to saved views
5. **Export Snapshots**: Export to dataset for stable reporting

## REFERENCES
- [Quiver Documentation](https://www.palantir.com/docs/foundry/quiver/)
- [Quiver Aggregations Guide](https://www.palantir.com/docs/foundry/quiver/aggregations/)
- [Object Explorer](https://www.palantir.com/docs/foundry/object-explorer/)
