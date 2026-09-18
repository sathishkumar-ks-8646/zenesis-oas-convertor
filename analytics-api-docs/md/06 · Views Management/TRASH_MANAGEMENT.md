# Trash View APIs – Documentation

This document describes the V2 **Trash View** REST APIs of Zoho Analytics — listing trashed views, restoring them to active state, and permanently deleting them from trash.

> Notes that apply to every API in this document:
> - All requests are authenticated via OAuth (`Authorization: Zoho-oauthtoken <token>`).
> - All three APIs are **workspace-scoped** and require the `ZANALYTICS-ORGID` header.
> - `ZohoAnalytics_Server_URI` depends on the data center (`analyticsapi.zoho.com`, `.eu`, etc.).

---

## Index

| # | API Name | Method | URL |
|---|----------|--------|-----|
| 1 | Get Trash Views | GET | `/restapi/v2/workspaces/<workspace-id>/trash` |
| 2 | Restore Trash View | POST | `/restapi/v2/workspaces/<workspace-id>/trash/<view-id>` |
| 3 | Delete Trash View | DELETE | `/restapi/v2/workspaces/<workspace-id>/trash/<view-id>` |

---

## 1. Get Trash Views

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/trash` |
| **OAuth Scope** | `ZohoAnalytics.metadata.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** |
| **Permission Required** | The authenticated user must be an **Account Admin** or **Organization Admin**, or a **Workspace Admin**, or a **Shared User**, or a **Group Member**, or any user with **Read** permission on the workspace. |

> This API has no `CONFIG` parameter. All inputs are provided via URL path parameters.

### Sample Requests

**Case 1 — List all trashed views in a workspace**

```http
GET /restapi/v2/workspaces/7617000032567001/trash HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Shared user calling the endpoint (returns only views they own)**

```http
GET /restapi/v2/workspaces/7617000032567001/trash HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.aaaaaa.bbbbbb
ZANALYTICS-ORGID: 700000123456
```

### Sample Responses

**Case 1 — Empty trash (no trashed views)**

```json
{
  "status": "success",
  "summary": "get trash view list",
  "data": {
    "views": []
  }
}
```

**Case 2 — Single trashed table (Account Admin view)**

```json
{
  "status": "success",
  "summary": "get trash view list",
  "data": {
    "views": [
      {
        "viewId": "7617000032567618",
        "viewName": "T1_001",
        "viewType": "Table",
        "deletedTime": "1682432425367",
        "deletedBy": "admin@example.com"
      }
    ]
  }
}
```

**Case 3 — Multiple trashed views of different types**

```json
{
  "status": "success",
  "summary": "get trash view list",
  "data": {
    "views": [
      {
        "viewId": "7617000032567465",
        "viewName": "Sales",
        "viewType": "Table",
        "deletedTime": "1682432425829",
        "deletedBy": "admin@example.com"
      },
      {
        "viewId": "7617000032567466",
        "viewName": "Region_vs_sales",
        "viewType": "AnalysisView",
        "deletedTime": "1682432425829",
        "deletedBy": "admin@example.com"
      },
      {
        "viewId": "7617000032567467",
        "viewName": "product_Vs_sales",
        "viewType": "AnalysisView",
        "deletedTime": "1682432425829",
        "deletedBy": "admin@example.com"
      },
      {
        "viewId": "7617000032567597",
        "viewName": "ANV_014",
        "viewType": "Pivot",
        "deletedTime": "1682432426258",
        "deletedBy": "orgadmin@example.com"
      }
    ]
  }
}
```

**Case 4 — Shared user: returns empty (shared users only see views they owned)**

```json
{
  "status": "success",
  "summary": "get trash view list",
  "data": {
    "views": []
  }
}
```

**Case 5 — Trash list including a dashboard tab (`DashTab` type)**

Dashboard tabs have additional fields: `tabParentId`, `tabParentName`, `tabPosition`. These fields are present **only** for views with `viewType: "DashTab"`.

```json
{
  "status": "success",
  "summary": "get trash view list",
  "data": {
    "views": [
      {
        "viewId": "7617000032567701",
        "viewName": "Q1 Summary",
        "viewType": "DashTab",
        "deletedTime": "1682432427100",
        "deletedBy": "admin@example.com",
        "tabParentId": "7617000032567700",
        "tabParentName": "Annual Report Dashboard",
        "tabPosition": 2
      }
    ]
  }
}
```

**Case 6 — List with a `isDisabled` flag (live connect view on unsupported plan)**

When a trashed view is a Live Connect report and the current plan does not support restoring it, the view appears in the list with `isDisabled: true`. Attempting to restore it will fail.

```json
{
  "status": "success",
  "summary": "get trash view list",
  "data": {
    "views": [
      {
        "viewId": "7617000032567800",
        "viewName": "Live_Sales_Report",
        "viewType": "AnalysisView",
        "deletedTime": "1682432428000",
        "deletedBy": "admin@example.com",
        "isDisabled": true
      }
    ]
  }
}
```

### Response Field Reference

| Field | Type | Always Present | Description |
|-------|------|----------------|-------------|
| `viewId` | String | Yes | ID of the trashed view, as a string. |
| `viewName` | String | Yes | Display name of the view at the time it was deleted. |
| `viewType` | String | Yes | Type of the view. See **View Type Values** below. |
| `deletedTime` | String | Yes | Epoch timestamp in **milliseconds** when the view was deleted. |
| `deletedBy` | String | Yes | Email address of the user who deleted the view. |
| `isDisabled` | Boolean | Only when `true` | Present and `true` when the view cannot be restored due to plan limitations (e.g., Live Connect views on a non-supporting plan). |
| `tabParentId` | String | Only for `DashTab` | ID of the parent tabbed dashboard this tab belongs to. |
| `tabParentName` | String | Only for `DashTab` | Display name of the parent tabbed dashboard. |
| `tabPosition` | Integer | Only for `DashTab` | Position index of this tab within the parent dashboard. |

**View Type Values:**

| `viewType` | Description |
|------------|-------------|
| `Table` | Data table (base table or imported data). |
| `AnalysisView` | Chart/analysis view (bar, line, pie, etc.). |
| `Pivot` | Pivot table view. |
| `Summary` | Summary view. |
| `QueryTable` | Query table / custom formula table. |
| `Dashboard` | Dashboard view. |
| `DashTab` | A tab within a tabbed dashboard. Includes `tabParentId`, `tabParentName`, `tabPosition`. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify the `<workspace-id>` in the URL. |
| 7301 | User does not have permission to list trash views. | Ensure the user has at least Read permission on the workspace. |
| 8535 | Invalid OAuth token. | Provide a valid, non-expired token with scope `ZohoAnalytics.metadata.read`. |

---

## 2. Restore Trash View

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/trash/<view-id>` |
| **OAuth Scope** | `ZohoAnalytics.modeling.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** |
| **Permission Required** | The authenticated user must be an **Account Admin** or **Organization Admin**, or a **Workspace Admin**, or the **View Owner** (the user who owned the view before it was trashed). |

### CONFIG Parameter

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `withDependents` | Boolean | No | `false` | When `true`, the view is restored together with all its **parent dependent objects** (tables, columns, formulas, relations, data connectors) that are also in trash and required for the view to function. When `false`, if any required parent objects are also in trash, the restore fails with error `7941`. See **Appendix D** for full details. |

### Sample Requests

**Case 1 — Restore a standalone table (no dependencies)**

```http
POST /restapi/v2/workspaces/7617000032567001/trash/7617000032567618 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Restore an analysis view that depends on a trashed parent table**

If `Sales` table is also in trash, the view `Region_vs_sales` (which is based on `Sales`) cannot be restored alone. Use `withDependents=true`:

```http
POST /restapi/v2/workspaces/7617000032567001/trash/7617000032567466 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"withDependents":true}
```

**Case 3 — Restore with explicit `withDependents=false` (safe for independent views)**

```http
POST /restapi/v2/workspaces/7617000032567001/trash/7617000032567597 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"withDependents":false}
```

### Sample Response

**HTTP 204 No Content** — Restore operations return no response body on success.

```
HTTP/1.1 204 No Content
```

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7082 | An unexpected error occurred during the trash restore operation. | Retry the request. If the error persists, contact support. |
| 7103 | Workspace not found. | Verify the `<workspace-id>` in the URL. |
| 7301 | User does not have permission to restore this view from trash. | Ensure the user is a Workspace Admin, Account Admin, Organization Admin, or the original owner of the trashed view. |
| 7929 | The view has already been restored from trash. | The view is no longer in trash. No action needed. |
| 7941 | The view has parent dependencies that are also in trash and must be restored together. | Retry with `"withDependents": true` in the CONFIG. See **Appendix D** for details. |
| 7943 | The requesting user does not have permission to restore this specific trashed view. | Only the view's original owner or an admin can restore it. |
| 8535 | Invalid OAuth token. | Provide a valid, non-expired token with scope `ZohoAnalytics.modeling.create`. |

---

## 3. Delete Trash View

| Attribute | Value |
|-----------|-------|
| **Method** | DELETE |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/trash/<view-id>` |
| **OAuth Scope** | `ZohoAnalytics.modeling.delete` |
| **ZANALYTICS-ORGID Header** | **Mandatory** |
| **Permission Required** | The authenticated user must be an **Account Admin** or **Organization Admin**, or a **Workspace Admin**, or the **View Owner** (the user who owned the view before it was trashed). |

> ⚠️ **This operation is permanent and irreversible.** Once a view is deleted from trash, it cannot be recovered. Ensure you mean to permanently delete the view and not restore it.

### CONFIG Parameter

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `withDependents` | Boolean | No | `false` | When `true`, the view and all its **child dependent views** that are also in trash are permanently deleted together. When `false`, if any child dependent views exist in trash, the delete fails with error `7942`. See **Appendix D** for full details. |

### Sample Requests

**Case 1 — Permanently delete a standalone analysis view (no children in trash)**

```http
DELETE /restapi/v2/workspaces/7617000032567001/trash/7617000032567466 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Permanently delete a table and all its dependent child views**

If `Sales` table has dependent analysis views (`Region_vs_sales`, `product_Vs_sales`) also in trash, use `withDependents=true` to delete all of them permanently:

```http
DELETE /restapi/v2/workspaces/7617000032567001/trash/7617000032567465 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"withDependents":true}
```

**Case 3 — Attempt to delete a parent table without `withDependents` (will fail)**

```http
DELETE /restapi/v2/workspaces/7617000032567001/trash/7617000032567465 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

This returns error `7942` because `Region_vs_sales` and `product_Vs_sales` are children of `Sales` and are also in trash. Pass `CONFIG={"withDependents":true}` to force-delete.

### Sample Response

**HTTP 204 No Content** — Delete operations return no response body on success.

```
HTTP/1.1 204 No Content
```

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7082 | An unexpected error occurred during the permanent delete operation. | Retry the request. If it persists, contact support. |
| 7103 | Workspace not found. | Verify the `<workspace-id>` in the URL. |
| 7301 | User does not have permission to delete this view from trash. | Ensure the user is a Workspace Admin, Account Admin, Organization Admin, or the original view owner. |
| 7929 | The view has already been restored from trash and is no longer in the trash bin. | The view is active again — it cannot be deleted from trash. |
| 7942 | The view has child dependent views in trash that must be deleted together. | Retry with `"withDependents": true` in the CONFIG. See **Appendix D** for details. |
| 8535 | Invalid OAuth token. | Provide a valid, non-expired token with scope `ZohoAnalytics.modeling.delete`. |

---

## Appendix A – Common HTTP Headers

| Header | Value | Required | Description |
|--------|-------|----------|-------------|
| `Authorization` | `Zoho-oauthtoken <oauth-token>` | **Mandatory** | OAuth 2.0 access token. |
| `ZANALYTICS-ORGID` | Organization ID string | **Mandatory** | Organization ID of the target workspace. Obtainable from the listing APIs (Get All Dashboards, etc.) as the `orgId` field. |
| `Content-Type` | `application/x-www-form-urlencoded` | Required when CONFIG is sent | Required for POST and DELETE requests that include a `CONFIG` body parameter. Not needed for GET requests or when no CONFIG is sent. |

Example — GET (no CONFIG):

```http
GET /restapi/v2/workspaces/7617000032567001/trash HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

Example — POST with CONFIG:

```http
POST /restapi/v2/workspaces/7617000032567001/trash/7617000032567466 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"withDependents":true}
```

---

## Appendix B – OAuth Scope Summary

| API | HTTP Method | Scope |
|-----|-------------|-------|
| Get Trash Views | GET | `ZohoAnalytics.metadata.read` |
| Restore Trash View | POST | `ZohoAnalytics.modeling.create` |
| Delete Trash View | DELETE | `ZohoAnalytics.modeling.delete` |

---

## Appendix C – Response Payload Notes

| Field | Description |
|-------|-------------|
| `status` | `success` or `failure`. Standard Zoho Analytics V2 response envelope. |
| `summary` | Human-readable description of the operation (`"get trash view list"` for [Get Trash Views](#1-get-trash-views)). |
| `data.views` | Array of trashed view objects ([Get Trash Views](#1-get-trash-views) only). Empty array `[]` when nothing is in trash. |
| `viewId` | Returned as a **string** despite being a long integer internally. |
| `deletedTime` | Epoch timestamp in **milliseconds** as a string. Divide by 1000 for Unix epoch seconds. |
| `isDisabled` | Only present when `true`. Indicates the view cannot be restored under the current plan (typically Live Connect reports on a plan that no longer supports them). |
| `tabParentId` | Only present for `DashTab` view types. String ID of the parent tabbed dashboard. |
| Restore/Delete responses | [Restore Trash View](#2-restore-trash-view) and [Delete Trash View](#3-delete-trash-view) return **HTTP 204 No Content** with an empty body on success. |

---

## Appendix D – Understanding Dependent Views in Restore and Delete

### What Are Dependent Views?

In Zoho Analytics, views form **parent–child dependency chains**:

- A **Table** is a parent. Analysis views (charts, pivots, summaries, query tables) built on top of it are its children.
- A **Dashboard** is a parent. Dashboard tabs (`DashTab`) are its children.
- A **Query Table** can itself depend on one or more base tables, and may have child analysis views.

When multiple linked views are all deleted at the same time, they all land in the trash together. The dependency chain is preserved even in trash.

---

### How `withDependents` Affects Restore

When you attempt to restore a view, the system first checks whether any **parent objects** that the view depends on are **also in trash**.

| Scenario | `withDependents=false` (default) | `withDependents=true` |
|----------|----------------------------------|-----------------------|
| View has no parents in trash (standalone) | ✅ Restore succeeds | ✅ Restore succeeds (same result) |
| View depends on a parent table that is also in trash | ❌ Error `7941` — cannot restore without its parent | ✅ Restores the view **and** its parent table (and any related columns, formulas, relations, data connectors) |
| View's parent is already active (not in trash) | ✅ Restore succeeds | ✅ Restore succeeds |

**Example — Restoring a dependent analysis view:**

The `Sales` table and two analysis views (`Region_vs_sales`, `product_Vs_sales`) were all deleted together. The trash list shows all three:

```
Sales          → Table        (parent)
Region_vs_sales → AnalysisView (child of Sales)
product_Vs_sales → AnalysisView (child of Sales)
```

**Option A — Restore `Sales` first, then restore the views separately:**

```http
POST /trash/7617000032567465   (Sales table)   ← no CONFIG needed, standalone
POST /trash/7617000032567466   (Region_vs_sales) ← withDependents=false now works
POST /trash/7617000032567467   (product_Vs_sales) ← withDependents=false now works
```

**Option B — Restore `Region_vs_sales` directly with dependencies:**

```http
POST /trash/7617000032567466
CONFIG={"withDependents":true}
```

This also restores `Sales` (the parent table) automatically, along with any related formulas and relations. Both analysis views are still in trash and must be restored separately or via a workspace-level bulk operation.

> **Tip:** When restoring multiple views deleted in a batch, always restore the parent tables first (with `withDependents=false`), then restore the child views. This avoids accidental cascading restores.

---

### How `withDependents` Affects Permanent Delete

When you attempt to permanently delete a view from trash, the system checks whether any **child dependent views** are **also in trash** and depend exclusively on this view.

| Scenario | `withDependents=false` (default) | `withDependents=true` |
|----------|----------------------------------|-----------------------|
| View has no children in trash | ✅ Delete succeeds | ✅ Delete succeeds |
| View has child analysis views / reports in trash that depend on it | ❌ Error `7942` — cannot delete parent while children are in trash | ✅ Permanently deletes the view **and all its child dependents** in trash (formulas, relations, dependent reports) |
| View is an analysis view (no children) | ✅ Delete succeeds | ✅ Delete succeeds |

**Example — Permanently deleting a table and its analysis views:**

```
Sales          → Table        (7617000032567465)
Region_vs_sales → AnalysisView (7617000032567466, child of Sales)
product_Vs_sales → AnalysisView (7617000032567467, child of Sales)
```

- `DELETE /trash/7617000032567466` (Region_vs_sales) → ✅ succeeds (leaf node, no children)
- `DELETE /trash/7617000032567465` (Sales) — with dependents still in trash → ❌ error `7942`
- `DELETE /trash/7617000032567465` with `CONFIG={"withDependents":true}` → ✅ permanently deletes Sales AND product_Vs_sales together

> ⚠️ `withDependents=true` on Delete is **irreversible**. All deleted views, their columns, formulas, and relations are permanently removed and cannot be recovered.

---

### Special Cases

| Case | Behaviour |
|------|-----------|
| **`isDisabled: true` in trash list** | The view is a Live Connect report and the current plan does not support Live Connect. It appears in the trash list but restore will fail. Upgrade the plan or permanently delete the view. |
| **DashTab type views** | Dashboard tabs (`DashTab`) are children of a tabbed dashboard. To restore a tab, the parent dashboard must also be active (not in trash). If the parent is in trash, restore the parent dashboard first, or use `withDependents=true` on the tab. |
| **View already restored (error 7929)** | If another user or process restored the same view concurrently, the view is no longer in trash. Verify with Get Trash Views — the view will be absent from the list. |
| **Deleting a `DashTab`** | Deleting a tab from trash does not affect the parent dashboard (if the parent is active). |
| **Restoring a view whose folder was also deleted** | If the original folder containing the view was deleted, the view is restored to the workspace root folder. The folder does not need to be restored first. |
| **Partial restore with `withDependents=true`** | The `withDependents=true` flag on Restore brings back the immediate parent chain (parent table, its columns, formulas, relations, connectors). Sibling views that also depended on the same parent are **not** automatically restored — only the specified view and its required ancestors. |
| **Bulk deletion order** | When deleting multiple views manually (multiple DELETE calls), delete leaf views (analysis views, pivots) before parent tables. This avoids triggering error `7942` unexpectedly. |
