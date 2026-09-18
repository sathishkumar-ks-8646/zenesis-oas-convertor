# Zoho Analytics V2 REST API — Publish

This document covers the V2 **Publish** REST APIs of Zoho Analytics — the APIs that expose a view (table, chart, pivot, summary, dashboard, query table, etc.) outside the normal shared-user model, either as a **Public URL** or as a **Private URL**, and the APIs that read/update the **presentation configuration** of the published page.

## What is "Publishing" in Zoho Analytics?

Publishing makes a single view reachable through a stand-alone URL of the form `https://<analytics-domain>/open-view/<view-id>[/<private-key>]`, without adding the visitor as a shared user of the workspace. There are two independent publish channels, and a view can have **both active at the same time**:

| Channel | URL shape | Who can open it | Managed by |
|---------|-----------|-----------------|------------|
| **Public URL** | `https://<analytics-domain>/open-view/<view-id>` | Anyone with the link (or everyone in the organization / business organization, depending on `publicPermLevel`) | [Make View Public](#1-make-view-public) / [Remove Public Permission](#2-remove-public-permission) |
| **Private URL** | `https://<analytics-domain>/open-view/<view-id>/<private-key>` | Only holders of the secret 32-character key, optionally additionally gated by a password and/or an expiry date | [Get Private URL](#3-get-private-url) / [Create Private URL](#4-create-private-url) / [Remove Private Access](#5-remove-private-access) |

Internally both channels are modelled as a share to a reserved pseudo-user — **`Public Visitor`** (`sharedToZuId: "-20"`) for the public channel and **`Private Link`** (`sharedToZuId: "-30"`) for the private channel. This is why the effect of these APIs is visible in the [Get Shared Details](SHARING_API_DOC_INFO.md#4-get-shared-details) response, and why the permission set accepted here is a read-only subset of the normal sharing `permissions` object.

Separately, [Get Publish Configurations](#6-get-publish-configurations) and [Update Publish Configurations](#7-update-publish-configurations) control **how the published page renders** (title, toolbar, search box, size, auto-refresh, legend position, URL-level criteria, Ask Zia, …). That configuration is shared by both channels and by the embed URL.

> Notes that apply to every API in this document:
> - All requests are authenticated via OAuth (`Authorization: Zoho-oauthtoken <token>`). All seven APIs use the **`embed`** scope family.
> - All seven APIs are **view-scoped** (`/workspaces/<workspace-id>/views/<view-id>/publish/...`) and require the `ZANALYTICS-ORGID` header.
> - The API host (`ZohoAnalytics_Server_URI`, e.g. `analyticsapi.zoho.com`, `analyticsapi.zoho.eu`) is **not** the host that appears in the returned `publicUrl` / `privateUrl`. The returned URL always points at the Zoho Analytics **application** domain (e.g. `analytics.zoho.com`) or, for Client Portal / White Label workspaces, at the workspace's portal domain.
> - All seven APIs are available in **Client Portal / White Label** contexts.
> - The five mutating APIs (Make View Public, Remove Public Permission, Create Private URL, Remove Private Access, Update Publish Configurations) additionally require the calling user's **primary email to be verified** — otherwise error `7565`.
> - Publish links are always **read-only**. Row-write permissions (`addRow`, `updateRow`, `deleteRow`, imports) and `share` can never be granted to a public or private link — they are forced to `false` server-side.

---

## Index

| # | API Name | Method | URL |
|---|----------|--------|-----|
| 1 | [Make View Public](#1-make-view-public) | POST | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/publish/public` |
| 2 | [Remove Public Permission](#2-remove-public-permission) | DELETE | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/publish/public` |
| 3 | [Get Private URL](#3-get-private-url) | GET | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/publish/privatelink` |
| 4 | [Create Private URL](#4-create-private-url) | POST | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/publish/privatelink` |
| 5 | [Remove Private Access](#5-remove-private-access) | DELETE | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/publish/privatelink` |
| 6 | [Get Publish Configurations](#6-get-publish-configurations) | GET | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/publish/config` |
| 7 | [Update Publish Configurations](#7-update-publish-configurations) | PUT | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/publish/config` |

> **Note on naming:** "Create Private link" is documented here as **"Create Private URL"**, "Remove Private Link" as **"Remove Private Access"**, "Get Publish Details" as **"Get Publish Configurations"**, and "Update Publish Details" as **"Update Publish Configurations"**. "Make View Public" and "Remove Public Permission" are unrenamed.
>
> **Related APIs not in this document:** [Get View URL](VIEW_OPERATIONS_API_DOC_INFO.md#8-get-view-url) (`GET /publish`) returns the plain in-app view URL and is documented with the View Operations APIs. The embed-URL APIs (`/publish/embed`, `/publish/embedurls`) are documented separately.

---

## 1. Make View Public

Publishes a view as a **Public URL** and, in the same call, defines the read-only permission set, the row-level filter criteria, and the column restrictions that apply to public visitors. Calling it again on an already-public view **updates** the existing public share in place.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/publish/public` |
| **OAuth Scope** | `ZohoAnalytics.embed.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user with Make Public permission on the view. |

### CONFIG Parameters

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `criteria` | String | No | — (no filter) | Row-level filter criteria applied to **every public visitor**, e.g. `"Sales_1"."Region"='West'`. Uses the same syntax as the sharing/report filter criteria. Validated against the view's involved columns — an unparseable criteria or an unknown column is rejected (`8054` / `8154`). |
| `inheritParentFilterCriteria` | Boolean | No | `false` | If `true`, the public visitor additionally inherits any filter criteria already applied on the parent view, on top of `criteria`. |
| `publicPermLevel` | String (enum `1` \| `2` \| `3`) | No | `1` | Audience of the public URL. See [`publicPermLevel` Values](#publicpermlevel-values). |
| `permissions` | JSONObject | No | `read: true`, everything else `false` | Read-only permission set granted to public visitors. `read` must not be `false` (`8074`). See [`permissions` Fields](#permissions-fields). |
| `includeAllColsForVUD` | Boolean | No | `false` | Applies only when `permissions.vud` is `true`. If `true`, "View Underlying Data" shows **all** columns of the underlying table instead of only the columns involved in the report. |
| `vudColumns` | JSONArray | No | — | Applies only when `permissions.vud` is `true`. Restricts "View Underlying Data" to exactly the listed columns. 1–100 entries. See [`vudColumns` / `drillColumns` Fields](#vudcolumns--drillcolumns-fields). |
| `drillColumns` | JSONArray | No | — | Applies only when `permissions.drillDown` is `true`. Restricts drill-down to exactly the listed columns. When omitted, drill-down is limited to the columns involved in the report. 1–100 entries. Same shape as `vudColumns`. |
| `domainName` | String | No | — | Client Portal / White Label domain to publish under. Only usable by a Client Portal admin of the workspace; the returned `publicUrl` is then built on that portal domain instead of the Zoho Analytics domain. Max 200 characters. |
| `validateSystemTags` | Boolean | No | `true` | If `true`, the request is blocked with a confirmation-required error (`8241`) when the view carries a restricted **DATA_WARNING** system tag. Pass `false` to acknowledge the warning and publish anyway. |

> `isListed` (whether a public workspace appears in Zoho Analytics' public listing) is **not** accepted here — set it through [Update Publish Configurations](#7-update-publish-configurations).

#### `publicPermLevel` Values

| Value | Name | Meaning |
|-------|------|---------|
| `1` | Public | Anyone holding the URL, including anonymous visitors who are not signed in to Zoho. This is the default. |
| `2` | Organization Public | Only users signed in to the **same Zoho Analytics organization** as the workspace. Not available on the Free plan (`7531`). |
| `3` | Business Organization Public | Only users belonging to the **same business organization** (the parent Zoho org) as the workspace's Account Admin. Not available on the Free plan (`7531`), and the caller must belong to that same business organization (`7500`). |

> Use [Get Publish Configurations](#6-get-publish-configurations) first to learn which levels are permitted for this workspace: `publicViewConfig.isOrgPublicAllowed` gates level `2` and `publicViewConfig.isBussOrgPublicAllowed` gates level `3`.
>
> In a Client Portal / White Label (custom-domain) request context, `publicPermLevel` is **forced to `1`** regardless of what is sent — the organization-scoped levels are not applicable to portal domains.

#### `permissions` Fields

Only these seven fields are accepted for a public or private link. Every other permission in the general [sharing `permissions` object](SHARING_API_DOC_INFO.md#permissions-fields) (`addRow`, `updateRow`, `deleteRow`, `deleteAllRows`, the four `import*` modes, `share`, `discussion`, `createPreset`) is forced to `false` server-side and cannot be enabled through this API.

| Field | Type | Default | Description |
|-------|------|---------|--------------|
| `read` | Boolean | `true` | View/read access. Always granted. Explicitly sending `read: false` is rejected with `8074` `READ_PERM_SHOULD_BE_TRUE_FOR_SHARING`. |
| `export` | Boolean | `false` | Allows the visitor to export the view's data (CSV / Excel / PDF / image). |
| `vud` | Boolean | `false` | Allows "View Underlying Data" — drilling from an aggregated report into the raw rows behind it. Pair with `includeAllColsForVUD` / `vudColumns` to control which columns are exposed. |
| `drillDown` | Boolean | `false` | Allows drilling down into the view by column values. Pair with `drillColumns` to control which columns can be drilled. |
| `insight` | Boolean | `false` | Allows the visitor to view Zia Insights generated for the view. |
| `drillThrough` | Boolean | `false` | Allows drill-through actions from this view into linked views. **Public links only** — for a private link this field is always forced to `false`. |
| `accessAdminPresets` | Boolean | `false` | Allows the visitor to view/apply presets defined by the view's admin/owner. |

> For custom-role users the requested permission set is additionally **sanitised against the view type** — for example row-level or VUD permissions that make no sense for a dashboard are dropped silently rather than raising an error.

#### `vudColumns` / `drillColumns` Fields

Each is a JSONArray of objects, one per underlying table referenced by the view:

| Field | Type | Mandatory | Description |
|-------|------|-----------|--------------|
| `tableName` | String | **Yes** | Name of the underlying table whose columns are being restricted. Must be a table actually involved in the view (`7138` otherwise). Max 50 characters. |
| `columnNames` | JSONArray of String | **Yes** | Column names from `tableName` to expose. 1–300 entries. Each name must exist in that table (`8154` otherwise). |

### Sample Requests

**Case 1 — `criteria` only: publish a view filtered to a single region**

```http
POST /restapi/v2/workspaces/137687000271334001/views/137687000006991601/publish/public HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "criteria": "\"Sales_1\".\"Region\"='West'"
}
```

**Case 2 — Permissions clubbed together: export + VUD on selected columns + drill-down on selected columns + Zia Insights**

```http
POST /restapi/v2/workspaces/137687000271334001/views/137687000006991650/publish/public HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "permissions": {
        "read": true,
        "export": true,
        "vud": true,
        "drillDown": true,
        "insight": true,
        "drillThrough": true,
        "accessAdminPresets": true
    },
    "includeAllColsForVUD": false,
    "vudColumns": [
        { "tableName": "Sales_1", "columnNames": ["Product", "Region"] }
    ],
    "drillColumns": [
        { "tableName": "Sales_1", "columnNames": ["Product", "Date"] }
    ],
    "inheritParentFilterCriteria": true
}
```

**Case 3 — Organization-only audience (`publicPermLevel: "2"`)**

```http
POST /restapi/v2/workspaces/137687000271334001/views/137687000006991601/publish/public HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "publicPermLevel": "2",
    "permissions": {
        "read": true,
        "export": true
    }
}
```

**Case 4 — White Label / Client Portal: publish on a portal domain**

```http
POST /restapi/v2/workspaces/137687000271334009/views/137687000006991777/publish/public HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "domainName": "portal.customdomain.com",
    "permissions": {
        "read": true,
        "export": true,
        "vud": true
    },
    "validateSystemTags": false
}
```

### Sample Responses

**HTTP 200 OK — Standard workspace (Cases 1–3)**

```json
{
    "status": "success",
    "summary": "Make view public",
    "data": {
        "publicUrl": "https://analytics.zoho.com/open-view/137687000006991601"
    }
}
```

**HTTP 200 OK — White Label / Client Portal (Case 4)**

```json
{
    "status": "success",
    "summary": "Make view public",
    "data": {
        "publicUrl": "https://portal.customdomain.com/open-view/137687000006991777"
    }
}
```

**HTTP 403 Forbidden — Workspace not enabled for the portal domain / user lacks the permission**

```json
{
    "status": "failure",
    "summary": "SECURITY_NOT_PERMITTED",
    "data": {
        "errorCode": 7301,
        "errorMessage": "You (WL_DBAdmin) do not have the permission to do this operation. "
    }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `status` | String | `"success"` on a successful call, `"failure"` on error. |
| `summary` | String | Localised operation summary. `"Make view public"` for this API. |
| `data` | JSONObject | Response payload wrapper. |
| `data.publicUrl` | String | The public URL of the view, in the form `https://<analytics-domain>/open-view/<view-id>`. The host is the Zoho Analytics application domain for a standard workspace, or the workspace's Client Portal / White Label domain when the call is made in a portal context or with `domainName`. **Note:** this value does not encode `publicPermLevel` — the same URL is returned for all three audience levels; the audience restriction is enforced when the URL is opened. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Create *and* update** | Although the operation type is `create`, calling this API on an already-public view **overwrites** the existing public share's permissions, criteria, and column restrictions rather than failing. There is no separate "update public link" API. |
| **Always read-only** | The permission array is sanitised to a read-only set before being persisted. Requesting write permissions has no effect — they are silently dropped, not rejected. |
| **`read` cannot be turned off** | Sending `permissions.read: false` fails with `8074`. Omitting `permissions` entirely grants read-only access. |
| **Column restrictions require the matching permission** | `vudColumns` is ignored unless `permissions.vud` is `true`; `drillColumns` is ignored unless `permissions.drillDown` is `true`. No error is raised for the ignored field. |
| **`publicPermLevel` is forced to `1` on custom domains** | In a Client Portal / White Label request context, the organization-scoped levels (`2`, `3`) are not applicable and the level is overridden to `1`. |
| **`criteria` is validated, `URLCriteria` is not the same thing** | The `criteria` here is a *share-level row filter* stored against the `Public Visitor` pseudo-user. It is unrelated to `URLCriteria` in [Update Publish Configurations](#7-update-publish-configurations), which is a *URL parameter* applied when the published page is rendered. |
| **`domainName` ≠ `ZANALYTICS-DEST-ORGID`** | `domainName` scopes the operation to a Client Portal / White Label domain. It is a completely different mechanism from the `ZANALYTICS-DEST-ORGID` header used by cross-org copy operations (see [Copy Views](VIEW_OPERATIONS_API_DOC_INFO.md#2-copy-views)) — never substitute one for the other. |
| **Verifying the result** | The resulting public share is visible via [Get Shared Details](SHARING_API_DOC_INFO.md#4-get-shared-details) as a `shareInfo` entry with `sharedTo: "Public Visitor"`, `sharedToZuId: "-20"`, and `publicPermLevel` set to the audience level; and via [Get Publish Configurations](#6-get-publish-configurations) as `publicViewConfig.publicPermLevel`. |
| **Dependency chain** | [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → `<view-id>` → (optional) [Get Publish Configurations](#6-get-publish-configurations) to check allowed audience levels → Make View Public. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 6054 | `PUBLISHCNT_VIOLATION` — The current plan does not allow this publish operation. | Upgrade the plan, or publish as a private link instead. |
| 7103 | `META_OBJECT_NOT_PRESENT` — Workspace not found. | Verify `<workspace-id>` and that the `ZANALYTICS-ORGID` header matches it. |
| 7104 | `META_OBJECT_NOT_PRESENT` — View not found. | Verify `<view-id>` exists. |
| 7138 | `META_OBJECT_NOT_PRESENT` — A `tableName` in `vudColumns` / `drillColumns` is not a table involved in this view. | Use only tables that the view actually reads from. |
| 7301 | `SECURITY_NOT_PERMITTED` — The user cannot make this view public (no Make Public permission, or the workspace/view is restricted). | Ensure the user is an Account Admin, Organization Admin, Workspace Admin, or has Make Public permission on the view. |
| 7319 | `OBJID_NOT_BELONGS_TO_DB` — The view does not belong to the specified workspace. | Ensure `<workspace-id>` and `<view-id>` are consistent. |
| 7500 | `UNAUTHORIZED_ORG_CANNOT_MAKEPUBLIC` — `publicPermLevel: "3"` requested but the caller does not belong to the workspace admin's business organization. | Use `publicPermLevel` `1` or `2`, or call as a user of the same business organization. |
| 7531 | `PUBLIC_TO_ORG_NOT_SUPPORTED_IN_FREE` — `publicPermLevel` `2` or `3` is not supported on the Free plan. | Upgrade the plan, or use `publicPermLevel: "1"`. |
| 7565 | `UNVERIFIED_EMAIL` — The calling user's primary email address is not verified. | Verify the account's primary email address and retry. |
| 8054 | `INVALID_FILTER_CRITERIA` — `criteria` could not be parsed. | Correct the criteria syntax (e.g. `"Table"."Column"='Value'`). |
| 8060 | `DOMAIN_NOT_EXIST` — The `domainName` supplied does not exist. | Use a domain returned by the [Domain and White Label APIs](DOMAIN_AND_WHITELABEL_API_DOC_INFO.md). |
| 8061 | `DOMAIN_DOES_NOT_BELONGS_TO_USER` — The caller is not an admin of the supplied `domainName`. | Call as an admin of that portal domain, or omit `domainName`. |
| 8074 | `READ_PERM_SHOULD_BE_TRUE_FOR_SHARING` — `permissions.read` was sent as `false`. | Omit `read` or set it to `true`. |
| 8080 | `INVALID_JSON_CONFIGURATION` — CONFIG is not valid JSON, contains an unsupported key, or violates a type/length/allowed-value constraint (e.g. `publicPermLevel` outside `1`/`2`/`3`). | Send only the documented keys with the documented types. |
| 8088 | `SECURITY_CONTROLS_FEATURE_DISABLED` — Public sharing has been disabled for this organization/workspace by security controls. | Ask the Organization Admin to re-enable public sharing in Security Controls. |
| 8154 | `COLUMN_NOT_PRESENT_IN_TABLE` — A column in `vudColumns` / `drillColumns` (or in `criteria`) does not exist in the given table. | Verify column names via [Get Columns](COLUMNS_API_DOC_INFO.md). |
| 8241 | `SYSTEM_TAG_DATA_WARNING_V2_VALIDATION_CONFIRMATION` — The view carries a restricted DATA_WARNING system tag. | Review the warning, then resend with `"validateSystemTags": false` to confirm. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.embed.create`. |
| 12052 | `WORKSPACE_NOT_ENABLED_FOR_DOMAIN_ACCESS` — The workspace is not enabled for access through the requested portal domain. | Enable the workspace for that Client Portal domain first. |

---

## 2. Remove Public Permission

Un-publishes the view's **Public URL**, revoking access for all public visitors. The private link (if any) and the publish configuration are left untouched.

| Attribute | Value |
|-----------|-------|
| **Method** | DELETE |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/publish/public` |
| **OAuth Scope** | `ZohoAnalytics.embed.delete` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user with Make Public permission on the view, or any user with Share permission on the view. |

> This API has no CONFIG parameter. All inputs are provided via URL path parameters only.

### Sample Requests

**Case 1 — Standard workspace**

```http
DELETE /restapi/v2/workspaces/137687000271334001/views/137687000006991601/publish/public HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — White Label / Client Portal workspace**

```http
DELETE /restapi/v2/workspaces/137687000271334009/views/137687000006991777/publish/public HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

```
HTTP/1.1 204 No Content
```

**HTTP 403 Forbidden — Failure responses still carry a JSON body**

```json
{
    "status": "failure",
    "summary": "SECURITY_NOT_PERMITTED",
    "data": {
        "errorCode": 7301,
        "errorMessage": "You (WL_DBAdmin) do not have the permission to do this operation. "
    }
}
```

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload (`status`, `summary`, `data.errorCode`, `data.errorMessage`).

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Remove Public Permission returns a bare HTTP `204 No Content` — no `status`/`summary` JSON to parse. |
| **Not idempotent when the view has no shares at all** | If the view is not shared to anyone (no users, no groups, no public/private link), the call fails with `8032` `VIEW_NOT_SHARED` rather than succeeding silently. If the view has other shares but is not public, the public entry is simply not found and the call completes without error. |
| **Only the public channel is removed** | An active private link on the same view survives this call — remove it with [Remove Private Access](#5-remove-private-access). |
| **Publish configuration survives** | The presentation settings read by [Get Publish Configurations](#6-get-publish-configurations) are not reset; re-publishing the view later reuses them. |
| **Audience level is irrelevant** | The same call removes a level-`1`, level-`2`, or level-`3` public share; there is no per-level removal. |
| **Dependency chain** | [Get Publish Configurations](#6-get-publish-configurations) (confirm `publicViewConfig.publicPermLevel > 0`) → Remove Public Permission. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7103 | `META_OBJECT_NOT_PRESENT` — Workspace not found. | Verify `<workspace-id>` and the `ZANALYTICS-ORGID` header. |
| 7104 | `META_OBJECT_NOT_PRESENT` — View not found. | Verify `<view-id>` exists. |
| 7301 | `SECURITY_NOT_PERMITTED` — The user cannot un-publish this view. | Ensure the user is an Account Admin, Organization Admin, Workspace Admin, or has Make Public / Share permission on the view. |
| 7319 | `OBJID_NOT_BELONGS_TO_DB` — The view does not belong to the specified workspace. | Ensure `<workspace-id>` and `<view-id>` are consistent. |
| 7565 | `UNVERIFIED_EMAIL` — The calling user's primary email address is not verified. | Verify the account's primary email address and retry. |
| 8032 | `VIEW_NOT_SHARED` — The view is not shared to anyone, so there is no public permission to remove. | Confirm the view is public via [Get Publish Configurations](#6-get-publish-configurations) before calling. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.embed.delete`. |

---

## 3. Get Private URL

Returns the existing **Private URL** of a view — the `open-view` URL with the view's secret 32-character private key appended. Read-only: it neither creates nor regenerates a key.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/publish/privatelink` |
| **OAuth Scope** | `ZohoAnalytics.embed.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user with Publish permission on the view. |

### CONFIG Parameters

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `domainName` | String | No | — | Client Portal / White Label domain to build the URL on. Only usable by a Client Portal admin of the workspace. Max 200 characters. Preferred over `withCustomDomain`. |
| `withCustomDomain` | Boolean | No | `false` | **Legacy flag.** If `true`, builds the URL on the workspace's configured portal domain without naming it. Requires the caller to be an Organization Admin or Super Admin **and** a Client Portal admin of the workspace. Prefer `domainName`. |

> This API has no `criteria` parameter — a private link's row filter is set when the link is created (see [Create Private URL](#4-create-private-url)).

### Sample Requests

**Case 1 — Standard workspace (no CONFIG)**

```http
GET /restapi/v2/workspaces/137687000271334001/views/137687000006991601/publish/privatelink HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — White Label / Client Portal: build the URL on a named portal domain**

```http
GET /restapi/v2/workspaces/137687000271334009/views/137687000006991777/publish/privatelink?CONFIG={"domainName":"portal.customdomain.com"} HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
```

**Case 3 — Legacy `withCustomDomain` flag (Organization Admin who is also the portal admin)**

```http
GET /restapi/v2/workspaces/137687000271334009/views/137687000006991777/publish/privatelink?CONFIG={"withCustomDomain":true} HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
```

### Sample Responses

**HTTP 200 OK — Standard workspace (Case 1)**

```json
{
    "status": "success",
    "summary": "Get private URL",
    "data": {
        "privateUrl": "https://analytics.zoho.com/open-view/137687000006991601/a23b4e7affbdcec6c12e5106e9c25f91"
    }
}
```

**HTTP 200 OK — White Label / Client Portal (Cases 2 and 3)**

```json
{
    "status": "success",
    "summary": "Get private URL",
    "data": {
        "privateUrl": "https://portal.customdomain.com/open-view/137687000006991777/062960d2243fe19312ef9d18d0b5a5b7"
    }
}
```

**HTTP 404 Not Found — The view has no private link yet**

```json
{
    "status": "failure",
    "summary": "VIEW_NOT_PUBLISHED_AS_PRIVATE",
    "data": {
        "errorCode": 8115,
        "errorMessage": "This view is not published as a private link."
    }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `status` | String | `"success"` on a successful call, `"failure"` on error. |
| `summary` | String | Localised operation summary. `"Get private URL"` for this API. |
| `data` | JSONObject | Response payload wrapper. |
| `data.privateUrl` | String | The private URL of the view, in the form `https://<analytics-domain>/open-view/<view-id>/<private-key>`. `<private-key>` is a 32-character lowercase hexadecimal secret. The host is the Zoho Analytics application domain for a standard workspace, or the portal domain in a Client Portal / White Label context. **Treat this value as a secret** — anyone holding it can open the view (subject to the link's password and expiry date, if configured). |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Read-only — never creates a link** | If the view has no private key, this API fails with `8115` instead of generating one. Use [Create Private URL](#4-create-private-url) to create the link first. |
| **Stable key** | Repeated calls return the same URL. The key changes only when [Create Private URL](#4-create-private-url) is called with `regenerateKey: true`. |
| **Password and expiry are not returned here** | This API returns only the URL. To read whether a password or expiry date is configured, and whether the link has expired, use [Get Publish Configurations](#6-get-publish-configurations) (`privateLinkConfig`). |
| **Expired links still return a URL** | An expired private link still has a key, so this API returns HTTP 200 with the URL. Check `privateLinkConfig.isExpired` in [Get Publish Configurations](#6-get-publish-configurations) to detect expiry. |
| **No email-verification requirement** | Unlike the mutating publish APIs, this read-only API does not require the caller's primary email to be verified. |
| **`withCustomDomain` is stricter than `domainName`** | The legacy flag additionally requires the caller to be an Organization Admin or Super Admin; `domainName` only requires portal-domain admin rights. Prefer `domainName` in new integrations. |
| **Dependency chain** | [Create Private URL](#4-create-private-url) → Get Private URL. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7103 | `META_OBJECT_NOT_PRESENT` — Workspace not found. | Verify `<workspace-id>` and the `ZANALYTICS-ORGID` header. |
| 7104 | `META_OBJECT_NOT_PRESENT` — View not found. | Verify `<view-id>` exists. |
| 7301 | `SECURITY_NOT_PERMITTED` — The user does not have Publish permission on the view. | Ensure the user is an Account Admin, Organization Admin, Workspace Admin, or has Publish permission on the view. |
| 7319 | `OBJID_NOT_BELONGS_TO_DB` — The view does not belong to the specified workspace. | Ensure `<workspace-id>` and `<view-id>` are consistent. |
| 8060 | `DOMAIN_NOT_EXIST` — The `domainName` supplied does not exist. | Use a domain returned by the [Domain and White Label APIs](DOMAIN_AND_WHITELABEL_API_DOC_INFO.md). |
| 8061 | `DOMAIN_DOES_NOT_BELONGS_TO_USER` — The caller is not an admin of the supplied `domainName`. | Call as an admin of that portal domain, or omit `domainName`. |
| 8080 | `INVALID_JSON_CONFIGURATION` — CONFIG is not valid JSON or contains an unsupported key. | Send only `domainName` and/or `withCustomDomain`. |
| 8115 | `VIEW_NOT_PUBLISHED_AS_PRIVATE` — The view has no private link. | Call [Create Private URL](#4-create-private-url) first. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.embed.read`. |
| 12052 | `WORKSPACE_NOT_ENABLED_FOR_DOMAIN_ACCESS` — The workspace is not enabled for access through the requested portal domain. | Enable the workspace for that Client Portal domain first. |

---

## 4. Create Private URL

Creates a **Private URL** for a view — generating the secret private key if one does not exist — and, in the same call, sets the link's permission set, row-level filter criteria, column restrictions, password, and expiry date. The freshly built private URL is returned in the response.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/publish/privatelink` |
| **OAuth Scope** | `ZohoAnalytics.embed.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user with Publish permission on the view. |

### CONFIG Parameters

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `criteria` | String | No | `""` (no filter) | Row-level filter criteria applied to **every private-link visitor**, e.g. `"Sales_1"."Region"='West'`. Only applied when `permissions` is being (re)written — that is, on first creation or when `permissions` is present in the request. |
| `permissions` | JSONObject | No | `read: true`, everything else `false` | Read-only permission set granted to private-link visitors. `read` must not be `false` (`8074`). See [`permissions` Fields](#permissions-fields) — note that `drillThrough` is always forced to `false` for a private link. |
| `includeAllColsForVUD` | Boolean | No | `false` | Applies only when `permissions.vud` is `true`. If `true`, "View Underlying Data" shows **all** columns of the underlying table instead of only the columns involved in the report. |
| `vudColumns` | JSONArray | No | — | Applies only when `permissions.vud` is `true`. Restricts "View Underlying Data" to exactly the listed columns. 1–100 entries. See [`vudColumns` / `drillColumns` Fields](#vudcolumns--drillcolumns-fields). |
| `drillColumns` | JSONArray | No | — | Applies only when `permissions.drillDown` is `true`. Restricts drill-down to exactly the listed columns. When omitted, drill-down is limited to the columns involved in the report. 1–100 entries. Same shape as `vudColumns`. |
| `password` | String | No | — (no password) | Password the visitor must enter before the view is rendered. **Minimum 6 characters**, maximum 256. Setting or changing the password invalidates all existing private-link sessions. Mutually exclusive with `removePassword`. |
| `removePassword` | Boolean | No | `false` | If `true` (and `password` is not supplied), removes the existing password so the link opens without a prompt. Ignored when `password` is present. |
| `expiryDate` | String | No | — (never expires) | Date on which the link stops working, in **`dd/MM/yyyy`** format interpreted in **GMT**. The link remains usable until the end of that day. Mutually exclusive with `removeExpiryDate`. |
| `removeExpiryDate` | Boolean | No | `false` | If `true` (and `expiryDate` is not supplied), removes the existing expiry date so the link never expires. Ignored when `expiryDate` is present. |
| `regenerateKey` | Boolean | No | `false` | If `true`, discards the existing private key and generates a new one — instantly invalidating every previously distributed private URL for this view. Has no effect on first creation (a key is generated regardless). |
| `domainName` | String | No | — | Client Portal / White Label domain to build the returned URL on. Only usable by a Client Portal admin of the workspace. Max 200 characters. |
| `withCustomDomain` | Boolean | No | `false` | **Legacy flag.** If `true`, builds the returned URL on the workspace's configured portal domain without naming it. Requires the caller to be an Organization Admin or Super Admin **and** a Client Portal admin of the workspace. Prefer `domainName`. |
| `validateSystemTags` | Boolean | No | `true` | If `true`, the request is blocked with a confirmation-required error (`8241`) when the view carries a restricted **DATA_WARNING** system tag. Pass `false` to acknowledge the warning and create the link anyway. |

### Sample Requests

**Case 1 — `criteria` only: create a private link restricted to a single region**

```http
POST /restapi/v2/workspaces/137687000271334001/views/137687000006991601/publish/privatelink HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "criteria": "\"Sales_1\".\"Region\"='West'"
}
```

**Case 2 — Permissions clubbed together: export + VUD on selected columns + drill-down on selected columns + Zia Insights + admin presets**

```http
POST /restapi/v2/workspaces/137687000271334001/views/137687000006991650/publish/privatelink HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "permissions": {
        "read": true,
        "export": true,
        "vud": true,
        "drillDown": true,
        "insight": true,
        "accessAdminPresets": true
    },
    "includeAllColsForVUD": false,
    "vudColumns": [
        { "tableName": "Sales_1", "columnNames": ["Product", "Region"] }
    ],
    "drillColumns": [
        { "tableName": "Sales_1", "columnNames": ["Product", "Date"] }
    ]
}
```

**Case 3 — Security options clubbed together: rotate the key, set a password, and set an expiry date**

```http
POST /restapi/v2/workspaces/137687000271334001/views/137687000006991601/publish/privatelink HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "regenerateKey": true,
    "password": "Qwertyui",
    "expiryDate": "20/11/2030"
}
```

**Case 4 — White Label / Client Portal: create the link on a portal domain**

```http
POST /restapi/v2/workspaces/137687000271334009/views/137687000006991777/publish/privatelink HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "domainName": "portal.customdomain.com",
    "permissions": {
        "read": true,
        "export": true
    },
    "password": "Portal@2030",
    "validateSystemTags": false
}
```

### Sample Responses

**HTTP 200 OK — Standard workspace (Cases 1–3)**

```json
{
    "status": "success",
    "summary": "Create private URL",
    "data": {
        "privateUrl": "https://analytics.zoho.com/open-view/137687000006991601/deae5f6151ddf291528b8f11a18d3419"
    }
}
```

**HTTP 200 OK — White Label / Client Portal (Case 4)**

```json
{
    "status": "success",
    "summary": "Create private URL",
    "data": {
        "privateUrl": "https://portal.customdomain.com/open-view/137687000006991777/de59081dec264798a5475c3c2c0b43e1"
    }
}
```

**HTTP 403 Forbidden — Publish disabled for the workspace / user lacks the permission**

```json
{
    "status": "failure",
    "summary": "SECURITY_NOT_PERMITTED",
    "data": {
        "errorCode": 7301,
        "errorMessage": "You (WL_DBAdmin) do not have the permission to do this operation. "
    }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `status` | String | `"success"` on a successful call, `"failure"` on error. |
| `summary` | String | Localised operation summary. `"Create private URL"` for this API. |
| `data` | JSONObject | Response payload wrapper. |
| `data.privateUrl` | String | The private URL of the view, in the form `https://<analytics-domain>/open-view/<view-id>/<private-key>`. When `regenerateKey: true` was sent, this contains the **new** key and every previously distributed URL is dead. **Treat this value as a secret.** The response never echoes back the `password` or `expiryDate` that were set — read those back via [Get Publish Configurations](#6-get-publish-configurations). |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Idempotent creation, incremental update** | On a view with no private link, this API generates a key and applies the full permission set. On a view that already has a link, the key is reused (unless `regenerateKey: true`) and `permissions` / `criteria` / column restrictions are only rewritten when `permissions` is present in the request. Password and expiry are applied whenever their fields are present. |
| **`criteria` needs `permissions`** | Because the row filter is persisted as part of the private-link share record, sending `criteria` **without** `permissions` on an already-existing link leaves the criteria unchanged. Send `permissions` (at minimum `{"read": true}`) alongside `criteria` when updating an existing link. |
| **`drillThrough` is always off** | Unlike a public link, a private link can never be granted `drillThrough` — the value is forced to `false` regardless of what is sent. |
| **`password` wins over `removePassword`; `expiryDate` wins over `removeExpiryDate`** | If both are sent, the setter is applied and the remover is ignored — no error is raised. |
| **Password minimum length is enforced by the template** | A `password` shorter than 6 characters is rejected with `8080` `INVALID_JSON_CONFIGURATION`, not with a password-specific error. |
| **Setting a password kills live sessions** | Changing the password clears all existing private-link sessions, so visitors currently viewing the page must re-authenticate. |
| **`expiryDate` is GMT and end-of-day inclusive** | `"20/11/2030"` is stored as the last usable moment of 20 Nov 2030 GMT, not as midnight at its start. |
| **`regenerateKey` is destructive and immediate** | Every URL handed out earlier stops working the moment the new key is persisted. There is no grace period and no way to recover the old key. |
| **Plan limits apply to private links** | Creating a *new* private link consumes one of the organization's allotted private links (`6121` / `6122` when exhausted). Regenerating an existing key does not consume a new allotment but is itself plan-gated (`6055` / `6057`). |
| **A separate PUT endpoint also exists** | `PUT /publish/privatelink` ("Update Private Link Configurations") updates an existing private link and fails with `8115` if none exists. It is not covered by this document; this POST API covers both creation and update. |
| **Verifying the result** | The resulting private share is visible via [Get Shared Details](SHARING_API_DOC_INFO.md#4-get-shared-details) as a `shareInfo` entry with `sharedTo: "Private Link"`, `sharedToZuId: "-30"`, and `publicPermLevel: 0`; the password/expiry state is visible via [Get Publish Configurations](#6-get-publish-configurations) (`privateLinkConfig`). |
| **Dependency chain** | [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → `<view-id>` → Create Private URL → [Get Private URL](#3-get-private-url) / [Get Publish Configurations](#6-get-publish-configurations). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 6055 | `REGENERATE_VIOLATION` — The current plan does not allow regenerating a private-link key. | Upgrade the plan, or omit `regenerateKey`. |
| 6057 | `SHAREDUSR_REGENERATE_VIOLATION` — A shared user attempted a plan-restricted key regeneration. | Ask the workspace owner to regenerate the key, or upgrade the plan. |
| 6054 | `PUBLISHCNT_VIOLATION` — The current plan does not allow private links. | Upgrade the plan. |
| 6056 | `SHAREDUSR_PUBLISHCNT_VIOLATION` — A shared user attempted a plan-restricted private-link creation. | Ask the workspace owner to create the link, or upgrade the plan. |
| 6121 | `EXCEEDING_USR_PLN_PRIVATE_LINKS` — The organization has used all private links allowed by its plan. | Remove an unused private link via [Remove Private Access](#5-remove-private-access), or upgrade the plan. |
| 6122 | `EXCEEDING_USR_PLN_PRIVATE_LINKS_DM` — Same limit, reported to a non-super-admin caller. | Ask the Organization Admin to free up a private link or upgrade the plan. |
| 7103 | `META_OBJECT_NOT_PRESENT` — Workspace not found. | Verify `<workspace-id>` and the `ZANALYTICS-ORGID` header. |
| 7104 | `META_OBJECT_NOT_PRESENT` — View not found. | Verify `<view-id>` exists. |
| 7138 | `META_OBJECT_NOT_PRESENT` — A `tableName` in `vudColumns` / `drillColumns` is not a table involved in this view. | Use only tables that the view actually reads from. |
| 7301 | `SECURITY_NOT_PERMITTED` — The user does not have Publish permission on the view, or publishing is restricted for the workspace. | Ensure the user is an Account Admin, Organization Admin, Workspace Admin, or has Publish permission on the view. |
| 7319 | `OBJID_NOT_BELONGS_TO_DB` — The view does not belong to the specified workspace. | Ensure `<workspace-id>` and `<view-id>` are consistent. |
| 7565 | `UNVERIFIED_EMAIL` — The calling user's primary email address is not verified. | Verify the account's primary email address and retry. |
| 8054 | `INVALID_FILTER_CRITERIA` — `criteria` could not be parsed. | Correct the criteria syntax (e.g. `"Table"."Column"='Value'`). |
| 8060 | `DOMAIN_NOT_EXIST` — The `domainName` supplied does not exist. | Use a domain returned by the [Domain and White Label APIs](DOMAIN_AND_WHITELABEL_API_DOC_INFO.md). |
| 8061 | `DOMAIN_DOES_NOT_BELONGS_TO_USER` — The caller is not an admin of the supplied `domainName`. | Call as an admin of that portal domain, or omit `domainName`. |
| 8074 | `READ_PERM_SHOULD_BE_TRUE_FOR_SHARING` — `permissions.read` was sent as `false`. | Omit `read` or set it to `true`. |
| 8080 | `INVALID_JSON_CONFIGURATION` — CONFIG is not valid JSON, contains an unsupported key, or violates a constraint (e.g. `password` shorter than 6 characters, malformed `expiryDate`). | Send only the documented keys with the documented types and formats. |
| 8088 | `SECURITY_CONTROLS_FEATURE_DISABLED` — Private links have been disabled for this organization/workspace by security controls. | Ask the Organization Admin to re-enable private links in Security Controls. |
| 8154 | `COLUMN_NOT_PRESENT_IN_TABLE` — A column in `vudColumns` / `drillColumns` (or in `criteria`) does not exist in the given table. | Verify column names via [Get Columns](COLUMNS_API_DOC_INFO.md). |
| 8241 | `SYSTEM_TAG_DATA_WARNING_V2_VALIDATION_CONFIRMATION` — The view carries a restricted DATA_WARNING system tag. | Review the warning, then resend with `"validateSystemTags": false` to confirm. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.embed.update`. |
| 12052 | `WORKSPACE_NOT_ENABLED_FOR_DOMAIN_ACCESS` — The workspace is not enabled for access through the requested portal domain. | Enable the workspace for that Client Portal domain first. |

---

## 5. Remove Private Access

Removes the view's **Private URL** entirely — the private key, the associated permission set, the password, and the expiry date. Every previously distributed private URL for the view stops working. The public URL (if any) and the publish configuration are left untouched.

| Attribute | Value |
|-----------|-------|
| **Method** | DELETE |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/publish/privatelink` |
| **OAuth Scope** | `ZohoAnalytics.embed.delete` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user with Publish permission on the workspace, or any user with Share permission on the view. |

> This API has no CONFIG parameter. All inputs are provided via URL path parameters only.

### Sample Requests

**Case 1 — Standard workspace**

```http
DELETE /restapi/v2/workspaces/137687000271334001/views/137687000006991601/publish/privatelink HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — White Label / Client Portal workspace**

```http
DELETE /restapi/v2/workspaces/137687000271334009/views/137687000006991777/publish/privatelink HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

```
HTTP/1.1 204 No Content
```

**HTTP 404 Not Found — The view has no private link**

```json
{
    "status": "failure",
    "summary": "VIEW_NOT_PUBLISHED_AS_PRIVATE",
    "data": {
        "errorCode": 8115,
        "errorMessage": "This view is not published as a private link."
    }
}
```

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload (`status`, `summary`, `data.errorCode`, `data.errorMessage`).

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Remove Private Access returns a bare HTTP `204 No Content` — no `status`/`summary` JSON to parse. |
| **Not idempotent** | Calling it on a view that has no private link fails with `8115` `VIEW_NOT_PUBLISHED_AS_PRIVATE`. Check `privateLinkConfig.isPrivate` via [Get Publish Configurations](#6-get-publish-configurations) first if you need a safe repeat. |
| **Password and expiry go with the link** | There is no separate "remove password" or "remove expiry" call needed — both are discarded along with the link. (To clear them while keeping the link alive, use `removePassword` / `removeExpiryDate` on [Create Private URL](#4-create-private-url).) |
| **Frees a plan allotment** | Removing a private link releases one of the organization's allotted private links, so a subsequent [Create Private URL](#4-create-private-url) that previously failed with `6121`/`6122` may then succeed. |
| **Permission check is workspace-level for Publish** | The Publish permission is evaluated at the **workspace** level for this API (unlike [Get Private URL](#3-get-private-url) and [Create Private URL](#4-create-private-url), which evaluate it per view). A custom-role user with Publish or Make Public permission on the specific view is also accepted. |
| **Only the private channel is removed** | An active public URL on the same view survives this call — remove it with [Remove Public Permission](#2-remove-public-permission). |
| **Dependency chain** | [Get Publish Configurations](#6-get-publish-configurations) (confirm `privateLinkConfig.isPrivate` is `true`) → Remove Private Access. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7103 | `META_OBJECT_NOT_PRESENT` — Workspace not found. | Verify `<workspace-id>` and the `ZANALYTICS-ORGID` header. |
| 7104 | `META_OBJECT_NOT_PRESENT` — View not found. | Verify `<view-id>` exists. |
| 7301 | `SECURITY_NOT_PERMITTED` — The user does not have Publish permission on the workspace or Share permission on the view. | Ensure the user is an Account Admin, Organization Admin, Workspace Admin, or has Publish / Share permission. |
| 7319 | `OBJID_NOT_BELONGS_TO_DB` — The view does not belong to the specified workspace. | Ensure `<workspace-id>` and `<view-id>` are consistent. |
| 7565 | `UNVERIFIED_EMAIL` — The calling user's primary email address is not verified. | Verify the account's primary email address and retry. |
| 8115 | `VIEW_NOT_PUBLISHED_AS_PRIVATE` — The view has no private link. | Nothing to remove; the link is already absent. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.embed.delete`. |

---

## 6. Get Publish Configurations

Returns the complete publish state of a view in one call: the **public** channel's audience and listing state, the **private** channel's password/expiry state, and the **presentation configuration** used to render the published page.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/publish/config` |
| **OAuth Scope** | `ZohoAnalytics.embed.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user with Publish permission on the view, or any user with Make Public permission on the view. |

> This API has no CONFIG parameter. All inputs are provided via URL path parameters only.

### Sample Requests

**Case 1 — Standard workspace**

```http
GET /restapi/v2/workspaces/137687000271334001/views/137687000006991601/publish/config HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — White Label / Client Portal workspace**

```http
GET /restapi/v2/workspaces/137687000271334009/views/137687000006991777/publish/config HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
```

### Sample Responses

**HTTP 200 OK — Paid organization, view not yet published (Case 1)**

```json
{
    "status": "success",
    "summary": "Get publish configurations",
    "data": {
        "publicViewConfig": {
            "publicPermLevel": 0,
            "isListed": false,
            "isOrgPublicAllowed": true,
            "orgName": "AcmeAnalytics",
            "isBussOrgPublicAllowed": false,
            "businessOrgName": ""
        },
        "privateLinkConfig": {
            "isPrivate": false,
            "isExpired": false,
            "password": "-1",
            "expiryDate": "-1"
        },
        "publishConfig": {
            "includeTitle": true,
            "includeDesc": true,
            "includeToolBar": false,
            "includeSocialWidgets": false,
            "includeSearchBox": false,
            "includeDatatypeSymbol": false,
            "includeShowHideOption": false,
            "isInteractive": true,
            "legendPosition": "RIGHT",
            "width": 800,
            "height": 600,
            "autoRefresh": -1,
            "URLCriteria": "",
            "includeAskZia": true
        }
    }
}
```

**HTTP 200 OK — Private link active with a password (after [Create Private URL](#4-create-private-url) Case 3)**

```json
{
    "status": "success",
    "summary": "Get publish configurations",
    "data": {
        "publicViewConfig": {
            "publicPermLevel": 0,
            "isListed": false,
            "isOrgPublicAllowed": true,
            "orgName": "AcmeAnalytics",
            "isBussOrgPublicAllowed": false,
            "businessOrgName": ""
        },
        "privateLinkConfig": {
            "isPrivate": true,
            "isExpired": false,
            "password": "Qwertyui",
            "expiryDate": "20/11/2030"
        },
        "publishConfig": {
            "includeTitle": true,
            "includeDesc": true,
            "includeToolBar": false,
            "includeSocialWidgets": false,
            "includeSearchBox": false,
            "includeDatatypeSymbol": false,
            "includeShowHideOption": false,
            "isInteractive": true,
            "legendPosition": "RIGHT",
            "width": 800,
            "height": 600,
            "autoRefresh": -1,
            "URLCriteria": "",
            "includeAskZia": true
        }
    }
}
```

**HTTP 200 OK — Free plan: `privateLinkConfig` is omitted and `isListed` is forced to `true`**

```json
{
    "status": "success",
    "summary": "Get publish configurations",
    "data": {
        "publicViewConfig": {
            "publicPermLevel": 0,
            "isListed": true,
            "isOrgPublicAllowed": false,
            "orgName": "AcmeFreeOrg",
            "isBussOrgPublicAllowed": false,
            "businessOrgName": ""
        },
        "publishConfig": {
            "includeTitle": true,
            "includeDesc": true,
            "includeToolBar": false,
            "includeSocialWidgets": false,
            "includeSearchBox": false,
            "includeDatatypeSymbol": false,
            "includeShowHideOption": false,
            "isInteractive": true,
            "legendPosition": "RIGHT",
            "width": 800,
            "height": 600,
            "autoRefresh": -1,
            "URLCriteria": "",
            "includeAskZia": true
        }
    }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `status` | String | `"success"` on a successful call, `"failure"` on error. |
| `summary` | String | Localised operation summary. `"Get publish configurations"` for this API. |
| `data` | JSONObject | Response payload wrapper. |
| `data.publicViewConfig` | JSONObject | Public-channel state. **Present only if the caller has Make Public permission on the workspace** — absent otherwise. |
| `publicViewConfig.publicPermLevel` | Number | Current public audience of the view: `0` = not public, `1` = Public (anyone with the link), `2` = Organization Public, `3` = Business Organization Public. See [`publicPermLevel` Values](#publicpermlevel-values). |
| `publicViewConfig.isListed` | Boolean | `true` when the workspace's public views are discoverable in Zoho Analytics' public listing. Forced to `true` and not editable on the Free plan (and non-CRM-Plus-Starter free tiers). Settable via [Update Publish Configurations](#7-update-publish-configurations) only while the workspace is public. |
| `publicViewConfig.isOrgPublicAllowed` | Boolean | `true` when `publicPermLevel: "2"` (Organization Public) may be requested. `false` on the Free plan and in Client Portal / White Label (custom-domain) contexts. |
| `publicViewConfig.orgName` | String | Display name of the Zoho Analytics organization that owns the workspace — used to label the "Organization Public" audience in a UI. |
| `publicViewConfig.isBussOrgPublicAllowed` | Boolean | `true` when `publicPermLevel: "3"` (Business Organization Public) may be requested. Requires a paid plan, a non-custom-domain context, and the caller to belong to the same business organization as the workspace's Account Admin. |
| `publicViewConfig.businessOrgName` | String | Display name of the parent business organization. Empty string `""` when `isBussOrgPublicAllowed` is `false`. |
| `data.privateLinkConfig` | JSONObject | Private-channel state. **Present only if private links are permitted for this organization/workspace *and* the caller has Publish permission on the workspace** — absent otherwise (see the Free-plan sample above). |
| `privateLinkConfig.isPrivate` | Boolean | `true` when the view currently has a private link (a private key exists). |
| `privateLinkConfig.isExpired` | Boolean | `true` when an expiry date is set and has already passed. Always `false` when no expiry date is configured. |
| `privateLinkConfig.password` | String | The private link's password **in clear text**, or the sentinel `"-1"` when no password is set. Treat this field as sensitive and never log or surface it to unauthorised users. |
| `privateLinkConfig.expiryDate` | String | The expiry date in `dd/MM/yyyy` format (GMT), or the sentinel `"-1"` when the link never expires. |
| `data.publishConfig` | JSONObject | Presentation configuration of the published page. **Always present**, for every caller. Shared by the public URL, the private URL, and the embed URL. |
| `publishConfig.includeTitle` | Boolean | Whether the view's title is rendered on the published page. |
| `publishConfig.includeDesc` | Boolean | Whether the view's description is rendered on the published page. |
| `publishConfig.includeToolBar` | Boolean | Whether the toolbar is rendered. Stored internally as its inverse (`REMTOOLBAR`); the API always presents the positive `includeToolBar` form. |
| `publishConfig.includeSocialWidgets` | Boolean | Whether social share widgets are rendered. |
| `publishConfig.includeSearchBox` | Boolean | Whether a search box is rendered. Applies to table-type views and tabular reports only; ignored for charts and dashboards. |
| `publishConfig.includeDatatypeSymbol` | Boolean | Whether each column header shows its data-type symbol. Table-type views and tabular reports only. |
| `publishConfig.includeShowHideOption` | Boolean | Whether the visitor can show/hide columns. Table-type views and tabular reports only. |
| `publishConfig.isInteractive` | Boolean | Whether the published chart is interactive (hover, tooltips, zoom) rather than a static rendering. Meaningful for chart views only — **always `true` for every other view type**. |
| `publishConfig.legendPosition` | String | Legend placement for chart views, as an uppercase alphabetic keyword. `"RIGHT"` is the default returned when nothing has been configured. Ignored for non-chart views. |
| `publishConfig.width` | Number | Rendering width in pixels. Default `800`. |
| `publishConfig.height` | Number | Rendering height in pixels. Default `600`. |
| `publishConfig.autoRefresh` | Number | Auto-refresh interval in **seconds**. `-1` means no auto-refresh (the default). Any other value is at least `120`. |
| `publishConfig.URLCriteria` | String | Row-level filter criteria applied as a URL parameter when the published page is rendered. Empty string `""` when none is configured. **Distinct from** the share-level `criteria` set by [Make View Public](#1-make-view-public) / [Create Private URL](#4-create-private-url). |
| `publishConfig.includeAskZia` | Boolean | Whether the Ask Zia conversational-analytics widget is available on the published page. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Two of the three blocks are conditional** | `publicViewConfig` appears only when the caller has Make Public permission on the workspace; `privateLinkConfig` appears only when private links are permitted **and** the caller has Publish permission on the workspace. `publishConfig` is always present. Code defensively — do not assume all three keys exist. |
| **`publicPermLevel: 0` is a read-only sentinel** | `0` (not public) is returned by this API but is **not** a valid input to [Make View Public](#1-make-view-public), whose `publicPermLevel` accepts only `1`, `2`, or `3`. To move a view to "not public", call [Remove Public Permission](#2-remove-public-permission). |
| **`password` is returned in clear text** | The private-link password is decrypted for this response. This is by design (so an admin UI can display it), but it makes the response sensitive — avoid logging it and restrict who may call this API. |
| **`"-1"` sentinels, not `null`** | `privateLinkConfig.password` and `privateLinkConfig.expiryDate` are the string `"-1"` when unset — never `null` and never absent while `privateLinkConfig` itself is present. |
| **Defaults reported before the first update differ from update-time defaults** | Until [Update Publish Configurations](#7-update-publish-configurations) has been called for the view, no publish data is stored and this API reports its own read-time defaults — notably `includeSearchBox: false` and `includeAskZia: true`. The update API's own defaults for those two fields are the opposite (`true` and `false` respectively), so a bare update call visibly flips them. See the [Update Publish Configurations notes](#notes--behaviour-6). |
| **Reflects both channels at once** | A view can be simultaneously public and private-linked; `publicViewConfig.publicPermLevel > 0` and `privateLinkConfig.isPrivate: true` can both hold in the same response. |
| **Custom-domain handling of `URLCriteria` is transparent** | Internally the criteria is stored under a different key for portal domains than for the Zoho Analytics domain, but this API normalises both to `URLCriteria` — callers see one field regardless of context. |
| **No email-verification requirement** | Unlike the mutating publish APIs, this read-only API does not require the caller's primary email to be verified. |
| **Dependency chain** | [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → `<view-id>` → Get Publish Configurations (then decide which publish API to call). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7103 | `META_OBJECT_NOT_PRESENT` — Workspace not found. | Verify `<workspace-id>` and the `ZANALYTICS-ORGID` header. |
| 7104 | `META_OBJECT_NOT_PRESENT` — View not found. | Verify `<view-id>` exists. |
| 7301 | `SECURITY_NOT_PERMITTED` — The user has neither Publish nor Make Public permission on the view. | Ensure the user is an Account Admin, Organization Admin, Workspace Admin, or has Publish / Make Public permission on the view. |
| 7319 | `OBJID_NOT_BELONGS_TO_DB` — The view does not belong to the specified workspace. | Ensure `<workspace-id>` and `<view-id>` are consistent. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.embed.read`. |

---

## 7. Update Publish Configurations

Updates the **presentation configuration** of the view's published page — title, description, toolbar, search box, dimensions, auto-refresh interval, legend position, URL-level criteria, Ask Zia — and, when the workspace is public, its public-listing flag.

| Attribute | Value |
|-----------|-------|
| **Method** | PUT |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/publish/config` |
| **OAuth Scope** | `ZohoAnalytics.embed.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user with Publish permission on the view, or any user with Make Public permission on the view. |

### CONFIG Parameters

> **This API replaces the whole configuration — it is not a patch.** Every field below is rewritten on every call, and any field you omit is reset to the Default listed here. Always read the current state with [Get Publish Configurations](#6-get-publish-configurations), merge your change into it, and send the complete object back.

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `URLCriteria` | String | No | `""` (cleared) | Row-level filter criteria applied when the published page is rendered, e.g. `"Sales_1"."Region"='West'`. Validated against the view's involved columns (`8054` / `8154`). Omitting it or sending `""` **clears** any previously configured criteria. Distinct from the share-level `criteria` of [Make View Public](#1-make-view-public) / [Create Private URL](#4-create-private-url). |
| `includeTitle` | Boolean | No | `true` | Render the view's title on the published page. |
| `includeDesc` | Boolean | No | `true` | Render the view's description on the published page. |
| `includeToolBar` | Boolean | No | `false` | Render the toolbar on the published page. |
| `includeSearchBox` | Boolean | No | `true` | Render a search box. Effective for table-type views and tabular reports only. |
| `includeDatatypeSymbol` | Boolean | No | `false` | Show each column's data-type symbol in the header. Table-type views and tabular reports only. |
| `includeShowHideOption` | Boolean | No | `false` | Let the visitor show/hide columns. Table-type views and tabular reports only. |
| `includeSocialWidgets` | Boolean | No | `false` | Render social share widgets. |
| `includeAskZia` | Boolean | No | `false` | Make the Ask Zia conversational-analytics widget available on the published page. |
| `isInteractive` | Boolean | No | `true` | Render a chart interactively (hover, tooltips, zoom). **Only honoured for chart views** — for every other view type the stored value is forced to `true` regardless of what is sent. |
| `legendPosition` | String | No | `"RIGHT"` | Legend placement for chart views, as an uppercase alphabetic keyword (the API validates only that the value is alphabetic; use the legend positions supported by the chart type, e.g. `RIGHT`). Ignored for non-chart views. |
| `width` | Long | No | `800` | Rendering width in pixels. |
| `height` | Long | No | `600` | Rendering height in pixels. |
| `autoRefresh` | Long | No | `-1` | Auto-refresh interval in **seconds**. `-1` disables auto-refresh. Any other value must be **at least 120** — smaller positive values are rejected with `8152`. |
| `isListed` | Boolean | No | — (unchanged) | Whether the workspace's public views appear in Zoho Analytics' public listing. Only applied when the workspace is currently public; otherwise ignored. On the Free plan (excluding CRM Plus Starter) it is **forced to `true`** and cannot be turned off. This is the only field that is left untouched when omitted. |
| `validateSystemTags` | Boolean | No | `true` | If `true`, the request is blocked with a confirmation-required error (`8241`) when the view carries a restricted **DATA_WARNING** system tag. Pass `false` to acknowledge the warning and update anyway. |

### Sample Requests

**Case 1 — `URLCriteria` only: filter the published page to a single region**

```http
PUT /restapi/v2/workspaces/137687000271334001/views/137687000006991601/publish/config HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "URLCriteria": "\"Sales_1\".\"Region\"='West'"
}
```

**Case 2 — Table-view presentation options clubbed together: chrome, search box, data-type symbols, show/hide, dimensions, auto-refresh**

```http
PUT /restapi/v2/workspaces/137687000271334001/views/137687000006991601/publish/config HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "includeTitle": true,
    "includeDesc": false,
    "includeToolBar": true,
    "includeSearchBox": true,
    "includeDatatypeSymbol": true,
    "includeShowHideOption": true,
    "includeSocialWidgets": false,
    "includeAskZia": true,
    "width": 1200,
    "height": 800,
    "autoRefresh": 300
}
```

**Case 3 — Chart-view options clubbed together: interactivity, legend placement, and public listing**

```http
PUT /restapi/v2/workspaces/137687000271334001/views/137687000006991650/publish/config HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "isInteractive": true,
    "legendPosition": "BOTTOM",
    "includeTitle": true,
    "includeDesc": true,
    "width": 1000,
    "height": 700,
    "isListed": false
}
```

**Case 4 — White Label / Client Portal: minimal chrome for embedding in a portal page**

```http
PUT /restapi/v2/workspaces/137687000271334009/views/137687000006991777/publish/config HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "URLCriteria": "\"WL_Table\".\"Region\"='West'",
    "includeTitle": false,
    "includeDesc": false,
    "includeToolBar": false,
    "includeSocialWidgets": false,
    "includeAskZia": false,
    "width": 900,
    "height": 500,
    "validateSystemTags": false
}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code, then read the applied state back with [Get Publish Configurations](#6-get-publish-configurations).

```
HTTP/1.1 204 No Content
```

**HTTP 400 Bad Request — Auto-refresh interval below the minimum**

```json
{
    "status": "failure",
    "summary": "INTERVAL_SHOULD_BE_120_OR_ABOVE",
    "data": {
        "errorCode": 8152,
        "errorMessage": "Refresh interval should be 120 seconds or above."
    }
}
```

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload (`status`, `summary`, `data.errorCode`, `data.errorMessage`). To read the resulting configuration, call [Get Publish Configurations](#6-get-publish-configurations).

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Update Publish Configurations returns a bare HTTP `204 No Content` — no `status`/`summary` JSON to parse. |
| **Full replace, not a patch** | The stored configuration is rebuilt from scratch on every call. Omitted fields fall back to the defaults in the CONFIG table above and **overwrite** whatever was stored before. Sending `{"includeTitle": true}` alone therefore also resets `width`, `height`, `autoRefresh`, `legendPosition`, `URLCriteria`, and every `include*` flag. `isListed` is the sole exception — it is only touched when present. |
| **Read-default vs. write-default asymmetry** | `includeSearchBox` defaults to `false` when read from a never-updated view but to `true` here; `includeAskZia` defaults to `true` when read but to `false` here. A bare update call visibly flips both. Always send them explicitly. |
| **`isInteractive` is forced for non-chart views** | For anything other than a chart view, the stored value is `true` no matter what is sent — tables, pivots, summaries, and dashboards are always interactive. |
| **`autoRefresh` has a hard floor** | Only `-1` (off) or values ≥ `120` seconds are accepted; anything in between fails with `8152`. |
| **`URLCriteria` is cleared by omission** | Because the configuration is rebuilt, omitting `URLCriteria` (or sending `""`) removes any criteria previously attached to the published URL. To keep it, resend it. |
| **`URLCriteria` ≠ share-level `criteria`** | `URLCriteria` is a URL parameter evaluated when the page renders and applies to *both* the public and private channels. The `criteria` field of [Make View Public](#1-make-view-public) / [Create Private URL](#4-create-private-url) is a per-channel share filter stored against the `Public Visitor` / `Private Link` pseudo-user. Both can be active at once and both then apply. |
| **`isListed` only bites on public workspaces** | The flag is applied only when the workspace itself is currently public; on a non-public workspace it is accepted and ignored. On the Free plan it is coerced to `true`. |
| **Applies to every publish channel** | The same configuration drives the public URL, the private URL, and the embed URL for this view — there is no per-channel presentation configuration. |
| **Dependency chain** | [Get Publish Configurations](#6-get-publish-configurations) (read current state) → merge → Update Publish Configurations → [Get Publish Configurations](#6-get-publish-configurations) (verify). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7103 | `META_OBJECT_NOT_PRESENT` — Workspace not found. | Verify `<workspace-id>` and the `ZANALYTICS-ORGID` header. |
| 7104 | `META_OBJECT_NOT_PRESENT` — View not found. | Verify `<view-id>` exists. |
| 7301 | `SECURITY_NOT_PERMITTED` — The user has neither Publish nor Make Public permission on the view. | Ensure the user is an Account Admin, Organization Admin, Workspace Admin, or has Publish / Make Public permission on the view. |
| 7319 | `OBJID_NOT_BELONGS_TO_DB` — The view does not belong to the specified workspace. | Ensure `<workspace-id>` and `<view-id>` are consistent. |
| 7565 | `UNVERIFIED_EMAIL` — The calling user's primary email address is not verified. | Verify the account's primary email address and retry. |
| 8054 | `INVALID_FILTER_CRITERIA` — `URLCriteria` could not be parsed. | Correct the criteria syntax (e.g. `"Table"."Column"='Value'`). |
| 8080 | `INVALID_JSON_CONFIGURATION` — CONFIG is not valid JSON, contains an unsupported key, or violates a type constraint (e.g. a non-alphabetic `legendPosition`). | Send only the documented keys with the documented types. |
| 8152 | `INTERVAL_SHOULD_BE_120_OR_ABOVE` — `autoRefresh` is a positive value below 120 seconds. | Use `-1` to disable auto-refresh, or a value of at least `120`. |
| 8154 | `COLUMN_NOT_PRESENT_IN_TABLE` — A column referenced in `URLCriteria` does not exist. | Verify column names via [Get Columns](COLUMNS_API_DOC_INFO.md). |
| 8241 | `SYSTEM_TAG_DATA_WARNING_V2_VALIDATION_CONFIRMATION` — The view carries a restricted DATA_WARNING system tag. | Review the warning, then resend with `"validateSystemTags": false` to confirm. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.embed.update`. |

---

## Appendix A – Common HTTP Headers

| Header | Value | Required | Description |
|--------|-------|----------|-------------|
| `Authorization` | `Zoho-oauthtoken <oauth-token>` | **Mandatory** | OAuth 2.0 access token of the calling user. Must carry the `ZohoAnalytics.embed.*` scope matching the operation (see [Appendix B](#appendix-b--oauth-scope-summary)). |
| `ZANALYTICS-ORGID` | Organization ID string | **Mandatory** | Organization ID of the workspace that owns the view. Obtainable from listing API responses as the `orgId` field. |
| `Content-Type` | `application/x-www-form-urlencoded` | Conditional | Required only for the three APIs that send a CONFIG body: [Make View Public](#1-make-view-public), [Create Private URL](#4-create-private-url), and [Update Publish Configurations](#7-update-publish-configurations). [Get Private URL](#3-get-private-url) takes its optional CONFIG as a query parameter instead. |

> **`ZANALYTICS-DEST-ORGID` is not used by any API in this document.** That header applies only to cross-organization copy operations (Copy Workspace, [Copy Views](VIEW_OPERATIONS_API_DOC_INFO.md#2-copy-views), Copy Formulas), which target a destination organization. Client Portal / White Label scoping in the publish APIs is expressed through the `domainName` CONFIG field (or the legacy `withCustomDomain` flag) — the two mechanisms are unrelated and must never be substituted for one another.

Example:

```http
POST /restapi/v2/workspaces/137687000271334001/views/137687000006991601/publish/public HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"criteria":"\"Sales_1\".\"Region\"='West'"}
```

---

## Appendix B – OAuth Scope Summary

| API | HTTP Method | Scope |
|-----|-------------|-------|
| Make View Public | POST | `ZohoAnalytics.embed.create` |
| Remove Public Permission | DELETE | `ZohoAnalytics.embed.delete` |
| Get Private URL | GET | `ZohoAnalytics.embed.read` |
| Create Private URL | POST | `ZohoAnalytics.embed.update` |
| Remove Private Access | DELETE | `ZohoAnalytics.embed.delete` |
| Get Publish Configurations | GET | `ZohoAnalytics.embed.read` |
| Update Publish Configurations | PUT | `ZohoAnalytics.embed.update` |

> Note the asymmetry: **Make View Public** uses the `create` scope while **Create Private URL** uses `update`. A token scoped only to `ZohoAnalytics.embed.create` can publish a public URL but cannot create a private link, and vice versa. Request both scopes for an integration that manages both channels.

---

## Appendix C – API-Specific Notes and Behaviours

### Make View Public

- **Create and update in one endpoint.** Despite the `create` operation type, re-calling this API on an already-public view overwrites the existing public share's permissions, criteria, and column restrictions instead of failing. There is no separate "update public link" API — plan integrations around a single idempotent upsert call.
- **Audience level must be pre-flighted.** `publicPermLevel` `2` and `3` are plan- and organization-gated. Read `publicViewConfig.isOrgPublicAllowed` / `isBussOrgPublicAllowed` from [Get Publish Configurations](#6-get-publish-configurations) before requesting them, rather than catching `7531`/`7500` after the fact. In a Client Portal / White Label context the level is silently forced to `1`.
- **Read-only by construction.** The permission array is sanitised to a read-only set server-side; row-write permissions and `share` are dropped silently rather than rejected, so a caller cannot tell from the response that they were ignored. Only the seven fields in [`permissions` Fields](#permissions-fields) have any effect.
- **`isListed` lives elsewhere.** The public-listing flag is *not* part of this API's CONFIG even though it is a public-channel concern — it is set through [Update Publish Configurations](#7-update-publish-configurations).
- **Dependency chain:** [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → [Get Publish Configurations](#6-get-publish-configurations) (check allowed audience levels) → Make View Public → verify via [Get Shared Details](SHARING_API_DOC_INFO.md#4-get-shared-details) (`sharedTo: "Public Visitor"`).

### Remove Public Permission

- **204 No Content, no body.** Verified against the implementation and the recorded request samples. Never parse a JSON success body for this API.
- **Fails on a view with no shares at all.** `8032` `VIEW_NOT_SHARED` is raised when the view has no share records whatsoever — this is a "nothing to remove" condition, not a permission problem. On a view that has other shares but is not public, the call completes silently.
- **Surgical.** Only the `Public Visitor` share record is removed. An active private link, user shares, group shares, and the publish configuration all survive.
- **Dependency chain:** [Get Publish Configurations](#6-get-publish-configurations) (confirm `publicViewConfig.publicPermLevel > 0`) → Remove Public Permission.

### Get Private URL

- **Strictly read-only.** This is the only private-link API that will not create or mutate anything — it fails with `8115` rather than lazily generating a key. Use it for retrieving an already-distributed URL, not for provisioning.
- **Returns a secret.** The response embeds the live private key. Treat `data.privateUrl` with the same care as a credential; it is the sole access token for the private channel.
- **Does not reveal the link's guards.** Password state, expiry date, and expiry status are not in this response — a URL returned here may still be password-gated or already expired. Pair with [Get Publish Configurations](#6-get-publish-configurations) when presenting link status to a user.
- **Two portal-domain mechanisms, different bars.** `domainName` needs portal-domain admin rights; the legacy `withCustomDomain` additionally needs Organization Admin / Super Admin. Prefer `domainName`.
- **Dependency chain:** [Create Private URL](#4-create-private-url) → Get Private URL.

### Create Private URL

- **The only publish API whose write semantics are conditional.** The key is created if absent (or rotated with `regenerateKey`), but `permissions` / `criteria` / `vudColumns` / `drillColumns` are only rewritten when `permissions` is present in the request. Sending `criteria` alone against an existing link is a silent no-op — always include `permissions` when updating.
- **`regenerateKey` is an irreversible revocation.** It invalidates every URL previously handed out for the view, with no grace period and no way to recover the old key. Treat it as a break-glass operation, not a routine refresh.
- **Password handling has two side effects worth knowing.** Setting or changing the password clears all live private-link sessions, and the password can later be read back **in clear text** through [Get Publish Configurations](#6-get-publish-configurations) — restrict who may call that API accordingly.
- **`drillThrough` is unavailable on this channel.** Public links accept it; private links force it to `false`. This is the one permission difference between the two channels.
- **Plan-limited resource.** New links consume the organization's private-link allotment (`6121`/`6122` when exhausted). Freeing one requires [Remove Private Access](#5-remove-private-access).
- **A sibling PUT endpoint exists but is out of scope here.** `PUT /publish/privatelink` updates an existing link only. This POST endpoint covers both create and update, so most integrations never need the PUT variant.
- **Dependency chain:** [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → Create Private URL → [Get Private URL](#3-get-private-url) / [Get Publish Configurations](#6-get-publish-configurations).

### Remove Private Access

- **204 No Content, no body.** Verified against the implementation and the recorded request samples.
- **Not idempotent.** A second call fails with `8115` `VIEW_NOT_PUBLISHED_AS_PRIVATE`. Guard repeats with a `privateLinkConfig.isPrivate` check rather than relying on a silent success.
- **Its permission check differs from the other private-link APIs.** The Publish permission is evaluated at the **workspace** level here, whereas [Get Private URL](#3-get-private-url) and [Create Private URL](#4-create-private-url) evaluate it **per view**. A user with view-scoped Publish permission but no workspace-level grant may therefore be able to create a link and not remove it (a custom-role user with view-level Publish/Make Public permission, or Share permission on the view, is also accepted).
- **Releases a plan allotment.** After removal, a previously blocked [Create Private URL](#4-create-private-url) may succeed.
- **Dependency chain:** [Get Publish Configurations](#6-get-publish-configurations) (confirm `privateLinkConfig.isPrivate`) → Remove Private Access.

### Get Publish Configurations

- **The pre-flight call for this entire family.** It is the only API that reports, in one round trip, whether the view is public and at what audience level, whether a private link exists and whether it is password-gated or expired, and which audience levels the plan permits. Call it first in almost every publish workflow.
- **Two of its three top-level blocks are permission-conditional.** `publicViewConfig` requires Make Public permission on the workspace; `privateLinkConfig` requires private links to be permitted **and** Publish permission on the workspace. A Free-plan response typically omits `privateLinkConfig` entirely. Never index into these keys without checking for their presence.
- **Returns the private-link password in clear text.** `privateLinkConfig.password` is decrypted for this response (sentinel `"-1"` when unset). This makes the endpoint materially more sensitive than the other read APIs in this document.
- **`publicPermLevel: 0` is output-only.** It signals "not public" on read but is not a legal input to [Make View Public](#1-make-view-public); un-publishing goes through [Remove Public Permission](#2-remove-public-permission).
- **Its `publishConfig` defaults are not the update API's defaults.** Before any [Update Publish Configurations](#7-update-publish-configurations) call, `includeSearchBox` reads as `false` and `includeAskZia` as `true`; the update API's own defaults for those fields are `true` and `false`. Do not treat a read as a safe round-trippable payload without setting both explicitly.
- **Dependency chain:** [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → Get Publish Configurations → the appropriate publish/un-publish API.

### Update Publish Configurations

- **204 No Content, no body.** Verified against the implementation and the recorded request samples.
- **Full replace — the single most important behaviour in this document.** The stored configuration is rebuilt from scratch on every call, so omitted fields are reset to their defaults, not preserved. The safe pattern is always read → merge → write. `isListed` is the only field that is left alone when omitted.
- **Two fields flip on a bare call.** Because of the read-default/write-default asymmetry, calling this API with a minimal body turns `includeSearchBox` on and `includeAskZia` off on a view that had never been updated before. Send both explicitly.
- **`URLCriteria` is a different concept from the channels' `criteria`.** `URLCriteria` is a URL-level filter that applies to the public URL, the private URL, and the embed URL alike; the `criteria` of [Make View Public](#1-make-view-public) / [Create Private URL](#4-create-private-url) is a per-channel share filter. When both exist, both apply — a common source of "the published page shows fewer rows than I expected".
- **Some fields are view-type-scoped.** `isInteractive` and `legendPosition` are honoured only for chart views (`isInteractive` is forced to `true` for everything else); `includeSearchBox`, `includeDatatypeSymbol`, and `includeShowHideOption` are honoured only for table-type views and tabular reports. Out-of-scope values are accepted and ignored rather than rejected.
- **`autoRefresh` is validated, not clamped.** A positive value below 120 seconds raises `8152` instead of being rounded up.
- **Dependency chain:** [Get Publish Configurations](#6-get-publish-configurations) → merge → Update Publish Configurations → [Get Publish Configurations](#6-get-publish-configurations) to verify.

---

## Appendix D – General Response Payload Notes

| Field / Behaviour | Detail |
|-------------------|--------|
| **Three of seven APIs return 204 with no body** | [Remove Public Permission](#2-remove-public-permission), [Remove Private Access](#5-remove-private-access), and [Update Publish Configurations](#7-update-publish-configurations) return HTTP **204 No Content** on success — treat the 2xx status code as the success indicator and never expect or parse a JSON body for these three. The other four return the standard `{"status", "summary", "data"}` envelope with HTTP 200. |
| **Failure responses always carry a body** | Even for the 204 APIs, errors return `{"status": "failure", "summary": "<ERROR_NAME>", "data": {"errorCode": <n>, "errorMessage": "<text>"}}`. `summary` on failure is the error's symbolic name (e.g. `SECURITY_NOT_PERMITTED`), not a localised sentence. |
| **The returned URL host is not the API host** | `data.publicUrl` and `data.privateUrl` point at the Zoho Analytics **application** domain (e.g. `analytics.zoho.com`) or, in a Client Portal / White Label context, at the workspace's portal domain — never at the `analyticsapi.*` host the request was sent to. Do not construct these URLs client-side from the API host. |
| **`publicUrl` and `privateUrl` differ only by the appended key** | Both are `https://<domain>/open-view/<view-id>`; the private form appends `/<32-char-hex-key>`. Nothing else in the URL encodes the permission set, criteria, or audience level — those are enforced server-side when the URL is opened. |
| **Conditional top-level keys, not empty placeholders** | [Get Publish Configurations](#6-get-publish-configurations) **omits** `publicViewConfig` / `privateLinkConfig` when the caller lacks the corresponding permission or the feature is unavailable — unlike the sharing APIs, which return empty containers. Always test for key presence before reading into them. |
| **`"-1"` is the "unset" sentinel, not `null`** | `privateLinkConfig.password` and `privateLinkConfig.expiryDate` use the string `"-1"` to mean "not configured". Similarly `publishConfig.autoRefresh` uses the number `-1` to mean "no auto-refresh". No field in these responses is ever `null`. |
| **Booleans are native, numbers are native, dates are strings** | Unlike the sharing APIs (where `inheritParentFilterCriteria` is serialised as the string `"true"`/`"false"`), every boolean in `publicViewConfig` / `privateLinkConfig` / `publishConfig` is a native JSON boolean, and `publicPermLevel`, `width`, `height`, and `autoRefresh` are native JSON numbers. `expiryDate` is a `dd/MM/yyyy` string in GMT. |
| **View IDs in the URL are numeric path segments** | Unlike the sharing APIs' response payloads, which return IDs as JSON strings, the publish APIs carry the view ID only inside the returned URL text — extract it as a string to avoid precision loss on large IDs. |
| **Effects are observable through the Sharing APIs** | Because both channels are modelled as shares to reserved pseudo-users, [Get Shared Details](SHARING_API_DOC_INFO.md#4-get-shared-details) is the canonical way to audit what a public or private link actually grants: look for `sharedTo: "Public Visitor"` / `sharedToZuId: "-20"` (with `publicPermLevel` set) and `sharedTo: "Private Link"` / `sharedToZuId: "-30"` (with `publicPermLevel: 0`), plus the resolved `permissionString`, `criteria`, `vudColumns`, and `drillColumns`. |
