# Zoho Analytics V2 REST API — Lookups and Relationships

This document covers the APIs for creating and removing lookup relationships between tables in a Zoho Analytics workspace.

## What is a Lookup?

A **lookup** (also called a **relationship**) links two tables in a workspace through a shared column, analogous to a foreign key constraint in a relational database:

- The **child table** is the table that holds the foreign-key values. Its column is identified by `<column-id>` in the URL.
- The **reference table** (parent table) holds the primary/unique key values. It is identified by `referenceViewId` in CONFIG.
- The **reference column** (`referenceColumnId`) must contain **unique values** in the reference table (acts as the unique key side of the relationship).
- The data type of the child column and the reference column must be **compatible**.

Once a lookup is established, multi-table reports, pivot tables, and query tables can pull data from both the child and reference tables without manual joins. The relationship is visible in the Schema View of the workspace.

> **Tables only:** Lookups can only be created between tables. Reports, charts, pivot tables, query tables, and dashboards cannot be used as the child view or the reference view.

> **Same workspace:** Both the child table and the reference table must belong to the same workspace.

---

## Index

| # | API Name | Method | URL |
|---|----------|--------|-----|
| 1 | [Add Lookup](#1-add-lookup) | POST | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/columns/<column-id>/lookup` |
| 2 | [Remove Lookup](#2-remove-lookup) | DELETE | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/columns/<column-id>/lookup` |

---

## 1. Add Lookup

Creates a lookup relationship from the specified child column to a column in a reference (parent) table. The child column in the URL is the "many" side of the relationship; the `referenceColumnId` in the reference table is the "one" (unique key) side.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/columns/<column-id>/lookup` |
| **OAuth Scope** | `ZohoAnalytics.modeling.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace, or any user with Design Modify permission on the workspace. |

### URL Parameters

| Parameter | Description |
|-----------|-------------|
| `<workspace-id>` | Numeric ID of the workspace that owns both tables. Obtained from Get Workspace Info or Get Workspace List. |
| `<view-id>` | Numeric ID of the **child table** — the table whose column will hold the foreign-key values. Obtained from Get View List. |
| `<column-id>` | Numeric ID of the **child column** in the child table — the column that will store foreign-key values matching the reference column. Obtained from Get Table Metadata. |

### CONFIG Parameters

| Parameter | Type | Mandatory | Description |
|-----------|------|-----------|-------------|
| `referenceViewId` | Long (Integer) | **Yes** | Numeric ID of the **reference (parent) table** — the table that holds the unique key values. This view must be a table in the same workspace. Obtained from Get View List. |
| `referenceColumnId` | Long (Integer) | **Yes** | Numeric ID of the **reference (parent) column** in the reference table — the column with unique values that the child column maps to. Obtained from Get Table Metadata on the reference table. |

### Constraints on the Relationship

The following conditions must be satisfied for a lookup to be created successfully:

| Constraint | Detail |
|------------|--------|
| **Compatible data types** | The child column's data type and the reference column's data type must be compatible. For example, a `PLAIN` (text) child column can reference a `PLAIN` reference column; a `NUMBER` child can reference a `NUMBER` reference. Mixed type lookups (e.g., text → number) are rejected with error 7183. |
| **Reference column must be unique** | The reference column (`referenceColumnId`) must contain only unique values. If duplicate values are detected, error 7509 is returned. Use a primary key column or a column with a uniqueness constraint on the reference table. |
| **Child column must not already be a lookup** | Each child column can only have one lookup relationship. If the child column already has a lookup defined, error 7280 is returned. |
| **No self-referential lookup** | The reference table (`referenceViewId`) cannot be the same as the child table (`<view-id>`). Error 7379 is returned. |
| **No chained (lookup-on-lookup) columns** | The child column cannot itself be a column pulled in via an existing lookup relationship (i.e., it cannot be a derived lookup column). Error 7166 is returned. |
| **No circular relationships** | The relationship must not form a cycle across multiple tables (e.g., A → B → C → A). Error 7184 is returned. |
| **Both views in same workspace** | If `referenceViewId` does not belong to the same workspace as `<view-id>`, error 7319 is returned. |

### Sample Requests

**Case 1 — Link `Order Details.Customer ID` to `Customers.ID`**

In this example, `Order Details` is the child table (many side), and `Customers` is the reference table (one side). The lookup means "each order's Customer ID references a unique Customer ID in the Customers table."

```http
POST /restapi/v2/workspaces/466206000000071000/views/7617000000508001/columns/7617000000508026/lookup HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"referenceViewId":7617000000509100,"referenceColumnId":7617000000509105}
```

**Case 2 — Link `Sales.Product Code` to `Products.Product Code`**

```http
POST /restapi/v2/workspaces/466206000000071000/views/7617000000511002/columns/7617000000511020/lookup HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"referenceViewId":7617000000512000,"referenceColumnId":7617000000512005}
```

**Case 3 — White label portal user creating a lookup**

```http
POST /restapi/v2/workspaces/466206000000071000/views/7617000000508001/columns/7617000000508026/lookup HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.cccccc.dddddd
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"referenceViewId":7617000000509100,"referenceColumnId":7617000000509105}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse; the absence of an error response (4xx/5xx with a `status: "failure"` body) is the sole success indicator.

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON body (see [Error Codes](#error-codes) below).

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Unlike most other modeling APIs in this suite (which return `{"status":"success","summary":"..."}` on HTTP 200), Add Lookup returns a bare HTTP `204 No Content`. Do not attempt to parse a JSON body from a successful response — check only the HTTP status code. |
| **One lookup per child column** | A child column can participate in exactly one lookup relationship. To change the reference target, first call Remove Lookup on the column, then call Add Lookup with the new `referenceViewId` and `referenceColumnId`. |
| **Reference column uniqueness is validated** | Before creating the lookup, the system checks that all current values in `referenceColumnId` are unique. If not, error 7509 is returned. Note: uniqueness is checked at creation time only — the system does not enforce uniqueness for future inserts into the reference table. |
| **Data type compatibility is strict for geo columns** | For `GEO`/`GEO_NUM` typed columns, the geo role level must also match between child and reference column (e.g., both must be the same geographic level: country-to-country, city-to-city). Mismatched geo roles return error 7183. |
| **Auto-number columns cannot be reference columns** | Using an `AUTO_NUMBER` column as the reference side (`referenceColumnId`) is rejected. |
| **Lookup affects dependent views at remove time, not create time** | Adding a lookup has no impact on existing reports. Removing a lookup may break reports that span the two tables. |
| **Schema View reflects the relationship** | After a successful add, the relationship line between the two tables becomes visible in the workspace's Schema View (Relationship View). |
| **Dependency chain** | `<workspace-id>` → Get Workspace Info. `<view-id>` → Get View List (child table). `<column-id>` → Get Table Metadata on the child table. `referenceViewId` → Get View List (reference table). `referenceColumnId` → Get Table Metadata on the reference table. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7107 | The specified child column (`<column-id>`) does not exist in the child table. | Verify `<column-id>` using Get Table Metadata on the child view. |
| 7166 | The child column is itself a lookup-derived column (lookup-on-lookup is not allowed). | Use a regular (base) column of the child table, not a column pulled in from a parent via an existing lookup. |
| 7183 | The child column and the reference column have incompatible data types. | Ensure both columns share a compatible data type (e.g., both `PLAIN`, both `NUMBER`). For GEO columns, the geo role level must also match. |
| 7184 | Adding this lookup would create a circular relationship chain across tables. | Review existing relationships and choose a reference table that does not already reference the child table (directly or transitively). |
| 7280 | A lookup relationship already exists on this child column. | Remove the existing lookup first (using Remove Lookup), then add the new one. |
| 7301 | User does not have permission. | Ensure the user is a Workspace Admin or has Design Modify permission on the workspace. |
| 7319 | The reference table (`referenceViewId`) does not belong to the same workspace as the child table. | Both tables must be in the workspace identified by `<workspace-id>`. |
| 7377 | An identical lookup relationship (same child column → same reference column) is already defined. | No action needed — the relationship already exists. |
| 7379 | The reference table is the same as the child table (self-referential lookup not allowed). | Provide a `referenceViewId` that is different from `<view-id>`. |
| 7509 | The reference column contains duplicate values; it must be unique to serve as the reference side. | Choose a column in the reference table that has unique values, or de-duplicate the reference column's data first. |

---

## 2. Remove Lookup

Removes the existing lookup relationship from the specified child column. Once removed, the child column no longer references the parent table, and multi-table views spanning these two tables may break.

By default, if any reports, charts, pivot tables, or query tables depend on this lookup relationship (i.e., they join the child and parent tables), the removal is blocked. Set `deleteDependentViews` to `true` to cascade-delete those dependent views along with the lookup.

| Attribute | Value |
|-----------|-------|
| **Method** | DELETE |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/columns/<column-id>/lookup` |
| **OAuth Scope** | `ZohoAnalytics.modeling.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace, or any user with Design Modify permission on the workspace. |

### URL Parameters

| Parameter | Description |
|-----------|-------------|
| `<workspace-id>` | Numeric ID of the workspace. |
| `<view-id>` | Numeric ID of the **child table** that owns the lookup column. |
| `<column-id>` | Numeric ID of the **child column** whose lookup relationship is to be removed. |

### CONFIG Parameters

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `deleteDependentViews` | Boolean | No | `false` | If `false`, the removal is blocked with error 7367 if any views (reports, charts, pivot tables, query tables) depend on this lookup. If `true`, all dependent views are permanently deleted along with the lookup. |

### Sample Requests

**Case 1 — Remove a lookup (safe mode — fails if dependents exist)**

```http
DELETE /restapi/v2/workspaces/466206000000071000/views/7617000000508001/columns/7617000000508026/lookup HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={}
```

**Case 2 — Remove a lookup and cascade-delete all dependent views**

```http
DELETE /restapi/v2/workspaces/466206000000071000/views/7617000000508001/columns/7617000000508026/lookup HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"deleteDependentViews":true}
```

**Case 3 — White label portal user removing a lookup**

```http
DELETE /restapi/v2/workspaces/466206000000071000/views/7617000000508001/columns/7617000000508026/lookup HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.cccccc.dddddd
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse; the absence of an error response (4xx/5xx with a `status: "failure"` body) is the sole success indicator.

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON body (see [Error Codes](#error-codes) below).

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Like Add Lookup, Remove Lookup returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. Check only the HTTP status code. |
| **Always check dependents before removing** | Use the [Get Column Dependents](COLUMNS_API_DOC_INFO.md#6-get-column-dependents) API on `<column-id>` to discover which views join on this lookup relationship. This helps decide between `deleteDependentViews: false` (safe check) and `deleteDependentViews: true` (cascade). |
| **`deleteDependentViews: true` is permanent** | All dependent multi-table reports, charts, pivot tables, and query tables that span the child and reference tables via this lookup are permanently deleted. This cannot be undone. |
| **Not idempotent — no lookup means error** | If no lookup is defined on the child column at the time of the call, error 7378 is returned. This API does not silently succeed when there is nothing to remove. |
| **All lookup relationships on the column are removed** | A column can have at most one lookup, but if the internal model has recorded multiple relation IDs for the same column (e.g., due to migrations), all of them are removed in a single atomic transaction. |
| **Schema View update** | After a successful removal, the relationship line between the tables disappears from the workspace's Schema View. |
| **Dependency chain** | `<workspace-id>` → Get Workspace Info. `<view-id>` → Get View List. `<column-id>` → Get Table Metadata. Before removing, call Get Column Dependents to assess impact. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7107 | The specified child column (`<column-id>`) does not exist in the child table. | Verify `<column-id>` using Get Table Metadata. |
| 7301 | User does not have permission. | Ensure the user is a Workspace Admin or has Design Modify permission on the workspace. |
| 7319 | The child table (`<view-id>`) does not belong to the specified workspace. | Confirm `<view-id>` is a table within `<workspace-id>`. |
| 7367 | The lookup is used by one or more dependent views; removal blocked. | Call Get Column Dependents to identify dependent views. Either delete them manually first, or set `deleteDependentViews: true` to cascade-delete them automatically. |
| 7378 | No lookup relationship is defined on this column. | Verify the correct `<column-id>` and `<view-id>`. The lookup may have already been removed. |

---

## Appendix A – Common HTTP Headers

| Header | Value | Required | Notes |
|--------|-------|----------|-------|
| `Authorization` | `Zoho-oauthtoken <oauth-token>` | **Mandatory** | OAuth 2.0 access token of the calling user. |
| `ZANALYTICS-ORGID` | Organisation ID | **Mandatory** for all APIs | Organisation ID of the workspace. |
| `Content-Type` | `application/x-www-form-urlencoded` | Required for POST/DELETE with body | Required when CONFIG is supplied. |

> **White Label / Client Portal:** Both Add Lookup and Remove Lookup are available via portal domain URLs when the caller has the required permission.

---

## Appendix B – OAuth Scope Summary

| API | Method | Scope |
|-----|--------|-------|
| Add Lookup | POST | `ZohoAnalytics.modeling.update` |
| Remove Lookup | DELETE | `ZohoAnalytics.modeling.update` |

---

## Appendix C – API-Specific Notes and Behaviours

### Add Lookup

- **One child column, one relationship.** A column can hold at most one lookup. To re-point a lookup to a different reference column, the existing one must be removed first.
- **Reference column uniqueness is a prerequisite.** Validate that `referenceColumnId` has unique values before calling. If the reference table contains duplicate values in that column, error 7509 is returned and no lookup is created.
- **Data type must be compatible.** Check the data type of the child column (from Get Table Metadata on `<view-id>`) and the reference column (from Get Table Metadata on `referenceViewId`) before calling.
- **Dependency chain for ID resolution:**
  1. Get Workspace Info → `<workspace-id>`
  2. Get View List → `<view-id>` (child table), `referenceViewId` (reference table)
  3. Get Table Metadata on child table → `<column-id>`
  4. Get Table Metadata on reference table → `referenceColumnId`

### Remove Lookup

- **Not idempotent.** Returns error 7378 if no lookup exists — not a silent success.
- **Always audit dependents first.** Use Get Column Dependents on `<column-id>` to discover which views join across this relationship. Only then decide whether to use `deleteDependentViews: true`.
- **`deleteDependentViews: true` is a cascading permanent delete.** All reports, charts, pivot tables, and query tables that are built across the child and reference tables via this lookup are permanently removed. There is no recovery.
- **Dependency chain for ID resolution:**
  1. Get View List → `<view-id>` (child table)
  2. Get Table Metadata → `<column-id>`
  3. Get Column Dependents → audit impact before proceeding

---

## Appendix D – General Response Payload Notes

| Field / Behaviour | Detail |
|-------------------|--------|
| **No data payload on success** | Both Add Lookup and Remove Lookup return HTTP `204 No Content` with **no JSON body at all** — not even a `status`/`summary` string. This differs from most other modeling APIs in this documentation suite that return HTTP 200 with a `{"status":"success","summary":"..."}` body. Only failure responses (4xx/5xx) contain a JSON error payload. No relationship IDs or column metadata are returned on success. |
| **Relationship reflection** | After Add Lookup, the Schema View in the Zoho Analytics UI shows a line between the child and reference tables. After Remove Lookup, this line disappears. |
| **`referenceViewId` and `referenceColumnId` in CONFIG are long integers** | Unlike `columnIds` in Hide/Show Columns (which are strings), these values are passed as unquoted numbers in CONFIG: `{"referenceViewId": 7617000000509100, "referenceColumnId": 7617000000509105}`. |
| **Impact on multi-table reports** | Lookups enable cross-table analysis. Adding a lookup makes it possible to drag columns from both tables into a single report. Removing a lookup breaks any report that currently joins the two tables via that column. |
