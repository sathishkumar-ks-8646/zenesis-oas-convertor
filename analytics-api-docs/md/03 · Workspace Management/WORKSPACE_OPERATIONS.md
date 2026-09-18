# Zoho Analytics V2 REST API — Workspace Operations

These APIs manage the lifecycle and metadata of workspaces — creating, copying, renaming, deleting, and inspecting workspaces. They also provide mechanisms to retrieve workspace access keys for cross-organisation operations, list workspaces accessible to a user, and export a workspace's structure as a reusable template.

> **Workspace:** A workspace is the top-level container in Zoho Analytics that holds tables, reports, dashboards, and sharing configurations. All data and views exist within a workspace.

---

## Index

| # | API Name | Method | URL |
|---|----------|--------|-----|
| 1 | [Create Workspace](#1-create-workspace) | POST | `/restapi/v2/workspaces` |
| 2 | [Copy Workspace](#2-copy-workspace) | POST | `/restapi/v2/workspaces/<workspace-id>` |
| 3 | [Rename Workspace](#3-rename-workspace) | PUT | `/restapi/v2/workspaces/<workspace-id>` |
| 4 | [Delete Workspace](#4-delete-workspace) | DELETE | `/restapi/v2/workspaces/<workspace-id>` |
| 5 | [Export as Template](#5-export-as-template) | GET | `/restapi/v2/workspaces/<workspace-id>/template/data` |
| 6 | [Get All Workspace List](#6-get-all-workspace-list) | GET | `/restapi/v2/workspaces` |
| 7 | [Get Owned Workspace List](#7-get-owned-workspace-list) | GET | `/restapi/v2/workspaces/owned` |
| 8 | [Get Shared Workspace List](#8-get-shared-workspace-list) | GET | `/restapi/v2/workspaces/shared` |
| 9 | [Get Workspace Secret Key](#9-get-workspace-secret-key) | GET | `/restapi/v2/workspaces/<workspace-id>/secretkey` |
| 10 | [Get Workspace Info](#10-get-workspace-info) | GET | `/restapi/v2/workspaces/<workspace-id>` |

---

## 1. Create Workspace

Creates a new empty workspace in the specified organisation. The workspace is created with no tables, views, or users — content must be added through subsequent APIs.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/workspaces` |
| **OAuth Scope** | `ZohoAnalytics.modeling.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID in which the workspace will be created. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin of the target organisation. |

### CONFIG Parameter

CONFIG is **mandatory**. It must be sent as a form-encoded body parameter named `CONFIG`.

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `workspaceName` | String | **Yes** | — | Name for the new workspace. Must be unique within the organisation. Max 50 characters. |
| `workspaceDesc` | String | No | `""` | Optional description of the workspace's purpose. Max 250 characters. |

### Sample Requests

**Case 1 — Create a minimal workspace with name only**

```http
POST /restapi/v2/workspaces HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"workspaceName":"Sales Analytics"}
```

**Case 2 — Create a workspace with a description**

```http
POST /restapi/v2/workspaces HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"workspaceName":"HR Analytics","workspaceDesc":"Workspace for HR team dashboards and headcount reports"}
```

### Sample Responses

**HTTP 200 OK** — Workspace created successfully.

```json
{
  "status": "success",
  "summary": "Create workspace",
  "data": {
    "workspaceId": "466206000000295001"
  }
}
```

#### Response Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `data.workspaceId` | String | Unique identifier of the newly created workspace. Use this as `<workspace-id>` in all subsequent workspace-specific API calls. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Response returns only `workspaceId`** | The response data contains only the newly created workspace's ID. Call Get Workspace Info or Get All Workspace List to retrieve the full workspace record. |
| **`workspaceDesc` defaults to empty string** | If omitted, the description is stored as `""`. This value can be updated later via Rename Workspace. |
| **`workspaceKey` not in create response** | The workspace secret key is not generated at creation time. Use Get Workspace Secret Key when you need the key for cross-org copy operations. |
| **Dependency** | No dependencies on other APIs for the request. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7301 | User is not an Account Admin or Organization Admin. | Ensure the caller has Account Admin or Organization Admin privileges in the target organisation. |
| 7951 | The organisation has reached its workspace creation limit based on the current subscription plan. | Upgrade the plan or delete unused workspaces before creating a new one. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.modeling.create`. |

---

## 2. Copy Workspace

Creates a copy of an existing workspace. The copy can be placed in the **same organisation** or a **different organisation**. When copying to a different organisation, the workspace's secret key (`workspaceKey`) must be provided for authorisation. The copy can optionally include all table data and/or preserve import source connections.

> **Rate Limit:** Only one copy operation per organisation is allowed to run at a time. A second request while a copy is in progress will be rejected.

> **Same-organisation copy:** Set `ZANALYTICS-ORGID` to the source workspace's organisation. No `workspaceKey` is required.

> **Cross-organisation copy (Account Admin):** Set `ZANALYTICS-ORGID` to the **destination** organisation's ID. The `workspaceKey` of the source workspace must be provided to authorise the copy — obtain it via the [Get Workspace Secret Key](#9-get-workspace-secret-key) API.

> **Cross-organisation copy (Organization Admin):** An Organization Admin who has admin access to multiple organisations can copy to a target org by setting `ZANALYTICS-ORGID` to their own (source) org and providing `ZANALYTICS-DEST-ORGID` as the destination org. The system validates that the caller is a member of the destination org before proceeding. The `workspaceKey` is still required when the destination org differs from the source workspace's org.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/workspaces/<workspace-id>` |
| **OAuth Scope** | `ZohoAnalytics.modeling.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — For same-org copies: the workspace's own organisation ID. For cross-org copies by Account Admin: the **destination** organisation ID. For cross-org copies by Org Admin: the caller's own (source) organisation ID — use `ZANALYTICS-DEST-ORGID` to specify the destination separately. |
| **ZANALYTICS-DEST-ORGID Header** | **Optional** — Used by Organization Admins who have admin access in multiple organisations. Set this to the **destination** organisation ID when it differs from the org resolved from `ZANALYTICS-ORGID`. When present, the system validates that the caller is a member of the specified destination org and uses it as the target for the copy. When absent, the destination org defaults to the caller's own resolved organisation. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin of the **destination** organisation. |

### CONFIG Parameter

CONFIG is **mandatory**. It must be sent as a form-encoded body parameter named `CONFIG`.

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `newWorkspaceName` | String | **Yes** | — | Name for the copied workspace. Must be unique in the destination organisation. Max 50 characters. |
| `newWorkspaceDesc` | String | No | `""` | Description for the copied workspace. Max 250 characters. When omitted, the new workspace has an empty description (the source description is not copied automatically). |
| `workspaceKey` | String | **Yes (cross-org)** | `null` | The secret key of the **source** workspace. Required when the destination organisation (ZANALYTICS-ORGID) differs from the source workspace's organisation. Not required when copying within the same organisation. Obtain this key from the [Get Workspace Secret Key](#9-get-workspace-secret-key) API. |
| `copyWithData` | Boolean | No | `false` | When `false` (default): copies only the workspace structure (tables schema, views, formulas, dashboards) — no data rows are copied. When `true`: copies the complete workspace including all table data rows. Copying with data increases both duration and resource usage significantly. |
| `copyWithImportSource` | Boolean | No | `false` | When `false` (default): import source connections are not copied. Tables in the copied workspace will have no active data source — data must be re-imported manually. When `true`: preserves import source configurations (cloud storage connections, database connectors, etc.) — the copied tables will retain their import source links. Only meaningful when there are active data sources in the source workspace. Cannot be `true` when the source workspace has only live/direct database connections (those always require manual reconnection). |

### Sample Requests

**Case 1 — Copy within the same org (structure only, no data)**

```http
POST /restapi/v2/workspaces/466206000000071000 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"newWorkspaceName":"Sales Analytics – Copy","newWorkspaceDesc":"Backup copy of Sales Analytics"}
```

**Case 2 — Copy within the same org including all data**

```http
POST /restapi/v2/workspaces/466206000000071000 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"newWorkspaceName":"Sales Analytics – Full Backup","copyWithData":true}
```

**Case 3 — Cross-organisation copy by Account Admin (requires `workspaceKey`)**

The `ZANALYTICS-ORGID` is set to the **destination** organisation. The `workspaceKey` authorises access to the source workspace from the destination org's perspective.

```http
POST /restapi/v2/workspaces/466206000000071000 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000999888
Content-Type: application/x-www-form-urlencoded

CONFIG={"newWorkspaceName":"Sales Analytics (Migrated)","workspaceKey":"02aee9b66f299843c961d3712fe09684","copyWithData":true,"copyWithImportSource":true}
```

**Case 4 — Cross-organisation copy by Org Admin using `ZANALYTICS-DEST-ORGID`**

An Organization Admin who has admin access in both the source org and a separate destination org sets `ZANALYTICS-ORGID` to their own (source) org and `ZANALYTICS-DEST-ORGID` to the destination org. The `workspaceKey` is still required since the destination org differs from the source workspace's org.

```http
POST /restapi/v2/workspaces/466206000000071000 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
ZANALYTICS-DEST-ORGID: 700000999888
Content-Type: application/x-www-form-urlencoded

CONFIG={"newWorkspaceName":"Sales Analytics (Org B Copy)","workspaceKey":"02aee9b66f299843c961d3712fe09684"}
```

### Sample Responses

**HTTP 200 OK** — Workspace copied successfully.

```json
{
  "status": "success",
  "summary": "Copy workspace",
  "data": {
    "workspaceId": "466206000000296001"
  }
}
```

#### Response Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `data.workspaceId` | String | Unique identifier of the newly created copy. Use this as `<workspace-id>` in subsequent calls. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **`workspaceKey` required for cross-org copies only** | When copying within the same organisation, `workspaceKey` is not validated. When copying to a different organisation (Account Admin or Org Admin cross-org), the key must match the source workspace's secret key from Get Workspace Secret Key. |
| **`ZANALYTICS-ORGID` vs `ZANALYTICS-DEST-ORGID`** | Account Admins doing a cross-org copy set `ZANALYTICS-ORGID` to the destination org. Org Admins who have access to multiple orgs set `ZANALYTICS-ORGID` to their own (source) org and `ZANALYTICS-DEST-ORGID` to the destination org. |
| **Rate limit: 1 concurrent copy per org** | Only one workspace copy can run at a time per organisation. A second request while one is in progress will be rejected. |
| **`newWorkspaceDesc` is not copied from source** | The description of the copy must be provided explicitly in `newWorkspaceDesc`. If omitted, the copied workspace has an empty description. |
| **`copyWithImportSource=true` limitation** | Only import-based data sources (scheduled syncs, file imports, API-pushed data) are preserved in the copy. Live/direct database connections must be manually reconnected. |
| **Response returns only `workspaceId`** | The ID of the newly created copy. Use Get Workspace Info to retrieve full details. |
| **Dependency** | `workspaceKey` → Get Workspace Secret Key (for the source workspace). Source workspace ID from any workspace list API. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Source workspace not found. | Verify `<workspace-id>` of the source workspace. |
| 7301 | User is not an Account Admin or Organization Admin of the destination organisation. | The caller must be an admin of the destination org, not just the source org. |
| 7951 | The destination organisation has reached its workspace limit. | Upgrade the destination org's plan or remove unused workspaces. |
| 8024 | Cross-org copy attempted without a valid `workspaceKey`, or the provided key does not match the source workspace's secret key. | Obtain the correct `workspaceKey` from the source workspace owner using Get Workspace Secret Key, then retry. For same-org copies, omit `workspaceKey`. |
| 8058 | The organisation ID provided in `ZANALYTICS-DEST-ORGID` does not exist. | Provide a valid, existing organisation ID in `ZANALYTICS-DEST-ORGID`. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.modeling.create`. |

---

## 3. Rename Workspace

Updates the name and/or description of an existing workspace. Both fields are replaced atomically — if `workspaceDesc` is omitted, the description is **reset to an empty string** (the previous value is not preserved).

| Attribute | Value |
|-----------|-------|
| **Method** | PUT |
| **URL** | `/restapi/v2/workspaces/<workspace-id>` |
| **OAuth Scope** | `ZohoAnalytics.modeling.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin of the organisation that owns the workspace. |

### CONFIG Parameter

CONFIG is **mandatory**. It must be sent as a form-encoded body parameter named `CONFIG`.

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `workspaceName` | String | **Yes** | — | New name for the workspace. Must be unique within the organisation. Max 50 characters. |
| `workspaceDesc` | String | No | `""` | New description for the workspace. Max 250 characters. When omitted, the description is **reset to an empty string** — the existing description is not preserved. Always pass the existing description if you only intend to rename. |

### Sample Requests

**Case 1 — Rename only (description will be cleared if not provided)**

```http
PUT /restapi/v2/workspaces/466206000000071000 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"workspaceName":"Global Sales Analytics"}
```

**Case 2 — Rename and update description simultaneously**

```http
PUT /restapi/v2/workspaces/466206000000071000 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"workspaceName":"Global Sales Analytics","workspaceDesc":"Consolidated sales reporting for all regions"}
```

**Case 3 — Update description only (pass the existing name to avoid renaming)**

```http
PUT /restapi/v2/workspaces/466206000000071000 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"workspaceName":"Sales Analytics","workspaceDesc":"Updated: Q3 2025 consolidated sales reporting"}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Rename Workspace returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |
| **`workspaceDesc` is RESET on omission** | If `workspaceDesc` is not included in the request, the workspace's existing description is permanently overwritten with an empty string. Always include the current `workspaceDesc` value (read from Get Workspace Info) to preserve it. |
| **Renaming to the same name** | Succeeds without error (idempotent for the name). |
| **Name must be unique within the org** | The new name must not be in use by another workspace in the same organisation. |
| **Dependency** | Workspace ID → any workspace list API or Get Workspace Info. Current `workspaceDesc` → Get Workspace Info. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify `<workspace-id>`. |
| 7111 | The new workspace name is already used by another workspace in the organisation. | Choose a name not already in use. |
| 7301 | User is not an Account Admin or Organization Admin. | Ensure the caller has Account Admin or Org Admin access. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.modeling.update`. |

---

## 4. Delete Workspace

Permanently deletes the specified workspace and all of its contents — tables, views, dashboards, formulas, import configurations, and all sharing settings. This operation is irreversible.

| Attribute | Value |
|-----------|-------|
| **Method** | DELETE |
| **URL** | `/restapi/v2/workspaces/<workspace-id>` |
| **OAuth Scope** | `ZohoAnalytics.modeling.delete` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin of the organisation that owns the workspace. |

> This API accepts an optional CONFIG parameter. No CONFIG fields are required for standard use.

### Sample Requests

**Case 1 — Delete a workspace**

```http
DELETE /restapi/v2/workspaces/466206000000071000 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Delete Workspace returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |
| **Permanent deletion — no recycle bin** | Once deleted, the workspace and all its views, data, import configurations, and sharing settings cannot be recovered. |
| **All access revoked immediately** | Users who had access to views in this workspace lose that access at the moment of deletion. |
| **Workspace Admins' org membership unaffected** | Deleting a workspace removes the users' workspace-level admin role but does not affect their org-level membership or other workspace access. |
| **Active import jobs are cancelled** | Any scheduled or in-progress data imports are stopped. |
| **`CONFIG` parameter is optional** | If no CONFIG is provided, the deletion proceeds with defaults. |
| **Dependency** | Workspace ID → any workspace list API. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify `<workspace-id>`. |
| 7301 | User is not an Account Admin or Organization Admin. | Ensure the caller has Account Admin or Org Admin access. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.modeling.delete`. |

---

## 5. Export as Template

Exports selected views from the specified workspace as a reusable template file. The response is a binary file in `.atpt` (Zoho Analytics Template) format — not a JSON payload. This file can be imported into another workspace to recreate the selected views and their structural dependencies.

> **File response:** The API returns the template as a binary file attachment. The response `Content-Type` will be `application/octet-stream` or similar binary content type. Save the response body directly as a `.atpt` file.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/template/data` |
| **OAuth Scope** | `ZohoAnalytics.metadata.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace. Account Admins and Organization Admins also have access. |

### CONFIG Parameter

CONFIG is **mandatory**. It must be sent as a query parameter or form-encoded body parameter named `CONFIG`.

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `viewIds` | Array of Longs | **Yes** | — | List of view IDs to include in the template. Min 1 view, max 1000. All specified views must belong to the same workspace. The export automatically includes structural dependencies (lookup columns, formula columns, related tables) required for the selected views to function. |
| `fileName` | String | No | System-generated | Custom name for the exported `.atpt` file (without extension). When omitted, the system generates a file name based on the workspace name. |

### Sample Requests

**Case 1 — Export two specific views as a template**

```http
GET /restapi/v2/workspaces/466206000000071000/template/data HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"viewIds":[466206000000085001,466206000000085003]}
```

**Case 2 — Export with a custom file name**

```http
GET /restapi/v2/workspaces/466206000000071000/template/data HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"viewIds":[466206000000085001,466206000000085003,466206000000085005],"fileName":"SalesAnalytics_Q3_Template"}
```

### Sample Response

**HTTP 200 OK** — Binary `.atpt` file is returned as the response body.

```
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="SalesAnalytics_Q3_Template.atpt"

<binary file content>
```

The `.atpt` file contains:
- Schema definitions for all selected tables and views
- Formula columns, lookup columns, and calculated fields
- View design and layout configurations
- Structural dependencies needed for the views to render correctly

> **Data is not included.** The template file contains structure and design only — no data rows from the source tables are exported. To include data, use the workspace export/import data APIs.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Response is a binary `.atpt` file** | Unlike all other APIs in this document, the response is not JSON. It is a binary stream. Clients must handle the response as binary (not parse as JSON) and write it to disk as a `.atpt` file. |
| **`viewIds` cannot be empty** | At least one view ID must be provided. An empty array is rejected. |
| **Dependent tables are auto-included** | If a view has a lookup column referencing another table, that table is automatically included in the template even if its ID was not in `viewIds`. |
| **All view IDs must belong to the workspace** | If any view ID in `viewIds` belongs to a different workspace, the request fails with error 7319. |
| **Dependency** | `viewIds` → Get View List API for the workspace. Workspace ID → Get Workspace Info. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify `<workspace-id>`. |
| 7104 | One or more specified view IDs do not exist. | Verify all `viewIds` are valid using the Get View List API. |
| 7319 | One or more specified view IDs do not belong to the specified workspace. | Ensure all `viewIds` belong to the workspace identified by `<workspace-id>`. |
| 7301 | User is not a Workspace Admin, Account Admin, or Organization Admin. | Ensure the caller has at least Workspace Admin access. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.metadata.read`. |

---

## 6. Get All Workspace List

Returns all workspaces accessible to the authenticated user — both workspaces they own or administer, and workspaces shared with them. The response separates owned and shared workspaces into two distinct arrays.

This API is user-scoped: it returns only workspaces that the calling user has any level of access to — it does not return every workspace in the organisation. Account Admins see all workspaces in their org in the owned list.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces` |
| **OAuth Scope** | `ZohoAnalytics.metadata.read` |
| **ZANALYTICS-ORGID Header** | Not required. |
| **Permission Required** | Any authenticated Zoho Analytics user. |

> This API has no CONFIG parameter.

### Sample Requests

**Case 1 — Account Admin fetching all accessible workspaces**

```http
GET /restapi/v2/workspaces HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
```

**Case 2 — Shared user fetching their workspace access list**

```http
GET /restapi/v2/workspaces HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.aaaaaa.bbbbbb
```

### Sample Responses

**HTTP 200 OK**

**Case 1 — Account Admin (owns all org workspaces, none shared from other orgs)**
```json
{
  "status": "success",
  "summary": "Get all workspaces",
  "data": {
    "ownedWorkspaces": [
      {
        "workspaceId": "466206000000071000",
        "workspaceName": "Sales Analytics",
        "workspaceDesc": "Sales reporting workspace",
        "orgId": "700000123456",
        "createdTime": "1619175390377",
        "createdBy": "admin@acme.com",
        "isDefault": false
      },
      {
        "workspaceId": "466206000000080000",
        "workspaceName": "HR Analytics",
        "workspaceDesc": "",
        "orgId": "700000123456",
        "createdTime": "1622097563854",
        "createdBy": "admin@acme.com",
        "isDefault": false
      }
    ],
    "sharedWorkspaces": []
  }
}
```

**Case 2 — Shared user with access to workspaces in multiple orgs**
```json
{
  "status": "success",
  "summary": "Get all workspaces",
  "data": {
    "ownedWorkspaces": [
      {
        "workspaceId": "138022000000002015",
        "workspaceName": "My Personal Workspace",
        "workspaceDesc": "",
        "orgId": "700000999888",
        "createdTime": "1606987644675",
        "createdBy": "shareduser@example.com",
        "isDefault": false
      }
    ],
    "sharedWorkspaces": [
      {
        "workspaceId": "466206000000071000",
        "workspaceName": "Sales Analytics",
        "workspaceDesc": "Sales reporting workspace",
        "orgId": "700000123456",
        "createdTime": "1619175390377",
        "createdBy": "admin@acme.com",
        "isDefault": false
      }
    ]
  }
}
```

#### Response Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `data.ownedWorkspaces` | Array | Workspaces where the calling user is the owner (Account Admin) or admin (Org Admin, Workspace Admin). Empty array if none. |
| `data.sharedWorkspaces` | Array | Workspaces from other organisations where views have been shared with the calling user, but the user does not administer the workspace. Empty array if none. |
| `workspaces[].workspaceId` | String | Unique workspace identifier. |
| `workspaces[].workspaceName` | String | Workspace display name. |
| `workspaces[].workspaceDesc` | String | Description. Empty string `""` if not set. |
| `workspaces[].orgId` | String | Organisation ID that owns this workspace. |
| `workspaces[].createdTime` | String | Unix timestamp (milliseconds) when the workspace was created. |
| `workspaces[].createdBy` | String | Email address of the user who created the workspace. |
| `workspaces[].isDefault` | Boolean | `true` if this is the organisation's default workspace. `false` for all other workspaces. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Returns both owned and shared workspaces** | This API combines the results of Get Owned Workspace List and Get Shared Workspace List for the calling user. |
| **`ZANALYTICS-ORGID` not required** | This API does not require the org ID header because it returns workspaces scoped to the calling user's access, across any org they have access to. |
| **`isDefault` and `isFavourite` in response** | The response indicates whether each workspace is the user's current default or in their favourites list, as set by the Workspace Preferences APIs. |
| **Dependency for other APIs** | The `workspaceId` values returned here are the primary source for all workspace-specific API calls. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.metadata.read`. |

---

## 7. Get Owned Workspace List

Returns all workspaces owned by (created within) the authenticated user's organisation. This is an admin-scoped API — only the Account Admin can call it, and it returns all workspaces in the org regardless of sharing.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/owned` |
| **OAuth Scope** | `ZohoAnalytics.metadata.read` |
| **ZANALYTICS-ORGID Header** | Not required. |
| **Permission Required** | The authenticated user must be the **Account Admin** of the organisation. |

> This API has no CONFIG parameter.

### Sample Requests

**Case 1 — Account Admin listing all org-owned workspaces**

```http
GET /restapi/v2/workspaces/owned HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
```

### Sample Responses

**HTTP 200 OK**

```json
{
  "status": "success",
  "summary": "Get owned workspaces",
  "data": {
    "workspaces": [
      {
        "workspaceId": "466206000000071000",
        "workspaceName": "Sales Analytics",
        "workspaceDesc": "Sales reporting workspace",
        "orgId": "700000123456",
        "createdTime": "1619175390377",
        "createdBy": "admin@acme.com",
        "isDefault": false
      },
      {
        "workspaceId": "466206000000080000",
        "workspaceName": "HR Analytics",
        "workspaceDesc": "",
        "orgId": "700000123456",
        "createdTime": "1622097563854",
        "createdBy": "admin@acme.com",
        "isDefault": false
      }
    ]
  }
}
```

> **Difference from Get All Workspace List:** Get Owned Workspace List returns only workspaces belonging to the Account Admin's own organisation. It is restricted to Account Admin access only. Get All Workspace List includes both owned and shared workspaces from all organisations and is accessible to any user.

#### Response Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `data.workspaces` | Array | All workspaces in the calling Account Admin's organisation. |
| `workspaces[].workspaceId` | String | Unique workspace identifier. |
| `workspaces[].workspaceName` | String | Workspace display name. |
| `workspaces[].workspaceDesc` | String | Description. Empty string `""` if not set. |
| `workspaces[].orgId` | String | Organisation ID. Always the Account Admin's org. |
| `workspaces[].createdTime` | String | Unix timestamp (milliseconds) when the workspace was created. |
| `workspaces[].createdBy` | String | Email of the user who created the workspace. |
| `workspaces[].isDefault` | Boolean | `true` if this is the organisation's default workspace. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Account Admin only** | Unlike Get All Workspace List (which any user can call), this API is restricted to Account Admins. It returns all workspaces under the caller's entire organisation, not just those the caller personally created. |
| **`ZANALYTICS-ORGID` not required** | The org scope is determined from the Account Admin's session. |
| **Relationship to Get All Workspace List** | Get Owned Workspace List is a superset for Account Admins — it includes workspaces the Account Admin may not directly own or have Workspace Admin access to, but are within their org. |
| **Dependency** | No dependencies on other APIs for the request. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7301 | User is not the Account Admin. Organization Admins and Workspace Admins cannot call this API. | Use Account Admin credentials. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.metadata.read`. |

---

## 8. Get Shared Workspace List

Returns all workspaces that have been shared with the authenticated user from **other organisations**. Workspaces in the user's own organisation are not included — use Get All Workspace List to see both owned and shared together.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/shared` |
| **OAuth Scope** | `ZohoAnalytics.metadata.read` |
| **ZANALYTICS-ORGID Header** | Not required. |
| **Permission Required** | Any authenticated Zoho Analytics user. |

> This API has no CONFIG parameter.

### Sample Requests

**Case 1 — User listing workspaces shared with them**

```http
GET /restapi/v2/workspaces/shared HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.aaaaaa.bbbbbb
```

### Sample Responses

**HTTP 200 OK**

**Case 1 — User has access to workspaces in two other organisations**
```json
{
  "status": "success",
  "summary": "Get shared workspaces",
  "data": {
    "workspaces": [
      {
        "workspaceId": "466206000000071000",
        "workspaceName": "Sales Analytics",
        "workspaceDesc": "Sales reporting workspace",
        "orgId": "700000123456",
        "createdTime": "1619175390377",
        "createdBy": "admin@acme.com",
        "isDefault": false
      }
    ]
  }
}
```

**Case 2 — User has no shared workspaces**
```json
{
  "status": "success",
  "summary": "Get shared workspaces",
  "data": {
    "workspaces": []
  }
}
```

**Case 3 — Client Portal user seeing their portal's workspace**
```json
{
  "status": "success",
  "summary": "Get shared workspaces",
  "data": {
    "workspaces": [
      {
        "workspaceId": "38190000004180410",
        "workspaceName": "Client Analytics Portal",
        "workspaceDesc": "",
        "orgId": "57058019",
        "createdTime": "1697525603846",
        "createdBy": "admin@brandco.com",
        "isDefault": false
      }
    ]
  }
}
```

#### Response Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `data.workspaces` | Array | Workspaces from other organisations shared with the calling user. Empty array if no workspaces are shared. |
| `workspaces[].workspaceId` | String | Unique workspace identifier. |
| `workspaces[].workspaceName` | String | Workspace display name. |
| `workspaces[].workspaceDesc` | String | Description. Empty string if not set. |
| `workspaces[].orgId` | String | Organisation ID of the workspace owner (not the caller's org). |
| `workspaces[].createdTime` | String | Unix timestamp (milliseconds) of workspace creation. |
| `workspaces[].createdBy` | String | Email of the user who created the workspace. |
| `workspaces[].isDefault` | Boolean | `true` if this is the source organisation's default workspace. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Returns workspaces from other orgs** | This API returns workspaces that have been shared with the calling user by users from other organisations. Workspaces within the caller's own org are not included. |
| **`ZANALYTICS-ORGID` not required** | The scope is cross-org and determined from the caller's identity, not an org header. |
| **Relationship to Get All Workspace List** | The results of this API are a subset of what Get All Workspace List returns (the shared-from-other-orgs portion). |
| **Dependency** | No dependencies on other APIs for the request. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.metadata.read`. |

---

## 9. Get Workspace Secret Key

Returns the secret key for the specified workspace. This key is used as the `workspaceKey` parameter when performing a cross-organisation Copy Workspace operation — it authorises the copying of the workspace to a different organisation.

The key can optionally be regenerated, which invalidates the previous key. Any previously shared `workspaceKey` values become invalid after regeneration.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/secretkey` |
| **OAuth Scope** | `ZohoAnalytics.metadata.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin of the organisation that owns the workspace. |

### CONFIG Parameter

CONFIG is optional. It must be sent as a query parameter or form-encoded body parameter named `CONFIG`.

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `regenerateKey` | Boolean | No | `false` | When `false` (default): returns the existing secret key without modification. When `true`: generates a new random secret key, stores it as the workspace's new secret key, and returns it. The previous key is permanently invalidated — any party that held the old key can no longer copy this workspace using it. |

### Sample Requests

**Case 1 — Retrieve the existing secret key**

```http
GET /restapi/v2/workspaces/466206000000071000/secretkey HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Regenerate and retrieve a new secret key**

```http
GET /restapi/v2/workspaces/466206000000071000/secretkey HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"regenerateKey":true}
```

### Sample Responses

**HTTP 200 OK** — Key returned (or regenerated and returned).

```json
{
  "status": "success",
  "summary": "Get workspace secretkey",
  "data": {
    "workspaceKey": "02aee9b66f299843c961d3712fe09684"
  }
}
```

#### Response Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `data.workspaceKey` | String | The workspace's current secret key (hex string). Pass this as `workspaceKey` in the Copy Workspace CONFIG when copying to a different organisation. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **`regenerateKey=false` (default) is safe to call repeatedly** | Returns the current key each time. If no key has been generated yet, one is created on the first call. |
| **`regenerateKey=true` invalidates the old key immediately** | Any cross-org copy attempt using the old key after regeneration will fail with error 8024. In-progress copy operations started before regeneration are not affected. |
| **Key is never in other API responses** | The workspace secret key is not returned by Get Workspace Info, Get All Workspace List, or any other API — only this dedicated endpoint returns it. |
| **Dependency** | Workspace ID → any workspace list API. The returned key is used as `workspaceKey` in Copy Workspace. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify `<workspace-id>`. |
| 7301 | User is not an Account Admin or Organization Admin. | Ensure the caller has Account Admin or Org Admin access. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.metadata.read`. |

---

## 10. Get Workspace Info

Returns metadata for the specified workspace. The calling user must have at least some level of access to the workspace (Workspace Admin, or any view in the workspace shared with them). An optional `withUserRoleInfo` flag enriches the response with the calling user's role details within the workspace.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/<workspace-id>` |
| **OAuth Scope** | `ZohoAnalytics.metadata.read` |
| **ZANALYTICS-ORGID Header** | Not required (workspace ID determines org). |
| **Permission Required** | The authenticated user must be a Workspace Admin, or a Shared User, or a Group Member of the workspace, or any user with at least Read permission on a view within the workspace. Account Admins and Organization Admins also have access. |

### CONFIG Parameter

CONFIG is optional.

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `withUserRoleInfo` | Boolean | No | `false` | When `false` (default): returns only workspace metadata. When `true`: additionally includes a `userRoleInfo` object in the response describing the calling user's role within the workspace — their role name, role ID, and whether they are assigned a custom role. |

### Sample Requests

**Case 1 — Basic workspace info (no role info)**

```http
GET /restapi/v2/workspaces/466206000000071000 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
```

**Case 2 — With calling user's role info**

```http
GET /restapi/v2/workspaces/466206000000071000 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
Content-Type: application/x-www-form-urlencoded

CONFIG={"withUserRoleInfo":true}
```

**Case 3 — Client Portal / White Label user getting workspace info**

```http
GET /restapi/v2/workspaces/38190000004180410 HTTP/1.1
Host: analytics.clientbrand.com
Authorization: Zoho-oauthtoken 1000.aaaaaa.bbbbbb
```

### Sample Responses

**HTTP 200 OK**

**Case 1 — Basic workspace info**
```json
{
  "status": "success",
  "summary": "Get workspace details",
  "data": {
    "workspaces": {
      "workspaceId": "466206000000071000",
      "workspaceName": "Sales Analytics",
      "workspaceDesc": "Sales reporting workspace for all regions",
      "createdTime": "1619175390377",
      "createdBy": "admin@acme.com",
      "orgId": "700000123456"
    }
  }
}
```

**Case 2 — With `withUserRoleInfo=true` (Account Admin caller)**
```json
{
  "status": "success",
  "summary": "Get workspace details",
  "data": {
    "workspaces": {
      "workspaceId": "466206000000071000",
      "workspaceName": "Sales Analytics",
      "workspaceDesc": "Sales reporting workspace for all regions",
      "createdTime": "1619175390377",
      "createdBy": "admin@acme.com",
      "orgId": "700000123456",
      "userRoleInfo": {
        "isCustomRoleUser": false,
        "roleId": 0,
        "roleName": "Account Admin"
      }
    }
  }
}
```

**Case 3 — With `withUserRoleInfo=true` (custom role user)**
```json
{
  "status": "success",
  "summary": "Get workspace details",
  "data": {
    "workspaces": {
      "workspaceId": "466206000000071000",
      "workspaceName": "Sales Analytics",
      "workspaceDesc": "Sales reporting workspace for all regions",
      "createdTime": "1619175390377",
      "createdBy": "admin@acme.com",
      "orgId": "700000123456",
      "userRoleInfo": {
        "isCustomRoleUser": true,
        "roleId": 466206000000090001,
        "roleName": "AnalystRole"
      }
    }
  }
}
```

> **`data.workspaces` is a single object, not an array.** Unlike the list APIs (Get All / Owned / Shared), this returns workspace details as a single JSON object under `workspaces`.

#### Response Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `data.workspaces` | Object | A single workspace info object. |
| `workspaces.workspaceId` | String | Unique workspace identifier. |
| `workspaces.workspaceName` | String | Display name of the workspace. |
| `workspaces.workspaceDesc` | String | Description. Empty string `""` if not set. |
| `workspaces.createdTime` | String | Unix timestamp (milliseconds) of workspace creation. |
| `workspaces.createdBy` | String | Email of the user who created the workspace. |
| `workspaces.orgId` | String | Organisation ID that owns this workspace. |
| `workspaces.userRoleInfo` | Object | *(Present only when `withUserRoleInfo=true`.)* The calling user's role details within this workspace. |
| `userRoleInfo.isCustomRoleUser` | Boolean | `true` if the calling user is assigned a custom role in this workspace. `false` for standard roles. |
| `userRoleInfo.roleId` | Number | Numeric identifier of the user's role. `0` for standard org roles (Account Admin, Org Admin, etc.). Non-zero for custom roles. |
| `userRoleInfo.roleName` | String | Display name of the calling user's role. Examples: `"Account Admin"`, `"Organization Admin"`, `"Workspace Admin"`, `"User"`, `"Viewer"`, or a custom role name. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **`withUserRoleInfo=false` (default)** | Returns standard workspace metadata only. Fastest response option. |
| **`withUserRoleInfo=true` adds `userRoleInfo` object** | The additional object contains `isCustomRoleUser` (boolean), `roleId` (numeric), and `roleName` (string). Account Admins and Org Admins return `roleId: 0`; custom role users return the custom role's ID and display name. |
| **`workspaceKey` is NOT returned** | Get Workspace Info does not expose the secret key. Use Get Workspace Secret Key for that. |
| **Accessible to shared users with READ permission** | Unlike other workspace management APIs, this API is available to any user who has at least one view shared with them in the workspace (in addition to Workspace Admins). |
| **Comparison with list APIs** | Get Workspace Info returns richer metadata for a single known workspace. Use the list APIs to discover workspace IDs, then this API for detailed info on a specific workspace. |
| **Dependency** | Workspace ID → any workspace list API. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify `<workspace-id>`. |
| 7301 | User does not have any access to the specified workspace. The user must be a workspace admin or have at least one view shared with them in this workspace. | Verify the user has been added to the workspace or has a view shared with them. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.metadata.read`. |

---

## Appendix A – Common HTTP Headers

| Header | Value | Required | Notes |
|--------|-------|----------|-------|
| `Authorization` | `Zoho-oauthtoken <oauth-token>` | **Mandatory** | OAuth 2.0 access token of the calling user. |
| `ZANALYTICS-ORGID` | Organisation ID | Mandatory for workspace-specific write operations | Required for Create (target org), Copy (source or destination org — see Copy Workspace notes), Rename, Delete, Export, and Get Secret Key. Not required for list operations or Get Workspace Info. |
| `ZANALYTICS-DEST-ORGID` | Destination Organisation ID | Optional — Copy Workspace only | Used by Organization Admins copying a workspace to a different org they have access to. Set to the destination org ID. When present, overrides destination org resolution and validates the caller is a member of that org. Not required for same-org copies or Account Admin cross-org copies (which use `ZANALYTICS-ORGID` directly as the destination). |
| `Content-Type` | `application/x-www-form-urlencoded` | Required for POST/PUT/DELETE with CONFIG | Not required for GET-only APIs with no body or query-param CONFIG. |

---

## Appendix B – OAuth Scope Summary

| API | Method | Scope |
|-----|--------|-------|
| Create Workspace | POST | `ZohoAnalytics.modeling.create` |
| Copy Workspace | POST | `ZohoAnalytics.modeling.create` |
| Rename Workspace | PUT | `ZohoAnalytics.modeling.update` |
| Delete Workspace | DELETE | `ZohoAnalytics.modeling.delete` |
| Export as Template | GET | `ZohoAnalytics.metadata.read` |
| Get All Workspace List | GET | `ZohoAnalytics.metadata.read` |
| Get Owned Workspace List | GET | `ZohoAnalytics.metadata.read` |
| Get Shared Workspace List | GET | `ZohoAnalytics.metadata.read` |
| Get Workspace Secret Key | GET | `ZohoAnalytics.metadata.read` |
| Get Workspace Info | GET | `ZohoAnalytics.metadata.read` |

---

## Appendix C – API-Specific Notes and Behaviours

### Workspace Name Constraints

| Rule | Detail |
|------|--------|
| Max length | 50 characters for `workspaceName` / `newWorkspaceName`. Exceeding this is rejected at parameter validation. |
| Uniqueness | Workspace names must be unique within the organisation. Creating or renaming to a duplicate name fails with error **7111**. |
| Description max | 250 characters. Exceeding this is rejected at parameter validation. |
| Description reset | In Rename Workspace, omitting `workspaceDesc` **clears the existing description** to empty string. Always include the current description to preserve it. |

### Create Workspace

| Scenario | Behaviour |
|----------|-----------|
| Plan workspace limit reached | Fails with error **7951**. The limit depends on the organisation's subscription tier. |
| Org Admin calling this API | Allowed — Org Admins can create workspaces within their organisation. |
| Workspace created with no views | The workspace is usable but empty. Tables and views must be added via separate APIs. |

### Copy Workspace

| Scenario | Behaviour |
|----------|-----------|
| Same-org copy without `workspaceKey` | Allowed — `workspaceKey` is only checked for cross-org copies. |
| Account Admin cross-org copy | Set `ZANALYTICS-ORGID` to the destination org ID. Provide `workspaceKey` (source workspace's secret key). The caller must be an Account Admin or Org Admin of the destination org. |
| Org Admin cross-org copy using `ZANALYTICS-DEST-ORGID` | Set `ZANALYTICS-ORGID` to the caller's own (source) org and `ZANALYTICS-DEST-ORGID` to the destination org. The system validates the caller is a member of the destination org. `workspaceKey` is still required because the destination org differs from the source workspace's org. |
| `ZANALYTICS-DEST-ORGID` refers to a non-existent org | Fails with error **8058** before any copy begins. |
| Caller is not a member of the org specified in `ZANALYTICS-DEST-ORGID` | Fails with error **7301** — "not authorised to do this operation." |
| Cross-org copy without `workspaceKey` | Fails with error **8024**. |
| Provided `workspaceKey` does not match source workspace's secret key | Fails with error **8024**. Obtain the correct key from Get Workspace Secret Key. |
| `copyWithData=true` on a large workspace | Operation takes significantly longer. The rate limit (1 concurrent copy per org) means other copy requests will queue or fail while this is in progress. |
| `copyWithImportSource=false` (default) | Tables in the copy will have no import source — data must be re-imported or manually entered. The table schema is preserved. |
| `copyWithImportSource=true` with a live database connection | Live/direct database connections (e.g., Zoho DataPrep live links) cannot be copied by definition — only import-based connections (scheduled syncs, file imports, API-pushed data) are preserved. Live connections require manual reconnection. |
| `newWorkspaceDesc` omitted | The copied workspace has an empty description. The source workspace's description is not automatically copied. |
| Destination org plan limit | Fails with error **7951** if the destination org has reached its workspace limit. |
| Concurrent copy in progress | Only one copy per org runs at a time. A simultaneous request is rejected. |

### Rename Workspace

| Scenario | Behaviour |
|----------|-----------|
| Renaming to the same name | Succeeds (idempotent). |
| Renaming to a name already in use in the org | Fails with error **7111**. |
| `workspaceDesc` omitted from request | Description is permanently cleared to empty string — existing description is lost. Always include `workspaceDesc` if you only intend to change the name. |

### Delete Workspace

| Scenario | Behaviour |
|----------|-----------|
| Workspace has active import jobs | Import jobs are cancelled. The workspace and all its data are deleted. |
| Workspace is shared with users | All sharing configurations are removed. Users who had access to views in this workspace will lose all access immediately. |
| Workspace has Workspace Admins | Their admin role for this workspace is removed when the workspace is deleted. Their org membership is not affected. |
| Deletion is permanent | There is no trash/recycle mechanism for workspaces. Once deleted, the workspace and all its content cannot be recovered. |

### Export as Template

| Scenario | Behaviour |
|----------|-----------|
| `viewIds` is an empty array | Rejected — at least one view ID must be provided. |
| A view ID belongs to a different workspace | Fails with error **7319**. All view IDs must be in the same workspace as specified in the URL. |
| Views with lookup columns | Dependent tables needed to resolve lookups are automatically included in the template. |
| Response format | The response is a binary `.atpt` file, not JSON. Clients must handle the response as a binary stream and save it to disk. |

### Get Workspace Secret Key

| Scenario | Behaviour |
|----------|-----------|
| `regenerateKey=false` (default) | Returns the existing key. If no key has been generated yet, the system generates and returns one. |
| `regenerateKey=true` | Generates a new key. The old key is permanently invalidated. Any cross-org copy that was in progress using the old key is not affected (the key is validated only at copy start), but any future copy attempts using the old key will fail. |
| Who can see the key | Only Account Admins and Org Admins of the workspace's organisation. The key is never returned in workspace listing or info APIs. |

### Get Workspace Info — `withUserRoleInfo`

| Scenario | Behaviour |
|----------|-----------|
| `withUserRoleInfo=false` (default) | Standard metadata only. Fastest response. |
| `withUserRoleInfo=true` — Account Admin caller | `roleName` returns `"Account Admin"`, `roleId` is `0`, `isCustomRoleUser` is `false`. |
| `withUserRoleInfo=true` — Org Admin caller | `roleName` returns `"Organization Admin"`, `roleId` is `0`. |
| `withUserRoleInfo=true` — custom role user | `isCustomRoleUser` is `true`, `roleId` is the custom role's numeric ID, `roleName` is the custom role's display name. |
| `withUserRoleInfo=true` — shared user (no workspace role) | `roleName` may reflect their view-level access role. Behaviour depends on their permission level. |

### Workspace List API Comparison

| API | Returns | Who can call | ZANALYTICS-ORGID |
|-----|---------|--------------|------------------|
| Get All Workspace List | Owned + shared workspaces for the caller | Any user | Not required |
| Get Owned Workspace List | All workspaces in the caller's org | Account Admin only | Not required |
| Get Shared Workspace List | Workspaces from other orgs shared with the caller | Any user | Not required |
| Get Workspace Info | Single workspace details | Workspace Admin, shared user, or any user with view access | Not required |
