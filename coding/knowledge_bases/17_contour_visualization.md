---
domain: contour
difficulty: beginner
tags: contour, visualization, charts, dashboards, data
---
# Contour Data Visualization

## OVERVIEW
Contour is Palantir Foundry's primary data visualization application for creating interactive charts, dashboards, and reports. It provides a user-friendly interface for exploring datasets and building shareable visualizations.

Key capabilities:
- **Chart Library**: Bar, line, pie, scatter, heatmap, and more
- **Data Binding**: Direct connection to Foundry datasets
- **Interactivity**: Cross-filtering, drill-down, and tooltips
- **Sharing**: Publish and embed visualizations
- **Collaboration**: Comments and annotations

Contour is designed for data analysts and business users who need to quickly visualize and share insights.

## PREREQUISITES
Before using Contour:
1. **Dataset Access**: Read permission on source datasets
2. **Data Literacy**: Understanding of basic statistics and charts
3. **Foundry Navigation**: Ability to find and select datasets

Recommended prior learning:
- Foundry Platform Essentials (KB-01)
- Data modeling concepts

## CORE_CONTENT

### Chart Types
| Category | Charts |
|----------|--------|
| Comparison | Bar, Column, Grouped Bar, Stacked Bar |
| Trend | Line, Area, Stacked Area |
| Distribution | Histogram, Box Plot, Violin |
| Relationship | Scatter, Bubble |
| Composition | Pie, Donut, Treemap |
| Geographic | Map, Choropleth, Point Map |
| Part-to-Whole | Stacked Bar, Pie, Sunburst |

### Chart Configuration
```yaml
Chart: Monthly Sales Trend
Type: Line
Data Source: sales_summary
Columns:
  X-Axis: month
  Y-Axis: totalRevenue
  Color: region
Options:
  Show Legend: true
  Enable Tooltips: true
  Show Data Labels: false
Filters:
  - year = 2024
```

### Dashboard Layout
```
Dashboard: Sales Overview
├── Row 1: KPI Cards
│   ├── Total Revenue
│   ├── New Customers
│   └── Growth Rate
├── Row 2: Main Charts
│   ├── Revenue by Region (Bar)
│   └── Monthly Trend (Line)
└── Row 3: Details
    ├── Top Products (Table)
    └── Region Map (Choropleth)
```

### Cross-Filtering
Enable interactions between charts:
1. Click region on bar chart
2. All other charts filter to that region
3. Reset by clicking empty space

## EXAMPLES

### Sales Dashboard
```
Dataset: sales_transactions
Filters: date >= '2024-01-01'

Charts:
1. Revenue by Product Category (Bar)
   - X: productCategory
   - Y: SUM(amount)
   
2. Monthly Revenue Trend (Line)
   - X: month
   - Y: SUM(amount)
   - Color: region
   
3. Top 10 Customers (Horizontal Bar)
   - Sort: revenue DESC
   - Limit: 10
   
4. Geographic Sales (Map)
   - Location: customerState
   - Size: SUM(amount)
```

### Operational Metrics
```
Dataset: operations_metrics
Refresh: Daily

Charts:
1. Daily Active Users (Line with Goal)
   - Goal Line: 1000
   - Highlight: Below goal in red

2. Error Rate Gauge
   - Type: Gauge
   - Green: 0-1%
   - Yellow: 1-5%
   - Red: >5%

3. Top Errors (Table)
   - Columns: errorCode, count, lastOccurrence
   - Sort: count DESC
```

## COMMON_PITFALLS

1. **Data Volume**: Large datasets slow rendering; pre-aggregate data
2. **Overplotting**: Too many data points make scatter plots unreadable
3. **Color Overuse**: Too many colors confuse viewers
4. **Missing Context**: Always include titles, labels, and legends
5. **Stale Data**: Check dataset refresh schedules

## BEST_PRACTICES

1. **Choose Charts Wisely**: Match chart type to data relationship
2. **Limit Dimensions**: 2-3 dimensions per chart maximum
3. **Label Everything**: Titles, axis labels, legends
4. **Consistent Colors**: Use same colors for same categories across charts
5. **Mobile Friendly**: Test dashboards on smaller screens
6. **Performance**: Pre-filter data at source, not in Contour

## REFERENCES
- [Contour Documentation](https://www.palantir.com/docs/foundry/contour/)
- [Chart Type Guide](https://www.palantir.com/docs/foundry/contour/chart-types/)
- [Dashboard Best Practices](https://www.palantir.com/docs/foundry/contour/dashboards/)
