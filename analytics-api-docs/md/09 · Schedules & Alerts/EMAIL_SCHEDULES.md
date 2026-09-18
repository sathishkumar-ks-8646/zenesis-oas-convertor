# Zoho Analytics V2 REST API — Email Schedules

This document covers the V2 **Email Schedule** REST APIs of Zoho Analytics — the APIs that create, list, update, enable/disable, trigger, and delete recurring email deliveries of views (tables, charts, pivots, summaries, dashboards, query tables) to a set of recipients.

## What is an "Email Schedule" in Zoho Analytics?

An **email schedule** is a named, recurring job that exports one or more views in a chosen file format and emails them to a list of recipients — individual email addresses, workspace groups, or both — at a frequency you define. It has four moving parts:

| Part | CONFIG attribute(s) | Notes |
|------|--------------------|-------|
| **What is sent** | `viewIds`, `exportType`, `selectedTabs` | Which views, in which file format. Fixed at creation — `viewIds` and `exportType` cannot be changed later. |
| **When it runs** | `scheduleDetails` | Frequency, time of day, and the day/week/month selectors that apply to that frequency. |
| **Who receives it** | `emailIds`, `groupIds`, `cc`, `isBCC` | Recipients may be raw email addresses or workspace groups; a carbon-copy list is separate. |
| **How it reads** | `scheduleName`, `subject`, `message`, `applyShareCriteria`, `applyDefaultUf` | Naming, email body, and whether each recipient sees data filtered to their own share criteria. |

> **The single most important behaviour:** updating a schedule can **replace its ID**. See [Schedule ID Lifecycle](#schedule-id-lifecycle) before writing any integration that stores schedule IDs.

> Notes that apply to every API in this document:
> - All requests are authenticated via OAuth (`Authorization: Zoho-oauthtoken <token>`). The read API uses the **`metadata`** scope family; the five write APIs use the **`modeling`** scope family — see [Appendix B](#appendix-b--oauth-scope-summary).
> - All six APIs are **workspace-scoped** (`/workspaces/<workspace-id>/emailschedules...`) and require the `ZANALYTICS-ORGID` header.
> - **All six APIs are disabled in Client Portal / White Label request contexts.** A request that arrives through a custom domain is rejected with `7301` before any business logic runs — see [White Label / Client Portal Behaviour](#white-label--client-portal-behaviour).
> - Email schedules consume a per-organization **schedule quota**. See [Quota Consumption](#quota-consumption).
> - None of these APIs accepts a `criteria` attribute. Row-level filtering for a schedule is driven by `applyShareCriteria` (each recipient receives data filtered by the share criteria already configured for them), not by a per-request filter expression.

---

## Index

| # | API Name | Method | URL |
|---|----------|--------|-----|
| 1 | [Get Email Schedules](#1-get-email-schedules) | GET | `/restapi/v2/workspaces/<workspace-id>/emailschedules` |
| 2 | [Create Email Schedule](#2-create-email-schedule) | POST | `/restapi/v2/workspaces/<workspace-id>/emailschedules` |
| 3 | [Update Email Schedule](#3-update-email-schedule) | PUT | `/restapi/v2/workspaces/<workspace-id>/emailschedules/<schedule-id>` |
| 4 | [Delete Email Schedule](#4-delete-email-schedule) | DELETE | `/restapi/v2/workspaces/<workspace-id>/emailschedules/<schedule-id>` |
| 5 | [Change Email Schedule Status](#5-change-email-schedule-status) | PUT | `/restapi/v2/workspaces/<workspace-id>/emailschedules/<schedule-id>/status` |
| 6 | [Trigger Email Schedule](#6-trigger-email-schedule) | POST | `/restapi/v2/workspaces/<workspace-id>/emailschedules/<schedule-id>` |

> **Note on naming:** Per the request for this batch, "Get Email Schedule List" is documented here as **"Get Email Schedules"**. The other five names are unchanged.
>
> **Note on method overloading:** `POST /emailschedules/<schedule-id>` (Trigger) and `PUT /emailschedules/<schedule-id>` (Update) share a path but differ by method, and `POST /emailschedules` (Create) differs only by the absence of `<schedule-id>`. Sending the wrong verb silently performs the wrong operation — Trigger sends real email immediately.

---

## Schedule ID Lifecycle

This is the behaviour that most often surprises integrators, so it is documented up front.

**[Update Email Schedule](#3-update-email-schedule) does not always update in place.** Depending on what changed, the server either edits the existing scheduler entry or **deletes it and inserts a brand-new one with a new `scheduleId`**.

| What you change in the update CONFIG | Result |
|---|---|
| `scheduleName` | **New `scheduleId` is minted.** The old scheduler entry is deleted. |
| Anything inside `scheduleDetails` that alters the effective run period (`calendarFrequency`, `hour`, `minute`, `skipFrequency`, `weekDays`, `weekDay`, `weekNumber`, `monthDay`, `monthDays`, `months`) | **New `scheduleId` is minted.** The old scheduler entry is deleted. |
| `emailIds`, `groupIds`, `cc`, `subject`, `message`, `isBCC`, `selectedTabs`, `reportBurstConfig` — with `scheduleName` and `scheduleDetails` unchanged or omitted | **`scheduleId` is preserved.** The existing entry is edited in place. |

The rule the server applies is: **keep the ID only if the schedule name and the computed run period are both byte-for-byte identical to the stored values.** Any difference in either one causes regeneration. (A third input, the schedule's timezone, also participates in this comparison, but the V2 update path always carries the stored timezone forward, so it can never be the cause.)

Practical consequences:

1. **The response is authoritative.** `data.scheduleId` in the [Update Email Schedule](#3-update-email-schedule) response is always the *effective* ID after the call — the new one if it was regenerated, the same one otherwise. Read it and replace whatever you had stored.
2. **The `<schedule-id>` in your request URL may be dead the moment the call returns.** A second update using the old path ID will fail with `7812` `SCHEDULE_DELETED`.
3. **Re-sending the current name and period is safe.** Because the comparison is on values, not on presence, a "write the whole object back" update that happens to send identical `scheduleName` and `scheduleDetails` keeps the ID.
4. **Renaming and re-scheduling are not free.** Both are structural changes that destroy and recreate the underlying scheduler task. Anything keyed off the old ID externally (dashboards, logs, your own database) needs remapping.
5. **The last-run history does not follow the new ID.** Because the old entry is deleted, run history and audit rows associated with the previous ID do not carry over to the new one.

If your integration needs stable identifiers, key your own records on `scheduleName` (unique within a workspace) rather than on `scheduleId`, and resolve the current ID through [Get Email Schedules](#1-get-email-schedules) before each write.

---

## White Label / Client Portal Behaviour

All six APIs are blocked in Client Portal / White Label request contexts — the same posture as the [Embed URL APIs](EMBEDURL_API_DOC_INFO.md#white-label--client-portal-behaviour), and the opposite of the [Publish](PUBLISH_API_DOC_INFO.md) and [Slideshow](SLIDESHOW_API_DOC_INFO.md) families.

| Scenario | Result |
|----------|--------|
| The API request arrives **through** a Client Portal / White Label custom domain | **Rejected with `7301`** before any business logic runs. Email schedules cannot be managed from a portal-domain context at all. |
| The API request is sent to the **standard API host** for a workspace that happens to be white-labelled | **Allowed**, and behaves exactly as for any other workspace. |

There is no `domainName` CONFIG attribute on any of these APIs — the commented-out entries in the request templates are not active. Manage schedules for a white-labelled workspace by calling the standard `analyticsapi.zoho.*` host.

---

## Quota Consumption

Each schedule consumes one or more units from the organization's email-schedule quota, reported per schedule as `schedulesConsumed` in the [Get Email Schedules](#1-get-email-schedules) response:

| Configuration | Units consumed |
|---|---|
| Default (no share criteria) | `ceil((recipients + cc recipients) / 25)` — one unit per 25 addresses. |
| `applyShareCriteria: true` | **One unit per recipient**, because each recipient receives an individually filtered export. |

A create or update that would push the organization past its quota is rejected before anything is saved.

---

## 1. Get Email Schedules

Returns every email schedule defined in the workspace, with its name, run period, enabled state, creator, and the views it delivers. This is the discovery call for `<schedule-id>`, which the other five APIs need.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/emailschedules` |
| **OAuth Scope** | `ZohoAnalytics.metadata.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user with Create Email Schedule permission on the workspace. |

> This API has no CONFIG parameter. All inputs are provided via URL path parameters only.

### Sample Requests

**Case 1 — Standard workspace**

```http
GET /restapi/v2/workspaces/137687000271334001/emailschedules HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — White Label / Client Portal: request sent through the portal domain (rejected)**

```http
GET /restapi/v2/workspaces/137687000271334009/emailschedules HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
```

### Sample Responses

**HTTP 200 OK — Workspace with a multi-view schedule and a single-view schedule**

```json
{
    "status": "success",
    "summary": "Get email schedules",
    "data": {
        "emailSchedules": [
            {
                "scheduleId": "137687000010815003",
                "scheduleName": "Weekly Sales Report",
                "schedulePeriod": "weekly on Friday at 14:10 IST",
                "schedulesConsumed": 1,
                "isEnabled": true,
                "createdBy": "jane.doe@example.com",
                "views": [
                    "137687000006991601",
                    "137687000006991650"
                ]
            },
            {
                "scheduleId": "137687000010815001",
                "scheduleName": "Daily Sales Snapshot",
                "schedulePeriod": "Every 6 days at 10:50 GMT",
                "schedulesConsumed": 1,
                "isEnabled": false,
                "createdBy": "jane.doe@example.com",
                "views": [
                    "137687000006991601"
                ]
            }
        ]
    }
}
```

**HTTP 200 OK — Workspace with no email schedules**

```json
{
    "status": "success",
    "summary": "Get email schedules",
    "data": {
        "emailSchedules": []
    }
}
```

**HTTP 403 Forbidden — Request sent through a Client Portal / White Label domain (Case 2)**

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
| `summary` | String | Localised operation summary. `"Get email schedules"` for this API. |
| `data` | JSONObject | Response payload wrapper. |
| `data.emailSchedules` | JSONArray | One entry per email schedule in the workspace. **Always present**; an empty array `[]` when the workspace has none. |
| `emailSchedules[].scheduleId` | String | ID of the schedule, serialised as a **string**. Use as `<schedule-id>` in the other five APIs. **May change after an update** — see [Schedule ID Lifecycle](#schedule-id-lifecycle). |
| `emailSchedules[].scheduleName` | String | Display name of the schedule. Unique within the workspace. |
| `emailSchedules[].schedulePeriod` | String | The run frequency and time rendered as **human-readable prose in the schedule's timezone**, e.g. `"weekly on Friday at 14:10 IST"`, `"daily at 12:05 IST"`, `"Every 6 days at 10:50 GMT"`. This is a display string, not a parseable structure — it is **not** the `scheduleDetails` object you sent, and there is no API that returns `scheduleDetails` back. To change the period you must resend a complete `scheduleDetails` object. |
| `emailSchedules[].schedulesConsumed` | Number | How many units of the organization's email-schedule quota this schedule consumes. See [Quota Consumption](#quota-consumption). |
| `emailSchedules[].isEnabled` | Boolean | `true` when the schedule is active and will run at its next occurrence; `false` when it has been deactivated via [Change Email Schedule Status](#5-change-email-schedule-status). A deactivated schedule still exists and can still be triggered manually. |
| `emailSchedules[].createdBy` | String | Email address of the user who created the schedule. Relevant to permissions: a custom-role user without full email-schedule access can only act on schedules where this is their own address. |
| `emailSchedules[].views` | JSONArray of String | IDs of the views the schedule delivers, as strings. Present for ordinary schedules. |
| `emailSchedules[].selectedTabs` | JSONArray of String | **Replaces `views`** when the schedule targets a *tabbed dashboard* — it then lists the delivered tab IDs instead. Exactly one of `views` or `selectedTabs` is present per entry, never both. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Workspace-wide, unfiltered, unpaged** | The response always covers every schedule in the workspace. There is no search, sort, or paging parameter — filter client-side on `scheduleName`, `isEnabled`, or `createdBy`. |
| **Empty array, not an error** | A workspace with no schedules returns HTTP 200 with `"emailSchedules": []`. |
| **`schedulePeriod` is prose, not structure** | It is generated for display and its wording varies by frequency and timezone. Never parse it to reconstruct a `scheduleDetails` object; keep your own copy of what you sent if you need to round-trip. |
| **`views` and `selectedTabs` are mutually exclusive** | Ordinary schedules report `views`; tabbed-dashboard schedules report `selectedTabs`. Code defensively for both keys rather than assuming `views` is always present. |
| **Recipients are not returned** | `emailIds`, `groupIds`, `cc`, `exportType`, `applyShareCriteria`, and `applyDefaultUf` are **not** in this response. There is no read API that returns a schedule's full configuration — an integration that needs it must retain what it sent. |
| **The only way to discover a regenerated ID** | After an update that changed the name or period, this API (or the update response itself) is how you learn the new `scheduleId`. |
| **Newer builds may return additional fields** | Some builds also include `subject`, `message`, and `isBCC` on each entry. Treat the response as extensible and ignore unrecognised keys rather than validating against a closed schema. |
| **Not callable from a portal domain** | See [White Label / Client Portal Behaviour](#white-label--client-portal-behaviour). |
| **Dependency chain** | [Get Workspace List](WORKSPACE_OPERATIONS_API_DOC_INFO.md) → `<workspace-id>` → Get Email Schedules → `<schedule-id>` for every other API here. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7103 | `META_OBJECT_NOT_PRESENT` — Workspace not found. | Verify `<workspace-id>` and that the `ZANALYTICS-ORGID` header matches it. |
| 7301 | `SECURITY_NOT_PERMITTED` — The request came through a Client Portal / White Label domain (where this API is disabled), or the user lacks Create Email Schedule permission on the workspace. | Call from the standard API host as an Account Admin, Organization Admin, Workspace Admin, or a user with Create Email Schedule permission. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.metadata.read`. |

---

## 2. Create Email Schedule

Creates a new recurring email schedule in the workspace and returns its ID.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/emailschedules` |
| **OAuth Scope** | `ZohoAnalytics.modeling.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user with Create Email Schedule permission on the workspace. The caller must additionally hold **Export** permission on every view listed in `viewIds`. |

### CONFIG Parameters

CONFIG is **mandatory** for this API.

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `scheduleName` | String | **Yes** | — | Name of the schedule. Must be **unique within the workspace** (`8000` otherwise). Also one of the two inputs that decide whether a later update regenerates the ID — see [Schedule ID Lifecycle](#schedule-id-lifecycle). |
| `viewIds` | JSONArray of String/Long | **Yes** | — | IDs of the views to deliver, 1–1000 entries. All must belong to `<workspace-id>`, and the caller must have Export permission on each. Duplicates are removed. **Cannot be changed after creation** — there is no `viewIds` attribute on the update API. |
| `exportType` | String (enum) | **Yes** | — | File format of the attachment. See [`exportType` Values](#exporttype-values). Case-insensitive on input, normalised to upper case. **Cannot be changed after creation.** |
| `scheduleDetails` | JSONObject | **Yes** | — | When the schedule runs. See [`scheduleDetails` Fields](#scheduledetails-fields). |
| `emailIds` | JSONArray of String | No* | — | Recipient email addresses, 0–1000 entries. Lower-cased and de-duplicated. Addresses outside a trusted domain may be rejected (`8031`). |
| `groupIds` | JSONArray of String/Long | No* | — | IDs of [workspace groups](WORKSPACE_GROUPS_API_DOC_INFO.md) whose members receive the email, 0–1000 entries. Must belong to `<workspace-id>`. |
| `cc` | JSONObject | No | — | Carbon-copy recipients. See [`cc` Fields](#cc-fields). |
| `isBCC` | Boolean | No | `true` | When `true` (the default), the addresses in `emailIds` are placed in **BCC** so recipients cannot see one another. Set `false` to address them in the **To** line. |
| `subject` | String | No | System default | Subject line of the email. Max 500 characters. |
| `message` | String | No | System default | Body text of the email. Max 5,000 characters. HTML is sanitised. |
| `applyShareCriteria` | Boolean | No | `false` | When `true`, each recipient receives an export filtered by the **share criteria already configured for that user** on the view — so different recipients see different rows from one schedule. Increases quota consumption to one unit per recipient (see [Quota Consumption](#quota-consumption)). |
| `applyDefaultUf` | Boolean | No | `false` | When `true`, the view's **default user filter** values are applied to the export instead of the unfiltered view. |
| `emailAsInline` | Boolean | No | `false` | When `true`, the exported content is rendered **inline in the email body** instead of being attached as a file. Meaningful for `HTML` exports. |
| `isNormalDbExp` | Boolean | No | `false` | Dashboard export layout switch. When `true`, the dashboard is exported in the standard document layout rather than the widget-by-widget layout. Applies to dashboard schedules only. |
| `selectedTabs` | JSONArray | No | All tabs | For a **tabbed dashboard**, restricts delivery to the listed tabs. 0–30 entries. Ignored for other view types. |
| `reportBurstConfig` | JSONObject | No | — | Turns the schedule into a **report burst** — one personalised email per row of a distribution-list table. See [`reportBurstConfig` Fields](#reportburstconfig-fields). |
| `validateSystemTags` | Boolean | No | `true` | If `true`, the request is rejected with a confirmation-required error (`8241`) when any view in `viewIds` carries a restricted **DATA_WARNING** system tag — directly, or inherited through lineage from a parent data source or table. Pass `false` to acknowledge and proceed. Only relevant when System Tags are enabled for the organization. |

\* At least one delivery target is required: the combination of `emailIds`, `groupIds`, and `cc` must resolve to at least one address, otherwise error `8033`.

> The `timeZone` of a schedule is **not settable through this API**. Every schedule is created in the timezone of the workspace's Account Admin, and that timezone is preserved for the life of the schedule.

#### `exportType` Values

| Value | Meaning | Restrictions |
|-------|---------|--------------|
| `CSV` | Comma-separated values file. | Not permitted for dashboards. |
| `XLS` | Excel workbook. | **Only one view** may be scheduled (`8037` if `viewIds` has more than one). Not permitted for dashboards. |
| `PDF` | PDF document. | Permitted for all view types, including dashboards. |
| `HTML` | HTML document, attachable or inline (see `emailAsInline`). | Permitted for all view types, including dashboards. |
| `IMG` | Image file. | **Chart views only** — every view in `viewIds` must be a chart (`8036` otherwise). Not permitted for dashboards. |

> **Dashboard rules:** a schedule whose first view is a dashboard may contain **only that one view** (`8034` otherwise) and may use only `PDF` or `HTML` (`8035` otherwise).

#### `scheduleDetails` Fields

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `calendarFrequency` | String (enum) | **Yes** | — | `daily`, `weekly`, `monthly`, or `yearly`. Determines which of the remaining fields apply. |
| `hour` | Integer | **Yes** | — | Hour of the day, **0–23**. |
| `minute` | Integer | **Yes** | — | Minute within the hour. Must be a **multiple of 5 in the range 0–55** (`0, 5, 10, … 55`). |
| `skipFrequency` | Integer | No | `0` | How many periods to skip between runs — `0` means every period, `1` means every other, and so on. The permitted maximum depends on `calendarFrequency`: **0–6** for `daily`, **0–3** for `weekly`, **0–11** for `monthly`, **0–4** for `yearly`. |
| `weekDays` | JSONArray of Integer | **Yes** for `weekly` | — | Days of the week to run on. `1` = Sunday … `7` = Saturday. |
| `weekNumber` | Integer | Conditional | — | Week of the month, **1–5**. Required for `monthly`/`yearly` when `monthDays`/`monthDay` is not supplied. |
| `weekDay` | Integer | Conditional | — | A single day of the week, `1` = Sunday … `7` = Saturday. Used together with `weekNumber`. |
| `monthDays` | JSONArray of Integer | Conditional | — | Days of the month for `monthly`. Values **1–31**, or **`99` to mean "last day of the month"**. Supply either `monthDays` **or** the `weekNumber` + `weekDay` pair. |
| `months` | JSONArray of Integer | **Yes** for `yearly` | — | Months to run in, `1` = January … `12` = December. |
| `monthDay` | Integer | Conditional | — | A single day of the month for `yearly`. Values **1–31**, or **`99` for the last day**. Supply either `monthDay` **or** the `weekNumber` + `weekDay` pair. |

**Which fields apply to which frequency:**

| `calendarFrequency` | Required alongside `hour`/`minute` | Optional |
|---|---|---|
| `daily` | — | `skipFrequency` (0–6) |
| `weekly` | `weekDays` | `skipFrequency` (0–3) |
| `monthly` | `monthDays` **or** (`weekNumber` + `weekDay`) | `skipFrequency` (0–11) |
| `yearly` | `months`, **and** `monthDay` **or** (`weekNumber` + `weekDay`) | `skipFrequency` (0–4) |

#### `cc` Fields

| Field | Type | Mandatory | Description |
|-------|------|-----------|--------------|
| `emailIds` | JSONArray of String | No | Carbon-copy email addresses. Lower-cased and de-duplicated. |
| `groupIds` | JSONArray of String/Long | No | IDs of workspace groups to carbon-copy. Must belong to `<workspace-id>`. |

#### `reportBurstConfig` Fields

A report burst reads a **distribution-list table** and sends one personalised email per row, filtering each report by values taken from that row.

| Field | Type | Mandatory | Description |
|-------|------|-----------|--------------|
| `zaTableId` | Long | **Yes** | ID of the table holding the distribution list (`8040` if not found). |
| `emailColumnId` | Long | **Yes** | ID of the column in that table containing the recipient email address (`8041` if not found). |
| `reports` | JSONArray | **Yes** | 1–15 report entries, each shaped as below. |
| `reports[].objId` | Long | **Yes** | ID of the view to include in the burst (`8046` if not found). |
| `reports[].exportFormat` | String | **Yes** | Export format for this report entry. |
| `reports[].deliveryMode` | Integer | No | `0` or `1` — how the report is delivered for this entry (`8047` if out of range). |
| `reports[].criteriaExpression` | String | No | Filter expression applied to this report per recipient. Max 65,535 characters. |
| `reports[].sortOrder` | Integer | No | Position of this report within the email. |
| `reports[].filterColumns` | JSONArray | No | 0–10 entries mapping distribution-list columns to report columns. |
| `reports[].filterColumns[].criteriaColumnId` | Long | **Yes** | Column in the distribution-list table supplying the filter value. |
| `reports[].filterColumns[].targetColumnId` | Long | **Yes** | Column in the report that the value filters (`8045` if not found). |

### Sample Requests

**Case 1 — Daily CSV schedule, minimal**

```http
POST /restapi/v2/workspaces/137687000271334001/emailschedules HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "scheduleName": "Daily Sales Snapshot",
    "viewIds": ["137687000006991601"],
    "exportType": "CSV",
    "scheduleDetails": {
        "calendarFrequency": "daily",
        "hour": 9,
        "minute": 0
    },
    "emailIds": ["jane.doe@example.com"],
    "subject": "Daily Sales Snapshot",
    "message": "Please find today's sales snapshot attached."
}
```

**Case 2 — Weekly PDF to users and groups, with CC, share criteria and default user filter clubbed together**

```http
POST /restapi/v2/workspaces/137687000271334001/emailschedules HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "scheduleName": "Weekly Sales Report",
    "viewIds": [
        "137687000006991601",
        "137687000006991650"
    ],
    "exportType": "PDF",
    "scheduleDetails": {
        "calendarFrequency": "weekly",
        "hour": 14,
        "minute": 30,
        "weekDays": [2, 6],
        "skipFrequency": 1
    },
    "emailIds": [
        "jane.doe@example.com",
        "john.roe@example.com"
    ],
    "groupIds": ["137687000006991700"],
    "cc": {
        "emailIds": ["manager@example.com"],
        "groupIds": ["137687000006991701"]
    },
    "isBCC": false,
    "applyShareCriteria": true,
    "applyDefaultUf": true,
    "subject": "Weekly Sales Report",
    "message": "Your weekly report is attached."
}
```

**Case 3 — Monthly dashboard as inline HTML on the last day of the month, restricted to selected tabs**

```http
POST /restapi/v2/workspaces/137687000271334001/emailschedules HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "scheduleName": "Monthly Revenue Board",
    "viewIds": ["137687000006991700"],
    "exportType": "HTML",
    "scheduleDetails": {
        "calendarFrequency": "monthly",
        "hour": 8,
        "minute": 15,
        "monthDays": [1, 99]
    },
    "emailIds": ["finance@example.com"],
    "emailAsInline": true,
    "isNormalDbExp": true,
    "selectedTabs": ["137687000006991710", "137687000006991711"],
    "subject": "Monthly Revenue Board",
    "validateSystemTags": false
}
```

**Case 4 — Yearly image schedule for a chart, on the second Monday of January and July**

```http
POST /restapi/v2/workspaces/137687000271334001/emailschedules HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "scheduleName": "Half-Yearly Trend Chart",
    "viewIds": ["137687000006991650"],
    "exportType": "IMG",
    "scheduleDetails": {
        "calendarFrequency": "yearly",
        "hour": 7,
        "minute": 0,
        "months": [1, 7],
        "weekNumber": 2,
        "weekDay": 2
    },
    "emailIds": ["leadership@example.com"]
}
```

### Sample Responses

**HTTP 200 OK — Schedule created**

```json
{
    "status": "success",
    "summary": "Create Email Schedule",
    "data": {
        "scheduleId": "137687000010886001"
    }
}
```

**HTTP 400 Bad Request — Duplicate schedule name**

```json
{
    "status": "failure",
    "summary": "DUPLICATE_SCHEDULE",
    "data": {
        "errorCode": 8000,
        "errorMessage": "A schedule with this name already exists in the workspace."
    }
}
```

**HTTP 403 Forbidden — Request sent through a Client Portal / White Label domain**

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
| `summary` | String | Localised operation summary. `"Create Email Schedule"` for this API. |
| `data` | JSONObject | Response payload wrapper. |
| `data.scheduleId` | String | ID of the newly created schedule, serialised as a **string**. Store it — but note it is **not permanently stable**: a later update that changes the name or the run period replaces it. See [Schedule ID Lifecycle](#schedule-id-lifecycle). |

> The response does not echo back the schedule's configuration. Confirm what was stored with [Get Email Schedules](#1-get-email-schedules).

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **`viewIds` and `exportType` are permanent** | Neither appears in the update CONFIG. To deliver different views or a different file format, delete the schedule and create a new one. |
| **Names must be unique per workspace** | A duplicate `scheduleName` fails with `8000`; the call is never turned into an update. |
| **Export permission is checked per view** | The caller must hold Export permission on **every** view in `viewIds`, in addition to the workspace-level Create Email Schedule permission. |
| **At least one resolved recipient is required** | `emailIds`, `groupIds`, and `cc` may each be omitted, but between them they must resolve to at least one address — otherwise `8033`. An empty group counts for nothing. |
| **Recipients are BCC by default** | `isBCC` defaults to **`true`**, so recipients cannot see one another unless you explicitly send `isBCC: false`. |
| **`applyShareCriteria` multiplies quota** | It changes consumption from one unit per 25 addresses to **one unit per recipient**, because each recipient gets an individually filtered export. Budget accordingly on large lists. |
| **Format restrictions are view-type dependent** | `XLS` is single-view only; `IMG` is chart-only; dashboards are single-view and `PDF`/`HTML` only. See [`exportType` Values](#exporttype-values). |
| **Timezone is inherited, not chosen** | The schedule runs in the workspace Account Admin's timezone. `scheduleDetails.hour` / `minute` are interpreted in that timezone, and `schedulePeriod` in the list response is rendered with it. |
| **Untrusted recipient domains are rejected** | If the organization restricts sharing to trusted domains, addresses outside them fail with `8031`. |
| **No `criteria` attribute** | Per-request row filtering is not supported; use `applyShareCriteria` (per-recipient share filters) or `reportBurstConfig` (per-row bursting). |
| **Not callable from a portal domain** | See [White Label / Client Portal Behaviour](#white-label--client-portal-behaviour). |
| **Dependency chain** | [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → `viewIds`; [Get Group List](WORKSPACE_GROUPS_API_DOC_INFO.md#1-get-group-list) → `groupIds` → Create Email Schedule → `scheduleId`. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7103 | `META_OBJECT_NOT_PRESENT` — Workspace not found. | Verify `<workspace-id>` and the `ZANALYTICS-ORGID` header. |
| 7104 | `META_OBJECT_NOT_PRESENT` — A view in `viewIds` does not exist. | Verify the IDs via [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list). |
| 7301 | `SECURITY_NOT_PERMITTED` — Request came through a Client Portal / White Label domain, the user lacks Create Email Schedule permission, or lacks Export permission on a view in `viewIds`. | Call from the standard API host with the required permissions. |
| 7319 | `OBJID_NOT_BELONGS_TO_DB` — A view in `viewIds` belongs to a different workspace. | Include only views from `<workspace-id>`. |
| 7832 | `INVALID_EXPORT_TYPE` — `exportType` is not one of the supported formats. | Use `CSV`, `XLS`, `PDF`, `HTML`, or `IMG`. |
| 8000 | `DUPLICATE_SCHEDULE` — A schedule with this `scheduleName` already exists in the workspace. | Choose a different name. |
| 8001 | `MAILCOUNT_PER_SCHED_EXCEED` — Too many recipients for a single schedule. | Reduce the recipient list, or split it across schedules. |
| 8009 | `MAIL_MULTIVIEW_MAXCOUNT_EXCEEEDED` — Too many views in one schedule. | Reduce `viewIds`, or split across schedules. |
| 8030 | `EMAILEXPORT_DISABLED_IN_ORG` — Email export is disabled for this organization. | Ask the Organization Admin to enable export in Security Controls. |
| 8031 | `UNTRUSTED_EMAILIDS` — A recipient address is outside the organization's trusted domains. | Use trusted-domain addresses, or ask the Organization Admin to add the domain. |
| 8032 | `EMAILINGVIEW_DISABLED` — Emailing this view is disabled. | Check the view's and workspace's export settings. |
| 8033 | `MAILSCH_SELECT_ATLEASTONE_EMAILID` — No recipient could be resolved from `emailIds`, `groupIds`, and `cc`. | Supply at least one address or a non-empty group. |
| 8034 | `ONLY_ONE_DASHBOARD_IS_ALLOWED_PER_SCH` — More than one view scheduled where the first is a dashboard. | Schedule the dashboard on its own. |
| 8035 | `EXPORT_FORMATS_ALLOWED_FOR_DASHBOARD` — Dashboard scheduled with a format other than `PDF`/`HTML`. | Use `PDF` or `HTML`. |
| 8036 | `EXPORT_FORMATS_ALLOWED_FOR_CHART` — `IMG` requested for a view that is not a chart. | Use `IMG` only for chart views. |
| 8037 | `ONLY_ONE_VIEW_IS_ALLOWED_FOR_XLS` — `XLS` requested with more than one view. | Send exactly one view, or choose another format. |
| 8040–8047 | `BURST_*` — A `reportBurstConfig` reference is invalid (distribution table, email column, report, filter column, or delivery mode). | Verify the IDs and values in `reportBurstConfig`. |
| 8119 | `INVALID_VALUE_FOR_ATTRIBUTE` — A `scheduleDetails` value is out of range (e.g. `hour` outside 0–23, `minute` not a multiple of 5, `weekDays` outside 1–7, `months` outside 1–12, `skipFrequency` beyond the limit for the chosen frequency). | The error message names the attribute and its permitted range; correct the value. |
| 8241 | `SYSTEM_TAG_DATA_WARNING_V2_VALIDATION_CONFIRMATION` — A view carries a restricted DATA_WARNING system tag. | Review the warning, then resend with `"validateSystemTags": false`. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.modeling.create`. |

---

## 3. Update Email Schedule

Updates an existing schedule's name, run period, recipients, or email content. **Read [Schedule ID Lifecycle](#schedule-id-lifecycle) first** — this call can replace the schedule's ID.

| Attribute | Value |
|-----------|-------|
| **Method** | PUT |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/emailschedules/<schedule-id>` |
| **OAuth Scope** | `ZohoAnalytics.modeling.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user with Create Email Schedule permission on the workspace. A custom-role user whose role does not grant access to all email schedules may update **only schedules they created themselves** — otherwise `8002`. |

### CONFIG Parameters

CONFIG is **mandatory**, but every field inside it is optional: **omitted fields retain their current values**. Note that `viewIds` and `exportType` are absent from this API entirely — they cannot be changed after creation.

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `scheduleName` | String | No | unchanged | New name for the schedule. Must remain unique within the workspace. **Changing this regenerates `scheduleId`.** |
| `scheduleDetails` | JSONObject | No | unchanged | New run frequency and time. Must be a **complete** object — it is not merged field-by-field with the existing period. See [`scheduleDetails` Fields](#scheduledetails-fields). **Changing the effective period regenerates `scheduleId`.** |
| `emailIds` | JSONArray of String | No | unchanged | **Replaces** the recipient list, 0–1000 entries. Does not regenerate the ID. |
| `groupIds` | JSONArray of String/Long | No | unchanged | **Replaces** the recipient group list, 0–1000 entries. Does not regenerate the ID. |
| `cc` | JSONObject | No | unchanged | **Replaces** the carbon-copy configuration. See [`cc` Fields](#cc-fields). Supplying `cc` with only `emailIds` leaves `cc.groupIds` unchanged, and vice versa. |
| `isBCC` | Boolean | No | unchanged | Whether recipients are addressed via BCC. |
| `subject` | String | No | unchanged | New subject line. Max 500 characters. |
| `message` | String | No | unchanged | New body text. Max 5,000 characters. HTML is sanitised. |
| `selectedTabs` | JSONArray | No | unchanged | For tabbed dashboards, the tabs to deliver. 0–30 entries. |
| `reportBurstConfig` | JSONObject | No | — | Report-burst configuration. See [`reportBurstConfig` Fields](#reportburstconfig-fields). **Omitting it removes any existing burst configuration**, converting the schedule back to a normal one — this is the one field where omission is not "leave unchanged". |
| `validateSystemTags` | Boolean | No | `true` | If `true`, the request is rejected with `8241` when a view delivered by this schedule carries a restricted DATA_WARNING system tag. Pass `false` to acknowledge and proceed. |

### Sample Requests

**Case 1 — Recipients and email content only (`scheduleId` is preserved)**

```http
PUT /restapi/v2/workspaces/137687000271334001/emailschedules/137687000010815003 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "emailIds": [
        "jane.doe@example.com",
        "new.recipient@example.com"
    ],
    "cc": {
        "emailIds": ["manager@example.com"]
    },
    "isBCC": true,
    "subject": "Weekly Sales Report (updated)",
    "message": "The recipient list for this report has been updated."
}
```

**Case 2 — Rename and re-schedule to daily (`scheduleId` is regenerated)**

```http
PUT /restapi/v2/workspaces/137687000271334001/emailschedules/137687000010815003 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "scheduleName": "Daily Sales Overview",
    "scheduleDetails": {
        "calendarFrequency": "daily",
        "hour": 10,
        "minute": 30
    },
    "subject": "Daily Sales Overview"
}
```

**Case 3 — Switch to a yearly period with new recipients (`scheduleId` is regenerated)**

```http
PUT /restapi/v2/workspaces/137687000271334001/emailschedules/137687000010815001 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "scheduleName": "Annual Revenue Report",
    "scheduleDetails": {
        "calendarFrequency": "yearly",
        "hour": 7,
        "minute": 0,
        "months": [1, 7],
        "monthDay": 1
    },
    "emailIds": ["finance@example.com"],
    "groupIds": ["137687000006991700"],
    "cc": {
        "emailIds": ["manager@example.com"],
        "groupIds": ["137687000006991701"]
    },
    "subject": "Annual Revenue Report",
    "message": "Here is your updated schedule report."
}
```

**Case 4 — White Label / Client Portal: request sent through the portal domain (rejected)**

```http
PUT /restapi/v2/workspaces/137687000271334009/emailschedules/137687000010815009 HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "subject": "Portal report"
}
```

### Sample Responses

**HTTP 200 OK — ID preserved (Case 1): `scheduleId` matches the one in the request URL**

```json
{
    "status": "success",
    "summary": "Update email schedule",
    "data": {
        "scheduleId": "137687000010815003"
    }
}
```

**HTTP 200 OK — ID regenerated (Cases 2 and 3): `scheduleId` differs from the one in the request URL**

```json
{
    "status": "success",
    "summary": "Update email schedule",
    "data": {
        "scheduleId": "137687000010887001"
    }
}
```

**HTTP 400 Bad Request — The schedule no longer exists (e.g. a stale ID after a previous regenerating update)**

```json
{
    "status": "failure",
    "summary": "SCHEDULE_DELETED",
    "data": {
        "errorCode": 7812,
        "errorMessage": "This schedule has been deleted."
    }
}
```

**HTTP 400 Bad Request — Custom-role user editing a schedule they do not own**

```json
{
    "status": "failure",
    "summary": "SCHMAIL_ACTION_NOTSUPPORTED",
    "data": {
        "errorCode": 8002,
        "errorMessage": "Sorry, you do not have permission to Edit Email Schedule."
    }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `status` | String | `"success"` on a successful call, `"failure"` on error. |
| `summary` | String | Localised operation summary. `"Update email schedule"` for this API. |
| `data` | JSONObject | Response payload wrapper. |
| `data.scheduleId` | String | **The effective schedule ID after the update**, serialised as a string. Equal to the `<schedule-id>` from the request URL when the ID was preserved, and a **different, newly minted ID** when the name or run period changed. Always read this value and replace any stored ID — see [Schedule ID Lifecycle](#schedule-id-lifecycle). The response gives no separate flag telling you which happened; compare it against the ID you sent. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **The ID may change — compare, don't assume** | Changing `scheduleName` or the effective run period deletes the old scheduler entry and creates a new one. Compare `data.scheduleId` with the `<schedule-id>` you sent to detect it. |
| **True partial update** | Every field falls back to its stored value when omitted, including `scheduleName` and `scheduleDetails`. A CONFIG containing only `subject` is valid and changes only the subject. |
| **`reportBurstConfig` is the exception to "omitted means unchanged"** | Omitting it **clears** any existing burst configuration. To keep a burst schedule bursting, resend the whole `reportBurstConfig` object on every update. |
| **List fields replace, never merge** | `emailIds`, `groupIds`, `cc.emailIds`, `cc.groupIds`, and `selectedTabs` each overwrite the stored list wholesale. To add one recipient, resend the full list. |
| **`scheduleDetails` must be complete** | It is parsed as a whole into a new run period. Sending only `hour` without `calendarFrequency` fails; send the full object. |
| **`viewIds` and `exportType` cannot be changed** | They are not accepted here. Delivering different views or a different format requires deleting and recreating the schedule. |
| **Still needs at least one recipient** | If the update leaves the schedule with no resolvable recipient, it fails with `8033` and nothing is saved. |
| **Ownership matters for custom roles** | A custom-role user without organization-wide email-schedule access can only update schedules whose `createdBy` is their own address (`8002` otherwise). Check `createdBy` via [Get Email Schedules](#1-get-email-schedules). |
| **Quota is re-evaluated** | Growing the recipient list, or turning on per-recipient filtering, can push the organization over its schedule quota and fail the update. |
| **Not callable from a portal domain** | See [White Label / Client Portal Behaviour](#white-label--client-portal-behaviour). |
| **Dependency chain** | [Get Email Schedules](#1-get-email-schedules) (resolve the current `scheduleId` and `createdBy`) → Update Email Schedule → read `data.scheduleId` → store it. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7103 | `META_OBJECT_NOT_PRESENT` — Workspace not found. | Verify `<workspace-id>` and the `ZANALYTICS-ORGID` header. |
| 7301 | `SECURITY_NOT_PERMITTED` — Request came through a Client Portal / White Label domain, or the user lacks Create Email Schedule permission on the workspace. | Call from the standard API host with the required permission. |
| 7812 | `SCHEDULE_DELETED` — No schedule exists with the given `<schedule-id>`. Commonly a **stale ID after an earlier update regenerated it**. | Re-resolve the current ID via [Get Email Schedules](#1-get-email-schedules). |
| 8000 | `DUPLICATE_SCHEDULE` — Another schedule in the workspace already uses the requested `scheduleName`. | Choose a different name. |
| 8001 | `MAILCOUNT_PER_SCHED_EXCEED` — Too many recipients after the update. | Reduce the recipient list. |
| 8002 | `SCHMAIL_ACTION_NOTSUPPORTED` — The schedule is not in this workspace, or a custom-role user attempted to edit a schedule they do not own. | Verify the ID belongs to this workspace; otherwise have the schedule's creator or an admin perform the update. |
| 8005 | `SCH_NOT_IN_WS` — The schedule does not belong to the specified workspace. | Ensure `<workspace-id>` and `<schedule-id>` are consistent. |
| 8031 | `UNTRUSTED_EMAILIDS` — A recipient address is outside the organization's trusted domains. | Use trusted-domain addresses. |
| 8033 | `MAILSCH_SELECT_ATLEASTONE_EMAILID` — The update would leave the schedule with no recipients. | Keep at least one address or non-empty group. |
| 8040–8047 | `BURST_*` — A `reportBurstConfig` reference is invalid. | Verify the IDs and values in `reportBurstConfig`. |
| 8119 | `INVALID_VALUE_FOR_ATTRIBUTE` — A `scheduleDetails` value is out of range. | The error message names the attribute and its permitted range. |
| 8241 | `SYSTEM_TAG_DATA_WARNING_V2_VALIDATION_CONFIRMATION` — A delivered view carries a restricted DATA_WARNING system tag. | Review the warning, then resend with `"validateSystemTags": false`. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.modeling.update`. |

---

## 4. Delete Email Schedule

Permanently deletes an email schedule. The views it delivered are unaffected; only the schedule and its pending runs are removed.

| Attribute | Value |
|-----------|-------|
| **Method** | DELETE |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/emailschedules/<schedule-id>` |
| **OAuth Scope** | `ZohoAnalytics.modeling.delete` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user with Create Email Schedule permission on the workspace. A custom-role user whose role does not grant access to all email schedules may delete **only schedules they created themselves** — otherwise `8002`. |

> This API has no CONFIG parameter. All inputs are provided via URL path parameters only.

### Sample Requests

**Case 1 — Standard workspace**

```http
DELETE /restapi/v2/workspaces/137687000271334001/emailschedules/137687000010815003 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — White Label / Client Portal: request sent through the portal domain (rejected)**

```http
DELETE /restapi/v2/workspaces/137687000271334009/emailschedules/137687000010815009 HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

```
HTTP/1.1 204 No Content
```

**HTTP 400 Bad Request — Schedule already deleted, or an ID left stale by an earlier update**

```json
{
    "status": "failure",
    "summary": "SCHEDULE_DELETED",
    "data": {
        "errorCode": 7812,
        "errorMessage": "This schedule has been deleted."
    }
}
```

**HTTP 400 Bad Request — Custom-role user deleting a schedule they do not own**

```json
{
    "status": "failure",
    "summary": "SCHMAIL_ACTION_NOTSUPPORTED",
    "data": {
        "errorCode": 8002,
        "errorMessage": "Sorry, you do not have permission to Delete Email Schedule."
    }
}
```

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload (`status`, `summary`, `data.errorCode`, `data.errorMessage`).

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Delete Email Schedule returns a bare HTTP `204 No Content` — no `status`/`summary` JSON to parse. |
| **Views are not affected** | Only the schedule definition and its pending runs are removed. The delivered reports, dashboards, and tables are untouched, as are their sharing and publish state. |
| **Not idempotent** | A second delete of the same `<schedule-id>` fails with `7812` `SCHEDULE_DELETED`. Guard retries with a [Get Email Schedules](#1-get-email-schedules) check. |
| **No trash, no restore** | A deleted schedule cannot be recovered. Recreating it produces a new `scheduleId` and resets its run history. |
| **Frees quota** | Deleting a schedule releases the units it consumed, so a create that previously failed on quota may then succeed. |
| **Single schedule per call** | There is no bulk-delete payload; iterate over [Get Email Schedules](#1-get-email-schedules) to clear several. |
| **Ownership matters for custom roles** | Same rule as Update — a custom-role user without organization-wide email-schedule access can only delete their own schedules. |
| **Not callable from a portal domain** | See [White Label / Client Portal Behaviour](#white-label--client-portal-behaviour). |
| **Dependency chain** | [Get Email Schedules](#1-get-email-schedules) (confirm the schedule exists and check `createdBy`) → Delete Email Schedule. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7103 | `META_OBJECT_NOT_PRESENT` — Workspace not found. | Verify `<workspace-id>` and the `ZANALYTICS-ORGID` header. |
| 7301 | `SECURITY_NOT_PERMITTED` — Request came through a Client Portal / White Label domain, or the user lacks Create Email Schedule permission on the workspace. | Call from the standard API host with the required permission. |
| 7812 | `SCHEDULE_DELETED` — No schedule exists with the given `<schedule-id>`. | Nothing to delete; re-check via [Get Email Schedules](#1-get-email-schedules). |
| 8002 | `SCHMAIL_ACTION_NOTSUPPORTED` — The schedule is not in this workspace, or a custom-role user attempted to delete a schedule they do not own. | Verify the ID belongs to this workspace; otherwise have the creator or an admin delete it. |
| 8005 | `SCH_NOT_IN_WS` — The schedule does not belong to the specified workspace. | Ensure `<workspace-id>` and `<schedule-id>` are consistent. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.modeling.delete`. |

---

## 5. Change Email Schedule Status

Activates or deactivates a schedule without deleting it. A deactivated schedule keeps its configuration and ID but stops running automatically.

| Attribute | Value |
|-----------|-------|
| **Method** | PUT |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/emailschedules/<schedule-id>/status` |
| **OAuth Scope** | `ZohoAnalytics.modeling.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user with Create Email Schedule permission on the workspace. |

### CONFIG Parameters

CONFIG is **mandatory** for this API.

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `operation` | String (enum) | **Yes** | — | `activate` to enable the schedule, `deactivate` to disable it. Any other value is rejected with `8119`, whose message names the two permitted values. |

### Sample Requests

**Case 1 — Deactivate a schedule (pause it without losing its configuration)**

```http
PUT /restapi/v2/workspaces/137687000271334001/emailschedules/137687000010815003/status HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "operation": "deactivate"
}
```

**Case 2 — Activate a previously deactivated schedule**

```http
PUT /restapi/v2/workspaces/137687000271334001/emailschedules/137687000010815003/status HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "operation": "activate"
}
```

**Case 3 — White Label / Client Portal: request sent through the portal domain (rejected)**

```http
PUT /restapi/v2/workspaces/137687000271334009/emailschedules/137687000010815009/status HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "operation": "activate"
}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. Confirm the new state with [Get Email Schedules](#1-get-email-schedules) (`isEnabled`).

```
HTTP/1.1 204 No Content
```

**HTTP 400 Bad Request — Invalid `operation` value**

```json
{
    "status": "failure",
    "summary": "INVALID_VALUE_FOR_ATTRIBUTE",
    "data": {
        "errorCode": 8119,
        "errorMessage": "Invalid value 'pause' for the attribute 'operation'. Allowed values are activate and deactivate."
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

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload. To read the resulting state, call [Get Email Schedules](#1-get-email-schedules) and inspect `isEnabled`.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Change Email Schedule Status returns a bare HTTP `204 No Content` — no `status`/`summary` JSON to parse. |
| **`operation` is a strict two-value enum** | Only the exact lowercase strings `activate` and `deactivate` are accepted. Anything else — including `true`/`false`, `enable`/`disable`, or different casing — fails with `8119`. |
| **Idempotent** | Activating an already-active schedule, or deactivating an already-inactive one, succeeds without error. |
| **The ID never changes** | Unlike [Update Email Schedule](#3-update-email-schedule), this call never regenerates `scheduleId` — it only flips the run state. |
| **Deactivation preserves everything** | Recipients, period, views, format, and the ID all survive. Reactivating resumes the schedule at its next natural occurrence; missed occurrences are not backfilled. |
| **Deactivated schedules can still be triggered manually** | [Trigger Email Schedule](#6-trigger-email-schedule) works regardless of `isEnabled`. |
| **Quota effects** | A deactivated schedule stops counting toward the active-schedule quota; reactivating it re-checks the quota and can fail if the organization is now at its limit. |
| **Not callable from a portal domain** | See [White Label / Client Portal Behaviour](#white-label--client-portal-behaviour). |
| **Dependency chain** | [Get Email Schedules](#1-get-email-schedules) (read current `isEnabled`) → Change Email Schedule Status → [Get Email Schedules](#1-get-email-schedules) to verify. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7103 | `META_OBJECT_NOT_PRESENT` — Workspace not found. | Verify `<workspace-id>` and the `ZANALYTICS-ORGID` header. |
| 7301 | `SECURITY_NOT_PERMITTED` — Request came through a Client Portal / White Label domain, or the user lacks Create Email Schedule permission on the workspace. | Call from the standard API host with the required permission. |
| 7812 | `SCHEDULE_DELETED` — No schedule exists with the given `<schedule-id>`. | Re-resolve the current ID via [Get Email Schedules](#1-get-email-schedules). |
| 8002 | `SCHMAIL_ACTION_NOTSUPPORTED` — The schedule is not in this workspace, or the caller may not act on it. | Verify the ID belongs to this workspace. |
| 8003 | `ALL_SCH_RUNERROR` — The schedule could not be activated. | Check that the schedule's views still exist and that the organization is within its schedule quota. |
| 8004 | `ALL_SCH_PAUSEERROR` — The schedule could not be deactivated. | Retry; if it persists, verify the schedule still exists. |
| 8005 | `SCH_NOT_IN_WS` — The schedule does not belong to the specified workspace. | Ensure `<workspace-id>` and `<schedule-id>` are consistent. |
| 8119 | `INVALID_VALUE_FOR_ATTRIBUTE` — `operation` is neither `activate` nor `deactivate`. | Send exactly `activate` or `deactivate`. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.modeling.update`. |

---

## 6. Trigger Email Schedule

Runs a schedule immediately — the "send now" action. **This sends real email to every configured recipient**, using the schedule's stored configuration.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/emailschedules/<schedule-id>` |
| **OAuth Scope** | `ZohoAnalytics.modeling.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user with Create Email Schedule permission on the workspace. Export must also be enabled for the organization and for the workspace. |

> This API has no CONFIG parameter. All inputs are provided via URL path parameters only.

### Sample Requests

**Case 1 — Send an active schedule immediately**

```http
POST /restapi/v2/workspaces/137687000271334001/emailschedules/137687000010815003 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Send a deactivated schedule on demand (allowed)**

```http
POST /restapi/v2/workspaces/137687000271334001/emailschedules/137687000010815001 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 3 — White Label / Client Portal: request sent through the portal domain (rejected)**

```http
POST /restapi/v2/workspaces/137687000271334009/emailschedules/137687000010815009 HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. The 204 confirms the send was *accepted and initiated*, not that every recipient's message was delivered.

```
HTTP/1.1 204 No Content
```

**HTTP 400 Bad Request — The schedule no longer exists**

```json
{
    "status": "failure",
    "summary": "SCHEDULE_DELETED",
    "data": {
        "errorCode": 7812,
        "errorMessage": "This schedule has been deleted."
    }
}
```

**HTTP 404 Not Found — Every view the schedule delivered has been deleted**

```json
{
    "status": "failure",
    "summary": "META_OBJECT_NOT_PRESENT",
    "data": {
        "errorCode": 7106,
        "errorMessage": "The view is not present."
    }
}
```

**HTTP 400 Bad Request — Export disabled for the organization**

```json
{
    "status": "failure",
    "summary": "EMAILEXPORT_DISABLED_IN_ORG",
    "data": {
        "errorCode": 8030,
        "errorMessage": "Email export is disabled for this organization."
    }
}
```

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload. There is no send-report, message ID, or per-recipient delivery status in the response.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Trigger Email Schedule returns a bare HTTP `204 No Content` — no `status`/`summary` JSON to parse, and no delivery report. |
| **It sends real email** | There is no dry-run or preview mode. Every configured recipient and CC address receives the export. Be careful when testing against a production schedule. |
| **Beware the verb** | `POST /emailschedules/<schedule-id>` triggers a send, while `PUT` on the same path updates the schedule. Sending POST where PUT was intended emails everyone. |
| **Works on deactivated schedules** | `isEnabled: false` only stops *automatic* runs; a manual trigger still sends. |
| **Does not shift the recurring timetable** | A manual send is a one-off. The schedule's next automatic occurrence is unchanged, and the manual run does not consume one. |
| **All views must still exist** | If every view the schedule delivered has been deleted, the trigger fails with `7106`. |
| **Export gates apply at send time** | Organization-level and workspace-level export restrictions are re-checked on every trigger, so a schedule created while export was enabled can start failing with `8030` later. |
| **204 means accepted, not delivered** | Mail generation and delivery continue asynchronously; per-recipient failures are not reported through this API. |
| **The ID never changes** | Triggering never regenerates `scheduleId`. |
| **Not callable from a portal domain** | See [White Label / Client Portal Behaviour](#white-label--client-portal-behaviour). |
| **Dependency chain** | [Get Email Schedules](#1-get-email-schedules) → `<schedule-id>` → Trigger Email Schedule. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7103 | `META_OBJECT_NOT_PRESENT` — Workspace not found. | Verify `<workspace-id>` and the `ZANALYTICS-ORGID` header. |
| 7106 | `META_OBJECT_NOT_PRESENT` — The schedule has no surviving views to send. | Recreate the schedule against existing views. |
| 7301 | `SECURITY_NOT_PERMITTED` — Request came through a Client Portal / White Label domain, or the user lacks Create Email Schedule permission on the workspace. | Call from the standard API host with the required permission. |
| 7812 | `SCHEDULE_DELETED` — No schedule exists with the given `<schedule-id>`. | Re-resolve the current ID via [Get Email Schedules](#1-get-email-schedules). |
| 8002 | `SCHMAIL_ACTION_NOTSUPPORTED` — The schedule is not in this workspace, or the caller may not act on it. | Verify the ID belongs to this workspace. |
| 8005 | `SCH_NOT_IN_WS` — The schedule does not belong to the specified workspace. | Ensure `<workspace-id>` and `<schedule-id>` are consistent. |
| 8030 | `EMAILEXPORT_DISABLED_IN_ORG` — Email export is disabled for this organization. | Ask the Organization Admin to enable export in Security Controls. |
| 8032 | `EMAILINGVIEW_DISABLED` — Emailing is disabled for a view in this schedule. | Check the view's and workspace's export settings. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.modeling.create`. |

---

## Appendix A – Common HTTP Headers

| Header | Value | Required | Description |
|--------|-------|----------|-------------|
| `Authorization` | `Zoho-oauthtoken <oauth-token>` | **Mandatory** | OAuth 2.0 access token of the calling user. Must carry the scope matching the operation (see [Appendix B](#appendix-b--oauth-scope-summary)). |
| `ZANALYTICS-ORGID` | Organization ID string | **Mandatory** | Organization ID of the workspace that owns the schedule. Obtainable from the [Get Organizations](ORG_INFO_API_DOC_INFO.md) response or from listing API responses as the `orgId` field. |
| `Content-Type` | `application/x-www-form-urlencoded` | Conditional | Required only for the three APIs that send a CONFIG body: [Create Email Schedule](#2-create-email-schedule), [Update Email Schedule](#3-update-email-schedule), and [Change Email Schedule Status](#5-change-email-schedule-status). The other three send no payload. |
| `Host` | `analyticsapi.zoho.com` (or the DC equivalent) | **Mandatory** | Must be the **standard** Zoho Analytics API host. A request whose host is a Client Portal / White Label custom domain is rejected with `7301` for all six APIs — see [White Label / Client Portal Behaviour](#white-label--client-portal-behaviour). |

> **`ZANALYTICS-DEST-ORGID` is not used by any API in this document.** That header applies only to cross-organization copy operations (Copy Workspace, [Copy Views](VIEW_OPERATIONS_API_DOC_INFO.md#2-copy-views), Copy Formulas), which target a destination organization. The email-schedule APIs have no portal-domain or cross-org targeting mechanism at all.

Example:

```http
POST /restapi/v2/workspaces/137687000271334001/emailschedules HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"scheduleName":"Daily Sales Snapshot","viewIds":["137687000006991601"],"exportType":"CSV","scheduleDetails":{"calendarFrequency":"daily","hour":9,"minute":0},"emailIds":["jane.doe@example.com"]}
```

---

## Appendix B – OAuth Scope Summary

| API | HTTP Method | Scope |
|-----|-------------|-------|
| Get Email Schedules | GET | `ZohoAnalytics.metadata.read` |
| Create Email Schedule | POST | `ZohoAnalytics.modeling.create` |
| Update Email Schedule | PUT | `ZohoAnalytics.modeling.update` |
| Delete Email Schedule | DELETE | `ZohoAnalytics.modeling.delete` |
| Change Email Schedule Status | PUT | `ZohoAnalytics.modeling.update` |
| Trigger Email Schedule | POST | `ZohoAnalytics.modeling.create` |

> This family **spans two scope groups**: the read API uses `metadata.read` while all five write APIs use `modeling.*`. An integration that lists and manages schedules therefore needs `ZohoAnalytics.metadata.read` **plus** the relevant `ZohoAnalytics.modeling.*` scopes — requesting only the `modeling` group leaves it unable to discover schedule IDs, and requesting only `metadata` leaves it read-only. Note also that **Trigger uses `modeling.create`**, so a token scoped for reading and updating cannot send a schedule on demand.

---

## Appendix C – API-Specific Notes and Behaviours

### Get Email Schedules

- **The entry point, and the only recovery path for a regenerated ID.** Every other API needs a `<schedule-id>`, and after an update that changed the name or period this is how you rediscover the new one. Treat it as the first call in any schedule workflow.
- **It is a summary, not the full configuration.** Recipients, CC list, `exportType`, `applyShareCriteria`, and `applyDefaultUf` are not returned, and no other API returns them either. An integration that needs to round-trip a schedule must retain its own copy of what it sent.
- **`schedulePeriod` is display prose, not data.** It is generated in the schedule's timezone with wording that varies by frequency (`"weekly on Friday at 14:10 IST"`, `"Every 6 days at 10:50 GMT"`). It is not the `scheduleDetails` you sent and must never be parsed to rebuild one.
- **`views` and `selectedTabs` are alternatives.** Tabbed-dashboard schedules report `selectedTabs` in place of `views`. Handle both keys.
- **`createdBy` is a permission signal.** For custom-role users without organization-wide email-schedule access, only entries whose `createdBy` matches their own address can be updated, deleted, or triggered — check it before offering those actions in a UI.
- **Different scope group from the write APIs.** This is the one API in the family on `metadata.read`; the other five are on `modeling.*`.
- **Dependency chain:** [Get Workspace List](WORKSPACE_OPERATIONS_API_DOC_INFO.md) → Get Email Schedules → `<schedule-id>` for every other API here.

### Create Email Schedule

- **`viewIds` and `exportType` are set for life.** Neither can be changed by [Update Email Schedule](#3-update-email-schedule). Getting them wrong means deleting the schedule and starting over, which also loses its run history — so validate view IDs and format compatibility before the first call.
- **Format rules are view-type dependent and enforced hard.** `XLS` accepts exactly one view; `IMG` accepts only charts; a dashboard must be scheduled alone and only as `PDF` or `HTML`. These are four distinct error codes (`8037`, `8036`, `8034`, `8035`) rather than one generic failure.
- **Recipients default to BCC.** `isBCC` defaults to `true`, so unless you set it to `false` recipients will not see one another — a deliberate privacy default that surprises people expecting a visible To line.
- **`applyShareCriteria` is the per-recipient personalisation switch, and it is expensive.** It changes quota consumption from one unit per 25 addresses to **one unit per recipient**. On a 200-person list that is the difference between 8 units and 200.
- **Uniqueness is on the name, and the name is also an ID-stability input.** A `scheduleName` must be unique in the workspace, and — because renaming regenerates the ID — it is the most stable key an integration can hold. Choose names deliberately.
- **No per-request row filter.** There is no `criteria` attribute. Row-level personalisation comes from `applyShareCriteria`, `applyDefaultUf`, or `reportBurstConfig`.
- **Dependency chain:** [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) + [Get Group List](WORKSPACE_GROUPS_API_DOC_INFO.md#1-get-group-list) → Create Email Schedule → [Get Email Schedules](#1-get-email-schedules).

### Update Email Schedule

- **It can replace the schedule's identity — the defining behaviour of this API.** Changing `scheduleName` or the effective run period deletes the underlying scheduler entry and inserts a new one with a new `scheduleId`; the old ID is then dead and returns `7812` on the next call. Changing only recipients or email content edits in place. Always read `data.scheduleId` from the response and compare it against what you sent. Full rules in [Schedule ID Lifecycle](#schedule-id-lifecycle).
- **It returns 200 with a body, unlike most V2 PUTs.** The body exists precisely to carry the possibly-new ID back, so this is one PUT whose response must never be ignored.
- **Genuinely partial — but with one trap.** Every omitted field keeps its stored value, *except* `reportBurstConfig`, whose omission **clears** the burst configuration. Burst schedules must resend it on every update.
- **List fields replace rather than merge.** Adding one recipient means resending the entire `emailIds` array; the same applies to `groupIds`, `cc.*`, and `selectedTabs`.
- **`scheduleDetails` is all-or-nothing.** It is parsed as a complete period definition, not merged field-by-field with the stored one.
- **Ownership gate for custom roles.** A custom-role user without organization-wide email-schedule access can only update schedules they created (`8002`), so check `createdBy` from [Get Email Schedules](#1-get-email-schedules) first.
- **Dependency chain:** [Get Email Schedules](#1-get-email-schedules) → Update Email Schedule → read `data.scheduleId` → store the effective ID.

### Delete Email Schedule

- **204 No Content, no body.** Verified against the implementation.
- **Views survive; the schedule does not.** Only the schedule definition, its pending runs, and its history are removed — nothing about the delivered reports, dashboards, or tables changes.
- **No trash and no restore.** Unlike views, which go through the [Trash APIs](TRASH_API_DOC_INFO.md), a deleted schedule is gone. Recreating it yields a new `scheduleId` and an empty run history.
- **Not idempotent.** A repeat delete fails with `7812`. The same code also appears when the ID went stale because an earlier update regenerated it — so a `7812` is not always "already deleted".
- **Frees quota immediately.** A create that previously failed on the organization's schedule limit may succeed right after a delete.
- **Same ownership gate as Update.** Custom-role users without full access can only delete their own schedules.
- **Dependency chain:** [Get Email Schedules](#1-get-email-schedules) → Delete Email Schedule.

### Change Email Schedule Status

- **204 No Content, no body.** Verified against the implementation.
- **The safe alternative to deleting.** Deactivation preserves the configuration, the recipients, and — importantly — the `scheduleId`. Use it for temporary pauses instead of delete-and-recreate, which would change the ID and lose history.
- **A strict two-value enum with an unusual shape.** `operation` accepts only the exact lowercase strings `activate` and `deactivate` — not booleans, not `enable`/`disable`. This is the only status-style API in the suite that uses a verb string rather than a `status` boolean, so it is easy to get wrong; the `8119` message names both valid values.
- **Idempotent, unlike most write APIs here.** Re-activating an active schedule or re-deactivating an inactive one is a no-op rather than an error.
- **Deactivation does not block manual sends.** [Trigger Email Schedule](#6-trigger-email-schedule) still works on an inactive schedule.
- **Reactivation re-checks quota.** A schedule paused while the organization had headroom can fail to reactivate (`8003`) if the quota has since been consumed.
- **Dependency chain:** [Get Email Schedules](#1-get-email-schedules) (read `isEnabled`) → Change Email Schedule Status → verify.

### Trigger Email Schedule

- **204 No Content, no body.** Verified against the implementation.
- **It is a live send with no dry-run.** Every recipient and CC address receives the export immediately. There is no preview, no send-to-self mode, and no way to undo it — treat it as a production action even in testing.
- **The most dangerous verb collision in the suite.** `POST /emailschedules/<schedule-id>` triggers a send while `PUT` on the exact same path updates the schedule. A client that gets the method wrong emails the entire recipient list instead of editing a subject line.
- **Works on deactivated schedules.** `isEnabled: false` suppresses only automatic runs.
- **Does not disturb the recurring timetable.** The next scheduled occurrence is unaffected and the manual run does not consume one.
- **Export gates are re-evaluated at send time.** Organization-level and workspace-level export restrictions are checked on every trigger, so a long-standing schedule can begin failing with `8030` after an admin disables export.
- **204 means accepted, not delivered.** Generation and delivery proceed asynchronously and per-recipient failures are not surfaced by this API.
- **Dependency chain:** [Get Email Schedules](#1-get-email-schedules) → Trigger Email Schedule.

---

## Appendix D – General Response Payload Notes

| Field / Behaviour | Detail |
|-------------------|--------|
| **Three of six APIs return 204 with no body** | [Delete Email Schedule](#4-delete-email-schedule), [Change Email Schedule Status](#5-change-email-schedule-status), and [Trigger Email Schedule](#6-trigger-email-schedule) return HTTP **204 No Content** on success — treat the 2xx status code as the success indicator and never expect or parse a JSON body. The other three return the standard `{"status", "summary", "data"}` envelope with HTTP 200. |
| **Update returns 200 with a body, and that body matters** | [Update Email Schedule](#3-update-email-schedule) is the exception among the write APIs: it returns `data.scheduleId`, which may be a **different ID** from the one in the request URL. Ignoring this response body is the most common way to end up with a stale ID and subsequent `7812` errors. |
| **Failure responses always carry a body** | Even for the 204 APIs, errors return `{"status": "failure", "summary": "<ERROR_NAME>", "data": {"errorCode": <n>, "errorMessage": "<text>"}}`. `summary` on failure is the error's symbolic name (e.g. `SCHEDULE_DELETED`, `SCHMAIL_ACTION_NOTSUPPORTED`), not a localised sentence. |
| **All IDs are strings** | `scheduleId` and every entry of `views` / `selectedTabs` are JSON **strings** even though the values are numeric. Parse them as strings or longs — never as native JSON numbers — to avoid precision loss on large IDs. |
| **`schedulesConsumed` and `isEnabled` are native types** | `schedulesConsumed` is a native JSON number and `isEnabled` a native boolean; everything else in the list response is a string or an array of strings. |
| **Empty array, never a missing key** | `data.emailSchedules` is always present in a successful [Get Email Schedules](#1-get-email-schedules) response, empty (`[]`) when the workspace has no schedules. |
| **Conditional keys within a schedule entry** | `views` and `selectedTabs` are mutually exclusive — exactly one appears per entry depending on whether the schedule targets a tabbed dashboard. Test for key presence rather than assuming `views`. |
| **The list response is a summary, not the full record** | Recipients, CC, `exportType`, `applyShareCriteria`, `applyDefaultUf`, and `reportBurstConfig` are never returned by any API in this family. Retain your own copy of a schedule's configuration if you need to reconstruct or clone it. |
| **Responses are extensible** | Some builds return additional per-schedule fields such as `subject`, `message`, and `isBCC`. Ignore unrecognised keys rather than validating against a closed schema. |
| **`schedulePeriod` is localised prose** | Its wording and timezone abbreviation depend on the schedule and the organization, so it is unsuitable for equality checks, sorting, or parsing. Compare schedules on `scheduleId` or `scheduleName` instead. |
| **Error codes 8000–8053 in this family are email-schedule specific** | They are defined in the mail-schedule error set and are numerically distinct from the identically numbered codes used by other API families. Always match on the `summary` symbolic name in addition to `errorCode` when handling errors across families. |
