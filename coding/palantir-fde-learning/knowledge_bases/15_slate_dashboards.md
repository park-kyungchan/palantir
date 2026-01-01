---
domain: slate
difficulty: advanced
tags: slate, dashboards, visualization, custom, code
---
# Slate Dashboard Development

## OVERVIEW
Slate is Palantir Foundry's code-first dashboard development platform. Unlike Workshop's no-code approach, Slate provides full React/HTML/CSS access for building highly customized analytical applications.

Key capabilities:
- **Full Code Access**: React components with custom styling
- **Data Binding**: Direct connection to Foundry datasets
- **Rich Visualizations**: D3, Plotly, and custom chart libraries
- **Interactive Filters**: Cross-filtering and drill-down
- **Embedded Analytics**: Embeddable in external applications

Slate is ideal for data scientists and developers who need complete control over visualization and interaction design.

## PREREQUISITES
Before building Slate dashboards:
1. **React Proficiency**: Intermediate+ React/TypeScript skills
2. **Data Visualization**: D3.js or similar library experience
3. **CSS/Styling**: Advanced CSS and responsive design
4. **Foundry Data Access**: Permission to query datasets

Recommended prior learning:
- Workshop Development (KB-12)
- React Ecosystem (KB-02)

## CORE_CONTENT

### Slate Architecture
```
Slate Application
├── Widgets (React Components)
│   ├── Header.tsx
│   ├── FilterPanel.tsx
│   └── MainChart.tsx
├── Data Sources
│   ├── salesData (Dataset query)
│   └── regionMapping (Static JSON)
├── Variables (State)
│   ├── selectedRegion: string
│   └── dateRange: [Date, Date]
└── Layouts
    └── MainLayout.json
```

### Widget Development
```typescript
// CustomChart.tsx - Slate Widget
import React from "react";
import { useDataSource } from "@foundry/slate";
import { BarChart, Bar, XAxis, YAxis, Tooltip } from "recharts";

interface Props {
  region: string;
}

export const SalesChart: React.FC<Props> = ({ region }) => {
  const { data, loading } = useDataSource("salesData", {
    filters: { region },
  });
  
  if (loading) return <Spinner />;
  
  return (
    <BarChart width={600} height={300} data={data}>
      <XAxis dataKey="month" />
      <YAxis />
      <Tooltip />
      <Bar dataKey="revenue" fill="#8884d8" />
    </BarChart>
  );
};
```

### Data Source Configuration
```json
{
  "name": "salesData",
  "type": "dataset",
  "rid": "ri.foundry.main.dataset.xxx",
  "query": {
    "columns": ["month", "region", "revenue"],
    "filters": [
      { "column": "year", "operator": "=", "value": 2024 }
    ],
    "aggregations": [
      { "column": "revenue", "function": "sum" }
    ],
    "groupBy": ["month", "region"]
  }
}
```

### Variable Binding
```typescript
// Using Slate variables
import { useVariable, setVariable } from "@foundry/slate";

export const RegionFilter: React.FC = () => {
  const [region, setRegion] = useVariable<string>("selectedRegion");
  
  return (
    <Select value={region} onChange={setRegion}>
      <Option value="NA">North America</Option>
      <Option value="EU">Europe</Option>
      <Option value="APAC">Asia Pacific</Option>
    </Select>
  );
};
```

## EXAMPLES

### Executive Dashboard
```typescript
// Dashboard Layout
const ExecutiveDashboard = () => {
  return (
    <DashboardContainer>
      <Header title="Sales Performance" />
      <Row>
        <KPICard metric="totalRevenue" label="Total Revenue" />
        <KPICard metric="newCustomers" label="New Customers" />
        <KPICard metric="churnRate" label="Churn Rate" />
      </Row>
      <Row>
        <Col span={16}>
          <SalesChart region={selectedRegion} />
        </Col>
        <Col span={8}>
          <RegionList onSelect={setSelectedRegion} />
        </Col>
      </Row>
    </DashboardContainer>
  );
};
```

## COMMON_PITFALLS

1. **Bundle Size**: Large libraries (D3) increase load time
2. **Re-renders**: Inefficient state management causes flickering
3. **Data Fetching**: Fetching on every filter change is slow
4. **Responsiveness**: Fixed layouts break on different screens
5. **Browser Support**: Advanced CSS may not work in older browsers

## BEST_PRACTICES

1. **Memoization**: Use `useMemo` and `useCallback` for expensive operations
2. **Code Splitting**: Lazy-load heavy visualization components
3. **Caching**: Cache data queries with appropriate TTLs
4. **Accessibility**: Include ARIA labels and keyboard navigation
5. **Testing**: Snapshot tests for visual regressions

## REFERENCES
- [Slate Documentation](https://www.palantir.com/docs/foundry/slate/)
- [Slate Widget Gallery](https://www.palantir.com/docs/foundry/slate/widgets/)
- [Recharts Documentation](https://recharts.org/)
- [D3.js Documentation](https://d3js.org/)
