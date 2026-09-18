# Zoho Analytics V2 REST API — Column Management

This document covers the APIs for managing columns in a Zoho Analytics table — adding, renaming, deleting, showing/hiding, sorting, and inspecting column dependencies.

> **Tables only:** Add Column, Rename Column, Delete Column, Hide/Show Columns, and Get Column Dependents operate exclusively on *tables*. Calling these APIs with the view ID of a report, chart, or dashboard returns an error.

> **DDL Lock:** Add Column, Rename Column, and Delete Column check for a DDL lock before proceeding. If a data import or schema operation is already in progress on the table, the request is rejected with error 7092 until the lock is released.

> **White Label / Client Portal:** Sort Data by Columns and Reorder Columns are **not available** in custom-domain (portal) contexts. All other column management APIs are available via portal domain URLs when the caller has the required permission.

---

## Index

| # | API Name | Method | URL |
|---|----------|--------|-----|
| 1 | [Add Column](#1-add-column) | POST | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/columns` |
| 2 | [Rename Column](#2-rename-column) | PUT | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/columns/<column-id>` |
| 3 | [Delete Column](#3-delete-column) | DELETE | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/columns/<column-id>` |
| 4 | [Hide Columns](#4-hide-columns) | PUT | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/columns/hide` |
| 5 | [Show Columns](#5-show-columns) | PUT | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/columns/show` |
| 6 | [Get Column Dependents](#6-get-column-dependents) | GET | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/columns/<column-id>/dependents` |
| 7 | [Sort Data by Columns](#7-sort-data-by-columns) | PUT | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/data/sort` |
| 8 | [Reorder Columns](#8-reorder-columns) | PUT | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/columns/reorder` |

---

## 1. Add Column

Adds one or more columns to an existing table. Supports two distinct modes in a single API:

- **Single-column mode:** Provide `columnName` and `dataType` at the top level of CONFIG. Returns the new column's ID.
- **Bulk mode:** Provide a `columns` array with multiple column definitions. Adds all columns in one request. Returns a success confirmation (individual column IDs are not returned in bulk mode).

> **Mode selection:** The API detects which mode to use based on whether a `columns` key is present in CONFIG. If `columns` is present, bulk mode is used regardless of whether `columnName` is also present.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/columns` |
| **OAuth Scope** | `ZohoAnalytics.modeling.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace, or any user with Design Modify permission on the workspace. |

### CONFIG Parameters — Single-Column Mode

Use these top-level fields when adding one column at a time:

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `columnName` | String | **Yes** | — | Display name for the new column. Must be unique within the table. |
| `dataType` | String | **Yes** | — | Data type of the column. See the [Supported Data Types](#supported-data-types) table below. |
| `geoRole` | Integer | No | `null` | Geographic role ID for `GEO`-type columns. Specifies the geographic categorization level (e.g., country, state, city). Required when using geo data types. |
| `isPIIColumn` | Boolean | No | `false` | If `true`, marks this column as containing Personally Identifiable Information (PII). |

### CONFIG Parameters — Bulk Mode

Use the `columns` array when adding multiple columns in one request. Each element in `columns` defines one column:

| Parameter | Type | Mandatory | Max Items | Description |
|-----------|------|-----------|-----------|-------------|
| `columns` | JSONArray | **Yes** (for bulk mode) | 300 | Array of column definition objects. |

**Fields within each `columns` entry:**

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `columnName` | String | **Yes** | — | Display name for the column. Must be unique within the table. |
| `dataType` | String | **Yes** | — | Data type. See [Supported Data Types](#supported-data-types) below. |
| `geoRole` | Integer | No | `null` | Geographic role ID. Required for GEO-type columns. |
| `isPIIColumn` | Boolean | No | `false` | Marks the column as PII. |
| `isMandatory` | Boolean | No | `false` | If `true`, marks the column as mandatory for data entry. **When `isMandatory` is `true`, the `default` field becomes required.** |
| `default` | String | **Required when `isMandatory: true`** | `null` | Default value applied when no data is provided. Required if `isMandatory` is `true`. |

> **Bulk mode limit:** A maximum of 10 columns can be sent per bulk request. Exceeding this limit returns error 8173.

### Supported Data Types

The `dataType` field accepts the following values. These apply to both single-column and bulk modes.

| `dataType` Value | Display Name | Notes |
|------------------|--------------|-------|
| `PLAIN` | Plain Text | Short single-line text. |
| `MULTI_LINE` | Multi-line Text | Long-form text with line breaks. |
| `NUMBER` | Number | Integer numbers (positive and negative). |
| `POSITIVE_NUMBER` | Positive Number | Non-negative integers only. |
| `DECIMAL_NUMBER` | Decimal Number | Floating-point numbers. |
| `CURRENCY` | Currency | Monetary values with currency formatting. |
| `PERCENT` | Percentage | Percentage values. |
| `AUTO_NUMBER` | Auto Number | System-generated sequential integer. Cannot be combined with `isMandatory: true`. |
| `BOOLEAN` | True/False | Boolean checkbox (checked/unchecked). |
| `DATE` | Date Time | Date with time component (datetime). |
| `DATE_AS_DATE` | Date | Date only — no time component. |
| `TIME` | Time | Time of day. |
| `DURATION` | Duration | Time duration (hours/minutes/seconds). |
| `EMAIL` | Email Address | Validated email address. |
| `URL` | URL | Validated URL string. |
| `GEO` | Geographic (Text) | Text-based geographic column. Pair with `geoRole` integer ID to specify the geographic level. |
| `GEO_NUM` | Geographic (Number) | Number-based geographic column. Pair with `geoRole`. |

### Sample Requests

**Case 1 — Single column: add a plain text column**

```http
POST /restapi/v2/workspaces/466206000000071000/views/7617000000508001/columns HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"columnName":"Customer Segment","dataType":"PLAIN"}
```

**Case 2 — Single column: add a currency column with PII flag**

```http
POST /restapi/v2/workspaces/466206000000071000/views/7617000000508001/columns HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"columnName":"Annual Salary","dataType":"CURRENCY","isPIIColumn":true}
```

**Case 3 — Bulk mode: add multiple columns in one request**

```http
POST /restapi/v2/workspaces/466206000000071000/views/7617000000508001/columns HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"columns":[{"columnName":"Discount (%)","dataType":"PERCENT"},{"columnName":"Delivery Date","dataType":"DATE_AS_DATE"},{"columnName":"Notes","dataType":"MULTI_LINE","isMandatory":false}]}
```

**Case 4 — Bulk mode: add a mandatory column (requires `default` field)**

```http
POST /restapi/v2/workspaces/466206000000071000/views/7617000000508001/columns HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"columns":[{"columnName":"Status","dataType":"PLAIN","isMandatory":true,"default":"Pending"},{"columnName":"Priority","dataType":"PLAIN","isMandatory":true,"default":"Normal"}]}
```

**Case 5 — White label portal user adding a column**

```http
POST /restapi/v2/workspaces/466206000000071000/views/7617000000508001/columns HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.cccccc.dddddd
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"columnName":"Feedback","dataType":"MULTI_LINE"}
```

### Sample Responses

**HTTP 200 OK — Single-column mode**

```json
{
  "status": "success",
  "summary": "Column added successfully.",
  "data": {
    "columnId": "7617000071955030"
  }
}
```

**HTTP 200 OK — Bulk mode**

```json
{
  "status": "success",
  "summary": "Column added successfully."
}
```

> In bulk mode, individual column IDs are not returned. Use Get Table Metadata to retrieve the newly added columns and their IDs.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Mode is auto-detected** | If the CONFIG contains a `columns` key, bulk mode is used and `columnName`/`dataType` at the top level are ignored. If no `columns` key is present, single mode is used. |
| **Single mode returns `columnId`; bulk mode does not** | Single column add returns the new `columnId`. Bulk mode returns only success/failure status. After a bulk add, call Get Table Metadata to retrieve the new column IDs. |
| **`isMandatory: true` requires `default`** | In bulk mode, if a column has `isMandatory: true`, the `default` field is mandatory. The API will fail if `default` is absent for that column. |
| **DDL lock check** | If the table is locked due to an in-progress import or schema operation, the request is rejected with error 7092. Retry after the import completes. |
| **Bulk mode per-request limit** | A maximum of 10 columns can be sent per bulk request. Exceeding this returns error 8173. |
| **Column name uniqueness** | Each `columnName` must be unique within the table. Attempting to add a column with an existing name returns error 7157. |
| **Dependency** | `<view-id>` → Get View List. The view must be a table. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7089 | (For hide) All columns cannot be hidden simultaneously. | — |
| 7092 | DDL lock is active — an import or schema operation is in progress on the table. | Wait for the current import or schema operation to complete before adding a column. |
| 7111 | A view with the same name already exists. | — |
| 7125 | The data type is not compatible with the column's configuration. | Verify the `dataType` value. |
| 7146 | The `dataType` value is not recognised. | Use one of the values from the Supported Data Types table. |
| 7157 | A column with the same name already exists in the table. | Use a unique `columnName` within the table. |
| 7301 | User does not have permission. | Ensure the user is a Workspace Admin or has Design Modify permission on the workspace. |
| 7397 | The view is not a table. | This API only operates on tables. Verify the view type using Get View List. |
| 7439 | The view ID provided is not a table. | Provide the view ID of a table, not a report or dashboard. |
| 8173 | The number of columns in bulk mode exceeds the allowed limit. | Reduce the number of columns per request or split into multiple calls. |

---

## 2. Rename Column

Renames the specified column in the given table. The column is identified by its numeric column ID in the URL.

| Attribute | Value |
|-----------|-------|
| **Method** | PUT |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/columns/<column-id>` |
| **OAuth Scope** | `ZohoAnalytics.modeling.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace, or any user with Design Modify permission on the workspace. |

### CONFIG Parameters

| Parameter | Type | Mandatory | Description |
|-----------|------|-----------|-------------|
| `columnName` | String | **Yes** | New display name for the column. Must be unique within the table. |

### Sample Requests

**Case 1 — Rename a column**

```http
PUT /restapi/v2/workspaces/466206000000071000/views/7617000000508001/columns/7617000000508026 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"columnName":"Geographic Region"}
```

**Case 2 — White label portal user renaming a column**

```http
PUT /restapi/v2/workspaces/466206000000071000/views/7617000000508001/columns/7617000000508026 HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.cccccc.dddddd
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"columnName":"Client Region"}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Unlike Add Column (which returns an HTTP 200 with a JSON body containing `columnId`), Rename Column returns a bare HTTP `204 No Content` — do not expect a `status`/`summary` field on success. |
| **Rename propagates to dependent views** | Reports, charts, pivot tables, and formula columns that reference this column are automatically updated to use the new column name. No manual update of dependent views is needed. |
| **Renaming to the same name** | Succeeds without error (idempotent for the name). |
| **DDL lock check** | If the table is locked due to an in-progress import, the request is rejected with error 7092. |
| **Snapshot tables** | Columns in snapshot tables cannot be renamed (error 7164). |
| **Column not found** | If the column ID does not exist in the table, error 7107 is returned. Use Get Table Metadata to verify the `columnId`. |
| **Dependency** | `<view-id>` → Get View List. `<column-id>` → Get Table Metadata (to find the column's numeric ID). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7092 | DDL lock is active on the table. | Wait for the in-progress operation to complete. |
| 7107 | The specified column does not exist in the table. | Verify the `<column-id>` using Get Table Metadata. |
| 7111 | A column with the new name already exists in the table. | Use a unique column name within the table. |
| 7157 | Column name already exists. | Use a unique `columnName` within the table. |
| 7164 | The table is a snapshot table; columns cannot be renamed. | Snapshot tables are read-only schema-wise. Create a new table if schema changes are needed. |
| 7301 | User does not have permission. | Ensure the user is a Workspace Admin or has Design Modify permission on the workspace. |
| 7439 | The view is not a table. | Provide the view ID of a table. |

---

## 3. Delete Column

Permanently deletes a column from the specified table. By default, deletion is blocked if any dependent views (reports, charts, formulas) reference this column. You can override this by setting `deleteDependentViews` to `true`.

| Attribute | Value |
|-----------|-------|
| **Method** | DELETE |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/columns/<column-id>` |
| **OAuth Scope** | `ZohoAnalytics.modeling.delete` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace, or any user with Design Modify permission on the workspace. |

### CONFIG Parameters

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `deleteDependentViews` | Boolean | No | `false` | If `true`, all dependent views (reports, charts, pivot tables, formulas) that reference this column are also permanently deleted. If `false`, the deletion is blocked with error 7277 if any dependents exist. |

### Sample Requests

**Case 1 — Delete a column with no dependents**

```http
DELETE /restapi/v2/workspaces/466206000000071000/views/7617000000508001/columns/7617000000508026 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={}
```

**Case 2 — Delete a column and all its dependent views**

```http
DELETE /restapi/v2/workspaces/466206000000071000/views/7617000000508001/columns/7617000000508026 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"deleteDependentViews":true}
```

**Case 3 — White label portal user deleting a column**

```http
DELETE /restapi/v2/workspaces/466206000000071000/views/7617000000508001/columns/7617000000508026 HTTP/1.1
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
| **Success response has no body** | Delete Column returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |
| **Use Get Column Dependents first** | Before deleting, call [Get Column Dependents](#6-get-column-dependents) to discover all views and formulas that reference this column. This helps decide whether to proceed with `deleteDependentViews=false` (safe) or `deleteDependentViews=true` (cascade delete). |
| **`deleteDependentViews=true` is permanent** | All dependent views (reports, charts, pivot tables, query tables, formula columns) are permanently deleted along with the column. This cannot be undone. |
| **DDL lock check** | If the table is locked due to an in-progress import, the request is rejected with error 7092. |
| **Column not found** | If the column ID does not exist in the table, error 7107 is returned. |
| **Dependency** | `<view-id>` → Get View List. `<column-id>` → Get Table Metadata. Use Get Column Dependents to assess impact before deletion. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7092 | DDL lock is active on the table. | Wait for the in-progress operation to complete. |
| 7107 | The specified column does not exist in the table. | Verify `<column-id>` using Get Table Metadata. |
| 7277 | The column has dependent views; deletion blocked. | Call Get Column Dependents to identify them, then either delete them manually first or set `deleteDependentViews: true` to cascade delete. |
| 7301 | User does not have permission. | Ensure the user is a Workspace Admin or has Design Modify permission on the workspace. |
| 7439 | The view is not a table. | Provide the view ID of a table. |

---

## 4. Hide Columns

Hides one or more columns in the specified table. Hidden columns are not visible to users viewing the table but are retained in the schema and can be shown again using Show Columns. At least one column must remain visible at all times.

| Attribute | Value |
|-----------|-------|
| **Method** | PUT |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/columns/hide` |
| **OAuth Scope** | `ZohoAnalytics.modeling.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace, or any user with Design Modify permission on the view. |

### CONFIG Parameters

| Parameter | Type | Mandatory | Max Items | Description |
|-----------|------|-----------|-----------|-------------|
| `columnIds` | JSONArray of String | **Yes** | 1000 | Array of column IDs (as strings) to hide. All IDs must belong to the specified view. |

### Sample Requests

**Case 1 — Hide a single column**

```http
PUT /restapi/v2/workspaces/466206000000071000/views/7617000000508001/columns/hide HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"columnIds":["7617000000508026"]}
```

**Case 2 — Hide multiple columns at once**

```http
PUT /restapi/v2/workspaces/466206000000071000/views/7617000000508001/columns/hide HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"columnIds":["7617000000508026","7617000000508027","7617000000508028"]}
```

**Case 3 — White label portal user hiding columns**

```http
PUT /restapi/v2/workspaces/466206000000071000/views/7617000000508001/columns/hide HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.cccccc.dddddd
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"columnIds":["7617000000508026"]}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Hide Columns returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |
| **At least one column must remain visible** | If all currently visible columns are included in the `columnIds` list, the operation is rejected with error 7089. Keep at least one column outside the list. |
| **`columnIds` values are strings** | Column IDs must be passed as quoted strings in the JSON array (e.g., `["7617000000508026"]`), not as integers. |
| **Hiding an already-hidden column** | Silently no-ops for that column — no error is raised. Only columns that change state (visible → hidden) are updated. |
| **Hidden columns remain in schema** | Hidden columns are not deleted. They can be revealed again with Show Columns and still participate in formulas and reports. |
| **Dependency** | `<view-id>` → Get View List. `columnIds` → Get Table Metadata (use `columnId` values, checking `isHidden: false` to find visible columns). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7089 | Hiding these columns would leave no visible columns in the table. | Ensure at least one column is not in the `columnIds` list. |
| 7107 | One or more column IDs do not exist in the table. | Verify all IDs using Get Table Metadata. |
| 7301 | User does not have permission. | Ensure the user is a Workspace Admin or has Design Modify permission on the view. |
| 7397 | The view is not a table. | This API only works on tables. |

---

## 5. Show Columns

Makes one or more previously hidden columns visible again in the specified table.

| Attribute | Value |
|-----------|-------|
| **Method** | PUT |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/columns/show` |
| **OAuth Scope** | `ZohoAnalytics.modeling.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace, or any user with Design Modify permission on the view. |

### CONFIG Parameters

| Parameter | Type | Mandatory | Max Items | Description |
|-----------|------|-----------|-----------|-------------|
| `columnIds` | JSONArray of String | **Yes** | 1000 | Array of column IDs (as strings) to make visible. All IDs must belong to the specified view. |

### Sample Requests

**Case 1 — Show a previously hidden column**

```http
PUT /restapi/v2/workspaces/466206000000071000/views/7617000000508001/columns/show HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"columnIds":["7617000000508026"]}
```

**Case 2 — Show multiple hidden columns**

```http
PUT /restapi/v2/workspaces/466206000000071000/views/7617000000508001/columns/show HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"columnIds":["7617000000508026","7617000000508027"]}
```

**Case 3 — White label portal user showing columns**

```http
PUT /restapi/v2/workspaces/466206000000071000/views/7617000000508001/columns/show HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.cccccc.dddddd
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"columnIds":["7617000000508026"]}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Show Columns returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |
| **Showing an already-visible column** | Silently no-ops — no error is raised. Only columns that change state (hidden → visible) are updated. |
| **`columnIds` values are strings** | Column IDs must be passed as quoted strings in the JSON array, not as integers. |
| **No constraint on showing columns** | There is no minimum or maximum visible column count enforced for Show Columns (only Hide Columns has the one-visible-column minimum constraint). |
| **Dependency** | `<view-id>` → Get View List. `columnIds` → Get Table Metadata (use `columnId` values from columns where `isHidden: true`). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7107 | One or more column IDs do not exist in the table. | Verify all IDs using Get Table Metadata. |
| 7301 | User does not have permission. | Ensure the user is a Workspace Admin or has Design Modify permission on the view. |
| 7397 | The view is not a table. | This API only works on tables. |

---

## 6. Get Column Dependents

Returns all views, custom formula columns, and aggregate formulas that depend on the specified column. Use this before deleting or renaming a column to understand the full impact.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/columns/<column-id>/dependents` |
| **OAuth Scope** | `ZohoAnalytics.metadata.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace. |

> This API has no CONFIG parameter.

### Sample Requests

**Case 1 — Get all dependents for a column**

```http
GET /restapi/v2/workspaces/466206000000071000/views/7617000000508001/columns/7617000000508026/dependents HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Workspace Admin checking a currency column's dependents before deletion**

```http
GET /restapi/v2/workspaces/466206000000071000/views/7617000000508001/columns/7617000000508030/dependents HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

### Sample Responses

**HTTP 200 OK**

**Case 1 — Column used in views and a custom formula**

```json
{
  "status": "success",
  "summary": "Get column dependents",
  "data": {
    "views": [
      {
        "viewId": "221641000006857125",
        "viewName": "Monthly Sales QT",
        "viewTypeId": 6,
        "reportType": "QueryTable"
      },
      {
        "viewId": "221641000006856603",
        "viewName": "Sales Tabular View",
        "viewTypeId": 1,
        "reportType": "Report"
      },
      {
        "viewId": "221641000006856594",
        "viewName": "Sales by Region",
        "viewTypeId": 2,
        "reportType": "Chart"
      },
      {
        "viewId": "221641000006856601",
        "viewName": "Sales Pivot",
        "viewTypeId": 3,
        "reportType": "PivotView"
      }
    ],
    "customFormulas": [
      {
        "columnId": "221641000006856615",
        "columnName": "Profit Margin"
      }
    ],
    "aggregateFormulas": []
  }
}
```

**Case 2 — Column with no dependents**

```json
{
  "status": "success",
  "summary": "Get column dependents",
  "data": {
    "views": [],
    "customFormulas": [],
    "aggregateFormulas": []
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `views` | Array | List of views (reports, charts, pivot tables, query tables) that use this column. Empty array if none. |
| `views[].viewId` | String | Unique ID of the dependent view. |
| `views[].viewName` | String | Display name of the dependent view. |
| `views[].viewTypeId` | Integer | Numeric type ID: `1` = Report (Tabular), `2` = Chart, `3` = Pivot, `4` = Summary, `6` = Query Table. |
| `views[].reportType` | String | Human-readable type label: `"Report"`, `"Chart"`, `"PivotView"`, `"SummaryView"`, `"QueryTable"`. |
| `customFormulas` | Array | Formula columns in the same table whose expression uses this column. Empty array if none. |
| `customFormulas[].columnId` | String | Column ID of the formula column. |
| `customFormulas[].columnName` | String | Display name of the formula column. |
| `aggregateFormulas` | Array | Aggregate formula metrics that use this column. Empty array if none. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Use before delete** | Always call this API before calling Delete Column to understand the full cascade impact. If `views` or `customFormulas` are non-empty, setting `deleteDependentViews: true` in Delete Column will permanently remove all those objects. |
| **Workspace Admin only** | Unlike most column APIs which accept users with Design Modify permission, this API requires full Workspace Admin access. |
| **`views` may contain duplicates** | The same view can appear multiple times if it uses the column in multiple ways (e.g., a query table that both filters and displays the column). |
| **Dependency** | `<view-id>` → Get View List. `<column-id>` → Get Table Metadata. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7107 | The specified column does not exist in the table. | Verify `<column-id>` using Get Table Metadata. |
| 7301 | User does not have permission. | Only Workspace Admins can call this API. |
| 7319 | The view ID does not belong to the specified workspace. | Confirm the `<view-id>` belongs to the workspace in the URL. |

---

## 7. Sort Data by Columns

Sets the default sort order for rows in the specified table view. Supports two operational modes:

- **Set sort:** Provide a `columns` array (column IDs) and a `sortOrder` to apply ascending or descending sort by the specified columns.
- **Reset sort:** Provide `resetSort: true` to clear all current sort settings on the table.

> **Not available in custom-domain (White Label) contexts.** This API cannot be called via a portal domain URL. It is only accessible through the standard `analyticsapi.zoho.com` host.

| Attribute | Value |
|-----------|-------|
| **Method** | PUT |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/data/sort` |
| **OAuth Scope** | `ZohoAnalytics.modeling.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace, or any user with Design Modify permission on the view. |

### CONFIG Parameters

| Parameter | Type | Mandatory | Max Items | Default | Description |
|-----------|------|-----------|-----------|---------|-------------|
| `columns` | JSONArray of String | **Yes** (when setting sort) | 300 | — | Ordered array of column IDs (as strings) to sort by. The first ID is the primary sort key, subsequent IDs are secondary sort keys. |
| `sortOrder` | Integer | **Yes** (when setting sort) | — | — | Sort direction applied to **all** columns in the `columns` array. `1` = Ascending (A→Z, 0→9). `2` = Descending (Z→A, 9→0). |
| `resetSort` | Boolean | **Yes** (when resetting) | — | `false` | If `true`, clears all sort settings on the table. Must **not** be combined with `sortOrder` or `columns` — doing so returns error 8182. |

> **`sortOrder` values:** Only `1` (Ascending) and `2` (Descending) are valid. Any other integer returns error 8119.

> **`resetSort` vs sort fields:** `resetSort: true` and `sortOrder` are mutually exclusive. Including both in the same request returns error 8182.

### Sample Requests

**Case 1 — Sort by a single column ascending**

```http
PUT /restapi/v2/workspaces/466206000000071000/views/7617000000508001/data/sort HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"columns":["7617000000508025"],"sortOrder":1}
```

**Case 2 — Sort by multiple columns (primary: Date descending, secondary: Region ascending)**

> Note: When multiple columns are in `columns`, the same `sortOrder` applies to all. To sort different columns in different directions, this is not supported in a single call. Use a query table or report for mixed sort directions.

```http
PUT /restapi/v2/workspaces/466206000000071000/views/7617000000508001/data/sort HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"columns":["7617000000508025","7617000000508026"],"sortOrder":2}
```

**Case 3 — Reset all sort settings**

```http
PUT /restapi/v2/workspaces/466206000000071000/views/7617000000508001/data/sort HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"resetSort":true}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Sort Data by Columns returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |
| **Not available on custom domains** | This API is disabled for white label portal contexts. Calls made through a portal domain URL will fail. |
| **`sortOrder` applies to all columns uniformly** | All columns in the `columns` array are sorted in the same direction. Mixed sort directions (e.g., column A ascending, column B descending) are not supported via this API. |
| **`columns` array order defines sort priority** | The first column ID is the primary sort key; subsequent IDs are secondary, tertiary, etc. |
| **`columns` values are strings** | Column IDs must be quoted strings (e.g., `["7617000000508025"]`), not integers. |
| **`resetSort: true` with `sortOrder` is invalid** | Including both `resetSort: true` and `sortOrder` in the same CONFIG returns error 8182 before any changes are made. |
| **Column IDs must belong to the view** | Any column ID not present in the table returns error 8180. |
| **Verify result** | Use Get Table Metadata to confirm `sortedOrder` and `sortedIndex` values on the affected columns after calling this API. |
| **Dependency** | `<view-id>` → Get View List. `columns` array values → Get Table Metadata (use `columnId` strings). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7301 | User does not have permission. | Ensure the user is a Workspace Admin or has Design Modify permission on the view. |
| 7319 | The view ID does not belong to the specified workspace. | Confirm the `<view-id>` is correct. |
| 8119 | Invalid value for `sortOrder`. Only `1` (Ascending) and `2` (Descending) are accepted. | Use `1` for ascending or `2` for descending. |
| 8180 | One or more column IDs in the `columns` array do not belong to this view. | Verify all column IDs using Get Table Metadata. |
| 8182 | `resetSort: true` and `sortOrder` cannot be used together. | Use either `resetSort: true` (with no other fields) or `columns` + `sortOrder` (without `resetSort`). |

---

## 8. Reorder Columns

Changes the display order of all columns in the specified table. The complete set of non-system column IDs must be supplied in the desired order — this API does not support reordering a partial subset of columns.

> **Not available in custom-domain (White Label) contexts.** This API cannot be called via a portal domain URL. It is only accessible through the standard `analyticsapi.zoho.com` host.

| Attribute | Value |
|-----------|-------|
| **Method** | PUT |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/columns/reorder` |
| **OAuth Scope** | `ZohoAnalytics.modeling.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace, or any user with Design Modify permission on the view. |

### CONFIG Parameters

| Parameter | Type | Mandatory | Max Items | Default | Description |
|-----------|------|-----------|-----------|---------|-------------|
| `columns` | JSONArray of String | **Yes** | 300 | — | Complete, ordered array of column IDs (as strings) representing the new display order. Must include **every** non-system column of the table — omitting even one returns error 8179. Duplicate IDs are silently de-duplicated (only the first occurrence is kept). |

> **All non-system columns required, not a subset.** Unlike Hide/Show Columns, this API requires the full column list on every call. System columns (e.g., `ROWID`, audit columns) are excluded from the required set and cannot be reordered.

### Sample Requests

**Case 1 — Reorder all columns in a 3-column table**

```http
PUT /restapi/v2/workspaces/466206000000071000/views/7617000000508001/columns/reorder HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"columns":["7617000000508027","7617000000508025","7617000000508026"]}
```

**Case 2 — Move the last column of a 4-column table to the first position**

```http
PUT /restapi/v2/workspaces/466206000000071000/views/7617000000508001/columns/reorder HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"columns":["7617000000508028","7617000000508025","7617000000508026","7617000000508027"]}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Reorder Columns returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |
| **Not available on custom domains** | This API is disabled for white label portal contexts. Calls made through a portal domain URL will fail. |
| **Full column set required** | Every non-system column ID in the table must be present in `columns`, or the request fails with error 8179 listing the missing IDs. Partial reordering is not supported. |
| **`columns` array order defines display order** | The position of each ID in the array becomes its new left-to-right display position (1-indexed internally). |
| **`columns` values are strings** | Column IDs must be quoted strings (e.g., `["7617000000508027"]`), not integers. |
| **Duplicate IDs are de-duplicated** | If the same column ID appears more than once, only its first occurrence is used; the array is treated as an ordered set. |
| **Column IDs must belong to the view** | Any column ID not present in the table returns error 8180. |
| **Verify result** | Use Get Table Metadata to confirm the new `columnOrder`/position values after calling this API. |
| **Dependency** | `<view-id>` → Get View List. `columns` array values → Get Table Metadata (use `columnId` strings, excluding system columns). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7301 | User does not have permission. | Ensure the user is a Workspace Admin or has Design Modify permission on the view. |
| 7319 | The view ID does not belong to the specified workspace. | Confirm the `<view-id>` is correct. |
| 8179 | One or more required (non-system) columns are missing from the `columns` array. | Include every non-system column ID of the table in `columns`, not just the ones being moved. |
| 8180 | One or more column IDs in the `columns` array do not belong to this view. | Verify all column IDs using Get Table Metadata. |

---

## Appendix A – Common HTTP Headers

| Header | Value | Required | Notes |
|--------|-------|----------|-------|
| `Authorization` | `Zoho-oauthtoken <oauth-token>` | **Mandatory** | OAuth 2.0 access token of the calling user. |
| `ZANALYTICS-ORGID` | Organisation ID | **Mandatory** for all APIs | Organisation ID of the workspace. |
| `Content-Type` | `application/x-www-form-urlencoded` | Required for POST/PUT/DELETE with body | Not required for Get Column Dependents (GET — no body). |

> **White Label / Client Portal:** [Sort Data by Columns](#7-sort-data-by-columns) and [Reorder Columns](#8-reorder-columns) are **not available** on custom portal domains. All other APIs are available via portal domain URLs when the caller has the required permission.

---

## Appendix B – OAuth Scope Summary

| API | Method | Scope |
|-----|--------|-------|
| Add Column | POST | `ZohoAnalytics.modeling.create` |
| Rename Column | PUT | `ZohoAnalytics.modeling.update` |
| Delete Column | DELETE | `ZohoAnalytics.modeling.delete` |
| Hide Columns | PUT | `ZohoAnalytics.modeling.update` |
| Show Columns | PUT | `ZohoAnalytics.modeling.update` |
| Get Column Dependents | GET | `ZohoAnalytics.metadata.read` |
| Sort Data by Columns | PUT | `ZohoAnalytics.modeling.update` |
| Reorder Columns | PUT | `ZohoAnalytics.modeling.update` |

---

## Appendix C – API-Specific Notes and Behaviours

### Add Column

- **Two modes; single mode returns `columnId`, bulk mode does not.** The presence of a `columns` key in CONFIG switches the API to bulk mode automatically. Use Get Table Metadata after a bulk add to find the new column IDs.
- **Mandatory columns in bulk mode:** If `isMandatory: true` is set on a column entry, the `default` field is required for that entry. Omitting `default` when `isMandatory: true` causes the request to fail.
- **DDL lock:** Check for error 7092 if an import is running. Retry after the import completes.
- **Dependency:** `<view-id>` from Get View List. After bulk add, call Get Table Metadata to retrieve new `columnId` values.

### Rename Column

- **Rename propagates automatically.** All views, formulas, and reports referencing the old column name are updated without manual intervention.
- **Pre-check with Get Column Dependents.** If many views depend on the column, a rename is safe (all references are updated), but it is still good practice to audit dependents before bulk renames.
- **Dependency:** `<column-id>` from Get Table Metadata.

### Delete Column

- **Always call Get Column Dependents first.** Understanding what `views`, `customFormulas`, and `aggregateFormulas` depend on this column determines whether a safe deletion (`deleteDependentViews: false`) or a cascade deletion (`deleteDependentViews: true`) is appropriate.
- **`deleteDependentViews: true` is irreversible.** Once confirmed, all listed dependent objects are permanently destroyed.
- **Dependency:** `<column-id>` from Get Table Metadata. Run Get Column Dependents before deciding on `deleteDependentViews`.

### Hide Columns / Show Columns

- **`columnIds` are strings.** Even though column IDs are numeric, they must be passed as quoted strings inside the JSON array.
- **Idempotent for the unchanged direction.** Hiding an already-hidden column or showing an already-visible column is silently no-oped.
- **One-column minimum for Hide.** Ensure at least one column will remain visible after the hide operation. Show Columns has no such constraint.
- **Dependency:** `columnIds` from Get Table Metadata (use the `columnId` field; filter by `isHidden` field to find current visibility state).

### Get Column Dependents

- **Workspace Admin only.** Unlike other column APIs (which accept DESIGNMODIFY permission), this API requires full Workspace Admin access.
- **Call before any destructive column operation.** Both Delete Column and Rename Column can have downstream effects. This API provides the complete impact list.
- **`views` may contain the same view twice** if the column is referenced in multiple ways in that view (e.g., both as a filter and a display column in a query table).
- **Dependency:** `<column-id>` from Get Table Metadata.

### Sort Data by Columns

- **Not available via portal/custom domain URLs.** Only callable through `analyticsapi.zoho.com`.
- **One sort direction for all columns.** The `sortOrder` value applies uniformly to every column in the `columns` array. Mixed-direction sorting must be done through report or query table configuration, not this API.
- **`resetSort: true` is a complete clear.** After reset, all columns will have `sortedOrder: 0` and `sortedIndex: -1` in Get Table Metadata responses.
- **Dependency:** `columns` (column ID strings) from Get Table Metadata.

### Reorder Columns

- **Not available via portal/custom domain URLs.** Only callable through `analyticsapi.zoho.com`.
- **Full column set is mandatory, every call.** Unlike Hide/Show Columns, this API always requires the complete non-system column list — you cannot reorder just two columns without also listing all the others in their existing positions.
- **De-duplication, not rejection.** Repeated IDs in the array are silently collapsed to their first occurrence rather than causing an error.
- **Dependency:** `columns` (column ID strings) from Get Table Metadata, excluding system columns.

---

## Appendix D – General Response Payload Notes

| Field / Behaviour | Detail |
|-------------------|--------|
| **`columnId` type** | Returned as a quoted string in all responses and required as a string in `columnIds` arrays. |
| **Single vs bulk Add Column responses** | Single mode: `data.columnId` is present. Bulk mode: `data` contains internal schema change information; individual `columnId` values are not returned. |
| **`sortOrder` in Sort Data by Columns** | `1` = Ascending (A→Z, smallest to largest). `2` = Descending (Z→A, largest to smallest). Reflected in `sortedOrder` field in Get Table Metadata responses: `0` = no sort, `1` = ascending, `-1` = descending (note the sign difference). |
| **`isHidden` in Get Table Metadata** | `true` when the column was hidden via Hide Columns. Use Show Columns to reverse. |
| **`viewTypeId` in Get Column Dependents** | `1` = Tabular Report, `2` = Chart, `3` = Pivot Table, `4` = Summary View, `6` = Query Table. |
