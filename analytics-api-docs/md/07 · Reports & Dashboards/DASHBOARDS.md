# Dashboards APIs – Documentation

This document describes the V2 **Dashboards** REST APIs of Zoho Analytics — covering dashboard listing, creation, metadata retrieval, and updates.
APIs are documented with URL, method, OAuth scope, permissions, sample requests/responses, and error codes.

> Notes that apply to every API in this document:
> - All requests are authenticated via OAuth (`Authorization: Zoho-oauthtoken <token>`).
> - `ZohoAnalytics_Server_URI` depends on the data center (`analyticsapi.zoho.com`, `.eu`, etc.).
> - **Get All Dashboards, Get Owned Dashboards, and Get Shared Dashboards** (the listing APIs) operate at the **user service level** — they return dashboards across all organizations the caller belongs to. No `ZANALYTICS-ORGID` header is required.
> - **Create Dashboard, Get Dashboard Metadata, and Update Dashboard** (the workspace-scoped APIs) operate on a specific workspace. The `ZANALYTICS-ORGID` header is **mandatory**.
> - The three listing APIs are user-scoped — the OAuth token must be issued with user-level scope.
> - Get All Dashboards and Get Owned Dashboards are disabled on custom domains. Get Shared Dashboards works on custom domains. The three workspace-scoped APIs are accessible on custom domains, subject to permission checks.

---

## Index

| # | API NAME | METHOD | URL |
|---|----------|--------|-----|
| 1 | Get All Dashboards | GET | `/restapi/v2/dashboards` |
| 2 | Get Owned Dashboards | GET | `/restapi/v2/dashboards/owned` |
| 3 | Get Shared Dashboards | GET | `/restapi/v2/dashboards/shared` |
| 4 | Create Dashboard | POST | `/restapi/v2/workspaces/<workspace-id>/dashboards` |
| 5 | Get Dashboard Metadata | GET | `/restapi/v2/workspaces/<workspace-id>/dashboards/<dashboard-id>/metadata` |
| 6 | Update Dashboard | PUT | `/restapi/v2/workspaces/<workspace-id>/dashboards/<dashboard-id>` |

---

## 1. Get All Dashboards

| Attribute | Value |
|-----------|-------|
| **API NAME** | Get All Dashboards |
| **URL** | `GET https://<ZohoAnalytics_Server_URI>/restapi/v2/dashboards` |
| **METHOD** | GET |
| **DESCRIPTION** | Returns all dashboards accessible to the authenticated user — both dashboards owned by the user and dashboards shared with the user — across all organizations and workspaces. The response groups results into two separate lists: `ownedViews` and `sharedViews`. |
| **OAUTHSCOPE** | `ZohoAnalytics.metadata.read` |
| **PERMISSION REQUIRED** | The authenticated user must be any active **Zoho Analytics user**. |

> This API has no request body parameters. All context is derived from the OAuth token.

### Sample Requests

**Case 1: Retrieve all dashboards for the authenticated user**

```http
GET /restapi/v2/dashboards HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
```

**Case 2: Same request from a different data center (EU)**

```http
GET /restapi/v2/dashboards HTTP/1.1
Host: analyticsapi.zoho.eu
Authorization: Zoho-oauthtoken 1000.aaaaaa.bbbbbb
```

### Sample Responses

**Case 1 – Success: user has both owned and shared dashboards**

```http
HTTP/1.1 200 OK
Content-Type: application/json;charset=UTF-8

{
  "status": "success",
  "summary": "Get all dashboards",
  "data": {
    "ownedViews": [
      {
        "viewId": "466206000000105001",
        "viewName": "Executive Sales Dashboard",
        "viewDesc": "High-level sales KPIs for the executive team",
        "viewType": "Dashboard",
        "parentViewId": "",
        "folderId": "466206000000071005",
        "createdTime": "1719820800000",
        "createdBy": "alice@example.com",
        "lastModifiedTime": "1722499200000",
        "lastModifiedBy": "alice@example.com",
        "isFavorite": true,
        "sharedBy": "",
        "workspaceId": "466206000000071000",
        "orgId": "700000123456"
      },
      {
        "viewId": "466206000000108003",
        "viewName": "Marketing Campaign Overview",
        "viewDesc": "",
        "viewType": "Dashboard",
        "parentViewId": "",
        "folderId": "466206000000071000",
        "createdTime": "1720080000000",
        "createdBy": "alice@example.com",
        "lastModifiedTime": "1720080000000",
        "lastModifiedBy": "alice@example.com",
        "isFavorite": false,
        "sharedBy": "",
        "workspaceId": "466206000000071000",
        "orgId": "700000123456"
      }
    ],
    "sharedViews": [
      {
        "viewId": "466206000000200010",
        "viewName": "Finance Overview",
        "viewDesc": "Finance team quarterly dashboard",
        "viewType": "Dashboard",
        "parentViewId": "",
        "folderId": "466206000000190001",
        "createdTime": "1718640000000",
        "createdBy": "bob@example.com",
        "lastModifiedTime": "1721001600000",
        "lastModifiedBy": "bob@example.com",
        "isFavorite": false,
        "sharedBy": "bob@example.com",
        "workspaceId": "466206000000190000",
        "orgId": "700000123456"
      }
    ]
  }
}
```

**Case 2 – Success: user has only owned dashboards (empty shared list)**

```json
{
  "status": "success",
  "summary": "Get all dashboards",
  "data": {
    "ownedViews": [
      {
        "viewId": "466206000000105001",
        "viewName": "Executive Sales Dashboard",
        "viewDesc": "High-level sales KPIs",
        "viewType": "Dashboard",
        "parentViewId": "",
        "folderId": "466206000000071005",
        "createdTime": "1719820800000",
        "createdBy": "alice@example.com",
        "lastModifiedTime": "1722499200000",
        "lastModifiedBy": "alice@example.com",
        "isFavorite": true,
        "sharedBy": "",
        "workspaceId": "466206000000071000",
        "orgId": "700000123456"
      }
    ],
    "sharedViews": []
  }
}
```

**Case 3 – Success: user has no dashboards at all**

```json
{
  "status": "success",
  "summary": "Get all dashboards",
  "data": {
    "ownedViews": [],
    "sharedViews": []
  }
}
```

### Response Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `success` or `failure`. |
| `summary` | string | Always `"Get all dashboards"` on success. |
| `data.ownedViews` | JSONArray | List of dashboards owned by the authenticated user. |
| `data.sharedViews` | JSONArray | List of dashboards shared with the authenticated user. |

Each item in `ownedViews` and `sharedViews` has the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `viewId` | string | Unique ID of the dashboard. |
| `viewName` | string | Display name of the dashboard. |
| `viewDesc` | string | Description of the dashboard. Empty string if none. |
| `viewType` | string | Always `"Dashboard"` for dashboard entries. |
| `parentViewId` | string | ID of the parent view, if any. Empty string if none. |
| `folderId` | string | ID of the folder containing the dashboard. |
| `createdTime` | string | Dashboard creation timestamp in epoch milliseconds. |
| `createdBy` | string | Email address of the dashboard owner/creator. |
| `lastModifiedTime` | string | Last modification timestamp in epoch milliseconds. |
| `lastModifiedBy` | string | Email address of the user who last modified the dashboard. |
| `isFavorite` | boolean | `true` if the dashboard is marked as a favorite by the requesting user. |
| `sharedBy` | string | Email of the user who shared this dashboard. Present in shared entries; empty string in owned entries. |
| `workspaceId` | string | ID of the workspace containing the dashboard. |
| `orgId` | string | ID of the organization the workspace belongs to. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7301 | User does not have permission to retrieve dashboards. | Ensure the request uses a valid OAuth token for an active Zoho Analytics user. |
| 8535 | Invalid OAuth token. | Provide a valid, non-expired OAuth token in the `Authorization` header. |

---

## 2. Get Owned Dashboards

| Attribute | Value |
|-----------|-------|
| **API NAME** | Get Owned Dashboards |
| **URL** | `GET https://<ZohoAnalytics_Server_URI>/restapi/v2/dashboards/owned` |
| **METHOD** | GET |
| **DESCRIPTION** | Returns the list of dashboards owned by the authenticated user across all organizations. Only accessible to Account Admin users. The response contains a single `views` array listing all owned dashboards. |
| **OAUTHSCOPE** | `ZohoAnalytics.metadata.read` |
| **PERMISSION REQUIRED** | The authenticated user must be an **Account Admin**. |

> This API has no request body parameters. All context is derived from the OAuth token.

### Sample Requests

**Case 1: Account Admin retrieves all owned dashboards**

```http
GET /restapi/v2/dashboards/owned HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
```

**Case 2: Same request from the India data center**

```http
GET /restapi/v2/dashboards/owned HTTP/1.1
Host: analyticsapi.zoho.in
Authorization: Zoho-oauthtoken 1000.cccccc.dddddd
```

### Sample Responses

**Case 1 – Success: Account Admin owns multiple dashboards across workspaces**

```http
HTTP/1.1 200 OK
Content-Type: application/json;charset=UTF-8

{
  "status": "success",
  "summary": "Get owned dashboards",
  "data": {
    "views": [
      {
        "viewId": "466206000000105001",
        "viewName": "Executive Sales Dashboard",
        "viewDesc": "High-level sales KPIs for the executive team",
        "viewType": "Dashboard",
        "parentViewId": "",
        "folderId": "466206000000071005",
        "createdTime": "1719820800000",
        "createdBy": "admin@example.com",
        "lastModifiedTime": "1722499200000",
        "lastModifiedBy": "admin@example.com",
        "isFavorite": true,
        "sharedBy": "",
        "workspaceId": "466206000000071000",
        "orgId": "700000123456"
      },
      {
        "viewId": "466206000000305020",
        "viewName": "HR Headcount Overview",
        "viewDesc": "",
        "viewType": "Dashboard",
        "parentViewId": "",
        "folderId": "466206000000300000",
        "createdTime": "1716912000000",
        "createdBy": "admin@example.com",
        "lastModifiedTime": "1720339200000",
        "lastModifiedBy": "admin@example.com",
        "isFavorite": false,
        "sharedBy": "",
        "workspaceId": "466206000000300000",
        "orgId": "700000998877"
      }
    ]
  }
}
```

**Case 2 – Success: Account Admin owns dashboards in multiple organizations**

```json
{
  "status": "success",
  "summary": "Get owned dashboards",
  "data": {
    "views": [
      {
        "viewId": "466206000000105001",
        "viewName": "Sales Performance Dashboard",
        "viewDesc": "Monthly and quarterly sales metrics",
        "viewType": "Dashboard",
        "parentViewId": "",
        "folderId": "466206000000071000",
        "createdTime": "1715990400000",
        "createdBy": "admin@example.com",
        "lastModifiedTime": "1722499200000",
        "lastModifiedBy": "admin@example.com",
        "isFavorite": false,
        "sharedBy": "",
        "workspaceId": "466206000000071000",
        "orgId": "700000123456"
      }
    ]
  }
}
```

**Case 3 – Success: Account Admin has no owned dashboards**

```json
{
  "status": "success",
  "summary": "Get owned dashboards",
  "data": {
    "views": []
  }
}
```

### Response Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `success` or `failure`. |
| `summary` | string | Always `"Get owned dashboards"` on success. |
| `data.views` | JSONArray | List of dashboards owned by the authenticated Account Admin user. Each item follows the same field structure as in [Get All Dashboards](#1-get-all-dashboards) (see [Response Field Reference — per-dashboard item](#response-field-reference)). |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7301 | User does not have permission to retrieve owned dashboards. | Ensure the authenticated user is an **Account Admin**. |
| 8535 | Invalid OAuth token. | Provide a valid, non-expired OAuth token in the `Authorization` header. |

---

## 3. Get Shared Dashboards

| Attribute | Value |
|-----------|-------|
| **API NAME** | Get Shared Dashboards |
| **URL** | `GET https://<ZohoAnalytics_Server_URI>/restapi/v2/dashboards/shared` |
| **METHOD** | GET |
| **DESCRIPTION** | Returns all dashboards that have been shared with the authenticated user across all organizations and workspaces. The response contains a single `views` array. Unlike [Get All Dashboards](#1-get-all-dashboards), this endpoint returns only shared dashboards (not owned ones), and it is also available on custom domains. |
| **OAUTHSCOPE** | `ZohoAnalytics.metadata.read` |
| **PERMISSION REQUIRED** | The authenticated user must be any active **Zoho Analytics user**. |

> This API has no request body parameters. All context is derived from the OAuth token.

### Sample Requests

**Case 1: Retrieve all dashboards shared with the authenticated user**

```http
GET /restapi/v2/dashboards/shared HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
```

**Case 2: Same request on a custom domain**

```http
GET /restapi/v2/dashboards/shared HTTP/1.1
Host: analytics.example.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
```

### Sample Responses

**Case 1 – Success: user has multiple shared dashboards**

```http
HTTP/1.1 200 OK
Content-Type: application/json;charset=UTF-8

{
  "status": "success",
  "summary": "Get shared dashboards",
  "data": {
    "views": [
      {
        "viewId": "466206000000200010",
        "viewName": "Finance Overview",
        "viewDesc": "Finance team quarterly dashboard",
        "viewType": "Dashboard",
        "parentViewId": "",
        "folderId": "466206000000190001",
        "createdTime": "1718640000000",
        "createdBy": "bob@example.com",
        "lastModifiedTime": "1721001600000",
        "lastModifiedBy": "bob@example.com",
        "isFavorite": false,
        "sharedBy": "bob@example.com",
        "workspaceId": "466206000000190000",
        "orgId": "700000123456"
      },
      {
        "viewId": "466206000000410055",
        "viewName": "Supply Chain Dashboard",
        "viewDesc": "Inventory and logistics metrics",
        "viewType": "Dashboard",
        "parentViewId": "",
        "folderId": "466206000000400000",
        "createdTime": "1714780800000",
        "createdBy": "carol@example.com",
        "lastModifiedTime": "1719993600000",
        "lastModifiedBy": "carol@example.com",
        "isFavorite": true,
        "sharedBy": "carol@example.com",
        "workspaceId": "466206000000400000",
        "orgId": "700000998877"
      }
    ]
  }
}
```

**Case 2 – Success: user has one shared dashboard marked as favorite**

```json
{
  "status": "success",
  "summary": "Get shared dashboards",
  "data": {
    "views": [
      {
        "viewId": "466206000000200010",
        "viewName": "Regional Sales Tracker",
        "viewDesc": "Sales performance by region",
        "viewType": "Dashboard",
        "parentViewId": "",
        "folderId": "466206000000190000",
        "createdTime": "1720512000000",
        "createdBy": "dave@example.com",
        "lastModifiedTime": "1722067200000",
        "lastModifiedBy": "dave@example.com",
        "isFavorite": true,
        "sharedBy": "dave@example.com",
        "workspaceId": "466206000000190000",
        "orgId": "700000123456"
      }
    ]
  }
}
```

**Case 3 – Success: no dashboards have been shared with the user**

```json
{
  "status": "success",
  "summary": "Get shared dashboards",
  "data": {
    "views": []
  }
}
```

### Response Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `success` or `failure`. |
| `summary` | string | Always `"Get shared dashboards"` on success. |
| `data.views` | JSONArray | List of dashboards shared with the authenticated user. Each item follows the same field structure as in [Get All Dashboards](#1-get-all-dashboards) (see [Response Field Reference — per-dashboard item](#response-field-reference)). The `sharedBy` field is always populated for shared dashboards. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7301 | User does not have permission to retrieve shared dashboards. | Ensure the request uses a valid OAuth token for an active Zoho Analytics user. |
| 8535 | Invalid OAuth token. | Provide a valid, non-expired OAuth token in the `Authorization` header. |

---

## 4. Create Dashboard

| Attribute | Value |
|-----------|-------|
| **API ID** | 2060 |
| **Method** | POST |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/dashboards` |
| **OAuth Scope** | `ZohoAnalytics.modeling.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** |
| **Permission Required** | The authenticated user must be an **Account Admin** or **Organization Admin**, or a **Workspace Admin**, or a **Shared User**, or a **Group Member**, or any user with **Create Report** permission on the workspace. |

### CONFIG Parameter

The `CONFIG` parameter is a JSON object sent as a form field. `displayName` and `layout` are required.

| Field | Type | Mandatory | Description | Default |
|-------|------|-----------|-------------|---------|
| `displayName` | String | **Yes** | Display name of the new dashboard. Must be unique within the workspace. Max 100 characters. | — |
| `description` | String | No | Optional text description for the dashboard. Max 250 characters. | `""` |
| `layout` | JSON Object | **Yes** | Layout card map. Keys are sequential card index strings (`"1"`, `"2"`, …). Each value is a layout card object (see sub-table below). | — |
| `layoutType` | Integer | No | Grid column preset applied at creation time: `1` = single column, `2` = two columns, `3` = three columns, `4` = four columns. Only meaningful when combined with a `layout` that uses the grid. | `0` (free form) |
| `themes` | JSON Object | No | Visual theme configuration (see Themes Object below). | Default theme |
| `settings` | JSON Object | No | Dashboard behaviour settings (see Settings Object below). | System defaults |

#### Layout Card Object

Each entry in `layout` is keyed by its card index (e.g., `"1"`, `"2"`) and contains the following fields:

| Field | Type | Mandatory | Description |
|-------|------|-----------|-------------|
| `type` | String | **Yes** | Card type. Allowed values: `VIEW`, `HTML`, `TITLE`, `PARA`, `IMAGE`, `EMBED`, `USERFILTERS`, `DELETED`. |
| `width` | Integer | **Yes** | Card width in grid units. Combined with `left`, must not exceed `80`. |
| `height` | Integer | **Yes** | Card height in grid units. Minimum varies by type (USERFILTERS: 3, HTML: 5, others: depends). |
| `left` | Integer | **Yes** | Left offset in grid units (0–79). |
| `top` | Integer | **Yes** | Top offset in grid units (0+). |
| `viewName` | String | Yes (for `VIEW`) | Display name of the existing analysis view to embed. Required when `type` is `VIEW`. |
| `content` | String | Yes (for HTML/IMAGE/EMBED/TITLE/PARA) | HTML markup, image URL, or embed URL depending on card type. |
| `properties` | JSON Object | No | Additional card-level properties (e.g., interaction overrides). Optional for `VIEW` cards. |

#### Themes Object

| Field | Type | Description | Allowed Values / Constraints |
|-------|------|-------------|------------------------------|
| `default` | String | Reset theme to built-in defaults. If set to `"true"`, all other theme fields are ignored. | `"true"`, `"unset"` |
| `type` | String | Background fill style. | `solid`, `gradient`, `image` |
| `layoutType` | Integer | Preset layout theme number (1–6). | `1`–`6` |
| `solid` | Object | Solid background config. Contains `background` (hex color). | — |
| `gradient` | Object | Gradient background (see Gradient Sub-Object below). | — |
| `image` | Object | Image background (see Image Sub-Object below). | — |
| `font` | Object | Global font settings. Contains `color` (hex), `family` (font name), `size` (7–24), `style` (`plain`, `bold`, `italic`). | — |
| `card` | Object | Card-level styling (see Card Sub-Object below). | — |
| `chartEffect` | Object | Chart animation effect. Contains `apply` (**mandatory**, `1`=none / `2`=apply) and `type` (`1`–`3`). | — |
| `palette` | Object | Color palette for charts. Contains `chart.type` (palette name string). | — |

**Gradient Sub-Object:**

| Field | Type | Description | Allowed Values |
|-------|------|-------------|----------------|
| `background` | String | Fallback background color (hex). | Hex color |
| `startColor` | String | Gradient start color (hex). | Hex color |
| `endColor` | String | Gradient end color (hex). | Hex color |
| `mode` | String | Gradient direction mode. | `linear`, `radial` |
| `linear.angle` | Integer | Angle of the linear gradient in degrees (-270 to 270). | `-270`–`270` |
| `radial.x` | Integer | Horizontal focal point of radial gradient (0–180). | `0`–`180` |
| `radial.y` | Integer | Vertical focal point of radial gradient (0–180). | `0`–`180` |

**Image Sub-Object:**

| Field | Type | Description | Allowed Values |
|-------|------|-------------|----------------|
| `url` | String | URL of the background image. | Valid URL |
| `background` | String | Fallback color behind the image (hex). | Hex color |
| `brightness` | Integer | Brightness adjustment (-100 to 100). | `-100`–`100` |
| `contrast` | Integer | Contrast adjustment (-100 to 100). | `-100`–`100` |
| `transparency` | String | Transparency percentage as a string (`"0"`–`"100"`). | `"0"`–`"100"` |
| `flip` | String | Whether to flip the image (`"true"` / `"false"`). | `"true"`, `"false"` |
| `fitType` | String | Image fit strategy (`"1"` = cover, `"2"` = contain, `"3"` = stretch). | `"1"`, `"2"`, `"3"` |

**Card Sub-Object:**

| Field | Type | Description | Allowed Values |
|-------|------|-------------|----------------|
| `background` | String | Card background color (hex). | Hex color |
| `opacity` | Float | Card background opacity (0.0–1.0). | `0.0`–`1.0` |
| `blur` | Integer | Background blur radius (0–50). | `0`–`50` |
| `radius` | Integer | Card corner radius (0–20). | `0`–`20` |
| `margin` | Integer | Card outer margin (0–10). | `0`–`10` |
| `shadow` | Integer | Card shadow style (1–3). | `1`–`3` |
| `paletteType` | Integer | Card palette variant (`1` = themed, `2` = custom). | `1`, `2` |
| `border` | Object | Card border. Contains `color` (hex) and `width` (string, `"0"`–`"5"`). | — |
| `title` | Object | Card title font. Contains nested `font` object (`color`, `family`, `size`, `style`). | — |
| `desc` | Object | Card description font. Contains nested `font` object (`color`, `family`, `size`, `style`). | — |

#### Settings Object

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `enableGlobalUF` | String | Enable global user filter for all cards. | `"false"` |
| `enableGlobalValueUF` | String | Enable global value-based user filter. | `"false"` |
| `smartAlignCharts` | String | Auto-align charts to the grid. | `"true"` |
| `allowExport` | Object | Controls which export formats are enabled. Contains boolean string fields: `csv`, `excel`, `html`, `image`, `pdf`, `zohoSheet`. | All `"true"` |
| `showContextualOptions` | String | Show contextual chart options to viewers. | `"true"` |
| `allowEmbedInsights` | String | Allow embedding AI insights in dashboards. | `"true"` |
| `enableSortMenu` | String | Show sort options in viewer mode. | `"true"` |
| `reportAsFilter` | String | Allow charts to act as filters for other charts. | `"false"` |
| `hideColumnOptions` | String | Hide column-level options in viewer mode. | `"true"` |
| `allowVUD` | String | Allow view/update/delete interactions. | `"true"` |
| `allowInsights` | String | Enable AI-powered insights. | `"true"` |
| `fitToWidth` | String | Stretch dashboard to fill browser width. | `"true"` |
| `layoutType` | String | Layout width mode. | `"web"` |
| `layoutWidth` | String | Custom layout width in pixels (only when `layoutType` is `custom_width`). | `"1279"` |
| `allowDrillDown` | String | Enable drill-down on chart data points. | `"true"` |
| `applyImmediateUF` | String | Apply user filter values immediately (without a submit button). | `"true"` |
| `timeSlicer` | String | Enable time-slicer user filter component. | `"false"` |
| `mapSync` | String | Sync map view across dashboard cards. | `"false"` |

> **layoutType allowed values:** `web`, `custom_width`, `tabloid_1056`, `letter_816`, `a4_797`, `a3_1123`

### Sample Requests

**Case 1 — Minimal dashboard with a single chart and default theme**

```http
POST /restapi/v2/workspaces/320873000000001001/dashboards HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 320873000000000001
Content-Type: application/x-www-form-urlencoded

CONFIG={"displayName":"Sales Overview","description":"Monthly sales KPIs","layout":{"1":{"type":"VIEW","width":40,"height":20,"left":0,"top":0,"viewName":"Monthly_Sales_Chart","properties":{}},"2":{"type":"VIEW","width":40,"height":20,"left":40,"top":0,"viewName":"Sales_Pivot","properties":{}}}}
```

**Case 2 — Dashboard with gradient theme, card styling, and restricted export**

```http
POST /restapi/v2/workspaces/320873000000001001/dashboards HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 320873000000000001
Content-Type: application/x-www-form-urlencoded

CONFIG={"displayName":"Dashboard_Gradient_Linear_3","themes":{"layoutType":6,"type":"gradient","gradient":{"background":"#bf00ff","startColor":"#bf00ff","endColor":"#000000","mode":"linear","linear":{"angle":270}},"font":{"color":"#bf00ff","family":"arial"},"card":{"background":"#00ff00","opacity":0.2,"blur":5,"margin":10,"radius":5,"shadow":3,"paletteType":2},"chartEffect":{"apply":2,"type":1},"palette":{"chart":{"type":"SOLID__BUSINESS"}}},"settings":{"allowDrillDown":"true","smartAlignCharts":"true","reportAsFilter":"true","showContextualOptions":"false","allowExport":{"csv":"true"},"fitToWidth":"false","enableGlobalUF":"true","applyImmediateUF":"true"},"layout":{"1":{"type":"VIEW","width":40,"height":20,"left":0,"top":8,"viewName":"Chart2","properties":{}},"2":{"type":"USERFILTERS","width":80,"height":3,"left":0,"top":0}}}
```

**Case 3 — Dashboard with image background, HTML card, and image card**

```http
POST /restapi/v2/workspaces/320873000000001001/dashboards HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 320873000000000001
Content-Type: application/x-www-form-urlencoded

CONFIG={"displayName":"Dashboard_Image_Theme_6","themes":{"layoutType":6,"type":"image","image":{"url":"https://example.com/bg.jpg","brightness":2,"flip":"true","transparency":"40","fitType":"2","contrast":5,"background":"#bf00ff"},"font":{"color":"#bf00ff","family":"arial"},"card":{"background":"#00ff00","opacity":0.2,"blur":5,"margin":10,"radius":5,"shadow":3,"paletteType":2},"chartEffect":{"apply":1},"palette":{"chart":{"type":"SOLID__BUSINESS"}}},"layout":{"1":{"type":"HTML","width":80,"height":5,"left":0,"top":0,"content":"<div><h2 style=\"font-family: Arial\">Dashboard Header</h2></div>"},"2":{"type":"IMAGE","width":40,"height":15,"left":0,"top":5,"content":"https://example.com/logo.png"},"3":{"type":"VIEW","width":40,"height":20,"left":40,"top":5,"viewName":"Pivot","properties":{}}}}
```

### Sample Response

**HTTP 200 OK**

```json
{
  "status": "success",
  "summary": "Create dashboard",
  "data": {
    "dashboardId": "320873000000597763",
    "displayName": "Sales Overview"
  }
}
```

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify the `<workspace-id>` in the URL is correct and accessible to the user. |
| 7111 | A dashboard with the same name already exists in the workspace. | Use a different `displayName` value. |
| 7301 | User does not have permission to create a dashboard. | Ensure the user is an Account Admin, Organization Admin, Workspace Admin, Shared User, Group Member, or has Create Report permission. |
| 8072 | The target object is not a valid dashboard. | Verify the request parameters and ensure the workspace supports dashboard creation. |
| 8119 | One or more CONFIG field values are invalid (e.g., invalid color, out-of-range number). | Review the CONFIG JSON and correct the invalid values. |
| 8535 | Invalid OAuth token. | Provide a valid, non-expired OAuth token with the `ZohoAnalytics.modeling.create` scope. |

---

## 5. Get Dashboard Metadata

| Attribute | Value |
|-----------|-------|
| **API ID** | 2061 |
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/dashboards/<dashboard-id>/metadata` |
| **OAuth Scope** | `ZohoAnalytics.modeling.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** |
| **Permission Required** | The authenticated user must be an **Account Admin** or **Organization Admin**, or the **View Owner**, or any user with **Read Only** permission on the dashboard. |

### CONFIG Parameter (Optional)

| Field | Type | Mandatory | Description | Default | Allowed Values |
|-------|------|-----------|-------------|---------|----------------|
| `include` | String | No | Controls which sections of the dashboard config to include in the response. | `all` | `all`, `themes`, `layout`, `settings` |

> When `include` is `"all"`, the response includes `objId`, `displayName`, `description`, `themes`, `layout`, and `settings`.  
> When `include` is set to a specific section (e.g., `"themes"`), only that section is returned (without `objId`/`displayName`/`description`).  
> Multiple sections can be requested via comma-separated values (e.g., `"themes,layout"`).

### Sample Requests

**Case 1 — Retrieve full metadata (all sections)**

```http
GET /restapi/v2/workspaces/320873000000001001/dashboards/320873000000597763/metadata HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 320873000000000001
```

**Case 2 — Retrieve only the layout section**

```http
GET /restapi/v2/workspaces/320873000000001001/dashboards/320873000000597763/metadata?CONFIG={"include":"layout"} HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 320873000000000001
```

**Case 3 — Retrieve themes and settings only**

```http
GET /restapi/v2/workspaces/320873000000001001/dashboards/320873000000597763/metadata?CONFIG={"include":"themes,settings"} HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 320873000000000001
```

### Sample Responses

**Case 1 — Default theme dashboard with VIEW and USERFILTERS cards (HTTP 200 OK)**

```json
{
  "status": "success",
  "summary": "Get dashboard metadata",
  "data": {
    "dashboardConfig": {
      "objId": "320873000000597763",
      "displayName": "Dashboard_Freeform_19",
      "description": "",
      "themes": {
        "default": "true",
        "layoutType": "2"
      },
      "settings": {
        "enableGlobalUF": "false",
        "smartAlignCharts": "true",
        "allowExport": {
          "pdf": "true",
          "excel": "true",
          "zohoSheet": "true",
          "image": "true",
          "csv": "true",
          "html": "true"
        },
        "showContextualOptions": "true",
        "allowEmbedInsights": "true",
        "enableSortMenu": "true",
        "reportAsFilter": "false",
        "hideColumnOptions": "true",
        "layoutWidth": "1279",
        "allowVUD": "true",
        "allowInsights": "true",
        "fitToWidth": "true",
        "layoutType": "web",
        "allowDrillDown": "true",
        "applyImmediateUF": "true",
        "timeSlicer": "false"
      },
      "layout": {
        "1": {
          "type": "USERFILTERS",
          "width": 80,
          "height": 3,
          "left": 0,
          "top": 0
        },
        "2": {
          "type": "VIEW",
          "width": 80,
          "height": 20,
          "left": 0,
          "top": 3,
          "viewName": "Sales_Report"
        }
      }
    }
  }
}
```

**Case 2 — Dashboard with HTML card (HTTP 200 OK)**

```json
{
  "status": "success",
  "summary": "Get dashboard metadata",
  "data": {
    "dashboardConfig": {
      "objId": "320873000000597796",
      "displayName": "Dashboard_HtmlCard_26",
      "description": "",
      "themes": {
        "default": "true",
        "layoutType": "2"
      },
      "settings": {
        "smartAlignCharts": "true",
        "allowExport": { "pdf": "true", "excel": "true", "zohoSheet": "true", "image": "true", "csv": "true", "html": "true" },
        "fitToWidth": "true",
        "allowDrillDown": "true",
        "applyImmediateUF": "true"
      },
      "layout": {
        "1": {
          "type": "HTML",
          "width": 80,
          "height": 5,
          "left": 0,
          "top": 0,
          "content": "<div><h2 style=\"font-family: Arial; color: #2c3e50;\">Dashboard Header</h2><p>This is a <strong>styled HTML</strong> content card.</p></div>"
        },
        "2": {
          "type": "VIEW",
          "width": 80,
          "height": 20,
          "left": 0,
          "top": 5,
          "viewName": "Pivot"
        }
      }
    }
  }
}
```

**Case 3 — Dashboard with IMAGE card**

```json
{
  "status": "success",
  "summary": "Get dashboard metadata",
  "data": {
    "dashboardConfig": {
      "objId": "320873000000597718",
      "displayName": "Dashboard_ImageCard_9",
      "description": "",
      "themes": {
        "layoutType": "2",
        "solid": { "background": "#ffffff" },
        "type": "solid",
        "card": { "background": "#ffffff" }
      },
      "settings": {
        "smartAlignCharts": "true",
        "allowExport": { "pdf": "true", "excel": "true", "zohoSheet": "true", "image": "true", "csv": "true", "html": "true" },
        "fitToWidth": "true",
        "allowDrillDown": "true"
      },
      "layout": {
        "1": {
          "type": "IMAGE",
          "width": 40,
          "height": 15,
          "left": 0,
          "top": 0,
          "content": "https://example.com/banner.jpg"
        },
        "2": {
          "type": "VIEW",
          "width": 40,
          "height": 20,
          "left": 40,
          "top": 0,
          "viewName": "Sales_Table"
        }
      }
    }
  }
}
```

**Case 4 — Dashboard with gradient theme and card styling**

```json
{
  "status": "success",
  "summary": "Get dashboard metadata",
  "data": {
    "dashboardConfig": {
      "objId": "320873000000487179",
      "displayName": "Dashboard_Gradient_Linear_3",
      "description": "",
      "themes": {
        "card": {
          "desc": { "font": { "size": "9", "color": "#bf00ff", "family": "verdana", "style": "italic" } },
          "shadow": "3",
          "paletteType": "2",
          "radius": "5",
          "margin": "10",
          "opacity": "0.2",
          "background": "#00ff00",
          "title": { "font": { "size": "8", "family": "sans-serif", "style": "bold", "color": "#bf00ff" } },
          "blur": "5"
        },
        "palette": { "chart": { "type": "SOLID__BUSINESS" } },
        "gradient": {
          "endColor": "#000000",
          "mode": "linear",
          "linear": { "angle": "270" },
          "startColor": "#bf00ff",
          "background": "#bf00ff"
        },
        "type": "gradient",
        "chartEffect": { "type": "1", "apply": "2" },
        "layoutType": "6",
        "font": { "color": "#bf00ff", "family": "arial" }
      },
      "settings": {
        "enableGlobalUF": "true",
        "smartAlignCharts": "true",
        "allowExport": { "pdf": "false", "excel": "false", "zohoSheet": "false", "image": "false", "csv": "true", "html": "false" },
        "showContextualOptions": "false",
        "allowEmbedInsights": "true",
        "reportAsFilter": "true",
        "allowDrillDown": "true",
        "applyImmediateUF": "true"
      },
      "layout": {
        "1": { "type": "USERFILTERS", "width": 80, "height": 3, "left": 0, "top": 0 },
        "2": { "type": "VIEW", "width": 40, "height": 20, "left": 0, "top": 8, "viewName": "Chart2" }
      }
    }
  }
}
```

**Case 5 — Full card styling with theme overview (solid type, all card borders and palette)**

```json
{
  "status": "success",
  "summary": "Get dashboard metadata",
  "data": {
    "dashboardConfig": {
      "objId": "320873000000487208",
      "displayName": "Dashboard_ThemeOverviewDefault_47",
      "description": "",
      "themes": {
        "chartEffect": { "apply": "1" },
        "card": {
          "border": { "color": "#cccccc", "width": "1" },
          "shadow": "2",
          "paletteType": "1",
          "blur": "0",
          "radius": "5",
          "margin": "10",
          "opacity": "0.5",
          "background": "#ffffff"
        },
        "palette": { "chart": { "type": "SOLID__BUSINESS" } },
        "type": "solid",
        "font": { "color": "#000000", "family": "Arial" },
        "layoutType": "1",
        "solid": { "background": "#ffffff" }
      },
      "settings": {
        "enableGlobalUF": "false",
        "smartAlignCharts": "true",
        "allowExport": { "pdf": "true", "excel": "true", "zohoSheet": "true", "image": "true", "csv": "true", "html": "true" },
        "showContextualOptions": "true",
        "enableSortMenu": "true",
        "allowVUD": "true",
        "allowInsights": "true",
        "fitToWidth": "true",
        "allowDrillDown": "true",
        "applyImmediateUF": "true"
      },
      "layout": {
        "1": { "type": "VIEW", "width": 40, "height": 20, "left": 0, "top": 0, "viewName": "Pivot" }
      }
    }
  }
}
```

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify the `<workspace-id>` in the URL. |
| 7104 | Dashboard not found. | Verify the `<dashboard-id>` exists and belongs to the specified workspace. |
| 7301 | User does not have permission to view this dashboard. | Ensure the user is an Account Admin, Organization Admin, View Owner, or has Read Only permission on the dashboard. |
| 8072 | The target object is not a valid dashboard. | Verify the `<dashboard-id>` refers to a dashboard (not a report or other view type). |
| 8102 | Dashboard view type not supported for this operation. | The requested dashboard may be a tabbed dashboard, which is not supported via this API. |
| 8119 | Invalid value supplied for the `include` parameter. | Use one or more of: `all`, `themes`, `layout`, `settings`. |
| 8535 | Invalid OAuth token. | Provide a valid, non-expired OAuth token with the `ZohoAnalytics.modeling.read` scope. |

---

## 6. Update Dashboard

| Attribute | Value |
|-----------|-------|
| **API ID** | 2062 |
| **Method** | PUT |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/dashboards/<dashboard-id>` |
| **OAuth Scope** | `ZohoAnalytics.modeling.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** |
| **Permission Required** | The authenticated user must be an **Account Admin** or **Organization Admin**, or the **View Owner**, or any user with **Design Modify** permission on the dashboard. |

### CONFIG Parameter

The `CONFIG` parameter is a JSON object. All fields are optional — only the fields provided are updated. To clear the theme back to defaults, use `"default": "true"` inside `themes`.

> **Note:** The `displayName` and `description` fields are **not** part of the Update Dashboard CONFIG. Use a dedicated rename API to change the dashboard name.

| Field | Type | Mandatory | Description | Default |
|-------|------|-----------|-------------|---------|
| `layoutType` | Integer | No | Grid column preset: `1`–`4` (see Create Dashboard for values). | Unchanged |
| `layout` | JSON Object | No | Replacement layout card map. Replaces the entire layout when provided. Card structure is identical to Create Dashboard. | Unchanged |
| `themes` | JSON Object | No | Updated theme settings. Set `"default": "true"` inside to reset to system defaults. Same structure as Create Dashboard `themes`. | Unchanged |
| `settings` | JSON Object | No | Updated settings. Only the settings keys provided are updated (partial update). Same structure as Create Dashboard `settings`. | Unchanged |

### Sample Requests

**Case 1 — Update layout to add a new chart card**

```http
PUT /restapi/v2/workspaces/320873000000001001/dashboards/320873000000597763 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 320873000000000001
Content-Type: application/x-www-form-urlencoded

CONFIG={"layout":{"1":{"type":"VIEW","width":40,"height":20,"left":0,"top":0,"viewName":"Sales_Chart","properties":{}},"2":{"type":"VIEW","width":40,"height":20,"left":40,"top":0,"viewName":"Revenue_Pivot","properties":{}},"3":{"type":"USERFILTERS","width":80,"height":3,"left":0,"top":20}}}
```

**Case 2 — Update to solid theme with custom card styling**

```http
PUT /restapi/v2/workspaces/320873000000001001/dashboards/320873000000597763 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 320873000000000001
Content-Type: application/x-www-form-urlencoded

CONFIG={"themes":{"layoutType":1,"type":"solid","solid":{"background":"#333542"},"card":{"background":"#3E3F4D","border":{"color":"#6F738E","width":"2"},"title":{"border":{"color":"#6F738E"}}},"font":{"color":"#ffffff","family":"Arial"},"chartEffect":{"apply":1}}}
```

**Case 3 — Update settings only (restrict exports, enable global filter)**

```http
PUT /restapi/v2/workspaces/320873000000001001/dashboards/320873000000597763 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 320873000000000001
Content-Type: application/x-www-form-urlencoded

CONFIG={"settings":{"enableGlobalUF":"true","allowExport":{"pdf":"false","excel":"true","zohoSheet":"false","csv":"true","html":"false"},"reportAsFilter":"true","fitToWidth":"false"}}
```

### Sample Response

**HTTP 204 No Content** — The Update Dashboard API returns no response body on success. A 204 status confirms the dashboard was updated.

```
HTTP/1.1 204 No Content
```

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify the `<workspace-id>` in the URL. |
| 7104 | Dashboard not found. | Verify the `<dashboard-id>` exists and belongs to the specified workspace. |
| 7301 | User does not have permission to update this dashboard. | Ensure the user is an Account Admin, Organization Admin, View Owner, or has Design Modify permission on the dashboard. |
| 8072 | The target object is not a valid dashboard. | Verify the `<dashboard-id>` refers to a dashboard. |
| 8102 | Dashboard view type not supported for this operation. | Tabbed dashboards cannot be updated via this API. |
| 8119 | One or more CONFIG field values are invalid (e.g., out-of-range numbers, invalid colors). | Review the CONFIG JSON and correct the invalid values. |
| 8535 | Invalid OAuth token. | Provide a valid, non-expired OAuth token with the `ZohoAnalytics.modeling.update` scope. |

---

## Appendix A – Common HTTP Headers

The `Authorization` header is required for all APIs. The `ZANALYTICS-ORGID` header is required only for workspace-scoped APIs (4–6).

| Header | Value | Required | Description |
|--------|-------|----------|-------------|
| `Authorization` | `Zoho-oauthtoken <oauth-token>` | **Mandatory** | OAuth token of the calling user. Must be a user-scope token. |
| `ZANALYTICS-ORGID` | — | **Not required** for the listing APIs / **Mandatory** for the workspace-scoped APIs | Get All Dashboards, Get Owned Dashboards, and Get Shared Dashboards are user-scoped and do not need an organization ID. Create Dashboard, Get Dashboard Metadata, and Update Dashboard require the `ZANALYTICS-ORGID` header with the target organization's ID. |

Example — Listing API (no org header):

```http
GET /restapi/v2/dashboards HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
```

Example — Workspace-scoped API (org header required):

```http
POST /restapi/v2/workspaces/320873000000001001/dashboards HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 320873000000000001
Content-Type: application/x-www-form-urlencoded
```

---

## Appendix B – OAuth Scope Summary

| API | HTTP Method | Scope |
|-----|-------------|-------|
| Get All Dashboards | GET | `ZohoAnalytics.metadata.read` |
| Get Owned Dashboards | GET | `ZohoAnalytics.metadata.read` |
| Get Shared Dashboards | GET | `ZohoAnalytics.metadata.read` |
| Create Dashboard | POST | `ZohoAnalytics.modeling.create` |
| Get Dashboard Metadata | GET | `ZohoAnalytics.modeling.read` |
| Update Dashboard | PUT | `ZohoAnalytics.modeling.update` |

---

## Appendix C – Response Payload Notes

| Field | Description |
|-------|-------------|
| `status` | `success` or `failure`. Standard Zoho Analytics V2 response envelope. |
| `summary` | Human-readable description of the completed operation. |
| `data.ownedViews` | (Get All Dashboards only) Dashboards created/owned by the requesting user. |
| `data.sharedViews` | (Get All Dashboards only) Dashboards shared with the requesting user by others. |
| `data.views` | (Get Owned Dashboards and Get Shared Dashboards) Single unified list — owned-only or shared-only based on the endpoint. |
| `viewId` | Returned as a **string** even though the underlying value is a long integer. |
| `workspaceId` | Returned as a **string**. Use this as `<workspace-id>` in workspace-scoped API calls. |
| `orgId` | Returned as a **string**. Corresponds to the `ZANALYTICS-ORGID` header value in workspace-scoped APIs. |
| `createdTime` / `lastModifiedTime` | Epoch timestamps in **milliseconds** as strings. Divide by 1000 to convert to Unix epoch seconds. |
| `sharedBy` | Present in all dashboard entries; empty string (`""`) in owned items, populated with email in shared items. |
| `isFavorite` | User-specific: `true` if the **requesting user** has marked this dashboard as a favorite. |
| `data.dashboardId` | (Create API only) ID of the newly created dashboard, returned as a string. |
| `data.displayName` | (Create API only) Display name of the newly created dashboard as stored. |
| `data.dashboardConfig` | (Get Metadata API only) Wrapper object containing full dashboard configuration. |
| `data.dashboardConfig.objId` | Dashboard ID as a string. |
| `data.dashboardConfig.themes` | Object describing the active visual theme (type, background, fonts, cards, palette, effects). |
| `data.dashboardConfig.settings` | Object describing dashboard behaviour settings (export, drill-down, UF, etc.). |
| `data.dashboardConfig.layout` | Object where each key is a card index string (`"1"`, `"2"`, …) and each value is a card configuration. |

> **Custom domain note:** Get Shared Dashboards works on custom domains. Get All Dashboards and Get Owned Dashboards are disabled on custom domains. Create Dashboard, Get Dashboard Metadata, and Update Dashboard are accessible on custom domains but subject to additional permission checks.

---

## Appendix D – Working with Get, Create, and Update Together

### Why Get Dashboard Metadata Before Update

The **Update Dashboard** API performs a **full section replacement** — not a merge. When you include `layout`, `themes`, or `settings` in an Update request, the server:

1. Deletes **all** stored rows for that section
2. Stores exactly what you sent

If you only send `{"settings": {"enableGlobalUF": "true"}}`, every other setting reverts to the system default. To avoid unintended data loss, always **fetch first, modify, then update**.

---

### Workflow 1 — Read-Modify-Write (Safe Update)

**Step 1: Fetch only the section you need to change**

Use `include` to avoid fetching the full config when you only need one section:

```http
GET /restapi/v2/workspaces/320873000000001001/dashboards/320873000000597763/metadata?CONFIG={"include":"settings"}
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 320873000000000001
```

Response — only the stored (non-default) settings are returned:

```json
{
  "data": {
    "dashboardConfig": {
      "settings": {
        "smartAlignCharts": "true",
        "fitToWidth": "true",
        "allowDrillDown": "true",
        "allowExport": { "pdf": "true", "excel": "true", "csv": "true", "html": "true", "image": "true", "zohoSheet": "true" }
      }
    }
  }
}
```

**Step 2: Modify the desired key(s) in the returned object**

Add `enableGlobalUF` to the settings object from the response:

```json
{
  "smartAlignCharts": "true",
  "fitToWidth": "true",
  "allowDrillDown": "true",
  "enableGlobalUF": "true",
  "allowExport": { "pdf": "true", "excel": "true", "csv": "true", "html": "true", "image": "true", "zohoSheet": "true" }
}
```

**Step 3: Send the complete modified object in the Update**

```http
PUT /restapi/v2/workspaces/320873000000001001/dashboards/320873000000597763
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 320873000000000001
Content-Type: application/x-www-form-urlencoded

CONFIG={"settings":{"smartAlignCharts":"true","fitToWidth":"true","allowDrillDown":"true","enableGlobalUF":"true","allowExport":{"pdf":"true","excel":"true","csv":"true","html":"true","image":"true","zohoSheet":"true"}}}
```

> Apply the same pattern for `themes` and `layout` — always send the full section back, not just the changed keys.

---

### Workflow 2 — Layout Update Without Losing Cards

The layout is a complete card map. Sending a partial layout (e.g., only 2 cards) replaces the entire layout with those 2 cards. To add a card without removing others:

**Step 1: Fetch the current layout**

```http
GET .../metadata?CONFIG={"include":"layout"}
```

**Step 2: Append the new card to the returned layout object**

The card index key must be the next sequential number. Existing card indices from the GET response are preserved:

```json
{
  "1": { "type": "USERFILTERS", "width": 80, "height": 3, "left": 0, "top": 0 },
  "2": { "type": "VIEW", "width": 40, "height": 20, "left": 0, "top": 3, "viewName": "Sales_Report" },
  "3": { "type": "VIEW", "width": 40, "height": 20, "left": 40, "top": 3, "viewName": "Revenue_Chart" }
}
```

**Step 3: PUT the full layout back**

```http
PUT .../dashboards/320873000000597763
...
CONFIG={"layout":{"1":{"type":"USERFILTERS","width":80,"height":3,"left":0,"top":0},"2":{"type":"VIEW","width":40,"height":20,"left":0,"top":3,"viewName":"Sales_Report"},"3":{"type":"VIEW","width":40,"height":20,"left":40,"top":3,"viewName":"Revenue_Chart"}}}
```

---

### Workflow 3 — Cloning a Dashboard (Get → Create)

Use the full metadata of an existing dashboard as a template for a new one:

**Step 1: Fetch full metadata of the source dashboard**

```http
GET /restapi/v2/workspaces/320873000000001001/dashboards/320873000000597763/metadata
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 320873000000000001
```

**Step 2: Take `layout`, `themes`, `settings` from the response `dashboardConfig` object**

Strip out `objId`, `displayName`, `description` — these are read-only fields in the GET response and are not valid CONFIG fields for Create.

**Step 3: POST to Create Dashboard with a new `displayName`**

```http
POST /restapi/v2/workspaces/320873000000001001/dashboards
Content-Type: application/x-www-form-urlencoded

CONFIG={
  "displayName": "Sales Overview - Copy",
  "description": "Cloned from Sales Overview dashboard",
  "layout": { <layout from GET response> },
  "themes": { <themes from GET response> },
  "settings": { <settings from GET response> }
}
```

> **Note:** `viewName` values inside `layout` must match the display names of existing analysis views in the **target workspace**. If cloning across workspaces, update the `viewName` values accordingly before posting.

---

### Special Cases and Caveats

| Case | Behaviour | Recommendation |
|------|-----------|----------------|
| **Partial settings in Update** | If you send `settings` with only some keys, all other settings revert to system defaults. Only explicitly-set values are stored. | Always send the full settings object (fetched via GET) with your changes merged in. |
| **Omitting a section in Update** | If `layout`, `themes`, or `settings` is absent from the CONFIG, that section is **not changed**. Safe to omit sections you are not modifying. | Only include the section(s) you intend to replace. |
| **`layoutType` preset in Create/Update** | When `layoutType` is `1`–`4` (grid preset), the server **auto-injects** a USERFILTERS card at position `"1"` and rearranges view cards into columns. Your input card order may be renumbered. | Omit `layoutType` (or set to `0`) for free-form layouts. Use GET after Create/Update to confirm the final stored layout. |
| **`viewName` in layout cards** | Identifies an analysis view by its **display name** (not ID). If the referenced view is renamed or deleted, the card will show as broken in the dashboard. | Always verify view names using the Reports API before sending layout. |
| **Reset theme to defaults** | Send `{"themes": {"default": "true"}}` in Update to clear all custom theme settings and restore the system default theme. | Use this to undo theme customizations in a single call without needing to know the original values. |
| **`objId` in GET response** | The `dashboardConfig.objId` field is the dashboard ID. Use it directly as `<dashboard-id>` in the Update URL. | `objId` = `dashboardId` (Create response) = `viewId` (listing API response). Same value, different field names. |
| **Tabbed dashboards** | Error `8102` is returned if you call Get Metadata or Update on a tabbed dashboard. These are not supported via the V2 API. | Use the UI or check the dashboard type before calling these APIs. |
| **`include` with comma-separated values** | Requesting `include=themes,layout` returns both sections without `objId`, `displayName`, or `description`. These top-level identity fields are only included when `include=all` (or omitted). | Always use `include=all` (default) when you need identity fields for clone workflows. |
