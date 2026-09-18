# Zoho Analytics V2 REST API — Sharing

This document covers the APIs for sharing views/reports with individual users or groups, updating and inspecting existing share configurations, removing shares, and checking a user's own effective permissions on a view.

## What is "Sharing" in Zoho Analytics?

A view (table, report, dashboard, etc.) can be made accessible to other users of the same organization (or, for Client Portal/White Label workspaces, users of a portal domain) without transferring ownership. Sharing is done either:

- **Directly to individual users** — by email address (`emailIds`), or
- **To a group** — a named collection of users (`groupIds`), managed via the [Workspace Groups APIs](WORKSPACE_GROUPS_API_DOC_INFO.md).

Each share grants a specific **permission set** (read, export, row-level write actions, drill-down, discussion, etc. — see [`permissions` Fields](#permissions-fields)), and can optionally restrict the shared user to specific **columns** and/or a row-level **filter criteria**.

---

## Index

| # | API Name | Method | URL |
|---|----------|--------|-----|
| 1 | [Get Workspace Shared Details](#1-get-workspace-shared-details) | GET | `/restapi/v2/workspaces/<workspace-id>/share` |
| 2 | [Share Views](#2-share-views) | POST | `/restapi/v2/workspaces/<workspace-id>/share` |
| 3 | [Update Shared Details](#3-update-shared-details) | PUT | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/share` |
| 4 | [Get Shared Details](#4-get-shared-details) | GET | `/restapi/v2/workspaces/<workspace-id>/share/shareddetails` |
| 5 | [Remove Shared Views](#5-remove-shared-views) | DELETE | `/restapi/v2/workspaces/<workspace-id>/share` |
| 6 | [Get My Permissions](#6-get-my-permissions) | GET | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/share/userpermissions` |

---

## 1. Get Workspace Shared Details

Returns a consolidated view of every share that exists in the workspace — grouped by user, by group, plus any public/private-link shares — in a single call. Intended for workspace-level share auditing/administration.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/share` |
| **OAuth Scope** | `ZohoAnalytics.share.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin of the specified workspace. This API is restricted to workspace owners — there is no permission-based alternative. |

> This API has no CONFIG parameter.

### Sample Requests

**Case 1 — Standard workspace**

```http
GET /restapi/v2/workspaces/137687000271334001/share HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Client Portal / White Label workspace**

```http
GET /restapi/v2/workspaces/137687000271334009/share HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
```

### Sample Responses

**HTTP 200 OK — No shares exist yet**

```json
{
    "status": "success",
    "summary": "Get share info",
    "data": {
        "userShareInfo": [],
        "groupShareInfo": [],
        "publicShareInfo": {},
        "privateLinkShareInfo": {}
    }
}
```

**HTTP 200 OK — Workspace with a group share (Client Portal / White Label)**

```json
{
    "status": "success",
    "summary": "Get share info",
    "data": {
        "userShareInfo": [],
        "groupShareInfo": [
            {
                "groupId": "38190000004189049",
                "groupName": "Group",
                "groupDesc": "",
                "groupMembers": ["melba.s+wl_groupuser1t0@zohotest.com"],
                "views": [
                    {
                        "viewId": "38190000004178369",
                        "viewName": "ChartWL1",
                        "sharedBy": "melba.s+wldbadmint0@zohotest.com",
                        "permissions": {
                            "read": true,
                            "export": true,
                            "vud": true,
                            "addRow": false,
                            "updateRow": false,
                            "deleteRow": false,
                            "deleteAllRows": false,
                            "importAppend": false,
                            "importAddOrUpdate": false,
                            "importDeleteAllAdd": false,
                            "importDeleteUpdateAdd": false,
                            "drillDown": true,
                            "share": false,
                            "discussion": false,
                            "insight": false
                        }
                    },
                    {
                        "viewId": "38190000004178370",
                        "viewName": "PivotWL1",
                        "sharedBy": "melba.s+wldbadmint0@zohotest.com",
                        "permissions": {
                            "read": true,
                            "export": true,
                            "vud": false,
                            "addRow": true,
                            "updateRow": true,
                            "deleteRow": true,
                            "deleteAllRows": true,
                            "importAppend": true,
                            "importAddOrUpdate": true,
                            "importDeleteAllAdd": true,
                            "importDeleteUpdateAdd": true,
                            "drillDown": false,
                            "share": true,
                            "discussion": true,
                            "insight": false
                        }
                    }
                ]
            }
        ],
        "publicShareInfo": {},
        "privateLinkShareInfo": {}
    }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `userShareInfo` | JSONArray | One entry per user the workspace's views are shared with. Each entry has `emailId`, `views[]` (each with `viewId`, `viewName`, `sharedBy`, `permissions`). Empty if no views are shared to individual users. |
| `groupShareInfo` | JSONArray | One entry per group the workspace's views are shared with. Each entry has `groupId`, `groupName`, `groupDesc`, `groupMembers[]` (member email addresses), and `views[]` (same shape as in `userShareInfo`). Empty if no views are shared to groups. |
| `publicShareInfo` | JSONObject | Public/anyone-with-link share configuration for the workspace's views, if any. Empty object `{}` if no view is publicly shared. |
| `privateLinkShareInfo` | JSONObject | Private-link ("share via secret URL") share configuration, if any. Empty object `{}` if none configured. |
| `views[].permissions` | JSONObject | The permission set granted for that specific view. See [`permissions` Fields](#permissions-fields) — note that `vudSelectedColumns`, `drillThrough`, `drillActions`, `accessAdminPresets`, and `createPreset` are omitted from this particular response and only appear in Get Shared Details / Get My Permissions responses. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Workspace-level, not view-level** | Unlike [Get Shared Details](#4-get-shared-details), this API requires no `viewIds` — it returns share data for **every** shared view in the workspace in one response. |
| **Owner-only visibility** | Only the Workspace Admin (or Account/Organization Admin) can call this — a regular shared user cannot use it to see who else a view is shared with. |
| **Empty arrays/objects on no data** | Fields are always present in the response but are empty (`[]` or `{}`) rather than omitted when nothing of that share type exists. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7301 | `SECURITY_NOT_PERMITTED` — User does not have permission to view workspace share info. | Ensure the user is an Account Admin, Organization Admin, or Workspace Admin. |

---

## 2. Share Views

Shares one or more views with a set of users and/or groups, with a specific permission set, optional column/row restrictions, and optional invite email.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/share` |
| **OAuth Scope** | `ZohoAnalytics.share.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user with Share permission on all of the specified `viewIds`. |

### CONFIG Parameters

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `viewIds` | JSONArray of String/Long | **Yes** | — | IDs of the views to share (1–1000 entries). All views must belong to the same workspace. |
| `emailIds` | JSONArray of String | No* | — | Email addresses of the users to share to. At least one of `emailIds` or `groupIds` must be supplied. |
| `groupIds` | JSONArray of String/Long | No* | — | IDs of the [workspace groups](WORKSPACE_GROUPS_API_DOC_INFO.md) to share to. At least one of `emailIds` or `groupIds` must be supplied. |
| `permissions` | JSONObject | No | all `false` except as noted | The permission set to grant. `read` **must be `true`** (error 8074 `READ_PERM_SHOULD_BE_TRUE_FOR_SHARING` otherwise). See [`permissions` Fields](#permissions-fields). |
| `columns` | JSONArray | No | — | Restricts the shared user to specific columns per table/view. See [`columns` / `vudColumns` / `drillColumns` Fields](#columns--vudcolumns--drillcolumns-fields). Only meaningful when sharing a **single** view (error 7543 if combined with multi-view share). |
| `includeAllColsForVUD` | Boolean | No | `false` | If `true`, the shared user can view all columns in "View Underlying Data" mode instead of only the columns in `vudColumns`. |
| `vudColumns` | JSONArray | No | — | Restricts which columns are visible in "View Underlying Data" mode. Same shape as `columns`. |
| `drillColumns` | JSONArray | No | — | Restricts which columns are visible when the shared user drills down. Same shape as `columns`. |
| `criteria` | String | No | — | Row-level filter criteria applied only for this shared user/group (e.g., `"Region"='East'`). Not supported when sharing multiple views at once (error 7541 `FILTER_CRITERIA_NOT_SUPPORTED_FOR_MULTI_VIEW_SHARE`). |
| `inheritParentFilterCriteria` | Boolean | No | `false` | If `true`, the shared user also inherits any filter criteria already applied on the view for the sharer, in addition to `criteria`. |
| `domainName` | String | No | — | Client Portal/White Label domain to scope this share to. Only relevant when the calling user is a domain admin managing a specific portal domain's users; omit for standard sharing. |
| `inviteMail` | Boolean | No | `false` | If `true`, sends an invite/notification email to the newly shared users. |
| `inviteMailCCMe` | Boolean | No | `false` | If `true` (and `inviteMail` is `true`), CCs the sharer on the invite email. |
| `mailSubject` | String | No | Default system subject | Custom subject line for the invite email. Only used if `inviteMail` is `true`. |
| `mailMessage` | String | No | Default system message | Custom body text for the invite email. Only used if `inviteMail` is `true`. |
| `validateSystemTags` | Boolean | No | `true` | If `true`, the share is blocked with a confirmation-required error (`8241`) when any view in `viewIds` carries a restricted **DATA_WARNING** system tag. Pass `false` to acknowledge the warning and share anyway. |

\* At least one of `emailIds` or `groupIds` is required; both may be supplied together to share to users and groups in the same call.

#### `permissions` Fields

| Field | Type | Default | Description |
|-------|------|---------|--------------|
| `read` | Boolean | `false` | View/read access. **Must be `true`** — sharing with only write/other permissions and `read=false` is rejected (error 8074). |
| `export` | Boolean | `false` | Allows exporting the view's data. |
| `vud` | Boolean | `false` | Allows "View Underlying Data" (drilling into the raw rows behind an aggregated report). |
| `drillDown` | Boolean | `false` | Allows drilling down into related/child views. |
| `addRow` | Boolean | `false` | Allows adding new rows (tables/imports only). |
| `updateRow` | Boolean | `false` | Allows updating existing rows. |
| `deleteRow` | Boolean | `false` | Allows deleting individual rows. |
| `deleteAllRows` | Boolean | `false` | Allows deleting **all** rows in the table at once. |
| `importAppend` | Boolean | `false` | Allows importing data in "Append" mode. |
| `importAddOrUpdate` | Boolean | `false` | Allows importing data in "Add or Update" mode. |
| `importDeleteAllAdd` | Boolean | `false` | Allows importing data in "Truncate and Add" mode. |
| `importDeleteUpdateAdd` | Boolean | `false` | Allows importing data in "Update and Add" (delta) mode. |
| `share` | Boolean | `false` | Allows the shared user to re-share the view with others. Read-Only (embedded/client-portal) users cannot be granted this together with any write permission (error 7545 `SHARE_AND_WRITE_PERMISSIONS_NOT_ALLOWED_FOR_RO_USERS`). |
| `vudSelectedColumns` | Boolean | `false` | Restricts "View Underlying Data" to only the columns listed in `vudColumns` (paired with `vud`). |
| `discussion` | Boolean | `false` | Allows posting/viewing discussion comments on the view. |
| `insight` | Boolean | `false` | Allows viewing AI-generated insights for the view. |
| `drillThrough` | Boolean | `false` | Allows drill-through actions from this view into linked views. |
| `drillActions` | Boolean | `false` | Allows executing configured drill actions. |
| `accessAdminPresets` | Boolean | `false` | Allows the shared user to view/apply admin-defined report presets. |
| `createPreset` | Boolean | `false` | Allows the shared user to create their own report presets. |

#### `columns` / `vudColumns` / `drillColumns` Fields

Each is a JSONArray of objects, one per underlying table referenced by the view:

| Field | Type | Mandatory | Description |
|-------|------|-----------|--------------|
| `tableName` | String | **Yes** | Name of the table whose columns are being restricted. |
| `columnNames` | JSONArray of String | **Yes** | Column names from `tableName` that the shared user is allowed to see. |

### Sample Requests

**Case 1 — Share a single view with one user, read + export only**

```http
POST /restapi/v2/workspaces/137687000271334001/share HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "viewIds": ["137687000006991601"],
    "emailIds": ["jane.doe@example.com"],
    "permissions": {
        "read": true,
        "export": true
    },
    "inviteMail": true
}
```

**Case 2 — Share to a group with a row-level filter and VUD access**

```http
POST /restapi/v2/workspaces/137687000271334001/share HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "viewIds": ["137687000006991601"],
    "groupIds": ["137687000006991700"],
    "permissions": {
        "read": true,
        "export": true,
        "vud": true
    },
    "criteria": "\"Region\"='East'",
    "inheritParentFilterCriteria": false
}
```

**Case 3 — White Label / Client Portal: share to a portal-domain user with write access**

```http
POST /restapi/v2/workspaces/137687000271334009/share HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "viewIds": ["137687000006991777"],
    "emailIds": ["client.user@portalcustomer.com"],
    "permissions": {
        "read": true,
        "export": true,
        "addRow": true,
        "updateRow": true
    },
    "domainName": "portal.customdomain.com"
}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Share Views returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |
| **`read` is a hard requirement** | Every share must grant at least `read`; there is no "write-only" share. |
| **Single-view restrictions** | `columns`, `vudColumns`, `drillColumns`, and `criteria` only apply when exactly one view is in `viewIds` — combining them with a multi-view share fails (errors 7541/7543). |
| **Re-sharing an already-shared view** | Sharing a view/user (or view/group) combination that is already shared returns error 7321/7322 rather than silently updating it — use [Update Shared Details](#3-update-shared-details) to modify an existing share. |
| **Dependency** | `viewIds` → [Get Views](VIEW_OPERATIONS_API_DOC_INFO.md); `groupIds` → [Get Group List](WORKSPACE_GROUPS_API_DOC_INFO.md#1-get-group-list). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 8074 | `READ_PERM_SHOULD_BE_TRUE_FOR_SHARING` — `permissions.read` was `false` or omitted. | Set `permissions.read` to `true`. |
| 7321 | `VIEW_ALREADY_SHARED` — The view is already shared with this user. | Use Update Shared Details to modify the existing share instead. |
| 7322 | `VIEW_ALREADY_SHARED` (group form) — The view is already shared with this group. | Use Update Shared Details to modify the existing share instead. |
| 7323 | `CANNOT_SHARED_TO_OBJOWNER` — Attempted to share the view with its own owner. | Remove the owner's email/group from the share request. |
| 7307 | `OWNER_CANNOT_SHARE_HIMSELF` — The sharer attempted to share a view to themselves. | Remove the sharer's own email from `emailIds`. |
| 7320 | `CANNOT_SHARETO_SELF` — Same as above (alternate path). | Same as above. |
| 7541 | `FILTER_CRITERIA_NOT_SUPPORTED_FOR_MULTI_VIEW_SHARE` — `criteria` supplied with more than one `viewIds` entry. | Share one view at a time when using row-level `criteria`. |
| 7543 | `VUD_OR_DRILL_COLUMNS_EDIT_NOT_SUPPORTED_FOR_MULTI_VIEW_SHARE` — `vudColumns`/`drillColumns` supplied with more than one view. | Share one view at a time when restricting VUD/drill columns. |
| 7545 | `SHARE_AND_WRITE_PERMISSIONS_NOT_ALLOWED_FOR_RO_USERS` — A Read-Only/embedded user was granted `share` together with a write permission. | Do not combine `share: true` with write permissions for Read-Only users. |
| 7533 | `CANNOT_SHARE_OBJECT_TO_GROUP` — The view's type does not support group sharing. | Share to individual `emailIds` instead. |
| 7535 | `CANNOT_SHARE_TO_MEMBERS_NOT_PART_OF_ORG` — One or more `emailIds` do not belong to the organization. | Verify the recipients are valid organization/portal users. |
| 7549 | `CANNOT_SHARE_TO_CUSTOMROLE_USER` — Attempted to share directly to a user who only has a custom-role-based org-level permission. | Share via the appropriate group/role mechanism instead. |
| 8029 | `SHARE_INVALID_EMAIL_ADDRESS` — One or more `emailIds` entries is not a valid email address. | Correct the malformed email address(es). |
| 8085 / 8086 | `SHAREDTO_EXTERNAL_DOMAIN_NOT_ALLOWED` — Sharing to an email outside the allowed domain(s) is disabled by org policy. | Share only to users within the permitted domain(s), or contact the Org Admin to adjust the policy. |
| 8241 | `SYSTEM_TAG_DATA_WARNING_V2_VALIDATION_CONFIRMATION` (HTTP 409) — A view being shared carries a restricted DATA_WARNING system tag. | Review the warning, then resend with `"validateSystemTags": false` to confirm. |
| 8080 | `INVALID_JSON_CONFIGURATION` — CONFIG is malformed or missing a required field. | Validate the CONFIG JSON against the parameter table above. |
| 7301 | `SECURITY_NOT_PERMITTED` — User does not have Share permission on one or more `viewIds`. | Ensure the user is an Account Admin, Organization Admin, or Workspace Admin, or has Share permission on all specified views. |

---

## 3. Update Shared Details

Updates the permission set, column/row restrictions, or filter criteria of an **existing** share on a single view, for the users/groups specified.

| Attribute | Value |
|-----------|-------|
| **Method** | PUT |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/share` |
| **OAuth Scope** | `ZohoAnalytics.share.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user with Share permission on `<view-id>`. |

### CONFIG Parameters

Same structure as [Share Views](#2-share-views) **except there is no `viewIds` key** — the view is identified by `<view-id>` in the URL, and there are no `inviteMail`/`inviteMailCCMe`/`mailSubject`/`mailMessage` fields (no invite email is sent on an update).

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `emailIds` | JSONArray of String | No* | — | Email addresses whose share on `<view-id>` should be updated. |
| `groupIds` | JSONArray of String/Long | No* | — | Group IDs whose share on `<view-id>` should be updated. |
| `permissions` | JSONObject | No | unchanged if omitted | New permission set to apply. See [`permissions` Fields](#permissions-fields). `read` must remain `true`. |
| `columns` | JSONArray | No | unchanged if omitted | See [`columns` Fields](#columns--vudcolumns--drillcolumns-fields). |
| `includeAllColsForVUD` | Boolean | No | unchanged if omitted | If `true`, the shared user can view all columns in "View Underlying Data" mode instead of only the columns in `vudColumns`. Same semantics as in [Share Views](#2-share-views). |
| `vudColumns` | JSONArray | No | unchanged if omitted | Restricts which columns are visible in "View Underlying Data" mode. Same shape as `columns` — see [Share Views](#2-share-views). |
| `drillColumns` | JSONArray | No | unchanged if omitted | Restricts which columns are visible when the shared user drills down. Same shape as `columns` — see [Share Views](#2-share-views). |
| `criteria` | String | No | unchanged if omitted | New row-level filter criteria. Pass an empty string to clear an existing criteria. |
| `inheritParentFilterCriteria` | Boolean | No | unchanged if omitted | If `true`, the shared user also inherits any filter criteria already applied on the view for the sharer, in addition to `criteria`. Same semantics as in [Share Views](#2-share-views). |
| `domainName` | String | No | — | Client Portal/White Label domain to scope this update to. |
| `validateSystemTags` | Boolean | No | `true` | If `true`, the update is blocked with a confirmation-required error (`8241`) when `<view-id>` carries a restricted **DATA_WARNING** system tag. Pass `false` to acknowledge the warning and update anyway. Same semantics as in [Share Views](#2-share-views). |

\* At least one of `emailIds` or `groupIds` is required, identifying which existing share(s) on `<view-id>` to update.

### Sample Requests

**Case 1 — Grant export access to an already-shared user**

```http
PUT /restapi/v2/workspaces/137687000271334001/views/137687000006991601/share HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "emailIds": ["jane.doe@example.com"],
    "permissions": {
        "read": true,
        "export": true
    }
}
```

**Case 2 — Client Portal: update a group's share to remove write access**

```http
PUT /restapi/v2/workspaces/137687000271334009/views/137687000006991777/share HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "groupIds": ["137687000006991790"],
    "permissions": {
        "read": true,
        "export": true,
        "addRow": false,
        "updateRow": false
    },
    "domainName": "portal.customdomain.com"
}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Update Shared Details returns a bare HTTP `204 No Content` on success. |
| **View must already be shared** | This API modifies an existing share; it does not create a new one — if the user/group is not currently shared on `<view-id>`, error 8032 `VIEW_NOT_SHARED` (or 8150 for groups) is returned. Use Share Views to create the share first. |
| **Partial update semantics** | Any field omitted from CONFIG leaves that aspect of the share unchanged; only supplied fields are applied. |
| **Dependency** | [Get Shared Details](#4-get-shared-details) → identify the current share state → Update Shared Details. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 8032 | `VIEW_NOT_SHARED` — The view is not currently shared with the specified user. | Share the view first via Share Views. |
| 8150 | `VIEW_NOT_SHARED_TO_GROUP` — The view is not currently shared with the specified group. | Share the view to this group first via Share Views. |
| 8074 | `READ_PERM_SHOULD_BE_TRUE_FOR_SHARING` — `permissions.read` was explicitly set to `false`. | Keep `permissions.read` as `true`. |
| 7545 | `SHARE_AND_WRITE_PERMISSIONS_NOT_ALLOWED_FOR_RO_USERS` — A Read-Only user was granted `share` together with a write permission. | Do not combine `share: true` with write permissions for Read-Only users. |
| 7542 | `FILTER_CRITERIA_NOT_PERMITTED_FOR_SHARED_USER` — `criteria` update is not permitted for this share type. | Remove or adjust the `criteria` field. |
| 8241 | `SYSTEM_TAG_DATA_WARNING_V2_VALIDATION_CONFIRMATION` (HTTP 409) — `<view-id>` carries a restricted DATA_WARNING system tag. | Review the warning, then resend with `"validateSystemTags": false` to confirm. |
| 8080 | `INVALID_JSON_CONFIGURATION` — CONFIG is malformed or missing a required field. | Validate the CONFIG JSON against the parameter table above. |
| 7301 | `SECURITY_NOT_PERMITTED` — User does not have Share permission on `<view-id>`. | Ensure the user is an Account Admin, Organization Admin, or Workspace Admin, or has Share permission on the view. |

---

## 4. Get Shared Details

Returns detailed share information — per user and per group, including permission booleans, a human-readable `permissionString`, filter criteria, and restricted columns — for one or more specific views.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/share/shareddetails` |
| **OAuth Scope** | `ZohoAnalytics.share.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user with Share permission on all of the specified `viewIds`. |

### CONFIG Parameters

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `viewIds` | JSONArray of String/Long | **Yes** | — | IDs of the views whose share details are to be fetched (1–1000 entries). |

### Sample Requests

**Case 1 — Get shared details for a single view**

```http
GET /restapi/v2/workspaces/137687000271334001/share/shareddetails?CONFIG={"viewIds":["320862000001361755"]} HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Get shared details for multiple views (Client Portal)**

```http
GET /restapi/v2/workspaces/137687000271334009/share/shareddetails?CONFIG={"viewIds":["320862000001361757","320862000001361759"]} HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
```

### Sample Responses

**HTTP 200 OK — Single view, shared to a user and a group**

```json
{
    "status": "success",
    "summary": "Get shared details for view",
    "data": {
        "sharedDetails": [
            {
                "viewId": "320862000001361755",
                "shareInfo": [
                    {
                        "sharedTo": "restapi_v2_shareduser@zohotest.com",
                        "sharedBy": "workspaceowner@zohotest.com",
                        "sharedToZuId": "64036387",
                        "permissionString": "Read Access, Export Data, Only Append Rows, Add or Update Rows, Share Views / Child Reports",
                        "permissions": {
                            "read": true,
                            "export": true,
                            "vud": false,
                            "addRow": false,
                            "updateRow": false,
                            "deleteRow": false,
                            "deleteAllRows": false,
                            "importAppend": true,
                            "importAddOrUpdate": true,
                            "importDeleteAllAdd": false,
                            "importDeleteUpdateAdd": false,
                            "share": true,
                            "drillDown": false,
                            "discussion": false,
                            "insight": false,
                            "accessAdminPresets": false,
                            "createPreset": false,
                            "drillThrough": false,
                            "drillActions": false
                        },
                        "criteria": "\"Region\"='East'",
                        "inheritParentFilterCriteria": "false",
                        "isInvalidCriteria": false,
                        "sharedColumns": [],
                        "vudColumns": [],
                        "drillColumns": [],
                        "isGroupShare": false,
                        "publicPermLevel": 0,
                        "isROUser": false
                    },
                    {
                        "sharedTo": "Group-1",
                        "sharedBy": "workspaceowner@zohotest.com",
                        "sharedToGroupId": "320862000001360842",
                        "permissionString": "Read Access, Export Data, Only Append Rows, Add or Update Rows, Share Views / Child Reports",
                        "permissions": {
                            "read": true,
                            "export": true,
                            "vud": false,
                            "addRow": false,
                            "updateRow": false,
                            "deleteRow": false,
                            "deleteAllRows": false,
                            "importAppend": true,
                            "importAddOrUpdate": true,
                            "importDeleteAllAdd": false,
                            "importDeleteUpdateAdd": false,
                            "share": true,
                            "drillDown": false,
                            "discussion": false,
                            "insight": false,
                            "accessAdminPresets": false,
                            "createPreset": false,
                            "drillThrough": false,
                            "drillActions": false
                        },
                        "criteria": "",
                        "inheritParentFilterCriteria": "false",
                        "isInvalidCriteria": false,
                        "sharedColumns": [],
                        "vudColumns": [],
                        "drillColumns": [],
                        "isGroupShare": true,
                        "publicPermLevel": 0,
                        "isROUser": false
                    }
                ]
            }
        ]
    }
}
```

**HTTP 200 OK — Multiple views requested in one call**

```json
{
    "status": "success",
    "summary": "Get shared details for view",
    "data": {
        "sharedDetails": [
            {
                "viewId": "320862000001361757",
                "shareInfo": [
                    {
                        "sharedTo": "restapi_v2_shareduser@zohotest.com",
                        "sharedBy": "workspaceowner@zohotest.com",
                        "sharedToZuId": "64036387",
                        "permissionString": "Read Access, Export Data, Only Append Rows, Add or Update Rows",
                        "permissions": {
                            "read": true,
                            "export": true,
                            "vud": false,
                            "addRow": false,
                            "updateRow": false,
                            "deleteRow": false,
                            "deleteAllRows": false,
                            "importAppend": true,
                            "importAddOrUpdate": true,
                            "importDeleteAllAdd": false,
                            "importDeleteUpdateAdd": false,
                            "share": false,
                            "drillDown": false,
                            "discussion": false,
                            "insight": false,
                            "accessAdminPresets": false,
                            "createPreset": false,
                            "drillThrough": false,
                            "drillActions": false
                        },
                        "criteria": "",
                        "inheritParentFilterCriteria": "false",
                        "isInvalidCriteria": false,
                        "sharedColumns": [],
                        "vudColumns": [],
                        "drillColumns": [],
                        "isGroupShare": false,
                        "publicPermLevel": 0,
                        "isROUser": false
                    }
                ]
            },
            {
                "viewId": "320862000001361759",
                "shareInfo": [
                    {
                        "sharedTo": "restapi_v2_shareduser@zohotest.com",
                        "sharedBy": "workspaceowner@zohotest.com",
                        "sharedToZuId": "64036387",
                        "permissionString": "Read Access, Export Data, Only Append Rows, Add or Update Rows",
                        "permissions": {
                            "read": true,
                            "export": true,
                            "vud": false,
                            "addRow": false,
                            "updateRow": false,
                            "deleteRow": false,
                            "deleteAllRows": false,
                            "importAppend": true,
                            "importAddOrUpdate": true,
                            "importDeleteAllAdd": false,
                            "importDeleteUpdateAdd": false,
                            "share": false,
                            "drillDown": false,
                            "discussion": false,
                            "insight": false,
                            "accessAdminPresets": false,
                            "createPreset": false,
                            "drillThrough": false,
                            "drillActions": false
                        },
                        "criteria": "",
                        "inheritParentFilterCriteria": "false",
                        "isInvalidCriteria": false,
                        "sharedColumns": [],
                        "vudColumns": [],
                        "drillColumns": [],
                        "isGroupShare": false,
                        "publicPermLevel": 0,
                        "isROUser": false
                    }
                ]
            }
        ]
    }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `sharedDetails` | JSONArray | One entry per requested `viewId`. |
| `sharedDetails[].viewId` | String | The view ID this entry describes. |
| `sharedDetails[].shareInfo` | JSONArray | One entry per user/group the view is shared with. |
| `shareInfo[].sharedTo` | String | Email address (for a user share) or group name (for a group share). |
| `shareInfo[].sharedBy` | String | Email address of the user who created/last modified this share. |
| `shareInfo[].sharedToZuId` | String | Zoho user ID of the recipient. Present only for user shares (`isGroupShare: false`); a value of `-10` indicates a portal/embedded user account. |
| `shareInfo[].sharedToGroupId` | String | Group ID of the recipient. Present only for group shares (`isGroupShare: true`). |
| `shareInfo[].permissionString` | String | Human-readable, comma-separated summary of the granted permissions — useful for display in UI without re-deriving it from the `permissions` booleans. |
| `shareInfo[].permissions` | JSONObject | Full permission set. See [`permissions` Fields](#permissions-fields). |
| `shareInfo[].criteria` | String | Row-level filter criteria applied for this share, if any. Empty string if none. |
| `shareInfo[].inheritParentFilterCriteria` | String (`"true"`/`"false"`) | Whether the shared user also inherits the sharer's own filter on the view. |
| `shareInfo[].isInvalidCriteria` | Boolean | `true` if the stored `criteria` expression is no longer valid (e.g., references a column that was deleted). |
| `shareInfo[].sharedColumns` | JSONArray | Column restrictions applied to this share, if any (empty if the shared user can see all columns). |
| `shareInfo[].vudColumns` | JSONArray | Column restrictions for "View Underlying Data" mode, if any. |
| `shareInfo[].drillColumns` | JSONArray | Column restrictions for drill-down, if any. |
| `shareInfo[].isGroupShare` | Boolean | `true` if this entry represents a share to a group rather than an individual user. |
| `shareInfo[].publicPermLevel` | Integer | Internal public-share permission level indicator; `0` for regular (non-public) shares. |
| `shareInfo[].isROUser` | Boolean | `true` if the recipient is a Read-Only (embedded/Client Portal) user. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **View-scoped, batched** | Unlike Get Workspace Shared Details, this API is scoped to the specific `viewIds` requested (not the whole workspace), and can fetch several views' share details in one call. |
| **Includes derived text** | `permissionString` is a ready-to-display summary — do not attempt to reconstruct it manually from the `permissions` booleans; use it directly if you only need to show the recipient a summary. |
| **`sharedToZuId` vs `sharedToGroupId`** | Only one of the two is present per `shareInfo` entry, depending on `isGroupShare`. |
| **Dependency** | [Get Views](VIEW_OPERATIONS_API_DOC_INFO.md) → `viewIds` → Get Shared Details. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 8080 | `INVALID_JSON_CONFIGURATION` — `viewIds` missing or malformed. | Supply a valid, non-empty `viewIds` JSONArray. |
| 7301 | `SECURITY_NOT_PERMITTED` — User does not have Share permission on one or more requested `viewIds`. | Ensure the user is an Account Admin, Organization Admin, or Workspace Admin, or has Share permission on all requested views. |

---

## 5. Remove Shared Views

Removes an existing share of one or more views from a set of users and/or groups, or removes **all** of a user's/group's shared views in the workspace at once.

| Attribute | Value |
|-----------|-------|
| **Method** | DELETE |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/share` |
| **OAuth Scope** | `ZohoAnalytics.share.delete` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | For removing specific `viewIds`: the authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user with Share permission on the specified views. For `removeAllViews: true`: the authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin of the workspace — this bulk option is restricted to workspace owners. |

### CONFIG Parameters

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `emailIds` | JSONArray of String | No* | — | Email addresses whose share should be removed. |
| `groupIds` | JSONArray of String/Long | No* | — | Group IDs whose share should be removed. |
| `viewIds` | JSONArray of String/Long | Conditionally required | — | IDs of the views to unshare. **Required when `removeAllViews` is `false`/omitted; must be omitted (empty) when `removeAllViews` is `true`** (error 8105 `REMOVESHARE_ALL_VIEWS_PRESENT` if both are supplied together). |
| `removeAllViews` | Boolean | No | `false` | If `true`, removes **every** view shared to the specified `emailIds`/`groupIds` in this workspace, instead of only the views in `viewIds`. |
| `domainName` | String | No | — | Client Portal/White Label domain to scope this removal to. |

\* At least one of `emailIds` or `groupIds` is required, identifying whose share(s) to remove.

### Sample Requests

**Case 1 — Remove a specific view's share from a user**

```http
DELETE /restapi/v2/workspaces/137687000271334001/share HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "emailIds": ["jane.doe@example.com"],
    "viewIds": ["137687000006991601"]
}
```

**Case 2 — Remove all views shared to a group (Workspace Admin only)**

```http
DELETE /restapi/v2/workspaces/137687000271334001/share HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "groupIds": ["137687000006991700"],
    "removeAllViews": true
}
```

**Case 3 — Client Portal: remove a specific view's share from a portal-domain user**

```http
DELETE /restapi/v2/workspaces/137687000271334009/share HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "emailIds": ["client.user@portalcustomer.com"],
    "viewIds": ["137687000006991777"],
    "domainName": "portal.customdomain.com"
}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Remove Shared Views returns a bare HTTP `204 No Content` on success. |
| **`viewIds` and `removeAllViews` are mutually exclusive** | Supplying `viewIds` together with `removeAllViews: true` is rejected (error 8105); supplying neither `viewIds` nor `removeAllViews: true` is also rejected (`REMOVESHARE_API_PARAMS`, error 8031). |
| **`removeAllViews` requires ownership** | Removing *all* of a user's/group's shares workspace-wide is a bulk administrative action restricted to the Workspace Admin (or Account/Organization Admin) — a regular user with only Share permission on individual views cannot use this flag. |
| **Not shared is not an error for bulk removal** | For `removeAllViews: true`, users/groups with no existing shares are simply skipped; for specific `viewIds`, unsharing a view/user combination that was never shared returns error 8032/8150. |
| **Dependency** | [Get Shared Details](#4-get-shared-details) → confirm the share exists → Remove Shared Views. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 8031 | `REMOVESHARE_API_PARAMS` — Neither `viewIds` nor `removeAllViews: true` was supplied. | Supply either a `viewIds` array or set `removeAllViews: true`. |
| 8105 | `REMOVESHARE_ALL_VIEWS_PRESENT` — Both `viewIds` and `removeAllViews: true` were supplied together. | Supply only one of the two — `viewIds` for a targeted removal, or `removeAllViews: true` alone for a bulk removal. |
| 8032 | `VIEW_NOT_SHARED` — The specified view is not currently shared with this user. | Verify the share exists via Get Shared Details before removing. |
| 8150 | `VIEW_NOT_SHARED_TO_GROUP` — The specified view is not currently shared with this group. | Verify the share exists via Get Shared Details before removing. |
| 8080 | `INVALID_JSON_CONFIGURATION` — CONFIG is malformed or missing a required field. | Validate the CONFIG JSON against the parameter table above. |
| 7533 | `CANNOT_SHARE_OBJECT_TO_GROUP` — The view's type does not support group-based sharing/unsharing. | Only applicable to user-based (`emailIds`) removal for this view type. |
| 7301 | `SECURITY_NOT_PERMITTED` — User lacks Share permission on the targeted view(s), or attempted `removeAllViews: true` without Workspace Admin privileges. | Ensure the user is an Account Admin, Organization Admin, or Workspace Admin (required for `removeAllViews`), or has Share permission on the specified views. |

---

## 6. Get My Permissions

Returns the effective permission set the **calling user** currently has on a specific view.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/share/userpermissions` |
| **OAuth Scope** | `ZohoAnalytics.share.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | Any authenticated user with at least Read-Only access to `<view-id>` (i.e., any user the view has been shared with, or the view's owner/Workspace Admin). |

> This API has no CONFIG parameter.

> **Deprecated alias:** `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/share/mypermissions` is the original path for this same API and continues to function, but is deprecated in favor of `/share/userpermissions`. New integrations should use `/share/userpermissions`.

### Sample Requests

**Case 1 — Current path**

```http
GET /restapi/v2/workspaces/137687000271334001/views/137687000006991601/share/userpermissions HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Deprecated alias (still functional)**

```http
GET /restapi/v2/workspaces/137687000271334001/views/137687000006991601/share/mypermissions HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

### Sample Responses

**HTTP 200 OK — Workspace Admin (full permissions)**

```json
{
    "status": "success",
    "summary": "Get user permissions",
    "data": {
        "permissions": {
            "read": true,
            "export": true,
            "vud": true,
            "addRow": true,
            "updateRow": true,
            "deleteRow": true,
            "deleteAllRows": true,
            "importAppend": true,
            "importAddOrUpdate": true,
            "importDeleteAllAdd": true,
            "importDeleteUpdateAdd": true,
            "drillDown": true,
            "share": true,
            "discussion": true,
            "insight": false
        }
    }
}
```

**HTTP 200 OK — Shared user with read-only + VUD + drill-down (Client Portal)**

```json
{
    "status": "success",
    "summary": "Get user permissions",
    "data": {
        "permissions": {
            "read": true,
            "export": true,
            "vud": true,
            "addRow": false,
            "updateRow": false,
            "deleteRow": false,
            "deleteAllRows": false,
            "importAppend": false,
            "importAddOrUpdate": false,
            "importDeleteAllAdd": false,
            "importDeleteUpdateAdd": false,
            "drillDown": true,
            "share": false,
            "discussion": false,
            "insight": false
        }
    }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `permissions` | JSONObject | The calling user's effective permission set on `<view-id>`. Same booleans as [`permissions` Fields](#permissions-fields); a Workspace Admin/owner is granted all applicable permissions as `true` by default. `accessAdminPresets` and `createPreset` may additionally appear as `true` for users with preset-related access even without other write permissions. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Self-service only** | This API always reports the *calling* user's own permissions — there is no parameter to check another user's permissions; use [Get Shared Details](#4-get-shared-details) (as the Workspace Admin) to inspect other users' shares. |
| **Two equivalent paths** | `/share/mypermissions` (deprecated) and `/share/userpermissions` (current) return an identical response — both map to the same underlying `getUserPermissions` implementation. |
| **Owner/Admin sees full access** | For a view's owner or the Workspace Admin, all applicable permission booleans are returned as `true` even though no explicit share record exists for them. |
| **Dependency** | [Get Views](VIEW_OPERATIONS_API_DOC_INFO.md) → `viewId` → Get My Permissions. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7301 | `SECURITY_NOT_PERMITTED` — The calling user has no access at all to `<view-id>` (view does not belong to the workspace, or user has neither ownership nor a share). | Verify `<view-id>` belongs to `<workspace-id>` and that the calling user has been shared this view. |

---

## Appendix A – Common HTTP Headers

| Header | Value | Required | Notes |
|--------|-------|----------|-------|
| `Authorization` | `Zoho-oauthtoken <oauth-token>` | **Mandatory** | OAuth 2.0 access token of the calling user. |
| `ZANALYTICS-ORGID` | Organisation ID | **Mandatory** for all APIs | Organisation ID of the workspace. |
| `Content-Type` | `application/x-www-form-urlencoded` | Required for POST/PUT with body | Not required for GET/DELETE (CONFIG is sent as a query parameter or, for Remove Shared Views, as form data). |

> **White Label / Client Portal:** All six sharing APIs are available via portal domain URLs when the caller has the required permission. The `domainName` CONFIG field (on Share Views, Update Shared Details, Remove Shared Views) is the mechanism used to scope a share operation to a specific portal domain's users when the calling user is a domain admin managing multiple portal domains — this is unrelated to the `ZANALYTICS-DEST-ORGID` header used elsewhere for cross-organization copy operations.

---

## Appendix B – OAuth Scope Summary

| API | Method | Scope |
|-----|--------|-------|
| Get Workspace Shared Details | GET | `ZohoAnalytics.share.read` |
| Share Views | POST | `ZohoAnalytics.share.create` |
| Update Shared Details | PUT | `ZohoAnalytics.share.update` |
| Get Shared Details | GET | `ZohoAnalytics.share.read` |
| Remove Shared Views | DELETE | `ZohoAnalytics.share.delete` |
| Get My Permissions | GET | `ZohoAnalytics.share.read` |

---

## Appendix C – API-Specific Notes and Behaviours

### Get Workspace Shared Details

- **Owner-only, workspace-wide snapshot.** This is the only sharing API that requires no `viewIds` at all — it enumerates every share (user, group, public, private-link) across the entire workspace in a single call, restricted to the Workspace Admin/owner.
- **Read-only sibling of Get Shared Details.** Use this API for a workspace-wide audit; use [Get Shared Details](#4-get-shared-details) when you need the fuller per-share fields (`permissionString`, `criteria`, `sharedColumns`, etc.) for a specific set of views.
- **Dependency chain:** Get Workspace List → Get Workspace Shared Details.

### Share Views

- **`read` is non-negotiable.** Every successful share grants at least read access — there is no supported "write-only" share configuration (error 8074 enforces this).
- **Single-view-only restrictions.** `columns`, `vudColumns`, `drillColumns`, and `criteria` are only usable when `viewIds` contains exactly one view — plan multi-view shares to use only the common, unrestricted permission set.
- **Re-sharing fails, does not upsert.** Calling this API again for a view/user (or view/group) pair that is already shared returns an error (7321/7322) instead of updating the share — always route modifications through [Update Shared Details](#3-update-shared-details).
- **Dependency chain:** [Get Views](VIEW_OPERATIONS_API_DOC_INFO.md) + [Get Group List](WORKSPACE_GROUPS_API_DOC_INFO.md#1-get-group-list) → Share Views → `<view-id>` share created.

### Update Shared Details

- **Modify-only, not upsert.** This API requires the share to already exist (errors 8032/8150 otherwise) — it is the counterpart to Share Views for existing shares, not a replacement for it.
- **No invite email support.** Unlike Share Views, there are no `inviteMail`/`mailSubject`/`mailMessage` fields — updating a share never re-sends an invitation.
- **Dependency chain:** [Get Shared Details](#4-get-shared-details) (fetch current state) → Update Shared Details (apply changes).

### Get Shared Details

- **The richest read API in this family.** Returns `permissionString` (ready for display), `criteria`, `isInvalidCriteria`, and column restrictions in addition to the raw `permissions` booleans — prefer this over Get Workspace Shared Details when you already know which `viewIds` you need details for.
- **Batchable.** Accepts multiple `viewIds` in one call, returning one `sharedDetails` entry per view — avoid looping per-view calls when auditing several views at once.
- **Dependency chain:** [Get Views](VIEW_OPERATIONS_API_DOC_INFO.md) → `viewIds` → Get Shared Details.

### Remove Shared Views

- **Two mutually exclusive modes.** Targeted removal (`viewIds`) is available to any user with Share permission on those views; bulk removal (`removeAllViews: true`) is restricted to the Workspace Admin/owner — mixing the two in one request is rejected (error 8105).
- **Idempotency caveat.** Removing a share that does not exist is an error (8032/8150) for targeted removal, but is silently skipped (no error) for bulk (`removeAllViews: true`) removal of users/groups with no shares.
- **Dependency chain:** [Get Shared Details](#4-get-shared-details) → confirm target share(s) → Remove Shared Views.

### Get My Permissions

- **Self-only, dual path.** Always reflects the caller's own access; `/share/mypermissions` is a deprecated alias retained for backward compatibility alongside the current `/share/userpermissions` path.
- **No admin override parameter.** There is intentionally no way to query another user's permissions through this endpoint — Workspace Admins must use [Get Shared Details](#4-get-shared-details) instead.
- **Dependency chain:** [Get Views](VIEW_OPERATIONS_API_DOC_INFO.md) → `viewId` → Get My Permissions.

---

## Appendix D – General Response Payload Notes

| Field / Behaviour | Detail |
|-------------------|--------|
| **Mutating APIs return 204 with no body** | Share Views, Update Shared Details, and Remove Shared Views all return HTTP **204 No Content** on success — treat the 2xx status code as the success indicator, never expect or parse a JSON body for these three APIs. |
| **`permissions` field set differs slightly by endpoint** | Get Workspace Shared Details' nested `views[].permissions` omits `vudSelectedColumns`, `drillThrough`, `drillActions`, `accessAdminPresets`, and `createPreset` (only present in Get Shared Details and Get My Permissions responses). Always code defensively for optional/absent permission keys rather than assuming a fixed schema across all six APIs. |
| **IDs are transmitted as strings** | `viewId`, `groupId`, `sharedToZuId`, `sharedToGroupId`, and all other ID-like fields are JSON strings in every response, even though they are numeric — always parse them as long/string, not as native JSON numbers, to avoid precision loss on large IDs. |
| **`criteria` / `inheritParentFilterCriteria` are always strings in Get Shared Details** | Even though `inheritParentFilterCriteria` is conceptually boolean, Get Shared Details serializes it as the string `"true"`/`"false"` rather than a native boolean — this differs from the CONFIG request format, where it is sent as a native boolean. |
| **Empty containers, not omitted fields** | `userShareInfo`, `groupShareInfo`, `sharedColumns`, `vudColumns`, `drillColumns`, etc. are always present in successful responses but empty (`[]`/`{}`) when there is nothing to report — do not treat their absence as an error condition (they are never absent). |
