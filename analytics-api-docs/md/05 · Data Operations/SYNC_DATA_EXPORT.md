# Zoho Analytics V2 REST API — Synchronous Data Export

This document covers the **synchronous data export** REST API of Zoho Analytics — the API that reads a view and streams the exported file back in the same HTTP response.

## What is a "Synchronous" export?

This API returns **the exported file itself** as the response body. There is no job to create, no status to poll, and no download link to follow: when the call returns, the bytes of the CSV, JSON, XML, XLS, PDF, HTML, or image file are already in your hands.

That convenience is also its constraint. Because the file must be produced inside a single request, the API is deliberately restricted to views that can be rendered quickly — see [Limitations](#limitations).

| | Synchronous export (this document) | Asynchronous export |
|---|---|---|
| **Endpoint** | `GET /workspaces/<id>/views/<id>/data` | `GET /bulk/workspaces/<id>/views/<id>/data` |
| **Response body** | The exported file | A JSON envelope containing a `jobId` |
| **Number of calls** | One | Create the job, poll it, then download |
| **Dashboards, Query Tables, live-connect views** | Not supported | Supported |
| **Tables above the row limit** | Not supported | Supported |
| **`callbackUrl`** | Not supported | Supported |

---

## Index

| # | API Name | Method | URL |
|---|----------|--------|-----|
| 1 | [Export Data from a View](#1-export-data-from-a-view) | GET | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/data` |

> **Note on naming:** This API is published as **"Export Data from a View"**. It is the view-scoped synchronous export. A sibling endpoint, `GET /restapi/v2/workspaces/<workspace-id>/data`, exports the result of an ad-hoc SQL query instead of a saved view; it takes a different CONFIG (built around a `sqlQuery` attribute) and is documented separately.

---

## How This API Relates to the Other APIs

This API is a **terminal consumer**: it produces a file and changes nothing. Everything it needs is an ID or a name produced by some other API.

```
 [Get View List]  ─────────────────►  <view-id>
        │                                  │
        │                                  ▼
 [Get Columns] ──► column display names ──►  1. Export Data from a View
        │              (selectedColumns)     (GET .../views/<view-id>/data)
        │                                  │
        │                                  ├──► CSV / JSON / XML / XLS
        │                                  ├──► PDF / HTML
        │                                  └──► PNG / JPEG (charts only)
        │
        └──► Sharing decides whether the caller has Export permission at all
```

| Relationship | Detail |
|--------------|--------|
| **`<view-id>` comes from elsewhere** | This API never returns a view ID; it consumes one. Get it from [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list), or from the response of [Import Data into a New Table (Synchronous)](SYNC_DATA_IMPORT_API_DOC_INFO.md#1-import-data-into-a-new-table-synchronous), or from [Create Query Table](QUERY_TABLES_API_DOC_INFO.md#2-create-query-table). |
| **`selectedColumns` takes column *display names*, not IDs** | Fetch them with [Get Columns](COLUMNS_API_DOC_INFO.md). A name that does not match any column in the view fails with `8015` — the whole export fails, nothing partial is returned. |
| **Export permission is granted by the sharing APIs** | The `export` share permission set by [Share Views](SHARING_API_DOC_INFO.md#2-share-views) is exactly the permission this API checks. See [Permission Model](#permission-model). |
| **Hidden and personal-data columns are decided at design time** | Whether a column is hidden, or marked as personal data, is set through the column APIs; this export only chooses whether to *include* such columns. See [Get Columns](COLUMNS_API_DOC_INFO.md). |
| **`criteria` shares its grammar with the Row APIs** | The same filter-expression syntax used by [Update Row](ROW_API_DOC_INFO.md#2-update-row) and [Delete Row](ROW_API_DOC_INFO.md#3-delete-row) applies here — see [`criteria` Syntax](#criteria-syntax). |
| **Restricted views must go through the asynchronous export** | Dashboards, Query Tables, live-connect views, and large tables are rejected here with `8133`. They are handled by the bulk export APIs under `/restapi/v2/bulk/...`. |
| **The same export settings drive Email Schedules** | Page setup, paper size, margins, header/footer slots, and `exportLanguage` carry the same meanings and the same value sets in [Create Email Schedule](EMAIL_SCHEDULES_API_DOC_INFO.md#2-create-email-schedule). A page layout tuned here can be reused there. |
| **It has no reverse operation** | Export is read-only. Getting data *into* a table is [Synchronous Data Import](SYNC_DATA_IMPORT_API_DOC_INFO.md) or [Asynchronous & Batch Data Import](ASYNC_DATA_IMPORT_API_DOC_INFO.md). |

### Typical sequences

**Export one report as a filtered CSV**

```
[Get View List] → <view-id> → Export Data from a View
                              CONFIG={"responseFormat":"csv","criteria":"..."}
```

**Export a chart as a PNG for embedding in a report**

```
[Get View List] → <view-id> of a chart → Export Data from a View
                                         CONFIG={"responseFormat":"image","imageFormat":"png"}
```

**Export only three columns of a table, password protected**

```
[Get Columns] → column display names → Export Data from a View
                                       CONFIG={"selectedColumns":[...],"password":"..."}
```

---

## Limitations

These are the limits that apply to this API with **default settings**.

### Views that cannot be exported synchronously

| Restriction | Behaviour |
|-------------|-----------|
| **Tables with more than 1,000,000 rows** | Rejected with `8133`. Use the asynchronous export instead. |
| **Dashboards** (including dashboard tabs) | Rejected with `8133`. |
| **Query Tables** | Rejected with `8133`. |
| **Views belonging to a live-connect workspace** | Rejected with `8133`. |

All four are checked **before** any CONFIG validation, so a request that trips one of them fails with `8133` even if the CONFIG is also malformed.

### Format restrictions

| Restriction | Behaviour |
|-------------|-----------|
| **`image` is only valid for chart views** | Any other view type fails with `8014`. |
| **`imageFormat` accepts only `png`, `jpg`, `jpeg`** | Anything else fails with `8017`. |
| **Image width must be 250–2000 px, height 200–2000 px** | Outside that range fails with `7803`. |
| **`selectedColumns` is honoured only for tables and tabular views** | For charts, pivots, and summary views the attribute is accepted and ignored — the view's own column layout decides what is exported. |

### Size and volume limits

| Limit | Value | Error |
|-------|-------|-------|
| Total exported payload | 100 MB | `7830` |
| PDF cells (visible columns × rows) | 1,000,000 | `7827` |
| XLS rows per sheet | 65,536 | `7806` |
| XLS columns per sheet | 256 | `7807` |
| XLS characters per cell | 32,767 | `7808` |
| `CONFIG` length | 100,000 characters | `8507` |
| `selectedColumns` entries | 1–300 | `8547` |
| `password` length | 6–256 characters | `8188` |

### Attributes that belong to other export APIs

The following are **not** applicable to this API, because the views or features they configure are not reachable here:

| Attribute | Why it does nothing here |
|-----------|--------------------------|
| `callbackUrl` | Callbacks exist only for the asynchronous export; this API has no job to notify about. |
| `generateTOC`, `dashboardLayout`, `zoomFactor` | Dashboard-only page-setup attributes. Dashboards cannot be exported synchronously. |

---

## Permission Model

| API | Who may call it |
|-----|-----------------|
| [Export Data from a View](#1-export-data-from-a-view) | An Account Admin or Organization Admin, or a Workspace Admin, or the View Owner, or any user with **Export** permission on the view. |

Two further gates apply on top of the permission check:

| Gate | Behaviour |
|------|-----------|
| **Verified email** | The calling user's primary email address must be verified, otherwise `7565`. |
| **Organization security controls** | If the organization has disabled export, every call fails with `8088`, regardless of the caller's role or permissions. |

Two attributes behave differently depending on whether the caller administers the workspace:

| Attribute | Account Admin / Organization Admin / Workspace Admin | Any other user |
|-----------|------------------------------------------------------|----------------|
| `showPersonalCols` | Honoured. Default `false`, so columns marked as personal data are **excluded** unless you ask for them. | Ignored. Personal-data columns are included, because a shared user only ever sees the columns already shared to them. |
| `criteria` | Applied as sent. | Applied, then **ANDed** with the share filter criteria configured for that user. A shared user can never widen their slice of the table with a broad `criteria`. |

---

## `criteria` Syntax

`criteria` is a SQL-like filter expression that selects which rows are exported. Column names are quoted with double quotes and string literals with single quotes:

```
"Region"='East'
"SalesTable"."Region"='East'
"Sales">1000 and "Region"='West'
"Region" in ('East','West') and "Order Date">='01-Jan-2026'
```

Notes that matter in practice:

- Omitting `criteria` exports **every row** the caller is entitled to see.
- A column named in `criteria` must exist in the view, otherwise the request fails with `7330`.
- A table name that is not part of the view fails with `7332`.
- A syntactically malformed expression fails with `7331`; an expression that parses but cannot be converted to SQL fails with `7327`.
- Aggregate functions (`sum`, `avg`, `count`, …) are not permitted in `criteria` — they fail with `7333`.
- For a **tabular view**, only columns of its own base table may be referenced; anything else fails with `7543`.
- For a **shared user**, the share filter criteria is ANDed automatically — see [Permission Model](#permission-model).
- Because `criteria` travels inside the `CONFIG` query parameter, it must be JSON-escaped and then URL-encoded. Double quotes around column names become `\"` in JSON and `%22` on the wire.
- When `responseFormat` is `json` or `xml` with `keyValueFormat` set to `false`, the criteria you sent is echoed back in the response envelope.

---

## 1. Export Data from a View

Exports the data of a view and returns the generated file in the response body.

| Attribute | Value |
|-----------|-------|
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/data` |
| **HTTP Method** | `GET` |
| **OAuth Scope** | `ZohoAnalytics.data.read` |
| **Mandatory Header** | `ZANALYTICS-ORGID` |
| **CONFIG** | Optional — omitting it exports the whole view as CSV with defaults |
| **Success Status** | `200 OK`, body is the exported file |
| **Content-Type** | Varies with `responseFormat` — see [Response Structure by Format](#response-structure-by-format) |

**Path parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `<workspace-id>` | Long | ID of the workspace that owns the view. |
| `<view-id>` | Long | ID of the view to export. Must belong to `<workspace-id>`, otherwise the call fails. |

Because this is a `GET`, `CONFIG` is passed as a **query parameter** holding a stringified, URL-encoded JSON object:

```
GET /restapi/v2/workspaces/466206000000071000/views/466206000000072000/data?CONFIG=%7B%22responseFormat%22%3A%22csv%22%7D
```

### CONFIG Parameters — Common to Every Format

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `responseFormat` | String | No | `"csv"` | Output format. One of `csv`, `json`, `xml`, `xls`, `pdf`, `html`, `image` (case-insensitive). Any other value fails with `8001`. |
| `criteria` | String | No | — | Filter expression selecting the rows to export. Omit to export every row. See [`criteria` Syntax](#criteria-syntax). |
| `password` | String | No | — | Protects the exported file with a password. Minimum 6 characters, maximum 256; shorter values fail with `8188`. Changes the delivery format — see [Password Protection](#password-protection). |
| `selectedColumns` | JSONArray of String | No | — | Column **display names** to export, in the order given, 1–300 entries. Only honoured for tables and tabular views. An unmatched name fails with `8015`. Omit to export all eligible columns. |
| `showHiddenCols` | Boolean | No | `true` (`false` for `html`) | Whether columns hidden in the view are included. A column named explicitly in `selectedColumns` is always included, hidden or not. |
| `showPersonalCols` | Boolean | No | `false` | Whether columns marked as personal data are included. Honoured only for Account Admins, Organization Admins, and Workspace Admins — see [Permission Model](#permission-model). |
| `includeHeader` | Boolean | No | `true` | Whether a header row of column names is written. Applies to `csv`, `xls`, `pdf`, and `html`. |
| `includeRowNums` | Boolean | No | `false` | Prefixes each record with a sequential `Row Number` value. |
| `includeRowIds` | Boolean | No | `false` | Equivalent to `includeRowNums` — both feed the same switch, so sending either one enables the row-number column. |
| `applyDefaultUF` | Boolean | No | `false` | Applies the view's saved default user filters before exporting. Meaningful for tabular views. |
| `validateSystemTags` | Boolean | No | `true` | When `true`, the request is rejected with `8241` if the view carries a restricted **DATA_WARNING** system tag — applied directly, or inherited through lineage from a parent data source or table. Send `false` to acknowledge the warning and proceed. Only relevant when System Tags are enabled for the organization. |

### CONFIG Parameters — CSV Specific

Applicable when `responseFormat` is `csv`.

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `delimiter` | Integer | No | `0` (comma) | Field separator. `0` Comma, `1` Tab, `2` Semicolon, `3` Space, `4` Pipe. Any other value fails with `8119`. |
| `recordDelimiter` | Integer | No | `0` (DOS) | Line ending. `0` DOS (`\r\n`), `1` UNIX (`\n`), `2` MAC (`\r`). Any other value fails with `8119`. |
| `quoted` | Integer | No | — | Text qualifier wrapped around values. `0` single quote, `1` double quote. Omit for no qualifier. Any other value fails with `8119`. |

### CONFIG Parameters — JSON and XML Specific

Applicable when `responseFormat` is `json` or `xml`.

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `keyValueFormat` | Boolean | No | `true` for `json`, `false` for `xml` | Chooses the record shape. `true` emits each row as column-name/value pairs; `false` emits a wrapped envelope with a separate column list and rows as positional arrays. The two shapes are structurally different — see [Response Structure by Format](#response-structure-by-format). |

### CONFIG Parameters — PDF Specific

Applicable when `responseFormat` is `pdf`.

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `paperSize` | Integer | No | `4` (A4) | `0` Letter, `1` Legal, `2` Tabloid, `3` A3, `4` A4, `5` Auto-fit width. Outside `0`–`5` fails with `8119`. |
| `paperStyle` | String | No | `"Portrait"` | `"Portrait"` or `"Landscape"` (case-insensitive). Anything else fails with `8119`. |
| `topMargin` | Float | No | `0.25` | Top margin in inches, `0`–`1` inclusive. Outside that range fails with `7801`. |
| `bottomMargin` | Float | No | `0.25` | Bottom margin in inches, `0`–`1`. |
| `leftMargin` | Float | No | `0.25` | Left margin in inches, `0`–`1`. |
| `rightMargin` | Float | No | `0.25` | Right margin in inches, `0`–`1`. |
| `showTitle` | Integer | No | `0` (top) | Where the view title is placed. `0` Top, `1` Bottom, `2` Do not include. Outside `0`–`2` fails with `8119`. |
| `showDesc` | Integer | No | `0` (top) | Where the view description is placed. `0` Top, `1` Bottom, `2` Do not include. |
| `columnWidthRatio` | Integer | No | `1` | Column sizing. `0` proportional to the widths set in the view, `1` sized to content, `2` all columns equal. Outside `0`–`2` fails with `8119`. |
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

The same six values apply to every one of the six slots.

| Value | Content placed in the slot |
|-------|----------------------------|
| `0` | Blank |
| `1` | View title |
| `2` | Export date |
| `3` | Page number |
| `4` | Page number with total (`3 of 12`) |
| `5` | The custom text from the matching `…Text` attribute |
| `6` | Logo |

Any other value fails with `8119`. When a slot is set to `1`, the view's own title is substituted and the matching `…Text` attribute is ignored.

### CONFIG Parameters — HTML Specific

Applicable when `responseFormat` is `html`.

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `includeTitle` | Integer | No | `0` (top) | Where the view title is placed. `0` Top, `1` Bottom, `2` Do not include. Outside `0`–`2` fails with `8119`. |
| `includeDesc` | Integer | No | `0` (top) | Where the view description is placed. `0` Top, `1` Bottom, `2` Do not include. |
| `columnWidthRatio` | Integer | No | `2` | Column sizing. `0` proportional to the widths set in the view, `1` sized to content, `2` all columns equal. Note the default differs from PDF. |

### CONFIG Parameters — Image Specific

Applicable when `responseFormat` is `image`. Valid **only for chart views**; any other view type fails with `8014`.

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `imageFormat` | String | No | `"png"` | `"png"`, `"jpg"`, or `"jpeg"` (case-insensitive). Anything else fails with `8017`. |
| `width` | Integer | No | `500` | Image width in pixels, `250`–`2000`. Outside that range fails with `7803`. |
| `height` | Integer | No | `400` | Image height in pixels, `200`–`2000`. Outside that range fails with `7803`. |
| `title` | Boolean | No | `false` | Whether the chart title is drawn on the image. |
| `description` | Boolean | No | `false` | Whether the chart description is drawn on the image. |
| `legend` | Boolean | No | `true` | Whether the chart legend is drawn on the image. |

### CONFIG Parameters — XLS

`xls` takes no format-specific attributes. It uses the common set: `selectedColumns`, `includeHeader`, `showHiddenCols`, `showPersonalCols`, `includeRowNums`, `criteria`, and `password`.

### Password Protection

Sending `password` changes **how** the file is delivered, not only whether it is locked:

| `responseFormat` | Result when `password` is sent |
|------------------|--------------------------------|
| `csv`, `json`, `xml`, `html`, `image` | The file is placed inside a **password-protected ZIP archive**. The response `Content-Type` becomes `application/zip`. |
| `xls` | The workbook itself is encrypted. `Content-Type` stays `application/vnd.ms-excel`. |
| `pdf` | The PDF itself is encrypted, with printing and copying permitted. `Content-Type` stays `application/pdf`. |

A client that always writes the body to `export.csv` will therefore write a ZIP archive under a `.csv` name as soon as a password is added. Branch on the response `Content-Type`.

### Sample Requests

For readability the `CONFIG` values below are shown as plain JSON. On the wire each must be stringified and URL-encoded, as in [Appendix A](#appendix-a--common-http-headers).

**Case 1 — `criteria` alone: export only the rows that match a filter**

```http
GET /restapi/v2/workspaces/466206000000071000/views/466206000000072000/data HTTP/1.1
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

The response is a CSV containing only the East-region rows. Every other attribute takes its default: comma-separated, DOS line endings, header row present, hidden columns included, personal-data columns excluded.

**Case 2 — a fully configured CSV export**

Covers column selection, the three CSV delimiter attributes, the row-number column, and password protection in one call.

```http
GET /restapi/v2/workspaces/466206000000071000/views/466206000000072000/data HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

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
  "password": "Zoho@123"
}
```

Because `password` is present, the body is a **ZIP archive** containing the tab-separated file, and `Content-Type` is `application/zip`.

**Case 3 — a fully configured PDF export**

Covers paper setup, all four margins, title and description placement, column sizing, language, and the header/footer slots.

```http
GET /restapi/v2/workspaces/466206000000071000/views/466206000000073000/data HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

```json
{
  "responseFormat": "pdf",
  "paperSize": 4,
  "paperStyle": "Landscape",
  "topMargin": 0.5,
  "bottomMargin": 0.5,
  "leftMargin": 0.25,
  "rightMargin": 0.25,
  "showTitle": 0,
  "showDesc": 2,
  "columnWidthRatio": 2,
  "exportLanguage": 0,
  "leftHeader": 1,
  "centerHeader": 0,
  "rightHeader": 2,
  "leftFooter": 5,
  "leftFooterText": "Confidential — Internal Use Only",
  "centerFooter": 4,
  "rightFooter": 0,
  "includeHeader": true
}
```

**Case 4 — JSON and XML with the two record shapes**

```json
{
  "responseFormat": "json",
  "keyValueFormat": true,
  "includeRowNums": false,
  "showHiddenCols": false
}
```

```json
{
  "responseFormat": "xml",
  "keyValueFormat": false,
  "selectedColumns": ["Region", "Sales"]
}
```

**Case 5 — a chart as an image**

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

**HTTP 200 OK — `responseFormat: "csv"`**

```
Content-Type: text/csv

Region,Product,Sales
East,Laptop,145000
East,Monitor,38200
East,Keyboard,4750
```

**HTTP 200 OK — `responseFormat: "json"`, `keyValueFormat: true` (the default)**

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

**HTTP 200 OK — `responseFormat: "json"`, `keyValueFormat: false`**

```json
{
  "response": {
    "uri": "/restapi/v2/workspaces/466206000000071000/views/466206000000072000/data",
    "action": "EXPORT",
    "criteria": "\"SalesTable\".\"Region\"='East'",
    "result": {
      "column_order": ["Region", "Product", "Sales"],
      "rows": [
        ["East", "Laptop", "145000"],
        ["East", "Monitor", "38200"]
      ]
    }
  }
}
```

**HTTP 200 OK — `responseFormat: "xml"`, `keyValueFormat: false` (the default)**

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<response uri="/restapi/v2/workspaces/466206000000071000/views/466206000000072000/data" action="EXPORT">
<result>
<rows>
<row>
<column name="Region">East</column>
<column name="Product">Laptop</column>
<column name="Sales">145000</column>
</row>
</rows>
</result>
</response>
```

**HTTP 200 OK — `responseFormat: "xml"`, `keyValueFormat: true`**

```xml
<result>
<rows>
<row>
<Region>East</Region>
<Product>Laptop</Product>
<Sales>145000</Sales>
</row>
</rows>
</result>
```

**HTTP 200 OK — `responseFormat: "csv"` with `includeRowNums: true`**

```
Row Number,Region,Product,Sales
1,East,Laptop,145000
2,East,Monitor,38200
```

**HTTP 200 OK — binary formats**

`xls`, `pdf`, and `image` return raw binary. Only the headers are meaningful to read:

```
Content-Type: application/pdf

%PDF-1.4
… binary …
```

**HTTP 400 Bad Request — the view cannot be exported synchronously**

```json
{
  "status": "failure",
  "summary": "SYNC_EXPORT_NOT_ALLOWED",
  "data": {
    "errorCode": 8133,
    "errorMessage": "This view cannot be exported synchronously. Use the asynchronous export API instead."
  }
}
```

**HTTP 400 Bad Request — a name in `selectedColumns` does not exist**

```json
{
  "status": "failure",
  "summary": "API_EXPORT_COLUMN_NOT_PRESENT",
  "data": {
    "errorCode": 8015,
    "errorMessage": "The column Revenue is not present in this view."
  }
}
```

**HTTP 400 Bad Request — `image` requested for a non-chart view**

```json
{
  "status": "failure",
  "summary": "API_IMAGE_RESPONSE_NOT_POSSIBLE",
  "data": {
    "errorCode": 8014,
    "errorMessage": "Image response is possible only for chart views."
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

### Response Structure by Format

| `responseFormat` | `Content-Type` | Body |
|------------------|----------------|------|
| `csv` | `text/csv` | Delimited text. Optional header row, optional leading `Row Number` field. |
| `json` (`keyValueFormat: true`) | `application/json` | `{"data":[ {…}, … ]}` — one object per row, keyed by column display name. |
| `json` (`keyValueFormat: false`) | `application/json` | `{"response":{"uri":…,"action":"EXPORT","result":{"column_order":[…],"rows":[[…]]}}}` |
| `xml` (`keyValueFormat: false`) | `application/xml` | `<?xml …?><response …><result><rows><row><column name="…">…</column></row></rows></result></response>` |
| `xml` (`keyValueFormat: true`) | `application/xml` | `<result><rows><row><ColumnName>…</ColumnName></row></rows></result>` — no XML declaration and no `<response>` wrapper. |
| `xls` | `application/vnd.ms-excel` | Binary workbook. |
| `pdf` | `application/pdf` | Binary PDF. |
| `html` | `text/html` | An HTML fragment containing the rendered table. |
| `image` | `image/png` or `image/jpeg` | Binary image. |
| any of the above **with `password`** | `application/zip`, or the native type for `xls` and `pdf` | See [Password Protection](#password-protection). |

### Response Fields

The success body is a file, not a JSON envelope, so there are structured fields to document only for the JSON and XML formats.

**JSON with `keyValueFormat: true` (the default for `json`)**

| Field | Type | Description |
|-------|------|-------------|
| `data` | Array | One entry per exported row, in export order. Empty when nothing matched `criteria`. |
| `data[].<Column Name>` | String | One key per exported column, named by its **display name** exactly as it appears in the view. Values are strings, including for numeric and date columns. |
| `data[].Row Number` | String | Present only when `includeRowNums` or `includeRowIds` is `true`. A sequential counter starting at `1`, written as the first key of each object. |

**JSON with `keyValueFormat: false`**

| Field | Type | Description |
|-------|------|-------------|
| `response` | Object | Envelope wrapping the whole payload. |
| `response.uri` | String | The request path that produced this export. |
| `response.action` | String | Always `"EXPORT"`. |
| `response.criteria` | String | Echo of the `criteria` that was applied. **Present only when a criteria was sent** — test for the key rather than assuming it. |
| `response.result` | Object | The data itself. |
| `response.result.column_order` | Array of String | Exported column display names, in the order the row arrays follow. When `includeRowNums` is `true`, `"Row Number"` is the first entry. |
| `response.result.rows` | Array of Array | One inner array per row, positionally aligned with `column_order`. All values are strings. |

**XML with `keyValueFormat: false` (the default for `xml`)**

| Element / Attribute | Description |
|---------------------|-------------|
| `<response>` | Root element. |
| `response/@uri` | The request path that produced this export. |
| `response/@action` | Always `EXPORT`. |
| `<result>` | Wrapper around the rows. |
| `<rows>` | Container of `<row>` elements. |
| `<row>` | One exported row. |
| `<column name="…">` | One per exported column. The `name` attribute carries the column display name; the element text carries the value. |

**XML with `keyValueFormat: true`**

| Element | Description |
|---------|-------------|
| `<result>` | Root element. There is **no** XML declaration and **no** `<response>` wrapper in this shape. |
| `<rows>` | Container of `<row>` elements. |
| `<row>` | One exported row. |
| `<ColumnName>` | One element per column, **named after the column itself**. Column names containing characters that are not valid in an XML element name make this shape unusable — prefer `keyValueFormat: false` for such views. |

**Response headers**

| Header | Description |
|--------|-------------|
| `Content-Type` | The only header that describes the payload. Set from `responseFormat`, or to `application/zip` when `password` wraps the file — see [Response Structure by Format](#response-structure-by-format). |
| `Content-Disposition` | **Not sent.** This API returns no filename suggestion, so the client must name the downloaded file itself. |

### Notes & Behaviour

| Behaviour | Detail |
|-----------|--------|
| **`CONFIG` is optional** | A bare `GET .../data` with no query string exports the entire view as CSV, comma-separated, with a header row, hidden columns included, and personal-data columns excluded. |
| **`responseFormat` is optional too** | Sending a `CONFIG` without `responseFormat` yields CSV. |
| **The response body is the file, not a wrapper** | Unlike every other API in this suite, a successful call returns no `status` / `summary` / `data` envelope. Only **failures** use the JSON envelope. A client must therefore branch on the HTTP status before attempting to parse the body as JSON. |
| **Restriction checks run before CONFIG validation** | A dashboard exported as `csv` fails with `8133`, not with a format error, because the view-type gate is evaluated first. |
| **An empty result is a success** | A `criteria` that matches nothing returns `200` with a header-only CSV, or `{"data":[]}`, or an empty `<rows/>`. It is not an error. |
| **All exported values are strings** | In both JSON shapes, numbers, dates, and currency values come back quoted, formatted per the column's display settings rather than as raw storage values. |
| **`includeRowIds` and `includeRowNums` are the same switch** | Sending either enables the leading `Row Number` field. Sending both is harmless. |
| **`showHiddenCols` defaults differ by format** | `true` for `csv`, `json`, `xml`, `xls`, and `pdf`; `false` for `html`. Set it explicitly when the same integration produces more than one format. |
| **`columnWidthRatio` defaults differ by format** | `1` for `pdf`, `2` for `html`. Same value set, different default. |
| **`selectedColumns` overrides `showHiddenCols` for the columns it names** | A hidden column listed in `selectedColumns` is exported even when `showHiddenCols` is `false`. |
| **`selectedColumns` also sets the column order** | Columns come out in the order listed, not in the view's own order. |
| **`password` shorter than 6 characters is rejected outright** | `8188` fires during validation, before any data is read. |
| **The whole export is atomic from the caller's point of view** | Because validation happens up front and the file is streamed afterwards, a validation failure yields a clean JSON error and no partial file. A size limit tripped mid-stream (`7830`) resets the buffer and returns the error instead. |
| **Personal-data handling is role-dependent** | For a non-administering caller, `showPersonalCols` is ignored and personal columns are included. Do not rely on this attribute as a redaction mechanism for shared users — see [Permission Model](#permission-model). |
| **Dashboard-only page-setup attributes are silently ignored** | `generateTOC`, `dashboardLayout`, and `zoomFactor` describe multi-view dashboard PDFs, which this API cannot produce. |
| **Dependency chain:** | [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → `<view-id>`; [Get Columns](COLUMNS_API_DOC_INFO.md) → `selectedColumns` names → Export Data from a View → the file. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7104 | `META_OBJECT_NOT_PRESENT` — The view does not exist. | Verify `<view-id>` with [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list). |
| 7301 | `SECURITY_NOT_PERMITTED` — The caller lacks Export permission on the view, or the view does not belong to `<workspace-id>`. | Ensure the caller is an Account Admin, Organization Admin, Workspace Admin, or View Owner, or holds Export permission on the view. |
| 7327 | `FILTER_CRITERIA_INVALID` — `criteria` parsed but could not be converted into a query. | Simplify the expression and check operator and value types. |
| 7330 | `UNKNOWN_COLUMN_IN_FILTERCRITERIA` — A column named in `criteria` does not exist in the view. | Check the name against [Get Columns](COLUMNS_API_DOC_INFO.md). |
| 7331 | `FILTERCRITERIA_PARSE_ERROR` — `criteria` is syntactically malformed. | Check quoting: double quotes around column names, single quotes around string literals. |
| 7332 | `UNKNOWN_TABLE_IN_FILTERCRITERIA` — A table qualifier in `criteria` is not part of the view. | Qualify columns only with tables the view actually uses. |
| 7333 | `INVALID_GROUP_FUNC_USE_IN_FILTERCRITERIA` — An aggregate function was used in `criteria`. | Remove `sum`, `avg`, `count`, and similar functions; filter on raw column values instead. |
| 7543 | `ONLY_BASETABLE_COL_IN_TABULAR_FILTERCRITERIA` — `criteria` on a tabular view referenced a column outside its base table. | Filter using only the base table's own columns. |
| 7565 | `UNVERIFIED_EMAIL` — The calling user's primary email address is not verified. | Verify the account's primary email address and retry. |
| 7801 | `MARGIN_VALUE_EXCEEDS` — A PDF margin is outside `0`–`1` inches. | Send a value between `0` and `1`. |
| 7803 | `INVALID_DIMENSION` — `width` or `height` is outside the permitted image range. | Use `width` 250–2000 and `height` 200–2000. |
| 7806 | `XLS_CELL_LIMIT_EXCEEDS` — The XLS export exceeds the per-sheet cell limit. | Narrow the export with `criteria` or `selectedColumns`, or export as CSV. |
| 7807 | `XLS_COL_LIMIT_EXCEEDS` — More than 256 columns were requested for an XLS export. | Reduce the column count with `selectedColumns`, or export as CSV. |
| 7808 | `XLS_CELL_CHAR_LIMIT_EXCEEDS` — A single cell exceeds 32,767 characters. | Exclude the offending column, or export as CSV. |
| 7809 | `XLS_NO_DATA` — The XLS export produced no data. | Widen or remove `criteria`. |
| 7824 | `EXPORT_REQ_BLOCKED` — Export has been blocked for this workspace. | Contact Zoho Analytics support using the address in the error message. |
| 7827 | `EXP_PDF_RECORD_LIMIT` — The PDF exceeds 1,000,000 cells (visible columns × rows). | Narrow the export with `criteria` or `selectedColumns`, or choose a non-paginated format. |
| 7830 | `EXP_ALL_RECORD_LIMIT` — The exported payload exceeds 100 MB. | Split the export with `criteria`, or use the asynchronous export. |
| 8001 | `INVALID_RESP_FORMAT` — `responseFormat` is not a supported value. | Send one of `csv`, `json`, `xml`, `xls`, `pdf`, `html`, `image`. |
| 8014 | `API_IMAGE_RESPONSE_NOT_POSSIBLE` — `image` was requested for a view that is not a chart. | Export charts as images; use `pdf` or `html` for tables and reports. |
| 8015 | `API_EXPORT_COLUMN_NOT_PRESENT` — A name in `selectedColumns` does not match any column in the view. | Check the display names with [Get Columns](COLUMNS_API_DOC_INFO.md). |
| 8017 | `INVALID_IMAGE_FORMAT` — `imageFormat` is not `png`, `jpg`, or `jpeg`. | Send one of the three supported values. |
| 8088 | `SECURITY_CONTROLS_FEATURE_DISABLED` — Export has been disabled for the organization by an administrator. | Ask an Organization Admin to re-enable export in the organization's security controls. |
| 8119 | `INVALID_VALUE_FOR_ATTRIBUTE` — A numeric or enumerated attribute is outside its permitted set. The message names the attribute and the accepted values. | Correct the value; see [Appendix E](#appendix-e--enum-reference). |
| 8133 | `SYNC_EXPORT_NOT_ALLOWED` — The view is a dashboard, a query table, a live-connect view, or a table above the row limit. | Use the asynchronous export API for this view. |
| 8188 | `EXPORT_INVALID_PASSWORD` — `password` is empty, blank, or shorter than 6 characters. | Send a password of 6–256 characters. |
| 8241 | `SYSTEM_TAG_DATA_WARNING_V2_VALIDATION_CONFIRMATION` — The view carries a restricted DATA_WARNING system tag. | Review the warning, then resend with `"validateSystemTags": false`. |
| 8507 | `MORE_THAN_MAX_LENGTH` — `CONFIG` exceeds 100,000 characters. | Shorten `criteria` or `selectedColumns`. |
| 8547 | `ARRAY_SIZE_OUT_OF_RANGE` — `selectedColumns` is empty or holds more than 300 entries. | Send between 1 and 300 column names, or omit the attribute. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token carrying `ZohoAnalytics.data.read`. |

---

## Appendix A – Common HTTP Headers

| Header | Value | Required | Description |
|--------|-------|----------|-------------|
| `Authorization` | `Zoho-oauthtoken <oauth-token>` | **Mandatory** | OAuth 2.0 access token of the calling user, carrying `ZohoAnalytics.data.read`. |
| `ZANALYTICS-ORGID` | Organization ID string | **Mandatory** | Organization ID of the workspace that owns the view. |

> **`ZANALYTICS-DEST-ORGID` is not used by this API.** That header applies only to cross-organization copy operations (Copy Workspace, [Copy Views](VIEW_OPERATIONS_API_DOC_INFO.md#2-copy-views), Copy Formulas), which target a destination organization.

There is no request body — this is a `GET`, and `CONFIG` travels in the query string:

```http
GET /restapi/v2/workspaces/466206000000071000/views/466206000000072000/data?CONFIG=%7B%22responseFormat%22%3A%22csv%22%2C%22criteria%22%3A%22%5C%22Region%5C%22%3D%27East%27%22%7D HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

The decoded `CONFIG` above is `{"responseFormat":"csv","criteria":"\"Region\"='East'"}`.

---

## Appendix B – OAuth Scope Summary

| API | HTTP Method | Scope |
|-----|-------------|-------|
| Export Data from a View | GET | `ZohoAnalytics.data.read` |

> The scope follows the HTTP method, and a `GET` maps to `read`. A token scoped only for `ZohoAnalytics.data.read` is sufficient for every format, including PDF and image rendering, because none of them modifies data. Conversely, `ZohoAnalytics.data.create` — the scope used by the import APIs — will **not** authorise this call.

---

## Appendix C – API-Specific Notes and Behaviours

### Export Data from a View

- **This is the only API in the suite whose success response is not JSON.** Everything else in the V2 surface returns either a `status`/`summary`/`data` envelope or an empty `204`. Here the success body is the file. Write client code that checks the HTTP status first, parses JSON only on failure, and reads `Content-Type` to decide how to handle the success body.
- **No `Content-Disposition` header is returned.** There is no server-suggested filename. Derive one yourself from the view name and the format, and remember that a password-protected `csv` arrives as a ZIP.
- **The view type decides more than the format does.** `image` needs a chart; dashboards and query tables are unavailable entirely; `selectedColumns` only applies to tables and tabular views. Establish the view type once via [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) and drive the CONFIG from it, rather than probing formats until one succeeds.
- **`8133` is a routing signal, not a bug.** It means "this view belongs to the asynchronous export". Treat it as a branch in the integration — fall back to the bulk export APIs — rather than as an error to retry.
- **`keyValueFormat` inverts between JSON and XML.** JSON defaults to key-value pairs; XML defaults to the wrapped `<column name="…">` envelope. An integration that sets neither gets two structurally unrelated documents from the same view. Set it explicitly whenever both formats are in play.
- **`keyValueFormat: true` for XML produces a fragment, not a document.** No `<?xml?>` declaration, no `<response>` root. Strict XML parsers will need the `keyValueFormat: false` shape, which is also the safer choice when column names contain spaces or punctuation.
- **`criteria` is the single most useful attribute for staying inside the limits.** The row-count ceiling, the PDF cell ceiling, and the 100 MB payload ceiling are all evaluated on what the export actually produces, so a narrowing `criteria` is what turns an unexportable view into an exportable one.
- **Password protection changes the response content type.** For `csv`, `json`, `xml`, `html`, and `image` the payload becomes a ZIP. This is the most common cause of "the exported file is corrupt" reports.
- **`showPersonalCols` is a convenience for administrators, not an access control.** For any other caller it is ignored and personal columns are included. Column-level restriction for shared users belongs in [Share Views](SHARING_API_DOC_INFO.md#2-share-views).
- **Page-setup values are shared with Email Schedules.** `paperSize`, `paperStyle`, the four margins, `showTitle`, `showDesc`, `exportLanguage`, and the six header/footer slots use the same value sets as [Create Email Schedule](EMAIL_SCHEDULES_API_DOC_INFO.md#2-create-email-schedule). A layout proven here can be transplanted there unchanged.
- **Dependency chain:** [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) + [Get Columns](COLUMNS_API_DOC_INFO.md) → Export Data from a View → the exported file. Nothing consumes this API's output within the V2 surface; it is the end of the line.

---

## Appendix D – General Response Payload Notes

| Field / Behaviour | Detail |
|-------------------|--------|
| **Success is HTTP 200 with a file body** | Not `204`, and not a JSON envelope. The body is the export itself. |
| **Failure responses share one shape** | `{"status": "failure", "summary": "<ERROR_NAME>", "data": {"errorCode": <n>, "errorMessage": "<text>"}}`. `summary` on failure is the error's symbolic name (for example `SYNC_EXPORT_NOT_ALLOWED`), not a localised sentence. |
| **`Content-Type` is the only descriptive header** | It is derived from `responseFormat`, or replaced by `application/zip` when `password` wraps the file. |
| **The body is not compressed** | No `Content-Encoding` is applied to the synchronous export; the bytes on the wire are the file's own bytes. |
| **All cell values are strings in JSON and XML** | Numeric, currency, percentage, and date columns are exported as formatted strings, following the column's display settings — not as JSON numbers. |
| **Column keys use display names** | Both JSON shapes and both XML shapes key on the column's display name as shown in the view, which is also what `selectedColumns` expects on the request side. |
| **`Row Number` is a synthetic field** | When enabled, it is a sequential counter over the exported rows. It is not the table's internal row identifier and will not match across two exports with different `criteria`. |
| **An empty export is still well-formed** | `{"data":[]}`, `<rows></rows>`, or a header-only CSV. Check for emptiness explicitly; no error is raised. |
| **`response.criteria` is conditionally present** | It appears in the `keyValueFormat: false` JSON and XML envelopes only when a `criteria` was actually sent. Test for the key. |
| **Binary formats carry no metadata in the payload** | `xls`, `pdf`, and image responses expose nothing about row counts or applied filters. If you need that, run the export in `json` first, or read the counts from the source view. |

---

## Appendix E – Enum Reference

Every enumerated attribute of this API in one place. An out-of-range value fails with `8119` unless noted otherwise.

**`responseFormat`** — default `csv`; invalid values fail with `8001`

| Value | Output |
|-------|--------|
| `csv` | Delimited text file |
| `json` | JSON document |
| `xml` | XML document |
| `xls` | Excel workbook |
| `pdf` | PDF document |
| `html` | HTML fragment |
| `image` | PNG or JPEG image — **chart views only** |

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

**`paperSize`** — PDF page size, default `4`

| Value | Page size |
|-------|-----------|
| `0` | Letter |
| `1` | Legal |
| `2` | Tabloid |
| `3` | A3 |
| `4` | A4 |
| `5` | Auto-fit — width grows with the number of visible columns |

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

**`imageFormat`** — default `png`; invalid values fail with `8017`

| Value | Image type |
|-------|------------|
| `png` | PNG |
| `jpg` | JPEG |
| `jpeg` | JPEG |

---

## Appendix F – Attribute Applicability by `responseFormat`

`✓` applicable, `–` accepted but has no effect for that format.

| Attribute | csv | json | xml | xls | pdf | html | image |
|-----------|:---:|:----:|:---:|:---:|:---:|:----:|:-----:|
| `criteria` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `password` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `validateSystemTags` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `selectedColumns` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | – |
| `showHiddenCols` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | – |
| `showPersonalCols` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | – |
| `includeHeader` | ✓ | – | – | ✓ | ✓ | ✓ | – |
| `includeRowNums` / `includeRowIds` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | – |
| `applyDefaultUF` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | – |
| `delimiter`, `recordDelimiter`, `quoted` | ✓ | – | – | – | – | – | – |
| `keyValueFormat` | – | ✓ | ✓ | – | – | – | – |
| `paperSize`, `paperStyle`, margins | – | – | – | – | ✓ | – | – |
| `showTitle`, `showDesc` | – | – | – | – | ✓ | – | – |
| `exportLanguage` | – | – | – | – | ✓ | – | – |
| header / footer slots and their `…Text` | – | – | – | – | ✓ | – | – |
| `includeTitle`, `includeDesc` | – | – | – | – | – | ✓ | – |
| `columnWidthRatio` | – | – | – | – | ✓ | ✓ | – |
| `imageFormat`, `width`, `height` | – | – | – | – | – | – | ✓ |
| `title`, `description`, `legend` | – | – | – | – | – | – | ✓ |
