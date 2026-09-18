# Zoho Analytics V2 REST API — Slideshow

This document covers the V2 **Slideshow** REST APIs of Zoho Analytics — the APIs that create, list, inspect, update, and delete slideshows within a workspace, and that build the URL through which a slideshow is presented.

## What is a "Slideshow" in Zoho Analytics?

A **slideshow** is a named, ordered collection of views (charts, pivots, summaries, dashboards, tables, query tables) belonging to a single workspace, presented one after another on a stand-alone page at `https://<analytics-domain>/ZDBSlideshow.cc?SLIDEID=<slide-id>&SLIDEKEY=<slide-key>&...`.

Two identifiers matter:

| Identifier | Purpose |
|------------|---------|
| **`slideId`** | The permanent numeric ID of the slideshow. Used in every URL path of these APIs. Safe to store and share internally. |
| **`slideKey`** | A 32-character hexadecimal secret embedded in the presentation URL. It is what allows the slideshow page to be opened. Rotating it (`regenerateSlideKey`) instantly invalidates every URL previously handed out. |

Each slideshow also carries an **access type** that decides whether a viewer must be signed in to Zoho Analytics — see [`accessType` Values](#accesstype-values). A slideshow set to "access without login" behaves like a private link and is therefore subject to the same plan and security-control gating as private links.

> Notes that apply to every API in this document:
> - All requests are authenticated via OAuth (`Authorization: Zoho-oauthtoken <token>`). All six APIs use the **`embed`** scope family.
> - All six APIs are **workspace-scoped** (`/workspaces/<workspace-id>/slides...`) and require the `ZANALYTICS-ORGID` header.
> - The API host (`ZohoAnalytics_Server_URI`, e.g. `analyticsapi.zoho.com`, `analyticsapi.zoho.eu`) is **not** the host that appears in the returned `slideUrl`. The returned URL always points at the Zoho Analytics **application** domain (e.g. `analytics.zoho.com`) or, for Client Portal / White Label workspaces, at the workspace's portal domain.
> - All six APIs are available in **Client Portal / White Label** contexts.
> - The three mutating APIs (Create Slide Show, Update Slide Show, Delete Slide Show) additionally require the calling user's **primary email to be verified** — otherwise error `7565`.
> - Slideshows are a **plan-gated feature**. Every API in this family — including the read-only ones — runs the plan check first and fails with `6063` on plans where slideshows are unavailable.
> - **No API in this family accepts a `criteria` attribute.** Row-level filtering is not part of the slideshow contract; a slideshow presents each view exactly as that view is defined. Filter the underlying views (or use [Update Publish Configurations](PUBLISH_API_DOC_INFO.md#7-update-publish-configurations) for a published view) instead.

---

## Index

| # | API Name | Method | URL |
|---|----------|--------|-----|
| 1 | [Get Slide List](#1-get-slide-list) | GET | `/restapi/v2/workspaces/<workspace-id>/slides` |
| 2 | [Get Slide URL](#2-get-slide-url) | GET | `/restapi/v2/workspaces/<workspace-id>/slides/<slide-id>/publish` |
| 3 | [Get Slide Info](#3-get-slide-info) | GET | `/restapi/v2/workspaces/<workspace-id>/slides/<slide-id>` |
| 4 | [Create Slide Show](#4-create-slide-show) | POST | `/restapi/v2/workspaces/<workspace-id>/slides` |
| 5 | [Update Slide Show](#5-update-slide-show) | PUT | `/restapi/v2/workspaces/<workspace-id>/slides/<slide-id>` |
| 6 | [Delete Slide Show](#6-delete-slide-show) | DELETE | `/restapi/v2/workspaces/<workspace-id>/slides/<slide-id>` |

> **Note on naming:** The public API portal presents the same six operations under slightly different display names — Get Slideshows, Get Slideshow URL, Get Slideshow Details, Create Slideshow, Update Slideshow, and Delete Slideshow respectively. The underlying paths, scopes, and payloads are identical.
>
> **Related APIs not in this document:** the per-view publish channels (public URL, private URL, publish configuration) are documented in [PUBLISH_API_DOC_INFO.md](PUBLISH_API_DOC_INFO.md); view-level sharing is in [SHARING_API_DOC_INFO.md](SHARING_API_DOC_INFO.md).

---

## `accessType` Values

`accessType` appears both as a CONFIG input ([Create Slide Show](#4-create-slide-show), [Update Slide Show](#5-update-slide-show)) and as a response field ([Get Slide List](#1-get-slide-list), [Get Slide Info](#3-get-slide-info)). It has exactly two meaningful values:

| Value | Name | Meaning |
|-------|------|---------|
| `0` | Access with login | The default. A viewer opening the slideshow URL must be signed in to Zoho Analytics **and** must already have access to the views in the slideshow. Nothing new is exposed. |
| `1` | Access without login | The slideshow URL renders for anyone who holds it, with no sign-in. This is the private-link equivalent for slideshows, and it is therefore gated by the plan's private-link entitlement (`6054`/`6056`) and by the organization's private-link security control (`8088`). |

> **Only `1` selects "without login".** The server tests `accessType == 1` and treats every other integer — including values outside the documented set — as `0` (access with login). No error is raised for an out-of-range value; it silently means "with login". Send only `0` or `1`.

---

## 1. Get Slide List

Returns every slideshow that exists in the workspace, with its ID, name, and access type. This is the discovery call for `<slide-id>`, which every other API in this family needs.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/slides` |
| **OAuth Scope** | `ZohoAnalytics.embed.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user with Create Slideshow permission on the workspace. |

> This API has no CONFIG parameter. All inputs are provided via URL path parameters only.

### Sample Requests

**Case 1 — Standard workspace**

```http
GET /restapi/v2/workspaces/137687000271334001/slides HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — White Label / Client Portal workspace**

```http
GET /restapi/v2/workspaces/137687000271334009/slides HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
```

### Sample Responses

**HTTP 200 OK — Workspace with several slideshows of mixed access type (Case 1)**

```json
{
    "status": "success",
    "summary": "Get slideshows",
    "data": {
        "slideshows": [
            {
                "slideName": "Sales Overview",
                "slideId": "137687000003149001",
                "accessType": 1
            },
            {
                "slideName": "Quarterly Highlights",
                "slideId": "137687000003149002",
                "accessType": 1
            },
            {
                "slideName": "Regional Deep Dive",
                "slideId": "137687000003149003",
                "accessType": 0
            },
            {
                "slideName": "Ops Daily",
                "slideId": "137687000003149004",
                "accessType": 0
            }
        ]
    }
}
```

**HTTP 200 OK — White Label / Client Portal workspace (Case 2)**

```json
{
    "status": "success",
    "summary": "Get slideshows",
    "data": {
        "slideshows": [
            {
                "slideName": "Portal Summary",
                "slideId": "137687000003120001",
                "accessType": 1
            },
            {
                "slideName": "Portal Detail",
                "slideId": "137687000003120002",
                "accessType": 0
            }
        ]
    }
}
```

**HTTP 200 OK — Workspace with no slideshows yet**

```json
{
    "status": "success",
    "summary": "Get slideshows",
    "data": {
        "slideshows": []
    }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `status` | String | `"success"` on a successful call, `"failure"` on error. |
| `summary` | String | Localised operation summary. `"Get slideshows"` for this API. |
| `data` | JSONObject | Response payload wrapper. |
| `data.slideshows` | JSONArray | One entry per slideshow in the workspace, in the workspace's stored order. **Always present**; an empty array `[]` when the workspace has no slideshows. |
| `slideshows[].slideId` | String | Numeric ID of the slideshow, serialised as a **string**. Use this as `<slide-id>` in the other five APIs. |
| `slideshows[].slideName` | String | Display name of the slideshow. Unique within the workspace. |
| `slideshows[].accessType` | Number | Whether a viewer must sign in: `0` = access with login, `1` = access without login. See [`accessType` Values](#accesstype-values). |

> `slideKey` and `viewIds` are **not** returned by this API — fetch them per slideshow via [Get Slide Info](#3-get-slide-info).

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Workspace-wide, not filtered** | There is no paging, search, or filter parameter — the response always covers every slideshow in the workspace. Filter client-side on `slideName` or `accessType`. |
| **Empty array, not an error** | A workspace with no slideshows returns HTTP 200 with `"slideshows": []`. Absence of slideshows is never an error condition. |
| **Deliberately omits the secret** | `slideKey` is excluded from this listing so that a broad "list everything" call cannot leak presentation URLs. Retrieve it per slideshow through [Get Slide Info](#3-get-slide-info) or build the URL directly with [Get Slide URL](#2-get-slide-url). |
| **`accessType` is numeric here** | In the V2 API `accessType` is the integer `0`/`1`. The older (non-V2) client APIs return the strings `"withLogin"`/`"withoutLogin"` for the same concept — do not mix the two shapes. |
| **Plan gate applies even to reading** | The slideshow plan entitlement is checked before the list is built, so this read-only API can itself fail with `6063` on a plan where slideshows are unavailable. |
| **No email-verification requirement** | Unlike the three mutating APIs, this read-only API does not require the caller's primary email to be verified. |
| **Dependency chain** | [Get Workspace List](WORKSPACE_OPERATIONS_API_DOC_INFO.md) → `<workspace-id>` → Get Slide List → `<slide-id>` for [Get Slide Info](#3-get-slide-info) / [Get Slide URL](#2-get-slide-url) / [Update Slide Show](#5-update-slide-show) / [Delete Slide Show](#6-delete-slide-show). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 6063 | `SLIDESHOW_NOT_ALLOWED` — The workspace owner's plan does not include the slideshow feature. | Upgrade the plan to one that supports slideshows. |
| 7103 | `META_OBJECT_NOT_PRESENT` — Workspace not found. | Verify `<workspace-id>` and that the `ZANALYTICS-ORGID` header matches it. |
| 7301 | `SECURITY_NOT_PERMITTED` — The user is neither a workspace owner nor a custom-role user with Create Slideshow permission. | Ensure the user is an Account Admin, Organization Admin, Workspace Admin, or has Create Slideshow permission on the workspace. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.embed.read`. |

---

## 2. Get Slide URL

Builds and returns the presentation URL for an existing slideshow. The rendering options sent in CONFIG are not stored — they are baked into the query string of the URL that comes back, so different callers can obtain differently configured URLs for the same slideshow.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/slides/<slide-id>/publish` |
| **OAuth Scope** | `ZohoAnalytics.embed.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user with Create Slideshow permission on the workspace. |

### CONFIG Parameters

CONFIG is **optional** for this API. Because this is a `GET`, it must be passed as a **query parameter** whose value is the stringified, URL-encoded JSON object. Omitting CONFIG entirely returns the URL with all defaults applied.

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `autoplay` | Boolean | No | `true` | Whether the slideshow advances from one view to the next on its own. Emitted as `AUTOPLAY=<value>` in the returned URL. Set to `false` for a manually driven presentation. |
| `slideInterval` | Integer | No | `25` | Seconds each view is displayed before the slideshow advances. **Must be between 10 and 300 inclusive** — any other value is rejected with `8119`. Emitted as `INTERVAL=<value>`. Only meaningful when `autoplay` is `true`. |
| `includeTitle` | Boolean | No | `true` | Whether each view's name is shown on its slide. Emitted as `INCLUDETITLE=<value>`. |
| `includeDesc` | Boolean | No | `true` | Whether each view's description is shown on its slide. Emitted as `INCLUDEDESC=<value>`. |
| `includeSocialWidgets` | Boolean | No | `false` | Whether social share widgets are rendered on the slides. Emitted as `SOCIALWIDGETS=<value>`. |
| `withCustomDomain` | Boolean | No | `false` | If `true`, returns the URL on the workspace's configured Client Portal / White Label domain instead of the Zoho Analytics domain. Requires the caller to be an **Organization Admin or Super Admin**, and the workspace must have a portal domain configured — if either condition fails, the flag is silently ignored and the normal domain is used. Unnecessary when the request is already made in a portal context (see Notes). |
| `domainName` | String | No | — | Accepted by the request template (max 200 characters) but **not used** by the slideshow URL builder. It has no effect on the returned URL; use `withCustomDomain` instead. |

### Sample Requests

**Case 1 — No CONFIG: default presentation URL**

```http
GET /restapi/v2/workspaces/137687000271334001/slides/137687000003149001/publish HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Playback options clubbed together: autoplay with a longer interval, no social widgets**

CONFIG (before encoding):

```json
{
    "autoplay": true,
    "slideInterval": 100,
    "includeTitle": true,
    "includeDesc": true,
    "includeSocialWidgets": false
}
```

```http
GET /restapi/v2/workspaces/137687000271334001/slides/137687000003149001/publish?CONFIG=%7B%22autoplay%22%3Atrue%2C%22slideInterval%22%3A100%2C%22includeTitle%22%3Atrue%2C%22includeDesc%22%3Atrue%2C%22includeSocialWidgets%22%3Afalse%7D HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 3 — Chrome options clubbed together: manual advance, no title or description, social widgets on**

CONFIG (before encoding):

```json
{
    "autoplay": false,
    "includeTitle": false,
    "includeDesc": false,
    "includeSocialWidgets": true
}
```

```http
GET /restapi/v2/workspaces/137687000271334001/slides/137687000003149001/publish?CONFIG=%7B%22autoplay%22%3Afalse%2C%22includeTitle%22%3Afalse%2C%22includeDesc%22%3Afalse%2C%22includeSocialWidgets%22%3Atrue%7D HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 4 — White Label / Client Portal: return the URL on the portal domain**

CONFIG (before encoding):

```json
{
    "withCustomDomain": true,
    "autoplay": true,
    "slideInterval": 60
}
```

```http
GET /restapi/v2/workspaces/137687000271334009/slides/137687000003120002/publish?CONFIG=%7B%22withCustomDomain%22%3Atrue%2C%22autoplay%22%3Atrue%2C%22slideInterval%22%3A60%7D HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
```

### Sample Responses

**HTTP 200 OK — Defaults (Case 1)**

```json
{
    "status": "success",
    "summary": "Get slideshow URL",
    "data": {
        "slideUrl": "https://analytics.zoho.com/ZDBSlideshow.cc?SLIDEID=137687000003149001&SLIDEKEY=7ddc2de689a5b7f4efb81ca48245c9be&AUTOPLAY=true&INTERVAL=25&INCLUDETITLE=true&INCLUDEDESC=true&SOCIALWIDGETS=false"
    }
}
```

**HTTP 200 OK — Longer interval (Case 2)**

```json
{
    "status": "success",
    "summary": "Get slideshow URL",
    "data": {
        "slideUrl": "https://analytics.zoho.com/ZDBSlideshow.cc?SLIDEID=137687000003149001&SLIDEKEY=7ddc2de689a5b7f4efb81ca48245c9be&AUTOPLAY=true&INTERVAL=100&INCLUDETITLE=true&INCLUDEDESC=true&SOCIALWIDGETS=false"
    }
}
```

**HTTP 200 OK — Manual advance, no title/description, social widgets on (Case 3)**

```json
{
    "status": "success",
    "summary": "Get slideshow URL",
    "data": {
        "slideUrl": "https://analytics.zoho.com/ZDBSlideshow.cc?SLIDEID=137687000003149001&SLIDEKEY=7ddc2de689a5b7f4efb81ca48245c9be&AUTOPLAY=false&INTERVAL=25&INCLUDETITLE=false&INCLUDEDESC=false&SOCIALWIDGETS=true"
    }
}
```

**HTTP 200 OK — White Label / Client Portal (Case 4)**

```json
{
    "status": "success",
    "summary": "Get slideshow URL",
    "data": {
        "slideUrl": "https://portal.customdomain.com/ZDBSlideshow.cc?SLIDEID=137687000003120002&SLIDEKEY=2f9afc5a38d71d366000dbaac41d9007&AUTOPLAY=true&INTERVAL=60&INCLUDETITLE=true&INCLUDEDESC=true&SOCIALWIDGETS=false"
    }
}
```

**HTTP 403 Forbidden — User lacks the slideshow permission on the workspace**

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
| `summary` | String | Localised operation summary. `"Get slideshow URL"` for this API. |
| `data` | JSONObject | Response payload wrapper. |
| `data.slideUrl` | String | The full presentation URL, always of the form `https://<domain>/ZDBSlideshow.cc?SLIDEID=<slide-id>&SLIDEKEY=<slide-key>&AUTOPLAY=<bool>&INTERVAL=<seconds>&INCLUDETITLE=<bool>&INCLUDEDESC=<bool>&SOCIALWIDGETS=<bool>`. The seven query parameters are always present, in that order, whether or not they were supplied in CONFIG. **`SLIDEKEY` is a secret** — for an `accessType: 1` slideshow this URL is sufficient to view the content with no sign-in, so treat the whole value as a credential. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Nothing is persisted** | The rendering options are query-string decoration on the returned URL only. Calling this API does not change the slideshow, and two callers can hold two differently configured URLs for the same `slideId` simultaneously. Contrast with [Update Publish Configurations](PUBLISH_API_DOC_INFO.md#7-update-publish-configurations), which does store per-view presentation settings. |
| **The full query string is always emitted** | Even a bare call with no CONFIG returns all seven parameters with their defaults, so the URL shape is stable and parseable. |
| **`autoplay` defaults to `true`** | A call with no CONFIG produces `AUTOPLAY=true&INTERVAL=25`. Send `"autoplay": false` explicitly for a manually advanced presentation. |
| **`slideInterval` is validated, not clamped** | Values below 10 or above 300 raise `8119` `INVALID_VALUE_FOR_ATTRIBUTE` rather than being rounded into range. The error message names the offending value and the permitted `10-300` range. |
| **Portal domain is automatic in a portal context** | When the request itself arrives through a Client Portal / White Label domain, the returned URL is already built on that domain — `withCustomDomain` is unnecessary. The flag exists for the case where an Organization Admin calls from the standard Zoho Analytics context and wants the portal-domain form of the URL. |
| **`withCustomDomain` fails silently** | If the caller is not an Organization Admin or Super Admin, or the workspace has no portal domain configured, the flag is ignored and the standard domain is returned with HTTP 200. There is no error to distinguish "ignored" from "applied" — compare the host in `slideUrl` to confirm. |
| **`domainName` has no effect** | The key is accepted by the request template but is never read by the slideshow URL builder. Sending it does not error and does not change the host. |
| **Reflects the current `slideKey`** | The URL always embeds the slideshow's live key, so a URL fetched after a `regenerateSlideKey` update differs from one fetched before, and the earlier one no longer works. |
| **No email-verification requirement** | Unlike the three mutating APIs, this read-only API does not require the caller's primary email to be verified. |
| **Dependency chain** | [Get Slide List](#1-get-slide-list) → `<slide-id>` → Get Slide URL. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 6063 | `SLIDESHOW_NOT_ALLOWED` — The workspace owner's plan does not include the slideshow feature. | Upgrade the plan to one that supports slideshows. |
| 7103 | `META_OBJECT_NOT_PRESENT` — Workspace not found. | Verify `<workspace-id>` and the `ZANALYTICS-ORGID` header. |
| 7301 | `SECURITY_NOT_PERMITTED` — The user is neither a workspace owner nor a custom-role user with Create Slideshow permission. | Ensure the user is an Account Admin, Organization Admin, Workspace Admin, or has Create Slideshow permission on the workspace. |
| 7351 | `SLIDESHOW_NOT_BELONGS_TO_DB` — The slideshow does not exist, or belongs to a different workspace. | Verify `<slide-id>` against [Get Slide List](#1-get-slide-list) for this workspace. |
| 7396 | `SLIDE_NOT_PRESENT_IN_DB` — The slideshow record exists but no slide details could be read for it. | Re-check the slideshow via [Get Slide List](#1-get-slide-list); recreate it if it is in an inconsistent state. |
| 8080 | `INVALID_JSON_CONFIGURATION` — CONFIG is not valid JSON, was not URL-encoded correctly, or contains an unsupported key. | Stringify and URL-encode the CONFIG object, and send only the documented keys. |
| 8119 | `INVALID_VALUE_FOR_ATTRIBUTE` — `slideInterval` is outside the permitted `10-300` range. | Send a value between 10 and 300 seconds, or omit it to use the default of 25. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.embed.read`. |

---

## 3. Get Slide Info

Returns the full definition of a single slideshow: its name, its access type, its secret slide key, and the ordered list of view IDs it contains.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/slides/<slide-id>` |
| **OAuth Scope** | `ZohoAnalytics.embed.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user with Create Slideshow permission on the workspace. |

> This API has no CONFIG parameter. All inputs are provided via URL path parameters only.

### Sample Requests

**Case 1 — Standard workspace**

```http
GET /restapi/v2/workspaces/137687000271334001/slides/137687000003149001 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — White Label / Client Portal workspace**

```http
GET /restapi/v2/workspaces/137687000271334009/slides/137687000003120002 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
```

### Sample Responses

**HTTP 200 OK — Slideshow requiring a login (`accessType: 0`), three views (Case 1)**

```json
{
    "status": "success",
    "summary": "Get slideshow details",
    "data": {
        "slideInfo": {
            "slideId": "137687000003149001",
            "slideKey": "3a9aea323f01b0c17012e905a1b10013",
            "slideName": "Sales Overview",
            "accessType": 0,
            "viewIds": [
                "137687000006991601",
                "137687000006991650",
                "137687000006991700"
            ]
        }
    }
}
```

**HTTP 200 OK — Same slideshow after an update: key rotated, opened up without login, views replaced**

```json
{
    "status": "success",
    "summary": "Get slideshow details",
    "data": {
        "slideInfo": {
            "slideId": "137687000003149001",
            "slideKey": "7ddc2de689a5b7f4efb81ca48245c9be",
            "slideName": "Sales Overview",
            "accessType": 1,
            "viewIds": [
                "137687000006991710",
                "137687000006991711",
                "137687000006991712"
            ]
        }
    }
}
```

**HTTP 200 OK — White Label / Client Portal workspace (Case 2)**

```json
{
    "status": "success",
    "summary": "Get slideshow details",
    "data": {
        "slideInfo": {
            "slideId": "137687000003120002",
            "slideKey": "2f9afc5a38d71d366000dbaac41d9007",
            "slideName": "Portal Detail",
            "accessType": 0,
            "viewIds": [
                "137687000006991777",
                "137687000006991778",
                "137687000006991779"
            ]
        }
    }
}
```

**HTTP 400 Bad Request — Slideshow belongs to a different workspace**

```json
{
    "status": "failure",
    "summary": "SLIDESHOW_NOT_BELONGS_TO_DB",
    "data": {
        "errorCode": 7351,
        "errorMessage": "The given slideshow does not belong to this workspace."
    }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `status` | String | `"success"` on a successful call, `"failure"` on error. |
| `summary` | String | Localised operation summary. `"Get slideshow details"` for this API. |
| `data` | JSONObject | Response payload wrapper. |
| `data.slideInfo` | JSONObject | The slideshow's full definition. Always present on success. |
| `slideInfo.slideId` | String | Numeric ID of the slideshow, serialised as a **string**. Echoes the `<slide-id>` from the URL. |
| `slideInfo.slideKey` | String | The 32-character lowercase hexadecimal secret embedded in the presentation URL. **Treat as a credential** — combined with `slideId` it reconstructs the viewing URL, which needs no sign-in when `accessType` is `1`. Changes whenever [Update Slide Show](#5-update-slide-show) is called with `regenerateSlideKey: true`. |
| `slideInfo.slideName` | String | Display name of the slideshow. Unique within the workspace. |
| `slideInfo.accessType` | Number | Whether a viewer must sign in: `0` = access with login, `1` = access without login. See [`accessType` Values](#accesstype-values). |
| `slideInfo.viewIds` | JSONArray of String | IDs of the views in the slideshow, **in presentation order**. Each ID is a string. Resolve names/types via [Get View Details](VIEW_OPERATIONS_API_DOC_INFO.md#7-get-view-details). |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **The only API that returns `slideKey`** | [Get Slide List](#1-get-slide-list) deliberately omits it. If you need to construct a presentation URL yourself, this is where the key comes from — though [Get Slide URL](#2-get-slide-url) is the supported way to build the URL. |
| **`viewIds` order is the presentation order** | The array is not sorted by ID or name; it is the sequence in which the views are shown. Preserving order matters when round-tripping through [Update Slide Show](#5-update-slide-show), which replaces the whole list. |
| **View names are not resolved** | Only IDs are returned. Pair with [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) if you need to display names. |
| **Does not re-check per-view access** | The permission check is at workspace level (owner, or Create Slideshow permission). This API does not verify that the caller can read each view in `viewIds`, so a slideshow may list views the caller cannot open individually. |
| **Error precedence: `7351` before `7396`** | A wrong or non-existent `<slide-id>` is caught first by the workspace-membership check and reported as `7351`. `7396` surfaces only in the rarer case where the slideshow record exists but its slide details cannot be read. |
| **No email-verification requirement** | Unlike the three mutating APIs, this read-only API does not require the caller's primary email to be verified. |
| **Dependency chain** | [Get Slide List](#1-get-slide-list) → `<slide-id>` → Get Slide Info → (optional) [Get View Details](VIEW_OPERATIONS_API_DOC_INFO.md#7-get-view-details) for each `viewIds` entry. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 6063 | `SLIDESHOW_NOT_ALLOWED` — The workspace owner's plan does not include the slideshow feature. | Upgrade the plan to one that supports slideshows. |
| 7103 | `META_OBJECT_NOT_PRESENT` — Workspace not found. | Verify `<workspace-id>` and the `ZANALYTICS-ORGID` header. |
| 7301 | `SECURITY_NOT_PERMITTED` — The user is neither a workspace owner nor a custom-role user with Create Slideshow permission. | Ensure the user is an Account Admin, Organization Admin, Workspace Admin, or has Create Slideshow permission on the workspace. |
| 7351 | `SLIDESHOW_NOT_BELONGS_TO_DB` — The slideshow does not exist, or belongs to a different workspace. | Verify `<slide-id>` against [Get Slide List](#1-get-slide-list) for this workspace. |
| 7396 | `SLIDE_NOT_PRESENT_IN_DB` — The slideshow record exists but no slide details could be read for it. | Re-check the slideshow via [Get Slide List](#1-get-slide-list); recreate it if it is in an inconsistent state. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.embed.read`. |

---

## 4. Create Slide Show

Creates a new slideshow in the workspace from an ordered set of views, and returns its new ID together with a ready-to-use presentation URL built with default rendering options.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/slides` |
| **OAuth Scope** | `ZohoAnalytics.embed.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user with Create Slideshow permission on the workspace. |

### CONFIG Parameters

CONFIG is **mandatory** for this API.

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `slideName` | String | **Yes** | — | Name of the new slideshow. Must be **unique within the workspace** (`7196` otherwise). Permitted characters are letters, digits, whitespace, and non-Basic-Latin characters — punctuation and symbols are rejected by the template with `8080`. An absent key raises `8079`; an empty/blank value raises `8078`. |
| `viewIds` | JSONArray of String/Long | **Yes** | — | IDs of the views to include, **in the order they should be presented**. 1–100 entries. Every view must belong to `<workspace-id>` (`7319` otherwise). An absent key raises `8079`; an empty array raises `8078`. |
| `accessType` | Integer (`0` \| `1`) | No | `0` | Whether viewers must sign in. See [`accessType` Values](#accesstype-values). Choosing `1` (access without login) additionally triggers the private-link plan check (`6054`/`6056`) and the private-link security control (`8088`). |
| `validateSystemTags` | Boolean | No | `true` | If `true`, the request is blocked with a confirmation-required error (`8241`) when any view in `viewIds` carries a restricted **DATA_WARNING** system tag — directly, or inherited through lineage from a parent data source or table. Pass `false` to acknowledge the warning and create the slideshow anyway. Only relevant when System Tags are enabled for the organization. |

### Sample Requests

**Case 1 — Minimal: name and views only (defaults to access with login)**

```http
POST /restapi/v2/workspaces/137687000271334001/slides HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "slideName": "Sales Overview",
    "viewIds": ["137687000006991601", "137687000006991650"]
}
```

**Case 2 — Attributes clubbed together: a public slideshow of three views, skipping system-tag validation**

```http
POST /restapi/v2/workspaces/137687000271334001/slides HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "slideName": "Quarterly Highlights",
    "viewIds": [
        "137687000006991601",
        "137687000006991650",
        "137687000006991700"
    ],
    "accessType": 1,
    "validateSystemTags": false
}
```

**Case 3 — White Label / Client Portal: a portal-domain slideshow accessible without login**

```http
POST /restapi/v2/workspaces/137687000271334009/slides HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "slideName": "Portal Summary",
    "viewIds": [
        "137687000006991777",
        "137687000006991778"
    ],
    "accessType": 1
}
```

### Sample Responses

**HTTP 200 OK — Access with login (Case 1)**

```json
{
    "status": "success",
    "summary": "Create slideshow",
    "data": {
        "slideId": "137687000003149001",
        "slideUrl": "https://analytics.zoho.com/ZDBSlideshow.cc?SLIDEID=137687000003149001&SLIDEKEY=3a9aea323f01b0c17012e905a1b10013&AUTOPLAY=true&INTERVAL=25&INCLUDETITLE=true&INCLUDEDESC=true&SOCIALWIDGETS=false"
    }
}
```

**HTTP 200 OK — Access without login (Case 2)**

```json
{
    "status": "success",
    "summary": "Create slideshow",
    "data": {
        "slideId": "137687000003149002",
        "slideUrl": "https://analytics.zoho.com/ZDBSlideshow.cc?SLIDEID=137687000003149002&SLIDEKEY=ab69f2cdb88712190bc4bfae8bb4aef8&AUTOPLAY=true&INTERVAL=25&INCLUDETITLE=true&INCLUDEDESC=true&SOCIALWIDGETS=false"
    }
}
```

**HTTP 200 OK — White Label / Client Portal (Case 3)**

```json
{
    "status": "success",
    "summary": "Create slideshow",
    "data": {
        "slideId": "137687000003120001",
        "slideUrl": "https://portal.customdomain.com/ZDBSlideshow.cc?SLIDEID=137687000003120001&SLIDEKEY=456090ad1e6afdbccf3ee53a89a1d9dd&AUTOPLAY=true&INTERVAL=25&INCLUDETITLE=true&INCLUDEDESC=true&SOCIALWIDGETS=false"
    }
}
```

**HTTP 403 Forbidden — Slideshows disabled for this portal workspace / user lacks the permission**

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
| `summary` | String | Localised operation summary. `"Create slideshow"` for this API. |
| `data` | JSONObject | Response payload wrapper. |
| `data.slideId` | String | ID of the newly created slideshow, serialised as a **string**. Store this — it is the `<slide-id>` for [Get Slide Info](#3-get-slide-info), [Get Slide URL](#2-get-slide-url), [Update Slide Show](#5-update-slide-show), and [Delete Slide Show](#6-delete-slide-show). |
| `data.slideUrl` | String | Presentation URL for the new slideshow, built with **default** rendering options (`AUTOPLAY=true&INTERVAL=25&INCLUDETITLE=true&INCLUDEDESC=true&SOCIALWIDGETS=false`). To obtain a URL with different options, call [Get Slide URL](#2-get-slide-url) with a CONFIG. **`SLIDEKEY` is a secret** — treat the whole value as a credential. |

> `slideName`, `accessType`, and `viewIds` are **not** echoed back. Read them via [Get Slide Info](#3-get-slide-info) if you need to confirm what was stored.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **`viewIds` order is the presentation order** | The array is stored as given — the first ID is the first slide. This is the only place the order is set on creation; changing it later means resending the whole array through [Update Slide Show](#5-update-slide-show). |
| **Names must be unique per workspace** | A duplicate `slideName` fails with `7196` `SLIDENAME_ALREADY_EXISTS`; the call is not turned into an update. Check [Get Slide List](#1-get-slide-list) first, or catch `7196` and retry with a different name. |
| **`slideName` character set is restrictive** | Only letters, digits, whitespace, and non-Basic-Latin characters pass template validation. Common punctuation (`-`, `_`, `:`, `/`, `&`, `.`) is rejected with `8080`, not silently stripped. |
| **Views are checked for workspace membership, not for readability** | Every ID in `viewIds` must belong to `<workspace-id>` (`7319`), but the caller's read permission on each individual view is **not** re-verified on this path — the workspace-level Create Slideshow permission governs the whole operation. |
| **`accessType: 1` is the private-link equivalent** | It brings in the private-link plan entitlement (`6054`/`6056`) and the organization's private-link security control (`8088`). `accessType: 0` skips both checks. |
| **The returned URL uses defaults only** | There is no way to pass rendering options to this API — `slideURL` options belong to [Get Slide URL](#2-get-slide-url). The URL returned here is a convenience, not a configured artefact. |
| **Portal domain is automatic in a portal context** | When called through a Client Portal / White Label domain, the returned `slideUrl` is already on that domain; no CONFIG flag is involved. |
| **No `criteria` support** | Slideshows present each view as defined; there is no row-filter attribute on this API. |
| **Dependency chain** | [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → `viewIds` → Create Slide Show → `slideId` → [Get Slide URL](#2-get-slide-url) / [Get Slide Info](#3-get-slide-info). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 6054 | `PUBLISHCNT_VIOLATION` — `accessType: 1` requested but the plan does not allow login-free (private-link style) access. | Use `accessType: 0`, or upgrade the plan. |
| 6056 | `SHAREDUSR_PUBLISHCNT_VIOLATION` — A shared user requested `accessType: 1` on a plan that restricts it. | Ask the workspace owner to create the slideshow, use `accessType: 0`, or upgrade the plan. |
| 6063 | `SLIDESHOW_NOT_ALLOWED` — The workspace owner's plan does not include the slideshow feature. | Upgrade the plan to one that supports slideshows. |
| 7103 | `META_OBJECT_NOT_PRESENT` — Workspace not found. | Verify `<workspace-id>` and the `ZANALYTICS-ORGID` header. |
| 7104 | `META_OBJECT_NOT_PRESENT` — A view in `viewIds` does not exist. | Verify the IDs via [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list). |
| 7196 | `SLIDENAME_ALREADY_EXISTS` — Another slideshow in this workspace already uses `slideName`. | Choose a different name, or update the existing slideshow via [Update Slide Show](#5-update-slide-show). |
| 7301 | `SECURITY_NOT_PERMITTED` — The user is neither a workspace owner nor a custom-role user with Create Slideshow permission. | Ensure the user is an Account Admin, Organization Admin, Workspace Admin, or has Create Slideshow permission on the workspace. |
| 7319 | `OBJID_NOT_BELONGS_TO_DB` — A view in `viewIds` belongs to a different workspace. | Include only views from `<workspace-id>`. |
| 7565 | `UNVERIFIED_EMAIL` — The calling user's primary email address is not verified. | Verify the account's primary email address and retry. |
| 8078 | `EMPTY_JSON_ATTRIBUTE_FOUND` — `slideName` is blank, or `viewIds` is an empty array. | Supply a non-empty name and at least one view ID. |
| 8079 | `ATTRIBUTE_NOT_PRESENT_IN_JSON_CONFIGURATION` — `slideName` or `viewIds` is missing from CONFIG. | Both are mandatory; include them. |
| 8080 | `INVALID_JSON_CONFIGURATION` — CONFIG is not valid JSON, contains an unsupported key, or violates a constraint (e.g. punctuation in `slideName`, more than 100 entries in `viewIds`). | Send only the documented keys with the documented types and value constraints. |
| 8088 | `SECURITY_CONTROLS_FEATURE_DISABLED` — `accessType: 1` requested but login-free links are disabled for this organization/workspace by security controls. | Use `accessType: 0`, or ask the Organization Admin to re-enable private links in Security Controls. |
| 8241 | `SYSTEM_TAG_DATA_WARNING_V2_VALIDATION_CONFIRMATION` — A view in `viewIds` carries a restricted DATA_WARNING system tag. | Review the warning, then resend with `"validateSystemTags": false` to confirm. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.embed.create`. |

---

## 5. Update Slide Show

Updates an existing slideshow: renames it, replaces its set of views, changes its access type, and/or rotates its slide key. Unlike the publish configuration APIs, this one is a genuine **partial update** — only the attributes present in CONFIG are touched.

| Attribute | Value |
|-----------|-------|
| **Method** | PUT |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/slides/<slide-id>` |
| **OAuth Scope** | `ZohoAnalytics.embed.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user with Create Slideshow permission on the workspace. |

### CONFIG Parameters

CONFIG is **mandatory** for this API, but every field inside it is optional. Fields you omit keep their current values.

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `slideName` | String | No | — (unchanged) | New name for the slideshow. Must be unique within the workspace, ignoring the slideshow being updated (`7196` otherwise) — re-sending the slideshow's own current name is therefore accepted. Same character-set restriction as on create: letters, digits, whitespace, and non-Basic-Latin characters only. |
| `viewIds` | JSONArray of String/Long | No | — (unchanged) | **Replaces** the entire set of views, in the order given. 1–100 entries. Every view must belong to `<workspace-id>` (`7319` otherwise). This is not an append — to add one view, send the existing list from [Get Slide Info](#3-get-slide-info) plus the new ID. |
| `accessType` | Integer (`0` \| `1`) | No | — (unchanged) | New access type. See [`accessType` Values](#accesstype-values). Switching **to** `1` triggers the private-link plan check (`6054`/`6056`) and the private-link security control (`8088`); switching to `0` does not. |
| `regenerateSlideKey` | Boolean | No | `false` | If `true`, generates a new slide key, immediately invalidating every presentation URL issued earlier. Also gated by the private-link plan check and security control. Sending `false` explicitly is a no-op. |
| `validateSystemTags` | Boolean | No | `true` | If `true`, the request is blocked with a confirmation-required error (`8241`) when any view in `viewIds` carries a restricted **DATA_WARNING** system tag. Pass `false` to acknowledge and proceed. Only evaluated when `viewIds` is present. |

### Sample Requests

**Case 1 — Rename only (views and access type untouched)**

```http
PUT /restapi/v2/workspaces/137687000271334001/slides/137687000003149001 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "slideName": "Sales Overview 2026"
}
```

**Case 2 — Attributes clubbed together: replace the views, rename, and open it up without login**

```http
PUT /restapi/v2/workspaces/137687000271334001/slides/137687000003149001 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "slideName": "Sales Overview 2026",
    "viewIds": [
        "137687000006991710",
        "137687000006991711",
        "137687000006991712"
    ],
    "accessType": 1,
    "validateSystemTags": false
}
```

**Case 3 — Rotate the slide key to revoke previously shared URLs**

```http
PUT /restapi/v2/workspaces/137687000271334001/slides/137687000003149001 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "regenerateSlideKey": true
}
```

**Case 4 — White Label / Client Portal: add a view to a portal slideshow (full list resent)**

```http
PUT /restapi/v2/workspaces/137687000271334009/slides/137687000003120002 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "viewIds": [
        "137687000006991777",
        "137687000006991778",
        "137687000006991779"
    ]
}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code, then read the applied state back with [Get Slide Info](#3-get-slide-info).

```
HTTP/1.1 204 No Content
```

**HTTP 404 Not Found — Name collides with another slideshow in the workspace**

```json
{
    "status": "failure",
    "summary": "SLIDENAME_ALREADY_EXISTS",
    "data": {
        "errorCode": 7196,
        "errorMessage": "A slideshow with this name already exists."
    }
}
```

**HTTP 403 Forbidden — User lacks the slideshow permission on the workspace**

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

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload (`status`, `summary`, `data.errorCode`, `data.errorMessage`). To read the resulting state, call [Get Slide Info](#3-get-slide-info).

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Update Slide Show returns a bare HTTP `204 No Content` — no `status`/`summary` JSON to parse, and no updated `slideUrl`. Fetch the new URL from [Get Slide URL](#2-get-slide-url) after rotating the key. |
| **True partial update** | Only keys present in CONFIG are applied; omitted attributes keep their values. This is the opposite of [Update Publish Configurations](PUBLISH_API_DOC_INFO.md#7-update-publish-configurations), which rebuilds its whole configuration on every call. |
| **`viewIds` replaces, never appends** | Sending two IDs on a slideshow that had five leaves it with exactly those two, in that order. To add or reorder, read the current list from [Get Slide Info](#3-get-slide-info), modify it, and resend it in full. |
| **Applied in a fixed order** | The server processes `slideName`, then `accessType`, then `viewIds`, then `regenerateSlideKey`. Each step can fail independently — a request that renames and replaces views may therefore have renamed successfully before failing on a bad view ID. Verify with [Get Slide Info](#3-get-slide-info) after a partial failure. |
| **Re-sending the current name is safe** | The uniqueness check excludes the slideshow being updated, so an idempotent "write the whole object back" pattern does not trip `7196`. |
| **`regenerateSlideKey` is an irreversible revocation** | Every URL previously handed out stops working the moment the new key is stored. There is no grace period and no way to recover the old key. |
| **Two operations share the private-link gating** | Both `accessType: 1` and `regenerateSlideKey: true` run the private-link plan check (`6054`/`6056`) and security-control check (`8088`). A rename-only or `accessType: 0` update skips them. |
| **`validateSystemTags` only matters with `viewIds`** | System-tag validation runs against the views being added; a request without `viewIds` never triggers `8241`. |
| **No `criteria` support** | There is no row-filter attribute on this API. |
| **Dependency chain** | [Get Slide Info](#3-get-slide-info) (read current name/views/access type) → merge → Update Slide Show → [Get Slide Info](#3-get-slide-info) / [Get Slide URL](#2-get-slide-url) to verify. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 6054 | `PUBLISHCNT_VIOLATION` — `accessType: 1` or `regenerateSlideKey: true` requested but the plan does not allow login-free (private-link style) access. | Use `accessType: 0` and omit `regenerateSlideKey`, or upgrade the plan. |
| 6056 | `SHAREDUSR_PUBLISHCNT_VIOLATION` — A shared user requested a plan-restricted `accessType: 1` or key rotation. | Ask the workspace owner to perform the update, or upgrade the plan. |
| 6063 | `SLIDESHOW_NOT_ALLOWED` — The workspace owner's plan does not include the slideshow feature. | Upgrade the plan to one that supports slideshows. |
| 7103 | `META_OBJECT_NOT_PRESENT` — Workspace not found. | Verify `<workspace-id>` and the `ZANALYTICS-ORGID` header. |
| 7104 | `META_OBJECT_NOT_PRESENT` — A view in `viewIds` does not exist. | Verify the IDs via [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list). |
| 7196 | `SLIDENAME_ALREADY_EXISTS` — Another slideshow in this workspace already uses the requested `slideName`. | Choose a different name. |
| 7301 | `SECURITY_NOT_PERMITTED` — The user is neither a workspace owner nor a custom-role user with Create Slideshow permission. | Ensure the user is an Account Admin, Organization Admin, Workspace Admin, or has Create Slideshow permission on the workspace. |
| 7319 | `OBJID_NOT_BELONGS_TO_DB` — A view in `viewIds` belongs to a different workspace. | Include only views from `<workspace-id>`. |
| 7351 | `SLIDESHOW_NOT_BELONGS_TO_DB` — The slideshow does not exist, or belongs to a different workspace. | Verify `<slide-id>` against [Get Slide List](#1-get-slide-list) for this workspace. |
| 7565 | `UNVERIFIED_EMAIL` — The calling user's primary email address is not verified. | Verify the account's primary email address and retry. |
| 8080 | `INVALID_JSON_CONFIGURATION` — CONFIG is not valid JSON, contains an unsupported key, or violates a constraint (e.g. punctuation in `slideName`, more than 100 entries in `viewIds`). | Send only the documented keys with the documented types and value constraints. |
| 8088 | `SECURITY_CONTROLS_FEATURE_DISABLED` — `accessType: 1` or key rotation requested but login-free links are disabled for this organization/workspace by security controls. | Ask the Organization Admin to re-enable private links in Security Controls. |
| 8241 | `SYSTEM_TAG_DATA_WARNING_V2_VALIDATION_CONFIRMATION` — A view in `viewIds` carries a restricted DATA_WARNING system tag. | Review the warning, then resend with `"validateSystemTags": false` to confirm. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.embed.update`. |

---

## 6. Delete Slide Show

Deletes a slideshow from the workspace. The views that were part of it are untouched — only the slideshow definition, its slide key, and therefore its presentation URL are removed.

| Attribute | Value |
|-----------|-------|
| **Method** | DELETE |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/slides/<slide-id>` |
| **OAuth Scope** | `ZohoAnalytics.embed.delete` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user with Create Slideshow permission on the workspace. |

> This API has no CONFIG parameter. All inputs are provided via URL path parameters only.

### Sample Requests

**Case 1 — Standard workspace**

```http
DELETE /restapi/v2/workspaces/137687000271334001/slides/137687000003149001 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — White Label / Client Portal workspace**

```http
DELETE /restapi/v2/workspaces/137687000271334009/slides/137687000003120002 HTTP/1.1
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

**HTTP 400 Bad Request — Slideshow already deleted, or belongs to a different workspace**

```json
{
    "status": "failure",
    "summary": "SLIDESHOW_NOT_BELONGS_TO_DB",
    "data": {
        "errorCode": 7351,
        "errorMessage": "The given slideshow does not belong to this workspace."
    }
}
```

**HTTP 403 Forbidden — User lacks the slideshow permission on the workspace**

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
| **Success response has no body** | Delete Slide Show returns a bare HTTP `204 No Content` — no `status`/`summary` JSON to parse. |
| **Views are not affected** | Deleting a slideshow removes only the grouping and its key. The underlying reports, dashboards, and tables remain exactly as they were, with their own sharing and publish state intact. |
| **Not idempotent** | A second delete of the same `<slide-id>` fails with `7351` `SLIDESHOW_NOT_BELONGS_TO_DB`, because the slideshow can no longer be found in the workspace. Guard repeats with a [Get Slide List](#1-get-slide-list) check rather than relying on a silent success. |
| **Revokes the URL immediately** | Any presentation URL for this slideshow stops working as soon as the delete completes. There is no trash or restore path for slideshows — unlike views, which go through the [Trash APIs](TRASH_API_DOC_INFO.md). |
| **Single slideshow per call** | The V2 API deletes one `<slide-id>` at a time; there is no bulk-delete payload. Loop over [Get Slide List](#1-get-slide-list) to clear several. |
| **Plan gate still applies** | The slideshow plan entitlement is checked before the delete, so the call can fail with `6063` on a plan where slideshows are unavailable even though the operation is destructive rather than creative. |
| **Dependency chain** | [Get Slide List](#1-get-slide-list) (confirm the slideshow exists) → Delete Slide Show. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 6063 | `SLIDESHOW_NOT_ALLOWED` — The workspace owner's plan does not include the slideshow feature. | Upgrade the plan to one that supports slideshows. |
| 7103 | `META_OBJECT_NOT_PRESENT` — Workspace not found. | Verify `<workspace-id>` and the `ZANALYTICS-ORGID` header. |
| 7301 | `SECURITY_NOT_PERMITTED` — The user is neither a workspace owner nor a custom-role user with Create Slideshow permission. | Ensure the user is an Account Admin, Organization Admin, Workspace Admin, or has Create Slideshow permission on the workspace. |
| 7351 | `SLIDESHOW_NOT_BELONGS_TO_DB` — The slideshow does not exist, was already deleted, or belongs to a different workspace. | Verify `<slide-id>` against [Get Slide List](#1-get-slide-list) for this workspace. |
| 7565 | `UNVERIFIED_EMAIL` — The calling user's primary email address is not verified. | Verify the account's primary email address and retry. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.embed.delete`. |

---

## Appendix A – Common HTTP Headers

| Header | Value | Required | Description |
|--------|-------|----------|-------------|
| `Authorization` | `Zoho-oauthtoken <oauth-token>` | **Mandatory** | OAuth 2.0 access token of the calling user. Must carry the `ZohoAnalytics.embed.*` scope matching the operation (see [Appendix B](#appendix-b--oauth-scope-summary)). |
| `ZANALYTICS-ORGID` | Organization ID string | **Mandatory** | Organization ID of the workspace that owns the slideshow. Obtainable from the [Get Organizations](ORG_INFO_API_DOC_INFO.md) response or from listing API responses as the `orgId` field. |
| `Content-Type` | `application/x-www-form-urlencoded` | Conditional | Required only for the two APIs that send a CONFIG body: [Create Slide Show](#4-create-slide-show) and [Update Slide Show](#5-update-slide-show). [Get Slide URL](#2-get-slide-url) takes its optional CONFIG as a URL-encoded query parameter instead; the other three APIs send no payload at all. |

> **`ZANALYTICS-DEST-ORGID` is not used by any API in this document.** That header applies only to cross-organization copy operations (Copy Workspace, [Copy Views](VIEW_OPERATIONS_API_DOC_INFO.md#2-copy-views), Copy Formulas), which target a destination organization. Client Portal / White Label handling in the slideshow APIs is either automatic (when the request arrives through the portal domain) or expressed through the `withCustomDomain` flag on [Get Slide URL](#2-get-slide-url) — the two mechanisms are unrelated and must never be substituted for one another.

Example:

```http
POST /restapi/v2/workspaces/137687000271334001/slides HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"slideName":"Sales Overview","viewIds":["137687000006991601"]}
```

---

## Appendix B – OAuth Scope Summary

| API | HTTP Method | Scope |
|-----|-------------|-------|
| Get Slide List | GET | `ZohoAnalytics.embed.read` |
| Get Slide URL | GET | `ZohoAnalytics.embed.read` |
| Get Slide Info | GET | `ZohoAnalytics.embed.read` |
| Create Slide Show | POST | `ZohoAnalytics.embed.create` |
| Update Slide Show | PUT | `ZohoAnalytics.embed.update` |
| Delete Slide Show | DELETE | `ZohoAnalytics.embed.delete` |

> Unlike the [Publish APIs](PUBLISH_API_DOC_INFO.md#appendix-b--oauth-scope-summary), the slideshow family maps cleanly onto the four CRUD scopes — the three read APIs share `embed.read`, and create/update/delete each use their matching scope. An integration that manages slideshows end to end needs all four.

---

## Appendix C – API-Specific Notes and Behaviours

### Get Slide List

- **The entry point for the whole family.** Every other slideshow API needs a `<slide-id>`, and this is the only way to discover one. Treat it as the first call in any slideshow workflow.
- **Unfiltered and unpaged by design.** The response always contains every slideshow in the workspace. There is no query parameter for search, sort, or paging — do that client-side on `slideName` / `accessType`.
- **Withholds the secret deliberately.** `slideKey` is excluded so a broad listing cannot leak presentation URLs. That makes this the safe API to expose to a listing UI; [Get Slide Info](#3-get-slide-info) is the one that needs tighter access control.
- **`accessType` shape differs from the legacy client APIs.** V2 returns the integers `0`/`1`; the older non-V2 APIs return the strings `"withLogin"`/`"withoutLogin"` for the same field. Do not write code that accepts either without normalising.
- **A read that can fail on plan.** Because the slideshow entitlement check runs before the list is built, `6063` is a realistic failure mode even for this read-only call — handle it rather than assuming reads always succeed.
- **Dependency chain:** [Get Workspace List](WORKSPACE_OPERATIONS_API_DOC_INFO.md) → Get Slide List → `<slide-id>` for every other API here.

### Get Slide URL

- **The only stateless API in the family.** It reads the slideshow and returns a decorated URL; nothing is written. Two consumers can hold two differently configured URLs for the same slideshow at the same time, which makes it safe to call per-consumer rather than per-slideshow.
- **Rendering options live here, not on the slideshow.** There is no stored presentation configuration for a slideshow (contrast [Update Publish Configurations](PUBLISH_API_DOC_INFO.md#7-update-publish-configurations) for a published view). If a caller needs consistent options, it must send the same CONFIG every time.
- **`autoplay` defaults to `true`.** A bare call returns an auto-advancing URL at 25-second intervals. This is easy to get wrong when porting from documentation that lists the default as `false` — send the flag explicitly if it matters.
- **`slideInterval` is the one hard-validated field.** Outside `10-300` it raises `8119` rather than clamping, and the error message names both the value and the range.
- **`withCustomDomain` can be ignored without telling you.** Non-Organization-Admin callers, or workspaces with no portal domain, get a normal-domain URL and HTTP 200. Inspect the host in `slideUrl` to know which form you received.
- **`domainName` is accepted and dead.** The request template allows the key but the URL builder never reads it. Do not use it to target a portal domain; use `withCustomDomain`, or simply call through the portal host.
- **Dependency chain:** [Get Slide List](#1-get-slide-list) → `<slide-id>` → Get Slide URL.

### Get Slide Info

- **The only source of `slideKey` and `viewIds`.** It is therefore both the most useful read in the family and the most sensitive — for an `accessType: 1` slideshow, `slideId` + `slideKey` is all that is needed to view the content with no sign-in. Restrict who may call it accordingly.
- **The mandatory read-before-write step for updates.** Because [Update Slide Show](#5-update-slide-show) replaces `viewIds` wholesale, any add/remove/reorder operation has to start here to obtain the current, correctly ordered list.
- **`viewIds` order carries meaning.** It is presentation order, not sort order. Round-tripping it through an unordered collection will silently reshuffle the slideshow.
- **Workspace-level permission only.** The call does not verify that the caller can read each view listed in `viewIds`, so the response can name views the caller cannot open individually.
- **Error precedence matters when debugging.** `7351` (wrong workspace / no such slideshow) is raised before the slide-details lookup, so `7396` indicates a genuinely inconsistent record rather than a bad ID.
- **Dependency chain:** [Get Slide List](#1-get-slide-list) → Get Slide Info → [Get View Details](VIEW_OPERATIONS_API_DOC_INFO.md#7-get-view-details) per `viewIds` entry.

### Create Slide Show

- **Order of `viewIds` is the product.** A slideshow is fundamentally an ordered list; the array as sent is the sequence viewers see. There is no separate reorder API — reordering means resending the full list through [Update Slide Show](#5-update-slide-show).
- **Names are a uniqueness constraint, not a label.** A duplicate `slideName` is a hard failure (`7196`), never an implicit update. Combined with the restrictive character set (letters, digits, whitespace and non-Basic-Latin only — no `-`, `_`, `:`, `/`, `&`, `.`), name generation is the most common source of `8080`/`7196` on this API.
- **`accessType: 1` changes the risk profile of the call.** It turns the slideshow into a login-free link, which is why it pulls in the private-link plan entitlement (`6054`/`6056`) and the organization's private-link security control (`8088`). A create with `accessType: 0` bypasses both and will succeed on plans where `1` fails.
- **Workspace membership is checked; per-view readability is not.** All `viewIds` must live in `<workspace-id>` (`7319`), but the caller's read access to each view is not re-verified on this path.
- **The returned URL is a convenience with fixed options.** It always carries the defaults; there is no way to influence it from this API. Call [Get Slide URL](#2-get-slide-url) when the presentation options matter.
- **Dependency chain:** [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → `viewIds` → Create Slide Show → `slideId` → [Get Slide URL](#2-get-slide-url).

### Update Slide Show

- **204 No Content, no body.** Verified against the implementation and the recorded request samples. Never parse a JSON success body, and never expect the rotated `slideUrl` back — fetch it from [Get Slide URL](#2-get-slide-url).
- **Genuinely partial, unlike the publish-config API.** Omitted attributes retain their values, so a minimal CONFIG is safe here. This is the opposite of [Update Publish Configurations](PUBLISH_API_DOC_INFO.md#7-update-publish-configurations), which resets every omitted field — do not carry a read-merge-write habit from one API to the other assuming it is required.
- **`viewIds` is the one field that *is* a full replace.** It swaps the entire ordered list. "Add a view" therefore means [Get Slide Info](#3-get-slide-info) → append → resend everything.
- **Partial application is possible on failure.** The four operations are applied in sequence (name, access type, views, key rotation) and each can fail on its own. A request that renames and then hits `7319` on a view ID leaves the rename in place. Always re-read with [Get Slide Info](#3-get-slide-info) after an error on a multi-field update.
- **Two fields trigger private-link gating.** `accessType: 1` and `regenerateSlideKey: true` both run the plan check (`6054`/`6056`) and the security-control check (`8088`); a rename-only update runs neither.
- **`regenerateSlideKey` is an irreversible revocation.** Every URL distributed earlier dies immediately, with no grace period and no recovery of the old key. Treat it as break-glass, not routine hygiene.
- **Dependency chain:** [Get Slide Info](#3-get-slide-info) → merge → Update Slide Show → [Get Slide Info](#3-get-slide-info) / [Get Slide URL](#2-get-slide-url) to verify.

### Delete Slide Show

- **204 No Content, no body.** Verified against the implementation and the recorded request samples.
- **Destroys the grouping, not the content.** The views keep their own definitions, sharing, and publish state. Nothing in [SHARING_API_DOC_INFO.md](SHARING_API_DOC_INFO.md) or [PUBLISH_API_DOC_INFO.md](PUBLISH_API_DOC_INFO.md) is affected by deleting a slideshow.
- **No trash, no restore.** Unlike views, a deleted slideshow does not land in the [Trash](TRASH_API_DOC_INFO.md) — it is gone, and so is its slide key. Recreating it produces a new `slideId` and a new key, so previously shared URLs cannot be revived.
- **Not idempotent.** A repeat delete fails with `7351`. Check existence via [Get Slide List](#1-get-slide-list) if a caller may retry.
- **One at a time.** There is no bulk payload; clearing several slideshows means iterating over [Get Slide List](#1-get-slide-list).
- **Dependency chain:** [Get Slide List](#1-get-slide-list) → Delete Slide Show.

---

## Appendix D – General Response Payload Notes

| Field / Behaviour | Detail |
|-------------------|--------|
| **Two of six APIs return 204 with no body** | [Update Slide Show](#5-update-slide-show) and [Delete Slide Show](#6-delete-slide-show) return HTTP **204 No Content** on success — treat the 2xx status code as the success indicator and never expect or parse a JSON body for these two. The other four return the standard `{"status", "summary", "data"}` envelope with HTTP 200. |
| **Failure responses always carry a body** | Even for the 204 APIs, errors return `{"status": "failure", "summary": "<ERROR_NAME>", "data": {"errorCode": <n>, "errorMessage": "<text>"}}`. `summary` on failure is the error's symbolic name (e.g. `SECURITY_NOT_PERMITTED`, `SLIDESHOW_NOT_BELONGS_TO_DB`), not a localised sentence. |
| **All IDs are strings** | `slideId` and every entry of `viewIds` are JSON **strings** in every response, even though they are numeric. Parse them as strings or longs — never as native JSON numbers — to avoid precision loss on large IDs. |
| **`accessType` is a native number** | It is the only numeric field in these payloads: the integer `0` or `1`, not a string and not a boolean. Everything else in the responses is a string or an array of strings. |
| **Empty array, never a missing key** | `data.slideshows` is always present in a successful [Get Slide List](#1-get-slide-list) response, empty (`[]`) when the workspace has no slideshows. Likewise `slideInfo.viewIds` is always present in [Get Slide Info](#3-get-slide-info). No key in these responses is ever `null` or conditionally omitted. |
| **The returned URL host is not the API host** | `data.slideUrl` points at the Zoho Analytics **application** domain (e.g. `analytics.zoho.com`) or, in a Client Portal / White Label context, at the workspace's portal domain — never at the `analyticsapi.*` host the request was sent to. Do not construct these URLs client-side from the API host. |
| **`slideUrl` shape is stable and fully populated** | It is always `https://<domain>/ZDBSlideshow.cc?SLIDEID=<id>&SLIDEKEY=<key>&AUTOPLAY=<bool>&INTERVAL=<seconds>&INCLUDETITLE=<bool>&INCLUDEDESC=<bool>&SOCIALWIDGETS=<bool>` — all seven parameters, in that order, whether or not they were supplied. This makes the URL safe to parse, but it also means the key is always embedded. |
| **`slideKey` is a credential** | It appears in `slideInfo.slideKey` and inside every `slideUrl`. For an `accessType: 1` slideshow it grants sign-in-free access to the content, so avoid logging these values and restrict who may call [Get Slide Info](#3-get-slide-info) and [Get Slide URL](#2-get-slide-url). |
| **Create echoes only the identifiers** | [Create Slide Show](#4-create-slide-show) returns `slideId` and `slideUrl` only — not `slideName`, `accessType`, or `viewIds`. Confirm what was stored with [Get Slide Info](#3-get-slide-info) rather than assuming the request was applied verbatim. |
