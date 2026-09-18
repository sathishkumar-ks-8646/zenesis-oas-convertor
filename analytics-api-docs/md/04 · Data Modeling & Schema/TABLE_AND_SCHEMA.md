# Zoho Analytics V2 REST API — Table and Schema

This document covers the APIs for creating tables and inspecting table schema (column metadata) in a Zoho Analytics workspace. A table in Zoho Analytics is the primary data container — columns define its structure, and data is pushed or imported into rows.

> **Table vs. View:** In Zoho Analytics, the term *view* encompasses all objects inside a workspace — tables, reports, charts, and dashboards. Every table is a view with a specific type. The Get Table Metadata API accepts the view ID of a table and returns its column definitions.

> **Column-level Permissions:** Get Table Metadata returns only the columns that the calling user has been granted access to. Users with workspace-level DESIGNMODIFY permission see all columns; users with restricted view sharing may see a subset.

> **White Label / Client Portal:** Both APIs are available via portal domain URLs. Portal users with the appropriate workspace permissions can create tables and retrieve schema information.

---

## Index

| # | API Name | Method | URL |
|---|----------|--------|-----|
| 1 | [Create Table](#1-create-table) | POST | `/restapi/v2/workspaces/<workspace-id>/tables` |
| 2 | [Get Table Metadata](#2-get-table-metadata) | GET | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/metadata` |

---

## 1. Create Table

Creates a new table in the specified workspace. The table structure — its columns, data types, and optional lookup relationships — is defined entirely through the CONFIG parameter at creation time.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/tables` |
| **OAuth Scope** | `ZohoAnalytics.modeling.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace, or any user with Create Table permission on the workspace. |

### CONFIG Parameters

The top-level CONFIG object wraps a `tableDesign` object:

| Parameter | Type | Mandatory | Default | Max Length | Description |
|-----------|------|-----------|---------|------------|-------------|
| `tableDesign` | JSONObject | Yes | — | — | The complete table design definition. See sub-fields below. |

#### `tableDesign` Fields

| Field | Type | Mandatory | Default | Max Length | Description |
|-------|------|-----------|---------|------------|-------------|
| `TABLENAME` | String | Yes | — | 1000 | Display name for the new table. Must be unique within the workspace. |
| `TABLEDESCRIPTION` | String | No | `""` | 1000 | Optional description for the table. |
| `FOLDERNAME` | String | No | Default folder | 1000 | Name of an existing folder to place the table in. If omitted, the table is placed in the workspace's default folder. Resolved by folder display name — error 7144 if the folder does not exist. |
| `COLUMNS` | JSONArray | Yes | — | — | Array of column definition objects. Must contain at least one column. See column fields below. |

#### `COLUMNS` Array — Column Fields

Each element in the `COLUMNS` array defines one column:

| Field | Type | Mandatory | Default | Max Length | Description |
|-------|------|-----------|---------|------------|-------------|
| `COLUMNNAME` | String | Yes | — | 1000 | Display name of the column. Must be unique within the table. |
| `DATATYPE` | String | Yes | — | 1000 | Data type of the column. See the [Supported Data Types](#supported-data-types) table below. |
| `DESCRIPTION` | String | No | `""` | 1000 | Optional description for the column. |
| `MANDATORY` | String | No | `""` | 1000 | Set to `"true"` to mark the column as mandatory for data entry. |
| `DEFAULT` | String | No | `""` | 1000 | Default value to use for the column when no data is provided. Not supported for `AUTO_NUMBER` columns. |
| `ISHIDE` | Boolean | No | `false` | — | If `true`, the column is hidden from view by default. |
| `GEOROLE` | String | No | — | — | Geographic role for geo-type columns. Specifies the geographic entity the column represents (e.g., country, state, city). Required when using geo data types. |
| `LOOKUPCOLUMN` | JSONObject | No | — | 1000 | Defines a lookup relationship for this column. See lookup fields below. |
| `PII` | Boolean | No | `false` | — | If `true`, marks this column as containing Personally Identifiable Information (PII). |

#### `LOOKUPCOLUMN` Fields (for lookup columns)

| Field | Type | Mandatory | Description |
|-------|------|-----------|-------------|
| `TABLENAME` | String | Yes (when LOOKUPCOLUMN is present) | Display name of the parent table that this column references. Must be an existing table in the workspace. |
| `COLUMNNAME` | String | Yes (when LOOKUPCOLUMN is present) | Column name in the parent table that this column references. The data types of both columns must be compatible. |

#### Supported Data Types

| `DATATYPE` Value | Display Name | Description |
|------------------|--------------|-------------|
| `PLAIN` | Plain Text | Short single-line text. |
| `MULTI_LINE` | Multi-line Text | Long-form text with line breaks. |
| `NUMBER` | Number | Integer numbers. |
| `POSITIVE_NUMBER` | Positive Number | Non-negative integers only. |
| `DECIMAL_NUMBER` | Decimal Number | Floating-point numbers. |
| `CURRENCY` | Currency | Monetary values with currency formatting. |
| `PERCENT` | Percentage | Percentage values. |
| `AUTO_NUMBER` | Auto Number | System-generated sequential integer. Cannot have a DEFAULT value. |
| `BOOLEAN` | True/False | Boolean checkbox. |
| `DATE` | Date Time | Date with time (date + time components). |
| `DATE_AS_DATE` | Date | Date only (no time component). |
| `TIME` | Time | Time of day. |
| `DURATION` | Duration | Time duration (hours/minutes/seconds). |
| `EMAIL` | Email Address | Validated email address string. |
| `URL` | URL | Validated URL string. |
| `GEO` | Geographic (Text) | Text-based geographic column. Pair with `GEOROLE`. |
| `GEO_NUM` | Geographic (Number) | Number-based geographic column. Pair with `GEOROLE`. |

### Sample Requests

**Case 1 — Create a simple table with basic column types**

```http
POST /restapi/v2/workspaces/466206000000071000/tables HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"tableDesign":{"TABLENAME":"Sales Data","TABLEDESCRIPTION":"Monthly sales records","COLUMNS":[{"COLUMNNAME":"Region","DATATYPE":"PLAIN"},{"COLUMNNAME":"Order Date","DATATYPE":"DATE_AS_DATE"},{"COLUMNNAME":"Product","DATATYPE":"PLAIN"},{"COLUMNNAME":"Sales Amount","DATATYPE":"CURRENCY"},{"COLUMNNAME":"Units Sold","DATATYPE":"NUMBER"}]}}
```

**Case 2 — Create a table with a lookup column referencing another table**

```http
POST /restapi/v2/workspaces/466206000000071000/tables HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"tableDesign":{"TABLENAME":"Order Details","TABLEDESCRIPTION":"Line items for each order","FOLDERNAME":"Sales Analysis","COLUMNS":[{"COLUMNNAME":"Order ID","DATATYPE":"PLAIN","LOOKUPCOLUMN":{"TABLENAME":"Orders","COLUMNNAME":"Order ID"}},{"COLUMNNAME":"Product Name","DATATYPE":"PLAIN"},{"COLUMNNAME":"Quantity","DATATYPE":"POSITIVE_NUMBER"},{"COLUMNNAME":"Unit Price","DATATYPE":"CURRENCY"},{"COLUMNNAME":"Notes","DATATYPE":"MULTI_LINE","ISHIDE":true}]}}
```

**Case 3 — Create a table with mandatory columns, PII flag, and auto-number**

```http
POST /restapi/v2/workspaces/466206000000071000/tables HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"tableDesign":{"TABLENAME":"Customer Registry","TABLEDESCRIPTION":"Customer master records","COLUMNS":[{"COLUMNNAME":"Customer ID","DATATYPE":"AUTO_NUMBER"},{"COLUMNNAME":"Full Name","DATATYPE":"PLAIN","MANDATORY":"true"},{"COLUMNNAME":"Email","DATATYPE":"EMAIL","MANDATORY":"true","PII":true},{"COLUMNNAME":"Phone","DATATYPE":"PLAIN","PII":true},{"COLUMNNAME":"Signup Date","DATATYPE":"DATE_AS_DATE","DEFAULT":"01 Jan, 2024"}]}}
```

**Case 4 — White label portal user creating a table (with Create Table permission)**

```http
POST /restapi/v2/workspaces/466206000000071000/tables HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.cccccc.dddddd
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"tableDesign":{"TABLENAME":"Client Submissions","COLUMNS":[{"COLUMNNAME":"Submission Date","DATATYPE":"DATE_AS_DATE"},{"COLUMNNAME":"Submitted By","DATATYPE":"EMAIL"},{"COLUMNNAME":"Value","DATATYPE":"DECIMAL_NUMBER"}]}}
```

### Sample Responses

**HTTP 200 OK**

```json
{
  "status": "success",
  "summary": "Table has been created successfully.",
  "data": {
    "viewId": "7617000071955020"
  }
}
```

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Response returns only `viewId`** | The response contains only the newly created table's view ID. Use Get Table Metadata to retrieve the full column schema, or Get View List to see the table in the workspace. |
| **`FOLDERNAME` is the folder's display name** | This field accepts the folder's display name (not its ID). The name is resolved to an internal folder ID at request time. If the specified folder does not exist, the request fails with error 7144. Use Get Folder List to confirm the folder name before calling. |
| **`COLUMNS` must have at least one entry** | An empty `COLUMNS` array is rejected. |
| **Column names must be unique within the table** | Duplicate column names in the same `COLUMNS` array fail with error 7128. |
| **`AUTO_NUMBER` columns cannot have a `DEFAULT` value** | Including a `DEFAULT` value for an `AUTO_NUMBER` column returns error 7143. |
| **Lookup column compatibility** | Both the referencing column and the referenced column must have compatible data types. Incompatible types fail with error 7183. |
| **Lookup cannot reference the same table** | A column's `LOOKUPCOLUMN` cannot reference a column within the same table being created. This fails with error 7379. |
| **PII flag is metadata only** | Setting `PII: true` marks the column for data governance purposes. It does not restrict access or encrypt data automatically. |
| **Dependency** | If placing the table in a specific folder, obtain the folder display name from Get Folder List. If creating a lookup column, the referenced `TABLENAME` must match an existing table's display name in the workspace. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7111 | A table or view with the same name already exists in the workspace. | Use a unique `TABLENAME` within the workspace. |
| 7125 | The specified data type is not compatible with the column's configuration. | Verify the `DATATYPE` value and any associated format settings. |
| 7126 | A column name is empty or missing. | Provide a non-empty `COLUMNNAME` for every column in the `COLUMNS` array. |
| 7127 | A column name exceeds the maximum allowed length. | Keep `COLUMNNAME` values within 1000 characters. |
| 7128 | Duplicate column names found in the `COLUMNS` array. | Ensure all `COLUMNNAME` values are unique within the same table definition. |
| 7143 | A `DEFAULT` value was provided for an `AUTO_NUMBER` column. | Remove the `DEFAULT` field from `AUTO_NUMBER` column definitions. |
| 7144 | The specified `FOLDERNAME` does not exist in this workspace. | Use Get Folder List to verify the exact folder display name before calling this API. |
| 7146 | The `DATATYPE` value is not a recognised data type. | Use one of the supported values from the Supported Data Types table. |
| 7183 | The lookup column's data type is incompatible with the referenced column's data type. | Ensure both columns use compatible data types. |
| 7301 | User does not have permission. | Ensure the user is a Workspace Admin or has Create Table permission on the workspace. |
| 7379 | A lookup column cannot reference a column within the same table. | Set `LOOKUPCOLUMN.TABLENAME` to a different existing table, not the table being created. |
| 7395 | The column specified in `LOOKUPCOLUMN.COLUMNNAME` does not exist in the referenced table. | Verify the column name using Get Table Metadata on the referenced table. |
| 7413 | `TABLENAME` is missing or null. | Ensure the `tableDesign.TABLENAME` field is present and non-empty. |
| 7478 | The number of columns exceeds the maximum allowed for a table. | Reduce the number of columns in the `COLUMNS` array. |

---

## 2. Get Table Metadata

Returns the complete column schema of the specified table — including column names, data types, descriptions, lookup relationships, formula expressions, and formatting details. Only columns the calling user has been granted access to are included in the response.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/metadata` |
| **OAuth Scope** | `ZohoAnalytics.metadata.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace, or any user with Design Modify permission on the view. |

> This API has no CONFIG parameter.

### Sample Requests

**Case 1 — Workspace Admin retrieving full table schema**

```http
GET /restapi/v2/workspaces/466206000000071000/views/7617000000508001/metadata HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — User with Design Modify permission retrieving column schema**

```http
GET /restapi/v2/workspaces/466206000000071000/views/7617000000508001/metadata HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.aaaaaa.bbbbbb
ZANALYTICS-ORGID: 700000123456
```

**Case 3 — White label portal user retrieving table schema**

```http
GET /restapi/v2/workspaces/466206000000071000/views/7617000000508001/metadata HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.cccccc.dddddd
ZANALYTICS-ORGID: 700000123456
```

### Sample Responses

**HTTP 200 OK**

**Case 1 — Table with text, date, and currency columns**

```json
{
  "status": "success",
  "summary": "Get table metadata",
  "data": {
    "columns": [
      {
        "columnId": "7617000000508026",
        "columnName": "Region",
        "dataType": "PLAIN",
        "dataTypeId": 1,
        "dataTypeName": "Plain Text",
        "columnIndex": 1,
        "columnDesc": "",
        "columnMaxSize": 253,
        "isNullable": true,
        "defaultValue": "",
        "pkTableName": "",
        "pkColumnName": "",
        "formulaDisplayName": "",
        "isHidden": false,
        "sortedOrder": 0,
        "sortedIndex": -1
      },
      {
        "columnId": "7617000000508025",
        "columnName": "Order Date",
        "dataType": "DATE_AS_DATE",
        "dataTypeId": 22,
        "dataTypeName": "Date",
        "columnIndex": 2,
        "columnDesc": "",
        "columnMaxSize": 19,
        "isNullable": true,
        "defaultValue": "",
        "pkTableName": "",
        "pkColumnName": "",
        "formulaDisplayName": "",
        "dateFormat": "dd MMM, yyyy HH:mm:ss",
        "isHidden": false,
        "sortedOrder": 0,
        "sortedIndex": -1
      },
      {
        "columnId": "7617000000508030",
        "columnName": "Sales Amount",
        "dataType": "CURRENCY",
        "dataTypeId": 7,
        "dataTypeName": "Currency",
        "columnIndex": 3,
        "columnDesc": "",
        "columnMaxSize": 19,
        "isNullable": true,
        "defaultValue": "",
        "pkTableName": "",
        "pkColumnName": "",
        "formulaDisplayName": "",
        "currencyFormat": "en;US;",
        "thousandSeparator": ",",
        "decimalSeparator": ".",
        "decimalPlaces": 2,
        "isHidden": false,
        "sortedOrder": 0,
        "sortedIndex": -1
      }
    ]
  }
}
```

**Case 2 — Table with a lookup column (showing `pkTableName`/`pkColumnName`)**

```json
{
  "status": "success",
  "summary": "Get table metadata",
  "data": {
    "columns": [
      {
        "columnId": "7617000071955021",
        "columnName": "Order ID",
        "dataType": "PLAIN",
        "dataTypeId": 1,
        "dataTypeName": "Plain Text",
        "columnIndex": 1,
        "columnDesc": "",
        "columnMaxSize": 100,
        "isNullable": true,
        "defaultValue": "",
        "pkTableName": "Orders",
        "pkColumnName": "Order ID",
        "formulaDisplayName": "",
        "isHidden": false,
        "sortedOrder": 0,
        "sortedIndex": -1
      },
      {
        "columnId": "7617000071955022",
        "columnName": "Product Name",
        "dataType": "PLAIN",
        "dataTypeId": 1,
        "dataTypeName": "Plain Text",
        "columnIndex": 2,
        "columnDesc": "",
        "columnMaxSize": 100,
        "isNullable": true,
        "defaultValue": "",
        "pkTableName": "",
        "pkColumnName": "",
        "formulaDisplayName": "",
        "isHidden": false,
        "sortedOrder": 0,
        "sortedIndex": -1
      }
    ]
  }
}
```

**Case 3 — Table with a formula column (showing `formulaDisplayName`)**

```json
{
  "status": "success",
  "summary": "Get table metadata",
  "data": {
    "columns": [
      {
        "columnId": "7617000000508030",
        "columnName": "Sales",
        "dataType": "CURRENCY",
        "dataTypeId": 7,
        "dataTypeName": "Currency",
        "columnIndex": 1,
        "columnDesc": "",
        "columnMaxSize": 19,
        "isNullable": true,
        "defaultValue": "",
        "pkTableName": "",
        "pkColumnName": "",
        "formulaDisplayName": "",
        "currencyFormat": "en;US;",
        "thousandSeparator": ",",
        "decimalSeparator": ".",
        "decimalPlaces": 2,
        "isHidden": false,
        "sortedOrder": 0,
        "sortedIndex": -1
      },
      {
        "columnId": "7617000000508031",
        "columnName": "Cost",
        "dataType": "CURRENCY",
        "dataTypeId": 7,
        "dataTypeName": "Currency",
        "columnIndex": 2,
        "columnDesc": "",
        "columnMaxSize": 19,
        "isNullable": true,
        "defaultValue": "",
        "pkTableName": "",
        "pkColumnName": "",
        "formulaDisplayName": "",
        "currencyFormat": "en;US;",
        "thousandSeparator": ",",
        "decimalSeparator": ".",
        "decimalPlaces": 2,
        "isHidden": false,
        "sortedOrder": 0,
        "sortedIndex": -1
      },
      {
        "columnId": "7617000000508032",
        "columnName": "Profit",
        "dataType": "CURRENCY",
        "dataTypeId": 7,
        "dataTypeName": "Currency",
        "columnIndex": 3,
        "columnDesc": "",
        "columnMaxSize": 19,
        "isNullable": true,
        "defaultValue": "",
        "pkTableName": "",
        "pkColumnName": "",
        "formulaDisplayName": "\"Sales\" - \"Cost\"",
        "currencyFormat": "en;US;",
        "thousandSeparator": ",",
        "decimalSeparator": ".",
        "decimalPlaces": 2,
        "isHidden": false,
        "sortedOrder": 0,
        "sortedIndex": -1
      }
    ]
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `columnId` | String | Unique ID of the column. |
| `columnName` | String | Display name of the column. |
| `dataType` | String | Internal data type code (e.g. `"PLAIN"`, `"CURRENCY"`, `"DATE_AS_DATE"`). |
| `dataTypeId` | Integer | Numeric ID of the data type. |
| `dataTypeName` | String | Human-readable data type name (e.g. `"Plain Text"`, `"Currency"`, `"Date"`). |
| `columnIndex` | Integer | Sort order of the column within the table. Columns are ordered by ascending `columnIndex`. |
| `columnDesc` | String | Column description. Empty string if none set. |
| `columnMaxSize` | Integer | Maximum storage size of the column value (in characters or bytes, depending on type). |
| `isNullable` | Boolean | `true` if the column allows null/empty values. |
| `defaultValue` | String | The configured default value. Empty string if none set. |
| `pkTableName` | String | For lookup columns: the display name of the referenced (parent) table. Empty string for non-lookup columns. |
| `pkColumnName` | String | For lookup columns: the column name in the referenced table. Empty string for non-lookup columns. |
| `formulaDisplayName` | String | For formula columns: the formula expression as a display string. Empty string for non-formula columns. |
| `isHidden` | Boolean | `true` if the column is configured as hidden. |
| `sortedOrder` | Integer | Current sort direction applied to this column: `0` = none, `1` = ascending, `-1` = descending. |
| `sortedIndex` | Integer | Sort priority when multiple columns are sorted. `-1` = not part of any sort order. |
| `dateFormat` *(conditional)* | String | Date or datetime format string. Present only for `DATE` and `DATE_AS_DATE` columns. |
| `durationFormat` *(conditional)* | String | Duration format string. Present only for `DURATION` columns. |
| `timeFormat` *(conditional)* | String | Time format string. Present only for `TIME` columns. |
| `currencyFormat` *(conditional)* | String | Currency locale format string (e.g. `"en;US;"`). Present only for `CURRENCY` columns. |
| `thousandSeparator` *(conditional)* | String | Thousands separator character. Present for numeric types (`CURRENCY`, `NUMBER`, `DECIMAL_NUMBER`, `PERCENT`). |
| `decimalSeparator` *(conditional)* | String | Decimal separator character. Present for numeric types. |
| `decimalPlaces` *(conditional)* | Integer | Number of decimal places configured. Present for numeric types. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Filtered column list** | The response includes only the columns that the calling user has been granted access to. A Workspace Admin or user with full DESIGNMODIFY permission sees all columns. Users with restricted view-level sharing see only their shared columns. |
| **Non-table views are rejected** | This API only works on tables. Calling it with the view ID of a report, chart, or dashboard returns error 7397. Use the Get View List API to confirm the view type before calling. |
| **`pkTableName` / `pkColumnName` for non-lookup columns** | These fields are always present in every column object but are empty strings (`""`) for columns that are not lookup columns. |
| **`formulaDisplayName` for non-formula columns** | Always present in every column object but is an empty string for non-formula columns. |
| **Conditional type-specific fields** | `dateFormat`, `durationFormat`, `timeFormat`, `currencyFormat`, `thousandSeparator`, `decimalSeparator`, and `decimalPlaces` appear only in the response for column types where they apply. They are absent for unrelated column types. |
| **`columnId` is returned as a string** | Despite being a numeric identifier internally, `columnId` is serialized as a quoted string. |
| **Dependency** | `<view-id>` in the URL must be a table's view ID, obtained from the Get View List API for the workspace. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7105 | The specified view does not exist. | Verify the `<view-id>` using the Get View List API. |
| 7301 | User does not have permission. | Ensure the user is a Workspace Admin or has Design Modify permission on the specified view. |
| 7319 | The specified view ID does not belong to the given workspace. | Confirm the `<view-id>` belongs to the workspace identified by `<workspace-id>`. |
| 7397 | The specified view is not a table. | This API only returns metadata for tables. Use Get View List to confirm the view type is a table before calling. |

---

## Appendix A – Common HTTP Headers

| Header | Value | Required | Notes |
|--------|-------|----------|-------|
| `Authorization` | `Zoho-oauthtoken <oauth-token>` | **Mandatory** | OAuth 2.0 access token of the calling user. |
| `ZANALYTICS-ORGID` | Organisation ID | **Mandatory** for both APIs | Organisation ID of the workspace. |
| `Content-Type` | `application/x-www-form-urlencoded` | Required for Create Table (POST) | Not required for Get Table Metadata (GET — no request body). |

> **White Label / Client Portal:** Use the portal's custom domain as the `Host` instead of `analyticsapi.zoho.com`. `ZANALYTICS-ORGID` is still required.

---

## Appendix B – OAuth Scope Summary

| API | Method | Scope |
|-----|--------|-------|
| Create Table | POST | `ZohoAnalytics.modeling.create` |
| Get Table Metadata | GET | `ZohoAnalytics.metadata.read` |

---

## Appendix C – API-Specific Notes and Behaviours

### Create Table

- **Response gap:** Only `viewId` is returned. To inspect the created table's column schema, call Get Table Metadata immediately after creation.
- **`FOLDERNAME` resolves by display name:** Unlike most APIs that accept folder IDs, this field accepts the folder's display name. If the name doesn't exactly match an existing folder, the request fails with error 7144. Obtain the exact name from Get Folder List.
- **Lookup column chaining:** If you are creating multiple related tables in sequence, create the parent table first, then create child tables with `LOOKUPCOLUMN` references pointing to the parent.
- **Column ordering:** Columns appear in the table in the order they are listed in the `COLUMNS` array.
- **Dependency:** `FOLDERNAME` → Get Folder List (for the display name). For lookup columns, the referenced `TABLENAME` must match an existing table's display name in the workspace (obtained from Get View List).

### Get Table Metadata

- **Column visibility is caller-scoped:** The `columns` array in the response reflects the subset of columns the caller has access to. Do not assume that an empty or short column list means the table has few columns — the caller may simply have restricted sharing.
- **`pkTableName` identifies lookup source:** When `pkTableName` is a non-empty string, the column is a lookup column. The value is the display name of the parent table, which matches the `TABLENAME` used when the lookup was created.
- **`formulaDisplayName` reveals formula logic:** Non-empty `formulaDisplayName` means the column is a computed formula column. The formula is shown as a human-readable expression.
- **Type-specific formatting fields:** Use `dateFormat`, `currencyFormat`, `decimalPlaces`, etc. to correctly format values when displaying or importing data for those column types.
- **`columnIndex` is the display order:** Columns are returned in the order they appear in the table, sorted by `columnIndex`. This matches what users see in the Zoho Analytics UI.
- **Dependency:** `<view-id>` → Get View List API for the workspace. Verify that the view's type is a table before calling.

### Cross-API Dependency Chain

```
Get Workspace List
  └─ Get View List (for workspace)
       ├─ Get Table Metadata   [requires view-id of a table]
       └─ Create Table
            └─ Get Folder List [for FOLDERNAME value]
```

---

## Appendix D – General Response Payload Notes

| Field / Behaviour | Detail |
|-------------------|--------|
| **`viewId` in Create Table response** | Returned as a quoted string, not a numeric. Consistent with how all view/column/folder IDs are returned across the API. |
| **`columnId` in Get Table Metadata** | Returned as a quoted string. |
| **`dataType` vs `dataTypeName`** | `dataType` is the internal code used in Create Table requests (e.g., `"PLAIN"`). `dataTypeName` is the human-readable display name (e.g., `"Plain Text"`). Use `dataType` when creating or modifying columns via the API. |
| **Empty string vs absent fields** | `pkTableName`, `pkColumnName`, `formulaDisplayName`, `defaultValue`, `columnDesc` are always present in every column object and default to `""` when not applicable. Type-specific fields (`dateFormat`, `currencyFormat`, etc.) are absent entirely when not applicable to the column's data type. |
| **`columnMaxSize`** | Represents the configured or default maximum storage size for the column. For text columns this is a character limit; for numeric columns it reflects internal precision. |
