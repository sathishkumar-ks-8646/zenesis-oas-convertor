# Zoho Analytics V2 REST API — Auto Analysis

Auto Analysis APIs allow you to automatically generate a set of meaningful views (charts, pivots, summary views) from a table or a specific column within a table. The system examines the data in the source table, infers column roles (dimension vs. measure, geographic, etc.), and creates a curated collection of views — saving the effort of manually designing each view from scratch.

> **Supported source types:** Both APIs work only with **Tables**, **Query Tables**, and **Pipeline Tables**. Passing a chart, dashboard, pivot, or any other derived view type will fail with error **7397**.

---

## Index

| # | API Name | Method | URL Pattern |
|---|----------|--------|-------------|
| 1 | [Auto Analyse View](#1-auto-analyse-view) | POST | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/autoanalyse` |
| 2 | [Auto Analyse Column](#2-auto-analyse-column) | POST | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/columns/<column-id>/autoanalyse` |

---

## 1. Auto Analyse View

Triggers auto analysis on an entire table. The system scans **all columns** of the table, determines the best ways to visualise the data, and creates a set of views (charts, pivots, summaries) directly in the workspace. This is the full-table equivalent of asking "what can you show me from this data?"

The operation tracks completion state — once auto analysis has been run successfully on a table, a repeat call without `analyseAgain=true` will be rejected. This prevents unintended duplication of auto-generated views.

> **Why `analyseAgain` is necessary here:**
> After a successful run, the table is marked internally as "auto analysis completed." Calling this API again (e.g., after new data or new columns are added) without explicitly confirming intent will fail. Setting `analyseAgain=true` signals that you are intentionally re-running the analysis — all previously auto-generated views for this table are **replaced** by the new set. This guard prevents accidental duplication of views when the API is called multiple times.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/autoanalyse` |
| **OAuth Scope** | `ZohoAnalytics.modeling.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organization ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user with Create Report permission on the workspace. |

### CONFIG Parameter

The CONFIG parameter is optional. When provided, it is a JSON object sent as a form-encoded body parameter named `CONFIG`.

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `analyseAgain` | Boolean | No | `false` | Controls whether auto analysis can re-run on a table that has already been analysed. When `false` (default): if the table already has auto-generated views from a previous run, the request fails with error **8116** — protecting against accidental duplication. When `true`: the previous auto-generated views are discarded and a fresh analysis is performed, creating a new set of views based on the current state of the table data and schema. Set this to `true` after adding new columns or importing significantly different data. |

### Sample Requests

**Case 1 — First-time analysis on a table (no CONFIG needed)**

```http
POST /restapi/v2/workspaces/466206000000071000/views/466206000000105001/autoanalyse HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded
```

**Case 2 — Re-run analysis after new columns were added to the table**

```http
POST /restapi/v2/workspaces/466206000000071000/views/466206000000105001/autoanalyse HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"analyseAgain":true}
```

**Case 3 — Re-run analysis on a Query Table after its SQL was modified**

```http
POST /restapi/v2/workspaces/466206000000071000/views/466206000000115006/autoanalyse HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"analyseAgain":true}
```

### Sample Responses

**HTTP 200 OK**

**Case 1 — First-time analysis completed successfully**
```json
{
  "status": "success",
  "summary": "Auto Generate Reports",
  "data": {
    "status": "Reports generated successfully"
  }
}
```

**Case 2 — Re-analysis with `analyseAgain=true` completed successfully**
```json
{
  "status": "success",
  "summary": "Auto Generate Reports",
  "data": {
    "status": "Reports generated successfully"
  }
}
```

> **Note:** Both cases return the same response body. The difference is purely in the request: Case 2 replaces the old set of auto-generated views, while Case 1 creates them for the first time.

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify `<workspace-id>`. |
| 7104 | View (table) not found. | Verify `<view-id>` exists in the workspace. |
| 7301 | User does not have Create Report permission on the workspace. | Ensure the user is a Workspace Admin, Account Admin, Organization Admin, or has been granted Create Report permission on this workspace. |
| 7319 | View does not belong to the specified workspace. | Verify both `<workspace-id>` and `<view-id>` are consistent. |
| 7397 | The view is not a Table, Query Table, or Pipeline Table. | Auto analysis only works on base table types. Pass a valid table view ID. |
| 8116 | Auto analysis has already been completed for this table and `analyseAgain` was not set to `true`. | Pass `CONFIG={"analyseAgain":true}` to re-run the analysis and replace previously generated views. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.modeling.create`. |

---

## 2. Auto Analyse Column

Triggers auto analysis for a **single column** of a table. The system generates targeted views specifically for the selected column — for example, a bar chart of sales by region if the column is "Region", or a trend chart over time if the column is a date. This is useful when you want focused visualisations for a specific column without regenerating the full set.

> **Why `analyseAgain` is NOT present here:**
> Unlike the full-table analysis, column-level analysis does not track whether it has been run before for a given column. Each call generates a new set of views for that column independently — there is no "already completed" guard at the column level. You can call this API multiple times on the same column (for example, after changing column data or for exploratory purposes) and it will always produce a fresh set of views. The `analyseAgain` concept does not apply because column analysis is designed to be repeatable without risk of unintended duplication of full-table views.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/columns/<column-id>/autoanalyse` |
| **OAuth Scope** | `ZohoAnalytics.modeling.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organization ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user with Create Report permission on the workspace. |

> This API has no CONFIG parameter.

### Column Eligibility

Not all columns can be analysed. The following column types are **not supported** and will result in an error:

| Column Characteristic | Reason |
|-----------------------|--------|
| **Auto-Number columns** | These are system-generated sequential IDs with no analytical value. |
| **Multi-Line Text columns** | Free-form long text fields cannot be meaningfully aggregated or charted. |
| **URL columns** | URL strings are not suitable for axis-based analysis. |
| **Geometry columns** | Raw geometry fields require special spatial processing and are not handled by auto analysis. |
| **Hidden columns** | Columns marked as not visible in the table are excluded from analysis. |
| **System columns** (e.g., row ID) | Internal system-managed columns are excluded. |
| **Disabled columns in Query Tables** | Columns that have been disabled in a Query Table definition are not available for analysis. |
| **Standalone Geo Number columns (latitude or longitude without its pair)** | Latitude/Longitude columns must both be present and visible as a pair. A lone latitude or longitude column cannot be analysed independently. |

### Sample Requests

**Case 1 — Analyse a standard dimension column (e.g., "Region")**

```http
POST /restapi/v2/workspaces/466206000000071000/views/466206000000105001/columns/466206000000105020/autoanalyse HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded
```

**Case 2 — Analyse a date column (e.g., "Order Date") to generate time-series views**

```http
POST /restapi/v2/workspaces/466206000000071000/views/466206000000105001/columns/466206000000105025/autoanalyse HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded
```

**Case 3 — Analyse a column in a Query Table**

```http
POST /restapi/v2/workspaces/466206000000071000/views/466206000000115006/columns/466206000000115040/autoanalyse HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded
```

### Sample Responses

**HTTP 200 OK**

**Case 1 — Column analysis completed (dimension column)**
```json
{
  "status": "success",
  "summary": "Auto Generate Reports",
  "data": {
    "status": "Reports generated successfully"
  }
}
```

**Case 2 — Column analysis completed (date column generating time-series charts)**
```json
{
  "status": "success",
  "summary": "Auto Generate Reports",
  "data": {
    "status": "Reports generated successfully"
  }
}
```

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify `<workspace-id>`. |
| 7104 | View (table) not found. | Verify `<view-id>` exists in the workspace. |
| 7107 | Column not found in the specified table. | Verify `<column-id>` belongs to the table identified by `<view-id>`. |
| 7301 | User does not have Create Report permission on the workspace. | Ensure the user is a Workspace Admin, Account Admin, Organization Admin, or has been granted Create Report permission on this workspace. |
| 7319 | View does not belong to the specified workspace. | Verify both `<workspace-id>` and `<view-id>` are consistent. |
| 7397 | The view is not a Table, Query Table, or Pipeline Table. | Auto analysis only works on base table types. Pass a valid table view ID. |
| 8116 | The selected column type is not supported for auto analysis (e.g., Auto-Number, Multi-Line, URL, Geometry, or a system/hidden column). | Choose an eligible column. Refer to the Column Eligibility section for the full list of unsupported column characteristics. |
| 14037 | The column is disabled in its Query Table definition and cannot be used for analysis. | Enable the column in the Query Table configuration or choose a different column. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.modeling.create`. |

---

## Appendix A – Common HTTP Headers

| Header | Value | Required | Notes |
|--------|-------|----------|-------|
| `Authorization` | `Zoho-oauthtoken <oauth-token>` | **Mandatory** | OAuth 2.0 access token of the calling user. |
| `ZANALYTICS-ORGID` | Organization ID | **Mandatory** | Organization ID of the workspace containing the table. |
| `Content-Type` | `application/x-www-form-urlencoded` | Required when sending CONFIG | Required for Auto Analyse View when passing `CONFIG`. Not needed for Auto Analyse Column (no body). |

---

## Appendix B – OAuth Scope Summary

| API | Method | Scope |
|-----|--------|-------|
| Auto Analyse View | POST | `ZohoAnalytics.modeling.create` |
| Auto Analyse Column | POST | `ZohoAnalytics.modeling.create` |

---

## Appendix C – Operational Notes and Failure Cases

### Auto Analyse View vs Auto Analyse Column — Scope Comparison

| Aspect | Auto Analyse View | Auto Analyse Column |
|--------|-------------------|---------------------|
| **Input scope** | Entire table — all eligible columns are analysed together | Single specific column |
| **Tracks completion state?** | Yes — table is marked "analysed" after a successful run | No — always runs fresh, no state tracking |
| **Re-run guard** | `analyseAgain=true` required to overwrite existing auto-generated views | No guard needed; each call is independent |
| **View output** | A comprehensive set of views covering multiple column combinations | A focused set of views for the selected column only |
| **Best used when** | Getting a broad overview of all insights from a newly imported table | Exploring a specific column after data or schema changes |

### Edge Cases and Failure Scenarios

| Scenario | Behaviour |
|----------|-----------|
| Calling Auto Analyse View a second time without `analyseAgain=true` | Fails immediately with error **8116** — "Analysis already completed." The existing auto-generated views are not modified. |
| Setting `analyseAgain=true` on a table that has never been analysed | Permitted. The flag is treated as a no-op for the guard check and the analysis proceeds normally as a first-time run. |
| Table has only unsupported column types (all Auto-Number, URL, Multi-Line) | Auto Analyse View may complete with HTTP 200 but generate fewer or no views, depending on whether any eligible columns exist. No error is raised for empty results. |
| Passing a chart, pivot, dashboard, or any non-table view ID | Both APIs fail with error **7397** — "Not a valid table." The API is restricted exclusively to Tables, Query Tables, and Pipeline Tables. |
| Calling Auto Analyse Column on the same column multiple times | Each call succeeds independently. New views are created each time. If you want to avoid accumulation of duplicate views, delete the previously generated column views manually before re-running. |
| Query Table column that is disabled | Auto Analyse Column fails with error **14037**. The column must be enabled in the Query Table definition before it can be used for analysis. |
| Latitude column without a corresponding Longitude (or vice versa) | Auto Analyse Column fails. Both latitude and longitude must be present as a visible pair for a Geo Number column to be eligible for analysis. |
| Large table with many columns | Auto Analyse View may take longer than usual. The operation is synchronous — the HTTP response is returned only after all views are created. For very large tables, consider analysing individual high-priority columns using Auto Analyse Column for faster targeted results. |
| Auto analysis after importing new rows (same schema) | Schema has not changed, but data distribution may have changed. Run Auto Analyse View with `analyseAgain=true` to regenerate views that reflect the updated data. |
| Auto analysis after adding new columns to a table | Existing auto-generated views were created without knowledge of the new columns. Run Auto Analyse View with `analyseAgain=true` to include the new columns in the generated view set. |
