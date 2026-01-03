---
domain: actions
difficulty: intermediate
tags: actions, functions, ontology, mutations, logic
---
# Ontology Actions & Functions

## OVERVIEW
Actions and Functions are Palantir Foundry's mechanisms for embedding business logic into the Ontology. They enable complex operations beyond simple CRUD while maintaining type safety and audit trails.

**Actions**: Write operations that modify Ontology Objects (create, update, delete)
**Functions**: Read-only computations that return derived data

Key capabilities:
- **Type-Safe Mutations**: Validated object modifications
- **Business Rule Enforcement**: Pre/post-conditions and validation
- **Audit Logging**: Automatic tracking of all changes
- **Permission Control**: Fine-grained access control
- **External Integration**: API calls and webhook triggers

## PREREQUISITES
Before developing Actions/Functions:
1. **Ontology Design**: Object types defined and linked
2. **TypeScript/Python**: Intermediate coding skills
3. **Business Logic**: Clear understanding of rules to implement
4. **Testing Mindset**: Unit and integration testing approach

Recommended prior learning:
- Ontology Design Patterns (KB-03)
- OSDK TypeScript (KB-11)

## CORE_CONTENT

### Action Structure
```typescript
// TypeScript Action definition
import { Action, ActionContext } from "@palantir/foundry-actions";

@Action({
  name: "CreateEmployee",
  description: "Creates a new employee record",
})
export class CreateEmployeeAction {
  @Input() fullName: string;
  @Input() email: string;
  @Input() department: string;
  
  @Output() createdEmployee: Employee;
  
  async execute(ctx: ActionContext): Promise<void> {
    // Validation
    if (!this.email.includes("@company.com")) {
      throw new Error("Invalid email domain");
    }
    
    // Create object
    this.createdEmployee = await ctx.objects.Employee.create({
      fullName: this.fullName,
      email: this.email,
      department: this.department,
      startDate: new Date(),
    });
  }
}
```

### Function Structure
```typescript
// TypeScript Function definition
import { Function, FunctionContext } from "@palantir/foundry-functions";

@Function({
  name: "GetTeamStatistics",
  description: "Calculates statistics for a team",
})
export class GetTeamStatisticsFunction {
  @Input() departmentId: string;
  
  async execute(ctx: FunctionContext): Promise<TeamStats> {
    const employees = await ctx.objects.Employee
      .where({ department: this.departmentId })
      .fetchAll();
    
    return {
      totalEmployees: employees.length,
      avgTenure: calculateAvgTenure(employees),
      departments: groupByDepartment(employees),
    };
  }
}
```

### Action Types
| Type | Use Case | Example |
|------|----------|---------|
| Create | Add new objects | CreateEmployee, AddProduct |
| Update | Modify existing objects | UpdateAddress, ChangeStatus |
| Delete | Remove objects | DeactivateAccount, ArchiveRecord |
| Batch | Process multiple objects | BulkApprove, MassUpdate |
| Workflow | Multi-step processes | OnboardEmployee, CloseCase |

## EXAMPLES

### Approval Workflow Action
```typescript
@Action({ name: "ApproveExpense" })
export class ApproveExpenseAction {
  @Input() expenseId: string;
  @Input() approverNotes?: string;
  
  async execute(ctx: ActionContext): Promise<void> {
    const expense = await ctx.objects.Expense.get(this.expenseId);
    
    // Validate current state
    if (expense.status !== "PENDING") {
      throw new Error("Can only approve pending expenses");
    }
    
    // Business rule: Auto-reject if over budget
    if (expense.amount > expense.department.remainingBudget) {
      await expense.update({ status: "REJECTED", notes: "Exceeds budget" });
      return;
    }
    
    // Approve
    await expense.update({
      status: "APPROVED",
      approvedBy: ctx.user.id,
      approvedAt: new Date(),
      notes: this.approverNotes,
    });
    
    // Trigger downstream
    await ctx.actions.UpdateBudget.apply({
      departmentId: expense.departmentId,
      delta: -expense.amount,
    });
  }
}
```

## COMMON_PITFALLS

1. **Side Effects**: Avoid external API calls in Action execute(); use webhooks
2. **Transaction Scope**: Actions are atomic; partial failures rollback
3. **Circular References**: Actions calling Actions can cause infinite loops
4. **Performance**: Fetching too many objects in one Action causes timeouts
5. **Error Messages**: Expose user-friendly errors, not stack traces

## BEST_PRACTICES

1. **Single Responsibility**: Each Action does one thing well
2. **Validation First**: Validate inputs before any mutations
3. **Idempotency**: Design Actions to be safely re-runnable
4. **Logging**: Add context to errors for debugging
5. **Testing**: Write unit tests for business logic
6. **Permissions**: Set appropriate access controls

## REFERENCES
- [Actions Documentation](https://www.palantir.com/docs/foundry/actions/)
- [Functions Documentation](https://www.palantir.com/docs/foundry/functions/)
- [Ontology SDK Actions](https://www.palantir.com/docs/foundry/osdk/actions/)
