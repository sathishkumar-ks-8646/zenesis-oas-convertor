# Zoho Analytics V2 REST API — Custom Roles

This document covers the four **Custom Role** REST APIs of Zoho Analytics — the APIs that define the named permission bundles an organization can grant to its users instead of the built-in roles.

## What a custom role is

A custom role is an **organization-scoped** definition made of three things:

| Part | What it decides |
|------|-----------------|
| `roleName` | What the role is called. |
| `accessType` | **Which kinds of view** the role can reach — dashboards only, reports and dashboards, or data as well. |
| `permissions` | **What the role can do** with the views it reaches, expressed as seven groups of boolean flags. |

The two halves are not independent. `accessType` sets a ceiling, and a permission that lies above that ceiling is rejected rather than ignored — a role limited to dashboards cannot be granted the right to add rows. Most of the validation in this family exists to enforce that relationship, which is why [The `accessType` Hierarchy](#the-accesstype-hierarchy) and [Permission Dependency Rules](#permission-dependency-rules) come before the API reference below.

> Custom roles define permissions; they do not assign them. Attaching a role to a user or to a workspace is done through the user- and workspace-management APIs, not here.

---

## Index

| # | API Name | Method | URL |
|---|----------|--------|-----|
| 1 | [Get Custom Roles](#1-get-custom-roles) | GET | `/restapi/v2/orgs/roles` |
| 2 | [Create Custom Role](#2-create-custom-role) | POST | `/restapi/v2/orgs/roles` |
| 3 | [Update Custom Role](#3-update-custom-role) | PUT | `/restapi/v2/orgs/roles/<role-id>` |
| 4 | [Delete Custom Role](#4-delete-custom-role) | DELETE | `/restapi/v2/orgs/roles/<role-id>` |

> Notes that apply to all four APIs:
> - All require the `ZANALYTICS-ORGID` header.
> - All are **disabled in Client Portal / White Label request contexts.** A request arriving through a custom domain is rejected with `7301` before any business logic runs.
> - All require the caller to be an **Account Admin or Organization Admin**, and require the custom-roles feature to be available — see [Permission Model](#permission-model).
> - There is no path parameter for the organization: the role always belongs to the organization named in `ZANALYTICS-ORGID`.
> - **Two APIs return a body; two return `204 No Content`.** See [Appendix D](#appendix-d--general-response-payload-notes).

---

## How the Four APIs Relate

[Create Custom Role](#2-create-custom-role) is the only source of a `roleId`, and [Get Custom Roles](#1-get-custom-roles) is the only way to read a role's current definition back — which matters, because [Update Custom Role](#3-update-custom-role) replaces permissions wholesale rather than merging them.

```
        2. Create Custom Role  ──►  data.roleId
                                        │
        ┌───────────────────────────────┼───────────────────────────────┐
        │                               │                               │
        ▼                               ▼                               ▼
  1. Get Custom Roles            3. Update Custom Role          4. Delete Custom Role
  (every role in the org,        (rename, and/or replace        (removes the role
   with full permissions)         accessType + permissions)      definition)
        │                               ▲
        │      read the current         │
        └──────  definition first ──────┘
               before a partial edit
```

| Relationship | Detail |
|--------------|--------|
| **`roleId` has exactly one origin** | [Create Custom Role](#2-create-custom-role) returns it as `data.roleId`. [Get Custom Roles](#1-get-custom-roles) returns it afterwards as `roles[].roleId`. It is the `<role-id>` path segment for [Update Custom Role](#3-update-custom-role) and [Delete Custom Role](#4-delete-custom-role). |
| **Get is the mandatory prelude to a permission edit** | [Update Custom Role](#3-update-custom-role) does **not** merge: whenever it is given `permissions`, the supplied object replaces the stored one entirely. To change one flag you must read the whole definition from [Get Custom Roles](#1-get-custom-roles), modify it, and send it back. |
| **Get returns exactly the shape Update accepts** | `roles[].accessType` and `roles[].permissions` from the read response can be edited and posted straight back as the `accessType` and `permissions` of an update. This round-trip is the intended editing workflow. |
| **A rename needs no read** | Sending only `roleName` to [Update Custom Role](#3-update-custom-role) leaves `accessType` and `permissions` untouched. It is the one edit that is safe without a prior read. |
| **`accessType` and `permissions` travel together on update** | Supplying one without the other fails with `7580`. They are validated as a pair because the permissions are only meaningful against an access type. |
| **Every write is validated against the same rule set** | [Create Custom Role](#2-create-custom-role) and [Update Custom Role](#3-update-custom-role) run identical checks, so the same eleven errors can come from either — see [Permission Dependency Rules](#permission-dependency-rules). |
| **Deleting a role does not delete its users** | [Delete Custom Role](#4-delete-custom-role) removes the definition. Reassigning users who held it is handled by the user-management APIs. |
| **Assignment lives elsewhere** | None of these four attaches a role to a user or a workspace. They manage the definition only. |
| **The feature must be enabled and in plan** | All four fail with `7301` when custom roles are not enabled for the organization, and [Get Custom Roles](#1-get-custom-roles) fails with `6142` when the subscription plan does not include them. |

### Typical sequences

**Define a new role and confirm it**

```
Create Custom Role {roleName, accessType, permissions}  →  data.roleId
   → Get Custom Roles                                   →  confirm the stored definition
```

**Change one permission flag safely**

```
Get Custom Roles                    →  roles[] → pick the role → take accessType + permissions
   → flip the one flag in that object
   → Update Custom Role {accessType, permissions}       →  204
   → Get Custom Roles                                   →  verify
```

**Rename only**

```
Update Custom Role {"roleName": "Analysts (EMEA)"}      →  204
```

**Retire a role**

```
Get Custom Roles  →  roleId
   → Delete Custom Role                                 →  204
```

---

## The `accessType` Hierarchy

`accessType` is a single enum with three cumulative levels. Each level includes everything below it.

| Value | Reaches | Adds over the level below |
|-------|---------|---------------------------|
| `ALL_DASHBOARDS` | Dashboards only | — (the most restricted level) |
| `ALL_REPORTS_AND_DASHBOARDS` | Reports **and** dashboards | Reports, and the ability to manage data alerts |
| `ALL_DATA_REPORTS_AND_DASHBOARDS` | Tables, reports **and** dashboards | Underlying data — every data, design, table-creation, and datasource permission becomes available |

The level determines which permission groups may be switched on at all:

| Permission group | `ALL_DASHBOARDS` | `ALL_REPORTS_AND_DASHBOARDS` | `ALL_DATA_REPORTS_AND_DASHBOARDS` |
|------------------|:----------------:|:----------------------------:|:---------------------------------:|
| `interactionPermissions` | ✓ | ✓ | ✓ |
| `sharePermissions` | ✓ | ✓ | ✓ |
| `publishPermissions` — except `manageDataAlerts` | ✓ | ✓ | ✓ |
| `publishPermissions.manageDataAlerts` | – | ✓ | ✓ |
| `createPermissions.createFolder` | ✓ | ✓ | ✓ |
| `createPermissions` — `createTable`, `createQueryTable`, `createFormula` | – | – | ✓ |
| `dataPermissions` | – | – | ✓ |
| `designPermissions` | – | – | ✓ |
| `datasourcePermissions` | – | – | ✓ |

Switching on a permission marked `–` for the chosen level is an error, not a silent no-op. The specific code depends on the group — see [Permission Dependency Rules](#permission-dependency-rules).

---

## Permission Dependency Rules

Eleven rules are enforced on every [Create Custom Role](#2-create-custom-role) and [Update Custom Role](#3-update-custom-role) call. They run **before** anything is stored, so a rejected request changes nothing.

| # | Rule | Error |
|---|------|-------|
| 1 | `interactionPermissions.read` must be `true`. Always, at every access level. | `7579` |
| 2 | Any `dataPermissions` flag requires `accessType` = `ALL_DATA_REPORTS_AND_DASHBOARDS`. | `7573` |
| 3 | Any `datasourcePermissions` flag requires `accessType` = `ALL_DATA_REPORTS_AND_DASHBOARDS`. | `7584` |
| 4 | `designPermissions.designModify` requires `accessType` = `ALL_DATA_REPORTS_AND_DASHBOARDS`. | `7574` |
| 5 | `createTable`, `createQueryTable`, and `createFormula` require `accessType` = `ALL_DATA_REPORTS_AND_DASHBOARDS`. | `7575` |
| 6 | `publishPermissions.manageDataAlerts` requires `accessType` = `ALL_REPORTS_AND_DASHBOARDS` or `ALL_DATA_REPORTS_AND_DASHBOARDS`. | `7576` |
| 7 | `designPermissions.designModify` additionally requires **both** `sharePermissions.accessAdminPresets` and `sharePermissions.createPreset` to be `true`. | `7578` |
| 8 | `publishPermissions.manageEmailSchedules` requires `publishPermissions.export` to be `true`. | `7559` |
| 9 | `datasourcePermissions.useDatasource` requires `createPermissions.createTable` to be `true`. | `7585` |
| 10 | `editDatasource`, `syncData`, `useDatasource`, and `removeDatasource` each require `datasourcePermissions.viewDatasource` to be `true`. | `7586` |
| 11 | `dataPermissions.dataArchives` requires `accessType` = `ALL_DATA_REPORTS_AND_DASHBOARDS` **and every data permission to be enabled**. | `7577` |

> **Rule 1 is the one that catches people first.** `read` is not defaulted for you. A `permissions` object that omits `interactionPermissions` entirely — or sets `read` to `false` — is rejected with `7579` even if everything else is valid.

> **Rules 7, 8, 9, and 10 are cross-group dependencies.** They reach across the permission buckets, so a payload assembled group-by-group can look complete and still fail. Check them before sending: design modify pulls in two share permissions, email schedules pull in export, and the datasource group has its own internal prerequisites.

---

## Limitations

These are the limits that apply with **default settings**.

| Limitation | Value | Enforced by |
|------------|-------|-------------|
| **`roleName` length** | **1–30** characters. | `8507` |
| **`roleName` characters** | Letters, digits, spaces, underscore, and hyphen only. | `8509` |
| **`roleName` uniqueness** | Must be unique across the organization, including against built-in role names. | `7553` |
| **`permissions` size** | **5,000** characters serialized. | `8507` |
| **Each permission group's size** | **500** characters serialized. | `8507` |
| **`CONFIG` length** | **1,000,000** characters. | `8507` |
| **`accessType` values** | Exactly three; see [The `accessType` Hierarchy](#the-accesstype-hierarchy). | `8509` |
| **Bulk operations** | **Not supported.** Create, update, and delete each act on exactly one role per call. | — |
| **Role assignment** | **Not supported by these APIs.** They define roles; attaching them to users or workspaces is done elsewhere. | — |
| **Partial permission edits** | **Not supported.** [Update Custom Role](#3-update-custom-role) replaces the whole `permissions` object. | — |
| **Client Portal / White Label** | All four APIs are unavailable through a custom domain. | `7301` |
| **Feature availability** | The organization must have custom roles enabled and included in its plan. | `7301`, `6142` |

> **There is no partial permission update and no permission-level endpoint.** Every change to what a role can do means sending the complete `permissions` object again. Read it with [Get Custom Roles](#1-get-custom-roles) first; anything you leave out is switched off.

---

## Permission Model

| API | Who may call it |
|-----|-----------------|
| [Get Custom Roles](#1-get-custom-roles) | An Account Admin or Organization Admin. |
| [Create Custom Role](#2-create-custom-role) | An Account Admin or Organization Admin. |
| [Update Custom Role](#3-update-custom-role) | An Account Admin or Organization Admin. |
| [Delete Custom Role](#4-delete-custom-role) | An Account Admin or Organization Admin. |

No other role qualifies. A Workspace Admin, a View Owner, a user holding a custom role, and a shared user are all rejected with `7301`.

| Gate | Behaviour |
|------|-----------|
| **Custom roles must be enabled for the organization** | Otherwise every API fails with `7301`, even for an Account Admin. |
| **The plan must include custom roles** | Otherwise `6142`. |
| **Client Portal / White Label** | All four are unavailable through a custom domain and are rejected with `7301` before the role check runs. |
| **Authentication** | An absent or unusable token yields `7309`; an invalid or expired one yields `8535`. |

---

## Permission Groups

`permissions` is an object of seven groups. Every value inside a group is a boolean, and **an omitted flag is treated as `false`** — which is why an update must resend the complete object.

| Group | Governs | Requires `ALL_DATA_REPORTS_AND_DASHBOARDS` |
|-------|---------|:------------------------------------------:|
| `createPermissions` | Creating folders, tables, query tables, and formula columns | Partly — `createFolder` is available at every level |
| `dataPermissions` | Adding, changing, and importing rows | Yes |
| `designPermissions` | Changing a view's design | Yes |
| `interactionPermissions` | Viewing and exploring a view | No |
| `sharePermissions` | Re-sharing, discussions, private links, presets | No |
| `publishPermissions` | Export, email schedules, alerts, slideshows, public views | Partly — `manageDataAlerts` needs reports access |
| `datasourcePermissions` | Viewing and managing the datasource behind a table | Yes |

The complete key list for each group is in [Appendix E](#appendix-e--permission-reference).

---

## 1. Get Custom Roles

Returns every custom role defined in the organization, with its full permission definition.

| Attribute | Value |
|-----------|-------|
| **URL** | `/restapi/v2/orgs/roles` |
| **HTTP Method** | `GET` |
| **OAuth Scope** | `ZohoAnalytics.usermanagement.read` |
| **Mandatory Header** | `ZANALYTICS-ORGID` |
| **CONFIG** | This API takes no CONFIG fields |
| **Success Status** | `200 OK` with a JSON body |

This API takes no path parameters. The organization is identified by the `ZANALYTICS-ORGID` header.

### Sample Requests

```http
GET /restapi/v2/orgs/roles HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

There is nothing else to send.

### Sample Responses

**HTTP 200 OK — one role at the full access level**

```json
{
  "status": "success",
  "summary": "Get roles",
  "data": {
    "roles": [
      {
        "roleId": "320875000000477455",
        "roleName": "cr_tagging",
        "accessType": "ALL_DATA_REPORTS_AND_DASHBOARDS",
        "permissions": {
          "createPermissions": {
            "createTable": true,
            "createQueryTable": true,
            "createFolder": true,
            "createFormula": true
          },
          "dataPermissions": {
            "addRow": true,
            "modifyRow": true,
            "deleteRow": true,
            "importAppend": true,
            "importAddOrUpdate": true,
            "importDeleteAllAdd": true,
            "dataArchives": true
          },
          "designPermissions": {
            "designModify": true
          },
          "interactionPermissions": {
            "read": true,
            "insight": true,
            "vud": true,
            "drillDown": false,
            "drillThrough": false,
            "drillActions": false
          },
          "sharePermissions": {
            "share": true,
            "discussion": true,
            "privateLinks": true,
            "accessAdminPresets": true,
            "createPreset": true
          },
          "publishPermissions": {
            "export": true,
            "manageEmailSchedules": true,
            "allEmailSchedulesAccess": true,
            "manageDataAlerts": true,
            "allDataAlertsAccess": true,
            "createSlideshow": true,
            "publicViews": true
          },
          "datasourcePermissions": {
            "viewDatasource": false,
            "editDatasource": false,
            "syncData": false,
            "useDatasource": false,
            "removeDatasource": false
          }
        }
      }
    ]
  }
}
```

Note that **every group and every flag is present**, including the ones set to `false`. The response is a complete definition, not a diff.

**HTTP 200 OK — an organization with no custom roles**

```json
{
  "status": "success",
  "summary": "Get roles",
  "data": {
    "roles": []
  }
}
```

**HTTP 400 Bad Request — the plan does not include custom roles**

```json
{
  "status": "failure",
  "summary": "CUSTOMROLES_NOT_ALLOWED_IN_PLAN",
  "data": {
    "errorCode": 6142,
    "errorMessage": "Custom roles is not allowed in this plan."
  }
}
```

**HTTP 403 Forbidden — the caller is not an organization administrator**

```json
{
  "status": "failure",
  "summary": "SECURITY_NOT_PERMITTED",
  "data": {
    "errorCode": 7301,
    "errorMessage": "You do not have the permission to perform this operation."
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | String | `"success"` on success. |
| `summary` | String | `"Get roles"`. |
| `data` | Object | Wrapper. |
| `data.roles` | Array | Every custom role in the organization. Empty when none are defined. |
| `data.roles[].roleId` | String | ID of the role, **as a string**. The `<role-id>` for [Update Custom Role](#3-update-custom-role) and [Delete Custom Role](#4-delete-custom-role). |
| `data.roles[].roleName` | String | Display name of the role. |
| `data.roles[].accessType` | String | One of the three levels. See [The `accessType` Hierarchy](#the-accesstype-hierarchy). |
| `data.roles[].permissions` | Object | The complete permission definition, in seven groups. |
| `data.roles[].permissions.createPermissions` | Object | Creation flags — see [Appendix E](#appendix-e--permission-reference). |
| `data.roles[].permissions.dataPermissions` | Object | Row and import flags. |
| `data.roles[].permissions.designPermissions` | Object | Design-modification flag. |
| `data.roles[].permissions.interactionPermissions` | Object | Viewing and exploration flags. |
| `data.roles[].permissions.sharePermissions` | Object | Sharing, discussion, and preset flags. |
| `data.roles[].permissions.publishPermissions` | Object | Export, schedule, alert, and publishing flags. |
| `data.roles[].permissions.datasourcePermissions` | Object | Datasource management flags. |

Every leaf inside the seven groups is a JSON **boolean**.

### Notes & Behaviour

| Behaviour | Detail |
|-----------|--------|
| **It is the only way to read a role's definition** | There is no get-by-ID endpoint. Fetch the list and filter client-side on `roleId` or `roleName`. |
| **The response is the exact input shape for an update** | Take `accessType` and `permissions` from a role here, change what you need, and send them back to [Update Custom Role](#3-update-custom-role). This round-trip is the supported way to make a partial edit. |
| **Every flag is returned, including `false` ones** | Unlike the request side, where omission means `false`, the response is always complete. Do not infer that a returned `false` was explicitly set. |
| **`roleId` is a string** | Even though it is numerically a long. Do not parse it into a fixed-width integer type. |
| **Ordering is not guaranteed** | Sort client-side if presentation order matters. |
| **There is no pagination** | The full list is returned in one response. |
| **An empty list is a success** | `{"roles": []}` with HTTP 200. |
| **It reports definitions, not assignments** | The response says nothing about which users hold a role. |
| **Dependency chain:** | Get Custom Roles → `roles[].roleId` → [Update Custom Role](#3-update-custom-role) / [Delete Custom Role](#4-delete-custom-role); `roles[].permissions` → the body of an update. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 6142 | `CUSTOMROLES_NOT_ALLOWED_IN_PLAN` — The organization's subscription plan does not include custom roles. | Upgrade the plan. |
| 7301 | `SECURITY_NOT_PERMITTED` — The caller is not an Account Admin or Organization Admin, custom roles are not enabled for the organization, or the request came through a Client Portal / White Label domain. | Call as an organization administrator from the standard API host, with the feature enabled. |
| 7309 | `SECURITY_NEEDS_LOGIN` — No authentication was supplied. | Send an `Authorization` header. |
| 8083 | `ORGID_NOT_PRESENT_IN_THE_HEADER` — The `ZANALYTICS-ORGID` header is missing. | Add the header. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token, or the token lacks the `usermanagement` scope. | Provide a valid token carrying `ZohoAnalytics.usermanagement.read`. |

---

## 2. Create Custom Role

Creates one custom role in the organization.

| Attribute | Value |
|-----------|-------|
| **URL** | `/restapi/v2/orgs/roles` |
| **HTTP Method** | `POST` |
| **OAuth Scope** | `ZohoAnalytics.usermanagement.create` |
| **Mandatory Header** | `ZANALYTICS-ORGID` |
| **CONFIG** | **Mandatory** |
| **Success Status** | `200 OK` with a JSON body carrying `data.roleId` |

This API takes no path parameters.

### CONFIG Parameters

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `roleName` | String | **Yes** | — | Display name of the role, 1–30 characters. Letters, digits, spaces, underscore, and hyphen only. Must be unique across the organization, otherwise `7553`. |
| `accessType` | String | **Yes** | — | One of `ALL_DASHBOARDS`, `ALL_REPORTS_AND_DASHBOARDS`, `ALL_DATA_REPORTS_AND_DASHBOARDS`. See [The `accessType` Hierarchy](#the-accesstype-hierarchy). |
| `permissions` | JSONObject | **Yes** | — | The permission definition, in up to seven groups, serialized to at most 5,000 characters. Groups you omit are treated as all-`false`. Must satisfy every rule in [Permission Dependency Rules](#permission-dependency-rules). |

All three are mandatory. Omitting any of them fails with `8504`; sending one empty fails with `8539` or `8078`.

### Sample Requests

**Case 1 — a dashboard-only role**

The most restricted level. No data, design, or datasource permissions may appear, and `createFolder` is the only creation flag available.

```http
POST /restapi/v2/orgs/roles HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded
```

```json
{
  "roleName": "Dashboard Viewer",
  "accessType": "ALL_DASHBOARDS",
  "permissions": {
    "interactionPermissions": {
      "read": true,
      "vud": true,
      "drillDown": true,
      "insight": true,
      "drillThrough": true,
      "drillActions": true
    },
    "publishPermissions": {
      "export": true,
      "publicViews": true,
      "createSlideshow": true,
      "manageEmailSchedules": true,
      "allEmailSchedulesAccess": true
    },
    "sharePermissions": {
      "share": true,
      "discussion": true,
      "accessAdminPresets": true,
      "createPreset": true,
      "privateLinks": true
    },
    "createPermissions": {
      "createFolder": true
    }
  }
}
```

Note `export: true` alongside `manageEmailSchedules: true` — rule 8 requires it.

**Case 2 — reports and dashboards, with alerts**

Raising the access level unlocks `manageDataAlerts`, which `ALL_DASHBOARDS` would reject with `7576`.

```json
{
  "roleName": "Report Analyst",
  "accessType": "ALL_REPORTS_AND_DASHBOARDS",
  "permissions": {
    "interactionPermissions": {
      "read": true,
      "vud": true,
      "drillDown": true,
      "insight": true,
      "drillThrough": true,
      "drillActions": true
    },
    "publishPermissions": {
      "export": true,
      "publicViews": true,
      "manageDataAlerts": true,
      "allDataAlertsAccess": true,
      "createSlideshow": true,
      "manageEmailSchedules": true,
      "allEmailSchedulesAccess": true
    },
    "sharePermissions": {
      "share": true,
      "discussion": true,
      "accessAdminPresets": true,
      "createPreset": true,
      "privateLinks": true
    },
    "createPermissions": {
      "createFolder": true
    }
  }
}
```

**Case 3 — full access, covering every group**

The only level at which `dataPermissions`, `designPermissions`, `datasourcePermissions`, and the table-creation flags are legal. This payload satisfies rules 7 (design modify pulls in both preset permissions), 9 (`useDatasource` pulls in `createTable`), and 10 (every other datasource flag pulls in `viewDatasource`).

```json
{
  "roleName": "Data Engineer",
  "accessType": "ALL_DATA_REPORTS_AND_DASHBOARDS",
  "permissions": {
    "createPermissions": {
      "createTable": true,
      "createQueryTable": true,
      "createFolder": true,
      "createFormula": true
    },
    "dataPermissions": {
      "addRow": true,
      "modifyRow": true,
      "deleteRow": true,
      "importAppend": true,
      "importAddOrUpdate": true,
      "importDeleteAllAdd": true
    },
    "designPermissions": {
      "designModify": true
    },
    "interactionPermissions": {
      "read": true,
      "vud": true,
      "drillDown": true,
      "insight": true,
      "drillThrough": true,
      "drillActions": true
    },
    "sharePermissions": {
      "share": true,
      "discussion": true,
      "privateLinks": true,
      "accessAdminPresets": true,
      "createPreset": true
    },
    "publishPermissions": {
      "export": true,
      "manageEmailSchedules": true,
      "allEmailSchedulesAccess": true,
      "manageDataAlerts": true,
      "allDataAlertsAccess": true,
      "createSlideshow": true,
      "publicViews": true
    },
    "datasourcePermissions": {
      "viewDatasource": true,
      "editDatasource": true,
      "syncData": true,
      "useDatasource": true,
      "removeDatasource": true
    }
  }
}
```

### Sample Responses

**HTTP 200 OK — the role was created**

```json
{
  "status": "success",
  "summary": "Create role",
  "data": {
    "roleId": "20868000000013096"
  }
}
```

**HTTP 400 Bad Request — `read` was not enabled**

```json
{
  "status": "failure",
  "summary": "CR_READ_PERM_MUST_BE_ENABLED",
  "data": {
    "errorCode": 7579,
    "errorMessage": "Read permission must always be enabled."
  }
}
```

**HTTP 400 Bad Request — a data permission at a level that does not allow it**

```json
{
  "status": "failure",
  "summary": "CR_DATA_PERM_NOT_ALLOWED_FOR_ACCESS_TYPE",
  "data": {
    "errorCode": 7573,
    "errorMessage": "Data permissions (Add Row, Modify Row, Delete Row, Import Data, etc.) are only allowed when the access type includes All Data, Reports And Dashboards."
  }
}
```

**HTTP 400 Bad Request — email schedules without export**

```json
{
  "status": "failure",
  "summary": "EXPORT_PERM_NEEDED_FOR_EMAILSCH",
  "data": {
    "errorCode": 7559,
    "errorMessage": "Export permission is necessary for Managing Email Schedules."
  }
}
```

**HTTP 400 Bad Request — the name is already in use**

```json
{
  "status": "failure",
  "summary": "ROLENAME_EXISTS",
  "data": {
    "errorCode": 7553,
    "errorMessage": "A role with the same name already exists. Please provide a different name"
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | String | `"success"` on success. |
| `summary` | String | `"Create role"`. |
| `data` | Object | Wrapper. |
| `data.roleId` | String | ID of the new role, **as a string**. This is the only place it is returned on creation; capture it. It becomes `<role-id>` for [Update Custom Role](#3-update-custom-role) and [Delete Custom Role](#4-delete-custom-role). |

### Notes & Behaviour

| Behaviour | Detail |
|-----------|--------|
| **All three CONFIG attributes are mandatory** | Unlike [Update Custom Role](#3-update-custom-role), which accepts `roleName` alone. |
| **Omitted permission flags are `false`** | There is no "inherit" or "default on". A group you leave out is entirely disabled — except `read`, which must be explicitly `true`. |
| **Validation is complete before anything is stored** | A rejected request creates no role, so a failed call is safe to correct and retry. |
| **Rules fire in a fixed order** | `read` is checked first, so a payload with several problems reports `7579` before anything else. Fix and resend to surface the next one. |
| **Names compete with built-in roles too** | `7553` covers a clash with any existing role name in the organization, not only with other custom roles. |
| **`roleName` is limited to 30 characters** | Longer names fail with `8507`, and characters outside letters, digits, space, underscore, and hyphen fail with `8509`. |
| **It is not an upsert** | Re-creating an existing name fails rather than returning or updating the existing role. |
| **One role per call** | There is no bulk-create variant. |
| **Creating a role grants nothing by itself** | Until the role is assigned to a user or workspace elsewhere, it has no effect. |
| **Dependency chain:** | Create Custom Role → `data.roleId` → [Get Custom Roles](#1-get-custom-roles) to verify → [Update Custom Role](#3-update-custom-role) / [Delete Custom Role](#4-delete-custom-role). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 6142 | `CUSTOMROLES_NOT_ALLOWED_IN_PLAN` — The plan does not include custom roles. | Upgrade the plan. |
| 7301 | `SECURITY_NOT_PERMITTED` — The caller is not an organization administrator, the feature is not enabled, or the request came through a Client Portal / White Label domain. | Call as an organization administrator from the standard API host. |
| 7309 | `SECURITY_NEEDS_LOGIN` — No authentication was supplied. | Send an `Authorization` header. |
| 7553 | `ROLENAME_EXISTS` — A role with this name already exists in the organization. | Choose a different name. |
| 7554 | `INVALID_VIEWTYPE_GROUP` — `accessType` did not resolve to a known level. | Send one of the three documented values. |
| 7559 | `EXPORT_PERM_NEEDED_FOR_EMAILSCH` — `manageEmailSchedules` is `true` but `export` is not. | Set `publishPermissions.export` to `true`. |
| 7573 | `CR_DATA_PERM_NOT_ALLOWED_FOR_ACCESS_TYPE` — A data permission was enabled below the full access level. | Raise `accessType`, or set every `dataPermissions` flag to `false`. |
| 7574 | `CR_DESIGN_PERM_NOT_ALLOWED_FOR_ACCESS_TYPE` — `designModify` was enabled below the full access level. | Raise `accessType`, or disable `designModify`. |
| 7575 | `CR_CREATE_PERM_NOT_ALLOWED_FOR_ACCESS_TYPE` — `createTable`, `createQueryTable`, or `createFormula` was enabled below the full access level. | Raise `accessType`, or disable those flags. `createFolder` is allowed at every level. |
| 7576 | `CR_ALERT_PERM_NOT_ALLOWED_FOR_ACCESS_TYPE` — `manageDataAlerts` was enabled with `ALL_DASHBOARDS`. | Use `ALL_REPORTS_AND_DASHBOARDS` or higher, or disable the flag. |
| 7577 | `CR_SCHEDULED_DATA_DELETION_PERM_NOT_ALLOWED` — `dataArchives` is `true` but not every data permission is enabled. | Enable all data permissions, or disable `dataArchives`. |
| 7578 | `CR_DESIGN_MODIFY_REQUIRES_PRESET_PERMS` — `designModify` is `true` without both preset permissions. | Set `accessAdminPresets` and `createPreset` to `true`. |
| 7579 | `CR_READ_PERM_MUST_BE_ENABLED` — `interactionPermissions.read` is missing or `false`. | Set `read` to `true`. |
| 7584 | `CR_DATASOURCE_PERM_NOT_ALLOWED_FOR_ACCESS_TYPE` — A datasource permission was enabled below the full access level. | Raise `accessType`, or disable the datasource group. |
| 7585 | `CR_USE_DATASOURCE_REQUIRES_CREATETABLE` — `useDatasource` is `true` but `createTable` is not. | Enable `createPermissions.createTable`. |
| 7586 | `CR_VIEW_DATASOURCE_REQUIRED_FOR_DATASOURCE_PERMS` — Another datasource permission is enabled without `viewDatasource`. | Set `datasourcePermissions.viewDatasource` to `true`. |
| 8078 | `EMPTY_JSON_ATTRIBUTE_FOUND` — A mandatory attribute was sent blank. | The message names the attribute. |
| 8083 | `ORGID_NOT_PRESENT_IN_THE_HEADER` — The `ZANALYTICS-ORGID` header is missing. | Add the header. |
| 8504 | `LESS_THAN_MIN_OCCURANCE` — `CONFIG` was not sent, or a mandatory attribute is missing. | Send `roleName`, `accessType`, and `permissions`. |
| 8507 | `MORE_THAN_MAX_LENGTH` — `roleName` exceeds 30 characters, or `permissions` exceeds its size limit. | Shorten the value. |
| 8509 | `PATTERN_NOT_MATCHED` — `roleName` contains disallowed characters, or `accessType` is not one of the three values. | Correct the value. |
| 8534 | `JSON_PARSE_ERROR` — `CONFIG` is not valid JSON. | Fix the JSON and URL-encode it correctly. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token, or the token lacks the `usermanagement` scope. | Provide a valid token carrying `ZohoAnalytics.usermanagement.create`. |
| 8539 | `INVALID_VALUE_NOT_ALLOWED` — An attribute carries a value that is structurally valid but not accepted, such as an empty `roleName`. | Send a non-empty value. |

---

## 3. Update Custom Role

Renames a custom role, replaces its access type and permissions, or both.

| Attribute | Value |
|-----------|-------|
| **URL** | `/restapi/v2/orgs/roles/<role-id>` |
| **HTTP Method** | `PUT` |
| **OAuth Scope** | `ZohoAnalytics.usermanagement.update` |
| **Mandatory Header** | `ZANALYTICS-ORGID` |
| **CONFIG** | **Mandatory** |
| **Success Status** | **`204 No Content`** — no response body |

**Path parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `<role-id>` | Long | ID of the role to update. Must exist in the organization, otherwise `7548`. A non-numeric value does not reach the API and yields `8525`. |

### CONFIG Parameters

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `roleName` | String | Conditional | unchanged | New display name, 1–30 characters. Must be unique across the organization, otherwise `7553`. Omit to keep the current name. |
| `accessType` | String | Conditional | unchanged | New access level. **Must be sent together with `permissions`**, otherwise `7580`. |
| `permissions` | JSONObject | Conditional | unchanged | Complete replacement permission definition. **Must be sent together with `accessType`**, otherwise `7580`. |

Two rules govern which combinations are legal:

- **At least one of `roleName` or `accessType` must be present.** A CONFIG carrying neither fails with `7581`.
- **`accessType` and `permissions` are all-or-nothing.** Sending one without the other fails with `7580` — including sending `permissions` alone.

That leaves exactly three valid shapes:

| Shape | Effect |
|-------|--------|
| `roleName` only | Renames the role. `accessType` and `permissions` are preserved untouched. |
| `accessType` + `permissions` | Replaces the access level and the entire permission set. The name is preserved. |
| `roleName` + `accessType` + `permissions` | Replaces everything. |

> **This is a replace, not a merge.** When `permissions` is supplied, the stored definition is discarded and rebuilt from what you sent. Any flag you omit becomes `false`. Read the current definition from [Get Custom Roles](#1-get-custom-roles) and edit it, rather than sending only the flags you want to change.

### Sample Requests

**Case 1 — rename only**

The one edit that needs no prior read, and the only shape that leaves permissions alone.

```http
PUT /restapi/v2/orgs/roles/20868000000013096 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded
```

```json
{
  "roleName": "Report Analyst EMEA"
}
```

**Case 2 — replace access level and permissions**

Sent after reading the current definition and editing it. The name is untouched.

```json
{
  "accessType": "ALL_DATA_REPORTS_AND_DASHBOARDS",
  "permissions": {
    "createPermissions": {
      "createTable": true,
      "createQueryTable": true,
      "createFolder": true,
      "createFormula": true
    },
    "dataPermissions": {
      "addRow": true,
      "modifyRow": true,
      "deleteRow": true,
      "importAppend": true,
      "importAddOrUpdate": true,
      "importDeleteAllAdd": true
    },
    "designPermissions": {
      "designModify": true
    },
    "interactionPermissions": {
      "read": true,
      "vud": true,
      "drillDown": true,
      "insight": true,
      "drillThrough": true,
      "drillActions": true
    },
    "sharePermissions": {
      "share": true,
      "discussion": true,
      "privateLinks": true,
      "accessAdminPresets": true,
      "createPreset": true
    },
    "publishPermissions": {
      "export": true,
      "manageEmailSchedules": true,
      "allEmailSchedulesAccess": true,
      "manageDataAlerts": true,
      "allDataAlertsAccess": true,
      "createSlideshow": true,
      "publicViews": true
    }
  }
}
```

**Case 3 — rename and redefine in one call**

Downgrading to a lower access level. Every permission above the new ceiling must be absent or `false`, or the call is rejected.

```json
{
  "roleName": "Dashboard Only",
  "accessType": "ALL_DASHBOARDS",
  "permissions": {
    "interactionPermissions": {
      "read": true,
      "vud": true,
      "drillDown": true,
      "insight": true
    },
    "sharePermissions": {
      "share": true,
      "discussion": true
    },
    "publishPermissions": {
      "export": true
    },
    "createPermissions": {
      "createFolder": true
    }
  }
}
```

### Sample Responses

**HTTP 204 No Content — the role was updated**

```
HTTP/1.1 204 No Content
```

There is no response body. Read the new definition back with [Get Custom Roles](#1-get-custom-roles).

**HTTP 400 Bad Request — nothing to update**

```json
{
  "status": "failure",
  "summary": "CR_NO_FIELDS_TO_UPDATE",
  "data": {
    "errorCode": 7581,
    "errorMessage": "At least one of roleName, accessType with permissions must be provided for update."
  }
}
```

**HTTP 400 Bad Request — `accessType` sent without `permissions`**

```json
{
  "status": "failure",
  "summary": "CR_ACCESS_TYPE_AND_PERMS_REQUIRED_TOGETHER",
  "data": {
    "errorCode": 7580,
    "errorMessage": "Both accessType and permissions must be provided together."
  }
}
```

**HTTP 400 Bad Request — the role does not exist**

```json
{
  "status": "failure",
  "summary": "NO_SUCH_ROLE_EXIST",
  "data": {
    "errorCode": 7548,
    "errorMessage": "The given role does not exist."
  }
}
```

### Response Fields

**None.** This API returns `204 No Content` with an empty body. Confirm the change with [Get Custom Roles](#1-get-custom-roles).

### Notes & Behaviour

| Behaviour | Detail |
|-----------|--------|
| **`permissions` is replaced, never merged** | This is the most consequential behaviour of the API. A payload containing one group wipes the other six. Always start from a [Get Custom Roles](#1-get-custom-roles) response. |
| **`permissions` alone is rejected** | Even though it looks like the natural way to edit permissions, it fails with `7580`. `accessType` must accompany it — resend the role's current level if you are not changing it. |
| **A rename is the only safe standalone edit** | `roleName` on its own preserves the entire permission definition. |
| **The same eleven rules apply as on create** | Whenever `permissions` is supplied it is validated in full, so an update can fail with any of the create-time permission errors. |
| **Downgrading `accessType` requires cleaning the permissions first** | Lowering the level while leaving a higher-level flag `true` fails with `7573`, `7574`, `7575`, `7576`, or `7584` depending on which flag. Strip them in the same payload. |
| **Validation happens before anything is stored** | A rejected update leaves the role exactly as it was. |
| **Existing holders are affected immediately** | Users already assigned the role take on the new definition; there is no versioning and no migration step. |
| **A non-numeric `<role-id>` never reaches the API** | It fails at routing with `8525` rather than `7548`. |
| **One role per call** | There is no bulk-update variant. |
| **Dependency chain:** | [Get Custom Roles](#1-get-custom-roles) → `roleId` + `accessType` + `permissions` → edit → Update Custom Role → [Get Custom Roles](#1-get-custom-roles) to verify. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 6142 | `CUSTOMROLES_NOT_ALLOWED_IN_PLAN` — The plan does not include custom roles. | Upgrade the plan. |
| 7301 | `SECURITY_NOT_PERMITTED` — The caller is not an organization administrator, the feature is not enabled, or the request came through a Client Portal / White Label domain. | Call as an organization administrator from the standard API host. |
| 7309 | `SECURITY_NEEDS_LOGIN` — No authentication was supplied. | Send an `Authorization` header. |
| 7548 | `NO_SUCH_ROLE_EXIST` — No role exists for the given `<role-id>`. | Verify the ID with [Get Custom Roles](#1-get-custom-roles). |
| 7553 | `ROLENAME_EXISTS` — Another role already uses the new name. | Choose a different name. |
| 7554 | `INVALID_VIEWTYPE_GROUP` — `accessType` did not resolve to a known level. | Send one of the three documented values. |
| 7559 | `EXPORT_PERM_NEEDED_FOR_EMAILSCH` — `manageEmailSchedules` is `true` but `export` is not. | Set `publishPermissions.export` to `true`. |
| 7573 | `CR_DATA_PERM_NOT_ALLOWED_FOR_ACCESS_TYPE` — A data permission is enabled below the full access level. | Raise `accessType`, or disable those flags. |
| 7574 | `CR_DESIGN_PERM_NOT_ALLOWED_FOR_ACCESS_TYPE` — `designModify` is enabled below the full access level. | Raise `accessType`, or disable it. |
| 7575 | `CR_CREATE_PERM_NOT_ALLOWED_FOR_ACCESS_TYPE` — A data-level creation flag is enabled below the full access level. | Raise `accessType`, or disable those flags. |
| 7576 | `CR_ALERT_PERM_NOT_ALLOWED_FOR_ACCESS_TYPE` — `manageDataAlerts` is enabled with `ALL_DASHBOARDS`. | Use a higher `accessType`, or disable the flag. |
| 7577 | `CR_SCHEDULED_DATA_DELETION_PERM_NOT_ALLOWED` — `dataArchives` is `true` but not every data permission is enabled. | Enable all data permissions, or disable `dataArchives`. |
| 7578 | `CR_DESIGN_MODIFY_REQUIRES_PRESET_PERMS` — `designModify` is `true` without both preset permissions. | Set `accessAdminPresets` and `createPreset` to `true`. |
| 7579 | `CR_READ_PERM_MUST_BE_ENABLED` — `interactionPermissions.read` is missing or `false`. | Set `read` to `true`. |
| 7580 | `CR_ACCESS_TYPE_AND_PERMS_REQUIRED_TOGETHER` — One of `accessType` / `permissions` was sent without the other. | Send both, or neither. |
| 7581 | `CR_NO_FIELDS_TO_UPDATE` — Neither `roleName` nor `accessType` was supplied. | Send at least one. |
| 7584 | `CR_DATASOURCE_PERM_NOT_ALLOWED_FOR_ACCESS_TYPE` — A datasource permission is enabled below the full access level. | Raise `accessType`, or disable the group. |
| 7585 | `CR_USE_DATASOURCE_REQUIRES_CREATETABLE` — `useDatasource` is `true` but `createTable` is not. | Enable `createPermissions.createTable`. |
| 7586 | `CR_VIEW_DATASOURCE_REQUIRED_FOR_DATASOURCE_PERMS` — Another datasource permission is enabled without `viewDatasource`. | Set `datasourcePermissions.viewDatasource` to `true`. |
| 8083 | `ORGID_NOT_PRESENT_IN_THE_HEADER` — The `ZANALYTICS-ORGID` header is missing. | Add the header. |
| 8504 | `LESS_THAN_MIN_OCCURANCE` — `CONFIG` was not sent. | Send a CONFIG object. |
| 8507 | `MORE_THAN_MAX_LENGTH` — `roleName` exceeds 30 characters, or `permissions` exceeds its size limit. | Shorten the value. |
| 8509 | `PATTERN_NOT_MATCHED` — `roleName` contains disallowed characters, or `accessType` is not one of the three values. | Correct the value. |
| 8525 | `URL_RULE_NOT_CONFIGURED` — `<role-id>` is not numeric, so the request matched no route. | Send a numeric role ID. |
| 8534 | `JSON_PARSE_ERROR` — `CONFIG` is not valid JSON. | Fix the JSON and URL-encode it correctly. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token, or the token lacks the `usermanagement` scope. | Provide a valid token carrying `ZohoAnalytics.usermanagement.update`. |

---

## 4. Delete Custom Role

Deletes a custom role definition.

| Attribute | Value |
|-----------|-------|
| **URL** | `/restapi/v2/orgs/roles/<role-id>` |
| **HTTP Method** | `DELETE` |
| **OAuth Scope** | `ZohoAnalytics.usermanagement.delete` |
| **Mandatory Header** | `ZANALYTICS-ORGID` |
| **CONFIG** | This API takes no CONFIG fields |
| **Success Status** | **`204 No Content`** — no response body |

**Path parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `<role-id>` | Long | ID of the role to delete. Must exist in the organization, otherwise `7548`. A non-numeric value does not reach the API and yields `8525`. |

### Sample Requests

```http
DELETE /restapi/v2/orgs/roles/20868000000013096 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

There is nothing else to send.

### Sample Responses

**HTTP 204 No Content — the role was deleted**

```
HTTP/1.1 204 No Content
```

**HTTP 200 OK — reading the role list afterwards**

```json
{
  "status": "success",
  "summary": "Get roles",
  "data": {
    "roles": []
  }
}
```

**HTTP 400 Bad Request — the role does not exist, or was already deleted**

```json
{
  "status": "failure",
  "summary": "NO_SUCH_ROLE_EXIST",
  "data": {
    "errorCode": 7548,
    "errorMessage": "The given role does not exist."
  }
}
```

**HTTP 403 Forbidden — the caller is not an organization administrator**

```json
{
  "status": "failure",
  "summary": "SECURITY_NOT_PERMITTED",
  "data": {
    "errorCode": 7301,
    "errorMessage": "You do not have the permission to perform this operation."
  }
}
```

### Response Fields

**None.** This API returns `204 No Content` with an empty body. Confirm with [Get Custom Roles](#1-get-custom-roles).

### Notes & Behaviour

| Behaviour | Detail |
|-----------|--------|
| **It removes the definition only** | Users who held the role are not deleted. Reassigning them is done through the user-management APIs, not here. |
| **There is no undo** | The definition cannot be restored, and re-creating the same name produces a new role with a new `roleId` and no history. |
| **It is not idempotent** | A second delete of the same ID fails with `7548` rather than returning `204`. Treat that as "already gone" rather than as a failure to retry. |
| **The response reports nothing about impact** | It does not say how many users held the role. Establish that before deleting, through the user-management APIs. |
| **A non-numeric `<role-id>` never reaches the API** | It fails at routing with `8525` rather than `7548`. |
| **One role per call** | There is no bulk-delete variant. |
| **Dependency chain:** | [Get Custom Roles](#1-get-custom-roles) → `roleId` → Delete Custom Role → [Get Custom Roles](#1-get-custom-roles) to verify. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 6142 | `CUSTOMROLES_NOT_ALLOWED_IN_PLAN` — The plan does not include custom roles. | Upgrade the plan. |
| 7301 | `SECURITY_NOT_PERMITTED` — The caller is not an organization administrator, the feature is not enabled, or the request came through a Client Portal / White Label domain. | Call as an organization administrator from the standard API host. |
| 7309 | `SECURITY_NEEDS_LOGIN` — No authentication was supplied. | Send an `Authorization` header. |
| 7548 | `NO_SUCH_ROLE_EXIST` — No role exists for the given `<role-id>`, or it has already been deleted. | Verify the ID with [Get Custom Roles](#1-get-custom-roles). |
| 8083 | `ORGID_NOT_PRESENT_IN_THE_HEADER` — The `ZANALYTICS-ORGID` header is missing. | Add the header. |
| 8525 | `URL_RULE_NOT_CONFIGURED` — `<role-id>` is not numeric, so the request matched no route. | Send a numeric role ID. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token, or the token lacks the `usermanagement` scope. | Provide a valid token carrying `ZohoAnalytics.usermanagement.delete`. |

---

## Appendix A – Common HTTP Headers

| Header | Value | Required | Description |
|--------|-------|----------|-------------|
| `Authorization` | `Zoho-oauthtoken <oauth-token>` | **Mandatory** | OAuth 2.0 access token of the calling user, carrying the scope for the API being called — see [Appendix B](#appendix-b--oauth-scope-summary). |
| `ZANALYTICS-ORGID` | Organization ID string | **Mandatory** | Organization the role belongs to. Required by all four APIs; it is the only way the organization is identified, since no path parameter carries it. |
| `Content-Type` | `application/x-www-form-urlencoded` | Conditional | Required by [Create Custom Role](#2-create-custom-role) and [Update Custom Role](#3-update-custom-role), which carry a CONFIG body. |

> **`ZANALYTICS-DEST-ORGID` is not used by any of these APIs.** That header applies only to cross-organization copy operations (Copy Workspace, [Copy Views](VIEW_OPERATIONS_API_DOC_INFO.md#2-copy-views), Copy Formulas), which target a destination organization.

The `CONFIG` JSON is sent as the URL-encoded value of a form parameter named `CONFIG`:

```http
POST /restapi/v2/orgs/roles HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG=%7B%22roleName%22%3A%22Dashboard%20Viewer%22%2C%22accessType%22%3A%22ALL_DASHBOARDS%22%2C%22permissions%22%3A%7B%22interactionPermissions%22%3A%7B%22read%22%3Atrue%7D%7D%7D
```

The decoded `CONFIG` above is `{"roleName":"Dashboard Viewer","accessType":"ALL_DASHBOARDS","permissions":{"interactionPermissions":{"read":true}}}`.

---

## Appendix B – OAuth Scope Summary

| API | HTTP Method | Scope |
|-----|-------------|-------|
| Get Custom Roles | GET | `ZohoAnalytics.usermanagement.read` |
| Create Custom Role | POST | `ZohoAnalytics.usermanagement.create` |
| Update Custom Role | PUT | `ZohoAnalytics.usermanagement.update` |
| Delete Custom Role | DELETE | `ZohoAnalytics.usermanagement.delete` |

> All four sit in the **`usermanagement`** scope family, not `modeling` or `metadata`, because a custom role is an organization-administration object rather than a workspace object. An integration that manages roles needs all four operations, or the broader `ZohoAnalytics.usermanagement.ALL`. A token scoped for workspace work will not authorise any of them, and a missing `usermanagement` scope surfaces as `8535` rather than as a permission error.

---

## Appendix C – API-Specific Notes and Behaviours

### Get Custom Roles

- **It is the only read in the family, and there is no get-by-ID.** Every workflow that touches an existing role starts by listing all of them and filtering client-side.
- **Its response is deliberately the update request shape.** `accessType` and `permissions` can be lifted straight out of a role here and posted back to [Update Custom Role](#3-update-custom-role). Treat the read as the first half of every permission edit.
- **The response is always complete**, with all seven groups and every flag present including the `false` ones — unlike the request side, where omission means `false`.
- **It reports definitions, not assignments.** Nothing here tells you who holds a role; that lives in the user-management APIs.
- **`6142` and `7301` mean different things.** `6142` is a plan limitation, `7301` covers three separate causes — wrong role, feature disabled, or custom domain. Only `6142` is resolved by a subscription change.
- **Dependency chain:** Get Custom Roles → `roles[].roleId` → [Update Custom Role](#3-update-custom-role) / [Delete Custom Role](#4-delete-custom-role).

### Create Custom Role

- **`read` is the single most common failure.** It is not defaulted, so a `permissions` object that omits `interactionPermissions` is rejected with `7579` before any other rule is evaluated. Set it explicitly, always.
- **`accessType` is a ceiling, not a hint.** Enabling a permission above the chosen level is an error rather than a silent downgrade, and which error you get depends on the group — five different codes cover the same underlying idea.
- **Four rules cross group boundaries**, which is what makes a hand-assembled payload fail in ways that are hard to read: design modify pulls in two share permissions, email schedules pull in export, `useDatasource` pulls in `createTable`, and every other datasource flag pulls in `viewDatasource`.
- **`roleName` is 30 characters, not 100.** It is also restricted to letters, digits, spaces, underscore, and hyphen.
- **It is not an upsert**, so a re-runnable provisioning script must read [Get Custom Roles](#1-get-custom-roles) first and branch, or tolerate `7553`.
- **Creating a role changes nobody's access** until it is assigned elsewhere.
- **Dependency chain:** Create Custom Role → `data.roleId` → [Get Custom Roles](#1-get-custom-roles) to verify.

### Update Custom Role

- **The replace-not-merge behaviour is the thing to get right.** Supplying `permissions` discards the stored object entirely, so an update built from "just the flags I want to change" silently strips everything else. Always round-trip through [Get Custom Roles](#1-get-custom-roles).
- **`permissions` alone is rejected**, which surprises most callers: the natural payload for "change these permissions" fails with `7580`. Resend the role's existing `accessType` alongside it.
- **Renaming is the only genuinely partial edit**, and the only one that needs no prior read.
- **Downgrading `accessType` is a two-part change.** The lower level and the cleaned permission set must arrive in the same payload, or the higher-level flags left behind trigger `7573` / `7574` / `7575` / `7576` / `7584`.
- **Changes apply immediately to everyone holding the role.** There is no draft, no version, and no staged rollout.
- **`8525` versus `7548`.** A non-numeric ID fails at routing and never reaches the API; a numeric but unknown ID reaches it and returns `7548`.
- **Dependency chain:** [Get Custom Roles](#1-get-custom-roles) → edit `accessType` + `permissions` → Update Custom Role → [Get Custom Roles](#1-get-custom-roles).

### Delete Custom Role

- **It deletes a definition, not the people holding it.** Plan the reassignment of affected users through the user-management APIs before calling it; nothing here reports or handles them.
- **It is not idempotent.** The second call returns `7548`, so cleanup scripts should treat that code as success rather than retrying.
- **There is no impact report and no undo.** Recreating the name yields a fresh role with a new ID.
- **Dependency chain:** [Get Custom Roles](#1-get-custom-roles) → `roleId` → Delete Custom Role.

---

## Appendix D – General Response Payload Notes

| Field / Behaviour | Detail |
|-------------------|--------|
| **Two APIs return a body, two return 204** | [Get Custom Roles](#1-get-custom-roles) and [Create Custom Role](#2-create-custom-role) return `200` with the standard envelope. [Update Custom Role](#3-update-custom-role) and [Delete Custom Role](#4-delete-custom-role) return `204 No Content` with an empty body. |
| **A 204 carries no confirmation of what changed** | Neither mutating API reports the resulting definition. Verification is a follow-up [Get Custom Roles](#1-get-custom-roles). |
| **Failure responses share one shape** | `{"status": "failure", "summary": "<ERROR_NAME>", "data": {"errorCode": <n>, "errorMessage": "<text>"}}`. `summary` on failure is the error's symbolic name (for example `CR_READ_PERM_MUST_BE_ENABLED`), not a localised sentence. |
| **Success `summary` values are terse** | `"Get roles"` and `"Create role"`. Do not branch on summary text. |
| **IDs are strings** | `roleId` is a JSON string in both the create response and the read response, even though it is numerically a long. |
| **Permission flags are real booleans** | Every leaf inside the seven groups is a JSON `true` / `false`, never a string. |
| **The read response is always complete** | All seven groups and every flag appear, including `false` ones. Request payloads are the opposite — omission means `false`. |
| **An empty role list is a success** | `{"roles": []}` with HTTP 200. |
| **Validation errors leave nothing changed** | Every rule is evaluated before anything is stored, so a rejected create produces no role and a rejected update leaves the role as it was. |
| **One error is reported at a time** | Rules are checked in a fixed order, so a payload with several problems surfaces them one call at a time. |

---

## Appendix E – Permission Reference

Every recognised permission key, by group. All are booleans, and **an omitted key is treated as `false`**.

**`createPermissions`**

| Key | Allows | Minimum `accessType` |
|-----|--------|----------------------|
| `createFolder` | Creating folders | `ALL_DASHBOARDS` |
| `createTable` | Creating tables and importing data into new ones | `ALL_DATA_REPORTS_AND_DASHBOARDS` |
| `createQueryTable` | Creating query tables | `ALL_DATA_REPORTS_AND_DASHBOARDS` |
| `createFormula` | Creating formula columns | `ALL_DATA_REPORTS_AND_DASHBOARDS` |

**`dataPermissions`** — every key requires `ALL_DATA_REPORTS_AND_DASHBOARDS`

| Key | Allows |
|-----|--------|
| `addRow` | Adding rows to a table |
| `modifyRow` | Changing existing rows |
| `deleteRow` | Deleting rows. Also confers the bulk delete-all-rows capability. |
| `importAppend` | Importing in append mode |
| `importAddOrUpdate` | Importing in add-or-update mode |
| `importDeleteAllAdd` | Importing in delete-all-and-add mode |
| `dataArchives` | Managing scheduled data deletion. Requires **every** data permission to be enabled — see rule 11 in [Permission Dependency Rules](#permission-dependency-rules). |

**`designPermissions`**

| Key | Allows | Requires |
|-----|--------|----------|
| `designModify` | Changing a view's design — formatting, layout, structure | `ALL_DATA_REPORTS_AND_DASHBOARDS`, plus `accessAdminPresets` and `createPreset` |

**`interactionPermissions`** — available at every `accessType`

| Key | Allows |
|-----|--------|
| `read` | Viewing the shared item. **Must always be `true`.** |
| `vud` | Viewing the underlying data of a report |
| `drillDown` | Drilling down within a report |
| `drillThrough` | Drilling through to a linked report |
| `drillActions` | Running drill actions |
| `insight` | Using the AI and insight features on a view |

**`sharePermissions`** — available at every `accessType`

| Key | Allows |
|-----|--------|
| `share` | Re-sharing a view with other users |
| `discussion` | Taking part in view discussions and comments |
| `privateLinks` | Generating private links for a view |
| `accessAdminPresets` | Viewing presets created by the workspace administrator |
| `createPreset` | Creating personal filter and column presets |

**`publishPermissions`**

| Key | Allows | Minimum `accessType` |
|-----|--------|----------------------|
| `export` | Exporting view data | `ALL_DASHBOARDS` |
| `manageEmailSchedules` | Creating and editing email schedules. **Requires `export`.** | `ALL_DASHBOARDS` |
| `allEmailSchedulesAccess` | Also managing email schedules created by other users | `ALL_DASHBOARDS` |
| `manageDataAlerts` | Creating and editing data alerts | `ALL_REPORTS_AND_DASHBOARDS` |
| `allDataAlertsAccess` | Also managing data alerts created by other users | `ALL_REPORTS_AND_DASHBOARDS` |
| `createSlideshow` | Creating slideshows from dashboards | `ALL_DASHBOARDS` |
| `publicViews` | Making a view publicly accessible | `ALL_DASHBOARDS` |

**`datasourcePermissions`** — every key requires `ALL_DATA_REPORTS_AND_DASHBOARDS`

| Key | Allows | Also requires |
|-----|--------|---------------|
| `viewDatasource` | Seeing the datasource behind a table | — |
| `editDatasource` | Changing datasource connection details | `viewDatasource` |
| `syncData` | Triggering a data sync | `viewDatasource` |
| `useDatasource` | Building new tables from an existing datasource | `viewDatasource` **and** `createTable` |
| `removeDatasource` | Removing a datasource | `viewDatasource` |

> `allEmailSchedulesAccess` and `allDataAlertsAccess` are sub-options. Each widens the scope of its parent permission from "schedules I created" to "all schedules", and has no effect unless its parent is `true`.

---

## Appendix F – `accessType` ↔ Permission Availability Matrix

`✓` may be enabled, `–` rejected at that level.

| Permission | `ALL_DASHBOARDS` | `ALL_REPORTS_AND_DASHBOARDS` | `ALL_DATA_REPORTS_AND_DASHBOARDS` | Error if enabled below its level |
|------------|:---:|:---:|:---:|---|
| `read`, `vud`, `drillDown`, `drillThrough`, `drillActions`, `insight` | ✓ | ✓ | ✓ | — |
| `share`, `discussion`, `privateLinks`, `accessAdminPresets`, `createPreset` | ✓ | ✓ | ✓ | — |
| `export`, `manageEmailSchedules`, `allEmailSchedulesAccess`, `createSlideshow`, `publicViews` | ✓ | ✓ | ✓ | — |
| `createFolder` | ✓ | ✓ | ✓ | — |
| `manageDataAlerts`, `allDataAlertsAccess` | – | ✓ | ✓ | `7576` |
| `createTable`, `createQueryTable`, `createFormula` | – | – | ✓ | `7575` |
| `addRow`, `modifyRow`, `deleteRow`, `importAppend`, `importAddOrUpdate`, `importDeleteAllAdd`, `dataArchives` | – | – | ✓ | `7573` |
| `designModify` | – | – | ✓ | `7574` |
| `viewDatasource`, `editDatasource`, `syncData`, `useDatasource`, `removeDatasource` | – | – | ✓ | `7584` |

---

## Appendix G – CONFIG Attribute Availability by API

`✓` accepted, `–` not accepted by that API.

| Attribute | Get Custom Roles | Create Custom Role | Update Custom Role | Delete Custom Role |
|-----------|:---:|:---:|:---:|:---:|
| `roleName` | – | ✓ **mandatory** | ✓ conditional | – |
| `accessType` | – | ✓ **mandatory** | ✓ conditional — with `permissions` | – |
| `permissions` | – | ✓ **mandatory** | ✓ conditional — with `accessType` | – |

[Get Custom Roles](#1-get-custom-roles) and [Delete Custom Role](#4-delete-custom-role) take no CONFIG at all.

**Valid update combinations**

| `roleName` | `accessType` | `permissions` | Result |
|:---:|:---:|:---:|---|
| ✓ | – | – | Rename only; permissions preserved |
| – | ✓ | ✓ | Access level and permissions replaced; name preserved |
| ✓ | ✓ | ✓ | Everything replaced |
| – | – | – | `7581` |
| – | ✓ | – | `7580` |
| – | – | ✓ | `7580` |
| ✓ | ✓ | – | `7580` |
| ✓ | – | ✓ | `7580` |
