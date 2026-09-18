# Zoho Analytics V2 REST API — Asynchronous Data Export

This document covers the four **asynchronous data export** REST APIs of Zoho Analytics — the APIs that hand the export off to a background job, hand you back a job ID, and let you collect the finished file later.

## What is an "Asynchronous" export?

An asynchronous export is a three-step conversation. You create a job, you find out when it has finished, and then you download the file. Nothing is produced inside the first request.

```
 1/2. Create Export Job  ──►  jobId
                                │
                                ▼
      3. Get Export Job Details ──► jobCode 1001/1002 → keep polling
                                │
                                ├─► jobCode 1003 → the job failed, stop
                                │
                                └─► jobCode 1004 → downloadUrl + expiryTime
                                                        │
                                                        ▼
                                          4. Download Exported Data
```

The trade for that extra round trip is that the restrictions of the synchronous export disappear.

| | Asynchronous export (this document) | [Synchronous export](SYNC_DATA_EXPORT_API_DOC_INFO.md) |
|---|---|---|
| **Endpoint prefix** | `/restapi/v2/bulk/workspaces/...` | `/restapi/v2/workspaces/...` |
| **First response** | A JSON envelope containing `jobId` | The exported file itself |
| **Number of calls** | Three (create, poll, download) | One |
| **Dashboards, Query Tables, live-connect views** | **Supported** | Rejected with `8133` |
| **Tables above one million rows** | **Supported** | Rejected with `8133` |
| **Ad-hoc SQL query as the source** | **Supported** | Not available on the view endpoint |
| **`callbackUrl`** | **Supported** | Not supported |
| **Payload ceiling** | None imposed on the job | 100 MB |

---

## Index

| # | API Name | Method | URL |
|---|----------|--------|-----|
| 1 | [Create Export Job using SQL Query (Asynchronous)](#1-create-export-job-using-sql-query-asynchronous) | GET | `/restapi/v2/bulk/workspaces/<workspace-id>/data` |
| 2 | [Create Export Job using View ID (Asynchronous)](#2-create-export-job-using-view-id-asynchronous) | GET | `/restapi/v2/bulk/workspaces/<workspace-id>/views/<view-id>/data` |
| 3 | [Get Export Job Details](#3-get-export-job-details) | GET | `/restapi/v2/bulk/workspaces/<workspace-id>/exportjobs/<job-id>` |
| 4 | [Download Exported Data](#4-download-exported-data) | GET | `/restapi/v2/bulk/workspaces/<workspace-id>/exportjobs/<job-id>/data` |

> **Note on naming:** The two job-creation APIs are documented as **"Create Export Job using SQL Query (Asynchronous)"** and **"Create Export Job using View ID (Asynchronous)"**; the remaining two as **"Get Export Job Details"** and **"Download Exported Data"**.

---

## How the Four APIs Relate

These four are not four independent APIs. They are one pipeline, and the `jobId` produced by either creation API is the only thing that connects them.

```
 [Get View List] ─────► <view-id> ──┐
                                    │
 [Get Columns] ──► column names ────┤
   (selectedColumns)                │
                                    ▼
                    2. Create Export Job using View ID  ──┐
                                                          │
 [Create Query Table] / any SQL SELECT ──► sqlQuery       ├──► data.jobId
                                    │                     │
                                    ▼                     │
                    1. Create Export Job using SQL Query ─┘
                                                          │
                        ┌─────────────────────────────────┘
                        ▼
              3. Get Export Job Details  ◄──── poll until jobCode = 1004
                        │                      (or let callbackUrl tell you)
                        │
                        ├──► data.downloadUrl  ──┐
                        └──► data.expiryTime     │
                                                 ▼
                                    4. Download Exported Data
                                       (returns the file)
```

| Relationship | Detail |
|--------------|--------|
| **`jobId` is produced once and consumed twice** | Both creation APIs return it in `data.jobId`. It is the `<job-id>` path segment for [Get Export Job Details](#3-get-export-job-details) and for [Download Exported Data](#4-download-exported-data). It appears in no other API's response — capture it from the create call. |
| **`downloadUrl` is exactly the Download Exported Data endpoint** | [Get Export Job Details](#3-get-export-job-details) returns a fully-qualified URL that resolves to [Download Exported Data](#4-download-exported-data) for the same workspace and job. Following `downloadUrl` and calling the endpoint yourself are the same operation. |
| **Downloading before the job finishes is an error, not a wait** | [Download Exported Data](#4-download-exported-data) does not block. It fails with `8121` while the job is queued and `8122` while it is running. The poll in [Get Export Job Details](#3-get-export-job-details) is mandatory, not advisory. |
| **The two creation APIs differ only in their source** | One takes a saved view via `<view-id>`, the other an ad-hoc `sqlQuery`. Both feed the identical job pipeline, and steps 3 and 4 cannot tell them apart. |
| **Their CONFIG sets are close but not identical** | `criteria` and `applyDefaultUF` exist only for the view export; `sqlQuery` and `tableCriteriaList` only for the SQL query export. See [Filtering: `criteria` and `tableCriteriaList`](#filtering-criteria-and-tablecriterialist). |
| **`<view-id>` comes from elsewhere** | Get it from [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list), from [Import Data into a New Table (Synchronous)](SYNC_DATA_IMPORT_API_DOC_INFO.md#1-import-data-into-a-new-table-synchronous), or from [Create Query Table](QUERY_TABLES_API_DOC_INFO.md#2-create-query-table). |
| **`selectedColumns` takes column display names** | Fetch them with [Get Columns](COLUMNS_API_DOC_INFO.md). An unmatched name fails the create call with `8015`; the job is never created. |
| **Export permission is granted by the sharing APIs** | The `export` share permission set by [Share Views](SHARING_API_DOC_INFO.md#2-share-views) is what both creation APIs check. For a SQL query export it is checked on **every table the query touches**. See [Permission Model](#permission-model). |
| **`callbackUrl` replaces the poll, it does not replace step 4** | The callback fires when the job reaches a terminal state and carries the same fields as [Get Export Job Details](#3-get-export-job-details), but you still have to call [Download Exported Data](#4-download-exported-data) to get the bytes. |
| **The job is owned by its creator** | Only the user who created the job can poll or download it. See [Permission Model](#permission-model). |
| **The same CONFIG vocabulary as the synchronous export** | Formats, delimiters, page setup, and image options carry identical meanings and value sets to [Export Data from a View](SYNC_DATA_EXPORT_API_DOC_INFO.md#1-export-data-from-a-view). A CONFIG proven there works here. |
| **Nothing consumes the exported file** | Export is read-only and terminal. Getting data back *into* a table is [Synchronous Data Import](SYNC_DATA_IMPORT_API_DOC_INFO.md) or [Asynchronous & Batch Data Import](ASYNC_DATA_IMPORT_API_DOC_INFO.md). |

### Typical sequences

**Export a dashboard as a PDF — impossible synchronously, routine here**

```
[Get View List] → <view-id> of a dashboard
   → Create Export Job using View ID   {"responseFormat":"pdf","dashboardLayout":1}
   → Get Export Job Details (poll)     jobCode 1004
   → Download Exported Data
```

**Export a joined result set that no saved view represents**

```
Create Export Job using SQL Query   {"sqlQuery":"SELECT ...","responseFormat":"csv"}
   → Get Export Job Details (poll)  jobCode 1004
   → Download Exported Data
```

**Fire and forget, with a callback instead of a poll**

```
Create Export Job using View ID   {"responseFormat":"csv","callbackUrl":"https://..."}
   → (your endpoint receives an HTTP POST carrying jobCode and downloadUrl)
   → Download Exported Data
```

---

## Limitations

These are the limits that apply with **default settings**. A request that exceeds one is rejected, not queued.

| Limitation | Value | Enforced by |
|------------|-------|-------------|
| **Simultaneous export jobs** | **5** per organization. A job counts against the limit while it is queued or running. | `8132` |
| **Export job retention** | **72 hours** from the moment the job is **created** — not from when it completes. After that the job record and the exported file are removed, and both [Get Export Job Details](#3-get-export-job-details) and [Download Exported Data](#4-download-exported-data) behave as though the job never existed. | `expiryTime` in the response, then `8120` / `jobCode` `1005` |
| **Job visibility** | An export job can be polled and downloaded **only by the user who created it**. An Account Admin cannot collect another user's job. | `8124` |
| **SQL query length** | **100,000** characters for `sqlQuery`. | `8507` |
| **SQL query result rows** | **800,000** rows. A row limit is appended to the query automatically. | Truncated silently |
| **`tableCriteriaList` entries** | **0–25** objects. | `8547` |
| **`selectedColumns` entries** | **1–300** column names. | `8547` |
| **`CONFIG` length** | **200,000** characters for the SQL query export, **100,000** for the view export. | `8507` |
| **`password` length** | **6–256** characters. | `8188` |
| **`callbackUrl` length** | **10,000** characters, and the host must be publicly reachable. | `8125`, `8126`, `8127` |
| **Image dimensions** | Width **250–2000** px, height **200–2000** px. | `7803` |
| **PDF cells** | **1,000,000** (visible columns × rows). | `7827` |
| **XLS rows per sheet** | **65,536** | `7806` |
| **XLS columns per sheet** | **256** | `7807` |
| **XLS characters per cell** | **32,767** | `7808` |

### Format restrictions

| Restriction | Behaviour |
|-------------|-----------|
| **A dashboard can only be exported as `pdf` or `html`** | Any other `responseFormat` fails with `8119`. |
| **`image` is only valid for chart views** | Any other view type fails with `8014`, and a SQL query export can never produce an image. |
| **A SQL query export is always a flat sheet** | `image` is unavailable, and the dashboard-only page-setup attributes have nothing to act on. |

> **Poll and download promptly, then persist.** Because the whole job — record and file — lives for 72 hours from creation, an integration that needs a durable copy must download inside that window and store the file itself. Nothing is recoverable afterwards.

---

## Job Codes and Polling

[Get Export Job Details](#3-get-export-job-details) reports progress through `jobCode`, with `jobStatus` carrying the matching human-readable text.

| `jobCode` | `jobStatus` | Meaning | What to do |
|-----------|-------------|---------|------------|
| `1001` | `JOB NOT INITIATED` | The job has been accepted and queued but has not started. | Wait a few seconds and poll again. |
| `1002` | `JOB IN PROGRESS` | The job is being processed. | Wait a few seconds and poll again. |
| `1003` | `ERROR OCCURRED` | The job stopped because of an error. | Stop polling. The job will never complete; create a new one. |
| `1004` | `JOB COMPLETED` | The file is ready. | Read `downloadUrl` and `expiryTime`, then call [Download Exported Data](#4-download-exported-data). |
| `1005` | `JOB NOT FOUND` | No job exists for this ID — it was never created, or it has passed its 72-hour retention. | Stop polling. Verify the job ID. |

`1003` and `1005` are terminal, exactly like `1004`. Only `1001` and `1002` justify another poll.

> `downloadUrl` and `expiryTime` are present **only** when `jobCode` is `1004`. Test for the keys rather than assuming them.

---

## The `callbackUrl` Attribute

`callbackUrl` is an optional attribute of both creation APIs. It saves you the poll.

| Effect | Detail |
|--------|--------|
| **You get notified instead of polling** | When the job reaches a terminal state, Zoho Analytics sends an **HTTP POST** to your URL with `Content-Type: application/json`. |
| **The body is the job details, unwrapped** | The payload is the same object that [Get Export Job Details](#3-get-export-job-details) returns as its `data` — `jobId`, `jobCode`, `jobStatus`, and, on success, `downloadUrl` and `expiryTime`. It is **not** wrapped in the `status` / `summary` / `data` envelope. |
| **It fires on failure too** | The callback is sent whether the job completed or errored. Read `jobCode` to tell which: `1004` means the file is ready, `1003` means it is not. |

Rules and constraints:

- The URL must be a well-formed, publicly reachable `http`/`https` address, at most 10,000 characters. A malformed URL is rejected with `8125`.
- URLs resolving to a **private or internal IP address** are rejected with `8127` — the callback cannot be pointed at a LAN host.
- If the endpoint cannot be reached while the request is being validated, the create call fails with `8126` and no job is created.
- Your endpoint should answer with a 2xx status. A non-2xx response is recorded as a delivery failure.
- **Delivery is attempted once.** There is no retry, and a failed callback does not affect the job — the file is still there to download.
- The callback is a **notification, not a guarantee**. Keep [Get Export Job Details](#3-get-export-job-details) as the fallback, and remember the 72-hour window.

---

## Permission Model

| API | Who may call it |
|-----|-----------------|
| [Create Export Job using SQL Query (Asynchronous)](#1-create-export-job-using-sql-query-asynchronous) | An Account Admin or Organization Admin, or a Workspace Admin, or any user with **Export** permission on **every table the query references**. |
| [Create Export Job using View ID (Asynchronous)](#2-create-export-job-using-view-id-asynchronous) | An Account Admin or Organization Admin, or a Workspace Admin, or the View Owner, or any user with **Export** permission on the view. |
| [Get Export Job Details](#3-get-export-job-details) | **Only the user who created the job.** Any other user, including an Account Admin, receives `8124`. |
| [Download Exported Data](#4-download-exported-data) | **Only the user who created the job.** Any other user, including an Account Admin, receives `8124`. |

Further gates on the two creation APIs:

| Gate | Behaviour |
|------|-----------|
| **Verified email** | The calling user's primary email address must be verified, otherwise `7565`. This applies to the two creation APIs only; polling and downloading do not require it. |
| **Organization security controls** | If the organization has disabled export, every create call fails with `8088` regardless of role or permissions. |

Two attributes behave differently for a caller who does not administer the workspace:

| Attribute | Account Admin / Organization Admin / Workspace Admin | Any other user |
|-----------|------------------------------------------------------|----------------|
| `showPersonalCols` | Honoured. Default `false`, so columns marked as personal data are **excluded** unless you ask for them. | Ignored. Personal-data columns are included, because a shared user only ever sees the columns already shared to them. |
| `criteria` (view export) | Applied as sent. | Applied, then **ANDed** with the share filter criteria configured for that user. A shared user can never widen their slice with a broad `criteria`. |

---

## Filtering: `criteria` and `tableCriteriaList`

The two creation APIs filter rows in different ways, and neither accepts the other's attribute.

| API | Filtering attribute |
|-----|---------------------|
| [Create Export Job using View ID (Asynchronous)](#2-create-export-job-using-view-id-asynchronous) | `criteria` — one filter expression, evaluated against the view. |
| [Create Export Job using SQL Query (Asynchronous)](#1-create-export-job-using-sql-query-asynchronous) | `tableCriteriaList` — a per-table filter list. Row selection otherwise belongs in the `WHERE` clause of `sqlQuery` itself. |

### `criteria` syntax

`criteria` is a SQL-like filter expression that selects which rows are exported. Column names are quoted with double quotes and string literals with single quotes:

```
"Region"='East'
"SalesTable"."Region"='East'
"Sales">1000 and "Region"='West'
"Region" in ('East','West') and "Order Date">='01-Jan-2026'
```

Notes that matter in practice:

- Omitting `criteria` exports **every row** the caller is entitled to see.
- A column named in `criteria` must exist in the view, otherwise the create call fails with `7330`.
- A table name that is not part of the view fails with `7332`.
- A malformed expression fails with `7331`; one that parses but cannot be converted to SQL fails with `7327`.
- Aggregate functions (`sum`, `avg`, `count`, …) are not permitted — they fail with `7333`.
- For a **tabular view**, only columns of its own base table may be referenced; anything else fails with `7543`.
- For a **shared user**, the share filter criteria is ANDed automatically — see [Permission Model](#permission-model).
- The expression is validated **before** the job is created, so a bad `criteria` produces an error response and no `jobId`.
- Because `criteria` travels inside the `CONFIG` query parameter, it must be JSON-escaped and then URL-encoded. Double quotes around column names become `\"` in JSON and `%22` on the wire.
- The same grammar is used by [Update Row](ROW_API_DOC_INFO.md#2-update-row), [Delete Row](ROW_API_DOC_INFO.md#3-delete-row), and [Export Data from a View](SYNC_DATA_EXPORT_API_DOC_INFO.md#1-export-data-from-a-view).

### `tableCriteriaList` structure

`tableCriteriaList` applies one filter expression per participating table, and the filters are pushed into the generated query.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tableCriteriaList[].viewId` | Long | **Yes** | ID of a table that the query references. Must belong to `<workspace-id>`, otherwise `7571`. |
| `tableCriteriaList[].criteria` | String | **Yes** | Filter expression for that table, using the same grammar as `criteria` above. |

- 0 to 25 entries. More fails with `8547`.
- Every `viewId` listed must actually be involved in `sqlQuery`, otherwise `7836`.
- Both fields are mandatory inside each object; omitting either fails the create call with `8079`.

---

## Shared CONFIG Attributes

Everything in this section applies to **both** creation APIs. The attributes unique to each are listed in that API's own section.

### Common to every format

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `responseFormat` | String | No | `"csv"` | Output format. One of `csv`, `json`, `xml`, `xls`, `pdf`, `html`, `image` (case-insensitive). Any other value fails with `8001`. |
| `password` | String | No | — | Protects the exported file with a password. 6 to 256 characters; shorter fails with `8188`. Changes the delivery format — see [Password Protection](#password-protection). |
| `selectedColumns` | JSONArray of String | No | — | Column **display names** to export, in the order given, 1–300 entries. An unmatched name fails with `8015`. Omit to export all eligible columns. |
| `showHiddenCols` | Boolean | No | `true` (`false` for `html`) | Whether columns hidden in the view are included. A column named explicitly in `selectedColumns` is always included, hidden or not. |
| `showPersonalCols` | Boolean | No | `false` | Whether columns marked as personal data are included. Honoured only for administering users — see [Permission Model](#permission-model). |
| `includeHeader` | Boolean | No | `true` | Whether a header row of column names is written. Applies to `csv`, `xls`, `pdf`, and `html`. |
| `includeRowNums` | Boolean | No | `false` | Prefixes each record with a sequential `Row Number` value. |
| `includeRowIds` | Boolean | No | `false` | Equivalent to `includeRowNums` — both feed the same switch, so sending either one enables the row-number column. |
| `callbackUrl` | String | No | — | URL notified when the job reaches a terminal state. Maximum 10,000 characters. See [The `callbackUrl` Attribute](#the-callbackurl-attribute). |
| `validateSystemTags` | Boolean | No | `true` | When `true`, the request is rejected with `8241` if the source carries a restricted **DATA_WARNING** system tag — applied directly, or inherited through lineage from a parent data source or table. Send `false` to acknowledge and proceed. Only relevant when System Tags are enabled for the organization. |

### CSV specific

Applicable when `responseFormat` is `csv`.

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `delimiter` | Integer | No | `0` (comma) | Field separator. `0` Comma, `1` Tab, `2` Semicolon, `3` Space, `4` Pipe. Any other value fails with `8119`. |
| `recordDelimiter` | Integer | No | `0` (DOS) | Line ending. `0` DOS (`\r\n`), `1` UNIX (`\n`), `2` MAC (`\r`). Any other value fails with `8119`. |
| `quoted` | Integer | No | — | Text qualifier wrapped around values. `0` single quote, `1` double quote. Omit for no qualifier. |

### JSON and XML specific

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `keyValueFormat` | Boolean | No | `true` for `json`, `false` for `xml` | Chooses the record shape. `true` emits each row as column-name/value pairs; `false` emits a wrapped envelope with a separate column list and rows as positional arrays. See [Exported File Structure by Format](#exported-file-structure-by-format). |

### PDF specific

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `paperSize` | Integer | No | `4` (A4) | `0` Letter, `1` Legal, `2` Tabloid, `3` A3, `4` A4, `5` Auto-fit width. For a **dashboard** the range is `0`–`4` and the default is `2` (Tabloid). Outside the range fails with `8119`. |
| `paperStyle` | String | No | `"Portrait"` | `"Portrait"` or `"Landscape"` (case-insensitive). |
| `topMargin` | Float | No | `0.25` | Top margin in inches, `0`–`1` inclusive. Outside fails with `7801`. |
| `bottomMargin` | Float | No | `0.25` | Bottom margin in inches, `0`–`1`. |
| `leftMargin` | Float | No | `0.25` | Left margin in inches, `0`–`1`. |
| `rightMargin` | Float | No | `0.25` | Right margin in inches, `0`–`1`. |
| `showTitle` | Integer | No | `0` (top) | Where the title is placed. `0` Top, `1` Bottom, `2` Do not include. |
| `showDesc` | Integer | No | `0` (top) | Where the description is placed. `0` Top, `1` Bottom, `2` Do not include. |
| `columnWidthRatio` | Integer | No | `1` | Column sizing. `0` proportional to the widths set in the view, `1` sized to content, `2` all columns equal. |
| `exportLanguage` | Integer | No | `0` (English) | Font set used for rendering text. `0` English, `1` Chinese, `2` Japanese, `3` European, `4` Korean. Pick the one matching your data, otherwise non-Latin characters may not render. |
| `leftHeader` | Integer | No | `1` (Title) | Content of the top-left page-header slot. See [Header and Footer Slot Values](#header-and-footer-slot-values). |
| `centerHeader` | Integer | No | `0` (Blank) | Content of the top-centre page-header slot. |
| `rightHeader` | Integer | No | `2` (Date) | Content of the top-right page-header slot. |
| `leftFooter` | Integer | No | `0` (Blank) | Content of the bottom-left page-footer slot. |
| `centerFooter` | Integer | No | `3` (Page number) | Content of the bottom-centre page-footer slot. |
| `rightFooter` | Integer | No | `0` (Blank) | Content of the bottom-right page-footer slot. |
| `leftHeaderText` | String | No | — | Custom text for the top-left slot. Read only when `leftHeader` is `5`. |
| `centerHeaderText` | String | No | — | Custom text for the top-centre slot. Read only when `centerHeader` is `5`. |
| `rightHeaderText` | String | No | — | Custom text for the top-right slot. Read only when `rightHeader` is `5`. |
| `leftFooterText` | String | No | — | Custom text for the bottom-left slot. Read only when `leftFooter` is `5`. |
| `centerFooterText` | String | No | — | Custom text for the bottom-centre slot. Read only when `centerFooter` is `5`. |
| `rightFooterText` | String | No | — | Custom text for the bottom-right slot. Read only when `rightFooter` is `5`. |

#### Header and Footer Slot Values

The same seven values apply to every one of the six slots.

| Value | Content placed in the slot |
|-------|----------------------------|
| `0` | Blank |
| `1` | View title |
| `2` | Export date |
| `3` | Page number |
| `4` | Page number with total (`3 of 12`) |
| `5` | The custom text from the matching `…Text` attribute |
| `6` | Logo |

Any other value fails with `8119`. When a slot is set to `1`, the source's own title is substituted and the matching `…Text` attribute is ignored.

### HTML specific

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `includeTitle` | Integer | No | `0` (top) | Where the title is placed. `0` Top, `1` Bottom, `2` Do not include. |
| `includeDesc` | Integer | No | `0` (top) | Where the description is placed. `0` Top, `1` Bottom, `2` Do not include. |
| `columnWidthRatio` | Integer | No | `2` | Column sizing. `0` proportional to the widths set in the view, `1` sized to content, `2` all columns equal. Note the default differs from PDF. |

### XLS specific

`xls` adds no attributes of its own beyond `includeHeader`. It uses `selectedColumns`, `showHiddenCols`, `showPersonalCols`, `includeRowNums`, `password`, and the relevant filter attribute.

### Password Protection

Sending `password` changes **how** the file is delivered, not only whether it is locked. The `Content-Type` of [Download Exported Data](#4-download-exported-data) reflects this:

| `responseFormat` | Result when `password` is sent |
|------------------|--------------------------------|
| `csv`, `json`, `xml`, `html`, `image` | The file is placed inside a **password-protected ZIP archive**; the download returns `application/zip`. |
| `xls` | The workbook itself is encrypted. `Content-Type` stays `application/vnd.ms-excel`. |
| `pdf` | The PDF itself is encrypted, with printing and copying permitted. `Content-Type` stays `application/pdf`. |

---

## 1. Create Export Job using SQL Query (Asynchronous)

Creates an export job whose source is an ad-hoc SQL `SELECT` statement rather than a saved view.

| Attribute | Value |
|-----------|-------|
| **URL** | `/restapi/v2/bulk/workspaces/<workspace-id>/data` |
| **HTTP Method** | `GET` |
| **OAuth Scope** | `ZohoAnalytics.data.read` |
| **Mandatory Header** | `ZANALYTICS-ORGID` |
| **CONFIG** | **Mandatory** — it carries `sqlQuery` |
| **Success Status** | `200 OK` with a JSON body carrying `data.jobId` |

**Path parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `<workspace-id>` | Long | ID of the workspace the query runs against. Every table the query references must belong to it. |

### CONFIG Parameters

In addition to the [Shared CONFIG Attributes](#shared-config-attributes):

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `sqlQuery` | String | **Yes** | — | The SQL `SELECT` statement to execute, maximum 100,000 characters. Table and column names are the display names shown in Zoho Analytics. A statement that references no table, or that cannot be parsed, fails the create call. |
| `tableCriteriaList` | JSONArray of Object | No | — | Per-table filter expressions, 0–25 entries. See [`tableCriteriaList` structure](#tablecriterialist-structure). |

> `criteria` and `applyDefaultUF` are **not** accepted by this API. Row selection belongs in the `WHERE` clause of `sqlQuery`, or in `tableCriteriaList`.

> `responseFormat: "image"` can never succeed here — a query result is a flat sheet, not a chart, so the request fails with `8014`.

### Sample Requests

For readability the `CONFIG` values below are shown as plain JSON. On the wire each must be stringified and URL-encoded, as in [Appendix A](#appendix-a--common-http-headers).

**Case 1 — `tableCriteriaList` alone: filter each participating table**

```http
GET /restapi/v2/bulk/workspaces/466206000000071000/data HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

```json
{
  "sqlQuery": "SELECT \"Sales\".\"Region\", \"Sales\".\"Amount\", \"Targets\".\"Quota\" FROM \"Sales\" JOIN \"Targets\" ON \"Sales\".\"Region\" = \"Targets\".\"Region\"",
  "responseFormat": "csv",
  "tableCriteriaList": [
    {
      "viewId": 466206000000072000,
      "criteria": "\"Region\"='East'"
    },
    {
      "viewId": 466206000000072500,
      "criteria": "\"Quota\">100000"
    }
  ]
}
```

Each expression is pushed into the generated query for its own table. Both `viewId` values must be tables the statement actually references, otherwise the call fails with `7836`.

**Case 2 — a fully configured CSV job with a callback**

Covers column selection, the three CSV delimiter attributes, row numbers, password protection, and callback notification in one call.

```json
{
  "sqlQuery": "SELECT \"Region\", \"Product\", \"Sales\" FROM \"SalesTable\" WHERE \"Sales\" > 1000",
  "responseFormat": "csv",
  "selectedColumns": ["Region", "Product", "Sales"],
  "delimiter": 1,
  "recordDelimiter": 1,
  "quoted": 1,
  "includeHeader": true,
  "includeRowNums": true,
  "showHiddenCols": false,
  "showPersonalCols": false,
  "password": "Zoho@123",
  "callbackUrl": "https://example.com/hooks/za-export"
}
```

Because `password` is present, [Download Exported Data](#4-download-exported-data) will return a **ZIP archive** rather than a bare CSV.

**Case 3 — the same query as a print-ready PDF**

```json
{
  "sqlQuery": "SELECT \"Region\", \"Product\", \"Sales\" FROM \"SalesTable\"",
  "responseFormat": "pdf",
  "paperSize": 4,
  "paperStyle": "Landscape",
  "topMargin": 0.5,
  "bottomMargin": 0.5,
  "showTitle": 0,
  "showDesc": 2,
  "columnWidthRatio": 2,
  "exportLanguage": 0,
  "leftHeader": 1,
  "rightHeader": 2,
  "leftFooter": 5,
  "leftFooterText": "Confidential — Internal Use Only",
  "centerFooter": 4,
  "includeHeader": true
}
```

### Sample Responses

**HTTP 200 OK — the job was created**

```json
{
  "status": "success",
  "summary": "Create bulk export job",
  "data": {
    "jobId": "466206000000091000"
  }
}
```

**HTTP 400 Bad Request — the concurrent job limit is reached**

```json
{
  "status": "failure",
  "summary": "ASYNC_EXPORT_LIMIT_EXCEEDED",
  "data": {
    "errorCode": 8132,
    "errorMessage": "Async export limit reached. Kindly retry once after your previously initiated jobs are completed."
  }
}
```

**HTTP 400 Bad Request — a `tableCriteriaList` entry names a table the query does not use**

```json
{
  "status": "failure",
  "summary": "GIVEN_TABLE_NOT_INVOLVED_IN_SQL_EXPORT",
  "data": {
    "errorCode": 7836,
    "errorMessage": "The given table is not involved in the SQL query."
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | String | `"success"` on success. |
| `summary` | String | `"Create bulk export job"`. |
| `data` | Object | Job identification. |
| `data.jobId` | String | ID of the created job, **as a string**. The `<job-id>` for [Get Export Job Details](#3-get-export-job-details) and [Download Exported Data](#4-download-exported-data). |

### Notes & Behaviour

| Behaviour | Detail |
|-----------|--------|
| **`CONFIG` is mandatory here** | Unlike [Create Export Job using View ID (Asynchronous)](#2-create-export-job-using-view-id-asynchronous), this API has no source without a CONFIG, so an absent or empty CONFIG is rejected with `8077`. |
| **Export permission is checked per involved table** | The statement is parsed, the participating tables are resolved, and Export permission is verified on each. `7301` here means "not allowed to export one of the tables in the query", not "not allowed to export". |
| **A row limit is appended automatically** | The generated query is capped at 800,000 rows. A statement that would return more is silently truncated — the job still completes successfully. |
| **A query that references no table is rejected** | `7835`. Constant-only `SELECT` statements are not a valid export source. |
| **Validation happens before the job exists** | A bad `sqlQuery`, a bad `tableCriteriaList`, an unreachable `callbackUrl`, or a permission failure all produce an error response and **no** `jobId`. |
| **The whole job may still fail later** | Creation success only means the request was accepted. Errors raised while producing the file surface as `jobCode` `1003` on [Get Export Job Details](#3-get-export-job-details). |
| **`jobId` is a string** | Even though it is numerically a long. Do not parse it into a fixed-width integer type. |
| **Dependency chain:** | Any SQL `SELECT` over the workspace's tables → Create Export Job using SQL Query (Asynchronous) → `data.jobId` → [Get Export Job Details](#3-get-export-job-details) → [Download Exported Data](#4-download-exported-data). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7301 | `SECURITY_NOT_PERMITTED` — The caller lacks Export permission on at least one table referenced by the query. | Ensure the caller holds Export permission on every table in the statement. |
| 7401 | The SQL statement is not a valid or allowed construct. | Review the syntax; only `SELECT` statements over the workspace's own tables are accepted. |
| 7565 | `UNVERIFIED_EMAIL` — The calling user's primary email address is not verified. | Verify the account's primary email address and retry. |
| 7571 | `UNKNOWN_VIEWID_PASSED` — A `tableCriteriaList[].viewId` does not exist in this workspace. | Verify the IDs with [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list). |
| 7801 | `MARGIN_VALUE_EXCEEDS` — A PDF margin is outside `0`–`1` inches. | Send a value between `0` and `1`. |
| 7824 | `EXPORT_REQ_BLOCKED` — Export has been blocked for this workspace. | Contact Zoho Analytics support using the address in the error message. |
| 7827 | `EXP_PDF_RECORD_LIMIT` — The PDF exceeds 1,000,000 cells. | Narrow the statement or use `selectedColumns`. |
| 7835 | `NO_TABLES_INVOLVED_IN_SQL_EXPORT` — The statement references no table. | Query at least one table of the workspace. |
| 7836 | `GIVEN_TABLE_NOT_INVOLVED_IN_SQL_EXPORT` — A `tableCriteriaList[].viewId` is not used by the statement. | List only tables the query actually references. |
| 7837 | `INVOLVED_TABLE_DOES_NOT_HAVE_PERMISSION` — A table used by the query has no matching `tableCriteriaList` entry where one is required. | Supply a criteria entry for every participating table. |
| 8001 | `INVALID_RESP_FORMAT` — `responseFormat` is not a supported value. | Send one of `csv`, `json`, `xml`, `xls`, `pdf`, `html`. |
| 8014 | `API_IMAGE_RESPONSE_NOT_POSSIBLE` — `image` was requested. | A query result cannot be rendered as an image; choose another format. |
| 8015 | `API_EXPORT_COLUMN_NOT_PRESENT` — A name in `selectedColumns` is not in the result set. | Match the names to the columns the statement projects. |
| 8088 | `SECURITY_CONTROLS_FEATURE_DISABLED` — Export is disabled for the organization. | Ask an Organization Admin to re-enable export. |
| 8119 | `INVALID_VALUE_FOR_ATTRIBUTE` — A numeric or enumerated attribute is outside its permitted set. | Correct the value; see [Appendix E](#appendix-e--enum-reference). |
| 8125 | `CALLBACKURL_NOT_VALID` — `callbackUrl` is malformed. | Send a well-formed absolute `http`/`https` URL. |
| 8126 | `CALLBACKURL_CONNECTION_ERROR` — `callbackUrl` could not be reached during validation. | Make the endpoint publicly reachable before creating the job. |
| 8127 | `CALLBACKURL_RESTRICTED` — `callbackUrl` resolves to a private or internal address. | Use a publicly routable host. |
| 8128 | `INTERNAL_ERROR_ON_INITIATING_EXPORT` — The job could not be queued. | Retry; if it persists, contact support. |
| 8132 | `ASYNC_EXPORT_LIMIT_EXCEEDED` — 5 export jobs are already queued or running for the organization. | Wait for an in-flight job to finish, then retry. |
| 8188 | `EXPORT_INVALID_PASSWORD` — `password` is blank or shorter than 6 characters. | Send 6–256 characters. |
| 8241 | `SYSTEM_TAG_DATA_WARNING_V2_VALIDATION_CONFIRMATION` — A source table carries a restricted DATA_WARNING system tag. | Review the warning, then resend with `"validateSystemTags": false`. |
| 8077 | `EMPTY_JSON_CONFIGURATION` — `CONFIG` was not sent, or was sent empty. | Send a CONFIG object containing at least `sqlQuery`. |
| 8078 | `EMPTY_JSON_ATTRIBUTE_FOUND` — `sqlQuery` was sent but is blank. | Send a non-empty `SELECT` statement. |
| 8079 | `ATTRIBUTE_NOT_PRESENT_IN_JSON_CONFIGURATION` — A mandatory attribute is missing — `sqlQuery` on the request itself, or `viewId` / `criteria` inside a `tableCriteriaList` entry. | The message names the attribute. |
| 8507 | `MORE_THAN_MAX_LENGTH` — `CONFIG` exceeds 200,000 characters, or `sqlQuery` exceeds 100,000. | Shorten the statement. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token carrying `ZohoAnalytics.data.read`. |
| 8547 | `ARRAY_SIZE_OUT_OF_RANGE` — `tableCriteriaList` exceeds 25 entries, or `selectedColumns` is empty or exceeds 300. | Stay within the documented sizes. |

---

## 2. Create Export Job using View ID (Asynchronous)

Creates an export job whose source is a saved view — including the view types the synchronous export refuses.

| Attribute | Value |
|-----------|-------|
| **URL** | `/restapi/v2/bulk/workspaces/<workspace-id>/views/<view-id>/data` |
| **HTTP Method** | `GET` |
| **OAuth Scope** | `ZohoAnalytics.data.read` |
| **Mandatory Header** | `ZANALYTICS-ORGID` |
| **CONFIG** | Optional — omitting it queues a CSV export of the whole view |
| **Success Status** | `200 OK` with a JSON body carrying `data.jobId` |

**Path parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `<workspace-id>` | Long | ID of the workspace that owns the view. |
| `<view-id>` | Long | ID of the view to export. Must belong to `<workspace-id>`. |

Unlike the synchronous export, **every** view type is accepted here: tables, tabular views, charts, pivots, summary views, query tables, dashboards, and views of live-connect workspaces, at any row count.

### CONFIG Parameters

In addition to the [Shared CONFIG Attributes](#shared-config-attributes):

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `criteria` | String | No | — | Filter expression selecting the rows to export. Omit to export every row. See [`criteria` syntax](#criteria-syntax). |
| `applyDefaultUF` | Boolean | No | `false` | Applies the view's saved default user filters before exporting. Meaningful for tabular views. |
| `generateTOC` | Boolean | No | `false` | Generates a table of contents. **Dashboards only**, and only when `responseFormat` is `pdf`. |
| `dashboardLayout` | Integer | No | `1` | Page layout for a dashboard PDF. `0` each report on its own page, `1` the layout as it appears in the dashboard. **Dashboards only.** |
| `zoomFactor` | Integer | No | `100` | Rendering zoom for a dashboard PDF, `1`–`100`. **Dashboards only**; outside the range fails with `8119`. |

### Image specific

Applicable when `responseFormat` is `image`. Valid **only for chart views**; any other view type fails with `8014`.

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `imageFormat` | String | No | `"png"` | `"png"`, `"jpg"`, or `"jpeg"` (case-insensitive). Anything else fails with `8017`. |
| `width` | Integer | No | `500` | Image width in pixels, `250`–`2000`. Outside fails with `7803`. |
| `height` | Integer | No | `400` | Image height in pixels, `200`–`2000`. Outside fails with `7803`. |
| `title` | Boolean | No | `false` | Whether the chart title is drawn on the image. |
| `description` | Boolean | No | `false` | Whether the chart description is drawn on the image. |
| `legend` | Boolean | No | `true` | Whether the chart legend is drawn on the image. |

### Sample Requests

**Case 1 — `criteria` alone: export only the rows that match a filter**

```http
GET /restapi/v2/bulk/workspaces/466206000000071000/views/466206000000072000/data HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

```json
{
  "responseFormat": "csv",
  "criteria": "\"SalesTable\".\"Region\"='East'"
}
```

Every other attribute takes its default: comma-separated, DOS line endings, header row present, hidden columns included, personal-data columns excluded.

**Case 2 — a fully configured CSV job with a callback**

```json
{
  "responseFormat": "csv",
  "selectedColumns": ["Region", "Product", "Sales"],
  "delimiter": 1,
  "recordDelimiter": 1,
  "quoted": 1,
  "includeHeader": true,
  "includeRowNums": true,
  "showHiddenCols": false,
  "showPersonalCols": false,
  "applyDefaultUF": true,
  "password": "Zoho@123",
  "callbackUrl": "https://example.com/hooks/za-export"
}
```

**Case 3 — a dashboard as a PDF**

This is the case the synchronous export cannot serve at all.

```json
{
  "responseFormat": "pdf",
  "dashboardLayout": 1,
  "generateTOC": true,
  "zoomFactor": 100,
  "paperSize": 2,
  "paperStyle": "Landscape",
  "showTitle": 0,
  "showDesc": 0,
  "topMargin": 0.25,
  "bottomMargin": 0.25,
  "exportLanguage": 0
}
```

**Case 4 — a chart as an image**

```json
{
  "responseFormat": "image",
  "imageFormat": "png",
  "width": 1200,
  "height": 800,
  "title": true,
  "description": false,
  "legend": true
}
```

### Sample Responses

**HTTP 200 OK — the job was created**

```json
{
  "status": "success",
  "summary": "Create bulk export job",
  "data": {
    "jobId": "466206000000091000"
  }
}
```

**HTTP 400 Bad Request — a dashboard requested in a format it cannot produce**

```json
{
  "status": "failure",
  "summary": "INVALID_VALUE_FOR_ATTRIBUTE",
  "data": {
    "errorCode": 8119,
    "errorMessage": "Invalid value csv given for the attribute responseFormat. Allowed values are PDF and HTML."
  }
}
```

**HTTP 403 Forbidden — the caller lacks Export permission**

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
| `summary` | String | `"Create bulk export job"` — identical to the SQL query export, so the summary does not distinguish the two APIs. |
| `data` | Object | Job identification. |
| `data.jobId` | String | ID of the created job, **as a string**. |

### Notes & Behaviour

| Behaviour | Detail |
|-----------|--------|
| **`CONFIG` is optional** | A bare call with no query string queues a CSV export of the whole view with default settings. |
| **No view type is off limits** | Dashboards, query tables, live-connect views, and tables of any size are all accepted. This is the reason to prefer this API over the synchronous export. |
| **A dashboard restricts the format** | Only `pdf` and `html` are valid for a dashboard; anything else fails with `8119`. |
| **A dashboard export may arrive as a ZIP** | An `html` dashboard export, and a `pdf` export of a **multi-tab** dashboard, are delivered as a ZIP archive containing one file per view or tab. Branch on the `Content-Type` returned by [Download Exported Data](#4-download-exported-data). |
| **Dashboard PDFs use different paper defaults** | `paperSize` accepts `0`–`4` with default `2` (Tabloid), instead of `0`–`5` with default `4` (A4). |
| **`selectedColumns` is honoured only for tables and tabular views** | For charts, pivots, summary views, and dashboards it is accepted and ignored — the view's own layout decides what is exported. |
| **`selectedColumns` overrides `showHiddenCols` for the columns it names** | A hidden column listed explicitly is exported even when `showHiddenCols` is `false`. It also sets the column order. |
| **Validation happens before the job exists** | A bad `criteria`, an unmatched `selectedColumns` name, an unreachable `callbackUrl`, or a permission failure all produce an error response and **no** `jobId`. |
| **Creation success is not export success** | Failures while producing the file surface as `jobCode` `1003` on [Get Export Job Details](#3-get-export-job-details), never on this response. |
| **`criteria` is not accepted by the SQL query variant** | And `sqlQuery` / `tableCriteriaList` are not accepted here. See [Filtering: `criteria` and `tableCriteriaList`](#filtering-criteria-and-tablecriterialist). |
| **Dependency chain:** | [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → `<view-id>`; [Get Columns](COLUMNS_API_DOC_INFO.md) → `selectedColumns` names → Create Export Job using View ID (Asynchronous) → `data.jobId` → [Get Export Job Details](#3-get-export-job-details) → [Download Exported Data](#4-download-exported-data). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7104 | `META_OBJECT_NOT_PRESENT` — The view does not exist. | Verify `<view-id>` with [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list). |
| 7301 | `SECURITY_NOT_PERMITTED` — The caller lacks Export permission on the view, or the view does not belong to `<workspace-id>`. | Ensure the caller is an Account Admin, Organization Admin, Workspace Admin, or View Owner, or holds Export permission on the view. |
| 7327 | `FILTER_CRITERIA_INVALID` — `criteria` parsed but could not be converted into a query. | Simplify the expression and check operator and value types. |
| 7330 | `UNKNOWN_COLUMN_IN_FILTERCRITERIA` — A column named in `criteria` does not exist in the view. | Check the name against [Get Columns](COLUMNS_API_DOC_INFO.md). |
| 7331 | `FILTERCRITERIA_PARSE_ERROR` — `criteria` is syntactically malformed. | Check quoting: double quotes around column names, single quotes around string literals. |
| 7332 | `UNKNOWN_TABLE_IN_FILTERCRITERIA` — A table qualifier in `criteria` is not part of the view. | Qualify columns only with tables the view uses. |
| 7333 | `INVALID_GROUP_FUNC_USE_IN_FILTERCRITERIA` — An aggregate function was used in `criteria`. | Filter on raw column values instead. |
| 7543 | `ONLY_BASETABLE_COL_IN_TABULAR_FILTERCRITERIA` — `criteria` on a tabular view referenced a column outside its base table. | Filter using only the base table's own columns. |
| 7565 | `UNVERIFIED_EMAIL` — The calling user's primary email address is not verified. | Verify the account's primary email address and retry. |
| 7801 | `MARGIN_VALUE_EXCEEDS` — A PDF margin is outside `0`–`1` inches. | Send a value between `0` and `1`. |
| 7803 | `INVALID_DIMENSION` — `width` or `height` is outside the permitted image range. | Use `width` 250–2000 and `height` 200–2000. |
| 7824 | `EXPORT_REQ_BLOCKED` — Export has been blocked for this workspace. | Contact Zoho Analytics support using the address in the error message. |
| 7827 | `EXP_PDF_RECORD_LIMIT` — The PDF exceeds 1,000,000 cells. | Narrow the export with `criteria` or `selectedColumns`. |
| 8001 | `INVALID_RESP_FORMAT` — `responseFormat` is not a supported value. | Send one of `csv`, `json`, `xml`, `xls`, `pdf`, `html`, `image`. |
| 8014 | `API_IMAGE_RESPONSE_NOT_POSSIBLE` — `image` was requested for a view that is not a chart. | Export charts as images; use `pdf` or `html` otherwise. |
| 8015 | `API_EXPORT_COLUMN_NOT_PRESENT` — A name in `selectedColumns` does not match any column in the view. | Check the display names with [Get Columns](COLUMNS_API_DOC_INFO.md). |
| 8017 | `INVALID_IMAGE_FORMAT` — `imageFormat` is not `png`, `jpg`, or `jpeg`. | Send one of the three supported values. |
| 8088 | `SECURITY_CONTROLS_FEATURE_DISABLED` — Export is disabled for the organization. | Ask an Organization Admin to re-enable export. |
| 8119 | `INVALID_VALUE_FOR_ATTRIBUTE` — A numeric or enumerated attribute is outside its permitted set, or a dashboard was requested in a format other than PDF or HTML. | Correct the value; see [Appendix E](#appendix-e--enum-reference). |
| 8125 | `CALLBACKURL_NOT_VALID` — `callbackUrl` is malformed. | Send a well-formed absolute `http`/`https` URL. |
| 8126 | `CALLBACKURL_CONNECTION_ERROR` — `callbackUrl` could not be reached during validation. | Make the endpoint publicly reachable before creating the job. |
| 8127 | `CALLBACKURL_RESTRICTED` — `callbackUrl` resolves to a private or internal address. | Use a publicly routable host. |
| 8128 | `INTERNAL_ERROR_ON_INITIATING_EXPORT` — The job could not be queued. | Retry; if it persists, contact support. |
| 8132 | `ASYNC_EXPORT_LIMIT_EXCEEDED` — 5 export jobs are already queued or running for the organization. | Wait for an in-flight job to finish, then retry. |
| 8188 | `EXPORT_INVALID_PASSWORD` — `password` is blank or shorter than 6 characters. | Send 6–256 characters. |
| 8241 | `SYSTEM_TAG_DATA_WARNING_V2_VALIDATION_CONFIRMATION` — The view carries a restricted DATA_WARNING system tag. | Review the warning, then resend with `"validateSystemTags": false`. |
| 8507 | `MORE_THAN_MAX_LENGTH` — `CONFIG` exceeds 100,000 characters. | Shorten `criteria` or `selectedColumns`. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token carrying `ZohoAnalytics.data.read`. |
| 8547 | `ARRAY_SIZE_OUT_OF_RANGE` — `selectedColumns` is empty or holds more than 300 entries. | Send between 1 and 300 column names, or omit the attribute. |

---

## 3. Get Export Job Details

Reports the progress of an export job, and once it has finished, where to collect the file.

| Attribute | Value |
|-----------|-------|
| **URL** | `/restapi/v2/bulk/workspaces/<workspace-id>/exportjobs/<job-id>` |
| **HTTP Method** | `GET` |
| **OAuth Scope** | `ZohoAnalytics.data.read` |
| **Mandatory Header** | `ZANALYTICS-ORGID` |
| **CONFIG** | Not applicable — this API takes no CONFIG attributes |
| **Success Status** | `200 OK` with a JSON body |

**Path parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `<workspace-id>` | Long | ID of the workspace the job was created against. |
| `<job-id>` | Long | The `data.jobId` returned by either creation API. |

### Sample Requests

**Case 1 — poll a job**

```http
GET /restapi/v2/bulk/workspaces/466206000000071000/exportjobs/466206000000091000 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

There is nothing else to send. The same request is repeated until `jobCode` becomes terminal.

### Sample Responses

**HTTP 200 OK — still queued**

```json
{
  "status": "success",
  "summary": "Fetch export job info",
  "data": {
    "jobId": "466206000000091000",
    "jobCode": "1001",
    "jobStatus": "JOB NOT INITIATED"
  }
}
```

**HTTP 200 OK — running**

```json
{
  "status": "success",
  "summary": "Fetch export job info",
  "data": {
    "jobId": "466206000000091000",
    "jobCode": "1002",
    "jobStatus": "JOB IN PROGRESS"
  }
}
```

**HTTP 200 OK — finished, file ready**

```json
{
  "status": "success",
  "summary": "Fetch export job info",
  "data": {
    "jobId": "466206000000091000",
    "jobCode": "1004",
    "jobStatus": "JOB COMPLETED",
    "downloadUrl": "https://analyticsapi.zoho.com/restapi/v2/bulk/workspaces/466206000000071000/exportjobs/466206000000091000/data",
    "expiryTime": "1789171200000"
  }
}
```

**HTTP 200 OK — the job failed**

```json
{
  "status": "success",
  "summary": "Fetch export job info",
  "data": {
    "jobId": "466206000000091000",
    "jobCode": "1003",
    "jobStatus": "ERROR OCCURRED"
  }
}
```

Note the HTTP status is still `200` — the *request* succeeded, the *job* did not.

**HTTP 403 Forbidden — polling someone else's job**

```json
{
  "status": "failure",
  "summary": "EXPORT_JOB_ACCESS_DENIED",
  "data": {
    "errorCode": 8124,
    "errorMessage": "You Jane Doe do not have permission to access the job."
  }
}
```

**HTTP 404 Not Found — no such job**

```json
{
  "status": "failure",
  "summary": "EXPORT_JOB_NOT_FOUND",
  "data": {
    "errorCode": 8120,
    "errorMessage": "Job 466206000000091000 not found."
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | String | `"success"` whenever the request itself succeeded — including when the job has failed. |
| `summary` | String | `"Fetch export job info"`. |
| `data` | Object | Job state. |
| `data.jobId` | String | Echo of the requested job ID. |
| `data.jobCode` | String | Current state as a numeric code **in a string**: `"1001"`, `"1002"`, `"1003"`, `"1004"`, or `"1005"`. See [Job Codes and Polling](#job-codes-and-polling). |
| `data.jobStatus` | String | Human-readable form of `jobCode`: `JOB NOT INITIATED`, `JOB IN PROGRESS`, `ERROR OCCURRED`, `JOB COMPLETED`, or `JOB NOT FOUND`. Intended for display; branch on `jobCode`. |
| `data.downloadUrl` | String | Fully-qualified URL of [Download Exported Data](#4-download-exported-data) for this job. **Present only when `jobCode` is `"1004"`.** |
| `data.expiryTime` | String | Epoch time in **milliseconds**, as a string, at which the job and its file are removed. Set to 72 hours after the job was **created**. **Present only when `jobCode` is `"1004"`.** |

### Notes & Behaviour

| Behaviour | Detail |
|-----------|--------|
| **A failed job is still a successful request** | `jobCode` `1003` comes back with HTTP `200` and `status: "success"`. Never infer job health from the HTTP status. |
| **`1005` is returned, not raised** | If a job has expired or its ID was never valid *but the ID is well-formed*, the response is `200` with `jobCode` `1005`. A structurally unresolvable job produces `8120` instead. Handle both. |
| **`downloadUrl` and `expiryTime` are conditional** | They exist only alongside `jobCode` `1004`. Test for the keys. |
| **`expiryTime` is anchored to creation, not completion** | A job created at 09:00 and finishing at 09:40 still expires 72 hours after 09:00. A long-running job therefore leaves a shorter collection window. |
| **This API does not distinguish the two creation APIs** | A view export and a SQL query export produce identical response shapes. Track which is which yourself. |
| **It reveals nothing about the export content** | No row count, no file size, no format. If you need those, record the CONFIG you sent. |
| **Polling is cheap but not free** | Poll every few seconds rather than in a tight loop; use `callbackUrl` when you control an endpoint. |
| **Only the creator may poll** | Job ownership is by user, not by role — see [Permission Model](#permission-model). |
| **Dependency chain:** | [Create Export Job using SQL Query (Asynchronous)](#1-create-export-job-using-sql-query-asynchronous) or [Create Export Job using View ID (Asynchronous)](#2-create-export-job-using-view-id-asynchronous) → `data.jobId` → Get Export Job Details → `data.downloadUrl` → [Download Exported Data](#4-download-exported-data). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 8120 | `EXPORT_JOB_NOT_FOUND` — No export job exists for the given ID (HTTP 404). | Verify the `jobId` returned by the create call, and that the job has not passed its 72-hour retention. |
| 8124 | `EXPORT_JOB_ACCESS_DENIED` — The caller did not create this job (HTTP 403). | Poll with the same user that created the job. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token carrying `ZohoAnalytics.data.read`. |

---

## 4. Download Exported Data

Returns the exported file produced by a completed export job.

| Attribute | Value |
|-----------|-------|
| **URL** | `/restapi/v2/bulk/workspaces/<workspace-id>/exportjobs/<job-id>/data` |
| **HTTP Method** | `GET` |
| **OAuth Scope** | `ZohoAnalytics.data.read` |
| **Mandatory Header** | `ZANALYTICS-ORGID` |
| **CONFIG** | Not applicable — this API takes no CONFIG attributes |
| **Success Status** | `200 OK`, body is the exported file |
| **Content-Type** | Varies with the job's `responseFormat` — see [Exported File Structure by Format](#exported-file-structure-by-format) |

**Path parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `<workspace-id>` | Long | ID of the workspace the job was created against. |
| `<job-id>` | Long | The `data.jobId` returned by either creation API. |

This endpoint is exactly what `data.downloadUrl` from [Get Export Job Details](#3-get-export-job-details) points at.

### Sample Requests

**Case 1 — collect the file**

```http
GET /restapi/v2/bulk/workspaces/466206000000071000/exportjobs/466206000000091000/data HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

### Sample Responses

**HTTP 200 OK — a CSV job**

```
Content-Type: text/csv

Region,Product,Sales
East,Laptop,145000
East,Monitor,38200
```

**HTTP 200 OK — a JSON job with the default `keyValueFormat: true`**

```json
{
  "data": [
    {
      "Region": "East",
      "Product": "Laptop",
      "Sales": "145000"
    },
    {
      "Region": "East",
      "Product": "Monitor",
      "Sales": "38200"
    }
  ]
}
```

**HTTP 200 OK — a binary or archived job**

```
Content-Type: application/pdf

%PDF-1.4
… binary …
```

```
Content-Type: application/zip

PK…
… binary …
```

**HTTP 400 Bad Request — the job has not started yet**

```json
{
  "status": "failure",
  "summary": "EXPORT_JOB_NOT_INITIATED",
  "data": {
    "errorCode": 8121,
    "errorMessage": "Job 466206000000091000 not initiated."
  }
}
```

**HTTP 400 Bad Request — the job is still running**

```json
{
  "status": "failure",
  "summary": "EXPORT_JOB_NOT_COMPLETED",
  "data": {
    "errorCode": 8122,
    "errorMessage": "Job 466206000000091000 not completed."
  }
}
```

**HTTP 400 Bad Request — the job failed**

```json
{
  "status": "failure",
  "summary": "EXPORT_JOB_ERROR_OCCURRED",
  "data": {
    "errorCode": 8123,
    "errorMessage": "An internal error occurred while processing the job 466206000000091000. Kindly contact our support team."
  }
}
```

### Exported File Structure by Format

The file returned here is byte-for-byte what the [synchronous export](SYNC_DATA_EXPORT_API_DOC_INFO.md#response-structure-by-format) would have produced for the same CONFIG.

| Job `responseFormat` | `Content-Type` | Body |
|----------------------|----------------|------|
| `csv` | `text/csv` | Delimited text. Optional header row, optional leading `Row Number` field. |
| `json` (`keyValueFormat: true`) | `application/json` | `{"data":[ {…}, … ]}` — one object per row, keyed by column display name. |
| `json` (`keyValueFormat: false`) | `application/json` | `{"response":{"uri":…,"action":"EXPORT","result":{"column_order":[…],"rows":[[…]]}}}` |
| `xml` (`keyValueFormat: false`) | `application/xml` | `<?xml …?><response …><result><rows><row><column name="…">…</column></row></rows></result></response>` |
| `xml` (`keyValueFormat: true`) | `application/xml` | `<result><rows><row><ColumnName>…</ColumnName></row></rows></result>` — no XML declaration and no `<response>` wrapper. |
| `xls` | `application/vnd.ms-excel` | Binary workbook. |
| `pdf` | `application/pdf` | Binary PDF. |
| `html` | `text/html` | An HTML fragment containing the rendered table. |
| `image` | `image/png` or `image/jpeg` | Binary image. |
| **any format with `password`** | `application/zip`, or the native type for `xls` and `pdf` | See [Password Protection](#password-protection). |
| **a dashboard as `html`** | `application/zip` | One HTML file per view in the dashboard. |
| **a multi-tab dashboard as `pdf`** | `application/zip` | One PDF per tab. |

### Response Fields

The success body is a file, not a JSON envelope, so structured fields exist only for the JSON and XML formats. They are identical to the synchronous export's — see [Response Fields](SYNC_DATA_EXPORT_API_DOC_INFO.md#response-fields) there for the full field tables of all four shapes.

**Response headers**

| Header | Description |
|--------|-------------|
| `Content-Type` | The only header that describes the payload. Derived from the job's `responseFormat`, or `application/zip` when the file was archived — see [Exported File Structure by Format](#exported-file-structure-by-format). |
| `Content-Disposition` | **Not sent.** No filename is suggested, so the client must name the downloaded file itself. |

### Notes & Behaviour

| Behaviour | Detail |
|-----------|--------|
| **The response body is the file, not a wrapper** | A successful call returns no `status` / `summary` / `data` envelope. Only **failures** use the JSON envelope, so branch on the HTTP status before parsing. |
| **It never waits** | Calling before the job has finished is an error, not a blocking read: `8121` while queued, `8122` while running, `8123` if the job failed. Poll [Get Export Job Details](#3-get-export-job-details) first. |
| **Each error code names a distinct job state** | `8121` queued, `8122` running, `8123` failed, `8120` absent or expired, `8124` not yours. They map one-to-one onto `jobCode`, so the download error alone is enough to decide whether to retry. |
| **The file can be downloaded more than once** | Within the 72-hour window there is no single-use restriction and no state change on download. |
| **After 72 hours the job is gone** | The record and the file are removed together, and this endpoint then fails with `8120`. |
| **No `Content-Disposition`, no filename** | Derive one from the view or query and the format, and remember that a password-protected `csv` arrives as a ZIP. |
| **Only the creator may download** | Even an Account Admin gets `8124` for another user's job — see [Permission Model](#permission-model). |
| **`downloadUrl` and this endpoint are the same thing** | Following the URL from [Get Export Job Details](#3-get-export-job-details) and constructing the path yourself are equivalent. |
| **Dependency chain:** | [Get Export Job Details](#3-get-export-job-details) → `jobCode` `1004` → Download Exported Data → the file. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 8120 | `EXPORT_JOB_NOT_FOUND` — No export job exists for the given ID, or it has passed its 72-hour retention (HTTP 404). | Verify the `jobId`; if it has expired, create a new job. |
| 8121 | `EXPORT_JOB_NOT_INITIATED` — The job is queued but has not started (`jobCode` `1001`). | Poll [Get Export Job Details](#3-get-export-job-details) until `jobCode` is `1004`. |
| 8122 | `EXPORT_JOB_NOT_COMPLETED` — The job is still running (`jobCode` `1002`). | Poll [Get Export Job Details](#3-get-export-job-details) until `jobCode` is `1004`. |
| 8123 | `EXPORT_JOB_ERROR_OCCURRED` — The job failed (`jobCode` `1003`). | Nothing to download. Create a new job; if the failure repeats, contact support. |
| 8124 | `EXPORT_JOB_ACCESS_DENIED` — The caller did not create this job (HTTP 403). | Download with the same user that created the job. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token carrying `ZohoAnalytics.data.read`. |

---

## Appendix A – Common HTTP Headers

| Header | Value | Required | Description |
|--------|-------|----------|-------------|
| `Authorization` | `Zoho-oauthtoken <oauth-token>` | **Mandatory** | OAuth 2.0 access token of the calling user, carrying `ZohoAnalytics.data.read`. |
| `ZANALYTICS-ORGID` | Organization ID string | **Mandatory** | Organization ID of the workspace. Required by all four APIs, including the two job APIs. |

> **`ZANALYTICS-DEST-ORGID` is not used by any of these APIs.** That header applies only to cross-organization copy operations (Copy Workspace, [Copy Views](VIEW_OPERATIONS_API_DOC_INFO.md#2-copy-views), Copy Formulas), which target a destination organization.

None of the four APIs has a request body — all are `GET`, and the two creation APIs carry `CONFIG` in the query string:

```http
GET /restapi/v2/bulk/workspaces/466206000000071000/views/466206000000072000/data?CONFIG=%7B%22responseFormat%22%3A%22csv%22%2C%22criteria%22%3A%22%5C%22Region%5C%22%3D%27East%27%22%7D HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

The decoded `CONFIG` above is `{"responseFormat":"csv","criteria":"\"Region\"='East'"}`.

---

## Appendix B – OAuth Scope Summary

| API | HTTP Method | Scope |
|-----|-------------|-------|
| Create Export Job using SQL Query (Asynchronous) | GET | `ZohoAnalytics.data.read` |
| Create Export Job using View ID (Asynchronous) | GET | `ZohoAnalytics.data.read` |
| Get Export Job Details | GET | `ZohoAnalytics.data.read` |
| Download Exported Data | GET | `ZohoAnalytics.data.read` |

> All four share the **same** scope. Creating a job is a `GET` and reads no less and no more than the export itself, so a single `ZohoAnalytics.data.read` token drives the whole pipeline. `ZohoAnalytics.data.create` — the import scope — will not authorise any of them.

---

## Appendix C – API-Specific Notes and Behaviours

### Create Export Job using SQL Query (Asynchronous)

- **It is the only way to export a result set that no saved view represents.** Joins, unions, and aggregations can be expressed inline instead of being materialised as a query table first.
- **Permission is evaluated per participating table.** A `7301` here is about one table inside the statement, so the diagnosis is "which table" rather than "which user". Resolve the tables the query touches before blaming the token.
- **The 800,000-row cap is silent.** A statement that would return more is truncated and the job still reports `1004`. If completeness matters, constrain the statement so the result is provably under the cap, or count first.
- **`tableCriteriaList` is not a substitute for `WHERE`.** It exists to apply per-table restrictions on top of the statement. For ordinary row selection the `WHERE` clause is simpler and has no 25-entry ceiling.
- **`CONFIG` is mandatory, unlike its sibling.** There is no default source to fall back on.
- **`image` is structurally impossible.** A query result is a sheet, so `8014` is not a bug.
- **Dependency chain:** any SQL `SELECT` over the workspace's tables → Create Export Job using SQL Query (Asynchronous) → `data.jobId` → [Get Export Job Details](#3-get-export-job-details) → [Download Exported Data](#4-download-exported-data).

### Create Export Job using View ID (Asynchronous)

- **This is the answer to every `8133` from the synchronous export.** Dashboards, query tables, live-connect views, and large tables are all exportable here. When the synchronous call refuses, switch endpoints rather than trying different formats.
- **Dashboards behave differently from every other view type.** The format is restricted to `pdf` and `html`, the paper defaults change, and three extra attributes (`generateTOC`, `dashboardLayout`, `zoomFactor`) become meaningful. They do nothing for any other view type.
- **A dashboard export may not be a single file.** HTML dashboards and multi-tab dashboard PDFs come back as ZIP archives. Code that assumes one file per job will break on exactly the view type this API exists to serve.
- **`CONFIG` is optional.** A bare call queues a full CSV export, which makes this the shortest possible way to schedule a whole-view dump.
- **`selectedColumns` silently does nothing for charts, pivots, summary views, and dashboards.** Only tables and tabular views honour it.
- **`criteria` is validated up front.** A bad expression costs you an error response, not a wasted job.
- **Page setup is shared with Email Schedules.** `paperSize`, `paperStyle`, the four margins, `showTitle`, `showDesc`, `exportLanguage`, and the six header/footer slots use the same value sets as [Create Email Schedule](EMAIL_SCHEDULES_API_DOC_INFO.md#2-create-email-schedule).
- **Dependency chain:** [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) + [Get Columns](COLUMNS_API_DOC_INFO.md) → Create Export Job using View ID (Asynchronous) → `data.jobId` → [Get Export Job Details](#3-get-export-job-details) → [Download Exported Data](#4-download-exported-data).

### Get Export Job Details

- **HTTP status and job status are independent.** A failed job is reported as `200` / `success` / `jobCode` `1003`. An integration that only inspects HTTP codes will treat a failed export as a success and then get `8123` from the download.
- **Two terminal codes look like progress and are not.** `1003` and `1005` never change. Polling either forever is the most common mistake with this pipeline.
- **`expiryTime` counts from creation.** The window shrinks while the job runs, so a slow job leaves less time to collect. Read `expiryTime` rather than adding 72 hours to the moment you saw `1004`.
- **`expiryTime` is epoch milliseconds in a **string**.** So is `jobId`, and so is `jobCode`. Nothing in `data` is a JSON number.
- **The response says nothing about the export itself.** No format, no row count, no size. Keep your own record of what the job was for.
- **Prefer `callbackUrl` when you can host an endpoint.** It carries the same fields, removes the poll entirely, and fires on failure too.
- **Dependency chain:** either creation API → `data.jobId` → Get Export Job Details → `data.downloadUrl` → [Download Exported Data](#4-download-exported-data).

### Download Exported Data

- **It is the second API in this suite whose success response is not JSON.** The other is [Export Data from a View](SYNC_DATA_EXPORT_API_DOC_INFO.md#1-export-data-from-a-view). Check the HTTP status first, parse JSON only on failure, and read `Content-Type` to handle the success body.
- **Its error codes are a state machine, not noise.** `8121`, `8122`, `8123`, `8120`, and `8124` each identify one job state precisely, which means a client can drive the whole pipeline from download errors alone if it prefers that to polling.
- **No `Content-Disposition` header.** There is no server-suggested filename, and the extension is not derivable from the URL. Record the `responseFormat` you requested.
- **`application/zip` has three separate causes** — a password, an HTML dashboard, or a multi-tab dashboard PDF. Do not treat ZIP as evidence that a password was set.
- **Downloads are idempotent within the window.** Re-downloading is safe and does not consume the job.
- **Dependency chain:** [Get Export Job Details](#3-get-export-job-details) → `jobCode` `1004` → Download Exported Data → the file.

---

## Appendix D – General Response Payload Notes

| Field / Behaviour | Detail |
|-------------------|--------|
| **Three APIs return JSON, one returns a file** | The two creation APIs and [Get Export Job Details](#3-get-export-job-details) return the standard envelope. [Download Exported Data](#4-download-exported-data) returns the exported file itself. |
| **No API in this document returns 204** | All four answer `200` on success. |
| **Failure responses share one shape** | `{"status": "failure", "summary": "<ERROR_NAME>", "data": {"errorCode": <n>, "errorMessage": "<text>"}}`. `summary` on failure is the error's symbolic name (for example `EXPORT_JOB_NOT_COMPLETED`), not a localised sentence. |
| **Both creation APIs share one success `summary`** | `"Create bulk export job"`. It does not distinguish the view export from the SQL query export. |
| **`Get Export Job Details` always has `summary` `"Fetch export job info"`** | Including when the job it reports on has failed. |
| **Every value inside `data` is a string** | `jobId`, `jobCode`, `jobStatus`, `downloadUrl`, and `expiryTime` are all JSON strings, never numbers. |
| **`downloadUrl` and `expiryTime` are conditional** | Present only when `jobCode` is `"1004"`. Test for the keys. |
| **`downloadUrl` is absolute and region-aware** | It is built from the server URL serving the request, so it already points at the correct data centre. Prefer it over hand-assembling the path. |
| **A `200` from a creation API does not mean the export worked** | It means the job was accepted. The outcome is only visible through `jobCode`. |
| **All exported cell values are strings** | In the JSON and XML formats, numeric, currency, percentage, and date columns are exported as formatted strings following the column's display settings. |
| **The downloaded body is not compressed in transit** | No `Content-Encoding` is applied. A `application/zip` body is an archive by design, not a transport encoding. |
| **An empty export is still a completed job** | A `criteria` matching nothing yields `jobCode` `1004` and a header-only CSV, `{"data":[]}`, or an empty `<rows/>`. It is not an error. |

---

## Appendix E – Enum Reference

Every enumerated attribute of the two creation APIs in one place. An out-of-range value fails with `8119` unless noted otherwise.

**`responseFormat`** — default `csv`; invalid values fail with `8001`

| Value | Output | Available on |
|-------|--------|--------------|
| `csv` | Delimited text file | Both creation APIs |
| `json` | JSON document | Both |
| `xml` | XML document | Both |
| `xls` | Excel workbook | Both |
| `pdf` | PDF document | Both |
| `html` | HTML fragment | Both |
| `image` | PNG or JPEG image | View export only, **chart views only** |

**`delimiter`** — CSV field separator, default `0`

| Value | Separator |
|-------|-----------|
| `0` | Comma |
| `1` | Tab |
| `2` | Semicolon |
| `3` | Space |
| `4` | Pipe |

**`recordDelimiter`** — CSV line ending, default `0`

| Value | Line ending |
|-------|-------------|
| `0` | DOS (`\r\n`) |
| `1` | UNIX (`\n`) |
| `2` | MAC (`\r`) |

**`quoted`** — CSV text qualifier, no default

| Value | Qualifier |
|-------|-----------|
| `0` | Single quote |
| `1` | Double quote |

**`paperSize`** — PDF page size, default `4` (default `2` for a dashboard)

| Value | Page size |
|-------|-----------|
| `0` | Letter |
| `1` | Legal |
| `2` | Tabloid |
| `3` | A3 |
| `4` | A4 |
| `5` | Auto-fit — width grows with the number of visible columns. **Not available for a dashboard.** |

**`paperStyle`** — PDF orientation, default `Portrait`

| Value | Orientation |
|-------|-------------|
| `Portrait` | Upright |
| `Landscape` | Sideways |

**`showTitle`, `showDesc`** (PDF) and **`includeTitle`, `includeDesc`** (HTML) — default `0`

| Value | Placement |
|-------|-----------|
| `0` | Top |
| `1` | Bottom |
| `2` | Do not include |

**`columnWidthRatio`** — default `1` for PDF, `2` for HTML

| Value | Column sizing |
|-------|---------------|
| `0` | Proportional to the widths set in the view |
| `1` | Sized to content |
| `2` | All columns equal |

**`exportLanguage`** — PDF font set, default `0`

| Value | Font set |
|-------|----------|
| `0` | English |
| `1` | Chinese |
| `2` | Japanese |
| `3` | European |
| `4` | Korean |

**`leftHeader`, `centerHeader`, `rightHeader`, `leftFooter`, `centerFooter`, `rightFooter`** — PDF page-header and page-footer slots

| Value | Content |
|-------|---------|
| `0` | Blank |
| `1` | View title |
| `2` | Export date |
| `3` | Page number |
| `4` | Page number with total |
| `5` | Custom text from the matching `…Text` attribute |
| `6` | Logo |

Defaults: `leftHeader` `1`, `centerHeader` `0`, `rightHeader` `2`, `leftFooter` `0`, `centerFooter` `3`, `rightFooter` `0`.

**`dashboardLayout`** — dashboard PDF layout, default `1`

| Value | Layout |
|-------|--------|
| `0` | Each report on its own page |
| `1` | The layout as it appears in the dashboard |

**`imageFormat`** — default `png`; invalid values fail with `8017`

| Value | Image type |
|-------|------------|
| `png` | PNG |
| `jpg` | JPEG |
| `jpeg` | JPEG |

**`jobCode`** — response value of [Get Export Job Details](#3-get-export-job-details)

| Value | `jobStatus` | Terminal |
|-------|-------------|----------|
| `1001` | `JOB NOT INITIATED` | No |
| `1002` | `JOB IN PROGRESS` | No |
| `1003` | `ERROR OCCURRED` | Yes |
| `1004` | `JOB COMPLETED` | Yes |
| `1005` | `JOB NOT FOUND` | Yes |

---

## Appendix F – CONFIG Attribute Availability by API

`✓` accepted, `–` not accepted by that API.

| Attribute | Create Export Job using SQL Query | Create Export Job using View ID |
|-----------|:---------------------------------:|:-------------------------------:|
| `sqlQuery` | ✓ **mandatory** | – |
| `tableCriteriaList` | ✓ | – |
| `criteria` | – | ✓ |
| `applyDefaultUF` | – | ✓ |
| `generateTOC`, `dashboardLayout`, `zoomFactor` | – | ✓ (dashboards only) |
| `imageFormat`, `width`, `height`, `title`, `description`, `legend` | – | ✓ (chart views only) |
| `responseFormat` | ✓ | ✓ |
| `password` | ✓ | ✓ |
| `selectedColumns` | ✓ | ✓ |
| `showHiddenCols` | ✓ | ✓ |
| `showPersonalCols` | ✓ | ✓ |
| `includeHeader` | ✓ | ✓ |
| `includeRowNums` / `includeRowIds` | ✓ | ✓ |
| `callbackUrl` | ✓ | ✓ |
| `validateSystemTags` | ✓ | ✓ |
| `delimiter`, `recordDelimiter`, `quoted` | ✓ | ✓ |
| `keyValueFormat` | ✓ | ✓ |
| `paperSize`, `paperStyle`, margins, `showTitle`, `showDesc` | ✓ | ✓ |
| `columnWidthRatio`, `exportLanguage` | ✓ | ✓ |
| header / footer slots and their `…Text` | ✓ | ✓ |
| `includeTitle`, `includeDesc` | ✓ | ✓ |

[Get Export Job Details](#3-get-export-job-details) and [Download Exported Data](#4-download-exported-data) take no CONFIG attributes at all.
