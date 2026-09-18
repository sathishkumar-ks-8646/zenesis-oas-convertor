# Zoho Analytics V2 REST API — Workspace Folders

Folders provide a hierarchical organization layer within a workspace. Views (tables, reports, dashboards) can be placed inside folders to help users navigate large workspaces. Folders can be nested up to one level deep — a top-level folder can have sub-folders, but sub-folders cannot have children of their own.

> **Default Folder:** Every workspace has a single default folder. The default folder is where new views are placed when no explicit folder is selected. You can change which folder is the default at any time, but there can only be one default folder per workspace.

> **Folder Visibility for Shared Users:** Workspace Admins see all folders. Shared users and group members see only the folders that contain at least one view they have been granted access to. Parent folders of accessible sub-folders are also included.

> **White Label / Client Portal:** All folder management APIs are available via portal domain URLs. White label portal users can create and manage folders if they have been granted the Create Folder permission on the workspace.

---

## Index

| # | API Name | Method | URL |
|---|----------|--------|-----|
| 1 | [Get Folder List](#1-get-folder-list) | GET | `/restapi/v2/workspaces/<workspace-id>/folders` |
| 2 | [Create Folder](#2-create-folder) | POST | `/restapi/v2/workspaces/<workspace-id>/folders` |
| 3 | [Rename Folder](#3-rename-folder) | PUT | `/restapi/v2/workspaces/<workspace-id>/folders/<folder-id>` |
| 4 | [Delete Folder](#4-delete-folder) | DELETE | `/restapi/v2/workspaces/<workspace-id>/folders/<folder-id>` |
| 5 | [Change Folder Hierarchy](#5-change-folder-hierarchy) | PUT | `/restapi/v2/workspaces/<workspace-id>/folders/<folder-id>/move` |
| 6 | [Change Folder Position](#6-change-folder-position) | PUT | `/restapi/v2/workspaces/<workspace-id>/folders/<folder-id>/reorder` |
| 7 | [Move Views To Folder](#7-move-views-to-folder) | PUT | `/restapi/v2/workspaces/<workspace-id>/views/movetofolder` |
| 8 | [Make Default Folder](#8-make-default-folder) | PUT | `/restapi/v2/workspaces/<workspace-id>/folders/<folder-id>/default` |

---

## 1. Get Folder List

Returns all folders in the specified workspace, including their names, descriptions, display order, default status, and parent folder references. Shared users and group members receive a filtered list containing only the folders that include at least one view they have access to.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/folders` |
| **OAuth Scope** | `ZohoAnalytics.metadata.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace, or a Shared User or Group Member with at least READ permission on one or more views in the workspace. |

> This API has no CONFIG parameter.

### Sample Requests

**Case 1 — Workspace Admin listing all folders**

```http
GET /restapi/v2/workspaces/466206000000071000/folders HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Shared User listing accessible folders (filtered response)**

```http
GET /restapi/v2/workspaces/466206000000071000/folders HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.aaaaaa.bbbbbb
ZANALYTICS-ORGID: 700000123456
```

**Case 3 — White label portal user listing folders**

```http
GET /restapi/v2/workspaces/466206000000071000/folders HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.cccccc.dddddd
ZANALYTICS-ORGID: 700000123456
```

### Sample Responses

**HTTP 200 OK**

**Case 1 — Workspace Admin — workspace with nested folders**
```json
{
  "status": "success",
  "summary": "Get folders",
  "data": {
    "folders": [
      {
        "folderId": "7617000000508002",
        "folderName": "Tables & Reports",
        "folderDesc": "Default Folder",
        "folderIndex": -1,
        "isDefault": true,
        "parentFolderId": "-1"
      },
      {
        "folderId": "7617000071955001",
        "folderName": "Parent folder 1",
        "folderDesc": "",
        "folderIndex": 0,
        "isDefault": false,
        "parentFolderId": "-1"
      },
      {
        "folderId": "7617000071955003",
        "folderName": "Sub folder 1",
        "folderDesc": "",
        "folderIndex": 2,
        "isDefault": false,
        "parentFolderId": "7617000071955001"
      },
      {
        "folderId": "7617000071955002",
        "folderName": "Parent folder 2",
        "folderDesc": "",
        "folderIndex": 1,
        "isDefault": false,
        "parentFolderId": "-1"
      },
      {
        "folderId": "7617000071955004",
        "folderName": "Sub folder 2",
        "folderDesc": "",
        "folderIndex": 2,
        "isDefault": false,
        "parentFolderId": "7617000071955002"
      }
    ]
  }
}
```

**Case 2 — Shared User — filtered list (only folders containing accessible views)**
```json
{
  "status": "success",
  "summary": "Get folders",
  "data": {
    "folders": [
      {
        "folderId": "137687000000471834",
        "folderName": "Tables & Reports",
        "folderDesc": "Default Folder",
        "folderIndex": -1,
        "isDefault": true,
        "parentFolderId": "-1"
      },
      {
        "folderId": "137687000097308304",
        "folderName": "Parent folder 1",
        "folderDesc": "",
        "folderIndex": 0,
        "isDefault": false,
        "parentFolderId": "-1"
      },
      {
        "folderId": "137687000097308305",
        "folderName": "Sub folder 1",
        "folderDesc": "",
        "folderIndex": 2,
        "isDefault": false,
        "parentFolderId": "137687000097308304"
      }
    ]
  }
}
```

**Case 3 — Workspace with only the default folder**
```json
{
  "status": "success",
  "summary": "Get folders",
  "data": {
    "folders": [
      {
        "folderId": "13193000000302867",
        "folderName": "Tables & Reports",
        "folderDesc": "",
        "folderIndex": -1,
        "isDefault": true,
        "parentFolderId": "-1"
      }
    ]
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `folderId` | String | Unique ID of the folder. |
| `folderName` | String | Display name of the folder. |
| `folderDesc` | String | Description of the folder. Empty string if none set. |
| `folderIndex` | Integer | Sort position of the folder within its level. `-1` indicates the default folder. |
| `isDefault` | Boolean | `true` if this is the workspace's current default folder. |
| `parentFolderId` | String | ID of the parent folder. `"-1"` means the folder is at the top level (root). |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Filtered response for shared users** | Workspace Admins see all folders. Shared Users and Group Members receive only folders that contain at least one view they can access. If a user can access a view inside a sub-folder, both the sub-folder and its parent folder are included in their response. |
| **`parentFolderId` is a string** | Returned as a quoted string (e.g. `"-1"`), not a numeric. `"-1"` means the folder is at root level with no parent. |
| **`folderIndex` ordering** | Folders are sorted by `folderIndex` within their level. The default folder always has `folderIndex: -1`. |
| **Empty workspace** | If the workspace has no folders, the `folders` array is returned empty (`[]`). |
| **Dependency for other APIs** | The `folderId` values returned here are required as: `<folder-id>` in the URL for Rename Folder, Delete Folder, Change Folder Hierarchy, Change Folder Position, and Make Default Folder; `parentFolderId` in Create Folder; `referenceFolderId` in Change Folder Position. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7301 | User does not have permission. | Ensure the user is a Workspace Admin, or has at least READ access to one or more views in the workspace. |

---

## 2. Create Folder

Creates a new folder in the specified workspace. The folder can optionally be created as a sub-folder of an existing top-level folder and can be designated as the default folder upon creation.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/folders` |
| **OAuth Scope** | `ZohoAnalytics.modeling.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace, or any user with Create Folder permission on the workspace. |

### CONFIG Parameters

| Parameter | Type | Mandatory | Default | Max Length | Description |
|-----------|------|-----------|---------|------------|-------------|
| `folderName` | String | Yes | — | 200 | Name of the folder to create. Must be unique within the workspace. |
| `folderDesc` | String | No | `""` | 250 | Description for the folder. |
| `parentFolderId` | Long | No | `-1` (root) | — | ID of an existing top-level folder to create this folder under. Omit or pass `-1` to create a top-level folder. |
| `makeDefaultFolder` | Boolean | No | `false` | — | If `true`, the newly created folder becomes the default folder for the workspace. |

### Sample Requests

**Case 1 — Create a top-level folder**

```http
POST /restapi/v2/workspaces/466206000000071000/folders HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"folderName":"Sales Analysis","folderDesc":"All sales-related reports and dashboards"}
```

**Case 2 — Create a sub-folder under an existing parent folder**

```http
POST /restapi/v2/workspaces/466206000000071000/folders HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"folderName":"Q1 Reports","folderDesc":"Q1 breakdown","parentFolderId":7617000071955001}
```

**Case 3 — Create a top-level folder and immediately set it as the default**

```http
POST /restapi/v2/workspaces/466206000000071000/folders HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"folderName":"Main Workspace","makeDefaultFolder":true}
```

**Case 4 — White label portal user with Create Folder permission**

```http
POST /restapi/v2/workspaces/466206000000071000/folders HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.cccccc.dddddd
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"folderName":"Client Reports","folderDesc":"Reports shared with the client"}
```

### Sample Responses

**HTTP 200 OK**

```json
{
  "status": "success",
  "summary": "Create folder",
  "data": {
    "folderId": "7617000071955010"
  }
}
```

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Response returns only `folderId`** | The response data contains only the newly created folder's ID. To retrieve the full folder record (name, description, index, parent), call Get Folder List after creation. |
| **`folderDesc` defaults to empty string** | If `folderDesc` is omitted, it is stored as `""` — not `null`. This is the initial value and does not affect subsequent Rename operations. |
| **`parentFolderId` defaults to root** | If omitted or set to `-1`, the folder is created at the root level. |
| **`makeDefaultFolder=true` side effect** | Triggers Make Default Folder internally. The previously marked default folder loses its `isDefault: true` status. |
| **One level of nesting only** | The `parentFolderId` must reference a root-level folder. Attempting to nest inside an existing sub-folder is rejected with error 7496. |
| **Dependency** | If creating a sub-folder, obtain the target `folderId` from Get Folder List. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7140 | A folder with the same name already exists in the workspace. | Use a unique folder name within the workspace. |
| 7144 | The specified `parentFolderId` does not exist. | Verify the `parentFolderId` value using the Get Folder List API. |
| 7301 | User does not have permission. | Ensure the user is a Workspace Admin or has Create Folder permission on the workspace. |
| 7414 | Folder name cannot be empty. | Provide a non-empty value for `folderName`. |
| 7496 | Maximum subfolder nesting depth exceeded. | Sub-folders cannot themselves have children. Only one level of nesting is supported. |

---

## 3. Rename Folder

Updates the name and/or description of an existing folder. If `folderDesc` is omitted from the request, the folder's existing description is **reset to an empty string**.

> **Important:** Always include `folderDesc` in the request if you want to preserve the existing description. Omitting this field will clear it.

| Attribute | Value |
|-----------|-------|
| **Method** | PUT |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/folders/<folder-id>` |
| **OAuth Scope** | `ZohoAnalytics.modeling.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace, or any user with Create Folder permission on the workspace. |

### CONFIG Parameters

| Parameter | Type | Mandatory | Default | Max Length | Description |
|-----------|------|-----------|---------|------------|-------------|
| `folderName` | String | Yes | — | 200 | New name for the folder. Must be unique within the workspace. |
| `folderDesc` | String | No | `""` | 250 | New description for the folder. **Omitting this field resets the description to an empty string.** |

### Sample Requests

**Case 1 — Rename a folder and preserve its description**

```http
PUT /restapi/v2/workspaces/466206000000071000/folders/7617000071955001 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"folderName":"Annual Sales Analysis","folderDesc":"All sales-related reports and dashboards"}
```

**Case 2 — Rename a folder and update its description**

```http
PUT /restapi/v2/workspaces/466206000000071000/folders/7617000071955001 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"folderName":"FY2025 Sales","folderDesc":"Fiscal year 2025 sales reports"}
```

**Case 3 — White label portal user renaming a folder**

```http
PUT /restapi/v2/workspaces/466206000000071000/folders/7617000071955001 HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.cccccc.dddddd
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"folderName":"Client Dashboard","folderDesc":"Customer-facing dashboards"}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

```
HTTP/1.1 204 No Content
```

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Rename Folder returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |
| **`folderDesc` is RESET on omission** | If `folderDesc` is not included in the request, the folder's existing description is permanently overwritten with an empty string. This is the most common mistake with this API — always include the current `folderDesc` value (read from Get Folder List) if you only intend to change the name. |
| **Renaming to the same name** | Succeeds without error (idempotent for the name). |
| **Name uniqueness** | The new `folderName` must not already be in use by another folder in the same workspace. |
| **Dependency** | `<folder-id>` in the URL must be obtained from Get Folder List. Read the current `folderDesc` from Get Folder List before calling this API if you want to preserve it. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7140 | A folder with the same name already exists in the workspace. | Use a unique folder name within the workspace. |
| 7144 | The specified folder does not exist. | Verify the folder ID using the Get Folder List API. |
| 7301 | User does not have permission. | Ensure the user is a Workspace Admin or has Create Folder permission on the workspace. |
| 7414 | Folder name cannot be empty. | Provide a non-empty value for `folderName`. |

---

## 4. Delete Folder

Deletes the specified folder from the workspace. By default, views inside the folder are preserved and moved out before deletion. You can optionally request that all views inside the folder be deleted as well.

> **Dependent Views:** If a folder contains a table that has dependent child views (reports or dashboards built on top of that table), deletion will fail unless `deleteDependentViews` is set to `true`.

| Attribute | Value |
|-----------|-------|
| **Method** | DELETE |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/folders/<folder-id>` |
| **OAuth Scope** | `ZohoAnalytics.modeling.delete` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace, or any user with Create Folder permission on the workspace. |

### CONFIG Parameters

| Parameter | Type | Mandatory | Default | Max Length | Description |
|-----------|------|-----------|---------|------------|-------------|
| `deleteDependentViews` | Boolean | No | `false` | — | If `true`, all views inside the folder (including dependent child views of any tables) are permanently deleted along with the folder. If `false`, the API will fail if the folder contains tables that have dependent views. |

### Sample Requests

**Case 1 — Delete an empty folder**

```http
DELETE /restapi/v2/workspaces/466206000000071000/folders/7617000071955005 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={}
```

**Case 2 — Delete a folder and all its views**

```http
DELETE /restapi/v2/workspaces/466206000000071000/folders/7617000071955005 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"deleteDependentViews":true}
```

**Case 3 — White label portal user deleting a folder**

```http
DELETE /restapi/v2/workspaces/466206000000071000/folders/7617000071955005 HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.cccccc.dddddd
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

```
HTTP/1.1 204 No Content
```

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Delete Folder returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |
| **Views are preserved by default** | When `deleteDependentViews` is omitted (`false`), views inside the folder are not deleted — they are kept and become accessible at the workspace root level. Only the folder container is removed. |
| **Blocked when dependent views exist** | If the folder contains a table that has dependent child reports or dashboards, deletion with `deleteDependentViews=false` fails with error 7277. Either delete the dependent views first, or set `deleteDependentViews=true`. |
| **`deleteDependentViews=true` is permanent** | All views inside the folder, including tables and their child reports/dashboards, are permanently deleted. This cannot be undone. |
| **Deleting the current default folder** | Allowed. After deletion the workspace has no default folder until Make Default Folder is called. |
| **Dependency** | `<folder-id>` in the URL must be obtained from Get Folder List. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7144 | The specified folder does not exist. | Verify the folder ID using the Get Folder List API. |
| 7277 | The folder contains tables that have dependent child views; deletion blocked. | Set `deleteDependentViews` to `true` to delete the folder along with all dependent views, or manually delete the dependent views first. |
| 7301 | User does not have permission. | Ensure the user is a Workspace Admin or has Create Folder permission on the workspace. |

---

## 5. Change Folder Hierarchy

Changes the hierarchical position of a folder — either promoting a sub-folder to a top-level folder, or nesting an existing top-level folder under another top-level folder.

The `hierarchy` parameter controls the direction of the change:

| `hierarchy` Value | Meaning |
|-------------------|---------|
| `0` | Promote: Move the specified sub-folder up to become a top-level (root-level) folder. |
| `1` | Nest: Move the specified top-level folder to become a sub-folder of the folder specified by `parentFolderId`. |

| Attribute | Value |
|-----------|-------|
| **Method** | PUT |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/folders/<folder-id>/move` |
| **OAuth Scope** | `ZohoAnalytics.modeling.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace, or any user with Create Folder permission on the workspace. |

### CONFIG Parameters

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `hierarchy` | Integer | Yes | — | Direction of the hierarchy change. `0` = promote sub-folder to top level; `1` = nest under a parent folder. |
| `parentFolderId` | Long | **Yes when `hierarchy=1`** | — | ID of the top-level folder to become the parent. Required only when `hierarchy` is `1`. |

### Sample Requests

**Case 1 — Promote a sub-folder to top-level (hierarchy=0)**

```http
PUT /restapi/v2/workspaces/466206000000071000/folders/7617000071955003/move HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"hierarchy":0}
```

**Case 2 — Nest a top-level folder under another folder (hierarchy=1)**

```http
PUT /restapi/v2/workspaces/466206000000071000/folders/7617000071955002/move HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"hierarchy":1,"parentFolderId":7617000071955001}
```

**Case 3 — White label portal user changing folder hierarchy**

```http
PUT /restapi/v2/workspaces/466206000000071000/folders/7617000071955002/move HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.cccccc.dddddd
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"hierarchy":1,"parentFolderId":7617000071955001}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

```
HTTP/1.1 204 No Content
```

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Change Folder Hierarchy returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |
| **`hierarchy=0` — no `parentFolderId` needed** | When promoting a sub-folder to root level, `parentFolderId` must not be provided. The folder's parent link is removed and it becomes a root-level folder. |
| **`hierarchy=1` — `parentFolderId` is mandatory** | When nesting, both fields are required. Omitting `parentFolderId` when `hierarchy=1` results in an error. |
| **`parentFolderId` must be a root-level folder** | You cannot nest a folder inside an existing sub-folder. The folder given by `parentFolderId` must be at root level (its own `parentFolderId` is `"-1"`). |
| **Only `0` and `1` are valid** | Any other integer value for `hierarchy` immediately returns error 8119 before any database change is made. |
| **Dependency** | Both `<folder-id>` (the folder to move) and `parentFolderId` (when `hierarchy=1`) must be obtained from Get Folder List. Verify the `parentFolderId` target is a root-level folder before calling. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7144 | The specified folder or parent folder does not exist. | Verify the folder IDs using the Get Folder List API. |
| 7301 | User does not have permission. | Ensure the user is a Workspace Admin or has Create Folder permission on the workspace. |
| 8119 | Invalid value for `hierarchy`. Only `0` and `1` are accepted. | Use `0` to promote a sub-folder to root level, or `1` to nest a folder under a parent. |

---

## 6. Change Folder Position

Reorders a folder by moving it to just above another specified folder at the same hierarchy level. Both folders must be at the same level (both top-level or both sub-folders of the same parent).

| Attribute | Value |
|-----------|-------|
| **Method** | PUT |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/folders/<folder-id>/reorder` |
| **OAuth Scope** | `ZohoAnalytics.modeling.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace, or any user with Create Folder permission on the workspace. |

### CONFIG Parameters

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `referenceFolderId` | Long | Yes | — | ID of the folder that the target folder should be placed immediately above. |

### Sample Requests

**Case 1 — Move a folder above another folder**

```http
PUT /restapi/v2/workspaces/466206000000071000/folders/7617000071955002/reorder HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"referenceFolderId":7617000071955001}
```

**Case 2 — Reorder a sub-folder within its parent**

```http
PUT /restapi/v2/workspaces/466206000000071000/folders/7617000071955004/reorder HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"referenceFolderId":7617000071955003}
```

**Case 3 — White label portal user reordering folders**

```http
PUT /restapi/v2/workspaces/466206000000071000/folders/7617000071955002/reorder HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.cccccc.dddddd
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"referenceFolderId":7617000071955001}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

```
HTTP/1.1 204 No Content
```

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Change Folder Position returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |
| **Moves folder to immediately above the reference** | After this operation, the target folder (identified by `<folder-id>`) appears directly above `referenceFolderId` in the sorted list. |
| **Both folders must be at the same hierarchy level** | Both the target folder and `referenceFolderId` must be either both root-level or both sub-folders of the same parent. Cross-level reordering is not supported and will produce unexpected results. |
| **`folderIndex` is updated** | After this call, `folderIndex` values for affected folders are recalculated. Use Get Folder List to confirm the new ordering. |
| **Dependency** | Both `<folder-id>` (folder to reorder) and `referenceFolderId` (the position anchor) must be obtained from Get Folder List. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7144 | The specified folder or reference folder does not exist. | Verify the folder IDs using the Get Folder List API. |
| 7301 | User does not have permission. | Ensure the user is a Workspace Admin or has Create Folder permission on the workspace. |

---

## 7. Move Views To Folder

Moves one or more views (tables, reports, dashboards) into the specified destination folder within the workspace. All views must belong to the same workspace. Up to 1000 view IDs can be moved in a single request.

| Attribute | Value |
|-----------|-------|
| **Method** | PUT |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/movetofolder` |
| **OAuth Scope** | `ZohoAnalytics.modeling.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace, or any user with Create Folder permission on the workspace. |

### CONFIG Parameters

| Parameter | Type | Mandatory | Default | Max Items | Description |
|-----------|------|-----------|---------|-----------|-------------|
| `folderId` | Long | Yes | — | — | ID of the destination folder. |
| `viewIds` | JSONArray of Long | Yes | — | 1000 | Array of view IDs to move into the destination folder. |

### Sample Requests

**Case 1 — Move a single view to a folder**

```http
PUT /restapi/v2/workspaces/466206000000071000/views/movetofolder HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"folderId":7617000071955001,"viewIds":[7617000000510001]}
```

**Case 2 — Move multiple views to a folder in bulk**

```http
PUT /restapi/v2/workspaces/466206000000071000/views/movetofolder HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"folderId":7617000071955001,"viewIds":[7617000000510001,7617000000510002,7617000000510003]}
```

**Case 3 — White label portal user moving views to a folder**

```http
PUT /restapi/v2/workspaces/466206000000071000/views/movetofolder HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.cccccc.dddddd
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"folderId":7617000071955001,"viewIds":[7617000000510004,7617000000510005]}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

```
HTTP/1.1 204 No Content
```

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Move Views To Folder returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |
| **Transactional — all or nothing** | Either all specified views are moved, or none. A single invalid `viewId` (not belonging to the workspace) causes the entire request to fail with error 7319 before any views are moved. |
| **Maximum 1000 views per request** | For workspaces requiring more than 1000 moves, split into multiple calls. |
| **Destination can be any level** | Views can be moved to both root-level folders and sub-folders. |
| **No restriction on view type** | Tables, reports, and dashboards can all be moved. |
| **Dependency** | `folderId` must be obtained from Get Folder List. `viewIds` must be obtained from the Get View List API for the workspace. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7144 | The specified destination folder does not exist. | Verify the `folderId` using the Get Folder List API. |
| 7301 | User does not have permission. | Ensure the user is a Workspace Admin or has Create Folder permission on the workspace. |
| 7319 | One or more view IDs do not belong to the specified workspace. | Ensure all view IDs in `viewIds` belong to the workspace identified by `<workspace-id>`. |

---

## 8. Make Default Folder

Sets the specified folder as the default folder for the workspace. The previous default folder (if any) loses its default status. Every workspace has exactly one default folder at all times.

| Attribute | Value |
|-----------|-------|
| **Method** | PUT |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/folders/<folder-id>/default` |
| **OAuth Scope** | `ZohoAnalytics.modeling.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace, or any user with Create Folder permission on the workspace. |

> This API has no CONFIG parameter.

### Sample Requests

**Case 1 — Set a top-level folder as the default**

```http
PUT /restapi/v2/workspaces/466206000000071000/folders/7617000071955001/default HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Set a sub-folder as the default**

```http
PUT /restapi/v2/workspaces/466206000000071000/folders/7617000071955003/default HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 3 — White label portal user setting the default folder**

```http
PUT /restapi/v2/workspaces/466206000000071000/folders/7617000071955001/default HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.cccccc.dddddd
ZANALYTICS-ORGID: 700000123456
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

```
HTTP/1.1 204 No Content
```

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Make Default Folder returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |
| **Replaces the current default** | The previously marked default folder immediately loses its `isDefault: true` status. There is always exactly one default folder per workspace. |
| **Idempotent** | Calling this API on a folder that is already the default succeeds without error and makes no changes. |
| **No request body** | This API requires no CONFIG parameter. The folder is identified solely by `<folder-id>` in the URL. |
| **Verify with Get Folder List** | After calling this API, use Get Folder List to confirm `isDefault: true` is on the correct folder. |
| **Dependency** | `<folder-id>` in the URL must be obtained from Get Folder List. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7144 | The specified folder does not exist. | Verify the folder ID using the Get Folder List API. |
| 7301 | User does not have permission. | Ensure the user is a Workspace Admin or has Create Folder permission on the workspace. |

---

## Appendix A: Common HTTP Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | **Mandatory** | OAuth 2.0 bearer token in the format `Zoho-oauthtoken <token>`. |
| `ZANALYTICS-ORGID` | **Mandatory** | The Organisation ID of the workspace. Identifies the Zoho Analytics organisation that owns the workspace. |

> **White Label / Client Portal:** For custom-domain (portal) requests, use the portal's domain as the `Host` instead of `analyticsapi.zoho.com`. The `ZANALYTICS-ORGID` header is still required.

---

## Appendix B: OAuth Scope Summary

| API | OAuth Scope |
|-----|-------------|
| Get Folder List | `ZohoAnalytics.metadata.read` |
| Create Folder | `ZohoAnalytics.modeling.create` |
| Rename Folder | `ZohoAnalytics.modeling.update` |
| Delete Folder | `ZohoAnalytics.modeling.delete` |
| Change Folder Hierarchy | `ZohoAnalytics.modeling.update` |
| Change Folder Position | `ZohoAnalytics.modeling.update` |
| Move Views To Folder | `ZohoAnalytics.modeling.update` |
| Make Default Folder | `ZohoAnalytics.modeling.update` |

---

## Appendix C – API-Specific Notes and Behaviours

This appendix consolidates key behaviours, edge cases, and inter-API dependency information for each Workspace Folders API.

### Get Folder List

- **Primary source of IDs:** This is the entry point for all other folder APIs. `folderId` values obtained here are used as `<folder-id>` in the URL for every other folder operation, and as `parentFolderId` (Create Folder / Change Folder Hierarchy), `referenceFolderId` (Change Folder Position), and `folderId` (Move Views To Folder).
- **Shared-user filtering:** Shared Users and Group Members receive a filtered list. If a view is inside a sub-folder and that view is accessible to the user, both the sub-folder and its parent are included. An empty `folders` array means the user has access to no views in the workspace.
- **`parentFolderId: "-1"`** indicates a root-level folder (no parent). The value is always returned as a string.

### Create Folder

- **Response gap:** Only `folderId` is returned in the response. To retrieve the full folder record (name, description, index, isDefault), call Get Folder List after creation.
- **`makeDefaultFolder=true`:** Equivalent to calling Make Default Folder immediately after creation. The previous default folder loses its status.
- **Nesting rule:** Only one level of sub-folders is supported. `parentFolderId` must reference a root-level folder.
- **Dependency:** `parentFolderId` (when creating a sub-folder) → Get Folder List.

### Rename Folder

- **`folderDesc` reset behaviour (critical):** Omitting `folderDesc` permanently clears the existing description to an empty string. Always read the current `folderDesc` from Get Folder List before calling this API if you want to preserve it.
- **Dependency:** `<folder-id>` → Get Folder List. Current `folderDesc` value → Get Folder List.

### Delete Folder

- **Views survive by default:** With `deleteDependentViews=false` (the default), views inside the deleted folder are moved to the workspace root — they are not lost.
- **Error 7277 guard:** If any table inside the folder has dependent child views (reports/dashboards built on top of it), deletion is blocked unless `deleteDependentViews=true`.
- **Dependency:** `<folder-id>` → Get Folder List.

### Change Folder Hierarchy

- **`hierarchy` values are strict:** `0` = promote sub-folder to root; `1` = nest under a parent. Any other value immediately returns error 8119.
- **`parentFolderId` must be root-level:** You cannot chain nesting — the target parent must itself be a top-level folder.
- **Dependency:** `<folder-id>` and `parentFolderId` (when `hierarchy=1`) → Get Folder List.

### Change Folder Position

- **Position result:** The target folder is placed immediately above `referenceFolderId`. Use Get Folder List to verify `folderIndex` values after the call.
- **Same-level constraint:** Both folders must be at the same hierarchy level (both root-level, or both sub-folders of the same parent).
- **Dependency:** `<folder-id>` and `referenceFolderId` → Get Folder List.

### Move Views To Folder

- **Atomic operation:** The entire batch succeeds or fails together. A single invalid `viewId` (error 7319) causes zero views to be moved.
- **Dependency:** `folderId` → Get Folder List. `viewIds` → Get View List API for the workspace.

### Make Default Folder

- **Idempotent:** Safe to call even if the folder is already the default — no error is returned.
- **One default at a time:** The workspace always has exactly one default folder; the previous default loses its status immediately upon this call.
- **Dependency:** `<folder-id>` → Get Folder List.

---

## Appendix D – General Response Payload Notes

| Field / Behaviour | Detail |
|-------------------|--------|
| **`parentFolderId` type** | Always returned as a string (e.g. `"-1"`, `"7617000071955001"`), not a numeric. `"-1"` means root level. |
| **`folderIndex` meaning** | Sort order within the folder's hierarchy level. The default folder uses `-1`. Non-default folders are sorted in ascending order of `folderIndex`. |
| **`isDefault` uniqueness** | Exactly one folder per workspace has `isDefault: true` at any given time. |
| **Subfolder nesting limit** | Exactly one level of nesting is supported. A root-level folder can have sub-folders; sub-folders cannot have children. |
| **Create Folder response** | Returns only `folderId`. All other fields (`folderName`, `folderDesc`, `folderIndex`, `isDefault`, `parentFolderId`) are obtained by calling Get Folder List. |
| **Rename Folder `folderDesc` reset** | Omitting `folderDesc` in a Rename request permanently clears the description. This is intentional API behaviour, not a bug. |
