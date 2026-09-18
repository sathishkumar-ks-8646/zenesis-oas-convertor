# Zoho Analytics V2 REST API — Aggregate Formulas (Unified Metrics)

This document covers the APIs for creating, editing, deleting, listing, and evaluating **aggregate formulas** — also known as **Unified Metrics** — which are workspace-level, business-metric-style formulas built using aggregate functions (e.g., `sum()`, `max()`, `count_distinct()`) over one or more tables.

## What is an Aggregate Formula?

Unlike a [custom formula column](FORMULA_COLUMNS_API_DOC_INFO.md) (which computes a value per row), an **aggregate formula** produces a single summarized value (e.g., total sales, average order value) by applying an aggregate function across rows of a table. Aggregate formulas:

- Are defined at the level of a specific table/view (the "owning" view), but can reference columns from related tables connected via lookups.
- Can be reused across multiple reports, charts, and dashboards within the workspace as a single source of truth for a business metric — hence the term **Unified Metrics**.
- Support **synonyms** (alternate names) and a **priority** ranking, both of which are used by Zoho Analytics' natural-language search/insight features to better match user queries to the right metric.

> **Expression visibility depends on permission:** For users without edit permission on the aggregate formula (e.g., users with only view/share access), the `expression` field in list responses is returned as an **empty string** — the underlying formula logic is not exposed to non-editors, though the computed name, description, and metadata still are.

---

## Index

| # | API Name | Method | URL |
|---|----------|--------|-----|
| 1 | [Get Aggregate Formula](#1-get-aggregate-formula) | GET | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/aggregateformulas` |
| 2 | [Add Aggregate Formula](#2-add-aggregate-formula) | POST | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/aggregateformulas` |
| 3 | [Edit Aggregate Formula](#3-edit-aggregate-formula) | PUT | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/aggregateformulas/<formula-id>` |
| 4 | [Delete Aggregate Formula](#4-delete-aggregate-formula) | DELETE | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/aggregateformulas/<formula-id>` |
| 5 | [Get Unified Metrics in Workspace](#5-get-unified-metrics-in-workspace) | GET | `/restapi/v2/workspaces/<workspace-id>/aggregateformulas` |
| 6 | [Get Aggregate Formula Dependents](#6-get-aggregate-formula-dependents) | GET | `/restapi/v2/workspaces/<workspace-id>/aggregateformulas/<formula-id>/dependents` |
| 7 | [Get Aggregate Formula Value](#7-get-aggregate-formula-value) | GET | `/restapi/v2/workspaces/<workspace-id>/aggregateformulas/<formula-id>/value` |

> **Note on naming:** Get Aggregate Formula, Add Aggregate Formula, Edit Aggregate Formula, and Delete Aggregate Formula are scoped to a specific view (`/views/<view-id>/aggregateformulas`) and are used to manage aggregate formulas owned by that view. Get Unified Metrics in Workspace, Get Aggregate Formula Dependents, and Get Aggregate Formula Value are scoped to the entire workspace (`/aggregateformulas`, without a `<view-id>`) and are used to browse, audit, and evaluate any aggregate formula in the workspace regardless of which view owns it.

---

## 1. Get Aggregate Formula

Returns the list of aggregate formulas defined on the specified view.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/aggregateformulas` |
| **OAuth Scope** | `ZohoAnalytics.metadata.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace, or any user with Create Formula permission on the view. |
| **Rate Limit** | 30 requests per user per minute (10-minute lockout on breach). |

> This API has no CONFIG parameter.

### Sample Requests

**Case 1 — Get all aggregate formulas on a view**

```http
GET /restapi/v2/workspaces/137687000271334001/views/137687000271334499/aggregateformulas HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — White label portal user fetching aggregate formulas**

```http
GET /restapi/v2/workspaces/137687000271334001/views/137687000271334499/aggregateformulas HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.cccccc.dddddd
ZANALYTICS-ORGID: 700000123456
```

### Sample Responses

**HTTP 200 OK — User with edit permission (expression visible)**

```json
{
  "status": "success",
  "summary": "Get aggregate formulas",
  "data": {
    "aggregateFormulas": [
      {
        "formulaId": "137687000271334553",
        "formulaName": "Ag_1",
        "expression": "sum(\"Table_1\".\"Sales\")",
        "description": "",
        "subtypeId": 6,
        "subtypeName": "DECIMAL_NUMBER"
      },
      {
        "formulaId": "137687000271334555",
        "formulaName": "Ag_2",
        "expression": "count_distinct(\"Table_1\".\"Region\")",
        "description": "",
        "subtypeId": 4,
        "subtypeName": "NUMBER"
      }
    ]
  }
}
```

**HTTP 200 OK — View with no aggregate formulas**

```json
{
  "status": "success",
  "summary": "Get aggregate formulas",
  "data": {
    "aggregateFormulas": []
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `aggregateFormulas` | Array | List of aggregate formulas owned by this view. Empty array if none exist. |
| `aggregateFormulas[].formulaId` | String | Unique ID of the aggregate formula. Use as `<formula-id>` for Edit/Delete Aggregate Formula (view-scoped) and for the workspace-scoped Get Dependents / Get Value APIs. |
| `aggregateFormulas[].formulaName` | String | Display name of the aggregate formula. |
| `aggregateFormulas[].expression` | String | The aggregate expression (e.g., `sum("Table_1"."Sales")`). Empty string if the calling user lacks edit permission on the formula. |
| `aggregateFormulas[].description` | String | Description of the formula. Empty string if not set. |
| `aggregateFormulas[].subtypeId` | Integer | Internal numeric code for the result data type of the formula. See [Subtype Values](#subtype-values) below. |
| `aggregateFormulas[].subtypeName` | String | Display-form internal code for the result data type (e.g., `"NUMBER"`, `"DECIMAL_NUMBER"`). Matches the `dataType` values used in [Add Column](COLUMNS_API_DOC_INFO.md#1-add-column). |

#### Subtype Values

| `subtypeId` | `subtypeName` | Typical Cause |
|-------------|----------------|----------------|
| `4` | `NUMBER` | Integer-producing aggregates, e.g. `count()`, `count_distinct()`, `count_if()`, or boolean-style conditional expressions. |
| `6` | `DECIMAL_NUMBER` | Decimal-producing aggregates, e.g. `sum()`, `mean()`, `max()`, `min()` on decimal/currency source columns. |

> The exact `subtypeId`/`subtypeName` produced depends on the aggregate function used and the data type of the referenced column(s) — it is inferred automatically and cannot be explicitly set.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Expression visibility is permission-gated** | Users with only view/share access (no edit permission) will see `expression: ""` even though `formulaId`, `formulaName`, and other metadata are still returned. |
| **View-scoped, not workspace-wide** | This API only lists formulas owned by `<view-id>`. To see all aggregate formulas across the entire workspace (including those owned by other views), use [Get Unified Metrics in Workspace](#5-get-unified-metrics-in-workspace). |
| **Dependency** | `<view-id>` → Get View List. `formulaId` values feed into Edit/Delete Aggregate Formula, as well as the workspace-scoped Get Aggregate Formula Dependents and Get Aggregate Formula Value APIs. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7301 | User does not have permission. | Ensure the user is a Workspace Admin or has Create Formula permission on the view. |
| 7319 | The view does not belong to the specified workspace. | Confirm `<view-id>` belongs to `<workspace-id>`. |

---

## 2. Add Aggregate Formula

Creates a new aggregate formula owned by the specified view.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/aggregateformulas` |
| **OAuth Scope** | `ZohoAnalytics.modeling.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace, or any user with Create Formula permission on the view. |
| **Rate Limit** | 20 requests per user per minute (10-minute lockout on breach). |

### CONFIG Parameters

| Parameter | Type | Mandatory | Max Length | Default | Description |
|-----------|------|-----------|------------|---------|-------------|
| `formulaName` | String | **Yes** | 100 chars | — | Display name for the new aggregate formula. Must be unique within the workspace. |
| `expression` | String | **Yes** | 50,000 chars | — | The aggregate formula expression, using an aggregate function (e.g., `sum()`, `max()`, `min()`, `mean()`, `count()`, `count_distinct()`, `count_if()`) applied to one or more columns, referenced as `"TableName"."ColumnName"`. |
| `description` | String | No | 250 chars | `""` | Description of the aggregate formula. |
| `synonyms` | JSONArray of String | No | — | `[]` | Alternate names/keywords for this metric, used by natural-language search and insight suggestion features to match user queries to this formula. |
| `columnPriority` | Integer (enum) | No | — | `0` (Low) | Ranking priority of this formula when multiple metrics could match a natural-language query. See [Column Priority Values](#column-priority-values) below. |

#### Column Priority Values

| `columnPriority` Value | Priority Level |
|---------------------------|-----------------|
| `0` (default) | Low |
| `1` | Medium |
| `2` | High |

### Sample Requests

**Case 1 — Simple sum aggregate**

```http
POST /restapi/v2/workspaces/137687000271334001/views/137687000271334499/aggregateformulas HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"formulaName":"Total Sales","expression":"sum(\"Table_1\".\"Sales\")"}
```

**Case 2 — Aggregate with synonyms and high priority for NLP search**

```http
POST /restapi/v2/workspaces/137687000271334001/views/137687000271334499/aggregateformulas HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"formulaName":"Average Order Value","expression":"mean(\"Table_1\".\"Order Amount\")","description":"Average value of a single order","synonyms":["AOV","avg order value","mean order amount"],"columnPriority":2}
```

**Case 3 — White label portal user adding a count_distinct aggregate**

```http
POST /restapi/v2/workspaces/137687000271334001/views/137687000271334499/aggregateformulas HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.cccccc.dddddd
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"formulaName":"Unique Regions","expression":"count_distinct(\"Table_1\".\"Region\")"}
```

### Sample Responses

**HTTP 200 OK**

```json
{
  "status": "success",
  "summary": "Aggregate formula has been added successfully.",
  "data": {
    "formulaId": "137687000271334553",
    "formulaName": "Total Sales"
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `formulaId` | String | Unique ID assigned to the newly created aggregate formula. Use as `<formula-id>` for subsequent Edit/Delete calls, and for the workspace-scoped Get Dependents / Get Value APIs. |
| `formulaName` | String | The display name of the aggregate formula, echoing the `formulaName` value from the request. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Expression is validated at creation time** | Aggregate function names and referenced column names are checked before the formula is created. |
| **`formulaName` must be unique** | Duplicate aggregate formula names within the same workspace are rejected. |
| **Result data type (`subtypeId`) is inferred, not declared** | There is no data-type parameter; the type is derived from the aggregate function and the source column(s). |
| **`synonyms` and `columnPriority` are NLP/insights metadata only** | These fields do not affect the computed value of the formula — they only influence how the formula surfaces in natural-language search and auto-generated insights. |
| **Cross-table aggregates require a lookup relationship** | If the expression references columns from a table other than the owning view's table, that table must already be linked via a [lookup relationship](LOOKUPS_AND_RELATIONSHIPS_API_DOC_INFO.md). |
| **Dependency** | `<view-id>` → Get View List. Column/table names used in `expression` → Get Table Metadata. After creation, the returned `formulaId` can be queried via [Get Aggregate Formula Value](#7-get-aggregate-formula-value). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7112 | The formula expression could not be parsed (syntax error). | Review the expression for correct aggregate function syntax and column quoting. |
| 7113 | The expression references an unknown/unsupported function. | Verify the aggregate function name (e.g., `sum`, `mean`, `max`, `min`, `count`, `count_distinct`, `count_if`). |
| 7115 / 7116 | The expression references a column that does not exist, or the formula is otherwise invalid. | Verify all table/column names referenced in the expression. |
| 7160 | Formula columns/aggregate formulas are not allowed for this user/view combination. | Ensure the user is a Workspace Admin or has Create Formula permission on the view. |
| 7301 | User does not have permission. | Ensure the user is a Workspace Admin or has Create Formula permission on the view. |
| 7319 | The view does not belong to the specified workspace. | Confirm `<view-id>` belongs to `<workspace-id>`. |
| 8079 | A required attribute (`expression` or `formulaName`) is missing from CONFIG. | Ensure both `formulaName` and `expression` are provided. |

---

## 3. Edit Aggregate Formula

Updates an existing aggregate formula. Unlike [Edit Custom Formula](FORMULA_COLUMNS_API_DOC_INFO.md#3-edit-custom-formula), this API **does support renaming** the formula.

| Attribute | Value |
|-----------|-------|
| **Method** | PUT |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/aggregateformulas/<formula-id>` |
| **OAuth Scope** | `ZohoAnalytics.modeling.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace, or any user with Create Formula permission on the view. |
| **Rate Limit** | 20 requests per user per minute (10-minute lockout on breach). |

### CONFIG Parameters

| Parameter | Type | Mandatory | Max Length | Description |
|-----------|------|-----------|------------|-------------|
| `formulaName` | String | No\* | 100 chars | New display name for the aggregate formula. |
| `expression` | String | No\* | 50,000 chars | New aggregate expression. Fully replaces the existing expression. |
| `description` | String | No | 250 chars | New description. |
| `synonyms` | JSONArray of String | No | — | New list of synonyms. Fully replaces the existing list. |
| `columnPriority` | Integer (enum) | No | — | New priority ranking (`0`=Low, `1`=Medium, `2`=High). |

> \* **At least one of `expression` or `formulaName` must be provided.** Submitting neither returns error 8079.

> **Rename-only mode:** If you supply `formulaName` **without** `expression`, the API automatically fetches the formula's current expression internally and reapplies it unchanged — effectively performing a pure rename without requiring you to resend the expression text. This is the opposite behaviour from Edit Custom Formula, which has no `formulaName` field at all.

### Sample Requests

**Case 1 — Rename only (no expression change)**

```http
PUT /restapi/v2/workspaces/137687000271334001/views/137687000271334499/aggregateformulas/137687000271334553 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"formulaName":"Total Revenue"}
```

**Case 2 — Update the expression only**

```http
PUT /restapi/v2/workspaces/137687000271334001/views/137687000271334499/aggregateformulas/137687000271334553 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"expression":"sum(\"Table_1\".\"Sales\") - sum(\"Table_1\".\"Returns\")"}
```

**Case 3 — Update expression, description, synonyms, and priority together**

```http
PUT /restapi/v2/workspaces/137687000271334001/views/137687000271334499/aggregateformulas/137687000271334553 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"expression":"sum(\"Table_1\".\"Net Sales\")","description":"Total net sales after returns and discounts","synonyms":["net revenue","net sales total"],"columnPriority":2}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Edit Aggregate Formula returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |
| **Supports pure rename** | Unlike Edit Custom Formula, providing only `formulaName` (no `expression`) is valid — the existing expression is preserved automatically. |
| **`expression`, when supplied, fully replaces the old one** | There is no partial/incremental update of the formula logic. |
| **`synonyms`, when supplied, fully replaces the existing list** | To add a synonym without losing existing ones, first fetch the current list (via Get Unified Metrics in Workspace) and resend the full merged array. |
| **At least one of `formulaName` or `expression` is required** | Submitting a CONFIG with only `description`, `synonyms`, or `columnPriority` (and no `formulaName`/`expression`) returns error 8079. |
| **Renaming does not change `formulaId`** | The formula's identity is preserved across renames — all dependent reports/dashboards continue to reference it via `formulaId`. |
| **Dependency** | `<formula-id>` → Get Aggregate Formula (view-scoped) or Get Unified Metrics in Workspace. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7112 | The new expression could not be parsed (syntax error). | Review the expression for correct syntax. |
| 7113 | The expression references an unknown/unsupported function. | Verify the aggregate function name. |
| 7115 / 7116 | The expression references a column that does not exist, or the formula is otherwise invalid. | Verify all table/column names referenced. |
| 7160 | Formula operations are not allowed for this user/view combination. | Ensure the user is a Workspace Admin or has Create Formula permission on the view. |
| 7301 | User does not have permission. | Ensure the user is a Workspace Admin or has Create Formula permission on the view. |
| 7319 | The view does not belong to the specified workspace. | Confirm `<view-id>` belongs to `<workspace-id>`. |
| 7428 | The specified `<formula-id>` is not a valid aggregate formula on this view. | Verify `<formula-id>` using Get Aggregate Formula. |
| 8079 | Neither `formulaName` nor `expression` was provided. | Supply at least one of these two fields. |

---

## 4. Delete Aggregate Formula

Permanently deletes an aggregate formula from the specified view. By default, deletion is blocked if the formula is currently used by any dependent view (report, chart, dashboard) or referenced by another aggregate formula.

| Attribute | Value |
|-----------|-------|
| **Method** | DELETE |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/aggregateformulas/<formula-id>` |
| **OAuth Scope** | `ZohoAnalytics.modeling.delete` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace, or any user with Create Formula permission on the view. |
| **Rate Limit** | 20 requests per user per minute (10-minute lockout on breach). |

### CONFIG Parameters

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `deleteDependentViews` | Boolean | No | `false` | If `true`, all dependent views/dashboards that reference this aggregate formula are also permanently deleted before the formula itself is removed. If `false`, deletion is blocked with error 7173 if any dependents exist. |

### Sample Requests

**Case 1 — Delete an aggregate formula with no dependents**

```http
DELETE /restapi/v2/workspaces/137687000271334001/views/137687000271334499/aggregateformulas/137687000271334553 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={}
```

**Case 2 — Delete an aggregate formula and cascade-delete all dependents**

```http
DELETE /restapi/v2/workspaces/137687000271334001/views/137687000271334499/aggregateformulas/137687000271334553 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"deleteDependentViews":true}
```

**Case 3 — White label portal user deleting an aggregate formula**

```http
DELETE /restapi/v2/workspaces/137687000271334001/views/137687000271334499/aggregateformulas/137687000271334553 HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.cccccc.dddddd
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Delete Aggregate Formula returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |
| **Always check dependents first** | Use [Get Aggregate Formula Dependents](#6-get-aggregate-formula-dependents) before deleting to see exactly which views, dashboards, and other aggregate formulas depend on this one. |
| **`deleteDependentViews: true` is permanent** | All dependent reports, charts, pivot tables, dashboards, and referencing aggregate formulas are permanently deleted. This cannot be undone. |
| **Not idempotent** | Attempting to delete a formula ID that does not exist (or was already deleted) returns an error, not a silent success. |
| **Dependency** | `<formula-id>` → Get Aggregate Formula or Get Unified Metrics in Workspace. Always call Get Aggregate Formula Dependents beforehand to assess impact. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7107 | The specified formula ID does not exist as a column on this view. | Verify `<formula-id>` using Get Aggregate Formula. |
| 7160 | Formula operations are not allowed for this user/view combination. | Ensure the user is a Workspace Admin or has Create Formula permission on the view. |
| 7173 | The aggregate formula is currently used by one or more dependent views/dashboards/formulas; deletion blocked. | Use Get Aggregate Formula Dependents to identify dependents, then either remove them manually first or set `deleteDependentViews: true` to cascade delete. |
| 7301 | User does not have permission. | Ensure the user is a Workspace Admin or has Create Formula permission on the view. |
| 7319 | The view does not belong to the specified workspace. | Confirm `<view-id>` belongs to `<workspace-id>`. |
| 7428 | The specified column is not a valid aggregate formula. | Verify `<formula-id>` refers to an aggregate formula, not a regular or custom formula column. |

---

## 5. Get Unified Metrics in Workspace

Returns the full list of aggregate formulas (Unified Metrics) across **every** view/table in the workspace, along with the table that owns each formula. Use this API when you need a workspace-wide inventory of all metrics rather than the formulas owned by a single view.

> **Renamed for clarity:** This API corresponds to the underlying `/aggregateformulas` workspace-level endpoint. It has been documented here as **"Get Unified Metrics in Workspace"** to better reflect its purpose as a workspace-wide metrics catalogue, distinct from the view-scoped [Get Aggregate Formula](#1-get-aggregate-formula) API.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/aggregateformulas` |
| **OAuth Scope** | `ZohoAnalytics.metadata.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace, or any user with Read permission on the workspace. |

> This API has no CONFIG parameter.

### Sample Requests

**Case 1 — Get all Unified Metrics in the workspace**

```http
GET /restapi/v2/workspaces/137687000271334001/aggregateformulas HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — White label portal Shared User with restricted view of expressions**

```http
GET /restapi/v2/workspaces/137687000271334001/aggregateformulas HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.cccccc.dddddd
ZANALYTICS-ORGID: 700000123456
```

### Sample Responses

**HTTP 200 OK — Workspace Admin (full expression visibility)**

```json
{
  "status": "success",
  "summary": "Get aggregate formulas in workspace",
  "data": {
    "aggregateFormulas": [
      {
        "formulaId": "137687000271334557",
        "formulaName": "Ag_3",
        "expression": "max(\"Table_1\".\"Cost\")",
        "description": "",
        "subtypeId": 6,
        "subtype": "DECIMAL_NUMBER",
        "tableId": "137687000271334499",
        "tableName": "Table_1",
        "createdBy": "sales.admin@zylker.com",
        "modifiedTime": "1783507397220"
      },
      {
        "formulaId": "137687000271334569",
        "formulaName": "qt_agg1",
        "expression": "sum(\"QT1\".\"Cost\")",
        "description": "",
        "subtypeId": 6,
        "subtype": "DECIMAL_NUMBER",
        "tableId": "137687000271334508",
        "tableName": "QT1",
        "createdBy": "sales.admin@zylker.com",
        "modifiedTime": "1783507397220"
      }
    ]
  }
}
```

**HTTP 200 OK — Shared User (expression hidden — empty string)**

```json
{
  "status": "success",
  "summary": "Get aggregate formulas in workspace",
  "data": {
    "aggregateFormulas": [
      {
        "formulaId": "137687000271334207",
        "formulaName": "Ag_3",
        "expression": "",
        "description": "",
        "subtypeId": 6,
        "subtype": "DECIMAL_NUMBER",
        "tableId": "137687000271334149",
        "tableName": "Table_1",
        "createdBy": "sales.admin@zylker.com",
        "modifiedTime": "1783507040473"
      }
    ]
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `aggregateFormulas` | Array | List of every aggregate formula in the workspace, regardless of which view owns it. |
| `aggregateFormulas[].formulaId` | String | Unique ID of the aggregate formula. Use as `<formula-id>` for Get Aggregate Formula Dependents and Get Aggregate Formula Value. |
| `aggregateFormulas[].formulaName` | String | Display name of the formula. |
| `aggregateFormulas[].expression` | String | The aggregate expression. Returned as an **empty string** if the calling user does not have edit permission on the formula. |
| `aggregateFormulas[].description` | String | Description of the formula. Empty string if not set. |
| `aggregateFormulas[].subtypeId` | Integer | Internal numeric code for the formula's result data type. See [Subtype Values](#subtype-values). |
| `aggregateFormulas[].subtype` | String | Display-form internal code for the result data type (e.g., `"NUMBER"`, `"DECIMAL_NUMBER"`). **Note:** this field is named `subtype` here, not `subtypeName` as in the view-scoped Get Aggregate Formula API — the underlying data is identical, only the JSON key differs between the two APIs. |
| `aggregateFormulas[].tableId` | String | ID of the table/view that owns this aggregate formula. Cross-reference with Get View List. |
| `aggregateFormulas[].tableName` | String | Display name of the owning table/view. |
| `aggregateFormulas[].createdBy` | String | Email address of the user who created the formula. |
| `aggregateFormulas[].modifiedTime` | String | Epoch milliseconds of the last modification to the formula. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Field name discrepancy: `subtype` vs `subtypeName`** | This workspace-scoped API returns the display-form data type under the key `subtype`, while the view-scoped [Get Aggregate Formula](#1-get-aggregate-formula) API returns the same information under the key `subtypeName`. Both represent identical data — account for this naming difference when parsing responses from both APIs. |
| **Expression visibility is permission-gated per formula** | As with the view-scoped listing, users without edit permission on a given formula see `expression: ""` for that entry, even if they can see other metadata fields. |
| **Includes formulas owned by Query Tables** | `tableName` may refer to a Query Table (e.g., `"QT1"`) as well as a regular table, since aggregate formulas can be defined on Query Table views too. |
| **Read-only permission is sufficient** | Unlike the view-scoped Create/Edit/Delete APIs (which require Create Formula permission), this workspace-scoped listing only requires standard Read permission on the workspace. |
| **Dependency** | `tableId` → Get View List / Get Table Metadata (to see the owning table's schema). `formulaId` → Get Aggregate Formula Dependents, Get Aggregate Formula Value. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7301 | User does not have permission. | Ensure the user is a Workspace Admin or has Read permission on the workspace. |

---

## 6. Get Aggregate Formula Dependents

Returns all views, dashboards, and other aggregate formulas that depend on the specified aggregate formula, along with the parent table(s) it is built from. Use this before deleting or making breaking changes to a formula.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/aggregateformulas/<formula-id>/dependents` |
| **OAuth Scope** | `ZohoAnalytics.metadata.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace, or any user with Read permission on the workspace. |

> This API has no CONFIG parameter.

### Sample Requests

**Case 1 — Get dependents of an aggregate formula used in a dashboard**

```http
GET /restapi/v2/workspaces/137687000271334001/aggregateformulas/137687000112449553/dependents HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Get dependents of a formula with no dependents (safe to delete)**

```http
GET /restapi/v2/workspaces/137687000271334001/aggregateformulas/137687000112449600/dependents HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

### Sample Responses

**HTTP 200 OK — Formula used in a chart and a tabbed dashboard**

```json
{
  "status": "success",
  "summary": "Get aggregate formula dependents",
  "data": {
    "childViews": [
      {
        "viewName": "Chart_3_1",
        "viewId": "137687000112449496",
        "viewType": "Chart View",
        "viewTypeId": 2
      }
    ],
    "parentTables": [
      {
        "viewId": "137687000112449495",
        "viewName": "Table_3",
        "viewType": "Table",
        "viewTypeId": 0
      }
    ],
    "aggregateFormulas": [],
    "childDashboards": [
      {
        "viewId": "137687000112449498",
        "viewName": "Dashboard_1",
        "viewType": "Dashboard",
        "viewTypeId": 7
      },
      {
        "viewId": "137687000112449499",
        "viewName": "Tab Dashboard 1",
        "viewType": "Tab",
        "viewTypeId": 9,
        "tabIds": ["137687000112449500", "137687000112449501"]
      }
    ]
  }
}
```

**HTTP 200 OK — Formula with no dependents**

```json
{
  "status": "success",
  "summary": "Get aggregate formula dependents",
  "data": {
    "childViews": [],
    "parentTables": [
      {
        "viewId": "137687000112449600",
        "viewName": "Table_5",
        "viewType": "Table",
        "viewTypeId": 0
      }
    ],
    "aggregateFormulas": [],
    "childDashboards": []
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `childViews` | Array | Reports, charts, and pivot tables (non-dashboard views) that use this aggregate formula. Empty array if none. |
| `childViews[].viewId` | String | ID of the dependent view. |
| `childViews[].viewName` | String | Display name of the dependent view. |
| `childViews[].viewType` | String | Human-readable view type, e.g., `"Chart View"`, `"Pivot View"`. |
| `childViews[].viewTypeId` | Integer | Numeric view type ID (see [Common `viewTypeId` Values](#common-viewtypeid-values) below). |
| `parentTables` | Array | The base table(s) this aggregate formula is computed from (i.e., the table referenced in the `expression`). Typically contains a single entry — the owning table — but may include additional linked tables for cross-table aggregates. |
| `parentTables[].viewId` / `viewName` / `viewType` / `viewTypeId` | String / String / String / Integer | Same structure as `childViews`, but describing the source table rather than a dependent. |
| `aggregateFormulas` | Array | Other aggregate formulas that reference this one in their own expression (formula-on-formula dependencies). Empty array if none. |
| `aggregateFormulas[].formulaId` / `formulaName` | String / String | ID and name of the dependent aggregate formula. |
| `childDashboards` | Array | Dashboards (including tabbed dashboards) that include a widget referencing this formula. Empty array if none. |
| `childDashboards[].viewId` / `viewName` / `viewType` / `viewTypeId` | String / String / String / Integer | Standard view identification fields for the dashboard. |
| `childDashboards[].tabIds` | Array of String | **Only present when `viewType` is `"Tab"`** (a tabbed dashboard container). Lists the IDs of the individual dashboard tabs that use this formula. |

#### Common `viewTypeId` Values

| `viewTypeId` | `viewType` |
|--------------|------------|
| `0` | Table |
| `2` | Chart View |
| `3` | Pivot View |
| `7` | Dashboard |
| `9` | Tab (tabbed dashboard container) |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Always call before Delete Aggregate Formula** | The `childViews`, `childDashboards`, and `aggregateFormulas` arrays together represent everything that would be affected by `deleteDependentViews: true` on the Delete Aggregate Formula API. |
| **`parentTables` shows lineage, not dependents** | This is the only field in the response describing what the formula is built *from*, rather than what depends *on* it. Useful for understanding a formula's data lineage before editing its expression. |
| **Tabbed dashboards are consolidated** | Multiple tabs within the same tabbed dashboard that all use the formula are reported as a single `childDashboards` entry with `viewType: "Tab"` and a `tabIds` array, rather than one entry per tab. |
| **Dependency** | `<formula-id>` → Get Unified Metrics in Workspace or the view-scoped Get Aggregate Formula. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7301 | User does not have permission. | Ensure the user is a Workspace Admin or has Read permission on the workspace. |
| 7428 | The specified `<formula-id>` is not a valid aggregate formula, or does not belong to a view in this workspace. | Verify `<formula-id>` using Get Unified Metrics in Workspace. |

---

## 7. Get Aggregate Formula Value

Computes and returns the current live value of the specified aggregate formula by executing its expression against the underlying data at request time.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/aggregateformulas/<formula-id>/value` |
| **OAuth Scope** | `ZohoAnalytics.metadata.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace, or any user with Read permission on the workspace **and** access to the columns/tables involved in the formula. |

> This API has no CONFIG parameter.

### Sample Requests

**Case 1 — Get the value of a total sales metric**

```http
GET /restapi/v2/workspaces/137687000271334001/aggregateformulas/137687000105964059/value HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Get the value of a metric built on a Query Table**

```http
GET /restapi/v2/workspaces/137687000271334001/aggregateformulas/137687000267960449/value HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 3 — Shared user fetching a metric value**

```http
GET /restapi/v2/workspaces/137687000271334001/aggregateformulas/137687000105964061/value HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

### Sample Responses

**HTTP 200 OK — Table-based aggregate**

```json
{
  "status": "success",
  "summary": "Get aggregate formula value",
  "data": {
    "formulaId": "137687000105964059",
    "formulaName": "Ag_1",
    "formulaValue": "1299947.06"
  }
}
```

**HTTP 200 OK — Query Table-based aggregate**

```json
{
  "status": "success",
  "summary": "Get aggregate formula value",
  "data": {
    "formulaId": "137687000267960449",
    "formulaName": "qt_agg1",
    "formulaValue": "480774.4600000001"
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `formulaId` | String | ID of the aggregate formula queried. |
| `formulaName` | String | Display name of the aggregate formula. |
| `formulaValue` | String | The computed result of the formula's expression, evaluated live against the current data. Always returned as a string, regardless of whether the underlying result is numeric or decimal — parse according to the formula's `subtypeId`/`subtype` if numeric processing is required. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Value is computed live, not cached** | Each call re-executes the underlying aggregate query against the current data. Expect latency proportional to the size of the source table(s) and complexity of the expression. |
| **Requires column-level access, not just workspace access** | Beyond basic workspace Read permission, the caller must have visibility into the specific columns referenced by the formula's expression. If any referenced column is restricted from the caller via column-level sharing, the request is forbidden. |
| **`formulaValue` is always a string** | Even for numeric/decimal results, the value is serialized as a string (e.g., `"1299947.06"`) to preserve precision — parse it into a number in your application if further calculation is needed. |
| **Works for both table-based and Query Table-based formulas** | The owning view of the formula can be a regular table or a [Query Table](QUERY_TABLES_API_DOC_INFO.md); this API transparently supports both. |
| **Dependency** | `<formula-id>` → Get Unified Metrics in Workspace or the view-scoped Get Aggregate Formula. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7301 | User does not have permission, or the user lacks access to a column/table involved in the formula. | Ensure the user is a Workspace Admin, or has Read permission on the workspace and visibility into all columns used by the formula. |
| 7428 | The specified `<formula-id>` is not a valid aggregate formula. | Verify `<formula-id>` using Get Unified Metrics in Workspace. |

---

## Appendix A – Common HTTP Headers

| Header | Value | Required | Notes |
|--------|-------|----------|-------|
| `Authorization` | `Zoho-oauthtoken <oauth-token>` | **Mandatory** | OAuth 2.0 access token of the calling user. |
| `ZANALYTICS-ORGID` | Organisation ID | **Mandatory** for all APIs | Organisation ID of the workspace. |
| `Content-Type` | `application/x-www-form-urlencoded` | Required for POST/PUT with body | Not required for GET requests without CONFIG. |

> **White Label / Client Portal:** All seven aggregate formula APIs are available via portal domain URLs when the caller has the required permission.

---

## Appendix B – OAuth Scope Summary

| API | Method | Scope |
|-----|--------|-------|
| Get Aggregate Formula | GET | `ZohoAnalytics.metadata.read` |
| Add Aggregate Formula | POST | `ZohoAnalytics.modeling.create` |
| Edit Aggregate Formula | PUT | `ZohoAnalytics.modeling.update` |
| Delete Aggregate Formula | DELETE | `ZohoAnalytics.modeling.delete` |
| Get Unified Metrics in Workspace | GET | `ZohoAnalytics.metadata.read` |
| Get Aggregate Formula Dependents | GET | `ZohoAnalytics.metadata.read` |
| Get Aggregate Formula Value | GET | `ZohoAnalytics.metadata.read` |

---

## Appendix C – API-Specific Notes and Behaviours

### Get Aggregate Formula (view-scoped)

- **Entry point for view-owned formula management.** Use this to enumerate formulas before editing/deleting them via the view-scoped APIs.
- **`subtypeName` key** — remember this differs from the `subtype` key used in the workspace-scoped [Get Unified Metrics in Workspace](#5-get-unified-metrics-in-workspace). Do not assume identical field names across the two "list" endpoints.
- **Dependency chain:** Get View List → Get Aggregate Formula → Edit/Delete Aggregate Formula.

### Add Aggregate Formula

- **`synonyms` and `columnPriority` power NLP/Ask Zia search**, not the computed value. Populate these fields when you want the metric to be discoverable via natural-language queries in Zoho Analytics' AI-assisted search.
- **Cross-table expressions require an existing lookup.** If your expression spans two tables, ensure a [lookup relationship](LOOKUPS_AND_RELATIONSHIPS_API_DOC_INFO.md) already connects them, or the expression will fail to resolve the referenced column.
- **Dependency chain:** Get Table Metadata (verify columns) → Add Aggregate Formula → `formulaId` returned in response.

### Edit Aggregate Formula

- **The only formula-edit API in this API suite that supports renaming without resending the expression.** Compare this to [Edit Custom Formula](FORMULA_COLUMNS_API_DOC_INFO.md#3-edit-custom-formula), which has no rename capability at all. This asymmetry is a deliberate design difference between per-row formula columns and workspace-level aggregate formulas — plan integrations accordingly.
- **`synonyms` array is a full replace, not an append.** Always fetch and merge the existing list first if you want to add to it incrementally.
- **Dependency chain:** Get Aggregate Formula / Get Unified Metrics in Workspace (`formulaId`) → Edit Aggregate Formula.

### Delete Aggregate Formula

- **Always run Get Aggregate Formula Dependents first.** The dependents check considers `childViews`, `childDashboards`, and `aggregateFormulas` — all three categories are subject to cascading deletion when `deleteDependentViews: true` is set.
- **Dependency chain:** Get Aggregate Formula Dependents → Delete Aggregate Formula.

### Get Unified Metrics in Workspace

- **The most complete formula inventory in this API set.** Unlike the view-scoped listing, this returns formulas from every table/view in the workspace in one call, along with the owning `tableId`/`tableName` — ideal for building a workspace-wide metrics catalogue or documentation page.
- **Only requires Read permission**, not Create Formula permission — broader audience of callers can use this listing endpoint compared to the view-scoped CRUD APIs.
- **Dependency chain:** Get Unified Metrics in Workspace → Get Aggregate Formula Dependents / Get Aggregate Formula Value (using the returned `formulaId`).

### Get Aggregate Formula Dependents

- **`parentTables` is unique to this API** — none of the other Get Dependents-style APIs in this documentation set (e.g., [Get Column Dependents](COLUMNS_API_DOC_INFO.md#6-get-column-dependents)) return lineage information about what the object is built *from*; only aggregate formula dependents include this.
- **Dependency chain:** Get Unified Metrics in Workspace (`formulaId`) → Get Aggregate Formula Dependents → (optional) Delete Aggregate Formula.

### Get Aggregate Formula Value

- **This is the only API in the entire aggregate formula/custom formula documentation set that returns computed data rather than metadata.** Use it sparingly for large/complex formulas since each call triggers a live query execution.
- **Column-level permission matters, not just workspace-level.** A user could pass the workspace Read check yet still be denied here if they lack visibility into a specific column used by the formula's expression.
- **Dependency chain:** Get Unified Metrics in Workspace (`formulaId`) → Get Aggregate Formula Value.

---

## Appendix D – General Response Payload Notes

| Field / Behaviour | Detail |
|-------------------|--------|
| **`formulaId` is shared across view-scoped and workspace-scoped APIs** | The same `formulaId` value returned by the view-scoped [Get Aggregate Formula](#1-get-aggregate-formula) is used to call the workspace-scoped [Get Aggregate Formula Dependents](#6-get-aggregate-formula-dependents) and [Get Aggregate Formula Value](#7-get-aggregate-formula-value) — no separate ID resolution is needed. |
| **`subtypeName` in Get Aggregate Formula vs `subtype` in Get Unified Metrics in Workspace** | Both fields describe the same internal result-data-type code, but use different JSON keys between the view-scoped and workspace-scoped listing APIs. Always check which endpoint you're parsing. |
| **Expression redaction is permission-based, not role-based** | Whether `expression` is visible depends on whether the specific calling user has edit permission on that specific formula (which may vary formula-by-formula for custom-role users), not simply their broad role (Admin/Shared/Group). |
| **Empty response bodies are common for mutating calls** | Edit Aggregate Formula and Delete Aggregate Formula both return HTTP **204 No Content** with no JSON body at all — treat the 2xx status code as the success indicator, not the presence/absence of a `status` field. |
| **`formulaValue` is always serialized as a string** | Regardless of whether the aggregate's `subtypeId` indicates `NUMBER` or `DECIMAL_NUMBER`, the value in Get Aggregate Formula Value is returned as a JSON string, not a native number — parse accordingly. |
