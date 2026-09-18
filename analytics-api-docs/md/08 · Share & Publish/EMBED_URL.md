# Zoho Analytics V2 REST API — Embed URL

This document covers the V2 **Embed URL** REST APIs of Zoho Analytics — the APIs that mint short-lived, login-free URLs for embedding a single view inside an external application, list the embed URLs already issued for a view, and revoke them.

## What is an "Embed URL" in Zoho Analytics?

An **embed URL** is a signed, time-limited URL of the form `https://<analytics-domain>/open-view/<view-id>?RSCONFIG=<config-key>&FS=OS` that renders one view inside an `<iframe>` in a host application. It differs from every other publish channel in three important ways:

| | Embed URL | [Public URL](PUBLISH_API_DOC_INFO.md#1-make-view-public) | [Private URL](PUBLISH_API_DOC_INFO.md#4-create-private-url) |
|---|---|---|---|
| **Lifetime** | Expires after `validityPeriod` seconds (default 1 hour, maximum 1 day) | Never expires until revoked | Never expires unless an `expiryDate` is set |
| **Config storage** | Each call mints a **new** URL with its own permission set, filter criteria, and column restrictions | One shared configuration per view | One shared configuration per view |
| **How many per view** | Many, concurrently — one per call | One | One |
| **Availability** | **Embedded Analytics (OEM) customers only** | All plans (subject to plan gating) | Plan-gated |

Because each call produces an independent, self-contained URL, embed URLs are the mechanism for **multi-tenant embedding**: a host application can issue one URL per end customer, each pre-filtered with its own `criteria` and scoped to its own columns, without creating any Zoho Analytics users.

The `RSCONFIG` value in the URL is the opaque key under which that URL's configuration is stored. It is also the identifier used to revoke a single URL through [Delete Embed URL](#3-delete-embed-url), and the value returned as `rsConfig` by [Fetch All Embed URLs](#2-fetch-all-embed-urls).

> Notes that apply to every API in this document:
> - All requests are authenticated via OAuth (`Authorization: Zoho-oauthtoken <token>`). All three APIs use the **`embed`** scope family.
> - All three APIs are **view-scoped** (`/workspaces/<workspace-id>/views/<view-id>/publish/...`) and require the `ZANALYTICS-ORGID` header.
> - **All three APIs require the organization (or the specific workspace) to be enabled for Embedded Analytics (OEM).** On an ordinary organization every call fails with `8023` `OEM_OPERATION_NOT_ALLOWED` (HTTP 403) regardless of the caller's role.
> - **All three APIs are disabled in Client Portal / White Label request contexts.** A request that arrives through a custom domain is rejected with `7301` before any business logic runs — see [White Label / Client Portal Behaviour](#white-label--client-portal-behaviour).
> - The API host (`ZohoAnalytics_Server_URI`, e.g. `analyticsapi.zoho.com`, `analyticsapi.zoho.eu`) is **not** the host that appears in the returned `embedUrl`. The returned URL always points at the Zoho Analytics **application** domain (e.g. `analytics.zoho.com`) or, when `domainName` is supplied by a Client Portal admin, at that portal domain.
> - None of these APIs requires the caller's primary email to be verified.

---

## Index

| # | API Name | Method | URL |
|---|----------|--------|-----|
| 1 | [Get Embed URL](#1-get-embed-url) | GET | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/publish/embed` |
| 2 | [Fetch All Embed URLs](#2-fetch-all-embed-urls) | GET | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/publish/embedurls` |
| 3 | [Delete Embed URL](#3-delete-embed-url) | DELETE | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/publish/embed` |

>
> **Related APIs not in this document:** the per-view public/private publish channels and the publish presentation configuration are in [PUBLISH_API_DOC_INFO.md](PUBLISH_API_DOC_INFO.md); slideshow embedding is in [SLIDESHOW_API_DOC_INFO.md](SLIDESHOW_API_DOC_INFO.md); ordinary user/group sharing is in [SHARING_API_DOC_INFO.md](SHARING_API_DOC_INFO.md).

---

## White Label / Client Portal Behaviour

All three APIs are blocked in Client Portal / White Label request contexts. This is the **opposite** of the [Publish](PUBLISH_API_DOC_INFO.md) and [Slideshow](SLIDESHOW_API_DOC_INFO.md) families, and it has two distinct consequences that are easy to conflate:

| Scenario | Result |
|----------|--------|
| The API request itself arrives **through** a Client Portal / White Label custom domain | **Rejected with `7301`** before any business logic runs. The embed APIs cannot be invoked from a portal-domain context at all. |
| A Client Portal admin calls the API **from the standard API host** and passes `domainName` in CONFIG ([Get Embed URL](#1-get-embed-url) only) | **Allowed.** The generated `embedUrl` is built on that portal domain, so the iframe renders under the white-labelled host. |

So a white-labelled deployment embeds views by calling the standard `analyticsapi.zoho.*` host with `domainName`, never by calling the portal host. The `7301` responses shown in this document's White Label samples are the first scenario.

---

## 1. Get Embed URL

Mints a new, short-lived embed URL for a view. Everything the eventual viewer can see and do — which rows, which columns, whether they can export or drill — is fixed at the moment of this call and baked into the URL's stored configuration. The URL requires no sign-in.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/publish/embed` |
| **OAuth Scope** | `ZohoAnalytics.embed.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user with Publish permission or Make Public permission on the view. A caller who is **not** a workspace owner must additionally be listed in the organization's OEM-enabled users configuration, otherwise `7301`. In every case the organization or the workspace must be enabled for Embedded Analytics, otherwise `8023`. |

### CONFIG Parameters

CONFIG is **optional**. Because this is a `GET`, it must be passed as a **query parameter** whose value is the stringified, **URL-encoded** JSON object. Omitting CONFIG returns a read-only embed URL with a one-hour validity.

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `criteria` | String | No | — (no filter) | Row-level filter criteria applied to **this URL only**, e.g. `"Sales_1"."Region"='West'`. This is the primary multi-tenant mechanism: issue one embed URL per customer, each with a `criteria` that scopes it to that customer's rows. Validated against the view's involved columns (`8054` / `8154`) and stored **encrypted**. Max 250,000 characters. |
| `permissions` | JSONObject | No | `read: true`, everything else `false` | Read-only permission set carried by the URL. See [`permissions` Fields](#permissions-fields). |
| `vudColumns` | JSONArray | No | — | **Include model.** Applies only when `permissions.vud` is `true`. Restricts "View Underlying Data" to exactly the listed columns. 1–100 entries. See [`vudColumns` / `drillColumns` Fields](#vudcolumns--drillcolumns-fields). |
| `vudColumnsToExclude` | JSONArray | No | — | **Exclude model.** Applies only when `permissions.vud` is `true`. Hides exactly the listed columns from "View Underlying Data" and shows the rest. Same shape as `vudColumns`. When both are sent, the **exclude** model wins. |
| `drillColumns` | JSONArray | No | — | **Include model.** Applies only when `permissions.drillDown` is `true`. Restricts drill-down to exactly the listed columns. 1–100 entries. Same shape as `vudColumns`. |
| `drillColumnsToExclude` | JSONArray | No | — | **Exclude model.** Applies only when `permissions.drillDown` is `true`. Excludes exactly the listed columns from drill-down. When both are sent, the **exclude** model wins. |
| `validityPeriod` | Long | No | `3600` | How long the URL stays usable, in **seconds**, counted from the moment of this call. The default is one hour (`3600`) and the maximum is **86400 seconds (1 day)**. A larger value fails with `8177`. |
| `domainName` | String | No | — | Client Portal / White Label domain on which to build the returned URL. Only usable by a Client Portal admin of the workspace, calling from the standard API host — see [White Label / Client Portal Behaviour](#white-label--client-portal-behaviour). Max 200 characters. |
| `withCustomDomain` | Boolean | No | `false` | **Legacy flag.** Builds the URL on the workspace's configured portal domain without naming it. Requires the caller to be an Organization Admin or Super Admin **and** a Client Portal admin of the workspace. Prefer `domainName`. |
| `includeTitle` | Boolean | No | `true` | Whether the view's title is rendered inside the iframe. |
| `includeDesc` | Boolean | No | `true` | Whether the view's description is rendered inside the iframe. |
| `includeToolBar` | Boolean | No | `false` | Whether the toolbar is rendered inside the iframe. |
| `includeSearchBox` | Boolean | No | `false` | Whether a search box is rendered. Honoured **only for table-type views and tabular reports**; silently ignored for charts and dashboards. |
| `includeDatatypeSymbol` | Boolean | No | `false` | Whether column headers show their data-type symbol. Table-type views and tabular reports only. |
| `includeShowHideOption` | Boolean | No | `false` | Whether the viewer can show/hide columns. Table-type views and tabular reports only. |
| `legendPosition` | String | No | — (view's own setting) | Legend placement, honoured **only for chart views**. Accepts a single word (letters, digits, underscore), e.g. `BOTTOMCENTER`. Silently ignored for non-chart views. |
| `language` | String | No | — (viewer's default) | Renders the embedded view in this language. Must be one of the supported language names — see [`language` Values](#language-values). An unsupported name fails with `9102`. |
| `validateSystemTags` | Boolean | No | `true` | If `true`, the request is blocked with a confirmation-required error (`8241`) when the view carries a restricted **DATA_WARNING** system tag. Pass `false` to acknowledge the warning and mint the URL anyway. |

#### `permissions` Fields

An embed URL carries only the five read-oriented permissions below. `read` is always granted; the row-write permissions, `share`, and `discussion` can never be attached to an embed URL.

| Field | Type | Default | Description |
|-------|------|---------|--------------|
| `read` | Boolean | `true` | View/read access. Always granted and always present in the stored configuration — it cannot be switched off. |
| `export` | Boolean | `false` | Allows the viewer to export the embedded view's data. |
| `vud` | Boolean | `false` | Allows "View Underlying Data" — drilling from an aggregated report into the raw rows behind it. Pair with `vudColumns` / `vudColumnsToExclude` to control which columns are exposed. |
| `drillDown` | Boolean | `false` | Allows drilling down into the view by column values. Pair with `drillColumns` / `drillColumnsToExclude`. |
| `insight` | Boolean | `false` | Allows the viewer to see Zia Insights generated for the view. |

#### `vudColumns` / `drillColumns` Fields

`vudColumns`, `vudColumnsToExclude`, `drillColumns`, and `drillColumnsToExclude` all take the same shape — a JSONArray of objects, one per underlying table referenced by the view:

| Field | Type | Mandatory | Description |
|-------|------|-----------|--------------|
| `tableName` | String | **Yes** | Name of the underlying table whose columns are being restricted. Must be a table actually involved in the view (`7138` otherwise). Max 50 characters. |
| `columnNames` | JSONArray of String | **Yes** | Column names from `tableName`. 1–300 entries. Each name must exist in that table (`8154` otherwise). |

#### `language` Values

`english`, `chinese`, `chinese_td`, `japanese`, `korean`, `french`, `italian`, `spanish`, `portuguese`, `portuguese_td`, `german`, `dutch`, `russian`, `polish`, `arabic`, `hebrew`, `turkish`, `hungarian`, `swedish`, `danish`, `ukranian`, `vietnamies`, `bulgarian`, `croatian`, `czech`, `hindi`, `thai`, `indonesian`, `malay`, `khmer`.

### Sample Requests

**Case 1 — `criteria` only: one tenant's rows (the canonical multi-tenant call)**

CONFIG (before encoding):

```json
{
    "criteria": "\"Sales_1\".\"Region\"='West'"
}
```

```http
GET /restapi/v2/workspaces/137687000271334001/views/137687000006991601/publish/embed?CONFIG=%7B%22criteria%22%3A%22%5C%22Sales_1%5C%22.%5C%22Region%5C%22%3D'West'%22%7D HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Permissions and column restrictions clubbed together (include model)**

CONFIG (before encoding):

```json
{
    "permissions": {
        "read": true,
        "export": true,
        "vud": true,
        "drillDown": true,
        "insight": true
    },
    "vudColumns": [
        { "tableName": "Sales_1", "columnNames": ["Product", "Region"] }
    ],
    "drillColumns": [
        { "tableName": "Sales_1", "columnNames": ["Product", "Date"] }
    ],
    "includeToolBar": true
}
```

```http
GET /restapi/v2/workspaces/137687000271334001/views/137687000006991650/publish/embed?CONFIG=%7B%22permissions%22%3A%7B%22read%22%3Atrue%2C%22export%22%3Atrue%2C%22vud%22%3Atrue%2C%22drillDown%22%3Atrue%2C%22insight%22%3Atrue%7D%2C%22vudColumns%22%3A%5B%7B%22tableName%22%3A%22Sales_1%22%2C%22columnNames%22%3A%5B%22Product%22%2C%22Region%22%5D%7D%5D%2C%22drillColumns%22%3A%5B%7B%22tableName%22%3A%22Sales_1%22%2C%22columnNames%22%3A%5B%22Product%22%2C%22Date%22%5D%7D%5D%2C%22includeToolBar%22%3Atrue%7D HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 3 — Exclude model, longer validity, localisation, and minimal chrome clubbed together**

CONFIG (before encoding):

```json
{
    "permissions": {
        "read": true,
        "vud": true
    },
    "vudColumnsToExclude": [
        { "tableName": "Sales_1", "columnNames": ["Cost", "Margin"] }
    ],
    "validityPeriod": 86400,
    "language": "french",
    "includeTitle": false,
    "includeDesc": false,
    "includeSearchBox": true,
    "includeDatatypeSymbol": true,
    "includeShowHideOption": true
}
```

```http
GET /restapi/v2/workspaces/137687000271334001/views/137687000006991601/publish/embed?CONFIG=%7B%22permissions%22%3A%7B%22read%22%3Atrue%2C%22vud%22%3Atrue%7D%2C%22vudColumnsToExclude%22%3A%5B%7B%22tableName%22%3A%22Sales_1%22%2C%22columnNames%22%3A%5B%22Cost%22%2C%22Margin%22%5D%7D%5D%2C%22validityPeriod%22%3A86400%2C%22language%22%3A%22french%22%2C%22includeTitle%22%3Afalse%2C%22includeDesc%22%3Afalse%2C%22includeSearchBox%22%3Atrue%2C%22includeDatatypeSymbol%22%3Atrue%2C%22includeShowHideOption%22%3Atrue%7D HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 4 — White Label / Client Portal: portal-domain embed URL, requested from the standard API host**

CONFIG (before encoding):

```json
{
    "domainName": "portal.customdomain.com",
    "criteria": "\"WL_Table\".\"Region\"='West'",
    "permissions": {
        "read": true,
        "export": true
    },
    "validityPeriod": 7200
}
```

```http
GET /restapi/v2/workspaces/137687000271334009/views/137687000006991777/publish/embed?CONFIG=%7B%22domainName%22%3A%22portal.customdomain.com%22%2C%22criteria%22%3A%22%5C%22WL_Table%5C%22.%5C%22Region%5C%22%3D'West'%22%2C%22permissions%22%3A%7B%22read%22%3Atrue%2C%22export%22%3Atrue%7D%2C%22validityPeriod%22%3A7200%7D HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
```

### Sample Responses

**HTTP 200 OK — Filtered embed URL (Case 1)**

```json
{
    "status": "success",
    "summary": "Get embed URL",
    "data": {
        "embedUrl": "https://analytics.zoho.com/open-view/137687000006991601?RSCONFIG=118b3222babc1aa5d7a19284827863e9428b334f8abc65ee92e648794bf501bcc77fe1ed97d0b48d9681a00aeb9545d6&FS=OS"
    }
}
```

**HTTP 200 OK — VUD and drill-down restricted to selected columns (Case 2)**

```json
{
    "status": "success",
    "summary": "Get embed URL",
    "data": {
        "embedUrl": "https://analytics.zoho.com/open-view/137687000006991650?RSCONFIG=118b3222babc1aa5d7a19284827863e90177da79a369e9644caccd7026a87832eac37794b628a26837ccd0b6cf0db806&FS=OS"
    }
}
```

**HTTP 200 OK — White Label / Client Portal, portal-domain host (Case 4)**

```json
{
    "status": "success",
    "summary": "Get embed URL",
    "data": {
        "embedUrl": "https://portal.customdomain.com/open-view/137687000006991777?RSCONFIG=118b3222babc1aa5d7a19284827863e9fb29464e6e58fe88322963307a65fbaaf3a483a26d6adbf3a6c7906d213dc946&FS=OS"
    }
}
```

**HTTP 403 Forbidden — Request sent through a Client Portal / White Label domain (API disabled there)**

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

**HTTP 403 Forbidden — Organization not enabled for Embedded Analytics**

```json
{
    "status": "failure",
    "summary": "OEM_OPERATION_NOT_ALLOWED",
    "data": {
        "errorCode": 8023,
        "errorMessage": "This operation is not allowed."
    }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `status` | String | `"success"` on a successful call, `"failure"` on error. |
| `summary` | String | Localised operation summary. `"Get embed URL"` for this API. |
| `data` | JSONObject | Response payload wrapper. |
| `data.embedUrl` | String | The newly minted embed URL, of the form `https://<domain>/open-view/<view-id>?RSCONFIG=<config-key>&FS=OS`. `<config-key>` is the opaque encrypted key under which this URL's configuration is stored — it is the same value returned as `rsConfig` by [Fetch All Embed URLs](#2-fetch-all-embed-urls) and accepted by [Delete Embed URL](#3-delete-embed-url). `FS` is always `OS`. **Treat the whole value as a credential** — it grants sign-in-free access to the view, with the permissions and filter baked in, until it expires. |

> The response does **not** echo back the permissions, criteria, validity period, or column restrictions that were applied. Read them back through [Fetch All Embed URLs](#2-fetch-all-embed-urls).

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Every call mints a new URL** | This API is a factory, not an accessor. Ten calls produce ten independent, simultaneously valid URLs, each with its own configuration and its own expiry. Nothing about the view itself is modified. Use [Fetch All Embed URLs](#2-fetch-all-embed-urls) to see how many are outstanding. |
| **`criteria` is the multi-tenancy primitive** | Because the filter is bound to the URL rather than to the view or to a user, one view can serve many customers: issue one URL per customer with a `criteria` that scopes it to their rows. The criteria is stored encrypted and is not visible to the viewer. |
| **Short-lived by default** | With no `validityPeriod`, the URL dies after **3600 seconds**. Hosts that render long-lived dashboards must either raise `validityPeriod` (up to the maximum of 86400 seconds) or re-mint the URL server-side before it lapses. |
| **`validityPeriod` is validated, not clamped** | A value above the 86400-second maximum fails with `8177` `MAX_ALLOWED_VALUE_EXCEEDED` rather than being reduced to the limit. |
| **Exclude model beats include model** | If both `vudColumns` and `vudColumnsToExclude` are sent, the exclude list is used and the include list is ignored — no error is raised. The same applies to `drillColumns` versus `drillColumnsToExclude`. |
| **Column restrictions need the matching permission** | `vudColumns` / `vudColumnsToExclude` are ignored unless `permissions.vud` is `true`; `drillColumns` / `drillColumnsToExclude` are ignored unless `permissions.drillDown` is `true`. No error is raised for the ignored field. |
| **Only five permissions apply** | `read`, `export`, `vud`, `drillDown`, and `insight` are the whole permission surface of an embed URL. Anything else in the wider [sharing permission set](SHARING_API_DOC_INFO.md#permissions-fields) cannot be granted through this channel. |
| **The URL carries no options in its query string** | Everything requested in CONFIG — permissions, criteria, column restrictions, validity — is stored server-side against the `RSCONFIG` key; the URL itself is only `?RSCONFIG=<key>&FS=OS`. Treat `embedUrl` as opaque and do not attempt to alter behaviour by editing its query string. |
| **View-type-scoped options fail silently** | `includeSearchBox`, `includeDatatypeSymbol`, and `includeShowHideOption` apply only to table-type views and tabular reports; `legendPosition` applies only to charts. Sending them for the wrong view type is accepted and ignored. |
| **URL-encode the CONFIG** | The value contains `{`, `"`, and `=` characters that are illegal in a raw query string. Stringify and percent-encode it; sending it raw produces a client-side URI parse failure before the request ever reaches the server. |
| **Not callable from a portal domain** | See [White Label / Client Portal Behaviour](#white-label--client-portal-behaviour) — use `domainName` from the standard API host instead. |
| **Dependency chain** | [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → `<view-id>` → Get Embed URL → (audit) [Fetch All Embed URLs](#2-fetch-all-embed-urls) → (revoke) [Delete Embed URL](#3-delete-embed-url). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7103 | `META_OBJECT_NOT_PRESENT` — Workspace not found. | Verify `<workspace-id>` and that the `ZANALYTICS-ORGID` header matches it. |
| 7104 | `META_OBJECT_NOT_PRESENT` — View not found. | Verify `<view-id>` exists in the workspace. |
| 7138 | `META_OBJECT_NOT_PRESENT` — A `tableName` in a `vudColumns`/`drillColumns` array is not a table involved in this view. | Use only tables that the view actually reads from. |
| 7301 | `SECURITY_NOT_PERMITTED` — The request came through a Client Portal / White Label domain (where this API is disabled), or a non-owner caller is not in the organization's OEM-enabled users list, or the user lacks Publish / Make Public permission on the view. | Call from the standard API host; ensure the user is an Account Admin, Organization Admin, Workspace Admin, or has Publish / Make Public permission, and is OEM-enabled if not a workspace owner. |
| 7319 | `OBJID_NOT_BELONGS_TO_DB` — The view does not belong to the specified workspace. | Ensure `<workspace-id>` and `<view-id>` are consistent. |
| 8023 | `OEM_OPERATION_NOT_ALLOWED` — The organization/workspace is not enabled for Embedded Analytics. | Embedded Analytics must be enabled for the account; contact Zoho Analytics support/sales. |
| 8054 | `INVALID_FILTER_CRITERIA` — `criteria` could not be parsed. | Correct the criteria syntax (e.g. `"Table"."Column"='Value'`). |
| 8060 | `DOMAIN_NOT_EXIST` — The `domainName` supplied does not exist. | Use a domain returned by the [Domain and White Label APIs](DOMAIN_AND_WHITELABEL_API_DOC_INFO.md). |
| 8061 | `DOMAIN_DOES_NOT_BELONGS_TO_USER` — The caller is not an admin of the supplied `domainName`. | Call as an admin of that portal domain, or omit `domainName`. |
| 8080 | `INVALID_JSON_CONFIGURATION` — CONFIG is not valid JSON, was not URL-encoded correctly, contains an unsupported key, or violates a type/length constraint. | Stringify and URL-encode the CONFIG object, and send only the documented keys. |
| 8154 | `COLUMN_NOT_PRESENT_IN_TABLE` — A column in a `vudColumns`/`drillColumns` array (or in `criteria`) does not exist in the given table. | Verify column names via [Get Columns](COLUMNS_API_DOC_INFO.md). |
| 8177 | `MAX_ALLOWED_VALUE_EXCEEDED` — `validityPeriod` exceeds the maximum of 86400 seconds (1 day). | Send a value of 86400 seconds or less. |
| 8241 | `SYSTEM_TAG_DATA_WARNING_V2_VALIDATION_CONFIRMATION` — The view carries a restricted DATA_WARNING system tag. | Review the warning, then resend with `"validateSystemTags": false` to confirm. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.embed.read`. |
| 9102 | `LANGUAGE_NOT_SUPPORTED` — `language` is not one of the supported language names. | Use a value from [`language` Values](#language-values). |
| 12052 | `WORKSPACE_NOT_ENABLED_FOR_DOMAIN_ACCESS` — The workspace is not enabled for access through the requested portal domain. | Enable the workspace for that Client Portal domain first. |

---

## 2. Fetch All Embed URLs

Lists the embed URLs that have been issued for a view, together with the permission set, filter criteria, and column restrictions stored against each one. This is the audit and inventory call for the embed channel.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/publish/embedurls` |
| **OAuth Scope** | `ZohoAnalytics.embed.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin of the organization. The caller must also hold Publish permission or Make Public permission on the view, and the organization or workspace must be enabled for Embedded Analytics, otherwise `8023`. |

### CONFIG Parameters

CONFIG is **optional**. Because this is a `GET`, it must be passed as a **query parameter** whose value is the stringified, **URL-encoded** JSON object.

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `includeExpiredUrls` | Boolean | No | `false` | If `false` (the default), only URLs whose `expiryTime` is still in the future are returned. If `true`, **every** URL ever issued for the view is returned, including expired ones — useful for auditing what was handed out historically. |

### Sample Requests

**Case 1 — Active URLs only (no CONFIG)**

```http
GET /restapi/v2/workspaces/137687000271334001/views/137687000006991601/publish/embedurls HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Include expired URLs (full audit trail)**

CONFIG (before encoding):

```json
{
    "includeExpiredUrls": true
}
```

```http
GET /restapi/v2/workspaces/137687000271334001/views/137687000006991601/publish/embedurls?CONFIG=%7B%22includeExpiredUrls%22%3Atrue%7D HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 3 — White Label / Client Portal: request sent through the portal domain (rejected)**

```http
GET /restapi/v2/workspaces/137687000271334009/views/137687000006991777/publish/embedurls HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
```

### Sample Responses

**HTTP 200 OK — Several URLs on a table view, one of them filtered (Case 1)**

```json
{
    "status": "success",
    "summary": "Fetch all embed URLs",
    "data": {
        "embedUrls": [
            {
                "rsConfig": "118b3222babc1aa5d7a19284827863e92486f8de9e2ade456527fd5cc61646fe4ab69d0e354c6f84101aa0bd686feb4f",
                "createdBy": "jane.doe@example.com",
                "expiryTime": "1753882235539",
                "permissions": {
                    "read": true,
                    "export": false,
                    "vud": false,
                    "drillDown": false,
                    "insight": false
                },
                "criteria": ""
            },
            {
                "rsConfig": "118b3222babc1aa5d7a19284827863e92486f8de9e2ade456527fd5cc61646fe38300351ec0bccb3c661c0629bab73ae",
                "createdBy": "org.admin@example.com",
                "expiryTime": "1753882235768",
                "permissions": {
                    "read": true,
                    "export": false,
                    "vud": false,
                    "drillDown": false,
                    "insight": false
                },
                "criteria": ""
            },
            {
                "rsConfig": "118b3222babc1aa5d7a19284827863e92486f8de9e2ade456527fd5cc61646fe209e57696f5f6a59c08ef093671adbe5",
                "createdBy": "jane.doe@example.com",
                "expiryTime": "1753882235943",
                "permissions": {
                    "read": true,
                    "export": false,
                    "vud": false,
                    "drillDown": false,
                    "insight": false
                },
                "criteria": "(\"Region\"='West')"
            }
        ]
    }
}
```

**HTTP 200 OK — A chart view with a VUD-restricted URL and an insights-enabled URL**

```json
{
    "status": "success",
    "summary": "Fetch all embed URLs",
    "data": {
        "embedUrls": [
            {
                "rsConfig": "118b3222babc1aa5d7a19284827863e90177da79a369e9644caccd7026a87832eac37794b628a26837ccd0b6cf0db806",
                "createdBy": "jane.doe@example.com",
                "expiryTime": "1749146566512",
                "permissions": {
                    "read": true,
                    "export": false,
                    "vud": true,
                    "drillDown": false,
                    "insight": false
                },
                "criteria": "",
                "vudConfig": {
                    "vudConfigModel": "include",
                    "vudTables": [
                        "137687000006991640",
                        "137687000006991641"
                    ],
                    "vudColumns": [
                        "137687000006991896",
                        "137687000006991897",
                        "137687000006991886",
                        "137687000006991887"
                    ]
                }
            },
            {
                "rsConfig": "118b3222babc1aa5d7a19284827863e90177da79a369e9644caccd7026a87832c980cfd5f64573dc3980b7d95df52faa",
                "createdBy": "jane.doe@example.com",
                "expiryTime": "1749146570295",
                "permissions": {
                    "read": true,
                    "export": false,
                    "vud": false,
                    "drillDown": false,
                    "insight": true
                },
                "criteria": ""
            }
        ]
    }
}
```

**HTTP 200 OK — A drill-down-restricted URL**

```json
{
    "status": "success",
    "summary": "Fetch all embed URLs",
    "data": {
        "embedUrls": [
            {
                "rsConfig": "118b3222babc1aa5d7a19284827863e9dacefb9770cf86e69cef07bcaa9dea10bc63bcbe6e32cdb49616ea6aaad9e15c",
                "createdBy": "jane.doe@example.com",
                "expiryTime": "1749146567231",
                "permissions": {
                    "read": true,
                    "export": false,
                    "vud": false,
                    "drillDown": true,
                    "insight": false
                },
                "criteria": "",
                "drillConfig": {
                    "drillConfigModel": "include",
                    "drillColumns": [
                        "137687000006991891",
                        "137687000006991894",
                        "137687000006991881",
                        "137687000006991884"
                    ]
                }
            }
        ]
    }
}
```

**HTTP 200 OK — No embed URLs outstanding for the view**

```json
{
    "status": "success",
    "summary": "Fetch all embed URLs",
    "data": {
        "embedUrls": []
    }
}
```

**HTTP 403 Forbidden — Request sent through a Client Portal / White Label domain (Case 3)**

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
| `summary` | String | Localised operation summary. `"Fetch all embed URLs"` for this API. |
| `data` | JSONObject | Response payload wrapper. |
| `data.embedUrls` | JSONArray | One entry per embed URL issued for the view. **Always present**; an empty array `[]` when none are outstanding (or none are unexpired, when `includeExpiredUrls` is `false`). |
| `embedUrls[].rsConfig` | String | The opaque configuration key that identifies this URL — the same value that appears as `RSCONFIG=` in the `embedUrl` returned by [Get Embed URL](#1-get-embed-url), and the value to pass to [Delete Embed URL](#3-delete-embed-url) to revoke this single URL. **Treat as a credential.** |
| `embedUrls[].createdBy` | String | Email address of the user who minted this URL, resolved from the stored creator ID. |
| `embedUrls[].expiryTime` | String | Epoch timestamp in **milliseconds**, serialised as a string, at which this URL stops working. Compare against the current time to tell active from expired entries — the API itself does not flag expiry, it only filters by it. |
| `embedUrls[].permissions` | JSONObject | The permission set baked into this URL. Contains exactly `read`, `export`, `vud`, `drillDown`, and `insight` (all booleans); `read` is always `true`. `drillThrough` / `accessAdminPresets` never appear, because the embed channel does not store them. |
| `embedUrls[].criteria` | String | The row-level filter bound to this URL, decrypted for this response. Empty string `""` when the URL was minted without a `criteria`. **Sensitive** — it can reveal tenant identifiers. |
| `embedUrls[].vudConfig` | JSONObject | Present **only** when the URL was minted with a VUD column restriction. Absent otherwise. |
| `vudConfig.vudConfigModel` | String | `"include"` — `vudColumns` lists the only columns visible in View Underlying Data; or `"exclude"` — `vudColumns` lists the columns hidden from it. Derived from whether `vudColumns` or `vudColumnsToExclude` was sent at mint time. |
| `vudConfig.vudTables` | JSONArray of String | IDs of the underlying tables involved in the VUD restriction. |
| `vudConfig.vudColumns` | JSONArray of String | Column **IDs** (not names) covered by the restriction, flattened across all tables in `vudTables`. Resolve to names via [Get Columns](COLUMNS_API_DOC_INFO.md). |
| `embedUrls[].drillConfig` | JSONObject | Present **only** when the URL was minted with a drill-down column restriction. Absent otherwise. |
| `drillConfig.drillConfigModel` | String | `"include"` — `drillColumns` lists the only drillable columns; or `"exclude"` — `drillColumns` lists the columns excluded from drill-down. |
| `drillConfig.drillColumns` | JSONArray of String | Column **IDs** (not names) covered by the drill restriction, flattened across tables. Note there is no `drillTables` counterpart to `vudConfig.vudTables`. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Per-view, not per-workspace** | The listing covers one `<view-id>` at a time. There is no workspace-wide embed-URL inventory API — iterate over [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) to audit a whole workspace. |
| **Default hides expired URLs** | Without `includeExpiredUrls: true`, entries whose `expiryTime` has passed are filtered out server-side. A view that shows `[]` may still have historical URLs — re-query with the flag to see them. |
| **Expiry is a raw millisecond string** | `expiryTime` is not a formatted date and there is no `isExpired` boolean. Parse it as a long and compare with the current time yourself. |
| **`criteria` is returned decrypted** | The filter is stored encrypted but decrypted for this response, so the payload can expose tenant identifiers or customer names. Restrict who may call this API and avoid logging the response. |
| **`vudConfig` / `drillConfig` are conditional** | They appear only when the corresponding restriction was applied at mint time. Test for key presence rather than assuming a fixed schema. |
| **Model flags are translated for you** | The stored numeric model is converted to the readable strings `"include"` / `"exclude"` in this response — you never see the internal integer. |
| **Columns come back as IDs, not names** | Unlike the request side of [Get Embed URL](#1-get-embed-url), which takes `tableName` / `columnNames`, this response returns numeric IDs as strings. Round-tripping requires resolving them via [Get Columns](COLUMNS_API_DOC_INFO.md). |
| **`permissions` is narrower than the sharing permission object** | Exactly five keys, always present. Do not expect the row-write, `share`, `discussion`, `drillThrough`, or preset permissions that appear in [Get Shared Details](SHARING_API_DOC_INFO.md#4-get-shared-details). |
| **The natural verification step after minting or revoking** | Calling this API immediately after [Get Embed URL](#1-get-embed-url) shows the new entry; calling it after [Delete Embed URL](#3-delete-embed-url) confirms the entry is gone (or that the array is now empty). |
| **Not callable from a portal domain** | See [White Label / Client Portal Behaviour](#white-label--client-portal-behaviour). |
| **Dependency chain** | [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → `<view-id>` → Fetch All Embed URLs → `rsConfig` → [Delete Embed URL](#3-delete-embed-url). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7103 | `META_OBJECT_NOT_PRESENT` — Workspace not found. | Verify `<workspace-id>` and the `ZANALYTICS-ORGID` header. |
| 7104 | `META_OBJECT_NOT_PRESENT` — View not found. | Verify `<view-id>` exists in the workspace. |
| 7301 | `SECURITY_NOT_PERMITTED` — The request came through a Client Portal / White Label domain (where this API is disabled), or the caller is not an Account Admin / Organization Admin, or lacks Publish / Make Public permission on the view. | Call from the standard API host as an Account Admin or Organization Admin. |
| 7319 | `OBJID_NOT_BELONGS_TO_DB` — The view does not belong to the specified workspace. | Ensure `<workspace-id>` and `<view-id>` are consistent. |
| 8023 | `OEM_OPERATION_NOT_ALLOWED` — The organization/workspace is not enabled for Embedded Analytics. | Embedded Analytics must be enabled for the account; contact Zoho Analytics support/sales. |
| 8080 | `INVALID_JSON_CONFIGURATION` — CONFIG is not valid JSON, was not URL-encoded correctly, or contains an unsupported key. | Send only `includeExpiredUrls`, stringified and URL-encoded. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.embed.read`. |

---

## 3. Delete Embed URL

Revokes embed URLs for a view — either one specific URL identified by its `rsConfig` key, or every URL issued for the view. Revocation is immediate; the URL stops rendering on the next request.

| Attribute | Value |
|-----------|-------|
| **Method** | DELETE |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/publish/embed` |
| **OAuth Scope** | `ZohoAnalytics.embed.delete` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin of the organization. The caller must also hold Publish permission or Make Public permission on the view, and the organization or workspace must be enabled for Embedded Analytics, otherwise `8023`. |

### CONFIG Parameters

CONFIG is **mandatory** for this API, and exactly one of the two fields below must be supplied.

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `rsConfig` | String | Conditional* | — | The configuration key of the single embed URL to revoke, as returned by [Fetch All Embed URLs](#2-fetch-all-embed-urls) (`embedUrls[].rsConfig`) or taken from the `RSCONFIG=` parameter of an `embedUrl`. Max 1,000 characters. If no URL matches this key for the view, the call fails with `8175`. |
| `deleteAllUrls` | Boolean | Conditional* | `false` | If `true`, revokes **every** embed URL issued for the view, expired ones included. If the view has no embed URLs at all, the call fails with `8176`. |

\* **Exactly one** of `rsConfig` or `deleteAllUrls: true` must be sent. Supplying both, or neither, fails with `8178` `INVALID_DELETE_EMBED_URL_CONFIGURATION`. Note that sending `rsConfig` together with `deleteAllUrls: false` is valid — the flag is only "set" when it is `true`.

### Sample Requests

**Case 1 — Revoke one specific embed URL by its key**

```http
DELETE /restapi/v2/workspaces/137687000271334001/views/137687000006991601/publish/embed HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "rsConfig": "118b3222babc1aa5d7a19284827863e92486f8de9e2ade456527fd5cc61646fe4ab69d0e354c6f84101aa0bd686feb4f"
}
```

**Case 2 — Revoke every embed URL for the view**

```http
DELETE /restapi/v2/workspaces/137687000271334001/views/137687000006991601/publish/embed HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "deleteAllUrls": true
}
```

**Case 3 — White Label / Client Portal: request sent through the portal domain (rejected)**

```http
DELETE /restapi/v2/workspaces/137687000271334009/views/137687000006991777/publish/embed HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "deleteAllUrls": true
}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code, then confirm with [Fetch All Embed URLs](#2-fetch-all-embed-urls).

```
HTTP/1.1 204 No Content
```

**HTTP 404 Not Found — `deleteAllUrls` on a view that has no embed URLs**

```json
{
    "status": "failure",
    "summary": "OEM_VIEW_HOLD_NO_KEYS",
    "data": {
        "errorCode": 8176,
        "errorMessage": "No embed URLs are associated with the specified view."
    }
}
```

**HTTP 404 Not Found — `rsConfig` does not match any URL on this view**

```json
{
    "status": "failure",
    "summary": "OEM_KEY_NOT_PRESENT",
    "data": {
        "errorCode": 8175,
        "errorMessage": "The specified embed URL key is not present."
    }
}
```

**HTTP 400 Bad Request — Both `rsConfig` and `deleteAllUrls: true` sent (or neither)**

```json
{
    "status": "failure",
    "summary": "INVALID_DELETE_EMBED_URL_CONFIGURATION",
    "data": {
        "errorCode": 8178,
        "errorMessage": "Invalid configuration for deleting the embed URL."
    }
}
```

**HTTP 403 Forbidden — Request sent through a Client Portal / White Label domain (Case 3)**

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

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload (`status`, `summary`, `data.errorCode`, `data.errorMessage`). To confirm what remains, call [Fetch All Embed URLs](#2-fetch-all-embed-urls).

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Delete Embed URL returns a bare HTTP `204 No Content` — no `status`/`summary` JSON, and no count of how many URLs were removed. |
| **Two mutually exclusive modes** | Targeted (`rsConfig`) and bulk (`deleteAllUrls: true`). Supplying both or neither is rejected with `8178`, so the caller must decide explicitly — there is no default mode. |
| **Not idempotent in either mode** | A repeat targeted delete fails with `8175` (`OEM_KEY_NOT_PRESENT`); a repeat bulk delete fails with `8176` (`OEM_VIEW_HOLD_NO_KEYS`). Both are "nothing to delete" conditions reported as errors, not silent successes. Guard retries with [Fetch All Embed URLs](#2-fetch-all-embed-urls). |
| **Bulk mode also clears expired URLs** | `deleteAllUrls: true` removes every stored configuration for the view regardless of `expiryTime`, so it also wipes the historical audit trail that `includeExpiredUrls: true` would otherwise show. |
| **Revocation is immediate and irreversible** | The stored configuration is deleted, so the URL can no longer be resolved. There is no restore path — a replacement must be minted with [Get Embed URL](#1-get-embed-url), which produces a different `RSCONFIG` key. |
| **Only the embed channel is affected** | Public URLs, private URLs, slideshows, and ordinary user/group shares on the same view are untouched. Use [Remove Public Permission](PUBLISH_API_DOC_INFO.md#2-remove-public-permission) / [Remove Private Access](PUBLISH_API_DOC_INFO.md#5-remove-private-access) for those. |
| **Deleting a URL does not delete the view** | Only the issued access URLs are removed; the view, its data, and its definition are unchanged. |
| **CONFIG travels in the body, not the query string** | Unlike the two GET APIs in this family, this DELETE takes CONFIG as a form-encoded body parameter, so no URL encoding of the JSON is needed. |
| **Not callable from a portal domain** | See [White Label / Client Portal Behaviour](#white-label--client-portal-behaviour). |
| **Dependency chain** | [Fetch All Embed URLs](#2-fetch-all-embed-urls) → `rsConfig` → Delete Embed URL → [Fetch All Embed URLs](#2-fetch-all-embed-urls) to verify. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7103 | `META_OBJECT_NOT_PRESENT` — Workspace not found. | Verify `<workspace-id>` and the `ZANALYTICS-ORGID` header. |
| 7104 | `META_OBJECT_NOT_PRESENT` — View not found. | Verify `<view-id>` exists in the workspace. |
| 7301 | `SECURITY_NOT_PERMITTED` — The request came through a Client Portal / White Label domain (where this API is disabled), or the caller is not an Account Admin / Organization Admin, or lacks Publish / Make Public permission on the view. | Call from the standard API host as an Account Admin or Organization Admin. |
| 7319 | `OBJID_NOT_BELONGS_TO_DB` — The view does not belong to the specified workspace. | Ensure `<workspace-id>` and `<view-id>` are consistent. |
| 8023 | `OEM_OPERATION_NOT_ALLOWED` — The organization/workspace is not enabled for Embedded Analytics. | Embedded Analytics must be enabled for the account; contact Zoho Analytics support/sales. |
| 8080 | `INVALID_JSON_CONFIGURATION` — CONFIG is missing, is not valid JSON, contains an unsupported key, or `rsConfig` exceeds 1,000 characters. | Send a valid CONFIG containing only `rsConfig` or `deleteAllUrls`. |
| 8175 | `OEM_KEY_NOT_PRESENT` — No embed URL on this view matches the supplied `rsConfig`. | Re-read the current keys via [Fetch All Embed URLs](#2-fetch-all-embed-urls). |
| 8176 | `OEM_VIEW_HOLD_NO_KEYS` — `deleteAllUrls` was requested but the view has no embed URLs. | Confirm the view has outstanding URLs via [Fetch All Embed URLs](#2-fetch-all-embed-urls) with `includeExpiredUrls: true`. |
| 8178 | `INVALID_DELETE_EMBED_URL_CONFIGURATION` — Both `rsConfig` and `deleteAllUrls: true` were sent, or neither was. | Send exactly one of the two. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.embed.delete`. |

---

## Appendix A – Common HTTP Headers

| Header | Value | Required | Description |
|--------|-------|----------|-------------|
| `Authorization` | `Zoho-oauthtoken <oauth-token>` | **Mandatory** | OAuth 2.0 access token of the calling user. Must carry the `ZohoAnalytics.embed.*` scope matching the operation (see [Appendix B](#appendix-b--oauth-scope-summary)). |
| `ZANALYTICS-ORGID` | Organization ID string | **Mandatory** | Organization ID of the workspace that owns the view. Obtainable from the [Get Organizations](ORG_INFO_API_DOC_INFO.md) response or from listing API responses as the `orgId` field. |
| `Content-Type` | `application/x-www-form-urlencoded` | Conditional | Required only for [Delete Embed URL](#3-delete-embed-url), the one API here that sends a CONFIG body. [Get Embed URL](#1-get-embed-url) and [Fetch All Embed URLs](#2-fetch-all-embed-urls) take their optional CONFIG as a URL-encoded query parameter instead. |
| `Host` | `analyticsapi.zoho.com` (or the DC equivalent) | **Mandatory** | Must be the **standard** Zoho Analytics API host. A request whose host is a Client Portal / White Label custom domain is rejected with `7301` for all three APIs — see [White Label / Client Portal Behaviour](#white-label--client-portal-behaviour). |

> **`ZANALYTICS-DEST-ORGID` is not used by any API in this document.** That header applies only to cross-organization copy operations (Copy Workspace, [Copy Views](VIEW_OPERATIONS_API_DOC_INFO.md#2-copy-views), Copy Formulas), which target a destination organization. Portal-domain targeting in the embed APIs is expressed through the `domainName` CONFIG field (or the legacy `withCustomDomain` flag) on [Get Embed URL](#1-get-embed-url) — the two mechanisms are unrelated and must never be substituted for one another.

Example:

```http
DELETE /restapi/v2/workspaces/137687000271334001/views/137687000006991601/publish/embed HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"deleteAllUrls":true}
```

---

## Appendix B – OAuth Scope Summary

| API | HTTP Method | Scope |
|-----|-------------|-------|
| Get Embed URL | GET | `ZohoAnalytics.embed.read` |
| Fetch All Embed URLs | GET | `ZohoAnalytics.embed.read` |
| Delete Embed URL | DELETE | `ZohoAnalytics.embed.delete` |

> Note that **Get Embed URL uses the `read` scope even though it creates a new, persisted embed-URL configuration** — its XML operation type is `read`, not `create`. A token scoped to `ZohoAnalytics.embed.read` alone can therefore mint unlimited embed URLs but cannot revoke any of them. Grant `ZohoAnalytics.embed.delete` alongside it for any integration that needs to clean up after itself.

---

## Appendix C – API-Specific Notes and Behaviours

### Get Embed URL

- **A factory, not an accessor — this is the single most important thing to understand.** Unlike every other publish API, each call creates a *new* persisted configuration and returns a *new* URL. Nothing is idempotent and nothing about the view changes. An integration that calls it on every page load will accumulate one stored configuration per page load; pair it with [Delete Embed URL](#3-delete-embed-url) or a short `validityPeriod` to keep that bounded.
- **`criteria` is what makes multi-tenant embedding work.** The filter is bound to the URL rather than to the view or to a user, so one view can serve many customers with one URL each. This is the reason `criteria` is the most-used attribute of the whole family, and why it is stored encrypted.
- **The default lifetime is one hour.** Without `validityPeriod` the URL dies after 3600 seconds, and the maximum it can be raised to is 86400 seconds (1 day). The value is *validated*, not clamped — anything larger raises `8177`.
- **`domainName` supersedes `withCustomDomain`.** Both target a Client Portal / White Label domain, but the legacy flag additionally requires the caller to be an Organization Admin or Super Admin, and it fails silently when that is not the case. Prefer `domainName` in new integrations.
- **Exclude beats include for column restrictions.** Sending both `vudColumns` and `vudColumnsToExclude` silently uses the exclude list. Same for the drill pair. Pick one model per restriction.
- **Treat `embedUrl` as opaque.** The URL is only `?RSCONFIG=<key>&FS=OS`; every option requested in CONFIG lives server-side against that key. Do not parse it beyond extracting `RSCONFIG` when you need the revocation key, and do not try to change behaviour by editing the query string.
- **Dependency chain:** [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → `<view-id>` → Get Embed URL → [Fetch All Embed URLs](#2-fetch-all-embed-urls) to audit → [Delete Embed URL](#3-delete-embed-url) to revoke.

### Fetch All Embed URLs

- **The only way to see what has been handed out.** Because [Get Embed URL](#1-get-embed-url) returns nothing but the URL itself, this is the sole API that reveals a URL's permissions, filter criteria, column restrictions, creator, and expiry after the fact. It is the audit backbone of the embed channel.
- **Its default view is incomplete on purpose.** Expired entries are filtered out unless `includeExpiredUrls: true` is sent, so a `[]` response does not mean nothing was ever issued. Always use the flag for a genuine audit.
- **It returns decrypted `criteria`.** That makes the response materially more sensitive than the other reads in this family — a tenant-scoped filter can name the tenant. Restrict access and avoid logging.
- **Expiry is raw milliseconds with no helper flag.** There is no `isExpired` boolean and no formatted date; compare `expiryTime` against the current time yourself.
- **Columns come back as IDs while the request side takes names.** The asymmetry with [Get Embed URL](#1-get-embed-url)'s `tableName`/`columnNames` shape means a read-modify-remint workflow must resolve IDs through [Get Columns](COLUMNS_API_DOC_INFO.md) first.
- **Higher role bar than Get Embed URL.** Minting is available to workspace owners and OEM-enabled users; listing and revoking are restricted to Account Admins and Organization Admins. An integration user that can create URLs may well be unable to enumerate them.
- **Dependency chain:** [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → `<view-id>` → Fetch All Embed URLs → `rsConfig` → [Delete Embed URL](#3-delete-embed-url).

### Delete Embed URL

- **204 No Content, no body.** Verified against the implementation and the recorded 0-byte response samples. Never parse a JSON success body, and note that the response does not report how many URLs were removed.
- **The only API in this family that requires CONFIG.** Both of the GET APIs work with no CONFIG at all; here CONFIG is mandatory and must express exactly one of the two modes. Omitting it entirely, or sending both modes, is rejected with `8178` rather than defaulting to something.
- **Neither mode is idempotent.** Targeted repeats fail with `8175`, bulk repeats with `8176`. Both mean "nothing matched", which is arguably a success from the caller's point of view but is reported as a 404-class error — wrap retries accordingly.
- **Bulk delete destroys the audit trail.** `deleteAllUrls: true` removes expired configurations too, so anything [Fetch All Embed URLs](#2-fetch-all-embed-urls) would have shown with `includeExpiredUrls: true` is gone as well. Export the listing first if the history matters.
- **Revocation cannot be undone.** A replacement URL must be minted, and it will carry a different `RSCONFIG` key — so any host application holding the old URL must be updated, not just refreshed.
- **Scope-isolated from the other publish channels.** Public URLs, private URLs, slideshows, and user/group shares on the same view are untouched; each has its own removal API.
- **Dependency chain:** [Fetch All Embed URLs](#2-fetch-all-embed-urls) → `rsConfig` → Delete Embed URL → [Fetch All Embed URLs](#2-fetch-all-embed-urls) to verify.

---

## Appendix D – General Response Payload Notes

| Field / Behaviour | Detail |
|-------------------|--------|
| **One of three APIs returns 204 with no body** | [Delete Embed URL](#3-delete-embed-url) returns HTTP **204 No Content** on success — treat the 2xx status code as the success indicator and never expect or parse a JSON body. The two GET APIs return the standard `{"status", "summary", "data"}` envelope with HTTP 200. |
| **Failure responses always carry a body** | Even for the 204 API, errors return `{"status": "failure", "summary": "<ERROR_NAME>", "data": {"errorCode": <n>, "errorMessage": "<text>"}}`. `summary` on failure is the error's symbolic name (e.g. `OEM_OPERATION_NOT_ALLOWED`, `OEM_VIEW_HOLD_NO_KEYS`), not a localised sentence. |
| **403 is the normal outcome on a non-OEM organization** | Because all three APIs are gated on Embedded Analytics entitlement, `8023` (HTTP 403) — not `7301` — is what an ordinary organization sees, whatever the caller's role. Do not interpret it as a permission-configuration problem. |
| **Timestamps are millisecond epoch strings** | `embedUrls[].expiryTime` is a string containing epoch **milliseconds**. There are no formatted dates anywhere in these payloads, and no `isExpired` convenience flag. |
| **All IDs are strings** | `vudConfig.vudTables`, `vudConfig.vudColumns`, and `drillConfig.drillColumns` are arrays of **strings** even though the values are numeric IDs. Parse them as strings or longs — never as native JSON numbers — to avoid precision loss. |
| **Conditional keys, not empty placeholders** | `vudConfig` and `drillConfig` are **omitted entirely** when the URL carries no such restriction. This differs from the sharing APIs, which return empty containers. Always test for key presence. |
| **`criteria` is `""`, never `null` or absent** | An unfiltered embed URL reports `"criteria": ""`. `embedUrls` itself is likewise always present, empty (`[]`) when nothing matches the filter. |
| **`permissions` in the embed channel is a fixed five-key object** | Exactly `read`, `export`, `vud`, `drillDown`, `insight`, all booleans, `read` always `true`. It is a strict subset of the [sharing `permissions` object](SHARING_API_DOC_INFO.md#permissions-fields) and of the [publish `permissions` object](PUBLISH_API_DOC_INFO.md#permissions-fields) — code against the narrow shape, not the wide one. |
| **The returned URL host is not the API host** | `data.embedUrl` points at the Zoho Analytics **application** domain (e.g. `analytics.zoho.com`) or, when `domainName` was supplied, at that portal domain — never at the `analyticsapi.*` host the request was sent to. Do not construct these URLs client-side from the API host. |
| **`rsConfig` and `embedUrl` are credentials** | `rsConfig` appears in the listing response and inside every `embedUrl` as the `RSCONFIG=` parameter. Anyone holding the full URL can view the data, with the baked-in permissions and filter, until it expires. Avoid logging these values and restrict who may call [Fetch All Embed URLs](#2-fetch-all-embed-urls). |
| **Configuration is never echoed on mint** | [Get Embed URL](#1-get-embed-url) returns only `embedUrl` — not the permissions, criteria, validity, or column restrictions that were applied. Confirm what was stored with [Fetch All Embed URLs](#2-fetch-all-embed-urls) rather than assuming the request took effect verbatim. |
