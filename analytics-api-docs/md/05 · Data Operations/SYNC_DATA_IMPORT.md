# Zoho Analytics V2 REST API — Synchronous Data Import

This document covers the two **synchronous** data-import REST APIs of Zoho Analytics — the APIs that upload a CSV/JSON/XML/Excel payload and load it into a workspace, either by creating a new table or by writing into an existing one, and return the import result in the same HTTP response.

## What is a "Synchronous" import?

Both APIs accept the data **in the request itself** and return the outcome — rows loaded, columns detected, per-row errors — in the response body. There is no job to poll and no callback: when the call returns, the import has already finished (or already failed).

| | Synchronous import (this document) | Asynchronous / bulk import |
|---|---|---|
| **Endpoint** | `POST /workspaces/<id>/data` and `POST /workspaces/<id>/views/<id>/data` | `POST /bulk/workspaces/...` |
| **Result** | Returned inline in the same response | A job ID to poll |
| **Payload size** | Small to medium (see [Supplying the Data](#supplying-the-data)) | Large files |
| **Callback** | Not supported | Supported |

The two APIs here differ only in their **destination**:

| API | Destination | Key CONFIG attribute |
|-----|-------------|----------------------|
| [Import Data into a New Table (Synchronous)](#1-import-data-into-a-new-table-synchronous) | Creates a **new table** in the workspace and loads the data into it | `tableName` |
| [Import Data into an Existing Table (Synchronous)](#2-import-data-into-an-existing-table-synchronous) | Writes into an **existing table** | `importType` |

> Notes that apply to both APIs:
> - Both are authenticated via OAuth (`Authorization: Zoho-oauthtoken <token>`) and use the scope **`ZohoAnalytics.data.create`**.
> - Both require the `ZANALYTICS-ORGID` header.
> - Both are **available in Client Portal / White Label contexts**.
> - `CONFIG` is **mandatory** for both, and the data must be supplied either as a `FILE` upload or as a `DATA` parameter — see [Supplying the Data](#supplying-the-data).
> - Neither API accepts a `criteria` attribute. Which rows are loaded is decided by the file's contents and by `skipTop`, not by a filter expression.

---

## Index

| # | API Name | Method | URL |
|---|----------|--------|-----|
| 1 | [Import Data into a New Table (Synchronous)](#1-import-data-into-a-new-table-synchronous) | POST | `/restapi/v2/workspaces/<workspace-id>/data` |
| 2 | [Import Data into an Existing Table (Synchronous)](#2-import-data-into-an-existing-table-synchronous) | POST | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/data` |

> **Note on naming:** Per the request for this batch, "Import Data" is documented as **"Import Data into a New Table (Synchronous)"** and "Exist Import" as **"Import Data into an Existing Table (Synchronous)"**.

---

## How the Two APIs Relate

The two imports are two halves of one workflow, joined by the `viewId` that the first one produces.

```
 [Get View List]  ─────────────► <view-id> of an existing table
        │                                   │
        │                                   ▼
        │                    2. Import into an Existing Table
        │                       (APPEND / TRUNCATEADD / UPDATEADD)
        ▼
 1. Import into a New Table  ──► data.viewId  ──────────┘
        (creates the table)          │
                                     ▼
                          [Row APIs] [Export APIs] [Sharing] …
```

| Relationship | Detail |
|---|---|
| **The new-table import produces what the existing-table import consumes** | `data.viewId` from [Import Data into a New Table (Synchronous)](#1-import-data-into-a-new-table-synchronous) is the `<view-id>` for every later call — subsequent imports into the same table, the [Row APIs](ROW_API_DOC_INFO.md), exports, sharing, and so on. It is returned **only** by that API. |
| **The new-table import is create-once** | Re-running [Import Data into a New Table (Synchronous)](#1-import-data-into-a-new-table-synchronous) with the same `tableName` fails with `7111`, because the table already exists. Loading more data into that table is the job of [Import Data into an Existing Table (Synchronous)](#2-import-data-into-an-existing-table-synchronous). |
| **`importType` exists only on the existing-table import** | A new table is always populated by a straight load, so [Import Data into a New Table (Synchronous)](#1-import-data-into-a-new-table-synchronous) has no `importType`. The response reports it as `APPEND` for consistency. |
| **The two have different permission models** | [Import Data into a New Table (Synchronous)](#1-import-data-into-a-new-table-synchronous) is gated on creating tables in the workspace; [Import Data into an Existing Table (Synchronous)](#2-import-data-into-an-existing-table-synchronous) is gated per `importType` on the target table. See [Permission Model](#permission-model). |
| **Everything else is shared** | `fileType`, `autoIdentify`, `onError`, parsing options, date/number formats, and the whole response shape are identical between them. |

### Typical sequences

| Goal | Calls |
|------|-------|
| Load a brand-new dataset | [Import Data into a New Table (Synchronous)](#1-import-data-into-a-new-table-synchronous) → keep `data.viewId` |
| Add this month's rows to that dataset | [Import Data into an Existing Table (Synchronous)](#2-import-data-into-an-existing-table-synchronous) with `importType: "APPEND"` |
| Replace the dataset wholesale | [Import Data into an Existing Table (Synchronous)](#2-import-data-into-an-existing-table-synchronous) with `importType: "TRUNCATEADD"` |
| Merge updates by key | [Import Data into an Existing Table (Synchronous)](#2-import-data-into-an-existing-table-synchronous) with `importType: "UPDATEADD"` + `matchingColumns` |
| Verify what landed | [Get View Details](VIEW_OPERATIONS_API_DOC_INFO.md#7-get-view-details) or [Get Columns](COLUMNS_API_DOC_INFO.md) on the `viewId` |

---

## Supplying the Data

The payload is sent in **one** of two ways. Both APIs accept both modes.

| Mode | Parameter | Limit | Notes |
|------|-----------|-------|-------|
| **File upload** | `FILE` | **20 MB** (20480 KB) | `multipart/form-data`. The file is antivirus-scanned before it is read. The filename may not contain characters outside the permitted set. |
| **Pasted data** | `DATA` | **10,000,000 characters** | The raw file content sent as a form parameter. Exceeding the limit fails with `8139`. |

> If `DATA` is present and non-empty it is used; otherwise the uploaded `FILE` is read. The `fileType` attribute tells the parser how to interpret whichever one you send — it is not inferred from the file's extension.

---

## Permission Model

The two APIs are gated differently, and the requirement for [Import Data into an Existing Table (Synchronous)](#2-import-data-into-an-existing-table-synchronous) **changes with `importType`**.

### Import Data into a New Table (Synchronous)

The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user with **Create Table** permission on the workspace.

### Import Data into an Existing Table (Synchronous)

The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user holding the import permission that corresponds to the `importType` being used:

| `importType` | Permission required on the table | Equivalent share permission |
|--------------|----------------------------------|------------------------------|
| `APPEND` | Append Import | `importAppend` |
| `UPDATEADD` | Add or Update Import | `importAddOrUpdate` |
| `TRUNCATEADD` | Truncate and Add Import | `importDeleteAllAdd` |

> A user granted only `importAppend` can run an `APPEND` import on a shared table but receives `7301` for a `TRUNCATEADD` on the same table. Grant the specific import permissions through the [Sharing APIs](SHARING_API_DOC_INFO.md#permissions-fields).

---

## Table Preconditions (Existing-Table Import)

Before an existing-table import runs, the target table is checked:

| Condition | Error |
|-----------|-------|
| The table must not be a snapshot table | `7165` |
| The table must not be a system table | `7164` |
| No batch import may be holding a DDL lock on the table | `7092` |
| The table must belong to the workspace in the URL | `7319` |
| The caller's IP must be within the workspace's permitted range, when IP restriction is enabled | `7301` |

The new-table import has no such checks — there is no existing table yet — but the `tableName` must be unused in the workspace (`7111`).

---

## 1. Import Data into a New Table (Synchronous)

Creates a new table in the workspace from the uploaded data and returns the new table's ID along with the import result.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/data` |
| **OAuth Scope** | `ZohoAnalytics.data.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user with Create Table permission on the workspace. |

### CONFIG Parameters

CONFIG is **mandatory**. The three attributes at the top of the table are required; everything below is optional.

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `tableName` | String | **Yes** | — | Name of the table to create. Must be **unused in the workspace** (`7111` otherwise). |
| `fileType` | String (enum) | **Yes** | — | Format of the payload. See [`fileType` Values](#filetype-values). |
| `autoIdentify` | Boolean | **Yes** | — | When `true`, Zoho Analytics detects the CSV delimiter, quote character, and column data types itself. When `false`, `delimiter` and `quoted` become **mandatory**. See [`autoIdentify` and CSV Parsing](#autoidentify-and-csv-parsing). |
| `onError` | String (enum) | No | `ABORT` | What to do when a value cannot be parsed into its column's data type. See [`onError` Values](#onerror-values). |
| `selectedColumns` | JSONArray of String | No | all columns | Import only these columns from the source. 1–300 entries. |
| `skipTop` | Integer | No | `0` | Number of leading rows to ignore before the header row. |
| `delimiter` | Integer (enum) | Conditional | `0` | CSV field separator. **Mandatory when `autoIdentify` is `false`** and `fileType` is CSV. Values `0`–`4`; anything else fails with `8119`. |
| `quoted` | Integer (enum) | Conditional | `2` | CSV quote character. **Mandatory when `autoIdentify` is `false`** and `fileType` is CSV. Values `0`–`2`. |
| `commentChar` | String | No | none | Lines beginning with this character are ignored. CSV only. |
| `thousandSeparator` | Integer (enum) | No | auto | Grouping separator used in numeric values. See [Number Separator Values](#number-separator-values). |
| `decimalSeparator` | Integer (enum) | No | auto | Decimal separator used in numeric values. See [Number Separator Values](#number-separator-values). |
| `columnSeparators` | JSONObject | No | — | Per-column separator overrides — column name → `[thousandSeparator, decimalSeparator]`, both as strings. The array must have at least two entries (`8149`), and the two separators must differ (`8148`). |
| `dateFormat` | String | No | auto | Default date pattern for all date columns, e.g. `dd-MMM-yyyy`. An unparseable pattern fails with `7512`. |
| `columnDateFormat` | JSONObject | No | — | Per-column date pattern overrides — column name → pattern. 1–300 entries. Takes precedence over `dateFormat`. |
| `columnTimeFormat` | JSONObject | No | — | Per-column time pattern overrides. An invalid pattern is rejected. |
| `columnDurationFormat` | JSONObject | No | — | Per-column duration pattern overrides. An invalid pattern is rejected. |
| `columnDataTypes` | JSONArray | No | auto-detected | Explicit data types for columns instead of letting Zoho Analytics infer them. Up to 500 entries. See [`columnDataTypes` Fields](#columndatatypes-fields). |
| `matchNulls` | Boolean | No | `false` | Treat empty values in the source as nulls when matching. |
| `updateNullForNegativeValues` | Boolean | No | `false` | Store a null instead of the value when a negative number is found in a column that does not accept one. |
| `retainColumnNames` | Boolean | No | `false` | For JSON/XML imports, keep the source's original key names as column names instead of normalising them. |
| `importHiddenRows` | Boolean | No | `false` | For Excel sources, include rows hidden in the sheet. |
| `importHiddenColumns` | Boolean | No | `false` | For Excel sources, include columns hidden in the sheet. |

> `matchingColumns` is **not** used by this API — there are no existing rows to match against.

#### `fileType` Values

`CSV`, `JSON`, `XML`, `XLS`, `XLSX`, `PARQUET`, `GEOMETRY`. Case-insensitive.

> The parsing attributes `delimiter`, `quoted`, and `commentChar` apply to **CSV only** and are ignored for every other type.

#### `autoIdentify` and CSV Parsing

| `autoIdentify` | Effect |
|----------------|--------|
| `true` | Zoho Analytics detects the delimiter, quote character, and each column's data type from the content. `delimiter` and `quoted` become optional overrides. |
| `false` | Nothing is inferred. `delimiter` and `quoted` are **mandatory** for CSV — omitting either fails with `8079`. |

#### `onError` Values

| Value | Behaviour | Effect on the response |
|-------|-----------|------------------------|
| `ABORT` | **Default.** The whole import is rolled back on the first unparseable value. | The call **fails** with `7232`, and `errorMessage` carries the per-line detail. Nothing is imported. |
| `SKIPROW` | The offending row is skipped; the rest are imported. | HTTP 200. `successRowCount` is lower than `totalRowCount`; skipped lines are listed in `importErrors`. |
| `SETCOLUMNEMPTY` | The offending value is stored as empty; the rest of the row is imported. | HTTP 200. `warnings` is incremented and the reset values are listed in `importErrors`. |

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

A JSONArray of objects, one per column whose type you want to fix explicitly:

| Field | Type | Mandatory | Description |
|-------|------|-----------|--------------|
| `columnName` | String | **Yes** | Name of the column in the source data. |
| `dataType` | String | **Yes** | The Zoho Analytics data type to assign, e.g. `PLAIN`, `NUMBER`, `DECIMAL_NUMBER`, `CURRENCY`, `DATE`, `EMAIL`, `URL`. |
| `geoRole` | String | No | Geographic role, when `dataType` is a geo type. |

### Sample Requests

**Case 1 — Auto-identified CSV upload, minimal configuration**

```http
POST /restapi/v2/workspaces/466206000000071000/data HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: multipart/form-data; boundary=----ZohoBoundary

------ZohoBoundary
Content-Disposition: form-data; name="CONFIG"

{
    "tableName": "SalesData",
    "fileType": "CSV",
    "autoIdentify": true
}
------ZohoBoundary
Content-Disposition: form-data; name="FILE"; filename="sales.csv"
Content-Type: text/csv

Date,Region,Product,Sales,Cost
12 April 2020,West,Fruits and Vegetables,3928.38,200.05
------ZohoBoundary--
```

**Case 2 — Explicit CSV parsing options clubbed together (no auto-identify)**

```http
POST /restapi/v2/workspaces/466206000000071000/data HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: multipart/form-data; boundary=----ZohoBoundary

------ZohoBoundary
Content-Disposition: form-data; name="CONFIG"

{
    "tableName": "SalesDataStrict",
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
Content-Disposition: form-data; name="FILE"; filename="sales.csv"
Content-Type: text/csv

...
------ZohoBoundary--
```

**Case 3 — Pasted JSON data with explicit column data types and selected columns**

```http
POST /restapi/v2/workspaces/466206000000071000/data HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "tableName": "RegionSummary",
    "fileType": "JSON",
    "autoIdentify": true,
    "selectedColumns": ["Region", "Sales"],
    "columnDataTypes": [
        { "columnName": "Sales", "dataType": "CURRENCY" }
    ],
    "retainColumnNames": true,
    "onError": "SETCOLUMNEMPTY"
}&DATA=[{"Region":"West","Sales":"3928.38"},{"Region":"East","Sales":"1250.00"}]
```

**Case 4 — White Label / Client Portal workspace**

```http
POST /restapi/v2/workspaces/466206000000071009/data HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "tableName": "PortalSales",
    "fileType": "CSV",
    "autoIdentify": true
}&DATA=Region,Sales%0AWest,3928.38
```

### Sample Responses

**HTTP 200 OK — Table created and every row loaded (Case 1)**

```json
{
    "status": "success",
    "summary": "Import data",
    "data": {
        "viewId": "466206000000776558",
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
    }
}
```

**HTTP 200 OK — `onError: "SETCOLUMNEMPTY"`: bad values blanked and reported (Case 3)**

```json
{
    "status": "success",
    "summary": "Import data",
    "data": {
        "viewId": "466206000000776560",
        "importSummary": {
            "importType": "APPEND",
            "totalColumnCount": 2,
            "selectedColumnCount": 2,
            "totalRowCount": 2,
            "successRowCount": 2,
            "warnings": 1,
            "importOperation": "created"
        },
        "columnDetails": {
            "Region": "Plain Text",
            "Sales": "Currency"
        },
        "importErrors": "<nobr>[Line: 2 Field:  1] (Hello) -RESET : Invalid NUMBER value</NOBR><br>"
    }
}
```

**HTTP 400 Bad Request — `onError: "ABORT"` (the default) and the file has a bad value**

```json
{
    "status": "failure",
    "summary": "IMPORT_ABORTED",
    "data": {
        "errorCode": 7232,
        "errorMessage": "<nobr>[Line: 2 Field:  1] (West) -ERROR: Invalid NUMBER value</NOBR><br><nobr>The data found at the row 2 has invalid data for the given configuration</NOBR><BR>"
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
        "errorMessage": "An object with the name SalesData already exists in this workspace."
    }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `status` | String | `"success"` on a successful call, `"failure"` on error. |
| `summary` | String | Localised operation summary. `"Import data"` for both import APIs. |
| `data` | JSONObject | Response payload wrapper. |
| `data.viewId` | String | ID of the **newly created table**, as a string. **Returned only by this API** — the existing-table import omits it. This is the `<view-id>` for every follow-up call. |
| `data.importSummary` | JSONObject | Counts describing what was loaded. |
| `importSummary.importType` | String | Always `"APPEND"` for a new-table import — the table was empty, so the data was simply added. |
| `importSummary.totalColumnCount` | Number | Columns found in the source data. |
| `importSummary.selectedColumnCount` | Number | Columns actually imported. Lower than `totalColumnCount` when `selectedColumns` was used. |
| `importSummary.totalRowCount` | Number | Data rows found in the source. |
| `importSummary.successRowCount` | Number | Rows actually written. Lower than `totalRowCount` when `onError: "SKIPROW"` dropped rows. |
| `importSummary.warnings` | Number | Count of values that were reset or flagged — driven mainly by `onError: "SETCOLUMNEMPTY"` and by soft validation failures such as an unrecognised geo value. |
| `importSummary.importOperation` | String | `"created"` for this API (a new table was created); `"updated"` for the existing-table import. |
| `data.columnDetails` | JSONObject | Column name → **assigned data type**, as a display label (`"Plain Text"`, `"Number"`, `"Positive Number"`, `"Decimal Number"`, `"Currency"`, `"Percentage"`, `"Date"`, `"E-Mail"`, `"URL"`, `"Geo Column"`, …). This is how you confirm what Zoho Analytics inferred when `autoIdentify` was `true`. |
| `data.importErrors` | String | Per-line warnings and resets as an **HTML fragment** (`<nobr>[Line: 6 Field:  4] (andhara pradesh) -WARNING: Invalid GEO LOCATION</NOBR><br>…`). **Always present**; an empty string `""` when the import was completely clean. Not machine-readable — display it or log it rather than parsing it. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Synchronous — the result is final when the call returns** | There is no job ID, no polling, and no callback. A 200 means the rows are already in the table. |
| **`data.viewId` is the handoff** | It is the only place the new table's ID is produced. Store it — every later operation on that table needs it. |
| **Create-once** | Re-posting the same `tableName` fails with `7111`. Subsequent loads go through [Import Data into an Existing Table (Synchronous)](#2-import-data-into-an-existing-table-synchronous). |
| **`onError` decides whether a bad value is fatal** | The default `ABORT` turns a single unparseable cell into a failed import with **nothing** written. Use `SKIPROW` or `SETCOLUMNEMPTY` for tolerant loading, and read `importErrors` afterwards. |
| **A clean HTTP 200 is not a clean import** | Check `successRowCount` against `totalRowCount`, and `warnings` against `0`. Both can indicate silently dropped or blanked data. |
| **`columnDetails` is the type-inference report** | With `autoIdentify: true` the types are guessed from the data. Inspect this map — a column that should be `Currency` but came back `Plain Text` usually means the separators were wrong. |
| **`autoIdentify: false` makes two attributes mandatory** | `delimiter` and `quoted` must both be supplied for CSV, otherwise `8079`. |
| **Parsing attributes are CSV-only** | `delimiter`, `quoted`, and `commentChar` are ignored for JSON, XML, Excel, Parquet, and Geometry sources. |
| **Column-count ceiling** | A source with more columns than the table format permits fails with `7478`, and a row with more fields than expected fails with `7208`. |
| **No `criteria`** | Row selection is by file content and `skipTop` only. |
| **No callback** | Callback notification belongs to the asynchronous/bulk import APIs; the synchronous ones return everything inline. |
| **Dependency chain** | [Get Workspace List](WORKSPACE_OPERATIONS_API_DOC_INFO.md) → `<workspace-id>` → Import Data into a New Table (Synchronous) → `data.viewId` → [Import Data into an Existing Table (Synchronous)](#2-import-data-into-an-existing-table-synchronous), [Row APIs](ROW_API_DOC_INFO.md), [Get Columns](COLUMNS_API_DOC_INFO.md). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7092 | `DDL_LOCK_SINCE_IMPORT_IN_PROGRESS` — A batch import is holding a lock in this workspace. | Retry once the import has finished. |
| 7111 | `META_DBOBJECT_NAME_DUPLICATED` — An object with this `tableName` already exists in the workspace. | Choose a different name, or import into the existing table with [Import Data into an Existing Table (Synchronous)](#2-import-data-into-an-existing-table-synchronous). |
| 7208 | `IMPORT_FILE_NUMBER_OF_FIELDS_EXCEEDS_SIZE` — A row contains more fields than the header defines. | Correct the source data, or set the right `delimiter`. |
| 7232 | `IMPORT_ABORTED` — A value could not be parsed and `onError` is `ABORT`. `errorMessage` carries the per-line detail. | Fix the data, or resend with `onError` set to `SKIPROW` or `SETCOLUMNEMPTY`. |
| 7248 | `INVALID_FILE_CONTENT` — The payload could not be parsed as the declared `fileType`. | Check that `fileType` matches the actual content. |
| 7301 | `SECURITY_NOT_PERMITTED` — The user cannot create tables in this workspace. | Ensure the user is an Account Admin, Organization Admin, Workspace Admin, or has Create Table permission. |
| 7478 | `MORE_THAN_MAX_COLUMN` — The source has more columns than a table can hold. | Reduce the columns, or use `selectedColumns` to import a subset. |
| 7512 | `INVALID_DATE_FORMAT` — A pattern in `dateFormat` / `columnDateFormat` could not be parsed. | Supply a valid date pattern such as `dd-MMM-yyyy`. |
| 8046 | `INVALID_COLUMNS_SELECTED` — A name in `selectedColumns` is not present in the source data. | Match the names to the source's header row. |
| 8079 | `ATTRIBUTE_NOT_PRESENT_IN_JSON_CONFIGURATION` — A mandatory attribute is missing; with `autoIdentify: false` this is usually `delimiter` or `quoted`. | The message names the attribute. |
| 8119 | `INVALID_VALUE_FOR_ATTRIBUTE` — `fileType`, `onError`, `delimiter`, `quoted`, `thousandSeparator`, or `decimalSeparator` is outside its permitted set. | The message names the attribute and the allowed values. |
| 8139 | `PASTED_DATA_LIMIT_EXCEEDED` — The `DATA` parameter exceeds 10,000,000 characters. | Send the payload as a `FILE` upload instead. |
| 8148 | `DECIMAL_AND_THOUSAND_SEPARATOR_SAME` — The thousand and decimal separators resolve to the same character. | Choose different separators. |
| 8149 | `DECIMAL_AND_THOUSAND_COLUMN_SEPARATOR_LEGNTH_VALIDATION` — A `columnSeparators` entry has fewer than two values. | Send `[thousandSeparator, decimalSeparator]` for each column. |
| 8504 | `LESS_THAN_MIN_OCCURANCE` — `CONFIG` was not sent, or a mandatory key is missing at the template level. | Send a complete CONFIG object. |
| 8516 | `UNABLE_TO_PARSE_DATA_TYPE` — A CONFIG value has the wrong JSON type. | Check that booleans are booleans and integers are integers. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.data.create`. |

---

## 2. Import Data into an Existing Table (Synchronous)

Loads the uploaded data into an existing table, appending, replacing, or merging according to `importType`.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/data` |
| **OAuth Scope** | `ZohoAnalytics.data.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin, or any user holding the import permission that matches the requested `importType` — see [Permission Model](#permission-model). |

### CONFIG Parameters

CONFIG is **mandatory**. This API takes the same options as [Import Data into a New Table (Synchronous)](#1-import-data-into-a-new-table-synchronous), with `tableName` replaced by `importType` and `matchingColumns` added.

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `importType` | String (enum) | **Yes** | — | How the incoming rows are combined with the existing ones. See [`importType` Values](#importtype-values). Case-insensitive. |
| `fileType` | String (enum) | **Yes** | — | Format of the payload. See [`fileType` Values](#filetype-values). |
| `autoIdentify` | Boolean | **Yes** | — | As in the new-table import — when `false`, `delimiter` and `quoted` become mandatory for CSV. |
| `matchingColumns` | JSONArray of String | Conditional* | — | Columns used to match an incoming row against an existing one. 1–100 entries; every name must already exist in the table (`7107` otherwise). |
| `onError` | String (enum) | No | `ABORT` | See [`onError` Values](#onerror-values). |
| `selectedColumns` | JSONArray of String | No | all columns | Import only these columns from the source. 1–300 entries. |
| `skipTop` | Integer | No | `0` | Number of leading rows to ignore. |
| `delimiter` | Integer (enum) | Conditional | `0` | CSV field separator, `0`–`4`. Mandatory when `autoIdentify` is `false`. |
| `quoted` | Integer (enum) | Conditional | `2` | CSV quote character, `0`–`2`. Mandatory when `autoIdentify` is `false`. |
| `commentChar` | String | No | none | Lines starting with this character are ignored. CSV only. |
| `thousandSeparator` | Integer (enum) | No | auto | See [Number Separator Values](#number-separator-values). |
| `decimalSeparator` | Integer (enum) | No | auto | See [Number Separator Values](#number-separator-values). |
| `columnSeparators` | JSONObject | No | — | Per-column separator overrides. |
| `dateFormat` | String | No | auto | Default date pattern. |
| `columnDateFormat` | JSONObject | No | — | Per-column date pattern overrides. |
| `columnTimeFormat` | JSONObject | No | — | Per-column time pattern overrides. |
| `columnDurationFormat` | JSONObject | No | — | Per-column duration pattern overrides. |
| `columnDataTypes` | JSONArray | No | — | Explicit data types. **Entries naming a column that already exists in the table are discarded** — an existing column keeps its established type. |
| `matchNulls` | Boolean | No | `false` | Treat empty source values as nulls when matching rows. Relevant to `UPDATEADD`. |
| `updateNullForNegativeValues` | Boolean | No | `false` | Store null instead of a negative value in columns that do not accept one. |
| `retainColumnNames` | Boolean | No | `false` | For JSON/XML, keep the source's original key names. |
| `importHiddenRows` | Boolean | No | `false` | For Excel sources, include hidden rows. |
| `importHiddenColumns` | Boolean | No | `false` | For Excel sources, include hidden columns. |

\* `matchingColumns` is **mandatory** when `importType` is `UPDATEADD`, and ignored for `APPEND` and `TRUNCATEADD`.

#### `importType` Values

| Value | Behaviour | Needs `matchingColumns` |
|-------|-----------|-------------------------|
| `APPEND` | Adds every incoming row to the table, keeping all existing rows. | No |
| `TRUNCATEADD` | Deletes **all** existing rows, then adds the incoming ones. | No |
| `UPDATEADD` | Updates rows whose `matchingColumns` values match an incoming row; adds the rest as new rows. | **Yes** |

> These three modes are the complete supported set. Any other value is rejected with `8119`, whose message names the permitted values.

### Sample Requests

**Case 1 — Append a new batch of rows**

```http
POST /restapi/v2/workspaces/466206000000071000/views/466206000000776558/data HTTP/1.1
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
Content-Disposition: form-data; name="FILE"; filename="sales-march.csv"
Content-Type: text/csv

Date,Region,Product,Sales,Cost
01 March 2026,West,Fruits and Vegetables,4120.10,210.00
------ZohoBoundary--
```

**Case 2 — Merge updates by key, with parsing options clubbed together**

```http
POST /restapi/v2/workspaces/466206000000071000/views/466206000000776558/data HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: multipart/form-data; boundary=----ZohoBoundary

------ZohoBoundary
Content-Disposition: form-data; name="CONFIG"

{
    "importType": "UPDATEADD",
    "fileType": "CSV",
    "autoIdentify": false,
    "delimiter": 0,
    "quoted": 2,
    "matchingColumns": ["Region", "Product"],
    "matchNulls": true,
    "thousandSeparator": 0,
    "decimalSeparator": 0,
    "dateFormat": "dd MMM yyyy",
    "onError": "SETCOLUMNEMPTY"
}
------ZohoBoundary
Content-Disposition: form-data; name="FILE"; filename="sales-corrections.csv"
Content-Type: text/csv

...
------ZohoBoundary--
```

**Case 3 — Replace the table's contents entirely, using pasted data**

```http
POST /restapi/v2/workspaces/466206000000071000/views/466206000000776558/data HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "importType": "TRUNCATEADD",
    "fileType": "CSV",
    "autoIdentify": true,
    "selectedColumns": ["Region", "Sales"],
    "skipTop": 1
}&DATA=Region,Sales%0AWest,3928.38%0AEast,1250.00
```

**Case 4 — White Label / Client Portal workspace**

```http
POST /restapi/v2/workspaces/466206000000071009/views/466206000000776599/data HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "importType": "APPEND",
    "fileType": "CSV",
    "autoIdentify": true
}&DATA=Region,Sales%0AWest,3928.38
```

### Sample Responses

**HTTP 200 OK — Append into an existing table (Case 1)**

```json
{
    "status": "success",
    "summary": "Import data",
    "data": {
        "importSummary": {
            "importType": "APPEND",
            "totalColumnCount": 9,
            "selectedColumnCount": 9,
            "totalRowCount": 6,
            "successRowCount": 6,
            "warnings": 0,
            "importOperation": "updated"
        },
        "columnDetails": {
            "plainCol": "Plain Text",
            "emailCol": "E-Mail",
            "intCol": "Number",
            "numCol": "Positive Number",
            "decCol": "Decimal Number",
            "curCol": "Currency",
            "perCol": "Percentage",
            "dateCol": "Date",
            "boolCol": "Plain Text"
        },
        "importErrors": ""
    }
}
```

**HTTP 200 OK — `UPDATEADD` merge (Case 2)**

```json
{
    "status": "success",
    "summary": "Import data",
    "data": {
        "importSummary": {
            "importType": "UPDATEADD",
            "totalColumnCount": 9,
            "selectedColumnCount": 9,
            "totalRowCount": 6,
            "successRowCount": 6,
            "warnings": 0,
            "importOperation": "updated"
        },
        "columnDetails": {
            "plainCol": "Plain Text",
            "emailCol": "E-Mail",
            "intCol": "Number",
            "numCol": "Positive Number",
            "decCol": "Decimal Number",
            "curCol": "Currency",
            "perCol": "Percentage",
            "dateCol": "Date",
            "boolCol": "Plain Text"
        },
        "importErrors": ""
    }
}
```

**HTTP 200 OK — Rows loaded with per-value warnings**

```json
{
    "status": "success",
    "summary": "Import data",
    "data": {
        "importSummary": {
            "importType": "TRUNCATEADD",
            "totalColumnCount": 5,
            "selectedColumnCount": 5,
            "totalRowCount": 100,
            "successRowCount": 100,
            "warnings": 3,
            "importOperation": "updated"
        },
        "columnDetails": {
            "Region": "Plain Text",
            "State": "Geo Column",
            "Sales": "Currency",
            "Cost": "Currency",
            "Date": "Date"
        },
        "importErrors": "<nobr>[Line: 6 Field:  4] (andhara pradesh) -WARNING: Invalid GEO LOCATION</NOBR><br><nobr>[Line: 7 Field:  4] (utter pradesh) -WARNING: Invalid GEO LOCATION</NOBR><br>"
    }
}
```

**HTTP 400 Bad Request — A name in `matchingColumns` does not exist in the table**

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
| `summary` | String | Localised operation summary. `"Import data"`. |
| `data` | JSONObject | Response payload wrapper. |
| `data.importSummary` | JSONObject | Counts describing what was loaded — same shape as in [Import Data into a New Table (Synchronous)](#1-import-data-into-a-new-table-synchronous). |
| `importSummary.importType` | String | The `importType` that was applied, in **upper case**. |
| `importSummary.totalColumnCount` | Number | Columns found in the source data. |
| `importSummary.selectedColumnCount` | Number | Columns actually imported. |
| `importSummary.totalRowCount` | Number | Data rows found in the source. |
| `importSummary.successRowCount` | Number | Rows actually written. |
| `importSummary.warnings` | Number | Count of values reset or flagged during the load. |
| `importSummary.importOperation` | String | Always `"updated"` for this API — an existing table was written to rather than created. |
| `data.columnDetails` | JSONObject | Column name → assigned data type label. For an existing table these are the table's established types. |
| `data.importErrors` | String | Per-line warnings and resets as an HTML fragment. Always present; `""` when clean. |

> **`viewId` is not returned by this API** — the target table's ID was already supplied in the URL.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **The required permission depends on `importType`** | This is the behaviour most likely to produce an unexpected `7301`. Append, truncate-and-add, and add-or-update are four *separate* permissions, so a user who can append may still be refused a truncate. See [Permission Model](#permission-model). |
| **`TRUNCATEADD` deletes first** | Every existing row is removed before the incoming rows are written. If the import then fails mid-way, the table can be left with fewer rows than it started with. There is no dry-run. |
| **`UPDATEADD` requires `matchingColumns`** | Without it the call fails; with a name that is not a real column it fails with `7107`. The match is on the named columns' values, not on any row ID. |
| **Existing columns keep their types** | `columnDataTypes` entries that name a column already present in the table are dropped, so this attribute only influences columns the import is adding. |
| **`onError: "ABORT"` is still the default** | A single unparseable value aborts the whole import and rolls it back. |
| **A clean HTTP 200 is not a clean import** | Compare `successRowCount` with `totalRowCount` and check `warnings`. |
| **The table is DDL-locked during the import** | Concurrent structural changes are blocked while the load runs, and a load attempted while another import holds the lock fails with `7092`. |
| **Snapshot and system tables are rejected** | `7165` and `7164` respectively — see [Table Preconditions](#table-preconditions-existing-table-import). |
| **No `criteria`** | Which rows are affected is decided by `importType` and `matchingColumns`, not by a filter expression. |
| **Dependency chain** | [Import Data into a New Table (Synchronous)](#1-import-data-into-a-new-table-synchronous) or [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → `<view-id>` → [Get Columns](COLUMNS_API_DOC_INFO.md) (to pick `matchingColumns`) → Import Data into an Existing Table (Synchronous). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7092 | `DDL_LOCK_SINCE_IMPORT_IN_PROGRESS` — Another import is holding a DDL lock on this table. | Retry once it has finished. |
| 7104 | `META_OBJECT_NOT_PRESENT` — The view does not exist. | Verify `<view-id>`. |
| 7107 | `META_OBJECT_NOT_PRESENT` — A column named in `matchingColumns` is not present in the table. | Verify the names via [Get Columns](COLUMNS_API_DOC_INFO.md). |
| 7164 | `SYSTEM_TABLE_DATA_MOD` — System table data cannot be modified. | Target a user-created table instead. |
| 7165 | `SNAPSHOT_TABLE_DATAMOD` — Snapshot table data cannot be modified. | Target a non-snapshot table. |
| 7208 | `IMPORT_FILE_NUMBER_OF_FIELDS_EXCEEDS_SIZE` — A row contains more fields than expected. | Correct the source data or the `delimiter`. |
| 7232 | `IMPORT_ABORTED` — A value could not be parsed and `onError` is `ABORT`. | Fix the data, or resend with `SKIPROW` / `SETCOLUMNEMPTY`. |
| 7248 | `INVALID_FILE_CONTENT` — The payload could not be parsed as the declared `fileType`. | Check that `fileType` matches the content. |
| 7301 | `SECURITY_NOT_PERMITTED` — The user lacks the import permission matching `importType`, or is outside the workspace's permitted IP range. | Grant the specific import permission (see [Permission Model](#permission-model)), or use an `importType` the user is allowed. |
| 7319 | `OBJID_NOT_BELONGS_TO_DB` — The table does not belong to the specified workspace. | Ensure `<workspace-id>` and `<view-id>` are consistent. |
| 7478 | `MORE_THAN_MAX_COLUMN` — The source has more columns than the table can hold. | Reduce the columns, or use `selectedColumns`. |
| 7512 | `INVALID_DATE_FORMAT` — A date pattern could not be parsed. | Supply a valid pattern. |
| 8046 | `INVALID_COLUMNS_SELECTED` — A name in `selectedColumns` is not present in the source data. | Match the names to the source's header row. |
| 8079 | `ATTRIBUTE_NOT_PRESENT_IN_JSON_CONFIGURATION` — A mandatory attribute is missing — commonly `matchingColumns` for `UPDATEADD`, or `delimiter`/`quoted` when `autoIdentify` is `false`. | The message names the attribute. |
| 8119 | `INVALID_VALUE_FOR_ATTRIBUTE` — `importType`, `fileType`, `onError`, `delimiter`, `quoted`, `thousandSeparator`, or `decimalSeparator` is outside its permitted set. | The message names the attribute and the allowed values. |
| 8139 | `PASTED_DATA_LIMIT_EXCEEDED` — The `DATA` parameter exceeds 10,000,000 characters. | Send the payload as a `FILE` upload instead. |
| 8148 | `DECIMAL_AND_THOUSAND_SEPARATOR_SAME` — The thousand and decimal separators are the same character. | Choose different separators. |
| 8149 | `DECIMAL_AND_THOUSAND_COLUMN_SEPARATOR_LEGNTH_VALIDATION` — A `columnSeparators` entry has fewer than two values. | Send `[thousandSeparator, decimalSeparator]` per column. |
| 8504 | `LESS_THAN_MIN_OCCURANCE` — `CONFIG` was not sent, or a mandatory key is missing. | Send a complete CONFIG object. |
| 8516 | `UNABLE_TO_PARSE_DATA_TYPE` — A CONFIG value has the wrong JSON type. | Check booleans and integers are sent as such. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.data.create`. |

---

## Appendix A – Common HTTP Headers

| Header | Value | Required | Description |
|--------|-------|----------|-------------|
| `Authorization` | `Zoho-oauthtoken <oauth-token>` | **Mandatory** | OAuth 2.0 access token of the calling user, carrying `ZohoAnalytics.data.create`. |
| `ZANALYTICS-ORGID` | Organization ID string | **Mandatory** | Organization ID of the workspace being imported into. |
| `Content-Type` | `multipart/form-data; boundary=…` | Conditional | Required when sending the payload as a `FILE` upload. |
| `Content-Type` | `application/x-www-form-urlencoded` | Conditional | Required when sending the payload in the `DATA` parameter. |

> **`ZANALYTICS-DEST-ORGID` is not used by either API.** That header applies only to cross-organization copy operations (Copy Workspace, [Copy Views](VIEW_OPERATIONS_API_DOC_INFO.md#2-copy-views), Copy Formulas).

Example (pasted data into a new table):

```http
POST /restapi/v2/workspaces/466206000000071000/data HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG=%7B%22tableName%22%3A%22SalesData%22%2C%22fileType%22%3A%22CSV%22%2C%22autoIdentify%22%3Atrue%7D&DATA=Region%2CSales%0AWest%2C3928.38
```

---

## Appendix B – OAuth Scope Summary

| API | HTTP Method | Scope |
|-----|-------------|-------|
| Import Data into a New Table (Synchronous) | POST | `ZohoAnalytics.data.create` |
| Import Data into an Existing Table (Synchronous) | POST | `ZohoAnalytics.data.create` |

> Both use the **same** scope, including the existing-table import — which writes into, and with `TRUNCATEADD` deletes from, an existing table. The scope follows the HTTP method (`POST` → `create`), while the destructiveness of the operation is governed by the per-`importType` **permission** instead. A token scoped for `data.create` alone is therefore enough to empty a table via `TRUNCATEADD`, provided the user holds the matching permission.

---

## Appendix C – API-Specific Notes and Behaviours

### Import Data into a New Table (Synchronous)

- **It is the only source of the new table's `viewId`.** Everything downstream — further imports, [Row APIs](ROW_API_DOC_INFO.md), exports, sharing — needs that ID, and it appears in no other response. Capture it from `data.viewId` on the very first call.
- **Create-once, by design.** A second call with the same `tableName` fails with `7111` rather than appending. The API deliberately refuses to guess whether you meant "create" or "load more"; the latter is [Import Data into an Existing Table (Synchronous)](#2-import-data-into-an-existing-table-synchronous).
- **`onError` defaults to the strictest setting.** `ABORT` means one bad cell in a 100,000-row file leaves you with no table and a `7232`. For unattended loading, choose `SKIPROW` or `SETCOLUMNEMPTY` deliberately and then read `importErrors`.
- **`columnDetails` is the type-inference report, and it matters most here.** A new table's column types are decided by this one call and are awkward to change afterwards. When `autoIdentify` is `true`, always check that `Sales` came back as `Currency` rather than `Plain Text` — a wrong `thousandSeparator` is the usual cause.
- **`autoIdentify: false` turns two optional attributes into mandatory ones.** `delimiter` and `quoted` must both be present for CSV, and their absence surfaces as `8079` rather than as a validation message about `autoIdentify`.
- **HTTP 200 does not mean every row landed.** `successRowCount` and `warnings` are the real success indicators.
- **Dependency chain:** [Get Workspace List](WORKSPACE_OPERATIONS_API_DOC_INFO.md) → Import into a New Table → `data.viewId` → everything else.

### Import Data into an Existing Table (Synchronous)

- **Its permission requirement is a function of `importType`.** Four import modes map to four distinct permissions, so `7301` here means "not allowed to do *this kind* of import", not "not allowed to import". This is the single most common source of confusion with this API — check the [Permission Model](#permission-model) table before assuming a token or role problem.
- **`TRUNCATEADD` is destructive and unguarded.** It deletes every existing row before writing, with no dry-run, no confirmation, and no row-level trash. Combined with `onError: "ABORT"`, a malformed file can leave the table emptier than it started.
- **`UPDATEADD` matches on values, not identity.** `matchingColumns` names the columns whose values form the key; there is no row ID involved. A column name that does not exist fails with `7107`, and `matchNulls` decides whether empty source values participate in the match.
- **It cannot change an existing column's type.** `columnDataTypes` entries for columns already in the table are silently discarded, so this attribute only affects columns the import introduces.
- **No `viewId` in the response**, since the destination was already known — the response is otherwise identical to that of [Import Data into a New Table (Synchronous)](#1-import-data-into-a-new-table-synchronous).
- **The table is DDL-locked for the duration**, so concurrent structural changes are blocked and a competing import fails with `7092`.
- **Dependency chain:** [Import Data into a New Table (Synchronous)](#1-import-data-into-a-new-table-synchronous) or [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → `<view-id>` → [Get Columns](COLUMNS_API_DOC_INFO.md) → Import Data into an Existing Table (Synchronous).

---

## Appendix D – General Response Payload Notes

| Field / Behaviour | Detail |
|-------------------|--------|
| **Both APIs return HTTP 200 with a body** | Neither returns 204. The full import result — counts, detected types, and per-line errors — is delivered inline, because these are the synchronous imports. |
| **Failure responses share one shape** | `{"status": "failure", "summary": "<ERROR_NAME>", "data": {"errorCode": <n>, "errorMessage": "<text>"}}`. `summary` on failure is the error's symbolic name (e.g. `IMPORT_ABORTED`), not a localised sentence. |
| **`summary` is `"Import data"` for both** | The success summary does not distinguish new-table from existing-table imports. Use the presence of `viewId`, or `importSummary.importOperation`, to tell them apart. |
| **`importOperation` is the discriminator** | `"created"` from the new-table import, `"updated"` from the existing-table import. It is the only field in `importSummary` that differs structurally between the two APIs. |
| **`viewId` is conditionally present** | Returned only by the new-table import. Test for the key rather than assuming it. |
| **A 200 can still hide data loss** | `successRowCount < totalRowCount` means rows were skipped; `warnings > 0` means values were reset to empty. Neither raises an error, so both must be checked explicitly. |
| **`importErrors` is HTML, not data** | It is a fragment of `<nobr>…</NOBR><br>` markup describing each offending line, field, and value. Display or log it — do not parse it. It is always present, empty (`""`) when the import was clean. |
| **`columnDetails` uses display labels, not type codes** | Values are human-readable names such as `"Plain Text"`, `"Positive Number"`, `"Decimal Number"`, `"Currency"`, `"Percentage"`, `"Date"`, `"E-Mail"`, `"URL"`, `"Geo Column"` — not the `dataType` codes accepted by `columnDataTypes` on the request side. The two vocabularies do not round-trip. |
| **Counts are native numbers** | `totalColumnCount`, `selectedColumnCount`, `totalRowCount`, `successRowCount`, and `warnings` are genuine JSON numbers; `viewId` is a string. |
| **`importType` is echoed in upper case** | Regardless of the casing sent, and including the synthetic `"APPEND"` reported by the new-table import. |
