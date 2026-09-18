# Reports APIs – Documentation

This document describes the V2 **Reports (Analysis View)** REST APIs of Zoho Analytics.
It follows the same conventions used in `TAG_API_DOC_INFO.md` — each API is documented
with URL, method, behavior, OAuth scope, `CONFIG` schema, sample payload/response, and
common error codes.

> Notes that apply to every API in this document:
> - All requests are authenticated via OAuth (`Authorization: Zoho-oauthtoken <token>`).
> - The `ZANALYTICS-ORGID` header is **mandatory**.
> - `ZohoAnalytics_Server_URI` depends on the data center (`analyticsapi.zoho.com`, `.eu`, etc.).
> - The `CONFIG` parameter (for POST/PUT) must be sent as a URL-encoded JSON string in the request body.
> - `reportType` must be one of `chart`, `pivot`, or `summary`.

---

## Index

| # | API NAME | METHOD | URL |
|---|----------|--------|-----|
| 1 | Create Analysis View | POST | `/restapi/v2/workspaces/<workspace-id>/reports` |
| 2 | Update Analysis View | PUT | `/restapi/v2/workspaces/<workspace-id>/reports/<view-id>` |
| 3 | Get Report Metadata | GET | `/restapi/v2/workspaces/<workspace-id>/reports/<view-id>/metadata` |

---

## 1. Create Analysis View

| Attribute | Value |
|-----------|-------|
| **API NAME** | Create Analysis View |
| **URL** | `POST https://<ZohoAnalytics_Server_URI>/restapi/v2/workspaces/<workspace-id>/reports` |
| **METHOD** | POST |
| **DESCRIPTION** | Creates a new analysis view (chart, pivot table, or summary view) in the specified workspace, based on a referenced base table. The view is configured via the `CONFIG` JSON parameter specifying the report type, axis columns, filters, and visualization settings. |
| **OAUTHSCOPE** | `ZohoAnalytics.modeling.create` |
| **PERMISSION REQUIRED** | The authenticated user must be an **Account Admin** or **Organization Admin**, or a **Workspace Admin**, or a **Shared User**, or a **Group Member**, or any user with **Create Report** permission on the workspace. |

### FIELDS FOR CONFIG JSON

| Attribute | Data Type | Mandatory | Default | Allowed Values / Constraints | Description |
|-----------|-----------|-----------|---------|------------------------------|-------------|
| `baseTableName` | string | **Yes** | — | Max 100 characters | Display name of the base table on which the analysis view is created. |
| `reportType` | string | **Yes** | — | `chart`, `pivot`, `summary` | The type of analysis view to create. |
| `title` | string | No | `""` | Max 100 characters | Display name for the new view. If omitted, the view ID is used as the title. |
| `description` | string | No | `""` | Max 250 characters | Optional description for the view. |
| `folderId` | long | No | Root folder | Valid folder ID; pass `-1` for root | Folder in which to place the new view. |
| `chartType` | string | No | `""` | Max 50 characters (alphanumeric, spaces) | Chart sub-type (e.g., `bar`, `line`, `pie`, `bubble`, `stacked bar`, `heat map`). Required for `chart` views. |
| `axisColumns` | JSONArray | No | `[]` | Max serialized size: 1 MB. See **Axis Column Object** below. | Defines the axis/dimension/measure configuration for the view. |
| `isAxisMerge` | boolean | No | `false` | `true` or `false` | When `true`, merges multiple y-axes onto a single scale. Requires `mergeAxisInfo`. |
| `mergeAxisInfo` | JSONArray | No | `[]` | Max serialized size: 10 MB. Each item: `axisIndex` (int array of 1-based positions) + `labelName` (string). | Groupings for merged axes when `isAxisMerge` is `true`. |
| `filters` | JSONArray | No | `[]` | Max serialized size: 1 MB. See **Filter Object** below. | Data filters applied to the view at render time. |
| `userFilters` | JSONArray | No | `[]` | Max serialized size: 1 MB. See **User Filter Object** below. | Interactive filter widgets shown to the viewer inside the view. |
| `settings` | JSONObject | No | `{}` | Max 10 KB. See **View Settings Object** below. | Layout and theme settings for the view. |
| `modifiedPaths` | JSONObject | No | `{}` | Max 10 KB | Tracks which configuration paths were changed (used for incremental updates). |
| `drillActionConfig` | JSONObject | No | `{}` | Max 100 KB. See **Drill Action Config Object** below. | Configures drill-through actions triggered by clicking data points. |

---

#### Axis Column Object

Each element in `axisColumns` is a JSON object describing one dimension or measure on the view.

| Field | Data Type | Mandatory | Description | Allowed Values |
|-------|-----------|-----------|-------------|----------------|
| `type` | string | **Yes** | Axis role of this column. See **Axis Type Enum** below. | See enum below |
| `columnName` | string | Conditional | Name of the column. Required if `columnId` is not provided. | Max 1000 characters |
| `columnId` | long | Conditional | ID of the column (alternative to `columnName`). | Valid column ID |
| `tableName` | string | No | Table the column belongs to. Useful in multi-table workspaces. | Max 100 characters |
| `tableId` | long | No | ID of the table (alternative to `tableName`). | Valid table ID |
| `displayName` | string | No | Custom label shown on the axis in the rendered chart. | Max 250 characters |
| `operation` | string | No | Aggregation or date-grouping operation for the column. See **Operation Enum** below. | See enum below |
| `geoRole` | string | Conditional | Geographic role — required when `operation` is `geo`. See **GeoRole Enum** below. | See enum below |
| `rangeSize` | double | No | Bucket size for numeric range grouping (used with `range` operation). | Any positive double |
| `sort` | string | No | Sort direction for this axis dimension. | `asc` — ascending, `desc` — descending |
| `format` | JSONObject | No | Number/date display formatting. See **Column Format Object** below. | — |
| `windowFunction` | JSONObject | No | Window/table-calculation applied to this measure. See **Window Function Object** below. | — |

##### Axis Type Enum

| Value | Applicable View Types | Description |
|-------|-----------------------|-------------|
| `xAxis` | chart | Horizontal axis (dimension or date) |
| `yAxis` | chart | Vertical axis (measure) |
| `colorAxis` | chart | Groups data into color segments |
| `sizeaxis` | chart (bubble) | Encodes bubble size by measure |
| `textAxis` | chart | Displays a text label on the chart |
| `tooltip` | chart | Extra column shown in hover tooltip |
| `row` | pivot | Row dimension grouping |
| `column` | pivot | Column dimension grouping |
| `data` | pivot | Measure/value cell in pivot |
| `groupBy` | summary | Group-by dimension column |
| `summarize` | summary | Aggregated measure column |
| `custom` | any | Custom-purpose axis column |

##### Operation Enum

| Value | Description |
|-------|-------------|
| `actual` | Raw/actual value |
| `sum` | Sum of values |
| `average` | Average of values |
| `count` | Count of rows |
| `distinctCount` | Count of unique values |
| `min` | Minimum value |
| `max` | Maximum value |
| `stdDev` | Standard deviation |
| `variance` | Statistical variance |
| `percentile` | Percentile computation |
| `dimension` | Numeric column treated as dimension |
| `range` | Numeric range bucket grouping |
| `geo` | Geographic mapping (use with `geoRole`) |
| `year` | Group by year |
| `quarter` | Group by quarter (Q1–Q4) |
| `month` | Group by month |
| `monthYear` | Group by month-year |
| `absQuarter` | Absolute quarter (e.g., Q1 2024) |
| `dateTime` | Full date-time value |
| `seasonal` | Seasonal period grouping |

##### GeoRole Enum

| Value | Description |
|-------|-------------|
| `latitude` | Numeric latitude coordinate |
| `longitude` | Numeric longitude coordinate |
| `location` | Text-based location (city, region, country) |

##### Samples — Axis Column Configurations

**Sample 1: Bar chart — product dimension on x-axis, sales sum on y-axis**

```json
"axisColumns": [
  {
    "type": "xAxis",
    "columnName": "Product",
    "tableName": "Sales",
    "operation": "actual"
  },
  {
    "type": "yAxis",
    "columnName": "Sales",
    "tableName": "Sales",
    "operation": "sum"
  }
]
```

**Sample 2: Pivot table — rows, column year, and data measures with window functions**

```json
"axisColumns": [
  {
    "type": "row",
    "columnName": "Product",
    "operation": "actual"
  },
  {
    "type": "column",
    "columnName": "Date",
    "operation": "year"
  },
  {
    "type": "data",
    "columnName": "Sales",
    "operation": "average",
    "windowFunction": { "type": "pctOfTotal" }
  },
  {
    "type": "data",
    "columnName": "Sales",
    "operation": "distinctCount",
    "windowFunction": {
      "type": "pctOfCol",
      "baseField": "Product",
      "baseFieldPosition": "row"
    }
  }
]
```

**Sample 3: Scatter chart — color axis and tooltip for additional context**

```json
"axisColumns": [
  {
    "type": "xAxis",
    "columnName": "Product",
    "tableName": "Sales",
    "operation": "actual"
  },
  {
    "type": "yAxis",
    "columnName": "Sales",
    "tableName": "Sales",
    "operation": "sum"
  },
  {
    "type": "colorAxis",
    "columnName": "Region",
    "tableName": "Sales",
    "operation": "actual"
  },
  {
    "type": "tooltip",
    "columnName": "Customer Name",
    "tableName": "Sales",
    "operation": "actual"
  }
]
```

**Sample 4: Geo map chart — latitude and longitude columns**

```json
"axisColumns": [
  {
    "type": "xAxis",
    "columnName": "Latitude",
    "tableName": "LatLong",
    "operation": "geo",
    "geoRole": "latitude"
  },
  {
    "type": "yAxis",
    "columnName": "Longitude",
    "tableName": "LatLong",
    "operation": "geo",
    "geoRole": "longitude"
  }
]
```

---

#### Window Function Object

Attached to a measure entry in `axisColumns` to apply a table calculation on top of the aggregated value.

| Field | Data Type | Description | Allowed Values |
|-------|-----------|-------------|----------------|
| `type` | string | Window function type. | `runTotal` — running total, `pctOfTotal` — % of grand total, `pctOfCol` — % of column total, `pctdifffrom` — % diff from reference, `movingAvg` — moving average |
| `baseField` | string | Reference column name for comparison functions. | Column name string |
| `baseTable` | string | Reference table name. | Table name string |
| `baseFieldPosition` | string | Axis position of the reference field. | `xAxis`, `yAxis`, `row`, `column` |
| `baseFunction` | string | Date-grouping operation on the reference field. | Any value from **Operation Enum** |
| `percentileVal` | int | Percentile target value (only for `percentile` operation). | `0`–`100` |
| `movingCalculation` | JSONObject | Moving window definition: `calculation` (string), `previous` (int), `next` (int), `includeCurrent` (boolean), `includeNull` (boolean). | — |

##### Samples — Window Function

**Sample 1: Percentage of grand total**
```json
"windowFunction": {
  "type": "pctOfTotal"
}
```

**Sample 2: Percentage of column, referencing a pivot row dimension**
```json
"windowFunction": {
  "type": "pctOfCol",
  "baseField": "Product",
  "baseFieldPosition": "row"
}
```

**Sample 3: Running total anchored to date year on x-axis**
```json
"windowFunction": {
  "type": "runTotal",
  "baseField": "Date",
  "baseTable": "Sales",
  "baseFunction": "year",
  "baseFieldPosition": "xAxis"
}
```

---

#### Column Format Object

Attached to an `axisColumns` entry to control how values are rendered.

| Field | Data Type | Description | Allowed Values |
|-------|-----------|-------------|----------------|
| `type` | string | Format category. | `number`, `currency`, `percentage`, `date`, `text` |
| `displayName` | string | Override label for this column. | Max 1000 characters |
| `currencyFormat` | string | Currency symbol/code. | e.g., `$`, `€`, `USD` |
| `alignment` | string | Cell text alignment. | `left`, `center`, `right` |
| `thousandSeparator` | int | Enable thousand separator. | `0` — off, `1` — on |
| `decimalPlaces` | int | Number of decimal places to display. | `0`–`9` |
| `decimalSeparator` | int | Decimal separator character. | `0` — period (`.`), `1` — comma (`,`) |
| `showSymbol` | boolean | Show the currency or percentage symbol. | `true` or `false` |
| `showNegativeSign` | boolean | Show explicit minus sign for negatives. | `true` or `false` |
| `numberingType` | int | Scale suffix for large numbers. | `0` — none, `1` — thousands (K), `2` — millions (M), `3` — billions (B) |
| `unitsList` | string | Custom unit suffix appended to value. | e.g., `kg`, `hrs` |
| `displayLabel` | string | Label override displayed in chart legend. | Max 1000 characters |
| `dateFormat` | string | Date display format pattern. | e.g., `yyyy-MM-dd`, `dd MMM yyyy` |
| `userLocale` | boolean | Apply the viewer's locale for formatting. | `true` or `false` |

##### Samples — Column Format

**Sample 1: Currency with two decimal places and thousand separator**
```json
"format": {
  "type": "currency",
  "currencyFormat": "$",
  "decimalPlaces": 2,
  "thousandSeparator": 1,
  "showSymbol": true
}
```

**Sample 2: Percentage value with no decimal places**
```json
"format": {
  "type": "percentage",
  "decimalPlaces": 0,
  "showSymbol": true
}
```

**Sample 3: Large number expressed in millions with custom unit**
```json
"format": {
  "type": "number",
  "numberingType": 2,
  "thousandSeparator": 1,
  "unitsList": "M"
}
```

---

#### Filter Object

Each element in `filters` restricts the data rendered in the view based on column values.

| Field | Data Type | Description | Allowed Values |
|-------|-----------|-------------|----------------|
| `columnName` | string | Column to filter on. | Max 1000 characters |
| `columnId` | long | ID of the column (alternative to `columnName`). | Valid column ID |
| `tableName` | string | Table the column belongs to. | Max 1000 characters |
| `tableId` | long | ID of the table. | Valid table ID |
| `operation` | string | How the column value is computed for filtering. | Any value from **Operation Enum** |
| `filterType` | string | Filter category. | `value` — exact match, `ranking` — top/bottom N, `year`, `quarter`, `month`, `week`, `weekday`, `fulldate`, `date`, `datetime`, `quarteryear`, `weekyear`, `common`, `range` |
| `values` | JSONArray | Filter values or ranking spec (e.g., `"Top 5"`). | Array of strings |
| `rankingColumn` | string | Column used to rank results (for `ranking` filterType). | Column name |
| `rankingColumnDateSubType` | string | Date sub-grouping for ranking reference column. | Max 50 characters |
| `exclude` | boolean | When `true`, the listed `values` are excluded instead of included. | `true` or `false` |
| `wildcard` | JSONObject | Wildcard filter. Contains `criteria` (array, max 15 items each with `operation` + `value`) and `expression` (logical expression string). | — |
| `additionalDetails` | JSONObject | Extra filter context. Contains `type`, `label`, `isFromDashboard` (boolean), `fromViewId` (long). | — |

##### Samples — Filter Object

**Sample 1: Year filter — include specific years**
```json
"filters": [
  {
    "columnName": "Date",
    "tableName": "Sales",
    "operation": "actual",
    "filterType": "year",
    "values": ["2023", "2024"],
    "exclude": false
  }
]
```

**Sample 2: Ranking filter — top 5 products by average cost**
```json
"filters": [
  {
    "columnName": "Cost",
    "tableName": "Sales",
    "operation": "average",
    "filterType": "ranking",
    "values": ["Top 5"],
    "rankingColumn": "Product Category",
    "exclude": false
  }
]
```

**Sample 3: Combined value filter and seasonal week filter**
```json
"filters": [
  {
    "columnName": "Region",
    "tableName": "Sales",
    "operation": "actual",
    "filterType": "value",
    "values": ["North", "East"],
    "exclude": false
  },
  {
    "columnName": "Date",
    "tableName": "Sales",
    "operation": "seasonal",
    "filterType": "week",
    "values": ["Week 2", "Week 3", "Week 4"],
    "exclude": false
  }
]
```

---

#### User Filter Object

Each element in `userFilters` defines an interactive filter widget displayed to the viewer inside the view.

| Field | Data Type | Description | Allowed Values |
|-------|-----------|-------------|----------------|
| `tableName` | string | Table the filter column belongs to. | Max 1000 characters |
| `columnName` | string | Column the filter operates on. | Max 1000 characters |
| `operation` | string | Aggregation or grouping for the column. | Any value from **Operation Enum** |
| `compType` | string | UI widget type shown to the viewer. See **compType Enum** below. | See enum below |
| `filterType` | string | Data filter category applied by this widget. | Same values as **Filter Object** `filterType` |
| `isallval` | boolean | When `true`, initially selects all values in the widget. | `true` or `false` |
| `values` | JSONArray | Pre-selected/default values for the widget. | Array of strings |
| `defaultFilterValues` | JSONArray | Default values used when the viewer clears the selection. | Array of strings |
| `exclude` | boolean | When `true`, selected values are excluded. | `true` or `false` |
| `behaviour` | string | Controls which values populate the filter list. | `ListAllValues` — all dataset values, `ListOnlyRelevantValues` — only values relevant to current filters, `ListRelevantValues` — context-aware values |

##### compType Enum

| Value | Description |
|-------|-------------|
| `singleSelect` | Single-value dropdown selector |
| `multiSelect` | Multi-value checklist selector |
| `slider` | Numeric range slider |
| `dateRange` | Date range picker |

##### Samples — User Filter Object

**Sample 1: Single-select dropdown for a dimension, listing all values**
```json
"userFilters": [
  {
    "tableName": "Sales",
    "columnName": "Region",
    "operation": "actual",
    "compType": "singleSelect",
    "isallval": true,
    "exclude": false
  }
]
```

**Sample 2: Multi-select filter with pre-selected product values**
```json
"userFilters": [
  {
    "tableName": "Sales",
    "columnName": "Product",
    "operation": "actual",
    "compType": "multiSelect",
    "filterType": "individualValues",
    "isallval": false,
    "values": ["Bread", "CD"],
    "exclude": false
  }
]
```

**Sample 3: Date range picker with a default date window**
```json
"userFilters": [
  {
    "tableName": "Sales",
    "columnName": "Date",
    "operation": "dateRange",
    "compType": "dateRange",
    "filterType": "range",
    "isallval": false,
    "values": ["01 Jan 2020 to 31 Dec 2025"],
    "defaultFilterValues": ["01 Jan 2024 to 31 Dec 2024"]
  }
]
```

---

#### View Settings Object

Controls column layout widths and the visual theme for the view.

##### Layout Sub-fields

| Field | Data Type | Description | Allowed Values |
|-------|-----------|-------------|----------------|
| `defaultWidth` | int | Default column width in pixels for pivot/summary tables. | `1`–`1000` |

##### Theme Sub-fields

| Field | Data Type | Description | Allowed Values |
|-------|-----------|-------------|----------------|
| `themeType` | int | Preset theme style index. | `1`–`7` |
| `themeColor` | string | Primary accent color (hex code). | e.g., `#4A90D9` |
| `themeFontSize` | int | Base font size in points. | `5`–`24` |
| `themeRowSpacing` | int | Row height/spacing level. | `1` — compact, `2` — normal, `3` — relaxed |
| `compactIndent` | int | Row indentation depth in compact mode. | `0`–`3` |
| `fontColor` | string | Override font color (hex code). | e.g., `#333333` |

##### Samples — View Settings

**Sample 1: Pivot with explicit column width, theme, and font settings**
```json
"settings": {
  "layout": {
    "defaultWidth": 143
  },
  "themes": {
    "themeType": 4,
    "themeFontSize": 14,
    "themeRowSpacing": 2
  }
}
```

**Sample 2: Custom accent color and font color for dark-style presentation**
```json
"settings": {
  "themes": {
    "themeType": 3,
    "themeColor": "#4A90D9",
    "themeFontSize": 12,
    "themeRowSpacing": 1,
    "fontColor": "#FFFFFF"
  }
}
```

**Sample 3: Compact layout with indented rows and narrow default column width**
```json
"settings": {
  "layout": {
    "defaultWidth": 100
  },
  "themes": {
    "themeType": 1,
    "themeFontSize": 11,
    "themeRowSpacing": 1,
    "compactIndent": 2
  }
}
```

---

#### Drill Action Config Object

Configures actions triggered when a user clicks a data point in the rendered view.

| Field | Data Type | Description | Allowed Values |
|-------|-----------|-------------|----------------|
| `drillActionsConfig` | JSONArray | Array of drill action items (max 10 items). See sub-fields below. | — |

##### Drill Action Item Sub-fields

| Field | Data Type | Description | Allowed Values |
|-------|-----------|-------------|----------------|
| `id` | string | Unique action identifier. | Long integer or hyphenated long-int format |
| `name` | string | Display name for the action. | Max 50 characters |
| `urlString` | string | Target URL invoked when the action fires. | Valid URL; max 2000 characters |
| `methodType` | string | HTTP method for the URL call. | `GET`, `POST`, `PUT`, `DELETE` |
| `headers` | JSONArray | HTTP headers. Each entry: `key`, `value`, `type`. | Max serialized size: 5 KB |
| `params` | JSONArray | URL query parameters. Each entry: `key`, `value`, `type`. | Max serialized size: 5 KB |
| `formData` | JSONArray | Form body parameters. Each entry: `key`, `value`, `type`. | Max serialized size: 5 KB |
| `body` | string | Raw request body string. | Max 50,000 characters |
| `bodyType` | string | Body content format. | `raw`, `form`, `none` |

##### Samples — Drill Action Config

**Sample 1: Simple GET drill-through to an external page**
```json
"drillActionConfig": {
  "drillActionsConfig": [
    {
      "id": "1001",
      "name": "View Order Details",
      "urlString": "https://crm.example.com/orders?id={{OrderID}}",
      "methodType": "GET"
    }
  ]
}
```

**Sample 2: POST action with a JSON body and custom header**
```json
"drillActionConfig": {
  "drillActionsConfig": [
    {
      "id": "1002",
      "name": "Trigger Approval",
      "urlString": "https://api.example.com/approvals",
      "methodType": "POST",
      "headers": [
        { "key": "Content-Type", "value": "application/json", "type": "static" }
      ],
      "body": "{\"orderId\": \"{{OrderID}}\"}",
      "bodyType": "raw"
    }
  ]
}
```

### Sample values for CONFIG parameter

**Case 1: Create a bar chart with ranking filter**

```json
{
  "baseTableName": "Sales",
  "reportType": "chart",
  "chartType": "bar",
  "title": "Top Products by Average Cost",
  "description": "Bar chart filtered to top 5 products by average cost",
  "axisColumns": [
    {
      "type": "xAxis",
      "columnName": "Product",
      "tableName": "Sales",
      "operation": "actual"
    },
    {
      "type": "yAxis",
      "columnName": "Sales",
      "tableName": "Sales",
      "operation": "sum"
    },
    {
      "type": "yAxis",
      "columnName": "Date",
      "tableName": "Sales",
      "operation": "count"
    }
  ],
  "filters": [
    {
      "columnName": "Cost",
      "tableName": "Sales",
      "operation": "average",
      "filterType": "ranking",
      "values": ["Top 5"],
      "rankingColumn": "Product Category",
      "exclude": false
    }
  ]
}
```

**Case 2: Create a pivot table with multiple row/column axes and window functions**

```json
{
  "baseTableName": "Sales",
  "reportType": "pivot",
  "title": "Sales Pivot — Region by Year",
  "description": "Pivot showing sales and cost with percentage-of-total calculations",
  "axisColumns": [
    {
      "type": "row",
      "columnName": "Product",
      "operation": "actual"
    },
    {
      "type": "row",
      "columnName": "Date",
      "operation": "dateTime"
    },
    {
      "type": "column",
      "columnName": "Date",
      "operation": "year"
    },
    {
      "type": "data",
      "columnName": "Sales",
      "operation": "average",
      "windowFunction": { "type": "pctOfTotal" }
    },
    {
      "type": "data",
      "columnName": "Cost",
      "operation": "stdDev"
    },
    {
      "type": "data",
      "columnName": "Sales",
      "operation": "distinctCount",
      "windowFunction": {
        "type": "pctOfCol",
        "baseField": "Product",
        "baseFieldPosition": "row"
      }
    }
  ],
  "settings": {
    "layout": { "defaultWidth": 143 },
    "themes": { "themeType": 4, "themeFontSize": 14, "themeRowSpacing": 2 }
  }
}
```

**Case 3: Create a summary view with multi-select user filter and axis merge**

```json
{
  "baseTableName": "Sales",
  "reportType": "chart",
  "chartType": "combo",
  "title": "Sales vs Cost — Merged Axes",
  "description": "Combo chart with two y-axes merged and a multi-select product filter",
  "axisColumns": [
    {
      "type": "xAxis",
      "columnName": "Product",
      "tableName": "Sales",
      "operation": "actual",
      "displayName": ""
    },
    {
      "type": "yAxis",
      "columnName": "Sales",
      "tableName": "Sales",
      "operation": "min"
    },
    {
      "type": "yAxis",
      "columnName": "Cost",
      "tableName": "Sales",
      "operation": "sum"
    }
  ],
  "isAxisMerge": true,
  "mergeAxisInfo": [
    {
      "axisIndex": [2, 3],
      "labelName": "Sales & Cost"
    }
  ],
  "userFilters": [
    {
      "tableName": "Sales",
      "columnName": "Product",
      "operation": "actual",
      "compType": "multiSelect",
      "filterType": "individualValues",
      "isallval": false,
      "values": ["Bread", "CD"],
      "exclude": false
    }
  ],
  "folderId": 466206000000091001
}
```

### Sample Responses

**Case 1 – Success (chart created)**

```http
HTTP/1.1 200 OK
Content-Type: application/json;charset=UTF-8

{
  "status": "success",
  "summary": "Chart view created successfully.",
  "data": {
    "viewId": "466206000000105001"
  }
}
```

**Case 2 – Success (pivot created)**

```json
{
  "status": "success",
  "summary": "Pivot view created successfully.",
  "data": {
    "viewId": "466206000000106002"
  }
}
```

**Case 3 – Success (summary created)**

```json
{
  "status": "success",
  "summary": "Summary view created successfully.",
  "data": {
    "viewId": "466206000000107003"
  }
}
```

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Provide a valid `workspace-id` in the URL. |
| 7104 | The specified base table does not exist in the workspace. | Ensure `baseTableName` matches an existing table in the workspace. |
| 7111 | A view with the given title already exists in the workspace. | Choose a unique `title` for the new view. |
| 7301 | User does not have permission to create a report. | Ensure the user is an **Account Admin**, **Organization Admin**, **Workspace Admin**, **Shared User**, **Group Member**, or has **Create Report** permission on the workspace. |
| 8021 | Invalid view type specified. | Set `reportType` to one of `chart`, `pivot`, or `summary`. |
| 8050 | Invalid value provided. | Check that all CONFIG field values are within the allowed ranges and types. |
| 8075 | Invalid chart type parameter. | Provide a valid `chartType` value (e.g., `Bar`, `Line`, `Pie`). |
| 8119 | Invalid value for attribute. | Verify all attribute values in `axisColumns`, `filters`, and `settings` conform to the allowed constraints. |
| 8252 | Invalid report type. | Ensure `reportType` is `chart`, `pivot`, or `summary`. |
| 8535 | Invalid OAuth token. | Provide a valid, non-expired OAuth token in the `Authorization` header. |

---

## 2. Update Analysis View

| Attribute | Value |
|-----------|-------|
| **API NAME** | Update Analysis View |
| **URL** | `PUT https://<ZohoAnalytics_Server_URI>/restapi/v2/workspaces/<workspace-id>/reports/<view-id>` |
| **METHOD** | PUT |
| **DESCRIPTION** | Resets and updates the configuration of an existing analysis view in the specified workspace. The full view configuration (axis columns, filters, chart type, title, and settings) is replaced with the values provided in the `CONFIG` parameter. |
| **OAUTHSCOPE** | `ZohoAnalytics.modeling.update` |
| **PERMISSION REQUIRED** | The authenticated user must be an **Account Admin** or **Organization Admin**, or the **View Owner**, or a **Shared User**, or a **Group Member**, or any user with **Design Modify** permission on the view. |

### FIELDS FOR CONFIG JSON

> All sub-object schemas (Axis Column Object, Filter Object, User Filter Object, View Settings Object) are identical to those defined in **[Create Analysis View](#1-create-analysis-view)**. Refer to those sections for field details, enum values, and samples.

| Attribute | Data Type | Mandatory | Default | Allowed Values / Constraints | Description |
|-----------|-----------|-----------|---------|------------------------------|-------------|
| `objId` | long | No | — | Valid view ID | ID of the view to update. If omitted, the view ID from the URL path is used. |
| `reportType` | string | **Yes** | — | `chart`, `pivot`, `summary` | Type of the analysis view. **Must match the existing view type** — cannot be changed via this API. |
| `description` | string | No | `""` | Max 250 characters | Updated description. If omitted, the existing description is **cleared**. Always include the value from Get Report Metadata to preserve it. |
| `chartType` | string | No | `""` | Max 50 characters (alphanumeric, spaces) | Chart sub-type (e.g., `bar`, `line`, `pie`). Required for `chart` views. |
| `axisColumns` | JSONArray | No | `[]` | Max serialized size: 1 MB. See **Axis Column Object** in [Create Analysis View](#1-create-analysis-view). | Full replacement axis configuration for the view. |
| `isAxisMerge` | boolean | No | `false` | `true` or `false` | When `true`, merges multiple y-axes. Requires `mergeAxisInfo`. |
| `mergeAxisInfo` | JSONArray | No | `[]` | Max serialized size: 10 MB. Each item: `axisIndex` (int array) + `labelName` (string). | Axis merge groupings when `isAxisMerge` is `true`. |
| `filters` | JSONArray | No | `[]` | Max serialized size: 1 MB. See **Filter Object** in [Create Analysis View](#1-create-analysis-view). | Replacement data filters for the view. |
| `userFilters` | JSONArray | No | `[]` | Max serialized size: 1 MB. See **User Filter Object** in [Create Analysis View](#1-create-analysis-view). | Replacement interactive filter widgets for the view. |
| `settings` | JSONObject | No | `{}` | Max 10 KB. See **View Settings Object** in [Create Analysis View](#1-create-analysis-view). | Replacement layout and theme settings. |

> ⚠️ **Read-only fields in Update:** `title` (display name) and `folderId` cannot be changed via this API. `title` in the CONFIG is silently ignored — the existing display name is always preserved. If `folderId` is provided and differs from the view's current folder, the request **fails with an error**. Omit both fields from the Update CONFIG.

### Sample values for CONFIG parameter

**Case 1: Update chart type and axis columns**

```json
{
  "reportType": "chart",
  "chartType": "line",
  "title": "Monthly Sales — Line Chart",
  "axisColumns": [
    {
      "type": "xAxis",
      "columnName": "Date",
      "tableName": "Sales",
      "operation": "monthYear"
    },
    {
      "type": "yAxis",
      "columnName": "Sales",
      "tableName": "Sales",
      "operation": "sum"
    },
    {
      "type": "yAxis",
      "columnName": "Cost",
      "tableName": "Sales",
      "operation": "sum"
    }
  ]
}
```

**Case 2: Move view to a different folder and apply a date filter**

```json
{
  "reportType": "pivot",
  "folderId": 466206000000091005,
  "axisColumns": [
    {
      "type": "row",
      "columnName": "Region",
      "tableName": "Sales"
    },
    {
      "type": "column",
      "columnName": "Date",
      "tableName": "Sales",
      "operation": "year"
    },
    {
      "type": "data",
      "columnName": "Sales",
      "tableName": "Sales",
      "operation": "sum"
    }
  ],
  "filters": [
    {
      "columnName": "Date",
      "tableName": "Sales",
      "operation": "actual",
      "filterType": "year",
      "values": ["2024", "2025"],
      "exclude": false
    }
  ],
  "settings": {
    "layout": { "defaultWidth": 120 },
    "themes": { "themeType": 2, "themeFontSize": 13, "themeRowSpacing": 2 }
  }
}
```

**Case 3: Enable axis merge across two y-axes with theme settings**

```json
{
  "reportType": "chart",
  "chartType": "combo",
  "axisColumns": [
    {
      "type": "xAxis",
      "columnName": "Product",
      "tableName": "Sales",
      "operation": "actual"
    },
    {
      "type": "yAxis",
      "columnName": "Sales",
      "tableName": "Sales",
      "operation": "sum"
    },
    {
      "type": "yAxis",
      "columnName": "Date",
      "tableName": "Sales",
      "operation": "count"
    },
    {
      "type": "yAxis",
      "columnName": "Cost",
      "tableName": "Sales",
      "operation": "count"
    }
  ],
  "isAxisMerge": true,
  "mergeAxisInfo": [
    {
      "axisIndex": [2, 5],
      "labelName": "Sales & Cost Metrics"
    }
  ],
  "settings": {
    "themes": {
      "themeType": 3,
      "themeColor": "#4A90D9",
      "themeFontSize": 12,
      "themeRowSpacing": 1
    }
  }
}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Update Analysis View returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Provide a valid `workspace-id` in the URL. |
| 7104 | The specified view does not exist. | Ensure the `view-id` in the URL corresponds to an existing analysis view. |
| 7111 | A view with the given title already exists in the workspace. | Choose a unique `title` for the view. |
| 7301 | User does not have permission to update this view. | Ensure the user is an **Account Admin**, **Organization Admin**, **View Owner**, **Shared User**, **Group Member**, or has **Design Modify** permission on the view. |
| 8021 | Invalid view type specified. | Set `reportType` to one of `chart`, `pivot`, or `summary`. |
| 8050 | Invalid value provided. | Check that all CONFIG field values are within the allowed ranges and types. |
| 8075 | Invalid chart type parameter. | Provide a valid `chartType` value (e.g., `Bar`, `Line`, `Pie`). |
| 8100 | Operation not supported for this analysis view widget. | Ensure the update operation is valid for the current view type. |
| 8119 | Invalid value for attribute. | Verify all attribute values in `axisColumns`, `filters`, and `settings` conform to the allowed constraints. |
| 8252 | Invalid report type. | Ensure `reportType` is `chart`, `pivot`, or `summary`. |
| 8535 | Invalid OAuth token. | Provide a valid, non-expired OAuth token in the `Authorization` header. |

---

## Appendix A – Common HTTP Headers

Every API call documented here should include:

| Header | Value | Description |
|--------|-------|-------------|
| `Authorization` | `Zoho-oauthtoken <oauth-token>` | OAuth token of the calling user. |
| `ZANALYTICS-ORGID` | `<organization-id>` | Organization ID owning the workspace. **Mandatory.** Alternatively, a `workspaceKey` (in the format `orgid/workspacename`, e.g., `700000123456/Sales_Analytics`) may be used in place of the numeric workspace ID in the URL path. |
| `Content-Type` | `application/x-www-form-urlencoded` | `CONFIG` JSON must be sent as a URL-encoded form parameter named `CONFIG`. |

Example (Create Analysis View):

```http
POST /restapi/v2/workspaces/466206000000071000/reports HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG=%7B%22baseTableName%22%3A%22Sales_Data%22%2C%22reportType%22%3A%22chart%22%2C%22title%22%3A%22Monthly+Sales+Chart%22%7D
```

Example (Update Analysis View):

```http
PUT /restapi/v2/workspaces/466206000000071000/reports/466206000000105001 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG=%7B%22reportType%22%3A%22chart%22%2C%22chartType%22%3A%22Line%22%7D
```

---

## 3. Get Report Metadata

| Attribute | Value |
|-----------|-------|
| **API NAME** | Get Report Metadata |
| **URL** | `GET https://<ZohoAnalytics_Server_URI>/restapi/v2/workspaces/<workspace-id>/reports/<view-id>/metadata` |
| **METHOD** | GET |
| **DESCRIPTION** | Retrieves the full configuration metadata of an existing analysis view (chart, pivot table, or summary view) in the specified workspace. The response includes the report type, chart type, axis column definitions, applied filters, and visualization settings as stored in the system. |
| **OAUTHSCOPE** | `ZohoAnalytics.modeling.read` |
| **PERMISSION REQUIRED** | The authenticated user must be an **Account Admin** or **Organization Admin**, or the **View Owner**, or any user with **Design Modify** permission on the view. |

> This API has no `CONFIG` request parameter. All inputs are provided via URL path parameters.

### Sample Requests

**Case 1: Retrieve metadata for a bar chart view**

```http
GET /restapi/v2/workspaces/466206000000071000/reports/466206000000105001/metadata HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2: Retrieve metadata for a pivot or summary view**

```http
GET /restapi/v2/workspaces/466206000000071000/reports/466206000000106002/metadata HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

### Sample Responses

**Case 1: Simple bar chart — basic axis configuration**

A chart view with a single x-axis (product dimension) and a single y-axis (aggregated sales). Demonstrates the minimum `reportConfig` structure returned for a standard vertical bar chart.

```http
HTTP/1.1 200 OK
Content-Type: application/json;charset=UTF-8

{
  "status": "success",
  "summary": "Get analysis view metadata",
  "data": {
    "reportConfig": {
      "title": "Bar Chart Report",
      "description": "Vertical bar chart",
      "reportType": "chart",
      "chartType": "bar",
      "baseTableName": "Sales",
      "isAxisMerge": false,
      "axisColumns": [
        {
          "type": "xaxis",
          "columnName": "Product",
          "tableName": "Sales",
          "operation": "actual"
        },
        {
          "type": "yaxis",
          "columnName": "Sales",
          "tableName": "Sales",
          "operation": "sum"
        }
      ]
    }
  }
}
```

**Case 2: Bubble chart — multiple axis types (xAxis, yAxis, sizeAxis)**

A bubble chart using three axis types. The `sizeaxis` entry controls the bubble size (average cost). Demonstrates how multi-axis charts are represented in `axisColumns`.

```http
HTTP/1.1 200 OK
Content-Type: application/json;charset=UTF-8

{
  "status": "success",
  "summary": "Get analysis view metadata",
  "data": {
    "reportConfig": {
      "title": "Bubble Chart",
      "description": "Bubble chart visualization",
      "reportType": "chart",
      "chartType": "bubble",
      "baseTableName": "Sales",
      "isAxisMerge": false,
      "axisColumns": [
        {
          "type": "xaxis",
          "columnName": "Product",
          "tableName": "Sales",
          "operation": "actual"
        },
        {
          "type": "yaxis",
          "columnName": "Sales",
          "tableName": "Sales",
          "operation": "sum"
        },
        {
          "type": "sizeaxis",
          "columnName": "Cost",
          "tableName": "Sales",
          "operation": "average"
        }
      ]
    }
  }
}
```

**Case 3: Stacked bar chart with color axis — three-dimensional grouping**

A stacked bar chart that uses a `coloraxis` entry to split bars by a categorical dimension (Product), in addition to x-axis (year) and y-axis (sum of sales). Demonstrates how color-based grouping is stored in the axis column list.

```http
HTTP/1.1 200 OK
Content-Type: application/json;charset=UTF-8

{
  "status": "success",
  "summary": "Get analysis view metadata",
  "data": {
    "reportConfig": {
      "title": "Stacked Bar Chart",
      "description": "Stacked vertical bar chart",
      "reportType": "chart",
      "chartType": "stacked bar",
      "baseTableName": "Sales",
      "isAxisMerge": false,
      "axisColumns": [
        {
          "type": "xaxis",
          "columnName": "Date",
          "tableName": "Sales",
          "operation": "year"
        },
        {
          "type": "yaxis",
          "columnName": "Sales",
          "tableName": "Sales",
          "operation": "sum"
        },
        {
          "type": "coloraxis",
          "columnName": "Product",
          "tableName": "Sales",
          "operation": "actual"
        }
      ]
    }
  }
}
```

**Case 4: Chart with date filter applied — `filters` array in response**

A bar chart that has a date-range filter applied (years 2012 and 2013). Demonstrates how `filters` appear in the returned `reportConfig` when the view was saved with active data filters.

```http
HTTP/1.1 200 OK
Content-Type: application/json;charset=UTF-8

{
  "status": "success",
  "summary": "Get analysis view metadata",
  "data": {
    "reportConfig": {
      "title": "Date Filter Chart",
      "reportType": "chart",
      "chartType": "bar",
      "baseTableName": "Sales",
      "isAxisMerge": false,
      "axisColumns": [
        {
          "type": "xaxis",
          "columnName": "Date",
          "tableName": "Sales",
          "operation": "year"
        },
        {
          "type": "yaxis",
          "columnName": "Sales",
          "tableName": "Sales",
          "operation": "sum"
        }
      ],
      "filters": [
        {
          "tableName": "Sales",
          "columnName": "Date",
          "operation": "actual",
          "filterType": "year",
          "values": ["2012", "2013"],
          "exclude": false
        }
      ]
    }
  }
}
```

**Case 5: Combo chart with axis merge enabled — `isAxisMerge: true`**

A combo chart where two y-axes (Sales and Cost) are merged onto a single axis. The `isAxisMerge` flag is `true` and both y-axis columns appear in `axisColumns`. Demonstrates the axis merge configuration as persisted.

```http
HTTP/1.1 200 OK
Content-Type: application/json;charset=UTF-8

{
  "status": "success",
  "summary": "Get analysis view metadata",
  "data": {
    "reportConfig": {
      "title": "Chart With Axis Merge",
      "description": "Chart with axis merge enabled",
      "reportType": "chart",
      "chartType": "combo",
      "baseTableName": "Sales",
      "isAxisMerge": true,
      "axisColumns": [
        {
          "type": "xaxis",
          "columnName": "Date",
          "tableName": "Sales",
          "operation": "year"
        },
        {
          "type": "yaxis",
          "columnName": "Sales",
          "tableName": "Sales",
          "operation": "sum"
        },
        {
          "type": "yaxis",
          "columnName": "Cost",
          "tableName": "Sales",
          "operation": "sum"
        }
      ]
    }
  }
}
```

**Case 6: Chart with multiple wildcard filters — multiple `filters` entries**

A bar chart saved with two wildcard filters on different columns (Product and Region). Demonstrates how multiple filter objects are returned in the `filters` array when wildcard filtering is applied.

```http
HTTP/1.1 200 OK
Content-Type: application/json;charset=UTF-8

{
  "status": "success",
  "summary": "Get analysis view metadata",
  "data": {
    "reportConfig": {
      "title": "V2_Chart Multiple Wildcard Filters",
      "description": "Chart with multiple wildcard filters on different columns",
      "reportType": "chart",
      "chartType": "bar",
      "baseTableName": "Sales",
      "isAxisMerge": false,
      "axisColumns": [
        {
          "type": "xaxis",
          "columnName": "Product",
          "tableName": "Sales",
          "operation": "actual"
        },
        {
          "type": "yaxis",
          "columnName": "Sales",
          "tableName": "Sales",
          "operation": "sum"
        }
      ],
      "filters": [
        {
          "tableName": "Sales",
          "columnName": "Product",
          "operation": "actual",
          "filterType": "wildcard",
          "values": [],
          "exclude": false
        },
        {
          "tableName": "Sales",
          "columnName": "Region",
          "operation": "actual",
          "filterType": "wildcard",
          "values": [],
          "exclude": false
        }
      ]
    }
  }
}
```

**Case 7: Heat map chart — using colorAxis as the value measure**

A heat map chart where the color axis encodes the aggregated sales value, and the x/y axes represent product and year dimensions respectively. Demonstrates an alternate use of `coloraxis` as the primary measure axis.

```http
HTTP/1.1 200 OK
Content-Type: application/json;charset=UTF-8

{
  "status": "success",
  "summary": "Get analysis view metadata",
  "data": {
    "reportConfig": {
      "title": "Heat Map Chart",
      "description": "Heat map visualization",
      "reportType": "chart",
      "chartType": "heat map",
      "baseTableName": "Sales",
      "isAxisMerge": false,
      "axisColumns": [
        {
          "type": "xaxis",
          "columnName": "Product",
          "tableName": "Sales",
          "operation": "actual"
        },
        {
          "type": "yaxis",
          "columnName": "Date",
          "tableName": "Sales",
          "operation": "year"
        },
        {
          "type": "coloraxis",
          "columnName": "Sales",
          "tableName": "Sales",
          "operation": "sum"
        }
      ]
    }
  }
}
```

### Response Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `success` or `failure`. |
| `summary` | string | Always `"Get analysis view metadata"` on success. |
| `data.reportConfig` | JSONObject | The full configuration of the analysis view as stored. |
| `data.reportConfig.title` | string | Display name of the view. |
| `data.reportConfig.description` | string | Description of the view (omitted if empty). |
| `data.reportConfig.reportType` | string | View type: `chart`, `pivot`, or `summary`. |
| `data.reportConfig.chartType` | string | Chart sub-type (e.g., `bar`, `line`, `pie`, `bubble`, `stacked bar`, `heat map`). Present for `chart` views. |
| `data.reportConfig.baseTableName` | string | The name of the base table the view is built on. |
| `data.reportConfig.isAxisMerge` | boolean | `true` if multiple y-axes are merged onto a single axis. |
| `data.reportConfig.axisColumns` | JSONArray | Array of axis column objects defining the view's dimensions and measures. |
| `data.reportConfig.filters` | JSONArray | Array of data filter objects applied to the view. Omitted if no filters exist. |
| `data.reportConfig.userFilters` | JSONArray | Array of user-interactive filter objects. Omitted if none exist. |
| `data.reportConfig.settings` | JSONObject | Layout and theme settings. Omitted if no settings are configured. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Provide a valid `workspace-id` in the URL. |
| 7104 | The specified view does not exist in the workspace. | Ensure the `view-id` in the URL corresponds to an existing analysis view. |
| 7301 | User does not have permission to view this report's metadata. | Ensure the user is an **Account Admin**, **Organization Admin**, **View Owner**, or has **Design Modify** permission on the view. |
| 8021 | Invalid view type for the requested operation. | Ensure the target view is an analysis view (chart, pivot, or summary). |
| 8535 | Invalid OAuth token. | Provide a valid, non-expired OAuth token in the `Authorization` header. |

---

## Appendix B – OAuth Scope Summary

| API | HTTP Method | Scope |
|-----|-------------|-------|
| Create Analysis View | POST | `ZohoAnalytics.modeling.create` |
| Update Analysis View | PUT | `ZohoAnalytics.modeling.update` |
| Get Report Metadata | GET | `ZohoAnalytics.modeling.read` |

---

## Appendix C – Response Payload Notes

| Field | Description |
|-------|-------------|
| `status` | `success` or `failure`. Present in JSON success responses for Create Analysis View and Get Report Metadata, and in JSON failure responses. Update Analysis View success returns no body. |
| `summary` | Human-readable message describing the result of the operation. Present only in JSON success responses for Create Analysis View and Get Report Metadata. |
| `data.viewId` | (Create only) The ID of the newly created analysis view. Use this ID in subsequent API calls (e.g., Update Analysis View, Get Report Metadata). |
| `data.reportConfig` | (Get Report Metadata only) The full configuration object of the retrieved analysis view. |
| `errorCode` | (Failure only) Numeric error code identifying the failure reason. |
| `errorMessage` | (Failure only) Human-readable description of the error. |

> **Note:** The `CONFIG` parameter has a maximum serialized size of **10 MB** for both Create and Update Analysis View APIs. Ensure that nested arrays (`axisColumns`, `mergeAxisInfo`, `filters`, `userFilters`) do not cause the total CONFIG payload to exceed this limit.

---

## Appendix D – Working with Get, Create, and Update Together

### Why Get Report Metadata Before Update

The **Update Analysis View** API performs a **full configuration reset** — not a patch. The method is named `analysisViewResetAndUpdate` internally. When you PUT a CONFIG:

- Every axis column, filter, user filter, and settings entry is **completely replaced** with the new values.
- **`description`** is replaced (or cleared if omitted).
- Fields not provided (e.g., `axisColumns`) revert to their empty defaults.

To avoid losing existing configuration, always **fetch first, modify, then update**.

---

### Workflow 1 — Read-Modify-Write (Safe Update)

Use Get Report Metadata to retrieve the full current state of the view, make targeted changes, then PUT the complete modified config.

**Step 1: Fetch the current full config**

```http
GET /restapi/v2/workspaces/466206000000071000/reports/466206000000105001/metadata HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

Response (`data.reportConfig`):

```json
{
  "title": "Monthly Sales",
  "description": "Rolling 12-month trend",
  "reportType": "chart",
  "chartType": "bar",
  "baseTableName": "Sales",
  "isAxisMerge": false,
  "axisColumns": [
    { "type": "xaxis", "columnName": "Month", "tableName": "Sales", "operation": "actual" },
    { "type": "yaxis", "columnName": "Revenue", "tableName": "Sales", "operation": "sum" }
  ],
  "filters": [],
  "userFilters": []
}
```

**Step 2: Modify only what you need**

For example, change the chart type from `bar` to `line` and add a colour axis:

```json
{
  "reportType": "chart",
  "description": "Rolling 12-month trend",
  "chartType": "line",
  "baseTableName": "Sales",
  "isAxisMerge": false,
  "axisColumns": [
    { "type": "xaxis", "columnName": "Month", "tableName": "Sales", "operation": "actual" },
    { "type": "yaxis", "columnName": "Revenue", "tableName": "Sales", "operation": "sum" },
    { "type": "coloraxis", "columnName": "Region", "tableName": "Sales", "operation": "actual" }
  ],
  "filters": [],
  "userFilters": []
}
```

> Always carry the full `axisColumns` array — only the columns you send are stored. Any column removed here is permanently deleted from the view.

**Step 3: PUT the complete modified config**

```http
PUT /restapi/v2/workspaces/466206000000071000/reports/466206000000105001 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"reportType":"chart","description":"Rolling 12-month trend","chartType":"line","baseTableName":"Sales","isAxisMerge":false,"axisColumns":[{"type":"xaxis","columnName":"Month","tableName":"Sales","operation":"actual"},{"type":"yaxis","columnName":"Revenue","tableName":"Sales","operation":"sum"},{"type":"coloraxis","columnName":"Region","tableName":"Sales","operation":"actual"}],"filters":[],"userFilters":[]}
```

---

### Workflow 2 — Cloning a Report (Get → Create)

The `reportConfig` returned by Get Report Metadata is structurally identical to the Create CONFIG. Use it as a template for a new view.

**Step 1: Fetch full metadata of the source view**

```http
GET /restapi/v2/workspaces/466206000000071000/reports/466206000000105001/metadata
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Step 2: Prepare the Create CONFIG from the response**

Take `data.reportConfig` and:
- **Change `title`** — required, must be unique in the workspace.
- **Keep `baseTableName`** — required for Create.
- Keep `reportType`, `chartType`, `axisColumns`, `filters`, `userFilters`, `settings`, `isAxisMerge`, `mergeAxisInfo` as-is.
- **Omit `folderId`** from the response if you want the view in the default folder, or add it to place the clone in a specific folder.

**Step 3: POST to Create**

```http
POST /restapi/v2/workspaces/466206000000071000/reports HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"title":"Monthly Sales - Copy","reportType":"chart","chartType":"bar","baseTableName":"Sales","isAxisMerge":false,"axisColumns":[{"type":"xaxis","columnName":"Month","tableName":"Sales","operation":"actual"},{"type":"yaxis","columnName":"Revenue","tableName":"Sales","operation":"sum"}],"filters":[],"userFilters":[]}
```

---

### Special Cases and Caveats

| Case | Behaviour | Recommendation |
|------|-----------|----------------|
| **`title` is read-only on Update** | Any `title` value in the Update CONFIG is silently ignored — the existing display name is always preserved. There is no V2 API field to rename a view via Update. | Include `title` from the GET response for documentation/clarity, knowing it has no effect. To rename, use a dedicated view rename operation. |
| **`reportType` cannot be changed** | If the `reportType` in Update CONFIG does not match the existing view's type (chart/pivot/summary), the request fails with error `8021`. | Always carry `reportType` unchanged from the GET response when updating an existing view. |
| **`folderId` on Update** | If `folderId` is provided and **differs** from the current folder, the request throws `FOLDERID_CANNOT_BE_UPDATED`. If the same value is provided, it is a harmless no-op. | Omit `folderId` from the Update CONFIG entirely. `folderId` is not returned in the GET response, so it will naturally be absent if you use the GET response as your base. |
| **`description` is cleared if omitted** | `description` is read from the JSON input in both Create and Update paths. If absent from the Update CONFIG, the description is set to `null` (effectively cleared). | Always copy `description` from the GET response into your Update CONFIG to preserve it. |
| **`baseTableName` is ignored on Update** | The base table is derived from the existing view's stored parent reference — not from the CONFIG. Including `baseTableName` from the GET response is harmless but has no effect. | You may include it for consistency, but know it does nothing on Update. |
| **Axis type names are lowercase** | The GET response returns axis types in lowercase: `xaxis`, `yaxis`, `coloraxis`, `textaxis`, `sizeaxis`, `groupby`, `summarize`. These are the canonical values for the API. The doc may show mixed-case variants; always use the exact values from the GET response. | Copy axis `type` values verbatim from the GET response when constructing Create or Update CONFIG to avoid mismatch errors. |
| **Full axis reset** | On Update, the entire `axisColumns` array is replaced. Any axis column not in the new array is permanently removed from the view. | Fetch all current axis columns via GET, apply changes, and PUT the full updated array. |
| **Filters and user filters** | Like axis columns, `filters` and `userFilters` are fully replaced. Omitting them from the Update CONFIG removes all filters. | Include the full arrays from the GET response unless intentionally clearing them. |
| **`mergeAxisInfo` with `isAxisMerge`** | If `isAxisMerge` is `true`, `mergeAxisInfo` must also be provided. The GET response includes `mergeAxisInfo` when axis merge is active — use it as-is for Update. | When `isAxisMerge` is `false`, omit `mergeAxisInfo` entirely. |
| **Cross-workspace clone** | When cloning, `columnName` and `tableName` in `axisColumns` must match columns that exist in the **target workspace's** base table. | Verify column availability in the target workspace before POST. |
