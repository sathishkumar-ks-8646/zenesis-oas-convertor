# Zoho Analytics V2 REST API — Query Tables

This document covers the APIs for creating, editing, listing, and inspecting **Query Tables** — virtual tables defined by a user-written SQL `SELECT` query that runs against one or more existing tables/views in the workspace.

## What is a Query Table?

A **Query Table** (also called a **SQL View** or **QT**) is a view whose data is computed by executing a custom SQL query at query time rather than storing raw imported data. It allows joining, aggregating, and transforming data from one or more existing tables in the workspace using standard SQL syntax.

> **Rate Limited:** Create Query Table and Edit Query Table are throttled — a maximum of 7 requests per user per minute (5-minute lockout on breach) and 15 requests per minute service-wide. Design your integration to batch or space out query table creation/edit calls accordingly.

---

## Index

| # | API Name | Method | URL |
|---|----------|--------|-----|
| 1 | [Get Query Tables](#1-get-query-tables) | GET | `/restapi/v2/workspaces/<workspace-id>/querytables` |
| 2 | [Create Query Table](#2-create-query-table) | POST | `/restapi/v2/workspaces/<workspace-id>/querytables` |
| 3 | [Edit Query Table](#3-edit-query-table) | PUT | `/restapi/v2/workspaces/<workspace-id>/querytables/<querytable-id>` |
| 4 | [Get Query Table Details](#4-get-query-table-details) | GET | `/restapi/v2/workspaces/<workspace-id>/querytables/<querytable-id>` |

---

## 1. Get Query Tables

Returns a paginated, filterable, sortable list of all query tables in the workspace.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/querytables` |
| **OAuth Scope** | `ZohoAnalytics.metadata.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace, or any user with Create Query Table permission on the workspace. |

### CONFIG Parameters

CONFIG is optional for this API — omitting it returns the full, unfiltered, default-sorted list.

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `keyword` | String | No | — | Filters the list to query tables whose name contains this keyword (case-insensitive substring match). |
| `startIndex` | Integer | No | `1` | 1-based index of the first record to return, for pagination. |
| `noOfResult` | Integer | No | `20` | Number of records to return per page. Only applied when `startIndex` is also provided. |
| `sortedColumn` | Integer (enum) | No | `0` | Column to sort by. See [Sort Column Values](#sort-column-values) below. Valid range: `0`–`2`. |
| `sortedOrder` | Integer (enum) | No | `0` | Sort direction. See [Sort Order Values](#sort-order-values) below. Valid range: `0`–`1`. |
| `criteriaZuid` | Long | No | — | Filters the list to query tables created by the specified user (Zoho User ID). |

#### Sort Column Values

| `sortedColumn` Value | Sorts By |
|-----------------------|----------|
| `0` (default) | Display name (alphabetical) |
| `1` | Created time |
| `2` | Last modified time |

#### Sort Order Values

| `sortedOrder` Value | Direction |
|------------------------|-----------|
| `0` (default) | Ascending |
| `1` | Descending |

### Sample Requests

**Case 1 — Get all query tables (no filters)**

```http
GET /restapi/v2/workspaces/20868000000040672/querytables HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Search by keyword, sorted by last modified time, descending**

```http
GET /restapi/v2/workspaces/20868000000040672/querytables HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"keyword":"Sales","sortedColumn":2,"sortedOrder":1}
```

**Case 3 — Paginated request (page 2, 10 per page)**

```http
GET /restapi/v2/workspaces/20868000000040672/querytables HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"startIndex":11,"noOfResult":10}
```

### Sample Responses

**HTTP 200 OK**

```json
{
  "status": "success",
  "summary": "Get query tables",
  "data": {
    "queryTables": [
      {
        "viewId": "20868000000040794",
        "viewName": "Multi_Table",
        "viewDesc": "",
        "viewType": "QueryTable",
        "parentViewId": "",
        "folderId": "20868000000041715",
        "createdTime": "1781069354934",
        "createdBy": "sales.admin@zylker.com",
        "lastModifiedTime": "1781069400680",
        "lastModifiedBy": "sales.admin@zylker.com",
        "isFavorite": false,
        "sharedBy": "",
        "workspaceId": "20868000000040672",
        "orgId": "700000123456"
      },
      {
        "viewId": "20868000000040782",
        "viewName": "Regional_Sales_QT",
        "viewDesc": "",
        "viewType": "QueryTable",
        "parentViewId": "",
        "folderId": "20868000000041715",
        "createdTime": "1781069354934",
        "createdBy": "sales.admin@zylker.com",
        "lastModifiedTime": "1781069417733",
        "lastModifiedBy": "sales.admin@zylker.com",
        "isFavorite": false,
        "sharedBy": "",
        "workspaceId": "20868000000040672",
        "orgId": "700000123456"
      }
    ]
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `viewId` | String | Unique ID of the query table. Use this as `<querytable-id>` in Edit/Get Details APIs. |
| `viewName` | String | Display name of the query table. |
| `viewDesc` | String | Description of the query table. Empty string if not set. |
| `viewType` | String | Always `"QueryTable"` for entries in this list. |
| `parentViewId` | String | Empty for query tables (no parent view concept applies). |
| `folderId` | String | ID of the folder containing this query table. |
| `createdTime` | String | Epoch milliseconds when the query table was created. |
| `createdBy` | String | Email address of the creator. |
| `lastModifiedTime` | String | Epoch milliseconds of the last design modification. |
| `lastModifiedBy` | String | Email address of the last modifier. |
| `isFavorite` | Boolean | Whether the calling user has marked this query table as a favourite. |
| `sharedBy` | String | Email of the user who shared this query table with the caller, if applicable. Empty if owned by the caller. |
| `workspaceId` | String | ID of the workspace. |
| `orgId` | String | ID of the organisation. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **CONFIG is optional** | Omitting CONFIG entirely returns the full list of query tables (up to the default page size) sorted by name ascending. |
| **`noOfResult` only applies with `startIndex`** | Providing `noOfResult` alone without `startIndex` has no pagination effect; both must be supplied together to page through results. |
| **`sortedColumn` and `sortedOrder` are strict enums** | Values outside `0`–`2` for `sortedColumn` or `0`–`1` for `sortedOrder` return error 8119. |
| **`keyword` matches only the display name** | Substring search does not match the description or SQL query text. |
| **Dependency** | `viewId` values from this response are used as `<querytable-id>` for Edit Query Table and Get Query Table Details. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7301 | User does not have permission. | Ensure the user is a Workspace Admin or has Create Query Table permission on the workspace. |
| 8119 | Invalid value for `sortedColumn` or `sortedOrder`. | Use `0`–`2` for `sortedColumn` and `0`–`1` for `sortedOrder`. |

---

## 2. Create Query Table

Creates a new query table by executing a user-supplied SQL `SELECT` statement against existing tables/views in the workspace.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/querytables` |
| **OAuth Scope** | `ZohoAnalytics.modeling.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace, or any user with Create Query Table permission on the workspace. |
| **Rate Limit** | 7 requests/user/minute (5-minute lockout on breach); 15 requests/minute service-wide. |

### CONFIG Parameters

| Parameter | Type | Mandatory | Max Length | Description |
|-----------|------|-----------|------------|-------------|
| `queryTableName` | String | **Yes** | 80 chars | Display name for the new query table. Must be unique within the workspace. |
| `sqlQuery` | String | **Yes** | 100,000 chars | The SQL `SELECT` statement that defines the query table's data. Must reference existing tables/views in the same workspace. |
| `description` | String | No | 250 chars | Description of the query table. |
| `folderId` | Long | No | — | ID of the folder in which to place the query table. Defaults to the workspace's default folder if omitted. |

### Sample Requests

**Case 1 — Simple join query across two tables**

```http
POST /restapi/v2/workspaces/20868000000040672/querytables HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"queryTableName":"Employee_Department","sqlQuery":"SELECT E.FirstName, E.LastName, D.DepartmentName FROM Employee E INNER JOIN Department D ON E.DepartmentID = D.DepartmentID"}
```

**Case 2 — Aggregate query with description and target folder**

```http
POST /restapi/v2/workspaces/20868000000040672/querytables HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"queryTableName":"Monthly_Sales_Summary","sqlQuery":"SELECT Region, SUM(SalesAmount) AS TotalSales FROM Sales GROUP BY Region","description":"Aggregated monthly sales totals by region","folderId":20868000000041715}
```

**Case 3 — White label portal user creating a query table**

```http
POST /restapi/v2/workspaces/20868000000040672/querytables HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.cccccc.dddddd
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"queryTableName":"Client_Order_View","sqlQuery":"SELECT OrderID, OrderDate, Amount FROM Orders WHERE Status = 'Completed'"}
```

### Sample Responses

**HTTP 200 OK**

```json
{
  "status": "success",
  "summary": "Query table has been created successfully.",
  "data": {
    "viewId": "7617000099626164"
  }
}
```

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **SQL is parsed and validated at creation time** | The system converts the given `sqlQuery` into an internal query plan. Syntax errors, unknown tables/columns, and unsupported SQL constructs are caught and rejected before the query table is created. |
| **Referenced tables must exist in the same workspace** | Table/view names in the `FROM` and `JOIN` clauses must match existing views (by display name) in the same workspace. |
| **`queryTableName` must be unique** | Duplicate query table (or view) names within the workspace are rejected. |
| **Response returns only `viewId`** | Only the new query table's ID is returned. Call Get Query Table Details afterward to retrieve the full schema (auto-derived column list, data types, etc.). |
| **Column names and types are auto-derived** | The resulting query table's columns and their data types are inferred from the `SELECT` clause and the underlying source columns — they are not separately configurable at creation time. |
| **Query table over spatial (GEO) source files is not supported** | Creating a query table whose source is a spatial file type is rejected (error 7399). |
| **Duplicate submission protection** | If the same SQL query is submitted concurrently (e.g., due to network retries), the second request may be delayed or rejected to avoid creating duplicate query tables (error `DUPL_QUERY_TRIGGER`). |
| **Dependency** | `folderId` → Get Folder List. Referenced table/view names in `sqlQuery` → Get View List. After creation, call Get Query Table Details using the returned `viewId` to see resolved columns. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7301 | User does not have permission. | Ensure the user is a Workspace Admin or has Create Query Table permission on the workspace. |
| 7399 | The query references a spatial (GEO) file-based table, which is not supported for query tables. | Remove the spatial table reference from the SQL query. |
| 7400 | Query tables are not supported/allowed for this workspace. | Contact your administrator; this is a workspace-level restriction. |
| 7401 | The SQL statement is not a valid/allowed SQL construct. | Review the SQL for unsupported syntax (e.g., DDL/DML statements). Only `SELECT` queries are permitted. |
| 7402 | The SQL statement is invalid. | Verify the SQL syntax and referenced object names. |
| 7403 | Parsing of the SQL query failed. | Check for typos, mismatched parentheses, or unsupported SQL grammar. |
| 7404 | Conversion of the SQL query to the internal execution engine failed. | Simplify the query or check for unsupported functions/constructs. |
| 7407 | An invalid column was referenced in the `SELECT` clause. | Verify all column names referenced exist in the source table(s). |
| 7408 | An invalid column was referenced elsewhere in the query (e.g., `WHERE`, `GROUP BY`). | Verify all column names used in the query. |
| 7409 | An invalid/unknown table was referenced in the query. | Verify the table/view name matches an existing view in the workspace (case-sensitive display name). |
| 7413 | The number of arguments passed to a SQL function does not match its expected signature. | Check the function's expected argument count. |
| 7421 | A general SQL parse error occurred. | Review the query for syntax errors near the reported location. |
| 7433 | Duplicate column names detected in the `SELECT` clause (after aliasing). | Use unique aliases (`AS`) for columns with the same name from different tables. |
| 7447 | The query result would exceed the allowed row/column limit. | Add filters (`WHERE` clause) or reduce the number of selected columns to bring the result within limits. |

---

## 3. Edit Query Table

Updates the SQL definition and/or folder of an existing query table. The query table's data is recomputed based on the new SQL statement.

| Attribute | Value |
|-----------|-------|
| **Method** | PUT |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/querytables/<querytable-id>` |
| **OAuth Scope** | `ZohoAnalytics.modeling.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace, or any user with Design Modify permission on the query table. |
| **Rate Limit** | 7 requests/user/minute (5-minute lockout on breach); 15 requests/minute service-wide. |

### CONFIG Parameters

| Parameter | Type | Mandatory | Max Length | Description |
|-----------|------|-----------|------------|-------------|
| `sqlQuery` | String | **Yes** | 100,000 chars | The new SQL `SELECT` statement. Replaces the existing query definition entirely. |
| `folderId` | Long | No | — | ID of the folder to move the query table into. If omitted, the query table remains in its current folder. |

> **Note:** Unlike Create Query Table, this API has no `queryTableName` or `description` field — the display name and description of the query table cannot be changed via this API. Use Rename View / update description APIs for that purpose (not covered in this document).

### Sample Requests

**Case 1 — Update the SQL query only**

```http
PUT /restapi/v2/workspaces/20868000000040672/querytables/7617000099626164 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"sqlQuery":"SELECT E.FirstName, E.LastName, D.DepartmentName, E.Salary FROM Employee E INNER JOIN Department D ON E.DepartmentID = D.DepartmentID"}
```

**Case 2 — Update SQL and move to a different folder**

```http
PUT /restapi/v2/workspaces/20868000000040672/querytables/7617000099626164 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"sqlQuery":"SELECT Region, SUM(SalesAmount) AS TotalSales FROM Sales WHERE Year = 2026 GROUP BY Region","folderId":20868000000041720}
```

**Case 3 — White label portal user editing a query table**

```http
PUT /restapi/v2/workspaces/20868000000040672/querytables/7617000099626164 HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.cccccc.dddddd
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"sqlQuery":"SELECT OrderID, OrderDate, Amount FROM Orders WHERE Status IN ('Completed','Shipped')"}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Edit QueryTable returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. To confirm the change, call Get QueryTable Details afterward. |
| **`sqlQuery` is mandatory even for a folder-only move** | `sqlQuery` is always required, so it must be resupplied (with its existing value, unchanged) even if the intent is only to change `folderId`. Fetch the current SQL via Get Query Table Details first if you only want to move the query table. |
| **Full replace, not patch** | The new `sqlQuery` completely replaces the old one — there is no partial/incremental update of individual clauses. |
| **Column schema may change** | If the new SQL query selects different columns (added, removed, renamed, or retyped), the query table's column list is recomputed. Reports and dashboards built on removed/renamed columns will break. |
| **Concurrent edit protection** | If the query table is already being edited by another schema-changing operation, the request is rejected with a "design edit in progress" error until the previous operation finishes. |
| **No `queryTableName` or `description` field** | This API cannot rename the query table or change its description — only the SQL and folder can be updated here. |
| **Dependency** | `<querytable-id>` → Get Query Tables or Get Query Table Details. `folderId` → Get Folder List. After editing, call Get Query Table Details to confirm the updated column schema. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7301 | User does not have permission. | Ensure the user is a Workspace Admin or has Design Modify permission on the query table. |
| 7319 | The query table does not belong to the specified workspace. | Confirm `<querytable-id>` belongs to `<workspace-id>`. |
| 7401 | The SQL statement is not a valid/allowed SQL construct. | Only `SELECT` queries are permitted. |
| 7402 | The SQL statement is invalid. | Verify SQL syntax and referenced object names. |
| 7403 | Parsing of the SQL query failed. | Check for typos or unsupported SQL grammar. |
| 7404 | Conversion of the SQL query to the internal execution engine failed. | Simplify the query or check for unsupported functions/constructs. |
| 7407 | An invalid column was referenced in the `SELECT` clause. | Verify all column names exist in the source table(s). |
| 7409 | An invalid/unknown table was referenced in the query. | Verify the table/view name matches an existing view in the workspace. |
| 7422 | The query table is referenced as a source by a child view, preventing this type of structural change. | Review dependent views before making incompatible schema changes. |
| 7429 | A design edit (schema change) is already in progress for this query table. | Wait for the in-progress operation to complete, then retry. |
| 7447 | The query result would exceed the allowed row/column limit. | Add filters or reduce selected columns. |

---

## 4. Get Query Table Details

Returns the full metadata of a query table, including its SQL definition, the tables involved, and its column schema.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/querytables/<querytable-id>` |
| **OAuth Scope** | `ZohoAnalytics.metadata.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace, or any user with Design Modify permission on the query table. |

> This API has no CONFIG parameter.

### Sample Requests

**Case 1 — Get details of a query table**

```http
GET /restapi/v2/workspaces/7617000099626011/querytables/7617000099626164 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — White label portal user fetching query table details**

```http
GET /restapi/v2/workspaces/7617000099626011/querytables/7617000099626164 HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.cccccc.dddddd
ZANALYTICS-ORGID: 700000123456
```

### Sample Responses

**HTTP 200 OK**

```json
{
  "status": "success",
  "summary": "Get querytable details",
  "data": {
    "viewId": "7617000099626164",
    "viewName": "QT_1",
    "viewDesc": "",
    "sqlQuery": "SELECT\n\t\t E.FirstName,\n\t\t E.LastName,\n\t\t D.DepartmentName\nFROM  Employee E\nINNER JOIN Department D ON E.DepartmentID  = D.DepartmentID  \n",
    "workspaceId": "7617000099626011",
    "orgId": "700000123456",
    "createdTime": "1743431919984",
    "createdBy": "sales.admin@zylker.com",
    "createdByName": "Sales Admin",
    "lastDesignModifiedTime": "1743431920619",
    "lastDesignModifiedBy": "sales.admin@zylker.com",
    "lastDesignModifiedByName": "Sales Admin",
    "involvedViews": [
      {
        "viewId": "7617000099626002",
        "viewName": "Employee",
        "viewType": "Table"
      },
      {
        "viewId": "7617000099626105",
        "viewName": "Department",
        "viewType": "Table"
      }
    ],
    "columns": [
      {
        "columnId": "7617000099626167",
        "columnName": "E.FirstName",
        "dataType": "PLAIN",
        "dataTypeId": 1,
        "dataTypeName": "Plain Text",
        "columnIndex": 1,
        "columnDesc": "",
        "columnMaxSize": 253,
        "isNullable": true,
        "defaultValue": "",
        "pkTableName": "",
        "pkColumnName": "",
        "formulaDisplayName": "",
        "isHidden": false,
        "sortedOrder": 0,
        "sortedIndex": -1
      },
      {
        "columnId": "7617000099626168",
        "columnName": "E.LastName",
        "dataType": "PLAIN",
        "dataTypeId": 1,
        "dataTypeName": "Plain Text",
        "columnIndex": 2,
        "columnDesc": "",
        "columnMaxSize": 253,
        "isNullable": true,
        "defaultValue": "",
        "pkTableName": "",
        "pkColumnName": "",
        "formulaDisplayName": "",
        "isHidden": false,
        "sortedOrder": 0,
        "sortedIndex": -1
      },
      {
        "columnId": "7617000099626169",
        "columnName": "D.DepartmentName",
        "dataType": "PLAIN",
        "dataTypeId": 1,
        "dataTypeName": "Plain Text",
        "columnIndex": 3,
        "columnDesc": "",
        "columnMaxSize": 253,
        "isNullable": true,
        "defaultValue": "",
        "pkTableName": "",
        "pkColumnName": "",
        "formulaDisplayName": "",
        "isHidden": false,
        "sortedOrder": 0,
        "sortedIndex": -1
      }
    ]
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `viewId` | String | Unique ID of the query table. |
| `viewName` | String | Display name of the query table. |
| `viewDesc` | String | Description of the query table. |
| `sqlQuery` | String | The exact SQL statement currently defining this query table. |
| `workspaceId` | String | Workspace ID. |
| `orgId` | String | Organisation ID. |
| `createdTime` | String | Epoch milliseconds of creation. |
| `createdBy` | String | Email of the creator. |
| `createdByName` | String | Display name of the creator. |
| `lastDesignModifiedTime` | String | Epoch milliseconds of the last schema/SQL change. |
| `lastDesignModifiedBy` | String | Email of the last user who modified the SQL/schema. |
| `lastDesignModifiedByName` | String | Display name of the last modifier. |
| `involvedViews` | Array | List of source tables/views referenced by the SQL query. |
| `involvedViews[].viewId` | String | ID of the source view. |
| `involvedViews[].viewName` | String | Display name of the source view. |
| `involvedViews[].viewType` | String | Type of the source view, e.g., `"Table"`. |
| `columns` | Array | Auto-derived column schema of the query table (same structure as [Get Table Metadata](TABLE_AND_SCHEMA_API_DOC_INFO.md)). |
| `columns[].columnName` | String | Derived column name — typically `<table-alias>.<source-column-name>` unless aliased in the SQL with `AS`. |
| `columns[].dataType` / `dataTypeName` | String | Internal code / display name of the data type, inherited from the source column. |
| `columns[].pkTableName` / `pkColumnName` | String | Present only if the column is a lookup/foreign-key column resolved through a join; empty otherwise. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **`sqlQuery` reflects the exact stored SQL** | Formatting (line breaks, whitespace) is preserved as submitted in the most recent Create/Edit call. |
| **`columns[].columnName` often includes the source alias** | Unless the SQL query explicitly aliases each selected column with `AS`, the column name in the response is prefixed with the source table alias (e.g., `E.FirstName`), matching the `SELECT` clause exactly. |
| **`involvedViews` reflects only direct source tables** | If the query table's SQL references another query table (nested query tables), that nested query table itself appears in `involvedViews`, but its own upstream sources are not expanded recursively. |
| **Use before editing** | Since Edit Query Table requires resending the full `sqlQuery`, call this API first to retrieve the current query text, modify it, and then submit the edit. |
| **Dependency** | `<querytable-id>` → Get Query Tables. `involvedViews[].viewId` → cross-reference with Get View List / Get Table Metadata for the underlying source schema. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7301 | User does not have permission. | Ensure the user is a Workspace Admin or has Design Modify permission on the query table. |
| 7319 | The query table does not belong to the specified workspace. | Confirm `<querytable-id>` belongs to `<workspace-id>`. |

---

## Appendix A – Common HTTP Headers

| Header | Value | Required | Notes |
|--------|-------|----------|-------|
| `Authorization` | `Zoho-oauthtoken <oauth-token>` | **Mandatory** | OAuth 2.0 access token of the calling user. |
| `ZANALYTICS-ORGID` | Organisation ID | **Mandatory** for all APIs | Organisation ID of the workspace. |
| `Content-Type` | `application/x-www-form-urlencoded` | Required for POST/PUT with body | Not required for GET requests without CONFIG. |

> **White Label / Client Portal:** All four query table APIs are available via portal domain URLs when the caller has the required permission.

---

## Appendix B – OAuth Scope Summary

| API | Method | Scope |
|-----|--------|-------|
| Get Query Tables | GET | `ZohoAnalytics.metadata.read` |
| Create Query Table | POST | `ZohoAnalytics.modeling.create` |
| Edit Query Table | PUT | `ZohoAnalytics.modeling.update` |
| Get Query Table Details | GET | `ZohoAnalytics.metadata.read` |

---

## Appendix C – API-Specific Notes and Behaviours

### Get Query Tables

- **CONFIG is fully optional.** All fields default sensibly — omit CONFIG for a simple, unfiltered listing.
- **Pagination requires both `startIndex` and `noOfResult`.** Supplying only one has no effect.
- **`viewId` values feed directly into Edit and Get Details.** No separate ID resolution API call is required — this listing API is the entry point for the other three.

### Create Query Table

- **SQL is validated synchronously at creation time.** All syntax, table-reference, and column-reference checks happen before the API returns; there is no separate "draft" or "async validation" step exposed via this API.
- **Response is minimal — only `viewId`.** Always follow up with Get Query Table Details to retrieve the resolved column schema, since column names/types are derived from the query, not specified explicitly by the caller.
- **`folderId` defaults to the workspace's default folder.** Use Get Folder List and Make Default Folder (see [WORKSPACE_FOLDERS_API_DOC_INFO.md](WORKSPACE_FOLDERS_API_DOC_INFO.md)) to control the target folder explicitly.
- **Dependency chain:** Get View List (to identify valid source table names for the SQL) → Create Query Table → Get Query Table Details (to retrieve `viewId`'s resolved schema).

### Edit Query Table

- **`sqlQuery` must always be resent in full**, even for a folder-only move, because it is a mandatory attribute. There is no partial-update semantics.
- **No rename/description support.** This API cannot change `queryTableName` or `description` — only `sqlQuery` and `folderId`.
- **Changing the `SELECT` clause changes the column schema.** Any report, chart, or pivot built on a column that is renamed or removed from the new query will break. Always call Get Column Dependents-equivalent checks (via Get Query Table Details → `columns`) before making structural changes.
- **Dependency chain:** Get Query Table Details (fetch current `sqlQuery`) → modify → Edit Query Table → Get Query Table Details (confirm new schema).

### Get Query Table Details

- **Primary source of truth for the SQL definition.** Since the SQL is not exposed anywhere else (not in Get Query Tables list), always use this API to retrieve/audit the query text.
- **`involvedViews` is not recursive.** For query tables built on top of other query tables, only the immediate source is listed — trace nested dependencies manually if needed.
- **Dependency chain:** Get Query Tables (`viewId`) → Get Query Table Details → `involvedViews` cross-referenced against Get View List / Get Table Metadata for full lineage.

---

## Appendix D – General Response Payload Notes

| Field / Behaviour | Detail |
|-------------------|--------|
| **Rate limiting is per-user AND service-wide** | Both Create Query Table and Edit Query Table enforce a 7-per-minute-per-user limit (5-minute lockout) as well as a 15-per-minute service-wide limit. Exceeding either results in throttling — plan bulk operations with delays between calls. |
| **Query table columns follow the same schema shape as regular table columns** | The `columns` array in Get Query Table Details uses the same field structure (`columnId`, `dataType`, `dataTypeName`, `isHidden`, `sortedOrder`, etc.) documented in [TABLE_AND_SCHEMA_API_DOC_INFO.md](TABLE_AND_SCHEMA_API_DOC_INFO.md) and [COLUMNS_API_DOC_INFO.md](COLUMNS_API_DOC_INFO.md). |
| **Edit Query Table has no data payload on success** | Unlike Create (`viewId`) and Get Details (full metadata), a successful Edit call returns HTTP `204 No Content` with no response body. |
| **`orgId` in responses is the organisation ID, not the workspace ID** | Do not confuse `orgId` with `workspaceId` when parsing responses. |
