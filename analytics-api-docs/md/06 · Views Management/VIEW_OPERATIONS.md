# View Operations APIs – Documentation

This document covers V2 REST APIs for managing views within workspaces in Zoho Analytics: creating copies, renaming, deleting, and listing views.

> **Notes that apply to every API in this document:**
> - All requests require OAuth authentication via `Authorization: Zoho-oauthtoken <token>`.
> - `ZANALYTICS-ORGID` is required where noted. See API-specific notes for which org it represents.
> - `ZohoAnalytics_Server_URI` is data-centre dependent (`analyticsapi.zoho.com`, `.eu`, `.in`, etc.).
> - API IDs are for internal use only and are not exposed here.

---

## Index

| # | API Name | Method | URL |
|---|----------|--------|-----|
| 1 | Save As View | POST | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/saveas` |
| 2 | Copy Views | POST | `/restapi/v2/workspaces/<workspace-id>/views/copy` |
| 3 | Create Similar Views | POST | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/similarviews` |
| 4 | Rename View | PUT | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>` |
| 5 | Delete View | DELETE | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>` |
| 6 | Get View List | GET | `/restapi/v2/workspaces/<workspace-id>/views` |
| 7 | Get View Details | GET | `/restapi/v2/views/<view-id>` |
| 8 | Get View URL | GET | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/publish` |
| 9 | Get View Dependents | GET | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/dependents` |
| 10 | Get Recent Views | GET | `/restapi/v2/recentviews` |

---

## 1. Save As View

Creates a copy of an existing view (table or analysis view) within the **same workspace**. The new view is independent of the original after creation — changes to one do not affect the other.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/saveas` |
| **OAuth Scope** | `ZohoAnalytics.modeling.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — must be the Organization ID of the workspace in which the source view resides. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user with Design & Modify permission on the workspace. |

### CONFIG Parameter

The CONFIG parameter is a JSON object sent as a **form parameter** named `CONFIG`.

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `viewName` | String | **Yes** | — | The display name for the newly created view. Must be unique within the workspace. If a view with this name already exists, the request fails with error **7111**. Maximum length follows the workspace/view name validation rules. |
| `viewDesc` | String | No | `""` | A short description for the new view. Maximum 250 characters. If omitted, the new view is created with an empty description. |
| `copyWithData` | Boolean | No | `false` | **Applies to Tables only. Ignored for analysis views (charts, pivots, summaries, etc.).** When `true`: the new table is created as a full copy including all existing row data. When `false`: only the table schema (columns, data types, lookup references, formula definitions) is copied — no row data is duplicated. Use `false` (default) for schema-only copies that will be populated with new data. Combining with `copyHugeData=true` enables asynchronous background copy for large datasets. |
| `copyWithLookup` | Boolean | No | `false` | **Applies to Tables only. Ignored for analysis views.** When `true`: any lookup (join) relationships defined on the source table are also replicated on the new table copy. The copied lookup points to the same referenced table. When `false` (default): lookup definitions are dropped and the new table is standalone. Set to `true` when the new table needs to participate in the same relational model as the source. |
| `copyHugeData` | Boolean | No | `false` | **Applies to Tables only. Ignored for analysis views.** When `true`: data copy is processed asynchronously in the background, allowing the API call to return quickly even for large datasets. The `viewId` is returned immediately but the data population continues in the background. When `false` (default): the API call is synchronous and waits until data copy is complete before returning. Use `true` only when `copyWithData=true` and the source table is large (hundreds of thousands of rows or more) to avoid request timeouts. |
| `folderId` | Long | No | `null` | The ID of the folder within the workspace where the new view should be placed. If omitted (default `null`): the new view is placed in the root-level unorganised area of the workspace. If provided and the folder does not exist in the workspace, the request fails with error **7144**. Use the folder listing API or workspace metadata to get valid folder IDs. |

> **Note on view-type behaviour:**
> - For **Analysis Views** (charts, pivot tables, summary views, query tables, etc.): `copyWithData`, `copyWithLookup`, and `copyHugeData` are all silently ignored. The view definition (axis bindings, filters, settings) is copied. Additional permission checks are applied — the user must also have save permission on the parent table(s) of the analysis view.
> - For **Tables**: all CONFIG fields apply as described.
> - **Dashboards** cannot be duplicated via this API; use Save As on individual views or create a new dashboard manually.

### Sample Requests

**Case 1 — Save As a table (schema only, no data)**

```http
POST /restapi/v2/workspaces/466206000000071000/views/466206000000105001/saveas HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"viewName":"Sales_Archive","viewDesc":"Copy of Sales table for archival","copyWithData":false,"copyWithLookup":true,"folderId":466206000000085001}
```

**Case 2 — Save As a table with data (async copy for large table)**

```http
POST /restapi/v2/workspaces/466206000000071000/views/466206000000105001/saveas HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"viewName":"Sales_Backup_Q3","copyWithData":true,"copyHugeData":true}
```

**Case 3 — Save As an analysis view (chart/report)**

```http
POST /restapi/v2/workspaces/466206000000071000/views/466206000000109002/saveas HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"viewName":"Revenue Trend - Copy","viewDesc":"Duplicate of Q3 revenue trend chart"}
```

### Sample Response

**HTTP 200 OK**

```json
{
  "status": "success",
  "summary": "Saveas view",
  "data": {
    "viewId": "466206000000120001"
  }
}
```

| Response Field | Type | Description |
|----------------|------|-------------|
| `status` | String | `"success"` indicates successful creation. |
| `summary` | String | Human-readable result summary: `"Saveas view"`. |
| `data.viewId` | String | The ID of the **newly created** view. Use this ID in subsequent APIs. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify `<workspace-id>` in the URL is a valid, accessible workspace. |
| 7104 | Source view not found. | Verify `<view-id>` exists within the specified workspace. |
| 7111 | A view with the given `viewName` already exists in this workspace. | Choose a different, unique name for the new view. |
| 7144 | The specified `folderId` does not exist in this workspace. | Provide a valid folder ID from within the same workspace, or omit `folderId` to place the view at the root level. |
| 7301 | User does not have permission to duplicate this view. | Ensure the user is a Workspace Admin, Account Admin, Organization Admin, or has Design & Modify permission on the workspace. For analysis views, the user must also have save permission on the parent table. |
| 7319 | The source view does not belong to the specified workspace. | Ensure both `<workspace-id>` and `<view-id>` are correct and consistent. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.modeling.create`. |

---

## 2. Copy Views

Copies one or more views from a **source workspace** to a **destination workspace**. Both workspaces can belong to the same organisation or different organisations. This is a cross-workspace operation, unlike Save As which only works within a single workspace.

> ⚠️ **This API is not available on custom domains.**

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/copy` |
| **OAuth Scope** | `ZohoAnalytics.modeling.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — For Account Admins (or when no `ZANALYTICS-DEST-ORGID` is supplied): must be the **destination Organisation ID** (the org where views will be copied to). For Organization Admins using `ZANALYTICS-DEST-ORGID`: this is the caller's own (current/source) organisation ID instead. This is a key difference from other APIs where ZANALYTICS-ORGID refers to the source workspace's org. |
| **ZANALYTICS-DEST-ORGID Header** | **Optional** — Used by Organization Admins who have admin access to multiple organisations. Set this to the **destination** organisation ID when it differs from the org resolved from `ZANALYTICS-ORGID`. When present, the system validates that the caller is a member of the specified destination org and uses it as the target for the copy. When absent, the destination org defaults to the org resolved from `ZANALYTICS-ORGID`. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin (of the destination organisation). |

> **On ZANALYTICS-ORGID for this API:** By default, the header identifies the **destination org** because the security check validates the user's admin rights in the destination. The source workspace is identified by `<workspace-id>` in the URL. The destination workspace is identified by `destWorkspaceId` in CONFIG. The `destWorkspaceId` must belong to the org that is ultimately resolved as the destination (either `ZANALYTICS-ORGID` directly, or `ZANALYTICS-DEST-ORGID` when supplied).

> **Cross-organisation copy (Account Admin):** Set `ZANALYTICS-ORGID` to the **destination** organisation's ID. The `workspaceKey` of the source workspace must be provided to authorise the copy.

> **Cross-organisation copy (Organization Admin):** An Organization Admin who has admin access to multiple organisations can copy to a target org by setting `ZANALYTICS-ORGID` to their own (source) org and providing `ZANALYTICS-DEST-ORGID` as the destination org. The system validates that the caller is a member of the destination org before proceeding. The `workspaceKey` is still required when the destination org differs from the source workspace's org.

### CONFIG Parameter

The CONFIG parameter is a JSON object sent as a **form parameter** named `CONFIG`.

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `viewIds` | JSONArray of Long | **Yes** | — | Array of view IDs (from the source workspace) to copy. All IDs must belong to the workspace specified in the URL path. Maximum 1000 view IDs per request. If any view ID does not exist, the request fails with error **7104**. If a view ID does not belong to the source workspace, the request fails with error **7319**. |
| `destWorkspaceId` | Long | **Yes** | — | The ID of the destination workspace where views will be copied. Must belong to the organisation specified in `ZANALYTICS-ORGID`. If the destination workspace does not belong to the destination org, the request fails. |
| `workspaceKey` | String | Conditional | `""` | The copy key of the **source** workspace. **Required when copying across different organisations** (i.e., source and destination workspaces belong to different orgs). When the source and destination orgs are the same, this field is not required (may be omitted or passed as empty). Obtain the workspace copy key from the source workspace's settings. Alphanumeric characters only. If the cross-org copy is attempted without a matching `workspaceKey`, the request fails with error **15007**. |
| `copyWithDependentViews` | Boolean | No | `false` | When `true`: for each view in `viewIds`, all its dependent views (e.g., analysis views built on a table being copied) are also resolved and included in the copy operation automatically. When `false` (default): only the explicitly listed view IDs are copied. Dependent views that are not listed are excluded. Note that if a dependent view references a table that is not being copied, that dependent view may fail to copy or produce a broken state in the destination. Use `true` for tables to ensure the analysis views built on them are preserved. |
| `continueOnFailure` | Boolean | No | `false` | **Effective only when `copyWithDependentViews=true`.** When `true`: if any individual view in the expanded set fails to copy (e.g., due to a name conflict), the operation continues copying the remaining views and returns a partial result. When `false` (default): the entire operation is rolled back on the first failure. Use `true` for large batch copies where partial success is acceptable and you want to investigate failures after the fact. When `copyWithDependentViews=false`, this flag has no effect because each listed view is attempted independently. |
| `createAsSystemTable` | Boolean | No | `false` | When `true`: marks the copied tables in the destination workspace as system tables (a special internal classification). When `false` (default): copied views are standard user-visible tables. **This option is restricted to specific internal service integrations only.** Attempting to use `createAsSystemTable=true` without the required internal service context results in error **7301** (permission denied). External API consumers should always omit this field or set it to `false`. |

> **Note: `copyWithData` field** — the template definition accepts a `copyWithData` field for future use, but this field is not currently processed by the copy views operation. Table row data is not copied in cross-workspace copy; only the schema and view definitions are transferred.

### Combination Behaviour

| Combination | Behaviour |
|-------------|-----------|
| `copyWithDependentViews=false`, `continueOnFailure=false` | Only listed view IDs are copied. Any failure cancels the entire operation. |
| `copyWithDependentViews=false`, `continueOnFailure=true` | `continueOnFailure` has no effect. Only listed views are copied, each independently. |
| `copyWithDependentViews=true`, `continueOnFailure=false` | All dependent views are resolved and added. If any view (listed or resolved dependent) fails to copy, the entire operation is rolled back. |
| `copyWithDependentViews=true`, `continueOnFailure=true` | All dependent views are resolved. Failures on individual views are skipped; the operation proceeds and returns a combined result of successes. Failures are not in the `views` array of the response. |
| Cross-org copy (different source/dest org) without `workspaceKey` | Request fails immediately with error **15007** before any copy is attempted. |
| Cross-org copy with correct `workspaceKey` | Copy proceeds normally, subject to permission checks. |
| Same-org copy (source and dest in same org) | `workspaceKey` is ignored even if provided. |

### Sample Requests

**Case 1 — Copy two tables to a destination workspace in the same org**

```http
POST /restapi/v2/workspaces/466206000000071000/views/copy HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"viewIds":[466206000000105001,466206000000106002],"destWorkspaceId":466206000000080000}
```

**Case 2 — Copy views with all dependents, continue on failure**

```http
POST /restapi/v2/workspaces/466206000000071000/views/copy HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"viewIds":[466206000000105001],"destWorkspaceId":466206000000080000,"copyWithDependentViews":true,"continueOnFailure":true}
```

**Case 3 — Cross-organisation copy using workspace key**

```http
POST /restapi/v2/workspaces/466206000000071000/views/copy HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000987654
Content-Type: application/x-www-form-urlencoded

CONFIG={"viewIds":[466206000000105001,466206000000107003],"destWorkspaceId":467200000000090000,"workspaceKey":"abc123def456","copyWithDependentViews":true,"continueOnFailure":false}
```

**Case 4 — Cross-organisation copy by Org Admin using `ZANALYTICS-DEST-ORGID`**

An Organization Admin who has admin access in both the source org and a separate destination org sets `ZANALYTICS-ORGID` to their own (source/current) org and `ZANALYTICS-DEST-ORGID` to the destination org. The `workspaceKey` is still required since the destination org differs from the source workspace's org.

```http
POST /restapi/v2/workspaces/466206000000071000/views/copy HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
ZANALYTICS-DEST-ORGID: 700000999888
Content-Type: application/x-www-form-urlencoded

CONFIG={"viewIds":[466206000000105001],"destWorkspaceId":467200000000090000,"workspaceKey":"abc123def456"}
```

### Sample Response

**HTTP 200 OK** — Returns a mapping of source view IDs to newly created destination view IDs.

```json
{
  "status": "success",
  "summary": "Copy views",
  "data": {
    "views": [
      {
        "sourceViewId": "466206000000105001",
        "destViewId": "467200000000112001"
      },
      {
        "sourceViewId": "466206000000107003",
        "destViewId": "467200000000112002"
      }
    ]
  }
}
```

| Response Field | Type | Description |
|----------------|------|-------------|
| `status` | String | `"success"` on success. |
| `summary` | String | `"Copy views"` |
| `data.views` | Array | One entry per successfully copied view. |
| `data.views[].sourceViewId` | String | View ID in the source workspace. |
| `data.views[].destViewId` | String | Newly created view ID in the destination workspace. Use this to reference the copied view going forward. |

> When `continueOnFailure=true` and some views fail, only successfully copied views appear in the `views` array. There is no explicit failure list in the current response format.

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Source or destination workspace not found. | Verify `<workspace-id>` (URL) and `destWorkspaceId` (CONFIG) are valid. |
| 7104 | One or more view IDs in `viewIds` do not exist. | Verify each view ID in the array exists and is accessible. |
| 7301 | User does not have permission. Occurs when the user is not an Account Admin / Org Admin of the destination org, or when `createAsSystemTable=true` is used outside of an authorised internal service. | Ensure the user is an Account Admin or Organization Admin of the destination organisation. |
| 7319 | One or more view IDs do not belong to the source workspace specified in the URL. | Ensure all view IDs in `viewIds` are from the workspace specified in `<workspace-id>`. |
| 15007 | Cross-organisation copy not authorised. Occurs when the destination org differs from the source workspace's org and the `workspaceKey` is missing or incorrect. | Provide the correct `workspaceKey` of the source workspace for cross-org copy operations. |
| 8058 | The organisation ID provided in `ZANALYTICS-DEST-ORGID` does not exist. | Provide a valid, existing organisation ID in `ZANALYTICS-DEST-ORGID`. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.modeling.create`. |

---

## 3. Create Similar Views

Creates copies of all analysis views (charts, pivot tables, summaries, etc.) that exist on a **reference table** and replicates them for a **target table** within the same workspace. The column bindings in the copied views are automatically remapped to the corresponding columns of the target table.

This API is useful when you have two tables with the same (or compatible) column structure and want to replicate an entire set of reports from one table to the other.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/similarviews` |
| **OAuth Scope** | `ZohoAnalytics.modeling.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organization ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin, Organization Admin, or Workspace Admin of the workspace. |

> **`<view-id>` in the URL** is the **target table** — the table for which similar views will be created. The newly generated views will be bound to columns from this table.
>
> **`referenceViewId` in CONFIG** is the **reference table** — the table whose existing analysis views are used as the source templates. The structure (axis bindings, filter conditions, settings) of each view on the reference table is cloned and column references are remapped to match the target table's columns by name.

### CONFIG Parameter

The CONFIG parameter is a JSON object sent as a **form parameter** named `CONFIG`.

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `referenceViewId` | Long | **Yes** | — | The ID of the **reference table** within the same workspace. All analysis views built on this reference table will be used as templates. Both `<view-id>` (URL path) and `referenceViewId` must belong to the same workspace; if either does not, the request fails with error **7319**. If the reference table has no analysis views, the call succeeds (HTTP 204) but no views are created. |
| `folderId` | Long | **Yes** | — | The ID of the folder (within the workspace) where all newly created similar views will be placed. There is no default — this field is required. All generated views go into this single folder. If the folder does not exist in the workspace, the request fails with error **7144**. |
| `copyCustomFormula` | Boolean | No | `false` | When `true`: custom formula columns defined on the reference table's views are also copied and mapped to the target table. When `false` (default): formula column definitions are excluded from the copied views. Set to `true` only if the target table has compatible column definitions for the formula expressions to remain valid. Using `true` when column structures differ may result in formula errors on the new views. |
| `copyAggFormula` | Boolean | No | `false` | When `true`: aggregate formula columns (summary-level formulas) defined on the reference table's views are copied to the target table views. When `false` (default): aggregate formulas are excluded. Similar caution applies as with `copyCustomFormula` — only set to `true` if the target table supports the same aggregate expressions. |

> **Column remapping behaviour:**
> When columns are remapped from the reference table to the target table, matching is done by **column name**. If the target table has a column with the exact same name as a column used in a reference view, that axis slot is remapped to the target column. If no matching column is found, that axis slot is left empty or the view may be created in an incomplete state. Always ensure the target table has columns with names matching those used in the reference views before calling this API.

> **Combination note for `copyCustomFormula` + `copyAggFormula`:**
> Both can be `true` simultaneously. When both are `true`, all formula types (custom and aggregate) are included. When both are `false`, only the structural axis/filter bindings are copied — no formula columns.

### Sample Requests

**Case 1 — Create similar views using default settings (no formula copy)**

```http
POST /restapi/v2/workspaces/466206000000071000/views/466206000000105005/similarviews HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"referenceViewId":466206000000105001,"folderId":466206000000085001}
```

**Case 2 — Copy similar views and include all formula column types**

```http
POST /restapi/v2/workspaces/466206000000071000/views/466206000000105005/similarviews HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"referenceViewId":466206000000105001,"folderId":466206000000085001,"copyCustomFormula":true,"copyAggFormula":true}
```

**Case 3 — Copy similar views with only aggregate formulas**

```http
POST /restapi/v2/workspaces/466206000000071000/views/466206000000107003/similarviews HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"referenceViewId":466206000000105001,"folderId":466206000000090002,"copyCustomFormula":false,"copyAggFormula":true}
```

### Sample Response

**HTTP 204 No Content** — No response body is returned. Success is indicated purely by the HTTP status code.

```
HTTP/1.1 204 No Content
```

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify `<workspace-id>` in the URL is valid. |
| 7104 | Target table (`<view-id>`) or reference table (`referenceViewId`) not found. | Verify both view IDs exist in the workspace. |
| 7144 | The specified `folderId` does not exist in this workspace. | Provide a valid, existing folder ID within the same workspace. |
| 7301 | User is not authorised to create views in this workspace. | Ensure the user is an Account Admin, Organization Admin, or Workspace Admin. |
| 7319 | One or both view IDs do not belong to the specified workspace. | Ensure both `<view-id>` (URL) and `referenceViewId` (CONFIG) belong to `<workspace-id>`. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.modeling.create`. |

---

## 4. Rename View

Renames an existing view and optionally updates its description. This applies to all view types — tables, analysis views, dashboards, query tables, and others.

> ⚠️ **Description is always overwritten:** If `viewDesc` is omitted, the description is set to an empty string and the existing description is cleared. Always include the current description if you do not intend to change it.

| Attribute | Value |
|-----------|-------|
| **Method** | PUT |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>` |
| **OAuth Scope** | `ZohoAnalytics.modeling.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organization ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or the View Owner. |

### CONFIG Parameter

The CONFIG parameter is a JSON object sent as a **form parameter** named `CONFIG`.

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `viewName` | String | **Yes** | — | The new display name for the view. Must be non-empty and unique within the workspace. If a view with the same name already exists, the request fails with error **7111**. If an empty string is provided, the request fails with error **7413**. The name follows the workspace/view name validation rules for length and allowed characters. |
| `viewDesc` | String | No | `""` | The new description for the view. Maximum 250 characters. **If omitted, the description is cleared to an empty string** — the previous description is not preserved. To retain the existing description, you must explicitly pass its current value. |

### Sample Requests

**Case 1 — Rename a view (update name only, clears description)**

```http
PUT /restapi/v2/workspaces/466206000000071000/views/466206000000105001 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"viewName":"Sales_Q3_2024"}
```

**Case 2 — Rename a view and update its description**

```http
PUT /restapi/v2/workspaces/466206000000071000/views/466206000000105001 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"viewName":"Revenue Chart - Q3","viewDesc":"Monthly revenue breakdown for Q3 2024"}
```

**Case 3 — Rename a dashboard**

```http
PUT /restapi/v2/workspaces/466206000000071000/views/466206000000109002 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"viewName":"Executive Dashboard v2","viewDesc":"Consolidated KPIs for Q3 review"}
```

### Sample Response

**HTTP 204 No Content** — No response body is returned on success.

```
HTTP/1.1 204 No Content
```

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify `<workspace-id>` in the URL. |
| 7104 | View not found. | Verify `<view-id>` exists in the workspace. |
| 7111 | A view with the given `viewName` already exists in this workspace. | Choose a unique name for the view. |
| 7301 | User does not have permission to rename this view. | Ensure the user is a Workspace Admin, Account Admin, Organization Admin, or the View Owner. |
| 7319 | View does not belong to the specified workspace. | Verify both `<workspace-id>` and `<view-id>` are correct and consistent. |
| 7413 | `viewName` is empty. | Provide a non-empty, valid view name. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.modeling.update`. |

---

## 5. Delete View

Permanently deletes a view from a workspace. The view is moved to the workspace's **Trash** first (soft-delete), from where it can be restored within the retention period. This applies to all view types.

> ⚠️ **Dependent views:** If the view being deleted has other views that depend on it (e.g., analysis views built on a table, or charts embedded in a dashboard), deletion will fail by default unless `deleteDependentViews=true` is set. When set to `true`, all dependent views are also deleted along with the target view.

| Attribute | Value |
|-----------|-------|
| **Method** | DELETE |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>` |
| **OAuth Scope** | `ZohoAnalytics.modeling.delete` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organization ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or the View Owner. |

### CONFIG Parameter

The CONFIG parameter is optional. When provided, it is a JSON object sent as a **form parameter** named `CONFIG`.

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `deleteDependentViews` | Boolean | No | `false` | When `false` (default): if any other view in the workspace depends on `<view-id>` (e.g., an analysis view built on a table being deleted, a dashboard containing views from this table, or a query table referencing this table), the delete operation fails. The error surfaces as a dependency conflict. When `true`: the target view **and all views that depend on it** are deleted in the same operation. This includes direct dependents and transitive dependents (dependents of dependents). Use `true` only when you intend to clean up the entire view graph for this view. This action cannot be undone from the API; all deleted views go to Trash and must be restored individually from there if needed. |

### Sample Requests

**Case 1 — Delete a standalone view (no dependents)**

```http
DELETE /restapi/v2/workspaces/466206000000071000/views/466206000000109002 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Delete a table and all its dependent analysis views**

```http
DELETE /restapi/v2/workspaces/466206000000071000/views/466206000000105001 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"deleteDependentViews":true}
```

**Case 3 — Delete a dashboard (no dependent views on dashboards)**

```http
DELETE /restapi/v2/workspaces/466206000000071000/views/466206000000106002 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

### Sample Response

**HTTP 204 No Content** — No response body is returned on success.

```
HTTP/1.1 204 No Content
```

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify `<workspace-id>` in the URL. |
| 7104 | View not found. | Verify `<view-id>` exists in the workspace. |
| 7301 | User does not have permission to delete this view. Occurs when the user is neither a Workspace Admin, Account Admin, Organization Admin, nor the View Owner. | Ensure the user has the required role. |
| 7319 | View does not belong to the specified workspace. | Verify both `<workspace-id>` and `<view-id>` are correct. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.modeling.delete`. |

---

## 6. Get View List

Returns a list of views accessible to the authenticated user within a specific workspace. Supports filtering by view type, name keyword, created/modified by user, and pagination with sorting.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views` |
| **OAuth Scope** | `ZohoAnalytics.metadata.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organization ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or a Shared User, or a Group Member, or any user with Read permission on the workspace. |

### CONFIG Parameter

The CONFIG parameter is optional. When provided, it is a JSON object passed as a **query parameter** named `CONFIG`.

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `viewTypes` | JSONArray of Integer | No | All types | Filters the result to include only the specified view types. Each element must be an integer from the view type table below. When omitted, all view types accessible to the user are returned. Maximum 8 entries. |
| `keyword` | String | No | `null` | Filters views by a case-insensitive partial match on the view name. For example, `"Sales"` returns views whose names contain `"Sales"`. When omitted, no name filter is applied. |
| `startIndex` | Integer | No | `null` | Zero-based index of the first record to return. Used for pagination. When omitted, results start from index 0. |
| `noOfResult` | Integer | No | `null` | Maximum number of views to return. When omitted, all matching views are returned. Use in combination with `startIndex` to paginate through large workspaces. |
| `sortedColumn` | Integer | No | `0` | Column to sort results by. Allowed values: `0` = Name (default), `1` = Created time, `2` = Last modified time. Values outside `0–2` result in error **8119**. |
| `sortedOrder` | Integer | No | `0` | Sort direction. Allowed values: `0` = Ascending (default), `1` = Descending. Values outside `0–1` result in error **8119**. |
| `criteriaZuid` | Long | No | `null` | Filters views to only those created or last modified by the user with this ZUID (Zoho User ID). When omitted, views from all users are returned. Use this to view a specific user's contributions within a workspace. |

#### View Type Reference

| Integer | `viewType` in Response | Description |
|---------|----------------------|-------------|
| `0` | `Table` | Base data table |
| `1` | `Report` | Tabular view (grid-style report) |
| `2` | `AnalysisView` | Chart / analysis view |
| `3` | `Pivot` | Pivot table |
| `4` | `SummaryView` | Summary view |
| `5` | `TableView` | Custom tabular view |
| `6` | `QueryTable` | Query / SQL-based virtual table |
| `7` | `Dashboard` | Dashboard (includes tabbed dashboards) |
| `9` | `Tab` | A tab within a tabbed dashboard |

### Sample Requests

**Case 1 — Get all views (no filter)**

```http
GET /restapi/v2/workspaces/466206000000071000/views HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Get only dashboards and tables, sorted by last modified time (newest first)**

```http
GET /restapi/v2/workspaces/466206000000071000/views?CONFIG={"viewTypes":[7,0],"sortedColumn":2,"sortedOrder":1} HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 3 — Keyword search with pagination**

```http
GET /restapi/v2/workspaces/466206000000071000/views?CONFIG={"keyword":"Revenue","startIndex":0,"noOfResult":10,"sortedColumn":0,"sortedOrder":0} HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 4 — Get views created or modified by a specific user**

```http
GET /restapi/v2/workspaces/466206000000071000/views?CONFIG={"criteriaZuid":64035928,"sortedColumn":1,"sortedOrder":1} HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

### Sample Response

**HTTP 200 OK**

**Case 1 — Mixed view types (Admin user)**
```json
{
  "status": "success",
  "summary": "Get views",
  "data": {
    "views": [
      {
        "viewId": "137687000000471835",
        "viewName": "Sales",
        "viewDesc": "",
        "viewType": "Table",
        "parentViewId": "",
        "folderId": "137687000000471834",
        "createdTime": "1619175390377",
        "createdBy": "admin@example.com",
        "lastModifiedTime": "1683178935825",
        "lastModifiedBy": "admin@example.com",
        "isFavorite": false,
        "sharedBy": ""
      },
      {
        "viewId": "137687000000471836",
        "viewName": "Average Sales in a Day",
        "viewDesc": "",
        "viewType": "AnalysisView",
        "parentViewId": "137687000000471835",
        "folderId": "137687000000471834",
        "createdTime": "1619175390377",
        "createdBy": "admin@example.com",
        "lastModifiedTime": "1619175390377",
        "lastModifiedBy": "admin@example.com",
        "isFavorite": false,
        "sharedBy": ""
      },
      {
        "viewId": "137687000000471844",
        "viewName": "Dashboard",
        "viewDesc": "",
        "viewType": "Dashboard",
        "parentViewId": "",
        "folderId": "137687000000471834",
        "createdTime": "1619175390377",
        "createdBy": "admin@example.com",
        "lastModifiedTime": "1619175390377",
        "lastModifiedBy": "admin@example.com",
        "isFavorite": false,
        "sharedBy": ""
      }
    ]
  }
}
```

**Case 2 — Shared user response (only views shared with that user)**
```json
{
  "status": "success",
  "summary": "Get views",
  "data": {
    "views": [
      {
        "viewId": "137687000000471835",
        "viewName": "Sales",
        "viewDesc": "",
        "viewType": "Table",
        "parentViewId": "",
        "folderId": "137687000000471834",
        "createdTime": "1619175390377",
        "createdBy": "admin@example.com",
        "lastModifiedTime": "1683178935825",
        "lastModifiedBy": "admin@example.com",
        "isFavorite": false,
        "sharedBy": "admin@example.com"
      }
    ]
  }
}
```

> **Note on `sharedBy`:** For Workspace Admins and Account/Org Admins, `sharedBy` is always empty (`""`). For Shared Users and Group Members, `sharedBy` contains the email address of the user who explicitly shared the view with them.

> **Note on `isFavorite`:** This field is user-specific. It reflects whether the requesting user has marked this view as a favourite. It is not a global property of the view.

> **Note on `parentViewId`:** For analysis views (charts, pivots, summaries), this is the ID of the base table the view is built on. For tables and dashboards, it is an empty string (`""`).

#### Response Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `viewId` | String | Unique identifier of the view. |
| `viewName` | String | Display name of the view. |
| `viewDesc` | String | Description of the view. Empty string if none. |
| `viewType` | String | Type of the view. See View Type Reference table above. |
| `parentViewId` | String | ID of the parent table for analysis views. Empty string for Tables and Dashboards. |
| `folderId` | String | ID of the folder containing this view within the workspace. |
| `createdTime` | String | Creation timestamp in epoch milliseconds. |
| `createdBy` | String | Email address of the user who created the view. |
| `lastModifiedTime` | String | Last modification timestamp in epoch milliseconds (covers both data and design changes). |
| `lastModifiedBy` | String | Email address of the user who last modified the view. |
| `isFavorite` | Boolean | `true` if the requesting user has marked this view as a favourite. User-specific. |
| `sharedBy` | String | Email of the user who shared the view with the current user. Empty string for Workspace Admins and Account/Org Admins. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify `<workspace-id>`. |
| 7301 | User does not have permission to list views in this workspace. | Ensure the user has at least Read permission on the workspace. |
| 8119 | Invalid value for `sortedColumn` (must be 0–2) or `sortedOrder` (must be 0–1). | Use only the documented integer values for sort parameters. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.metadata.read`. |

---

## 7. Get View Details

Returns detailed metadata for a single view identified by its view ID. Unlike the Get View List API, this API does not require a workspace ID in the URL — the view is resolved directly by its ID. Optionally returns extended metadata including column definitions and involved views.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/views/<view-id>` |
| **OAuth Scope** | `ZohoAnalytics.metadata.read` |
| **ZANALYTICS-ORGID Header** | Not required by this API. However, passing it is harmless and recommended for consistency. |
| **Permission Required** | The authenticated user must have at least **Read Only** permission on the view. This includes Account Admins, Organization Admins, Workspace Admins, View Owners, and any user with Read Only or higher access to the view. |

> **No workspace ID in the URL:** This endpoint resolves the view globally by `<view-id>`. The workspace is derived from the view's metadata. This is different from all other workspace-scoped APIs in this document.

### CONFIG Parameter

The CONFIG parameter is optional. When provided, it is a JSON object passed as a **query parameter** named `CONFIG`.

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `withInvolvedMetaInfo` | Boolean | No | `false` | When `false` (default): returns only the basic view attributes (ID, name, description, type, workspace, org, timestamps). When `true`: returns extended metadata depending on the view type — see the **Extended Metadata by View Type** table below. For extended data that is restricted to Workspace Admins (column details, row count, involved view list), non-admin users still get the base fields; the restricted extended fields are returned as `null` or omitted for non-admins. |

#### Extended Metadata by View Type (`withInvolvedMetaInfo=true`)

| View Type | Additional Fields Returned | Admin-Only? |
|-----------|---------------------------|------------|
| **Table** | `columns` (array of column details), `rowCount` (integer) | `rowCount` is Workspace Admin only; `columns` is returned for all users with access |
| **QueryTable** | `columns` (array of column details), `rowCount`, `involvedViews` (parent tables used in the query) | `rowCount` and `involvedViews` are Workspace Admin only |
| **Tabbed Dashboard** | `tabs` (array of tab objects, each with `tabId`, `tabName`, and `involvedViews`) | Workspace Admin only |
| **Analysis View / Pivot / Summary / Regular Dashboard** | `involvedViews` (parent tables/views the view is built on) | Workspace Admin only |

### Sample Requests

**Case 1 — Get basic details of a table**

```http
GET /restapi/v2/views/137687000000471835 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
```

**Case 2 — Get extended metadata for a table (with columns)**

```http
GET /restapi/v2/views/137687000000471835?CONFIG={"withInvolvedMetaInfo":true} HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
```

**Case 3 — Get details of a tabbed dashboard with tab info**

```http
GET /restapi/v2/views/137687000015400002?CONFIG={"withInvolvedMetaInfo":true} HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
```

### Sample Responses

**Case 1 — Basic view info (Table)**
```json
{
  "status": "success",
  "summary": "Get view details",
  "data": {
    "views": {
      "viewId": "137687000000471835",
      "viewName": "Sales",
      "viewDesc": "",
      "viewType": "Table",
      "workspaceId": "137687000000471833",
      "orgId": "64036181",
      "createdTime": "1619175390377",
      "createdBy": "admin@example.com",
      "createdByName": "RestapiAdmin V2",
      "createdByZuId": "64035928",
      "lastDesignModifiedTime": "1619175390377",
      "lastDesignModifiedBy": "admin@example.com",
      "lastDesignModifiedByName": "RestapiAdmin V2",
      "lastDesignModifiedByZuId": "64035928"
    }
  }
}
```

**Case 2 — Extended info for a Table with columns (`withInvolvedMetaInfo=true`)**
```json
{
  "status": "success",
  "summary": "Get view details",
  "data": {
    "views": {
      "viewId": "137687000000471835",
      "viewName": "Sales",
      "viewDesc": "",
      "viewType": "Table",
      "workspaceId": "137687000000471833",
      "orgId": "64036181",
      "createdTime": "1619175390377",
      "createdBy": "admin@example.com",
      "createdByName": "RestapiAdmin V2",
      "createdByZuId": "64035928",
      "lastDesignModifiedTime": "1619175390377",
      "lastDesignModifiedBy": "admin@example.com",
      "lastDesignModifiedByName": "RestapiAdmin V2",
      "lastDesignModifiedByZuId": "64035928",
      "rowCount": 4820,
      "columns": [
        {
          "columnId": "137687000000471840",
          "columnName": "Date",
          "dataType": "DATE_AS_DATE",
          "dataTypeId": 22,
          "dataTypeName": "Date",
          "columnIndex": 1,
          "columnDesc": "",
          "columnMaxSize": 19,
          "isNullable": true,
          "defaultValue": "",
          "pkTableName": "",
          "pkColumnName": "",
          "formulaDisplayName": "",
          "dateFormat": "dd MMMM, yyyy",
          "isHidden": false,
          "sortedOrder": 0,
          "sortedIndex": -1
        },
        {
          "columnId": "137687000000471841",
          "columnName": "Region",
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
        }
      ]
    }
  }
}
```

**Case 3 — Tabbed Dashboard with tabs and involved views (`withInvolvedMetaInfo=true`, Workspace Admin)**
```json
{
  "status": "success",
  "summary": "Get view details",
  "data": {
    "views": {
      "viewId": "137687000015400002",
      "viewName": "TabbedDashboard",
      "viewDesc": "",
      "viewType": "Dashboard",
      "workspaceId": "137687000000471833",
      "orgId": "64036181",
      "createdTime": "1650282725951",
      "createdBy": "admin@example.com",
      "createdByName": "RestapiAdmin V2",
      "createdByZuId": "64035928",
      "lastDesignModifiedTime": "1650282868999",
      "lastDesignModifiedBy": "admin@example.com",
      "lastDesignModifiedByName": "RestapiAdmin V2",
      "lastDesignModifiedByZuId": "64035928",
      "isTabbedDashboard": true,
      "tabs": [
        {
          "tabId": "137687000015400051",
          "tabName": "Tab1",
          "involvedViews": [
            { "viewId": "137687000000471835", "viewName": "Sales", "viewType": "Table" },
            { "viewId": "137687000000471839", "viewName": "ProfitindifferentProducts.", "viewType": "Pivot View" },
            { "viewId": "137687000000471842", "viewName": "SalesVsProfit", "viewType": "Chart View" }
          ]
        },
        {
          "tabId": "137687000015400059",
          "tabName": "Tab2",
          "involvedViews": [
            { "viewId": "137687000000471836", "viewName": "Average Sales in a Day", "viewType": "Chart View" },
            { "viewId": "137687000000471840", "viewName": "Sales and Profit in each Region", "viewType": "Chart View" }
          ]
        }
      ]
    }
  }
}
```

**Case 4 — Dashboard Tab (individual tab within a tabbed dashboard)**
```json
{
  "status": "success",
  "summary": "Get view details",
  "data": {
    "views": {
      "viewId": "137687000015400059",
      "viewName": "Tab2",
      "viewDesc": "",
      "viewType": "Tab",
      "workspaceId": "137687000000471833",
      "orgId": "64036181",
      "createdTime": "1650282855067",
      "createdBy": "admin@example.com",
      "createdByName": "RestapiAdmin V2",
      "createdByZuId": "64035928",
      "lastDesignModifiedTime": "1650282868991",
      "lastDesignModifiedBy": "admin@example.com",
      "lastDesignModifiedByName": "RestapiAdmin V2",
      "lastDesignModifiedByZuId": "64035928",
      "parentViewId": "137687000015400002"
    }
  }
}
```

> **Note on `parentViewId` for Dashboard Tabs:** When the view is a Tab (`viewType: "Tab"`), the `parentViewId` field is present and contains the ID of the parent Tabbed Dashboard. For all other view types, this field is absent.

**Case 5 — QueryTable with involved parent tables (`withInvolvedMetaInfo=true`, Workspace Admin)**
```json
{
  "status": "success",
  "summary": "Get view details",
  "data": {
    "views": {
      "viewId": "137687000000471848",
      "viewName": "SalesQT",
      "viewDesc": "SQL-joined query table",
      "viewType": "QueryTable",
      "workspaceId": "137687000000471833",
      "orgId": "64036181",
      "createdTime": "1619175390377",
      "createdBy": "admin@example.com",
      "createdByName": "RestapiAdmin V2",
      "createdByZuId": "64035928",
      "lastDesignModifiedTime": "1619175390377",
      "lastDesignModifiedBy": "admin@example.com",
      "lastDesignModifiedByName": "RestapiAdmin V2",
      "lastDesignModifiedByZuId": "64035928",
      "rowCount": 0,
      "columns": [
        {
          "columnId": "137687000000471860",
          "columnName": "Cost",
          "dataType": "CURRENCY",
          "dataTypeId": 7,
          "dataTypeName": "Currency",
          "columnIndex": 1,
          "columnDesc": "",
          "columnMaxSize": 19,
          "isNullable": true,
          "defaultValue": "",
          "pkTableName": "",
          "pkColumnName": "",
          "formulaDisplayName": "",
          "isHidden": false,
          "sortedOrder": 0,
          "sortedIndex": -1
        }
      ],
      "involvedViews": [
        { "viewId": "137687000000471835", "viewName": "Sales", "viewType": "Table" },
        { "viewId": "137687000000471836", "viewName": "Products", "viewType": "Table" }
      ]
    }
  }
}
```

#### Response Field Reference

| Field | Type | Present When | Description |
|-------|------|-------------|-------------|
| `viewId` | String | Always | Unique identifier of the view. |
| `viewName` | String | Always | Display name. |
| `viewDesc` | String | Always | Description. Empty string if none. |
| `viewType` | String | Always | View type string. See the View Type Reference table in [Get View List](#6-get-view-list). |
| `workspaceId` | String | Always | Workspace this view belongs to. |
| `orgId` | String | Always | Organisation this view belongs to. |
| `createdTime` | String | When user has at least workspace access | Creation timestamp in epoch milliseconds. |
| `createdBy` | String | When user has at least workspace access | Email of the view creator. |
| `createdByName` | String | When user has at least workspace access | Full name of the view creator. |
| `createdByZuId` | String | When user has at least workspace access | ZUID of the view creator. |
| `lastDesignModifiedTime` | String | When user has at least workspace access | Last design change timestamp in epoch milliseconds. |
| `lastDesignModifiedBy` | String | When user has at least workspace access | Email of last design modifier. |
| `lastDesignModifiedByName` | String | When user has at least workspace access | Full name of last design modifier. |
| `lastDesignModifiedByZuId` | String | When user has at least workspace access | ZUID of last design modifier. |
| `isTabbedDashboard` | Boolean | Dashboards that are tabbed | `true` when the dashboard uses tabbed layout. Absent for regular dashboards. |
| `parentViewId` | String | Dashboard Tabs only | ID of the parent Tabbed Dashboard. |
| `isLive` | Boolean | Live-connected non-dashboard views | `true` if the view is backed by a Live Connect data source. |
| `rowCount` | Long | Tables & QueryTables, `withInvolvedMetaInfo=true`, Workspace Admin only | Number of rows in the table. `0` for Remote DB (Live Connect) tables. |
| `columns` | Array | Tables & QueryTables, `withInvolvedMetaInfo=true` | Column metadata array. See Column Fields table below. |
| `involvedViews` | Array | Analysis views, regular dashboards, QueryTables, `withInvolvedMetaInfo=true`, Workspace Admin only | Parent tables or views that this view is built on. |
| `tabs` | Array | Tabbed Dashboards, `withInvolvedMetaInfo=true`, Workspace Admin only | Array of tab objects with their contained views. |

#### Column Fields (within `columns` array)

| Field | Type | Description |
|-------|------|-------------|
| `columnId` | String | Unique identifier of the column. |
| `columnName` | String | Display name of the column. |
| `dataType` | String | Internal data type identifier (e.g., `PLAIN`, `DATE_AS_DATE`, `CURRENCY`). |
| `dataTypeId` | Integer | Numeric data type ID. |
| `dataTypeName` | String | Human-readable data type name (e.g., `"Plain Text"`, `"Date"`, `"Currency"`). |
| `columnIndex` | Integer | 1-based position of the column in the table. |
| `columnDesc` | String | Column description. |
| `columnMaxSize` | Integer | Maximum storage size of the column. |
| `isNullable` | Boolean | `true` if the column allows null values. |
| `defaultValue` | String | Default value for the column. Empty string if none. |
| `pkTableName` | String | Name of the referenced table if this column is a lookup (foreign key). Empty string otherwise. |
| `pkColumnName` | String | Name of the referenced column for a lookup. Empty string otherwise. |
| `formulaDisplayName` | String | Formula expression display name for formula columns. Empty for regular columns. |
| `isHidden` | Boolean | `true` if the column is hidden from the view. |
| `sortedOrder` | Integer | Sort direction applied to this column: `0` = none, `1` = ascending, `-1` = descending. |
| `sortedIndex` | Integer | Position in the sort priority if multiple columns are sorted. `-1` if not in sort order. |
| `dateFormat` | String | Date format string (e.g., `"dd MMMM, yyyy"`). Present only for date columns. |
| `currencyFormat` | String | Currency format string. Present only for currency columns. |
| `thousandSeparator` | String | Thousand separator character for numeric columns. |
| `decimalSeparator` | String | Decimal separator character for numeric columns. |
| `decimalPlaces` | Integer | Number of decimal places for numeric columns. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7104 | View not found. | Verify `<view-id>` is valid and accessible. |
| 7301 | User does not have Read Only permission on the view. | Ensure the user has been granted at least Read Only access to the view. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.metadata.read`. |

---

## 8. Get View URL

Generates and returns the publicly accessible URL for a view. The URL can be opened directly in a browser without authentication, allowing the view to be shared externally. The URL reflects any visual customisations specified in CONFIG (theme, toolbar, legend position, etc.) and optionally applies a data filter via `criteria`.

> **Two URL forms are returned depending on whether the view has a private key configured:**
> - **Public URL:** `https://analytics.zoho.com/open-view/<view-id>?ZDB_THEME_NAME=<theme>` — accessible by anyone with the link.
> - **Private key URL:** `https://analytics.zoho.com/open-view/<view-id>/<private-key>?ZDB_THEME_NAME=<theme>` — only accessible to users who also possess the private key.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/publish` |
| **OAuth Scope** | `ZohoAnalytics.embed.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organization ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user with Publish permission or Make Public permission on the workspace. |

### CONFIG Parameter

The CONFIG parameter is optional. When provided, it is a JSON object passed as a **query parameter** named `CONFIG`.

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `theme` | String | No | `"blue"` | The visual theme applied to the view in the URL. The theme name is appended as `?ZDB_THEME_NAME=<theme>` in the generated URL. Common values: `blue` (default), `bluedark`, `grey`, `green`, `violet`, `fire`, `tango`, `contrast`. |
| `includeTitle` | Boolean | No | `true` | When `true` (default): the view title is rendered in the shared page. When `false`: the title bar is hidden, giving more vertical space to the view content. |
| `includeDesc` | Boolean | No | `true` | When `true` (default): the view description is shown below the title. When `false`: the description is hidden. |
| `includeToolBar` | Boolean | No | `false` | When `false` (default): the toolbar (which includes export, share, and other action buttons) is hidden for a cleaner read-only appearance. When `true`: the toolbar is shown, allowing the viewer to interact with export and other toolbar functions. |
| `includeSearchBox` | Boolean | No | `false` | **Applies to Tables and Tabular Views only. Ignored for charts, pivots, dashboards.** When `false` (default): no search box is shown. When `true`: a search/filter box is shown above the table, allowing viewers to perform keyword searches within the displayed data. |
| `includeDatatypeSymbol` | Boolean | No | `false` | **Applies to Tables and Tabular Views only.** When `false` (default): column headers show only the column name. When `true`: a data type symbol (icon) is displayed next to each column name, helping viewers understand the column type (text, number, date, etc.) at a glance. |
| `includeShowHideOption` | Boolean | No | `false` | **Applies to Tables and Tabular Views only.** When `false` (default): viewers cannot toggle column visibility. When `true`: a column visibility toggle button appears, allowing viewers to show or hide specific columns without needing edit access. |
| `legendPosition` | String | No | `null` (view default) | **Applies to Chart (Analysis) Views only. Ignored for tables, dashboards, pivots.** Controls where the chart legend is placed. Allowed values: `top`, `bottom`, `left`, `right`, `hidden` (no legend), `float` (overlay on chart). When omitted, the position configured in the view's saved settings is used. |
| `criteria` | String | No | `null` | A Zoho Analytics filter criteria string applied as a data filter on the URL. Filters the data shown when the URL is opened — the viewer sees only the filtered subset. Example: `"\"Region\"='East'"`. The criteria is encoded and appended as a `CRITERIA` URL parameter. When omitted, all data is shown. The criteria must reference columns that exist in the view. |
| `withCustomDomain` | Boolean | No | `false` | When `false` (default): the URL uses the standard `analytics.zoho.com` domain. When `true`: if the workspace has a custom client portal domain configured, the URL is generated using that custom domain instead. Requires the workspace to have a custom domain set up; if not configured, request fails with error **8062**. Use `domainName` for explicit domain specification instead of this flag when possible. |
| `domainName` | String | No | `null` | Explicitly specifies the custom domain to use in the generated URL. When provided, takes precedence over `withCustomDomain`. Must be a valid custom domain configured for the workspace. If the specified domain does not exist, request fails with error **8060**. If the domain exists but does not belong to the workspace/user, fails with error **8061**. |

### Sample Requests

**Case 1 — Get the basic public URL with default theme**

```http
GET /restapi/v2/workspaces/466206000000071000/views/466206000000105001/publish HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — URL with green theme, no toolbar, criteria filter**

```http
GET /restapi/v2/workspaces/466206000000071000/views/466206000000105001/publish?CONFIG={"theme":"green","includeTitle":true,"includeDesc":false,"includeToolBar":false,"criteria":"\"Region\"='East'"} HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 3 — Table URL with search box and data type symbols**

```http
GET /restapi/v2/workspaces/466206000000071000/views/466206000000105003/publish?CONFIG={"includeSearchBox":true,"includeDatatypeSymbol":true,"includeShowHideOption":true} HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

### Sample Responses

**HTTP 200 OK**

**Case 1 — Standard public URL**
```json
{
  "status": "success",
  "summary": "Get view URL",
  "data": {
    "viewUrl": "https://analytics.zoho.com/open-view/466206000000105001?ZDB_THEME_NAME=blue"
  }
}
```

**Case 2 — URL with green theme and region filter**
```json
{
  "status": "success",
  "summary": "Get view URL",
  "data": {
    "viewUrl": "https://analytics.zoho.com/open-view/466206000000105001?ZDB_THEME_NAME=green&INCLUDEDESC=false&CRITERIA=%22Region%22%3D%27East%27"
  }
}
```

**Case 3 — View with private key configured (requires key in URL to access)**
```json
{
  "status": "success",
  "summary": "Get view URL",
  "data": {
    "viewUrl": "https://analytics.zoho.com/open-view/466206000000105001/d7f69c7581b1974af438b42c4aaaed98?ZDB_THEME_NAME=blue"
  }
}
```

> **Difference between Case 1 and Case 3:** When a view's public access is configured with a private key (Make Public with key), the key is embedded in the URL path. This URL is only accessible to users who have the correct key. Without the key segment, the URL returns an access-denied page.

| Response Field | Type | Description |
|----------------|------|-------------|
| `data.viewUrl` | String | The complete, ready-to-use URL. Open this directly in a browser. The URL includes all visual customisations and filter criteria as query parameters. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify `<workspace-id>`. |
| 7104 | View not found. | Verify `<view-id>` exists in the workspace. |
| 7301 | User does not have Publish or Make Public permission on the workspace. | Ensure the user is a Workspace Admin, Account Admin, Organization Admin, or has been granted Publish or Make Public permission. |
| 7319 | View does not belong to the specified workspace. | Verify both `<workspace-id>` and `<view-id>` are consistent. |
| 8060 | The specified `domainName` does not exist. | Provide a valid custom domain name configured for the workspace. |
| 8061 | The specified domain does not belong to the workspace or the calling user. | Use a domain that is associated with the workspace. |
| 8062 | `withCustomDomain=true` but no custom domain is configured for this workspace. | Configure a custom domain for the workspace first, or use the standard URL by omitting `withCustomDomain`. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.embed.read`. |

---

## 9. Get View Dependents

Returns all active views that **depend on** the specified view. A dependent view is any view that cannot exist independently without the specified source view — for example, a chart built on a table, a pivot built on a query table, or a query table built on another query table. Useful before a Delete operation to understand the full impact.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/dependents` |
| **OAuth Scope** | `ZohoAnalytics.metadata.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organization ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin, Organization Admin, or Workspace Admin. |

> This API has no CONFIG parameter.

### Dependency Resolution Rules

| Source View Type | What is Returned as Dependents |
|-----------------|-------------------------------|
| **Table** | All analysis views (charts, pivots, summaries, tabular views), query tables, and pipeline tables built directly or transitively on this table. Also includes any **dashboards** that contain any of those dependent views. |
| **Query Table** | All views built on this query table (direct), plus views built on those views (transitive). Dashboards containing any of those views. Also returns parent query tables that reference this query table in their SQL. |
| **Analysis View / Pivot / Summary** | Any dashboards that embed this view. No child views (analysis views cannot be parents themselves). |
| **Dashboard** | Empty list — dashboards have no dependents in the view graph. |
| **Dashboard Tab** | Any views embedded within this tab. |

> **Important:** Dashboard **Tabs** themselves are **never listed** as dependents. The response lists the parent Dashboard object instead. Individual tabs are excluded from the dependent list.

### Sample Requests

**Case 1 — Get dependents of a table**

```http
GET /restapi/v2/workspaces/466206000000071000/views/466206000000105001/dependents HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Get dependents of a query table**

```http
GET /restapi/v2/workspaces/466206000000071000/views/466206000000115006/dependents HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 3 — Get dependents of a dashboard (expected: empty)**

```http
GET /restapi/v2/workspaces/466206000000071000/views/466206000000109002/dependents HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

### Sample Responses

**HTTP 200 OK**

**Case 1 — Table with chart and pivot dependents, and a dashboard that embeds them**
```json
{
  "status": "success",
  "summary": "Get view dependents",
  "data": {
    "views": [
      {
        "viewId": "466206000000105010",
        "viewName": "Revenue Trend",
        "viewTypeId": 2,
        "viewType": "Chart View"
      },
      {
        "viewId": "466206000000105011",
        "viewName": "Sales by Region",
        "viewTypeId": 3,
        "viewType": "Pivot View"
      },
      {
        "viewId": "466206000000105012",
        "viewName": "Monthly Summary",
        "viewTypeId": 4,
        "viewType": "Summary View"
      },
      {
        "viewId": "466206000000109002",
        "viewName": "Executive Dashboard",
        "viewTypeId": 7,
        "viewType": "Dashboard"
      }
    ]
  }
}
```

**Case 2 — Query Table with child query table and analysis views**
```json
{
  "status": "success",
  "summary": "Get view dependents",
  "data": {
    "views": [
      {
        "viewId": "466206000000115010",
        "viewName": "SalesQT_Child",
        "viewTypeId": 6,
        "viewType": "Query Table"
      },
      {
        "viewId": "466206000000115011",
        "viewName": "QT_Chart_Analysis",
        "viewTypeId": 2,
        "viewType": "Chart View"
      },
      {
        "viewId": "466206000000115012",
        "viewName": "QT_Pivot_Analysis",
        "viewTypeId": 3,
        "viewType": "Pivot View"
      }
    ]
  }
}
```

**Case 3 — Dashboard (no dependents)**
```json
{
  "status": "success",
  "summary": "Get view dependents",
  "data": {
    "views": []
  }
}
```

#### Response Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `data.views` | Array | List of views that depend on the specified view. Empty array if no dependents exist. |
| `views[].viewId` | String | Unique ID of the dependent view. |
| `views[].viewName` | String | Display name of the dependent view. |
| `views[].viewTypeId` | Integer | Integer type code. See the View Type Reference table in [Get View List](#6-get-view-list). |
| `views[].viewType` | String | Human-readable type label (e.g., `"Chart View"`, `"Pivot View"`, `"Query Table"`, `"Dashboard"`). Note: these labels differ slightly from the `viewType` string in the Get View List response (e.g., `"Chart View"` here vs `"AnalysisView"` in listing). |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify `<workspace-id>`. |
| 7104 | View not found. | Verify `<view-id>` exists in the workspace. |
| 7301 | User is not a Workspace Admin, Account Admin, or Organization Admin. | Ensure the user has Workspace Admin or higher role in this workspace. |
| 7319 | View does not belong to the specified workspace. | Verify both `<workspace-id>` and `<view-id>` are consistent. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.metadata.read`. |

---

## 10. Get Recent Views

Returns a list of views recently accessed by the authenticated user across **all workspaces** the user has access to, sorted by access time (most recently accessed first). This is a user-scoped, cross-workspace API — no workspace ID is required in the URL.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/recentviews` |
| **OAuth Scope** | `ZohoAnalytics.metadata.read` |
| **ZANALYTICS-ORGID Header** | Not required — this API is user-scoped and not tied to a single workspace or organisation. |
| **Permission Required** | Any authenticated Zoho Analytics user. |

> This API has no CONFIG parameter. Results are personal to the calling user — different users calling this API see their own respective recent view history.

### Sample Requests

**Case 1 — Get my recent views**

```http
GET /restapi/v2/recentviews HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
```

**Case 2 — Same API, shared user context (only sees views shared with them)**

```http
GET /restapi/v2/recentviews HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.aaaaaa.bbbbbb
```

### Sample Responses

**HTTP 200 OK**

**Case 1 — Workspace Admin with mixed view types across workspaces**
```json
{
  "status": "success",
  "summary": "Get recent views",
  "data": {
    "views": [
      {
        "viewId": "137687000000005744",
        "viewName": "Column Sales",
        "viewType": "Table",
        "workspaceId": "137687000000005620",
        "workspaceName": "Q3 Sales Workspace",
        "viewLastAccessedTime": "1623165599255"
      },
      {
        "viewId": "137687000001859027",
        "viewName": "tabular_1",
        "viewType": "Report",
        "workspaceId": "137687000001859022",
        "workspaceName": "DBOwner-Backup",
        "viewLastAccessedTime": "1622797899143"
      },
      {
        "viewId": "137687000001859035",
        "viewName": "dashboard1",
        "viewType": "Dashboard",
        "workspaceId": "137687000001859022",
        "workspaceName": "DBOwner-Backup",
        "viewLastAccessedTime": "1622741330331"
      },
      {
        "viewId": "137687000001859030",
        "viewName": "summary",
        "viewType": "SummaryView",
        "workspaceId": "137687000001859022",
        "workspaceName": "DBOwner-Backup",
        "viewLastAccessedTime": "1622741297744"
      },
      {
        "viewId": "137687000001859029",
        "viewName": "pivot1",
        "viewType": "Pivot",
        "workspaceId": "137687000001859022",
        "workspaceName": "DBOwner-Backup",
        "viewLastAccessedTime": "1622741261238"
      }
    ]
  }
}
```

**Case 2 — Shared user (only sees views accessible to them)**
```json
{
  "status": "success",
  "summary": "Get recent views",
  "data": {
    "views": [
      {
        "viewId": "138022000000002005",
        "viewName": "Sales",
        "viewType": "Table",
        "workspaceId": "138022000000002015",
        "workspaceName": "SharedUser Sales",
        "viewLastAccessedTime": "1607076349147"
      },
      {
        "viewId": "138022000000002105",
        "viewName": "Cost Across Years by Region",
        "viewType": "AnalysisView",
        "workspaceId": "138022000000002015",
        "workspaceName": "SharedUser Sales",
        "viewLastAccessedTime": "1606987675756"
      }
    ]
  }
}
```

#### Response Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `data.views` | Array | List of recently accessed views, sorted by `viewLastAccessedTime` descending (most recent first). Empty array if the user has no recent view history. |
| `views[].viewId` | String | Unique ID of the view. |
| `views[].viewName` | String | Display name of the view. |
| `views[].viewType` | String | View type string (same format as Get View List API). |
| `views[].workspaceId` | String | ID of the workspace containing this view. |
| `views[].workspaceName` | String | Display name of the workspace. Useful for disambiguation when views from multiple workspaces appear in the result. |
| `views[].viewLastAccessedTime` | String | Epoch milliseconds timestamp of when the calling user last accessed this view. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.metadata.read`. |

---

## Appendix A – Common HTTP Headers

| Header | Value | Required | Notes |
|--------|-------|----------|-------|
| `Authorization` | `Zoho-oauthtoken <oauth-token>` | **Mandatory** | OAuth 2.0 access token of the calling user. |
| `ZANALYTICS-ORGID` | Organization ID | Required for every API except Get View Details and Get Recent Views | For **[Copy Views](#2-copy-views)**: by default the **destination** org ID; when `ZANALYTICS-DEST-ORGID` is also supplied (Org Admin cross-org scenario), this becomes the caller's own (source) org instead. For the others: org of the workspace in the URL. **Not required** for **[Get View Details](#7-get-view-details)** and **[Get Recent Views](#10-get-recent-views)**. |
| `ZANALYTICS-DEST-ORGID` | Destination Organisation ID | Optional — Copy Views only | Used by Organization Admins copying views to a different org they have access to. Set to the destination org ID. When present, overrides destination org resolution and validates the caller is a member of that org. Not required for same-org copies or Account Admin cross-org copies (which use `ZANALYTICS-ORGID` directly as the destination). |
| `Content-Type` | `application/x-www-form-urlencoded` | Recommended for POST/PUT/DELETE | Save As View, Copy Views, Create Similar Views, Rename View, and Delete View send CONFIG as a form-encoded body parameter. The GET APIs pass CONFIG as a URL query parameter (where applicable). |

---

## Appendix B – OAuth Scope Summary

| API | Method | Scope |
|-----|--------|-------|
| Save As View | POST | `ZohoAnalytics.modeling.create` |
| Copy Views | POST | `ZohoAnalytics.modeling.create` |
| Create Similar Views | POST | `ZohoAnalytics.modeling.create` |
| Rename View | PUT | `ZohoAnalytics.modeling.update` |
| Delete View | DELETE | `ZohoAnalytics.modeling.delete` |
| Get View List | GET | `ZohoAnalytics.metadata.read` |
| Get View Details | GET | `ZohoAnalytics.metadata.read` |
| Get View URL | GET | `ZohoAnalytics.embed.read` |
| Get View Dependents | GET | `ZohoAnalytics.metadata.read` |
| Get Recent Views | GET | `ZohoAnalytics.metadata.read` |

---

## Appendix C – Operational Notes and Failure Cases

### Save As View

| Scenario | Behaviour |
|----------|-----------|
| `viewName` conflicts with an existing view name in the workspace | Request fails immediately with error **7111** before any copy is started. |
| `folderId` refers to a folder in a different workspace | Request fails with error **7144** — folder must be in the same workspace as the view being copied. |
| `copyWithLookup=true` and the referenced table no longer exists | Lookup definitions are silently dropped for missing references. The copy still succeeds. |
| `copyHugeData=true` without `copyWithData=true` | `copyHugeData` has no effect. The copy is synchronous with schema only. |
| `copyWithData=true`, `copyHugeData=false` on a very large table | The HTTP request may time out before the data copy completes. Use `copyHugeData=true` for large datasets. |
| Analysis view whose parent table is deleted or inaccessible | Request fails with a permission/not-found error — the parent table must be accessible for the user to save a copy. |
| Dashboard view ID passed as `<view-id>` | Dashboards are not supported by Save As Views. The request may succeed (returning a new view ID) but the result is a copy of the dashboard definition only; card bindings may be broken if referenced views are not also copied. Consider using Copy Views for full dashboard duplication. |

### Copy Views

| Scenario | Behaviour |
|----------|-----------|
| Source and destination workspaces are the same | Allowed. View names may conflict; error **7111** will occur if a view with the same name already exists in the destination. |
| `viewIds` contains a mix of valid and invalid IDs | The security validation phase fails on the first invalid ID (error **7104** or **7319**); no views are copied. |
| `copyWithDependentViews=true` resolves a very large dependency tree | All resolved views are included in the transaction. For very deep dependency chains, the operation may take time. |
| `continueOnFailure=true` and all views fail | HTTP 200 is returned but `data.views` is an empty array. No error is raised. |
| Cross-org copy with incorrect `workspaceKey` | Fails with error **15007**. The workspace key must exactly match the source workspace's copy key; there is no partial match. |
| `destWorkspaceId` belongs to a different org than the resolved destination org | Validation fails; the destination workspace must belong to the destination org resolved from `ZANALYTICS-ORGID` (or `ZANALYTICS-DEST-ORGID` when supplied). |
| Org Admin cross-org copy using `ZANALYTICS-DEST-ORGID` | Set `ZANALYTICS-ORGID` to the caller's own (source) org and `ZANALYTICS-DEST-ORGID` to the destination org. The system validates the caller is a member of the destination org. `workspaceKey` is still required because the destination org differs from the source workspace's org. |
| `ZANALYTICS-DEST-ORGID` refers to a non-existent org | Fails with error **8058** before any copy begins. |
| Caller is not a member of the org specified in `ZANALYTICS-DEST-ORGID` | Fails with error **7301** — "not authorised to do this operation." |
| Destination workspace is full (row/view limits reached) | Copy proceeds up to the limit; remaining views fail. With `continueOnFailure=true`, partial copies are committed. |

### Create Similar Views

| Scenario | Behaviour |
|----------|-----------|
| Reference table has no analysis views | Operation succeeds (HTTP 204) with no views created. |
| Target and reference table are the same view ID | Allowed by the API. Results in duplicate views in the specified folder, since views from the reference are cloned for the same table. |
| Target table column names do not match reference table columns | Column remapping fails for unmatched axes. The similar views are still created but affected axis slots will be empty. Charts may render without data or with errors until the axis bindings are manually corrected. |
| `copyCustomFormula=true` but formula expressions reference columns absent on the target table | Formula columns are created on the target views, but they will be in an error state at render time until the expressions are manually updated to reference valid target columns. |
| `folderId` is a folder that belongs to a nested sub-folder | Supported. All similar views are placed directly into the specified folder regardless of its nesting level. |
| `referenceViewId` is an analysis view (not a table) | The intent is for both `<view-id>` and `referenceViewId` to be base tables. Passing a non-table view as `referenceViewId` may result in unexpected behaviour, as the operation is designed for table-to-table view replication. |

### Rename View

| Scenario | Behaviour |
|----------|-----------|
| `viewDesc` is omitted | The view's existing description is **cleared to empty string** — it is not preserved. Always pass the current description if you do not intend to change it. |
| `viewName` is an empty string | Request fails with error **7413** (view name cannot be empty). |
| Renaming to the same name the view already has | Request succeeds if the name uniqueness check passes (the view itself is excluded from the duplicate check). |
| Renaming a view that is embedded in a dashboard | The rename propagates to all dashboard card references. Dashboard cards reflect the new name immediately without requiring a dashboard update. |
| Renaming a QueryTable | The rename applies to the virtual table. Any analysis views built on the query table are not automatically renamed. |

### Delete View

| Scenario | Behaviour |
|----------|-----------|
| `deleteDependentViews=false` (default) and view has dependents | Request fails with a dependency error. The view is not deleted. Use **[Get View Dependents](#9-get-view-dependents)** to enumerate all dependents before attempting deletion. |
| `deleteDependentViews=true` | All direct and transitive dependents are deleted along with the target view. For a table with 50 analysis views, all 50 are deleted. For an analysis view embedded in dashboards, those dashboards are also deleted. Review all dependents via **Get View Dependents** before proceeding. |
| Deleting a Dashboard Tab | Deleting an individual tab (`viewType: "Tab"`) removes that tab and all views it contains from the parent tabbed dashboard. If it is the last remaining tab, the parent tabbed dashboard itself may be affected. |
| Deleting a Tabbed Dashboard | Deletes the parent tabbed dashboard object. All constituent tabs are deleted as dependents. Set `deleteDependentViews=true` to include tabs in the same operation. |
| Soft-delete behaviour | Deleted views are moved to Trash. They can be restored using the Restore Trash View API within the retention period. After the retention period, they are permanently purged. |
| Deleting a table that is a lookup source for another table | If the source table is deleted, lookup columns in tables that reference it will be orphaned. Set `deleteDependentViews=true` to handle this, or remove the lookup relationship first. |

### Get View List

| Scenario | Behaviour |
|----------|-----------|
| `viewTypes` filter excludes all view types the user has access to | Returns an empty `views` array with HTTP 200. No error is raised. |
| `keyword` matches no view names | Returns an empty `views` array with HTTP 200. |
| `startIndex` is beyond the total result count | Returns an empty `views` array with HTTP 200. |
| Shared User requests the list | Only views explicitly shared with that user are returned. The `sharedBy` field indicates who shared each view. Views not shared with the user are not listed. |
| Group Member requests the list | Views shared with the group the user belongs to are included. `sharedBy` shows the sharing user. |
| `criteriaZuid` is the ZUID of a user who has no views in the workspace | Returns an empty `views` array with HTTP 200. |
| `sortedColumn=1` (created time) with `sortedOrder=1` | Returns views from newest created to oldest created. |
| Workspace contains Dashboard Tabs (`viewType=9`) | Tabs are returned separately from their parent Tabbed Dashboard when `viewTypes` includes `9`. Each tab has `parentViewId` set to the parent dashboard's ID. To get only the dashboard entries (not individual tabs), use `viewTypes=[7]`. |

### Get View Details

| Scenario | Behaviour |
|----------|-----------|
| `withInvolvedMetaInfo=false` (default) on a Tabbed Dashboard | Only the base fields are returned — `isTabbedDashboard: true` is present but `tabs` is absent. To get tab structure, request with `withInvolvedMetaInfo=true`. |
| `withInvolvedMetaInfo=true` called by a non-admin (Shared User / Group Member) | Workspace Admin-restricted fields (`rowCount`, `involvedViews`, `tabs`) are returned as `null`. `columns` is still returned for views the user has access to. |
| Getting details of a Dashboard Tab via its `viewId` | Returns the tab's basic info including `parentViewId` pointing to the parent Tabbed Dashboard. Does not return the tab's contained views unless `withInvolvedMetaInfo=true` and the user is a Workspace Admin. |
| View is a Live Connect table | `isLive: true` is included in the response. `rowCount` returns `0` for live tables regardless of actual remote data volume. |
| View is a Tabbed Dashboard but user is non-admin with `withInvolvedMetaInfo=true` | `isTabbedDashboard: true` is present, but `tabs` is `null` (admin-only). |

### Get View URL

| Scenario | Behaviour |
|----------|-----------|
| `criteria` contains a column name that does not exist in the view | Request fails with a filter criteria validation error before generating the URL. Always validate column names against the view's current schema. |
| `domainName` specified but custom domain not yet configured | Request fails with error **8060** (domain does not exist). Configure the custom domain in workspace settings first. |
| `withCustomDomain=true` but no custom domain is configured | Request fails with error **8062**. Remove `withCustomDomain` or use the standard domain. |
| `legendPosition` applied to a table or dashboard | The parameter is silently ignored for non-chart view types. Only Analysis Views (charts) honour `legendPosition`. |
| `includeSearchBox`, `includeDatatypeSymbol`, or `includeShowHideOption` applied to a chart view | These parameters are silently ignored for non-table view types. They only apply to Tables and Tabular Views (Reports). |
| View has a private key configured | The generated URL includes the private key in the path: `.../open-view/<viewId>/<privateKey>?...`. Accessing the URL without the key will fail. This is the intended secure sharing behaviour. |
| Tabbed Dashboard view ID passed as `<view-id>` | A URL is generated for the tabbed dashboard as a whole. All CONFIG display parameters (toolbar, title, theme) apply to the dashboard frame. Individual tab configuration is not exposed through this API. |

### Get View Dependents

| Scenario | Behaviour |
|----------|-----------|
| View has no dependents (standalone table, dashboard, standalone chart) | Returns HTTP 200 with an empty `views` array. No error is raised. |
| Dashboard is passed as `<view-id>` | Dashboards are leaf nodes in the dependency graph — they have no downstream dependents. Returns an empty `views` array. |
| Analysis view (chart) is passed as `<view-id>` | Returns any dashboards that embed this chart. Analysis views themselves cannot be the parent of other views. |
| Table with deeply nested dependent chain (table → QT → chart → dashboard) | All views in the full transitive chain are returned, not just direct dependents. The result is the complete set of views that would break if the source view were deleted. |
| Dashboard Tabs in a Tabbed Dashboard | Dashboard Tabs are **excluded** from the dependent list. The parent Tabbed Dashboard object is included instead. Use **Get View Details** (`withInvolvedMetaInfo=true`) to inspect the contents of individual tabs. |
| Query table that is both a parent (references other tables) and a child (referenced by analysis views) | Get View Dependents returns **downstream** views only — those that depend on the QT. It does not list the tables the QT itself depends on (use Get View Details for that). |
| `<view-id>` belongs to the Trash | Only active (non-trashed) views are returned as dependents. Views that have been moved to Trash are not included. |

### Get Recent Views

| Scenario | Behaviour |
|----------|-----------|
| User has never accessed any views | Returns HTTP 200 with an empty `views` array. |
| Views from multiple workspaces and organisations | All recent views across all the user's accessible workspaces are returned together in a single list, ordered by access time. The `workspaceId` and `workspaceName` fields distinguish the workspace for each view. |
| A recently accessed view was subsequently deleted | Deleted views are not included in recent views. Only currently active views are returned. |
| Shared User or Group Member | Only views the user currently has access to appear in the result. If a view was later unshared, it is removed from the recent list. |
| Calling with different OAuth tokens (different users) | Returns each user's own individual recent view history. The API is strictly per-user. |

---
