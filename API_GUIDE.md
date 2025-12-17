# API Integration Guide

Guide for adding and managing ERP APIs in the chatbot system.

## Overview

The chatbot uses a catalog-based system where you define APIs in a JSON file. The AI agent automatically selects and calls the appropriate APIs based on user queries.

## API Catalog Structure

Location: `backend/data/api_catalog.json`

```json
{
  "apis": [
    {
      "id": "unique_identifier",
      "name": "Human Readable Name",
      "description": "Detailed description",
      "endpoint": "/api-path",
      "method": "GET",
      "parameters": [...],
      "tags": [...],
      "examples": [...],
      "response_description": "..."
    }
  ]
}
```

## Field Descriptions

### Required Fields

**id** (string)
- Unique identifier for the API
- Use snake_case
- Example: `"supplier_payables_get"`

**name** (string)
- Human-readable name
- Used in UI and responses
- Example: `"Get Supplier Payables"`

**description** (string)
- Detailed description of what the API does
- Include use cases and data types
- Be specific - helps the AI select the right API
- Example: `"Retrieves supplier payables including invoices, payments, balances..."`

**endpoint** (string)
- API endpoint path (without base URL)
- Can include path parameters with `{param_name}` syntax
- Examples: 
  - `"/supplierpayables-get"`
  - `"/projects/{projectId}/tasks"`

**method** (string)
- HTTP method
- Values: `"GET"`, `"POST"`, `"PUT"`, `"DELETE"`, `"PATCH"`

**parameters** (array)
- Array of parameter objects
- Can be empty array if no parameters

**tags** (array of strings)
- Keywords for categorization
- Helps AI understand context
- Examples: `["finance", "supplier", "payments"]`

**examples** (array of strings)
- Example user queries that should trigger this API
- Helps train the AI
- Be diverse and natural
- Examples: 
  - `"Show me all supplier payments"`
  - `"What do we owe to contractors?"`

**response_description** (string)
- Describe the response data structure
- Include key fields and their meanings
- Example: `"Returns array with fields: paid, balance, invoice_id, supplier name..."`

### Parameter Object Structure

```json
{
  "name": "parameter_name",
  "type": "query|path|form|body",
  "description": "What this parameter does",
  "required": true,
  "default": null,
  "example": "example_value"
}
```

**Parameter Types:**
- `query` - URL query parameter (`?param=value`)
- `path` - Path parameter (`/users/{userId}`)
- `form` - Form data (application/x-www-form-urlencoded)
- `body` - JSON body parameter

## Examples

### Example 1: Simple GET API

```json
{
  "id": "get_projects",
  "name": "Get Projects List",
  "description": "Retrieves all projects with basic information including project name, status, and dates. Use this for general project queries and listings.",
  "endpoint": "/projects",
  "method": "GET",
  "parameters": [
    {
      "name": "company_id",
      "type": "query",
      "description": "Company ID to filter projects",
      "required": true,
      "example": "88"
    },
    {
      "name": "status",
      "type": "query",
      "description": "Filter by project status (active, completed, pending)",
      "required": false,
      "example": "active"
    }
  ],
  "tags": ["projects", "listing", "overview"],
  "examples": [
    "Show me all projects",
    "List active projects",
    "What projects do we have?"
  ],
  "response_description": "Returns array of projects with id, name, status, start_date, end_date, budget"
}
```

### Example 2: GET with Path Parameter

```json
{
  "id": "get_project_details",
  "name": "Get Project Details",
  "description": "Retrieves detailed information about a specific project including team members, budget breakdown, timeline, and milestones.",
  "endpoint": "/projects/{projectId}",
  "method": "GET",
  "parameters": [
    {
      "name": "projectId",
      "type": "path",
      "description": "The unique project identifier",
      "required": true,
      "example": "165"
    },
    {
      "name": "company_id",
      "type": "query",
      "description": "Company ID",
      "required": true,
      "example": "88"
    }
  ],
  "tags": ["projects", "details", "budget", "timeline"],
  "examples": [
    "Show me details for project 165",
    "What's the budget for project 165?",
    "Who's working on project 165?"
  ],
  "response_description": "Returns detailed project object with team, budget, timeline, milestones, and status"
}
```

### Example 3: POST API with Form Data

```json
{
  "id": "create_invoice",
  "name": "Create Invoice",
  "description": "Creates a new invoice for a supplier with specified amount, items, and due date.",
  "endpoint": "/invoices/create",
  "method": "POST",
  "parameters": [
    {
      "name": "supplier_id",
      "type": "form",
      "description": "Supplier ID",
      "required": true,
      "example": "123"
    },
    {
      "name": "amount",
      "type": "form",
      "description": "Invoice amount",
      "required": true,
      "example": "50000"
    },
    {
      "name": "due_date",
      "type": "form",
      "description": "Due date in DD/MM/YYYY format",
      "required": true,
      "example": "31/12/2024"
    },
    {
      "name": "company_id",
      "type": "form",
      "description": "Company ID",
      "required": true,
      "example": "88"
    }
  ],
  "tags": ["invoice", "create", "supplier", "finance"],
  "examples": [
    "Create an invoice for supplier 123",
    "Add new invoice for $50000"
  ],
  "response_description": "Returns created invoice object with invoice_id and confirmation"
}
```

### Example 4: POST with JSON Body

```json
{
  "id": "update_project_status",
  "name": "Update Project Status",
  "description": "Updates the status and details of a project",
  "endpoint": "/projects/{projectId}/update",
  "method": "POST",
  "parameters": [
    {
      "name": "projectId",
      "type": "path",
      "description": "Project ID to update",
      "required": true,
      "example": "165"
    },
    {
      "name": "status",
      "type": "body",
      "description": "New project status",
      "required": true,
      "example": "completed"
    },
    {
      "name": "completion_notes",
      "type": "body",
      "description": "Notes about the update",
      "required": false,
      "example": "Project completed successfully"
    }
  ],
  "tags": ["projects", "update", "status"],
  "examples": [
    "Mark project 165 as completed",
    "Update project status to completed"
  ],
  "response_description": "Returns updated project object with new status"
}
```

## Best Practices

### 1. Write Clear Descriptions

**Good:**
```json
"description": "Retrieves all supplier invoices with payment status, amounts, due dates, and supplier details. Useful for tracking payables, checking payment history, and identifying overdue invoices."
```

**Bad:**
```json
"description": "Gets invoices"
```

### 2. Include Comprehensive Tags

**Good:**
```json
"tags": ["finance", "supplier", "invoice", "payment", "accounts payable", "contractor"]
```

**Bad:**
```json
"tags": ["invoice"]
```

### 3. Provide Natural Example Queries

**Good:**
```json
"examples": [
  "Show me all outstanding invoices",
  "Which suppliers haven't been paid?",
  "What's our total payable amount?",
  "List overdue payments"
]
```

**Bad:**
```json
"examples": [
  "get invoices"
]
```

### 4. Describe Response Data

**Good:**
```json
"response_description": "Returns array of invoice objects containing: invoice_id, invoice_no, supplier (name), amount (total), paid (amount paid), balance (outstanding), due_date (DD/MM/YYYY), gst_amount, grossAmount. Also includes totalPayable and totalPaid summary fields."
```

**Bad:**
```json
"response_description": "Invoice data"
```

### 5. Use Appropriate Parameter Types

- **Query params** for filters: `?status=active&type=contractor`
- **Path params** for IDs: `/projects/{projectId}`
- **Form data** for traditional forms: Login, simple updates
- **Body params** for complex JSON: Nested objects, arrays

## Testing New APIs

### 1. Add to Catalog

Edit `backend/data/api_catalog.json` and add your API definition.

### 2. Restart Backend

```bash
# Ctrl+C to stop
python main.py
```

### 3. Verify API Loaded

```bash
curl http://localhost:8000/api/apis | jq
```

Should show your new API in the list.

### 4. Test with Chat

Try queries from your `examples` array in the frontend.

### 5. Check Logs

Watch backend terminal for:
- API selection
- Parameter extraction
- API call results
- Any errors

## Common Issues

### Issue: API Not Being Selected

**Causes:**
- Description is too vague
- Tags don't match query context
- Examples don't cover query pattern

**Solution:**
- Enhance description with more keywords
- Add more relevant tags
- Add example queries similar to test query

### Issue: Wrong Parameters Extracted

**Causes:**
- Parameter descriptions unclear
- No example values
- Complex parameter relationships

**Solution:**
- Clarify parameter descriptions
- Add clear examples
- Simplify parameter structure if possible

### Issue: API Call Fails

**Causes:**
- Wrong parameter type
- Missing required parameters
- Authentication issues

**Solution:**
- Verify parameter types match API expectations
- Check all required parameters are defined
- Test API call manually with curl first

## Advanced: Dynamic Parameter Inference

The AI can infer parameters from context:

**Query:** "Show invoices for project 165"

The AI will extract:
- `projectId: "165"` from the query
- Use defaults for other parameters

**To improve inference:**
1. Provide clear parameter descriptions
2. Include parameter examples
3. Use consistent naming (match user's language)

## Adding 70+ APIs

When adding many APIs:

### 1. Group by Category

```json
{
  "apis": [
    // Finance APIs
    {...},
    {...},
    
    // Project Management APIs
    {...},
    {...},
    
    // Inventory APIs
    {...},
    {...}
  ]
}
```

### 2. Use Consistent Naming

- IDs: `category_action` (e.g., `supplier_payments_get`)
- Names: `Action Category` (e.g., `Get Supplier Payments`)

### 3. Share Common Tags

Use category tags consistently:
- Finance: `["finance", "accounting", "money"]`
- Projects: `["project", "task", "management"]`
- Inventory: `["inventory", "stock", "materials"]`

### 4. Document in Batches

Test 5-10 APIs at a time before adding more.

## API Catalog Validation

Before deploying, validate your catalog:

```bash
python -c "
import json
from pathlib import Path
from models.api_catalog import APICatalog

catalog_path = Path('data/api_catalog.json')
with open(catalog_path) as f:
    data = json.load(f)
    catalog = APICatalog(**data)
    print(f'✓ Catalog valid: {len(catalog.apis)} APIs loaded')
"
```

## Future Enhancements

Planned features:
- API versioning support
- Rate limiting configuration
- Response caching
- API health monitoring
- Auto-generate API catalog from OpenAPI specs

## Support

If you need help:
1. Check this guide
2. Review example APIs in the catalog
3. Test API manually with curl
4. Check backend logs for errors


