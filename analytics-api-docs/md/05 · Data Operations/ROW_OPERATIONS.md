# Zoho Analytics V2 REST API — Rows

This document covers the V2 **Row** REST APIs of Zoho Analytics — the APIs that insert, update, and delete individual rows of data in a table.

## What are the "Row" APIs?

The three Row APIs are the record-level write path into a Zoho Analytics table. They all address the same URL (`/workspaces/<workspace-id>/views/<view-id>/rows`) and differ only by HTTP method:

| Operation | Method | Scope of the change |
|-----------|--------|---------------------|
| [Add Row](#1-add-row) | POST | Inserts exactly **one** row per call. |
| [Update Row](#2-update-row) | PUT | Updates **every row matching `criteria`**, or all rows when `updateAllRows` is `true`. Can insert instead when nothing matches. |
| [Delete Row](#3-delete-row) | DELETE | Deletes **every row matching `criteria`**, or all rows when `deleteAllRows` is `true`. |

They operate strictly on **tables**. A report, dashboard, query table, or any other view type is rejected with `7137`. For loading many rows at once, use the Data Import APIs rather than looping over Add Row.

> Notes that apply to every API in this document:
> - All requests are authenticated via OAuth (`Authorization: Zoho-oauthtoken <token>`). All three use the **`data`** scope family — see [Appendix B](#appendix-b--oauth-scope-summary).
> - All three are **view-scoped** and require the `ZANALYTICS-ORGID` header.
> - `ZohoAnalytics_Server_URI` depends on the data centre (`analyticsapi.zoho.com`, `analyticsapi.zoho.eu`, etc.).
> - All three are **available in Client Portal / White Label contexts**.
> - `CONFIG` is **mandatory** for all three and is sent as a URL-encoded form parameter.
> - `criteria` and all column names/values are treated as sensitive and are excluded from request logging.
> - **All values are exchanged as strings.** Numeric, boolean, and date column values are sent as JSON strings and are echoed back as strings — see [Appendix D](#appendix-d--general-response-payload-notes).

---

## Index

| # | API Name | Method | URL |
|---|----------|--------|-----|
| 1 | [Add Row](#1-add-row) | POST | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/rows` |
| 2 | [Update Row](#2-update-row) | PUT | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/rows` |
| 3 | [Delete Row](#3-delete-row) | DELETE | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/rows` |

---

## Table Preconditions

Before any row operation runs, the target view is checked. These conditions apply to all three APIs unless noted:

| Condition | Applies to | Error |
|-----------|-----------|-------|
| The view must be a **table**, not a report/dashboard/query table | All three | `7137` |
| The table must **not** be a stream table | Add Row, Update Row | `101021` |
| The table must **not** be a snapshot table | All three | `7165` |
| The table must **not** be a system table | Add Row, Update Row | `7164` |
| DML must be allowed on the table | All three | `7405` |
| No batch import may be holding a DDL lock on the table | All three | `7092` |

---

## `criteria` Syntax

`criteria` is a SQL-like filter expression that selects the rows to update or delete. Column names are quoted with double quotes and string literals with single quotes:

```
"Region"='East'
"SalesTable"."Region"='East'
"Sales">1000 and "Region"='West'
```

Notes that matter in practice:

- A column named in `criteria` must exist in the table, otherwise the request fails with `7330`.
- For a **shared user**, the share filter criteria configured for that user is automatically ANDed with whatever `criteria` is sent. A shared user therefore can never update or delete rows outside their own slice of the table, even with a broad criteria.
- `criteria` is not accepted by [Add Row](#1-add-row) — a row insert has nothing to filter.

---

## 1. Add Row

Inserts a single row into a table.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/rows` |
| **OAuth Scope** | `ZohoAnalytics.data.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or the View Owner, or any user with Add Row permission on the view. |

### CONFIG Parameters

CONFIG is **mandatory** for this API.

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `columns` | JSONObject | **Yes** | — | Column name → value map for the new row. Up to **300** columns. Column names are matched **case-insensitively** against the table's display names. Names that do not match any column are not an error — they are returned in `invalidColumns` and the rest of the row is still inserted. At least one name must match, otherwise `8016`. |
| `dateFormat` | String | No | — | Default date pattern applied to **all** date/date-time values in `columns`, e.g. `dd-MMM-yyyy`. Overridden per column by `columnDateFormat`. |
| `columnDateFormat` | JSONObject | No | — | Per-column date pattern overrides — column name → date pattern. 1–300 entries. Takes precedence over `dateFormat` for the columns it names. An unparseable pattern fails with `7512`. |

> Values for lookup (reference) columns must match an existing value in the parent table, otherwise the request fails with `7515`.

### Sample Requests

**Case 1 — Simple row insert**

```http
POST /restapi/v2/workspaces/466206000000071000/views/466206000000081001/rows HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "columns": {
        "Region": "East",
        "Product": "Fruits and Vegetables",
        "Sales": "3928.38"
    }
}
```

**Case 2 — Row insert with a default date format and per-column overrides**

```http
POST /restapi/v2/workspaces/466206000000071000/views/466206000000081001/rows HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "columns": {
        "Region": "East",
        "Sales": "1000",
        "Order Date": "01-Jan-2026",
        "Ship Date": "15/01/2026"
    },
    "dateFormat": "dd-MMM-yyyy",
    "columnDateFormat": {
        "Ship Date": "dd/MM/yyyy"
    }
}
```

**Case 3 — White Label / Client Portal workspace**

```http
POST /restapi/v2/workspaces/466206000000071009/views/466206000000081009/rows HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "columns": {
        "Region": "West",
        "Sales": "2500"
    }
}
```

### Sample Responses

**HTTP 200 OK — Simple insert (Case 1)**

```json
{
    "status": "success",
    "summary": "Add row",
    "data": {
        "addedColumns": {
            "Region": "East",
            "Product": "Fruits and Vegetables",
            "Sales": "3928.38"
        },
        "invalidColumns": {}
    }
}
```

**HTTP 200 OK — Insert where one column name did not match the table**

```json
{
    "status": "success",
    "summary": "Add row",
    "data": {
        "addedColumns": {
            "Region": "East",
            "Sales": "1000"
        },
        "invalidColumns": {
            "Regoin": "East"
        }
    }
}
```

**HTTP 400 Bad Request — The target view is not a table**

```json
{
    "status": "failure",
    "summary": "NOT_A_TABLE",
    "data": {
        "errorCode": 7137,
        "errorMessage": "Sales Overview is not a table."
    }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `status` | String | `"success"` on a successful call, `"failure"` on error. |
| `summary` | String | Localised operation summary. `"Add row"` for this API. |
| `data` | JSONObject | Response payload wrapper. |
| `data.addedColumns` | JSONObject | The column name → value pairs that were actually written, echoed with the casing **as sent** in the request. **All values are strings**, even for numeric, boolean, and date columns. Present for a normal insert. |
| `data.invalidColumns` | JSONObject | The column name → value pairs from the request that did **not** match any column in the table. **Always present**; an empty object `{}` when every name matched. A non-empty value here is not an error — those values were silently skipped and the row was still inserted. |

> The response does not return the ID or row number of the inserted row.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **One row per call** | There is no batch form of this API. To load many rows, use the Data Import APIs — looping Add Row is far slower and consumes one API unit per row. |
| **Unknown columns are skipped, not rejected** | A misspelled column name lands in `invalidColumns` and the insert still succeeds with the remaining columns. Always inspect `invalidColumns`; an empty `{}` is the only confirmation that the whole row was written as intended. |
| **At least one column must match** | If *no* supplied name matches a table column the call fails with `8016`, since there would be nothing to insert. |
| **Column matching is case-insensitive** | `"region"`, `"Region"`, and `"REGION"` all resolve to the same column. The response echoes the casing you sent, not the table's. |
| **Values are strings in both directions** | Send `"Sales": "1000"`, not `"Sales": 1000`, and expect `"1000"` back. |
| **Date parsing precedence** | `columnDateFormat` for that specific column, else `dateFormat`, else the column's own configured format. |
| **Lookup columns are validated** | A value that does not exist in the parent table fails the whole insert with `7515`. |
| **Row-limit and plan checks apply** | The insert is checked against the organization's row allowance before it is written. |
| **No `criteria`** | Insert has nothing to filter; the attribute is not accepted. |
| **Dependency chain** | [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → `<view-id>` → [Get Columns](COLUMNS_API_DOC_INFO.md) (to confirm column names) → Add Row. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7092 | `DDL_LOCK_SINCE_IMPORT_IN_PROGRESS` — A batch import is holding a lock on this table. | Retry once the import has finished. |
| 7104 | `META_OBJECT_NOT_PRESENT` — The view does not exist. | Verify `<view-id>`. |
| 7137 | `NOT_A_TABLE` — The target view is not a table. | Target a table; reports, dashboards, and query tables cannot accept rows. |
| 7164 | `SYSTEM_TABLE_DATA_MOD` — System table data cannot be modified. | System tables are managed by Zoho Analytics. Target a user-created table instead. |
| 7165 | `SNAPSHOT_TABLE_DATAMOD` — Snapshot table data cannot be modified. | Target a non-snapshot table. |
| 7301 | `SECURITY_NOT_PERMITTED` — The user cannot add rows to this view. | Ensure the user is an Account Admin, Organization Admin, Workspace Admin, View Owner, or has Add Row permission on the view. |
| 7405 | `DML_NOT_ALLOWED` — Row modification is not allowed for this table. | Use a table that permits DML. |
| 7512 | `INVALID_DATE_FORMAT` — A pattern in `dateFormat` / `columnDateFormat` could not be parsed. | Supply a valid date pattern such as `dd-MMM-yyyy`. |
| 7515 | `UNKNOWN_LOOKUP_VALUE` — A value for a lookup column does not exist in the parent table. | Add the value to the parent table first, or send an existing one. |
| 8016 | `API_NO_COLUMN_PRESENT` — None of the supplied column names matched a column in the table. | Check the names via [Get Columns](COLUMNS_API_DOC_INFO.md). |
| 8504 | `LESS_THAN_MIN_OCCURANCE` — `CONFIG` was not sent, or `columns` is missing. | Send a CONFIG object containing `columns`. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.data.create`. |
| 101021 | `NOT_A_STREAM_TABLE` — Row operations are not supported on a stream table. | Target a non-stream table. |

---

## 2. Update Row

Updates the rows of a table that match a filter, or every row. Can optionally insert a row when nothing matches.

| Attribute | Value |
|-----------|-------|
| **Method** | PUT |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/rows` |
| **OAuth Scope** | `ZohoAnalytics.data.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or the View Owner, or any user with Update Row permission on the view. When `addIfNotExist` triggers an insert, **Add Row permission is additionally required**. |

### CONFIG Parameters

CONFIG is **mandatory** for this API. Exactly one of `criteria` or `updateAllRows` must be supplied.

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `columns` | JSONObject | **Yes** | — | Column name → new value map. Up to **300** columns. Matched case-insensitively; unmatched names are returned in `invalidColumns` rather than rejected. |
| `criteria` | String | Conditional* | — | Filter selecting the rows to update. See [`criteria` Syntax](#criteria-syntax). |
| `updateAllRows` | Boolean | Conditional* | `false` | When `true`, every row in the table is updated. |
| `addIfNotExist` | Boolean | No | `false` | When `true` and **no row matches `criteria`**, a new row is inserted from `columns` instead. Requires Add Row permission. Has no effect when rows do match. |
| `dateFormat` | String | No | — | Default date pattern for all date/date-time values in `columns`. |
| `columnDateFormat` | JSONObject | No | — | Per-column date pattern overrides. 1–300 entries. Takes precedence over `dateFormat`. |

\* **Exactly one** of `criteria` or `updateAllRows: true` must be sent. Supplying both, or neither, fails with `8130` `INVALID_UPDATE_CRITERIA_CONFIGURATION`.

### Sample Requests

**Case 1 — `criteria` only: update the rows of one region**

```http
PUT /restapi/v2/workspaces/466206000000071000/views/466206000000081001/rows HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "columns": {
        "Region": "East_1"
    },
    "criteria": "\"Region\"='East'"
}
```

**Case 2 — Update every row in the table**

```http
PUT /restapi/v2/workspaces/466206000000071000/views/466206000000081001/rows HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "columns": {
        "Status": "Processed"
    },
    "updateAllRows": true
}
```

**Case 3 — Update-or-insert with date handling clubbed together**

```http
PUT /restapi/v2/workspaces/466206000000071000/views/466206000000081001/rows HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "columns": {
        "Region": "North",
        "Sales": "2100",
        "Order Date": "01-Jan-2026"
    },
    "criteria": "\"Region\"='North'",
    "addIfNotExist": true,
    "dateFormat": "dd-MMM-yyyy"
}
```

**Case 4 — White Label / Client Portal workspace**

```http
PUT /restapi/v2/workspaces/466206000000071009/views/466206000000081009/rows HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "columns": {
        "Status": "Reviewed"
    },
    "criteria": "\"Region\"='West'"
}
```

### Sample Responses

**HTTP 200 OK — Rows matched and were updated (Cases 1, 2 and 4)**

```json
{
    "status": "success",
    "summary": "Update row",
    "data": {
        "updatedColumns": {
            "Region": "East_1"
        },
        "updatedRows": 27,
        "invalidColumns": {}
    }
}
```

**HTTP 200 OK — Nothing matched the criteria (no rows changed)**

```json
{
    "status": "success",
    "summary": "Update row",
    "data": {
        "updatedColumns": {
            "Region": "East_1"
        },
        "updatedRows": 0,
        "invalidColumns": {}
    }
}
```

**HTTP 200 OK — `addIfNotExist` inserted a row because nothing matched (Case 3)**

```json
{
    "status": "success",
    "summary": "Update row",
    "data": {
        "newRowAdded": true,
        "updatedColumns": {
            "Region": "North",
            "Sales": "2100",
            "Order Date": "01-Jan-2026"
        },
        "updatedRows": 0,
        "invalidColumns": {}
    }
}
```

**HTTP 400 Bad Request — Both `criteria` and `updateAllRows` sent (or neither)**

```json
{
    "status": "failure",
    "summary": "INVALID_UPDATE_CRITERIA_CONFIGURATION",
    "data": {
        "errorCode": 8130,
        "errorMessage": "Invalid criteria configuration for updating data."
    }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `status` | String | `"success"` on a successful call, `"failure"` on error. |
| `summary` | String | Localised operation summary. `"Update row"` for this API — the same string whether rows were updated or a row was inserted via `addIfNotExist`. |
| `data` | JSONObject | Response payload wrapper. |
| `data.updatedColumns` | JSONObject | The column name → value pairs that were applied, echoed with the casing as sent. **All values are strings.** |
| `data.updatedRows` | Number | How many existing rows were changed. **`0` is a normal success**, meaning the criteria matched nothing. It is also `0` when `addIfNotExist` inserted a row instead. |
| `data.newRowAdded` | Boolean | **Present only** when `addIfNotExist` caused an insert, in which case it is `true`. Absent on a normal update — test for key presence, not for a `false` value. |
| `data.invalidColumns` | JSONObject | Column name → value pairs that matched no column in the table. Always present; `{}` when everything matched. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **`criteria` and `updateAllRows` are mutually exclusive and jointly required** | Sending both, or neither, fails with `8130`. There is no implicit "update everything" default — omitting `criteria` does not update all rows, it errors. |
| **`updatedRows: 0` is a success, not a failure** | A criteria that matches nothing returns HTTP 200. Check `updatedRows` rather than relying on the status code to detect a no-op. |
| **`addIfNotExist` converts the call into an insert** | When it fires, the response switches shape: `newRowAdded: true` appears, the applied values come back under `updatedColumns` (not `addedColumns`), and `updatedRows` stays `0`. The caller needs Add Row permission as well as Update Row. |
| **The insert path is a plain insert** | `addIfNotExist` does not merge into a partially matching row — it writes exactly the `columns` supplied, so any column not listed takes its default or stays empty. |
| **Shared users are silently constrained** | Their share filter criteria is ANDed with the supplied `criteria`, so `updatedRows` may be lower than expected without any error being raised. |
| **Unknown columns are skipped, not rejected** | Same behaviour as Add Row — inspect `invalidColumns`. |
| **Values are strings in both directions** | Send `"Sales": "2000"` and expect `"2000"` back. |
| **Concurrency guard** | If another row-write request is still being processed for the same table, the call fails with `8062`. Retry after a short delay. |
| **Dependency chain** | [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → `<view-id>` → [Get Columns](COLUMNS_API_DOC_INFO.md) (for `criteria` and `columns` names) → Update Row. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7092 | `DDL_LOCK_SINCE_IMPORT_IN_PROGRESS` — A batch import is holding a lock on this table. | Retry once the import has finished. |
| 7104 | `META_OBJECT_NOT_PRESENT` — The view does not exist. | Verify `<view-id>`. |
| 7137 | `NOT_A_TABLE` — The target view is not a table. | Target a table. |
| 7164 | `SYSTEM_TABLE_DATA_MOD` — System table data cannot be modified. | Target a user-created table instead. |
| 7165 | `SNAPSHOT_TABLE_DATAMOD` — Snapshot table data cannot be modified. | Target a non-snapshot table. |
| 7301 | `SECURITY_NOT_PERMITTED` — The user cannot update rows in this view, or lacks Add Row permission when `addIfNotExist` fires. | Ensure the user has Update Row permission — and Add Row permission too if `addIfNotExist` is used. |
| 7330 | `UNKNOWN_COLUMN_IN_FILTERCRITERIA` — A column referenced in `criteria` does not exist in the table. | Verify the column names in `criteria` via [Get Columns](COLUMNS_API_DOC_INFO.md). |
| 7405 | `DML_NOT_ALLOWED` — Row modification is not allowed for this table. | Use a table that permits DML. |
| 7512 | `INVALID_DATE_FORMAT` — A pattern in `dateFormat` / `columnDateFormat` could not be parsed. | Supply a valid date pattern. |
| 7515 | `UNKNOWN_LOOKUP_VALUE` — A value for a lookup column does not exist in the parent table. | Send an existing lookup value. |
| 8016 | `API_NO_COLUMN_PRESENT` — None of the supplied column names matched a column in the table. | Check the names via [Get Columns](COLUMNS_API_DOC_INFO.md). |
| 8062 | `ADD_ROW_REQUEST_STILL_IN_PROGRESS` — Another row-write request for this table is still being processed. | Retry after the in-flight request completes. |
| 8130 | `INVALID_UPDATE_CRITERIA_CONFIGURATION` — Both `criteria` and `updateAllRows` were sent, or neither was. | Send exactly one of the two. |
| 8504 | `LESS_THAN_MIN_OCCURANCE` — `CONFIG` was not sent, or `columns` is missing. | Send a CONFIG object containing `columns`. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.data.update`. |
| 101021 | `NOT_A_STREAM_TABLE` — Row operations are not supported on a stream table. | Target a non-stream table. |

---

## 3. Delete Row

Deletes the rows of a table that match a filter, or every row.

| Attribute | Value |
|-----------|-------|
| **Method** | DELETE |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/rows` |
| **OAuth Scope** | `ZohoAnalytics.data.delete` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or the View Owner, or any user with **Delete All Rows** permission on the view. |

> **Note on the permission.** This API is gated on the **Delete All Rows** permission, not the row-level Delete Row permission — and that holds even when `criteria` targets a single row. A user granted only Delete Row on a shared view cannot call this API and receives `7301`.

### CONFIG Parameters

CONFIG is **mandatory** for this API. Exactly one of `criteria` or `deleteAllRows` must be supplied.

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `criteria` | String | Conditional* | — | Filter selecting the rows to delete. See [`criteria` Syntax](#criteria-syntax). |
| `deleteAllRows` | Boolean | Conditional* | `false` | When `true`, every row in the table is deleted. |

\* **Exactly one** of `criteria` or `deleteAllRows: true` must be sent. Supplying both, or neither, fails with `8131` `INVALID_DELETE_CRITERIA_CONFIGURATION`.

### Sample Requests

**Case 1 — `criteria` only: delete the rows of one region**

```http
DELETE /restapi/v2/workspaces/466206000000071000/views/466206000000081001/rows HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "criteria": "\"Region\"='West'"
}
```

**Case 2 — Delete every row in the table**

```http
DELETE /restapi/v2/workspaces/466206000000071000/views/466206000000081001/rows HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "deleteAllRows": true
}
```

**Case 3 — White Label / Client Portal workspace**

```http
DELETE /restapi/v2/workspaces/466206000000071009/views/466206000000081009/rows HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "criteria": "\"Status\"='Closed'"
}
```

### Sample Responses

**HTTP 200 OK — Rows matched and were deleted (Cases 1 and 3)**

```json
{
    "status": "success",
    "summary": "Delete row",
    "data": {
        "deletedRows": 27
    }
}
```

**HTTP 200 OK — Nothing matched the criteria**

```json
{
    "status": "success",
    "summary": "Delete row",
    "data": {
        "deletedRows": 0
    }
}
```

**HTTP 400 Bad Request — Both `criteria` and `deleteAllRows` sent (or neither)**

```json
{
    "status": "failure",
    "summary": "INVALID_DELETE_CRITERIA_CONFIGURATION",
    "data": {
        "errorCode": 8131,
        "errorMessage": "Invalid criteria configuration for deleting data."
    }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `status` | String | `"success"` on a successful call, `"failure"` on error. |
| `summary` | String | Localised operation summary. `"Delete row"` for this API. |
| `data` | JSONObject | Response payload wrapper. |
| `data.deletedRows` | Number | How many rows were deleted. **`0` is a normal success**, meaning the criteria matched nothing. This is the only field returned — there is no `invalidColumns` counterpart, because delete takes no `columns`. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Gated on Delete All Rows permission** | Even a single-row delete requires the Delete All Rows permission. This is the one place where the Row APIs' permission does not match the operation's name. |
| **`criteria` and `deleteAllRows` are mutually exclusive and jointly required** | Sending both, or neither, fails with `8131`. Omitting `criteria` does not delete everything — it errors. |
| **`deletedRows: 0` is a success, not a failure** | A criteria matching nothing returns HTTP 200. Check the count rather than the status code. |
| **Irreversible** | Deleted rows are not recoverable through the API; there is no row-level trash. `deleteAllRows: true` empties the table in one call. |
| **The table itself survives** | Only rows are removed — the table, its columns, its formulas, and everything built on it remain. To remove the table, use [Delete View](VIEW_OPERATIONS_API_DOC_INFO.md#5-delete-view). |
| **Shared users are silently constrained** | Their share filter criteria is ANDed with the supplied `criteria`, so a shared user calling `deleteAllRows: true` deletes only the rows within their own filtered slice. |
| **No stream-table restriction** | Unlike Add Row and Update Row, delete does not run the stream-table check, so `101021` does not apply here. |
| **Concurrency guard** | If another row-write request is still being processed for the same table, the call fails with `8062`. |
| **Dependency chain** | [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → `<view-id>` → [Get Columns](COLUMNS_API_DOC_INFO.md) (for `criteria` names) → Delete Row. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7092 | `DDL_LOCK_SINCE_IMPORT_IN_PROGRESS` — A batch import is holding a lock on this table. | Retry once the import has finished. |
| 7104 | `META_OBJECT_NOT_PRESENT` — The view does not exist. | Verify `<view-id>`. |
| 7137 | `NOT_A_TABLE` — The target view is not a table. | Target a table. |
| 7164 | `SYSTEM_TABLE_DATA_MOD` — System table data cannot be modified. | Target a user-created table instead. |
| 7165 | `SNAPSHOT_TABLE_DATAMOD` — Snapshot table data cannot be modified. | Target a non-snapshot table. |
| 7301 | `SECURITY_NOT_PERMITTED` — The user cannot delete rows from this view. | Ensure the user is an Account Admin, Organization Admin, Workspace Admin, View Owner, or has **Delete All Rows** permission on the view. |
| 7330 | `UNKNOWN_COLUMN_IN_FILTERCRITERIA` — A column referenced in `criteria` does not exist in the table. | Verify the column names in `criteria` via [Get Columns](COLUMNS_API_DOC_INFO.md). |
| 7405 | `DML_NOT_ALLOWED` — Row modification is not allowed for this table. | Use a table that permits DML. |
| 8062 | `ADD_ROW_REQUEST_STILL_IN_PROGRESS` — Another row-write request for this table is still being processed. | Retry after the in-flight request completes. |
| 8131 | `INVALID_DELETE_CRITERIA_CONFIGURATION` — Both `criteria` and `deleteAllRows` were sent, or neither was. | Send exactly one of the two. |
| 8504 | `LESS_THAN_MIN_OCCURANCE` — `CONFIG` was not sent. | Send a CONFIG object containing `criteria` or `deleteAllRows`. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.data.delete`. |

---

## Appendix A – Common HTTP Headers

| Header | Value | Required | Description |
|--------|-------|----------|-------------|
| `Authorization` | `Zoho-oauthtoken <oauth-token>` | **Mandatory** | OAuth 2.0 access token of the calling user. Must carry the scope matching the operation (see [Appendix B](#appendix-b--oauth-scope-summary)). |
| `ZANALYTICS-ORGID` | Organization ID string | **Mandatory** | Organization ID of the workspace that owns the view. Obtainable from the [Get Organizations](ORG_INFO_API_DOC_INFO.md) response or from listing API responses as the `orgId` field. |
| `Content-Type` | `application/x-www-form-urlencoded` | **Mandatory** | All three APIs send `CONFIG` as a URL-encoded form parameter — including `DELETE`, which carries a body here. |

> **`ZANALYTICS-DEST-ORGID` is not used by any API in this document.** That header applies only to cross-organization copy operations (Copy Workspace, [Copy Views](VIEW_OPERATIONS_API_DOC_INFO.md#2-copy-views), Copy Formulas).

Example (Add Row):

```http
POST /restapi/v2/workspaces/466206000000071000/views/466206000000081001/rows HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG=%7B%22columns%22%3A%7B%22Region%22%3A%22East%22%2C%22Sales%22%3A%221000%22%7D%7D
```

---

## Appendix B – OAuth Scope Summary

| API | HTTP Method | Scope |
|-----|-------------|-------|
| Add Row | POST | `ZohoAnalytics.data.create` |
| Update Row | PUT | `ZohoAnalytics.data.update` |
| Delete Row | DELETE | `ZohoAnalytics.data.delete` |

> The three operations use **three different scopes** within the `data` family. A token scoped only to `ZohoAnalytics.data.create` can insert rows but cannot update or delete them. Note also that an [Update Row](#2-update-row) call using `addIfNotExist` performs an insert while still requiring only `ZohoAnalytics.data.update` — the scope follows the HTTP method, whereas the *permission* check follows the operation actually performed.

---

## Appendix C – API-Specific Notes and Behaviours

### Add Row

- **Single-row only, and that is its main limitation.** There is no batch variant, so bulk loading through this API means one HTTP call and one API unit per row. Use the Data Import APIs for anything beyond a handful of rows.
- **Unknown column names fail silently by design.** They are collected into `invalidColumns` and the row is still inserted from whatever did match. A caller that ignores `invalidColumns` can write partial rows for a long time without noticing — always assert it is `{}`.
- **The floor is one matching column.** Only when *nothing* matches does the call fail (`8016`).
- **Case-insensitive in, as-sent out.** Matching ignores case, but `addedColumns` echoes the casing you supplied rather than the table's, so it cannot be used to discover canonical column names.
- **Date handling has a three-level precedence**: `columnDateFormat` for that column, then `dateFormat`, then the column's own configured format.
- **It is the only Row API with no `criteria`**, and correspondingly the only one that cannot be constrained by a shared user's share filter.
- **Dependency chain:** [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → [Get Columns](COLUMNS_API_DOC_INFO.md) → Add Row.

### Update Row

- **Two mutually exclusive selectors, one of which is mandatory.** `criteria` and `updateAllRows` cannot be combined, and omitting both is an error rather than a default — the API deliberately refuses to guess between "one row" and "every row".
- **`addIfNotExist` changes both the permission requirement and the response shape.** It needs Add Row permission on top of Update Row, and on firing it returns `newRowAdded: true` with the values under `updatedColumns` and `updatedRows: 0`. Code that keys off `addedColumns` will miss the insert entirely.
- **The upsert inserts, it does not merge.** Only the columns present in `columns` are written; there is no partially-matched row to fill in the rest.
- **`updatedRows: 0` is ambiguous on its own.** It means either "criteria matched nothing" or "a row was inserted instead" — distinguish them by the presence of `newRowAdded`.
- **Shared users see silently reduced effects**, because their share filter criteria is ANDed with the criteria they send.
- **Dependency chain:** [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → [Get Columns](COLUMNS_API_DOC_INFO.md) → Update Row.

### Delete Row

- **Its permission does not match its name.** The API validates **Delete All Rows**, not Delete Row, regardless of how narrow the `criteria` is. This is the single most surprising behaviour in the family and the most common cause of an unexpected `7301` for a shared user who was granted row-level delete.
- **Two mutually exclusive selectors, one mandatory** — same contract as Update Row, with its own error code (`8131`).
- **Irreversible and potentially total.** `deleteAllRows: true` empties the table in one call with no confirmation step and no row-level trash.
- **It skips the stream-table check** that Add Row and Update Row perform, so `101021` is the one precondition error that cannot occur here.
- **Shared users cannot over-delete.** Even `deleteAllRows: true` is confined to their share filter criteria, so the same request removes different amounts of data depending on who calls it.
- **The narrowest response in the family** — `deletedRows` and nothing else.
- **Dependency chain:** [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → [Get Columns](COLUMNS_API_DOC_INFO.md) → Delete Row.

---

## Appendix D – General Response Payload Notes

| Field / Behaviour | Detail |
|-------------------|--------|
| **All three APIs return HTTP 200 with a body** | Unusually for the V2 suite, none of the Row APIs returns 204 — even `DELETE` responds with `{"status", "summary", "data"}` carrying a row count. |
| **Failure responses share one shape** | `{"status": "failure", "summary": "<ERROR_NAME>", "data": {"errorCode": <n>, "errorMessage": "<text>"}}`. `summary` on failure is the error's symbolic name (e.g. `NOT_A_TABLE`), not a localised sentence. |
| **Column values are strings in both directions** | Send `"Sales": "1000"`, not `1000`; numeric, boolean, and date columns all come back as strings (`"3"`, `"true"`, `"01-Jan-2026"`). Convert on your side. |
| **Row counts are native numbers** | `updatedRows` and `deletedRows` are genuine JSON numbers, in contrast to the string-typed column values around them. |
| **A count of `0` is a success** | Both `updatedRows: 0` and `deletedRows: 0` are returned with HTTP 200 when the criteria matched nothing. Never infer failure from the status code alone. |
| **`invalidColumns` is always present on Add and Update** | Empty `{}` when every supplied name matched. It is never returned by Delete Row, which takes no `columns`. |
| **`newRowAdded` is conditionally present** | It appears only on an [Update Row](#2-update-row) call where `addIfNotExist` triggered an insert, and is then always `true`. Test for the key, not for a `false` value. |
| **Response field names differ per operation** | Insert returns `addedColumns`; update returns `updatedColumns` + `updatedRows`; an `addIfNotExist` insert returns `updatedColumns` + `updatedRows: 0` + `newRowAdded`; delete returns `deletedRows`. There is no single common data shape across the three. |
| **No row identifiers are returned** | None of the three responses includes a row ID, primary key, or row number — only the values applied and the counts affected. |
