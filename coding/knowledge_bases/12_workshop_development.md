---
domain: workshop
difficulty: intermediate
tags: workshop, ui, no-code, applications, widgets
---
# Workshop Development

## OVERVIEW
Workshop is Palantir Foundry's no-code/low-code application builder for creating operational applications on top of the Ontology. It enables rapid development of data-driven user interfaces without writing frontend code.

Key capabilities:
- **Drag-and-Drop Builder**: Visual UI composition
- **Pre-built Widgets**: Tables, charts, maps, forms, and more
- **Ontology Integration**: Direct binding to Objects and Actions
- **Event System**: Inter-widget communication and state management
- **Customizable Styling**: Theme and layout customization

Workshop apps are ideal for operational users who need structured access to data without direct Ontology access.

## PREREQUISITES
Before building Workshop applications:
1. **Ontology Defined**: Objects and Actions available
2. **Data Access**: Appropriate permissions on backing datasets
3. **Workshop Access**: Workshop module enabled in your Foundry stack
4. **UI/UX Basics**: Understanding of user interface design principles

Recommended prior learning:
- Ontology Design Patterns (KB-03)
- Actions Development (KB-05)

## CORE_CONTENT

### Application Structure
```
Workshop Application
├── Pages
│   ├── HomePage
│   ├── DetailPage
│   └── SettingsPage
├── Variables (State)
│   ├── selectedEmployee (Object)
│   └── filterDateRange (Date Range)
├── Events
│   ├── onEmployeeSelect
│   └── onFilterChange
└── Widgets
    ├── EmployeeTable
    ├── DetailCard
    └── FilterPanel
```

### Widget Types
| Category | Widgets |
|----------|---------|
| Display | Text, Image, Card, HTML |
| Tables | Object Table, Pivot Table |
| Charts | Bar, Line, Pie, Scatter |
| Maps | Map, Heatmap |
| Input | Text Input, Dropdown, Date Picker |
| Actions | Button, Action Form |
| Layout | Container, Tabs, Grid |

### Variable Binding
Variables store application state and enable reactive updates:
```
Variable: selectedDepartment (String)
  ↓ Binds to
Dropdown Widget
  ↓ Filters
Object Table (where department = selectedDepartment)
  ↓ Updates
Chart Widget (group by role)
```

### Event System
Events enable cross-widget communication:
1. **Click Event**: User clicks on table row
2. **Event Handler**: Sets `selectedEmployee` variable
3. **Dependent Widgets**: Detail card updates to show selected employee

## EXAMPLES

### Employee Directory Application
```
Page: Employee Directory
├── Filter Panel (Left Sidebar)
│   ├── Department Dropdown → Sets $department
│   └── Search Input → Sets $searchTerm
├── Employee Table (Main)
│   ├── Bound to: Employee Objects
│   ├── Filters: department = $department AND name LIKE $searchTerm
│   └── On Row Click: Set $selectedEmployee
└── Employee Detail Card (Right Panel)
    └── Bound to: $selectedEmployee
```

### Action Form Pattern
```
Page: Promotion Form
├── Employee Selector
│   └── On Change: Set $employee
├── Action Form Widget
│   ├── Bound to: PromoteEmployee Action
│   ├── Pre-filled: employeeId = $employee.id
│   └── User Inputs: newTitle, newSalary
└── Submit Button
    └── On Success: Navigate to confirmation page
```

## COMMON_PITFALLS

1. **Variable Scoping**: Variables are page-scoped by default; use global variables for cross-page state
2. **Performance**: Binding many widgets to large object sets causes slowdowns
3. **Permissions**: Workshop inherits user permissions; test as different users
4. **Event Loops**: Avoid circular event chains that cause infinite updates
5. **Mobile Responsiveness**: Test layouts on different screen sizes

## BEST_PRACTICES

1. **Modular Pages**: Keep pages focused on single use cases
2. **Naming Conventions**: Use clear, consistent variable names
3. **Loading States**: Configure loading indicators for async operations
4. **Error Handling**: Set up action failure handlers
5. **User Feedback**: Provide confirmation messages for actions
6. **Version Control**: Use Foundry's built-in app versioning

## REFERENCES
- [Workshop Documentation](https://www.palantir.com/docs/foundry/workshop/)
- [Widget Reference](https://www.palantir.com/docs/foundry/workshop/widgets/)
- [Workshop Best Practices](https://www.palantir.com/docs/foundry/workshop/best-practices/)
- Workshop examples in your Foundry stack
