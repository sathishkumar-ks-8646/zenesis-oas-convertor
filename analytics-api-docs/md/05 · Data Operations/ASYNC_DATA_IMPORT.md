# Zoho Analytics V2 REST API — Asynchronous & Batch Data Import

This document covers the five **bulk** data-import REST APIs of Zoho Analytics — the APIs that hand a large payload to the server, get back a **job ID**, and let you track that job to completion.

Unlike the [synchronous import APIs](SYNC_DATA_IMPORT_API_DOC_INFO.md), none of these APIs returns the import result directly. Every one of them returns a job reference, and the outcome is retrieved later through [Get Import Job Details](#5-get-import-job-details) or delivered to a [callback URL](#the-callbackurl-attribute).

## The two families

The five APIs fall into two families that solve different problems, plus one shared monitoring API.

| | **Asynchronous Import** | **Batch Import** |
|---|---|---|
| **APIs** | [Create Import Job for a New Table (Asynchronous)](#1-create-import-job-for-a-new-table-asynchronous)<br>[Create Import Job for an Existing Table (Asynchronous)](#2-create-import-job-for-an-existing-table-asynchronous) | [Batch Import Data into New Table](#3-batch-import-data-into-new-table)<br>[Batch Import Data into Existing Table](#4-batch-import-data-into-existing-table) |
| **Calls per import** | **One** — the whole file in a single request | **Many** — one request per batch, all sharing one job |
| **Data size** | Up to 100 MB in total | Unlimited in total; **each batch** up to 100 MB |
| **File formats** | CSV, JSON, XML, Excel, Parquet, Geometry | **CSV only** |
| **Returns** | `jobId` | `batchKey` **and** `jobId` |
| **Use when** | The file fits in one request | The dataset is too large for one request and must be split |
| **Monitored by** | [Get Import Job Details](#5-get-import-job-details) | [Get Import Job Details](#5-get-import-job-details) |

> **Choosing between them.** If your file is under 100 MB, use the asynchronous import — it is one call. Reach for batch import only when the dataset genuinely will not fit, because it requires you to split the file, carry a `batchKey` across calls, and explicitly close the job.

> Notes that apply to all five APIs:
> - All are authenticated via OAuth (`Authorization: Zoho-oauthtoken <token>`) and use the **`data`** scope family — see [Appendix B](#appendix-b--oauth-scope-summary).
> - All require the `ZANALYTICS-ORGID` header.
> - All are **available in Client Portal / White Label contexts**.
> - The four import APIs send the payload as a `FILE` part in a `multipart/form-data` request, together with a `CONFIG` part. They do **not** accept a `DATA` parameter — pasted data is a synchronous-import feature only.
> - All five return **HTTP 200** with a JSON body. None returns 204.
> - None accepts a `criteria` attribute. Which rows are loaded is decided by the file's contents and by `skipTop`.

---

## Index

| # | API Name | Method | URL |
|---|----------|--------|-----|
| 1 | [Create Import Job for a New Table (Asynchronous)](#1-create-import-job-for-a-new-table-asynchronous) | POST | `/restapi/v2/bulk/workspaces/<workspace-id>/data` |
| 2 | [Create Import Job for an Existing Table (Asynchronous)](#2-create-import-job-for-an-existing-table-asynchronous) | POST | `/restapi/v2/bulk/workspaces/<workspace-id>/views/<view-id>/data` |
| 3 | [Batch Import Data into New Table](#3-batch-import-data-into-new-table) | POST | `/restapi/v2/bulk/workspaces/<workspace-id>/data/batch` |
| 4 | [Batch Import Data into Existing Table](#4-batch-import-data-into-existing-table) | POST | `/restapi/v2/bulk/workspaces/<workspace-id>/views/<view-id>/data/batch` |
| 5 | [Get Import Job Details](#5-get-import-job-details) | GET | `/restapi/v2/bulk/workspaces/<workspace-id>/importjobs/<job-id>` |

---

## Limitations

These limits apply to every API in this document. They are hard limits — a request that exceeds one is rejected, not queued.

| Limitation | Value | Enforced by |
|------------|-------|-------------|
| **Maximum file size** | **100 MB** per uploaded file. For batch import this is **per batch**, not per job. | Rejected at upload |
| **Simultaneous import jobs** | **5** per organization. A job counts against the limit while it is queued or running. | `8134` |
| **Batches per batch-import job** | **100** | `7336` |
| **Import job summary retention** | **1 hour** after the job completes or fails. After that the summary is gone and [Get Import Job Details](#5-get-import-job-details) can no longer return it. | `expiryTime` in the response |
| **Batch import file format** | **CSV only.** JSON, XML, Excel, Parquet, and Geometry are not supported by the batch APIs. | — |
| **Batch import ordering** | Batches are committed in the order they are received. A batch cannot be re-sent or reordered once accepted. | `7337`, `7338` |
| **Job visibility** | An import job can be queried **only by the user who created it**. | `8138` |

> **Poll, then persist.** Because the summary lives for one hour, an integration that needs a durable record of what was imported must read [Get Import Job Details](#5-get-import-job-details) while the job is fresh and store the result itself.

---

## Workflow of the Asynchronous Import API

### 1. Create the import job

Call [Create Import Job for a New Table (Asynchronous)](#1-create-import-job-for-a-new-table-asynchronous) or [Create Import Job for an Existing Table (Asynchronous)](#2-create-import-job-for-an-existing-table-asynchronous). A unique **`jobId`** comes back in the response and is the reference for everything that follows.

### 2. Check the job status

Call [Get Import Job Details](#5-get-import-job-details) with that `jobId`, periodically — **every 10 seconds** is a reasonable cadence. The response carries a **`jobCode`** describing the current state.

### JOBCODE and status messages

| JOBCODE | Status message | Description |
|---------|----------------|-------------|
| **1001** | `JOB NOT INITIATED` | Job creation acknowledged but not yet started. Retry after a short delay. |
| **1002** | `JOB IN PROGRESS` | The job is currently being processed. Continue polling. |
| **1003** | `ERROR OCCURRED` | An error occurred during the import. Stop polling and check the error message. |
| **1004** | `JOB COMPLETED` | The import finished successfully. The import summary is available in the response. |
| **1005** | `JOB NOT FOUND` | The `jobId` is not valid. Stop polling and verify it. |

### Handling each JOBCODE

| JOBCODE | What to do |
|---------|-----------|
| `1001` or `1002` | Wait a few seconds and repeat the status check. |
| `1003` | **Stop polling.** Inspect `jobInfo` for the error detail. |
| `1004` | **Stop polling.** The job is complete and `jobInfo` holds the import summary. |
| `1005` | **Stop polling.** Verify the `jobId` — it is invalid, or the job has passed its retention window. |

> `jobCode` is returned as a **string** (`"1004"`), not as a number.

---

## Workflow of the Batch Import API

Batch import splits one logical import across many HTTP calls that all feed a single job.

```
 Split the source CSV into batches, each under 100 MB
        │
        ▼
 POST …/data/batch      CONFIG: {"batchKey":"start", "isLastBatch":false, …full config…}
        │                        ── the server opens the job ──
        ▼
   response: { "batchKey": "1694703482470_…_SalesTable", "jobId": "1767024000008787011" }
        │
        ├── POST …/data/batch   CONFIG: {"batchKey":"<returned key>", "isLastBatch":false}   ← repeat per batch
        │
        ▼
   POST …/data/batch      CONFIG: {"batchKey":"<returned key>", "isLastBatch":true}
        │                        ── closes the job ──
        ▼
 GET …/importjobs/<jobId>   ← poll until jobCode is 1004 or 1003
```

| Step | Rule |
|------|------|
| **First batch** | Send `batchKey: "start"`. This is the only call that carries the full import configuration — `tableName`/`importType`, `autoIdentify`, and every parsing option are read here and here only. |
| **Response of the first batch** | Returns the real `batchKey` **and** the `jobId`. Keep both. |
| **Follow-up batches** | Send the returned `batchKey`. Only `batchKey` and `isLastBatch` are read; any other configuration in the CONFIG of a follow-up batch is ignored. |
| **Final batch** | Send `isLastBatch: true`. This closes the job — no further batch can be added (`7337`). |
| **Monitoring** | Use the `jobId` with [Get Import Job Details](#5-get-import-job-details), exactly as for an asynchronous import. |

### When the data actually lands

| `importType` | Commit behaviour |
|--------------|------------------|
| `APPEND`, `UPDATEADD` | Each batch is committed as it is received. Data becomes visible progressively. |
| `TRUNCATEADD` | Nothing is committed until the final batch arrives. The existing rows are replaced in one step at the end. |

> Scheduled processing of the remaining batches begins automatically once the first batch has been imported, and batch order is preserved throughout.

---

## The `callbackUrl` Attribute

`callbackUrl` is an optional attribute of the asynchronous import CONFIG. It changes two things.

| Effect | Detail |
|--------|--------|
| **You get notified instead of polling** | When the job reaches a terminal state, Zoho Analytics sends an **HTTP POST** to your URL with `Content-Type: application/json`. The body is **exactly the same payload** that [Get Import Job Details](#5-get-import-job-details) would return for that job — same `jobId`, `jobCode`, `jobStatus`, and `jobInfo` fields. |
| **The job is always processed asynchronously** | Without a callback, a small upload may be handled inline and finish almost immediately. Supplying `callbackUrl` **forces the job onto the asynchronous pipeline** regardless of file size, so the `jobId` is always meaningful and the callback always fires. |

Rules and constraints:

- The URL must be a well-formed, publicly reachable `http`/`https` address. A malformed URL is rejected with `8125`.
- URLs resolving to a **private or internal IP address** are rejected with `8127` — the callback cannot be pointed at a LAN host.
- If the endpoint cannot be reached at validation time, the request fails with `8126`.
- Your endpoint should respond with a 2xx status. A non-2xx response is logged as a delivery failure.
- The callback is a **notification, not a guarantee** — always keep [Get Import Job Details](#5-get-import-job-details) as a fallback, and remember the summary is only retained for one hour.

> `callbackUrl` is accepted by the two **asynchronous** import APIs and by the **first batch** of a batch import. It has no effect on follow-up batches.

---

## Permission Model

| API | Who may call it |
|-----|-----------------|
| [Create Import Job for a New Table (Asynchronous)](#1-create-import-job-for-a-new-table-asynchronous), [Batch Import Data into New Table](#3-batch-import-data-into-new-table) | An Account Admin or Organization Admin, or a Workspace Admin, or any user with **Create Table** permission on the workspace. |
| [Create Import Job for an Existing Table (Asynchronous)](#2-create-import-job-for-an-existing-table-asynchronous), [Batch Import Data into Existing Table](#4-batch-import-data-into-existing-table) | An Account Admin or Organization Admin, or a Workspace Admin, or any user holding the import permission matching the requested `importType` — see below. |
| [Get Import Job Details](#5-get-import-job-details) | **Only the user who created the job.** Any other user, including an Account Admin, receives `8138`. |

### Import permission by `importType`

| `importType` | Permission required on the table | Equivalent share permission |
|--------------|----------------------------------|------------------------------|
| `APPEND` | Append Import | `importAppend` |
| `UPDATEADD` | Add or Update Import | `importAddOrUpdate` |
| `TRUNCATEADD` | Truncate and Add Import | `importDeleteAllAdd` |

> A user granted only `importAppend` can run an `APPEND` import but receives `7301` for a `TRUNCATEADD` on the same table. Grant the specific import permissions through the [Sharing APIs](SHARING_API_DOC_INFO.md#permissions-fields).

---

## Shared CONFIG Attributes

All four import APIs draw on the same parsing and formatting options. They are listed once here and referenced from each API.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `onError` | String (enum) | `ABORT` | What to do when a value cannot be parsed. See [`onError` Values](#onerror-values). |
| `selectedColumns` | JSONArray of String | all columns | Import only these columns from the source. 1–300 entries. |
| `skipTop` | Integer | `0` | Number of leading rows to ignore before the header row. |
| `delimiter` | Integer (enum) | `0` | CSV field separator, `0`–`4`. **Mandatory when `autoIdentify` is `false`.** |
| `quoted` | Integer (enum) | `2` | CSV quote character, `0`–`2`. **Mandatory when `autoIdentify` is `false`.** |
| `commentChar` | String | none | Lines beginning with this character are ignored. CSV only. **Mandatory when `autoIdentify` is `false`.** |
| `thousandSeparator` | Integer (enum) | auto | Grouping separator in numeric values. See [Number Separator Values](#number-separator-values). |
| `decimalSeparator` | Integer (enum) | auto | Decimal separator in numeric values. See [Number Separator Values](#number-separator-values). |
| `columnSeparators` | JSONObject | — | Per-column separator overrides — column name → `[thousandSeparator, decimalSeparator]`, both as strings. Needs at least two entries (`8149`), and the two must differ (`8148`). |
| `dateFormat` | String | auto | Default date pattern for all date columns, e.g. `dd-MMM-yyyy`. An unparseable pattern fails with `7512`. |
| `columnDateFormat` | JSONObject | — | Per-column date pattern overrides. 1–300 entries. Takes precedence over `dateFormat`. |
| `columnTimeFormat` | JSONObject | — | Per-column time pattern overrides. |
| `columnDurationFormat` | JSONObject | — | Per-column duration pattern overrides. |
| `columnDataTypes` | JSONArray | auto-detected | Explicit data types instead of inference. Up to 500 entries. See [`columnDataTypes` Fields](#columndatatypes-fields). |
| `matchNulls` | Boolean | `false` | Treat empty source values as nulls when matching rows. Relevant to `UPDATEADD`. |
| `updateNullForNegativeValues` | Boolean | `false` | Store null instead of a negative value in columns that do not accept one. |
| `retainColumnNames` | Boolean | `false` | For JSON/XML sources, keep the original key names as column names. |
| `importHiddenRows` | Boolean | `false` | For Excel sources, include rows hidden in the sheet. |
| `importHiddenColumns` | Boolean | `false` | For Excel sources, include columns hidden in the sheet. |
| `callbackUrl` | String | — | Notification endpoint. See [The `callbackUrl` Attribute](#the-callbackurl-attribute). |

#### `fileType` Values

`CSV`, `JSON`, `XML`, `XLS`, `XLSX`, `PARQUET`, `GEOMETRY`. Case-insensitive.

> Applies to the **asynchronous** import APIs only. The batch import APIs accept **CSV only** and have no `fileType` attribute.
>
> `delimiter`, `quoted`, and `commentChar` apply to CSV sources only and are ignored for every other type.

#### `onError` Values

| Value | Behaviour | Effect on the job |
|-------|-----------|-------------------|
| `ABORT` | **Default.** The whole import is rolled back on the first unparseable value. | The job ends with `jobCode` `1003`; nothing is imported. |
| `SKIPROW` | The offending row is skipped; the rest are imported. | `jobCode` `1004`. `successRowCount` is lower than `totalRowCount`; skipped lines appear in `importErrors`. |
| `SETCOLUMNEMPTY` | The offending value is stored as empty; the rest of the row is imported. | `jobCode` `1004`. `warnings` is incremented and the reset values appear in `importErrors`. |

#### Number Separator Values

| `thousandSeparator` | Character | | `decimalSeparator` | Character |
|--------------------:|-----------|---|-------------------:|-----------|
| `0` | Comma `,` | | `0` | Dot `.` |
| `1` | Dot `.` | | `1` | Comma `,` |
| `2` | Space | | | |
| `3` | Single quote `'` | | | |
| `4` | None | | | |

> The thousand and decimal separators must resolve to **different** characters, otherwise the import fails with `8148`.

#### `columnDataTypes` Fields

| Field | Type | Mandatory | Description |
|-------|------|-----------|--------------|
| `columnName` | String | **Yes** | Name of the column in the source data. |
| `dataType` | String | **Yes** | Zoho Analytics data type, e.g. `PLAIN`, `NUMBER`, `DECIMAL_NUMBER`, `CURRENCY`, `DATE`, `EMAIL`, `URL`. |
| `geoRole` | String | No | Geographic role, when `dataType` is a geo type. |

> For an **existing-table** import, entries naming a column that already exists are discarded — an existing column keeps its established type.

---

## 1. Create Import Job for a New Table (Asynchronous)

Uploads a file, creates a new table from it, and returns a job ID for tracking. The table is created and populated in the background.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/bulk/workspaces/<workspace-id>/data` |
| **OAuth Scope** | `ZohoAnalytics.data.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user with Create Table permission on the workspace. |

### CONFIG Parameters

CONFIG is **mandatory** and is sent as a form part alongside the `FILE` part.

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `tableName` | String | **Yes** | — | Name of the table to create. Must be **unused in the workspace** (`7111` otherwise). |
| `fileType` | String (enum) | **Yes** | — | Format of the uploaded file. See [`fileType` Values](#filetype-values). |
| `autoIdentify` | Boolean | **Yes** | — | When `true`, the delimiter, quote character, and column data types are detected automatically. When `false`, `delimiter`, `quoted`, and `commentChar` become **mandatory** for CSV. |
| *(shared options)* | — | No | — | `onError`, `selectedColumns`, `skipTop`, `delimiter`, `quoted`, `commentChar`, `thousandSeparator`, `decimalSeparator`, `columnSeparators`, `dateFormat`, `columnDateFormat`, `columnTimeFormat`, `columnDurationFormat`, `columnDataTypes`, `matchNulls`, `updateNullForNegativeValues`, `retainColumnNames`, `importHiddenRows`, `importHiddenColumns`, `callbackUrl` — see [Shared CONFIG Attributes](#shared-config-attributes). |

> `matchingColumns` is not used — there are no existing rows to match against.

### Sample Requests

**Case 1 — CSV upload with auto-identification**

```http
POST /restapi/v2/bulk/workspaces/466206000000071000/data HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: multipart/form-data; boundary=----ZohoBoundary

------ZohoBoundary
Content-Disposition: form-data; name="CONFIG"

{
    "tableName": "Sales",
    "fileType": "CSV",
    "autoIdentify": true
}
------ZohoBoundary
Content-Disposition: form-data; name="FILE"; filename="Sales.csv"
Content-Type: text/csv

<file contents>
------ZohoBoundary--
```

**Case 2 — JSON upload with a callback and explicit column types clubbed together**

```http
POST /restapi/v2/bulk/workspaces/466206000000071000/data HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: multipart/form-data; boundary=----ZohoBoundary

------ZohoBoundary
Content-Disposition: form-data; name="CONFIG"

{
    "tableName": "SalesJSON",
    "fileType": "JSON",
    "autoIdentify": true,
    "retainColumnNames": true,
    "columnDataTypes": [
        { "columnName": "Sales", "dataType": "CURRENCY" }
    ],
    "onError": "SETCOLUMNEMPTY",
    "callbackUrl": "https://example.com/zoho/import-callback"
}
------ZohoBoundary
Content-Disposition: form-data; name="FILE"; filename="Sales.json"
Content-Type: application/json

<file contents>
------ZohoBoundary--
```

**Case 3 — Strict CSV parsing with no auto-identification**

```http
POST /restapi/v2/bulk/workspaces/466206000000071000/data HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: multipart/form-data; boundary=----ZohoBoundary

------ZohoBoundary
Content-Disposition: form-data; name="CONFIG"

{
    "tableName": "SalesStrict",
    "fileType": "CSV",
    "autoIdentify": false,
    "delimiter": 0,
    "quoted": 2,
    "commentChar": "#",
    "skipTop": 2,
    "thousandSeparator": 0,
    "decimalSeparator": 0,
    "dateFormat": "dd MMM yyyy",
    "onError": "SKIPROW"
}
------ZohoBoundary
Content-Disposition: form-data; name="FILE"; filename="Sales.csv"
Content-Type: text/csv

<file contents>
------ZohoBoundary--
```

**Case 4 — White Label / Client Portal workspace**

```http
POST /restapi/v2/bulk/workspaces/466206000000071009/data HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
Content-Type: multipart/form-data; boundary=----ZohoBoundary

------ZohoBoundary
Content-Disposition: form-data; name="CONFIG"

{
    "tableName": "PortalSales",
    "fileType": "CSV",
    "autoIdentify": true
}
------ZohoBoundary
Content-Disposition: form-data; name="FILE"; filename="PortalSales.csv"
Content-Type: text/csv

<file contents>
------ZohoBoundary--
```

### Sample Responses

**HTTP 200 OK — Job created**

```json
{
    "status": "success",
    "summary": "Create bulk import job",
    "data": {
        "jobId": "1767024000003153087"
    }
}
```

**HTTP 400 Bad Request — Too many jobs already running**

```json
{
    "status": "failure",
    "summary": "ASYNC_IMPORT_LIMIT_EXCEEDED",
    "data": {
        "errorCode": 8134,
        "errorMessage": "The maximum number of simultaneous import jobs has been reached."
    }
}
```

**HTTP 400 Bad Request — A table with this name already exists**

```json
{
    "status": "failure",
    "summary": "META_DBOBJECT_NAME_DUPLICATED",
    "data": {
        "errorCode": 7111,
        "errorMessage": "An object with the name Sales already exists in this workspace."
    }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `status` | String | `"success"` on a successful call, `"failure"` on error. |
| `summary` | String | Localised operation summary. `"Create bulk import job"` for this API. |
| `data` | JSONObject | Response payload wrapper. |
| `data.jobId` | String | ID of the newly created import job, as a string. Pass it to [Get Import Job Details](#5-get-import-job-details) to track progress and, on completion, to read the import summary and the new table's `viewId`. |

> **`viewId` is not returned here.** The table does not exist yet when the job is created — the new table's ID arrives later, inside `jobInfo.viewId` of the [Get Import Job Details](#5-get-import-job-details) response.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **200 means "accepted", not "imported"** | The response confirms only that the job was queued. Nothing has been written yet, and the table does not exist. Poll [Get Import Job Details](#5-get-import-job-details) for the real outcome. |
| **The new table's `viewId` arrives via the job** | Unlike the synchronous [Import Data into a New Table (Synchronous)](SYNC_DATA_IMPORT_API_DOC_INFO.md#1-import-data-into-a-new-table-synchronous), which returns `viewId` immediately, here you must wait for `jobCode` `1004` and read `jobInfo.viewId`. |
| **Duplicate names fail at creation time** | `tableName` uniqueness is validated when the job is created, so `7111` comes back synchronously rather than as a failed job. |
| **`callbackUrl` forces asynchronous handling** | Without it, a small upload may be processed inline and complete almost at once. With it, the job always runs through the asynchronous pipeline so the callback can fire. |
| **`autoIdentify: false` makes three attributes mandatory** | `delimiter`, `quoted`, and `commentChar` must all be supplied for CSV. |
| **The 5-job limit is checked up front** | If the organization already has five queued or running import jobs, the call fails immediately with `8134`. |
| **Job summary expires in one hour** | Read and store the result promptly — see [Limitations](#limitations). |
| **Dependency chain** | [Get Workspace List](WORKSPACE_OPERATIONS_API_DOC_INFO.md) → `<workspace-id>` → Create Import Job → `data.jobId` → [Get Import Job Details](#5-get-import-job-details) → `jobInfo.viewId`. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7092 | `DDL_LOCK_SINCE_IMPORT_IN_PROGRESS` — A batch import is holding a lock in this workspace. | Retry once it has finished. |
| 7111 | `META_DBOBJECT_NAME_DUPLICATED` — An object with this `tableName` already exists. | Choose a different name, or import into the existing table with [Create Import Job for an Existing Table (Asynchronous)](#2-create-import-job-for-an-existing-table-asynchronous). |
| 7203 | `IMPORT_FILE_EMPTY` — No file was uploaded, or the uploaded file is empty. | Attach a non-empty `FILE` part. |
| 7248 | `INVALID_FILE_CONTENT` — The file could not be parsed as the declared `fileType`. | Check that `fileType` matches the actual content. |
| 7301 | `SECURITY_NOT_PERMITTED` — The user cannot create tables in this workspace. | Ensure the user is an Account Admin, Organization Admin, Workspace Admin, or has Create Table permission. |
| 7478 | `MORE_THAN_MAX_COLUMN` — The source has more columns than a table can hold. | Reduce the columns, or use `selectedColumns`. |
| 7512 | `INVALID_DATE_FORMAT` — A date pattern could not be parsed. | Supply a valid pattern such as `dd-MMM-yyyy`. |
| 8046 | `INVALID_COLUMNS_SELECTED` — A name in `selectedColumns` is not present in the source. | Match the names to the source's header row. |
| 8079 | `ATTRIBUTE_NOT_PRESENT_IN_JSON_CONFIGURATION` — A mandatory attribute is missing; with `autoIdentify: false` this is usually `delimiter`, `quoted`, or `commentChar`. | The message names the attribute. |
| 8119 | `INVALID_VALUE_FOR_ATTRIBUTE` — `fileType`, `onError`, `delimiter`, `quoted`, `thousandSeparator`, or `decimalSeparator` is outside its permitted set. | The message names the attribute and allowed values. |
| 8125 | `CALLBACKURL_NOT_VALID` — `callbackUrl` is not a well-formed URL. | Supply a valid absolute `http`/`https` URL. |
| 8126 | `CALLBACKURL_CONNECTION_ERROR` — The callback endpoint could not be reached. | Ensure the endpoint is publicly reachable. |
| 8127 | `CALLBACKURL_RESTRICTED` — The callback URL resolves to a private or internal address. | Use a publicly routable endpoint. |
| 8134 | `ASYNC_IMPORT_LIMIT_EXCEEDED` — The organization already has the maximum number of import jobs in progress. | Wait for a running job to finish and retry. |
| 8148 | `DECIMAL_AND_THOUSAND_SEPARATOR_SAME` — The thousand and decimal separators are the same character. | Choose different separators. |
| 8149 | `DECIMAL_AND_THOUSAND_COLUMN_SEPARATOR_LEGNTH_VALIDATION` — A `columnSeparators` entry has fewer than two values. | Send `[thousandSeparator, decimalSeparator]` per column. |
| 8504 | `LESS_THAN_MIN_OCCURANCE` — `CONFIG` was not sent, or a mandatory key is missing. | Send a complete CONFIG object. |
| 8516 | `UNABLE_TO_PARSE_DATA_TYPE` — A CONFIG value has the wrong JSON type. | Check booleans and integers are sent as such. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.data.create`. |

---

## 2. Create Import Job for an Existing Table (Asynchronous)

Uploads a file and loads it into an existing table in the background, appending, replacing, or merging according to `importType`.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/bulk/workspaces/<workspace-id>/views/<view-id>/data` |
| **OAuth Scope** | `ZohoAnalytics.data.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user holding the import permission matching the requested `importType` — see [Permission Model](#permission-model). |

### CONFIG Parameters

CONFIG is **mandatory**.

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `importType` | String (enum) | **Yes** | — | How incoming rows combine with existing ones. See [`importType` Values](#importtype-values). Case-insensitive. |
| `fileType` | String (enum) | **Yes** | — | Format of the uploaded file. See [`fileType` Values](#filetype-values). |
| `autoIdentify` | Boolean | **Yes** | — | As in the new-table import job — when `false`, `delimiter`, `quoted`, and `commentChar` become mandatory for CSV. |
| `matchingColumns` | JSONArray of String | Conditional* | — | Columns used to match an incoming row against an existing one. 1–100 entries; every name must already exist in the table (`7107` otherwise). |
| *(shared options)* | — | No | — | See [Shared CONFIG Attributes](#shared-config-attributes). |

\* `matchingColumns` is **mandatory** when `importType` is `UPDATEADD`, and ignored for `APPEND` and `TRUNCATEADD`.

#### `importType` Values

| Value | Behaviour | Needs `matchingColumns` |
|-------|-----------|-------------------------|
| `APPEND` | Adds every incoming row, keeping all existing rows. | No |
| `TRUNCATEADD` | Deletes **all** existing rows, then adds the incoming ones. | No |
| `UPDATEADD` | Updates rows whose `matchingColumns` values match; adds the rest as new rows. | **Yes** |

> These three modes are the complete supported set. Any other value is rejected with `8119`.

### Sample Requests

**Case 1 — Append a CSV file to an existing table**

```http
POST /restapi/v2/bulk/workspaces/466206000000071000/views/466206000003154002/data HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: multipart/form-data; boundary=----ZohoBoundary

------ZohoBoundary
Content-Disposition: form-data; name="CONFIG"

{
    "importType": "APPEND",
    "fileType": "CSV",
    "autoIdentify": true
}
------ZohoBoundary
Content-Disposition: form-data; name="FILE"; filename="Sales.csv"
Content-Type: text/csv

<file contents>
------ZohoBoundary--
```

**Case 2 — Merge by key from a JSON file, with a callback**

```http
POST /restapi/v2/bulk/workspaces/466206000000071000/views/466206000003154002/data HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: multipart/form-data; boundary=----ZohoBoundary

------ZohoBoundary
Content-Disposition: form-data; name="CONFIG"

{
    "importType": "UPDATEADD",
    "fileType": "JSON",
    "autoIdentify": true,
    "matchingColumns": ["Region", "Product"],
    "matchNulls": true,
    "onError": "SETCOLUMNEMPTY",
    "callbackUrl": "https://example.com/zoho/import-callback"
}
------ZohoBoundary
Content-Disposition: form-data; name="FILE"; filename="Sales.json"
Content-Type: application/json

<file contents>
------ZohoBoundary--
```

**Case 3 — Replace the table's contents, with explicit CSV parsing**

```http
POST /restapi/v2/bulk/workspaces/466206000000071000/views/466206000003154002/data HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: multipart/form-data; boundary=----ZohoBoundary

------ZohoBoundary
Content-Disposition: form-data; name="CONFIG"

{
    "importType": "TRUNCATEADD",
    "fileType": "CSV",
    "autoIdentify": false,
    "delimiter": 0,
    "quoted": 2,
    "commentChar": "#",
    "selectedColumns": ["Region", "Sales"],
    "skipTop": 1
}
------ZohoBoundary
Content-Disposition: form-data; name="FILE"; filename="Sales.csv"
Content-Type: text/csv

<file contents>
------ZohoBoundary--
```

**Case 4 — White Label / Client Portal workspace**

```http
POST /restapi/v2/bulk/workspaces/466206000000071009/views/466206000003154099/data HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
Content-Type: multipart/form-data; boundary=----ZohoBoundary

------ZohoBoundary
Content-Disposition: form-data; name="CONFIG"

{
    "importType": "APPEND",
    "fileType": "CSV",
    "autoIdentify": true
}
------ZohoBoundary
Content-Disposition: form-data; name="FILE"; filename="PortalSales.csv"
Content-Type: text/csv

<file contents>
------ZohoBoundary--
```

### Sample Responses

**HTTP 200 OK — Job created**

```json
{
    "status": "success",
    "summary": "Create bulk import job",
    "data": {
        "jobId": "1767024000003153090"
    }
}
```

**HTTP 400 Bad Request — A `matchingColumns` entry is not a column of the table**

```json
{
    "status": "failure",
    "summary": "META_OBJECT_NOT_PRESENT",
    "data": {
        "errorCode": 7107,
        "errorMessage": "The column Regoin is not present."
    }
}
```

**HTTP 403 Forbidden — The user lacks the import permission for this `importType`**

```json
{
    "status": "failure",
    "summary": "SECURITY_NOT_PERMITTED",
    "data": {
        "errorCode": 7301,
        "errorMessage": "You (RestapiNotPermittedUser V2) do not have the permission to do this operation. "
    }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `status` | String | `"success"` on a successful call, `"failure"` on error. |
| `summary` | String | Localised operation summary. `"Create bulk import job"`. |
| `data` | JSONObject | Response payload wrapper. |
| `data.jobId` | String | ID of the newly created import job. Pass it to [Get Import Job Details](#5-get-import-job-details). |

> Identical in shape to [Create Import Job for a New Table (Asynchronous)](#1-create-import-job-for-a-new-table-asynchronous). The distinction between the two appears later, in `jobInfo` — a new-table job reports `viewId` and `importOperation: "created"`, an existing-table job reports neither `viewId` nor a creation.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **200 means "accepted", not "imported"** | Nothing has been written when the response returns. Poll [Get Import Job Details](#5-get-import-job-details). |
| **The required permission depends on `importType`** | Append, truncate-and-add, and add-or-update are three separate permissions. A `7301` here means "not allowed to do *this kind* of import". |
| **`TRUNCATEADD` deletes first** | Every existing row is removed before the new rows are written. Because the work happens in the background, a job that then fails can leave the table with fewer rows than it started with — check `jobCode` before assuming the table is intact. |
| **`UPDATEADD` requires `matchingColumns`** | Matching is on the named columns' values, not on any row ID. A name that is not a real column fails with `7107` at job-creation time. |
| **Existing columns keep their types** | `columnDataTypes` entries naming an existing column are discarded. |
| **Validation is split across two phases** | Structural problems (bad `importType`, unknown `matchingColumns`, missing permission) fail synchronously at job creation; data problems (unparseable values, type mismatches) surface later as `jobCode` `1003`. |
| **`callbackUrl` forces asynchronous handling** | As in [Create Import Job for a New Table (Asynchronous)](#1-create-import-job-for-a-new-table-asynchronous). |
| **Dependency chain** | [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → `<view-id>` → [Get Columns](COLUMNS_API_DOC_INFO.md) (to pick `matchingColumns`) → Create Import Job → `data.jobId` → [Get Import Job Details](#5-get-import-job-details). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7092 | `DDL_LOCK_SINCE_IMPORT_IN_PROGRESS` — Another import is holding a DDL lock on this table. | Retry once it has finished. |
| 7104 | `META_OBJECT_NOT_PRESENT` — The view does not exist. | Verify `<view-id>`. |
| 7107 | `META_OBJECT_NOT_PRESENT` — A column named in `matchingColumns` is not present in the table. | Verify the names via [Get Columns](COLUMNS_API_DOC_INFO.md). |
| 7164 | `SYSTEM_TABLE_DATA_MOD` — System table data cannot be modified. | Target a user-created table. |
| 7165 | `SNAPSHOT_TABLE_DATAMOD` — Snapshot table data cannot be modified. | Target a non-snapshot table. |
| 7203 | `IMPORT_FILE_EMPTY` — No file was uploaded, or it is empty. | Attach a non-empty `FILE` part. |
| 7248 | `INVALID_FILE_CONTENT` — The file could not be parsed as the declared `fileType`. | Check that `fileType` matches the content. |
| 7301 | `SECURITY_NOT_PERMITTED` — The user lacks the import permission matching `importType`, or is outside the workspace's permitted IP range. | Grant the specific import permission, or use an `importType` the user is allowed. |
| 7319 | `OBJID_NOT_BELONGS_TO_DB` — The table does not belong to the specified workspace. | Ensure `<workspace-id>` and `<view-id>` are consistent. |
| 7478 | `MORE_THAN_MAX_COLUMN` — The source has more columns than the table can hold. | Reduce the columns, or use `selectedColumns`. |
| 7512 | `INVALID_DATE_FORMAT` — A date pattern could not be parsed. | Supply a valid pattern. |
| 8046 | `INVALID_COLUMNS_SELECTED` — A name in `selectedColumns` is not present in the source. | Match the names to the source's header row. |
| 8079 | `ATTRIBUTE_NOT_PRESENT_IN_JSON_CONFIGURATION` — A mandatory attribute is missing — commonly `matchingColumns` for `UPDATEADD`, or the CSV attributes when `autoIdentify` is `false`. | The message names the attribute. |
| 8119 | `INVALID_VALUE_FOR_ATTRIBUTE` — `importType`, `fileType`, `onError`, or a parsing attribute is outside its permitted set. | The message names the attribute and allowed values. |
| 8125 / 8126 / 8127 | `CALLBACKURL_NOT_VALID` / `CALLBACKURL_CONNECTION_ERROR` / `CALLBACKURL_RESTRICTED` — The callback URL is malformed, unreachable, or points at a private address. | See [The `callbackUrl` Attribute](#the-callbackurl-attribute). |
| 8134 | `ASYNC_IMPORT_LIMIT_EXCEEDED` — The maximum number of simultaneous import jobs is already in progress. | Wait for a running job to finish. |
| 8148 / 8149 | Separator configuration errors. | See [Number Separator Values](#number-separator-values). |
| 8504 | `LESS_THAN_MIN_OCCURANCE` — `CONFIG` was not sent, or a mandatory key is missing. | Send a complete CONFIG object. |
| 8516 | `UNABLE_TO_PARSE_DATA_TYPE` — A CONFIG value has the wrong JSON type. | Check booleans and integers. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.data.create`. |

---

## 3. Batch Import Data into New Table

Creates a new table and loads it from **several uploads**, all belonging to one import job. Called once per batch.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/bulk/workspaces/<workspace-id>/data/batch` |
| **OAuth Scope** | `ZohoAnalytics.data.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user with Create Table permission on the workspace. |

### CONFIG Parameters

CONFIG is **mandatory on every batch**. Which attributes are read depends on whether this is the first batch.

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `batchKey` | String | **Yes** | — | `"start"` on the **first** batch. On every following batch, the `batchKey` returned by the first call. An unrecognised key fails with `7338`. |
| `isLastBatch` | Boolean | No | `false` | Set `true` on the **final** batch to close the job and commit. Once sent, no further batch is accepted (`7337`). |
| `tableName` | String | **Yes on the first batch** | — | Name of the table to create. Must be unused in the workspace (`7111`). Ignored on follow-up batches. |
| `autoIdentify` | Boolean | **Yes on the first batch** | — | When `false`, `delimiter`, `quoted`, and `commentChar` become mandatory. Ignored on follow-up batches. |
| *(shared options)* | — | No | — | Read from the **first batch only** — `onError`, `selectedColumns`, `skipTop`, `delimiter`, `quoted`, `commentChar`, `thousandSeparator`, `decimalSeparator`, `columnSeparators`, `dateFormat`, `columnDateFormat`, `columnTimeFormat`, `columnDurationFormat`, `columnDataTypes`, `matchNulls`, `updateNullForNegativeValues`, `retainColumnNames`, `callbackUrl`. See [Shared CONFIG Attributes](#shared-config-attributes). |

> There is **no `fileType` attribute** — batch import accepts CSV only.
>
> Repeating the full configuration on every batch is harmless and is the convention in Zoho's own examples, but only `batchKey` and `isLastBatch` are actually read after the first batch.

### Sample Requests

**Case 1 — First batch: opens the job**

```http
POST /restapi/v2/bulk/workspaces/466206000000071000/data/batch HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: multipart/form-data; boundary=----ZohoBoundary

------ZohoBoundary
Content-Disposition: form-data; name="CONFIG"

{
    "batchKey": "start",
    "isLastBatch": false,
    "tableName": "SalesTable",
    "autoIdentify": true,
    "onError": "SETCOLUMNEMPTY"
}
------ZohoBoundary
Content-Disposition: form-data; name="FILE"; filename="Sales_batch1.csv"
Content-Type: text/csv

<batch 1 contents>
------ZohoBoundary--
```

**Case 2 — Follow-up batch: uses the returned `batchKey`**

```http
POST /restapi/v2/bulk/workspaces/466206000000071000/data/batch HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: multipart/form-data; boundary=----ZohoBoundary

------ZohoBoundary
Content-Disposition: form-data; name="CONFIG"

{
    "batchKey": "1694703482470_1767024000008426012_SalesTable",
    "isLastBatch": false
}
------ZohoBoundary
Content-Disposition: form-data; name="FILE"; filename="Sales_batch2.csv"
Content-Type: text/csv

<batch 2 contents>
------ZohoBoundary--
```

**Case 3 — Final batch: closes the job**

```http
POST /restapi/v2/bulk/workspaces/466206000000071000/data/batch HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: multipart/form-data; boundary=----ZohoBoundary

------ZohoBoundary
Content-Disposition: form-data; name="CONFIG"

{
    "batchKey": "1694703482470_1767024000008426012_SalesTable",
    "isLastBatch": true
}
------ZohoBoundary
Content-Disposition: form-data; name="FILE"; filename="Sales_batch3.csv"
Content-Type: text/csv

<batch 3 contents>
------ZohoBoundary--
```

**Case 4 — White Label / Client Portal workspace (first batch)**

```http
POST /restapi/v2/bulk/workspaces/466206000000071009/data/batch HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
Content-Type: multipart/form-data; boundary=----ZohoBoundary

------ZohoBoundary
Content-Disposition: form-data; name="CONFIG"

{
    "batchKey": "start",
    "isLastBatch": false,
    "tableName": "PortalSalesTable",
    "autoIdentify": true
}
------ZohoBoundary
Content-Disposition: form-data; name="FILE"; filename="PortalSales_batch1.csv"
Content-Type: text/csv

<batch 1 contents>
------ZohoBoundary--
```

### Sample Responses

**HTTP 200 OK — Batch accepted (identical shape for the first, follow-up, and final batches)**

```json
{
    "status": "success",
    "summary": "Create bulk import job",
    "data": {
        "batchKey": "1694703482470_1767024000008426012_SalesTable",
        "jobId": "1767024000008787011"
    }
}
```

**HTTP 400 Bad Request — A batch was sent after the final one**

```json
{
    "status": "failure",
    "summary": "BATCH_IMPORT_LAST_BATCH_ALREADY_RECEIVED",
    "data": {
        "errorCode": 7337,
        "errorMessage": "The last batch has already been received for the batch key 1694703482470_1767024000008426012_SalesTable."
    }
}
```

**HTTP 400 Bad Request — Too many batches for one job**

```json
{
    "status": "failure",
    "summary": "BATCH_IMPORT_LIMIT_EXCEEDED",
    "data": {
        "errorCode": 7336,
        "errorMessage": "The allowed number of batches (100) has been exceeded."
    }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `status` | String | `"success"` on a successful call, `"failure"` on error. |
| `summary` | String | Localised operation summary. `"Create bulk import job"` — the same string for every batch, including follow-ups. |
| `data` | JSONObject | Response payload wrapper. |
| `data.batchKey` | String | The job's batch key, e.g. `1694703482470_1767024000008426012_SalesTable`. **Generated by the server on the first batch** and echoed unchanged by every subsequent batch. Send it as `batchKey` in every following call. |
| `data.jobId` | String | ID of the import job. Constant across all batches of the job. Pass it to [Get Import Job Details](#5-get-import-job-details). |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **`batchKey: "start"` is a literal** | The first batch must send exactly the string `"start"`. It is not a placeholder for a value you generate — the server mints the real key and returns it. |
| **Configuration is read once** | `tableName`, `autoIdentify`, and every parsing option are consumed from the **first** batch. Changing them on a later batch has no effect; the job keeps the first batch's configuration. |
| **The job is not closed until you say so** | Without `isLastBatch: true` the job stays open and never commits. An abandoned batch job holds one of the five concurrent-job slots. |
| **The final batch is final** | After `isLastBatch: true`, any further batch on that key fails with `7337`. |
| **CSV only** | There is no `fileType`; every batch is parsed as CSV. |
| **Per-batch size limit** | Each uploaded batch may be up to 100 MB. The job's total size is unbounded, subject to the 100-batch ceiling. |
| **Ordering is preserved** | Batches are committed in the order the server receives them. There is no way to re-send or reorder a batch once accepted. |
| **Data appears progressively** | Scheduled processing of the remaining batches starts automatically after the first batch is imported. |
| **Errors can be synchronous or deferred** | An invalid key, a closed job, or an exceeded batch limit fails on the batch call itself. Data errors surface later as `jobCode` `1003`. |
| **Dependency chain** | [Get Workspace List](WORKSPACE_OPERATIONS_API_DOC_INFO.md) → first batch (`batchKey: "start"`) → `data.batchKey` + `data.jobId` → follow-up batches → final batch → [Get Import Job Details](#5-get-import-job-details). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7092 | `DDL_LOCK_SINCE_IMPORT_IN_PROGRESS` — A batch import is holding a lock in this workspace. | Retry once it has finished. |
| 7111 | `META_DBOBJECT_NAME_DUPLICATED` — An object with this `tableName` already exists. | Choose a different name, or use [Batch Import Data into Existing Table](#4-batch-import-data-into-existing-table). |
| 7203 | `IMPORT_FILE_EMPTY` — No file was uploaded for this batch, or it is empty. | Attach a non-empty `FILE` part to every batch. |
| 7248 | `INVALID_FILE_CONTENT` — The batch could not be parsed as CSV. | Batch import accepts CSV only. |
| 7301 | `SECURITY_NOT_PERMITTED` — The user cannot create tables in this workspace. | Ensure the user has Create Table permission. |
| 7336 | `BATCH_IMPORT_LIMIT_EXCEEDED` — More than 100 batches were sent for one job. | Use larger batches so the job fits within the limit. |
| 7337 | `BATCH_IMPORT_LAST_BATCH_ALREADY_RECEIVED` — A batch was sent after `isLastBatch: true`. | Start a new job for additional data. |
| 7338 | `BATCH_IMPORT_INVALID_KEY` — The `batchKey` is not recognised, or its job is no longer active. | Use the `batchKey` returned by the first batch, and start a new job if it has expired. |
| 7478 | `MORE_THAN_MAX_COLUMN` — The source has more columns than a table can hold. | Reduce the columns, or use `selectedColumns` on the first batch. |
| 7512 | `INVALID_DATE_FORMAT` — A date pattern could not be parsed. | Supply a valid pattern on the first batch. |
| 8079 | `ATTRIBUTE_NOT_PRESENT_IN_JSON_CONFIGURATION` — A mandatory attribute is missing; on the first batch this is usually `tableName` or `autoIdentify`. | The message names the attribute. |
| 8119 | `INVALID_VALUE_FOR_ATTRIBUTE` — `onError` or a parsing attribute is outside its permitted set. | The message names the attribute and allowed values. |
| 8125 / 8126 / 8127 | Callback URL is malformed, unreachable, or private. | See [The `callbackUrl` Attribute](#the-callbackurl-attribute). |
| 8134 | `ASYNC_IMPORT_LIMIT_EXCEEDED` — The maximum number of simultaneous import jobs is in progress. | Wait for a running job to finish, or close an abandoned batch job. |
| 8148 / 8149 | Separator configuration errors. | See [Number Separator Values](#number-separator-values). |
| 8504 | `LESS_THAN_MIN_OCCURANCE` — `CONFIG` was not sent, or `batchKey` is missing. | Every batch must carry a CONFIG containing `batchKey`. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.data.create`. |

---

## 4. Batch Import Data into Existing Table

Loads an existing table from several uploads belonging to one import job. Called once per batch.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/bulk/workspaces/<workspace-id>/views/<view-id>/data/batch` |
| **OAuth Scope** | `ZohoAnalytics.data.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user holding the import permission matching the requested `importType` — see [Permission Model](#permission-model). |

### CONFIG Parameters

CONFIG is **mandatory on every batch**.

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `batchKey` | String | **Yes** | — | `"start"` on the first batch; the returned key on every following batch. |
| `isLastBatch` | Boolean | No | `false` | Set `true` on the final batch to close the job and commit. |
| `importType` | String (enum) | **Yes on the first batch** | — | `APPEND`, `TRUNCATEADD`, or `UPDATEADD`. See [`importType` Values](#importtype-values). Ignored on follow-up batches. |
| `autoIdentify` | Boolean | **Yes on the first batch** | — | When `false`, `delimiter`, `quoted`, and `commentChar` become mandatory. Ignored on follow-up batches. |
| `matchingColumns` | JSONArray of String | Conditional* | — | Read from the first batch only. Every name must exist in the table (`7107`). |
| *(shared options)* | — | No | — | Read from the **first batch only**. See [Shared CONFIG Attributes](#shared-config-attributes). |

\* `matchingColumns` is **mandatory** when `importType` is `UPDATEADD`, and ignored otherwise.

> There is **no `fileType` attribute** — batch import accepts CSV only.

### Sample Requests

**Case 1 — First batch of an `UPDATEADD` merge**

```http
POST /restapi/v2/bulk/workspaces/466206000000071000/views/466206000003154002/data/batch HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: multipart/form-data; boundary=----ZohoBoundary

------ZohoBoundary
Content-Disposition: form-data; name="CONFIG"

{
    "batchKey": "start",
    "isLastBatch": false,
    "importType": "UPDATEADD",
    "autoIdentify": true,
    "matchingColumns": ["Region", "Product"],
    "onError": "SETCOLUMNEMPTY"
}
------ZohoBoundary
Content-Disposition: form-data; name="FILE"; filename="Sales_batch1.csv"
Content-Type: text/csv

<batch 1 contents>
------ZohoBoundary--
```

**Case 2 — Follow-up batch**

```http
POST /restapi/v2/bulk/workspaces/466206000000071000/views/466206000003154002/data/batch HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: multipart/form-data; boundary=----ZohoBoundary

------ZohoBoundary
Content-Disposition: form-data; name="CONFIG"

{
    "batchKey": "1694703482470_1767024000008426012_SalesTable",
    "isLastBatch": false
}
------ZohoBoundary
Content-Disposition: form-data; name="FILE"; filename="Sales_batch2.csv"
Content-Type: text/csv

<batch 2 contents>
------ZohoBoundary--
```

**Case 3 — Final batch of a `TRUNCATEADD` replacement (commits everything at this point)**

```http
POST /restapi/v2/bulk/workspaces/466206000000071000/views/466206000003154002/data/batch HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: multipart/form-data; boundary=----ZohoBoundary

------ZohoBoundary
Content-Disposition: form-data; name="CONFIG"

{
    "batchKey": "1694703482470_1767024000008426012_SalesTable",
    "isLastBatch": true
}
------ZohoBoundary
Content-Disposition: form-data; name="FILE"; filename="Sales_batch3.csv"
Content-Type: text/csv

<batch 3 contents>
------ZohoBoundary--
```

**Case 4 — White Label / Client Portal workspace (first batch)**

```http
POST /restapi/v2/bulk/workspaces/466206000000071009/views/466206000003154099/data/batch HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
Content-Type: multipart/form-data; boundary=----ZohoBoundary

------ZohoBoundary
Content-Disposition: form-data; name="CONFIG"

{
    "batchKey": "start",
    "isLastBatch": false,
    "importType": "APPEND",
    "autoIdentify": true
}
------ZohoBoundary
Content-Disposition: form-data; name="FILE"; filename="PortalSales_batch1.csv"
Content-Type: text/csv

<batch 1 contents>
------ZohoBoundary--
```

### Sample Responses

**HTTP 200 OK — Batch accepted**

```json
{
    "status": "success",
    "summary": "Create bulk import job",
    "data": {
        "batchKey": "1694703482470_1767024000008426012_SalesTable",
        "jobId": "1767024000008787015"
    }
}
```

**HTTP 400 Bad Request — The `batchKey` belongs to a different table**

```json
{
    "status": "failure",
    "summary": "BATCH_IMPORT_VIEWID_MISMATCH",
    "data": {
        "errorCode": 7340,
        "errorMessage": "The given view does not match the view associated with this batch key."
    }
}
```

**HTTP 400 Bad Request — The `batchKey` is not recognised**

```json
{
    "status": "failure",
    "summary": "BATCH_IMPORT_INVALID_KEY",
    "data": {
        "errorCode": 7338,
        "errorMessage": "The batch key 1694703482470_1767024000008426012_SalesTable is not valid."
    }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `status` | String | `"success"` on a successful call, `"failure"` on error. |
| `summary` | String | Localised operation summary. `"Create bulk import job"`. |
| `data` | JSONObject | Response payload wrapper. |
| `data.batchKey` | String | The job's batch key. Generated on the first batch, echoed by every subsequent batch. |
| `data.jobId` | String | ID of the import job, constant across all batches. |

> Identical in shape to [Batch Import Data into New Table](#3-batch-import-data-into-new-table).

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **The `batchKey` is bound to one table** | A key opened against one view cannot be used to upload batches into another; the mismatch is rejected with `7340`. This is the one validation that [Batch Import Data into New Table](#3-batch-import-data-into-new-table) does not have. |
| **Commit timing depends on `importType`** | `APPEND` and `UPDATEADD` commit each batch as it arrives, so rows appear progressively. `TRUNCATEADD` commits only after the final batch — the existing rows are replaced in a single step at the end. |
| **`TRUNCATEADD` across batches is the safer replacement pattern** | Because nothing is deleted until the last batch lands, an abandoned `TRUNCATEADD` batch job leaves the original data intact — unlike the single-call [Create Import Job for an Existing Table (Asynchronous)](#2-create-import-job-for-an-existing-table-asynchronous), which deletes first. |
| **Configuration is read once** | `importType`, `matchingColumns`, `autoIdentify`, and all parsing options come from the first batch. |
| **The required permission depends on `importType`** | Checked when the job is opened, on the first batch. |
| **CSV only** | No `fileType` attribute. |
| **The job must be closed** | Without `isLastBatch: true` the job never commits and holds a concurrent-job slot. |
| **Dependency chain** | [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → `<view-id>` → [Get Columns](COLUMNS_API_DOC_INFO.md) → first batch → `data.batchKey` + `data.jobId` → follow-up batches → final batch → [Get Import Job Details](#5-get-import-job-details). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7092 | `DDL_LOCK_SINCE_IMPORT_IN_PROGRESS` — Another import holds a DDL lock on this table. | Retry once it has finished. |
| 7104 | `META_OBJECT_NOT_PRESENT` — The view does not exist. | Verify `<view-id>`. |
| 7107 | `META_OBJECT_NOT_PRESENT` — A column named in `matchingColumns` is not present. | Verify the names via [Get Columns](COLUMNS_API_DOC_INFO.md). |
| 7164 | `SYSTEM_TABLE_DATA_MOD` — System table data cannot be modified. | Target a user-created table. |
| 7165 | `SNAPSHOT_TABLE_DATAMOD` — Snapshot table data cannot be modified. | Target a non-snapshot table. |
| 7203 | `IMPORT_FILE_EMPTY` — No file was uploaded for this batch, or it is empty. | Attach a non-empty `FILE` part. |
| 7248 | `INVALID_FILE_CONTENT` — The batch could not be parsed as CSV. | Batch import accepts CSV only. |
| 7301 | `SECURITY_NOT_PERMITTED` — The user lacks the import permission matching `importType`. | Grant the specific import permission, or use a permitted `importType`. |
| 7319 | `OBJID_NOT_BELONGS_TO_DB` — The table does not belong to the specified workspace. | Ensure `<workspace-id>` and `<view-id>` are consistent. |
| 7336 | `BATCH_IMPORT_LIMIT_EXCEEDED` — More than 100 batches were sent for one job. | Use larger batches. |
| 7337 | `BATCH_IMPORT_LAST_BATCH_ALREADY_RECEIVED` — A batch was sent after `isLastBatch: true`. | Start a new job for additional data. |
| 7338 | `BATCH_IMPORT_INVALID_KEY` — The `batchKey` is not recognised or is no longer active. | Use the key returned by the first batch. |
| 7340 | `BATCH_IMPORT_VIEWID_MISMATCH` — The `batchKey` belongs to a different table. | Send every batch of a job to the same `<view-id>`. |
| 7512 | `INVALID_DATE_FORMAT` — A date pattern could not be parsed. | Supply a valid pattern on the first batch. |
| 8079 | `ATTRIBUTE_NOT_PRESENT_IN_JSON_CONFIGURATION` — A mandatory attribute is missing; on the first batch this is usually `importType`, `autoIdentify`, or `matchingColumns`. | The message names the attribute. |
| 8119 | `INVALID_VALUE_FOR_ATTRIBUTE` — `importType`, `onError`, or a parsing attribute is outside its permitted set. | The message names the attribute and allowed values. |
| 8125 / 8126 / 8127 | Callback URL is malformed, unreachable, or private. | See [The `callbackUrl` Attribute](#the-callbackurl-attribute). |
| 8134 | `ASYNC_IMPORT_LIMIT_EXCEEDED` — The maximum number of simultaneous import jobs is in progress. | Wait for a running job to finish. |
| 8148 / 8149 | Separator configuration errors. | See [Number Separator Values](#number-separator-values). |
| 8504 | `LESS_THAN_MIN_OCCURANCE` — `CONFIG` was not sent, or `batchKey` is missing. | Every batch must carry a CONFIG containing `batchKey`. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.data.create`. |

---

## 5. Get Import Job Details

Returns the current state of an import job and, once it has finished, the full import summary. This is the monitoring API for **all four** import APIs above.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/bulk/workspaces/<workspace-id>/importjobs/<job-id>` |
| **OAuth Scope** | `ZohoAnalytics.data.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | **Only the user who created the import job.** Any other user — including an Account Admin or Organization Admin — receives `8138`. |

> This API has no CONFIG parameter.

### Sample Requests

**Case 1 — Poll an asynchronous import job**

```http
GET /restapi/v2/bulk/workspaces/466206000000071000/importjobs/1767024000003153087 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Poll a batch import job**

```http
GET /restapi/v2/bulk/workspaces/466206000000071000/importjobs/1767024000008787011 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 3 — White Label / Client Portal workspace**

```http
GET /restapi/v2/bulk/workspaces/466206000000071009/importjobs/1767024000003153099 HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
```

### Sample Responses

**HTTP 200 OK — Job still running (`jobCode` `1002`)**

```json
{
    "status": "success",
    "summary": "Fetch import job info",
    "data": {
        "jobId": "1767024000003153087",
        "jobCode": "1002",
        "jobStatus": "JOB IN PROGRESS"
    }
}
```

**HTTP 200 OK — Job completed after a new-table import (`jobCode` `1004`)**

```json
{
    "status": "success",
    "summary": "Fetch import job info",
    "data": {
        "jobId": "1767024000003153087",
        "jobCode": "1004",
        "jobStatus": "JOB COMPLETED",
        "jobInfo": {
            "viewId": "1767024000003154002",
            "importSummary": {
                "importType": "APPEND",
                "totalColumnCount": 7,
                "selectedColumnCount": 7,
                "totalRowCount": 755,
                "successRowCount": 755,
                "warnings": 0,
                "importOperation": "created"
            },
            "columnDetails": {
                "Date": "Date",
                "Region": "Plain Text",
                "Product Category": "Plain Text",
                "Product": "Plain Text",
                "Customer Name": "Plain Text",
                "Sales": "Currency",
                "Cost": "Currency"
            },
            "importErrors": ""
        },
        "expiryTime": "1623764592309"
    }
}
```

**HTTP 200 OK — Batch import job completed (carries `batchKey`)**

```json
{
    "status": "success",
    "summary": "Fetch import job info",
    "data": {
        "jobId": "1767024000008787011",
        "jobCode": "1004",
        "jobStatus": "JOB COMPLETED",
        "batchKey": "1694703482470_1767024000008426012_SalesTable",
        "jobInfo": {
            "importSummary": {
                "importType": "APPEND",
                "totalColumnCount": 5,
                "selectedColumnCount": 5,
                "totalRowCount": 250000,
                "successRowCount": 250000,
                "warnings": 0,
                "importOperation": "updated"
            },
            "columnDetails": {
                "Region": "Plain Text",
                "Product": "Plain Text",
                "Sales": "Currency",
                "Cost": "Currency",
                "Date": "Date"
            },
            "importErrors": ""
        },
        "expiryTime": "1623768192309"
    }
}
```

**HTTP 200 OK — Job failed (`jobCode` `1003`)**

```json
{
    "status": "success",
    "summary": "Fetch import job info",
    "data": {
        "jobId": "1767024000003153091",
        "jobCode": "1003",
        "jobStatus": "ERROR OCCURRED",
        "jobInfo": {
            "errorCode": 7232,
            "errorMessage": "<nobr>[Line: 2 Field:  1] (West) -ERROR: Invalid NUMBER value</NOBR><br>"
        },
        "expiryTime": "1623764592309"
    }
}
```

**HTTP 403 Forbidden — Another user's job**

```json
{
    "status": "failure",
    "summary": "IMPORT_JOB_ACCESS_DENIED",
    "data": {
        "errorCode": 8138,
        "errorMessage": "You do not have access to this import job."
    }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `status` | String | `"success"` on a successful call, `"failure"` on error. **A failed *import job* still returns `"success"`** — the job's own outcome is in `jobCode`, not here. |
| `summary` | String | Localised operation summary. `"Fetch import job info"` for this API. |
| `data` | JSONObject | Response payload wrapper. |
| `data.jobId` | String | The job's ID, echoed from the request. |
| `data.jobCode` | String | Current job state as a **string**: `"1001"`, `"1002"`, `"1003"`, `"1004"`, or `"1005"`. See [JOBCODE and status messages](#jobcode-and-status-messages). |
| `data.jobStatus` | String | Human-readable form of `jobCode` — `JOB NOT INITIATED`, `JOB IN PROGRESS`, `ERROR OCCURRED`, `JOB COMPLETED`, or `JOB NOT FOUND`. |
| `data.batchKey` | String | **Present only for batch-import jobs.** The batch key the job was assembled under. Absent for asynchronous imports. |
| `data.jobInfo` | JSONObject | **Present only when `jobCode` is `1004` or `1003`.** On success it holds the import summary; on failure it holds the error detail. Absent while the job is queued or running. |
| `jobInfo.viewId` | String | ID of the table that was created. Present only for a **new-table** import job. This is where the new table's ID is finally delivered. |
| `jobInfo.importSummary` | JSONObject | Counts describing what was loaded. |
| `importSummary.importType` | String | The import type applied, in upper case. `"APPEND"` for a new-table import. |
| `importSummary.totalColumnCount` | Number | Columns found in the source data. |
| `importSummary.selectedColumnCount` | Number | Columns actually imported. |
| `importSummary.totalRowCount` | Number | Data rows found in the source. |
| `importSummary.successRowCount` | Number | Rows actually written. Lower than `totalRowCount` when `onError: "SKIPROW"` dropped rows. |
| `importSummary.warnings` | Number | Count of values reset or flagged, driven mainly by `onError: "SETCOLUMNEMPTY"`. |
| `importSummary.importOperation` | String | `"created"` for a new-table job, `"updated"` for an existing-table job. |
| `jobInfo.columnDetails` | JSONObject | Column name → assigned data type, as a display label (`"Plain Text"`, `"Number"`, `"Currency"`, `"Date"`, `"E-Mail"`, `"URL"`, `"Geo Column"`, …). |
| `jobInfo.importErrors` | String | Per-line warnings and resets as an **HTML fragment**. Empty string `""` when the import was clean. Not machine-readable — display or log it rather than parsing it. |
| `jobInfo.errorCode` | Number | Present when `jobCode` is `1003`. The error code that caused the job to fail. |
| `jobInfo.errorMessage` | String | Present when `jobCode` is `1003`. The failure detail, often an HTML fragment naming the offending line and field. |
| `data.expiryTime` | String | Epoch timestamp in **milliseconds**, as a string, after which the job summary is discarded. Present only alongside `jobInfo`. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **`status` and `jobCode` mean different things** | `status` reports whether the *API call* worked; `jobCode` reports whether the *import* worked. A job that failed outright still returns `"status": "success"` with `jobCode` `1003`. Never infer import success from the HTTP status or `status` field. |
| **`jobInfo` is conditionally present** | It appears only for `1004` and `1003`. Polling code must tolerate its absence while the job is queued or running. |
| **`jobCode` is a string** | Compare against `"1004"`, not `1004`. |
| **`viewId` appears here, not at job creation** | For a new-table job this is the only place the created table's ID is delivered. |
| **`batchKey` marks a batch job** | Its presence distinguishes a batch import from an asynchronous one in the response. |
| **The job is private to its creator** | `8138` for anyone else, regardless of role. An integration that creates jobs under a service account must poll under that same account. |
| **`1005` also means "expired"** | A `jobId` that was valid an hour ago returns `JOB NOT FOUND` once the summary has been discarded — the code does not distinguish "never existed" from "no longer retained". |
| **Poll roughly every 10 seconds** | Frequent enough to be responsive, sparse enough to avoid needless load. Stop on `1003`, `1004`, or `1005`. |
| **Callback delivers this same payload** | If `callbackUrl` was supplied, the body POSTed to it is exactly this `data` structure. |
| **Dependency chain** | Any of the four import APIs above → `data.jobId` → Get Import Job Details → `jobInfo.viewId` → [Row APIs](ROW_API_DOC_INFO.md), [Get Columns](COLUMNS_API_DOC_INFO.md). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7103 | `META_OBJECT_NOT_PRESENT` — Workspace not found. | Verify `<workspace-id>` and the `ZANALYTICS-ORGID` header. |
| 8137 | `IMPORT_JOB_NOT_FOUND` — No import job exists with this ID. | Verify the `jobId`. Note that a job whose summary has expired is also reported as `jobCode` `1005`. |
| 8138 | `IMPORT_JOB_ACCESS_DENIED` — The job was created by a different user. | Poll under the same account that created the job. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.data.create`. |

---

## Appendix A – Common HTTP Headers

| Header | Value | Required | Description |
|--------|-------|----------|-------------|
| `Authorization` | `Zoho-oauthtoken <oauth-token>` | **Mandatory** | OAuth 2.0 access token of the calling user. |
| `ZANALYTICS-ORGID` | Organization ID string | **Mandatory** | Organization ID of the workspace. |
| `Content-Type` | `multipart/form-data; boundary=…` | Conditional | Required by the four import APIs, which send `CONFIG` and `FILE` as form parts. [Get Import Job Details](#5-get-import-job-details) sends no payload. |

> **`ZANALYTICS-DEST-ORGID` is not used by any API in this document.** That header applies only to cross-organization copy operations (Copy Workspace, [Copy Views](VIEW_OPERATIONS_API_DOC_INFO.md#2-copy-views), Copy Formulas).

Example (first batch of a batch import):

```http
POST /restapi/v2/bulk/workspaces/466206000000071000/data/batch HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: multipart/form-data; boundary=----ZohoBoundary

------ZohoBoundary
Content-Disposition: form-data; name="CONFIG"

{"batchKey":"start","isLastBatch":false,"tableName":"SalesTable","autoIdentify":true}
------ZohoBoundary
Content-Disposition: form-data; name="FILE"; filename="Sales_batch1.csv"
Content-Type: text/csv

<batch 1 contents>
------ZohoBoundary--
```

---

## Appendix B – OAuth Scope Summary

| API | HTTP Method | Scope |
|-----|-------------|-------|
| Create Import Job for a New Table (Asynchronous) | POST | `ZohoAnalytics.data.create` |
| Create Import Job for an Existing Table (Asynchronous) | POST | `ZohoAnalytics.data.create` |
| Batch Import Data into New Table | POST | `ZohoAnalytics.data.create` |
| Batch Import Data into Existing Table | POST | `ZohoAnalytics.data.create` |
| Get Import Job Details | GET | `ZohoAnalytics.data.create` |

> All five share **one** scope, including the read-only [Get Import Job Details](#5-get-import-job-details) — it is registered as a `create`-type operation even though it is a `GET`. A token holding only `ZohoAnalytics.data.read` therefore cannot poll an import job. Grant `ZohoAnalytics.data.create` for the whole workflow.

---

## Appendix C – API-Specific Notes and Behaviours

### Create Import Job for a New Table (Asynchronous)

- **The one-call answer for files up to 100 MB.** Everything [Import Data into a New Table (Synchronous)](SYNC_DATA_IMPORT_API_DOC_INFO.md#1-import-data-into-a-new-table-synchronous) does, but without holding the connection open — at the cost of having to poll.
- **The created table's `viewId` is deferred.** It is not in this response; it arrives in `jobInfo.viewId` once `jobCode` reaches `1004`. Integrations that immediately need the table ID must poll before they can continue.
- **Name collisions fail fast.** `tableName` uniqueness is checked at job-creation time, so `7111` is synchronous rather than a wasted job.
- **`callbackUrl` is what makes the job genuinely asynchronous.** Without it a small upload may be handled inline; with it the job always runs through the asynchronous pipeline so the callback can fire.
- **The 5-job ceiling is organization-wide.** It counts every queued or running job across the whole organization, including abandoned batch jobs that were never closed — a common cause of an unexpected `8134`.
- **Dependency chain:** [Get Workspace List](WORKSPACE_OPERATIONS_API_DOC_INFO.md) → Create Import Job → `jobId` → [Get Import Job Details](#5-get-import-job-details) → `jobInfo.viewId`.

### Create Import Job for an Existing Table (Asynchronous)

- **Its permission requirement is a function of `importType`.** Three import modes map to three distinct permissions, so a `7301` means "not allowed to do *this kind* of import", not "not allowed to import at all".
- **`TRUNCATEADD` is riskier here than in batch form.** The single-call version deletes the existing rows and then loads; because the work is asynchronous, a job that fails afterwards leaves the table emptier than it started. [Batch Import Data into Existing Table](#4-batch-import-data-into-existing-table) defers the delete until the final batch, which is safer for large replacements.
- **Validation is split across two phases.** Structural errors (`importType`, `matchingColumns`, permissions) fail synchronously; data errors surface later as `jobCode` `1003`. A 200 here proves only that the *configuration* was acceptable.
- **`UPDATEADD` matches on values.** `matchingColumns` names the columns whose values form the key; there is no row ID involved.
- **Existing columns keep their types.** `columnDataTypes` only influences columns the import adds.
- **Dependency chain:** [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → [Get Columns](COLUMNS_API_DOC_INFO.md) → Create Import Job → `jobId` → [Get Import Job Details](#5-get-import-job-details).

### Batch Import Data into New Table

- **It is a stateful protocol, not a single call.** `"start"` opens the job, the returned `batchKey` threads the batches together, and `isLastBatch: true` closes it. Getting any of the three wrong is the main failure mode, which is why `7337` and `7338` exist.
- **The first batch is the only one that configures anything.** `tableName`, `autoIdentify`, `onError`, and every parsing option are read once. Sending different values on batch three changes nothing and gives no warning.
- **An unclosed job is a leaked resource.** Without a final batch the job never commits and keeps occupying one of the five concurrent slots until it expires. Always send the closing batch, even on an error path.
- **CSV only, with a per-batch ceiling.** There is no `fileType`; each batch may be up to 100 MB and a job may hold up to 100 batches.
- **Order is fixed at upload time.** Batches commit in the order received, and none can be re-sent or reordered.
- **Dependency chain:** first batch (`"start"`) → `batchKey` + `jobId` → follow-up batches → final batch → [Get Import Job Details](#5-get-import-job-details) → `jobInfo.viewId`.

### Batch Import Data into Existing Table

- **The `batchKey` is bound to one table.** Sending a batch for the right key but the wrong `<view-id>` fails with `7340` — a validation that the new-table variant has no need for.
- **Commit timing differs by `importType`, and it matters.** `APPEND` and `UPDATEADD` commit each batch as it lands, so the table changes progressively and a half-finished job leaves partial data. `TRUNCATEADD` holds everything until the final batch, which makes it the safer way to replace a large table.
- **The permission check happens on the first batch**, against the `importType` declared there.
- **Configuration is read once**, exactly as in the new-table variant.
- **The job must be closed.** An abandoned job holds a concurrent-job slot and, for `TRUNCATEADD`, never applies any of the uploaded data.
- **Dependency chain:** [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → [Get Columns](COLUMNS_API_DOC_INFO.md) → first batch → follow-up batches → final batch → [Get Import Job Details](#5-get-import-job-details).

### Get Import Job Details

- **The single monitoring endpoint for all four import APIs.** Whatever created the job — one call or fifty batches, new table or existing — this is how you learn the outcome.
- **Two independent success signals, and conflating them is the classic bug.** `status` is the API call's result; `jobCode` is the import's result. A completely failed import returns `"status": "success"` with `jobCode` `1003`, so code that checks only the HTTP status will report success for a failed load.
- **`jobInfo` only exists in terminal states.** Polling code must handle its absence for `1001` and `1002`.
- **It is the delivery point for a new table's `viewId`.** For a new-table job this response is the only place that ID appears.
- **Strictly private to the job's creator.** `8138` for everyone else including admins — so the account that creates jobs must also be the account that polls them.
- **`1005` is ambiguous by design.** It covers both an invalid `jobId` and a job whose one-hour summary retention has lapsed. Persist the summary if you need it beyond that window.
- **It needs a `create` scope despite being a GET** — see [Appendix B](#appendix-b--oauth-scope-summary).
- **Dependency chain:** [Create Import Job for a New Table (Asynchronous)](#1-create-import-job-for-a-new-table-asynchronous), [Create Import Job for an Existing Table (Asynchronous)](#2-create-import-job-for-an-existing-table-asynchronous), [Batch Import Data into New Table](#3-batch-import-data-into-new-table), or [Batch Import Data into Existing Table](#4-batch-import-data-into-existing-table) → `jobId` → Get Import Job Details.

---

## Appendix D – General Response Payload Notes

| Field / Behaviour | Detail |
|-------------------|--------|
| **All five APIs return HTTP 200 with a body** | None returns 204. The four import APIs return a job reference; the monitoring API returns job state. |
| **Failure responses share one shape** | `{"status": "failure", "summary": "<ERROR_NAME>", "data": {"errorCode": <n>, "errorMessage": "<text>"}}`. `summary` on failure is the error's symbolic name (e.g. `BATCH_IMPORT_INVALID_KEY`), not a localised sentence. |
| **`status` describes the call, `jobCode` describes the import** | The most important distinction in this document. An import that failed entirely is reported as `"status": "success"` with `jobCode` `"1003"`. |
| **`summary` does not distinguish the four import APIs** | All four return `"Create bulk import job"`, including every batch of a batch job. Use the presence of `batchKey` to tell a batch response from an asynchronous one. |
| **All IDs and codes are strings** | `jobId`, `batchKey`, `viewId`, `jobCode`, and `expiryTime` are JSON **strings**, even though `jobCode` and `expiryTime` are numeric in nature. Compare `jobCode` against `"1004"`, not `1004`. |
| **Counts are native numbers** | Inside `importSummary`, `totalColumnCount`, `selectedColumnCount`, `totalRowCount`, `successRowCount`, and `warnings` are genuine JSON numbers. |
| **Conditionally present keys** | `jobInfo` and `expiryTime` appear only in terminal states; `batchKey` only for batch jobs; `jobInfo.viewId` only for new-table jobs; `jobInfo.errorCode` / `errorMessage` only on failure. Test for key presence rather than assuming a fixed schema. |
| **A completed job can still have lost data** | Within `jobInfo`, compare `successRowCount` with `totalRowCount` and check `warnings` — `jobCode` `1004` only means the job ran to completion, not that every row landed. |
| **`importErrors` is HTML, not data** | A fragment of `<nobr>…</NOBR><br>` markup describing each offending line, field, and value. Display or log it; do not parse it. |
| **`columnDetails` uses display labels** | Values such as `"Plain Text"`, `"Positive Number"`, `"Currency"`, `"Geo Column"` — not the `dataType` codes accepted by `columnDataTypes` on the request side. The two vocabularies do not round-trip. |
| **The summary is transient** | Everything under `jobInfo` disappears one hour after the job finishes. Store what you need. |
