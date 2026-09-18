# Zoho Analytics V2 REST API — Custom Formula Columns

This document covers the APIs for creating, editing, deleting, listing, and copying **custom formula columns** — computed columns whose values are derived from an expression referencing other columns in the same table/view.

> **Naming note:** The URL path for these APIs accepts both `customformulas` and `formulacolumns` as equivalent path segments (an alias for backward compatibility). This document uses **`customformulas`** exclusively, which is the recommended path segment for all new integrations.

> **Tables and single views only:** Custom formula columns can be added to tables and most report/view types. They are **not supported on Pipeline Tables** — attempting to add or edit a formula column on a pipeline table returns error 7467.

---

## Index

| # | API Name | Method | URL |
|---|----------|--------|-----|
| 1 | [Get Custom Formulas](#1-get-custom-formulas) | GET | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/customformulas` |
| 2 | [Add Custom Formula](#2-add-custom-formula) | POST | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/customformulas` |
| 3 | [Edit Custom Formula](#3-edit-custom-formula) | PUT | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/customformulas/<formula-id>` |
| 4 | [Delete Custom Formula](#4-delete-custom-formula) | DELETE | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/customformulas/<formula-id>` |
| 5 | [Copy Custom Formulas](#5-copy-custom-formulas) | POST | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/formulas/copy` |

---

## 1. Get Custom Formulas

Returns the list of custom formula columns defined on the specified view.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/customformulas` |
| **OAuth Scope** | `ZohoAnalytics.metadata.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace, or any user with Create Formula permission on the view. |
| **Rate Limit** | 30 requests per user per minute (10-minute lockout on breach). |

> This API has no CONFIG parameter.

### Sample Requests

**Case 1 — Get all custom formulas on a view**

```http
GET /restapi/v2/workspaces/20868000000040672/views/20868000000040795/customformulas HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — White label portal user fetching custom formulas**

```http
GET /restapi/v2/workspaces/20868000000040672/views/20868000000040795/customformulas HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.cccccc.dddddd
ZANALYTICS-ORGID: 700000123456
```

### Sample Responses

**HTTP 200 OK — View with one formula column**

```json
{
  "status": "success",
  "summary": "Get formula columns",
  "data": {
    "customFormulas": [
      {
        "formulaId": "320862000000625897",
        "formulaName": "Length"
      }
    ]
  }
}
```

**HTTP 200 OK — View with no formula columns**

```json
{
  "status": "success",
  "summary": "Get formula columns",
  "data": {
    "customFormulas": []
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `customFormulas` | Array | List of custom formula columns defined on this view. Empty array if none exist. |
| `customFormulas[].formulaId` | String | Unique column ID of the formula column. Use this as `<formula-id>` for Edit Custom Formula and Delete Custom Formula. |
| `customFormulas[].formulaName` | String | Display name of the formula column, as shown in the Zoho Analytics UI. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Only formula-type columns are listed** | Regular (non-computed) columns of the view are not included in this response, even though they may be visible in Get Table Metadata. |
| **Response does not include the expression text** | The formula's underlying expression is not returned by this API. There is no dedicated "get formula details" endpoint in this API set — the expression must be tracked externally if you need to re-read it (Edit Custom Formula requires resending the full expression). |
| **Aggregate formulas are excluded** | This endpoint returns only per-row (custom) formula columns. Workspace-level aggregate/metric formulas are a distinct concept and are not listed here. |
| **Dependency** | `<view-id>` → Get View List. `formulaId` values feed directly into Edit Custom Formula and Delete Custom Formula. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7160 | The authenticated user is not permitted to view/manage formula columns on this view. | Ensure the user is a Workspace Admin or has Create Formula permission on the view. |
| 7301 | User does not have permission. | Ensure the user is a Workspace Admin or has Create Formula permission on the view. |
| 7319 | The view does not belong to the specified workspace. | Confirm `<view-id>` belongs to `<workspace-id>`. |

---

## 2. Add Custom Formula

Creates a new custom formula column on the specified view. The formula's value is computed for each row using the supplied expression.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/customformulas` |
| **OAuth Scope** | `ZohoAnalytics.modeling.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace, or any user with Create Formula permission on the view. |
| **Rate Limit** | 20 requests per user per minute (10-minute lockout on breach). |

### CONFIG Parameters

| Parameter | Type | Mandatory | Max Length | Description |
|-----------|------|-----------|------------|-------------|
| `formulaName` | String | **Yes** | 100 chars | Display name for the new formula column. Must be unique within the view. |
| `expression` | String | **Yes** | 50,000 chars | The formula expression, using Zoho Analytics formula syntax (e.g., `IF()`, `CONCATENATE()`, arithmetic operators, references to other column names in double quotes). |
| `description` | String | No | 250 chars | Description of the formula column. |

> **Formula expression syntax:** Column references within the expression must use the exact display name of the column, enclosed in double quotes, e.g. `"Unit Price" * "Quantity"`. Refer to the Zoho Analytics formula function reference for the full list of supported functions.

### Sample Requests

**Case 1 — Simple arithmetic formula**

```http
POST /restapi/v2/workspaces/20868000000040672/views/20868000000040795/customformulas HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"formulaName":"Total Amount","expression":"\"Unit Price\" * \"Quantity\""}
```

**Case 2 — Conditional (IF) formula with a description**

```http
POST /restapi/v2/workspaces/20868000000040672/views/20868000000040795/customformulas HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"formulaName":"Order Status","expression":"IF(\"Amount Paid\" >= \"Order Total\", \"Paid\", \"Pending\")","description":"Flags each order as Paid or Pending based on payment amount"}
```

**Case 3 — White label portal user adding a text concatenation formula**

```http
POST /restapi/v2/workspaces/20868000000040672/views/20868000000040795/customformulas HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.cccccc.dddddd
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"formulaName":"Full Name","expression":"CONCATENATE(\"First Name\",\" \",\"Last Name\")"}
```

### Sample Responses

**HTTP 200 OK**

```json
{
  "status": "success",
  "summary": "Custom formula has been added successfully.",
  "data": {
    "formulaId": "320862000000625897",
    "formulaName": "Total Amount"
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `formulaId` | String | Unique column ID assigned to the newly created formula column. Use this as `<formula-id>` for subsequent Edit or Delete calls. |
| `formulaName` | String | The display name of the formula column, echoing the `formulaName` value from the request. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Expression is validated and parsed at creation time** | Column references, function names, and syntax are checked before the formula column is created. Invalid expressions are rejected with a parse or validation error before any schema change occurs. |
| **`formulaName` must be unique** | Duplicate formula/column names within the same view are rejected. |
| **Column references use exact display names in double quotes** | If a referenced column name is misspelled or does not exist in the view, an "unknown column" error is returned. |
| **Not supported on Pipeline Tables** | Attempting to add a formula column to a Pipeline Table view returns error 7467. |
| **Data type of the formula column is inferred** | The resulting column's data type is derived automatically from the expression (e.g., an arithmetic expression on numeric columns yields a numeric formula column). It cannot be explicitly set. |
| **Dependency** | `<view-id>` → Get View List. Column names used in `expression` → Get Table Metadata (to confirm exact display names). After creation, the returned `formulaId` can be used with Get Column Dependents (see [COLUMNS_API_DOC_INFO.md](COLUMNS_API_DOC_INFO.md)) to trace where the formula is later used. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7112 | The formula expression could not be parsed (syntax error). | Review the expression for unbalanced parentheses, missing operators, or incorrect quoting of column names. |
| 7113 | The expression references an unknown/unsupported function. | Verify the function name against the Zoho Analytics formula function reference. |
| 7115 / 7116 | The expression references a column that does not exist in the view, or the formula is otherwise invalid. | Verify all column names referenced in the expression exist and are spelled exactly as shown in Get Table Metadata. |
| 7160 | Formula columns are not allowed for this user/view combination. | Ensure the user is a Workspace Admin or has Create Formula permission on the view. |
| 7180 / 7181 | The formula creates a circular dependency (it references a formula that, directly or indirectly, references this one). | Remove the circular reference from the expression. |
| 7301 | User does not have permission. | Ensure the user is a Workspace Admin or has Create Formula permission on the view. |
| 7319 | The view does not belong to the specified workspace. | Confirm `<view-id>` belongs to `<workspace-id>`. |
| 7467 | Formula columns are not supported on Pipeline Tables. | Formula columns can only be added to regular tables and standard views. |
| 8079 | A required attribute (`expression` or `formulaName`) is missing from CONFIG. | Ensure both `formulaName` and `expression` are provided. |

---

## 3. Edit Custom Formula

Updates the expression and/or description of an existing custom formula column.

| Attribute | Value |
|-----------|-------|
| **Method** | PUT |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/customformulas/<formula-id>` |
| **OAuth Scope** | `ZohoAnalytics.modeling.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace, or any user with Create Formula permission on the view. |
| **Rate Limit** | 20 requests per user per minute (10-minute lockout on breach). |

### CONFIG Parameters

| Parameter | Type | Mandatory | Max Length | Description |
|-----------|------|-----------|------------|-------------|
| `expression` | String | **Yes** | 50,000 chars | The new formula expression. Fully replaces the existing expression. |
| `description` | String | No | 250 chars | New description for the formula column. If omitted, the existing description is retained (see Notes below for the current behaviour). |

> **Important — no `formulaName` field:** Unlike Add Custom Formula, this API's CONFIG template does **not** accept a `formulaName` field. The formula column's display name **cannot be renamed** through this API — only the expression and description can be updated.

### Sample Requests

**Case 1 — Update the formula expression only**

```http
PUT /restapi/v2/workspaces/20868000000040672/views/20868000000040795/customformulas/320862000000625897 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"expression":"(\"Unit Price\" * \"Quantity\") - \"Discount\""}
```

**Case 2 — Update expression and description together**

```http
PUT /restapi/v2/workspaces/20868000000040672/views/20868000000040795/customformulas/320862000000625897 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"expression":"IF(\"Amount Paid\" >= \"Order Total\", \"Paid\", \"Partially Paid\")","description":"Updated logic to reflect partial payments"}
```

**Case 3 — White label portal user editing a formula**

```http
PUT /restapi/v2/workspaces/20868000000040672/views/20868000000040795/customformulas/320862000000625897 HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.cccccc.dddddd
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"expression":"CONCATENATE(\"First Name\",\" \",\"Middle Name\",\" \",\"Last Name\")"}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Edit Custom Formula returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |
| **Cannot rename via this API** | There is no `formulaName` field in this API's CONFIG. To rename a formula column, use a dedicated column-rename operation if available for the view type, or delete and recreate the formula with the desired name. |
| **`expression` is mandatory and fully replaces the old one** | There is no partial/incremental update — the entire expression must be resupplied even for a minor change. |
| **`description` omission behaviour** | If `description` is not supplied, the internal save logic reuses the column's current display name and does not clear existing metadata; however, always resend `description` explicitly if you want to guarantee its value, since behaviour for unset optional text fields has historically reset to empty in other similar rename/edit APIs in this API suite (see [WORKSPACE_GROUPS_API_DOC_INFO.md](WORKSPACE_GROUPS_API_DOC_INFO.md) and [WORKSPACE_FOLDERS_API_DOC_INFO.md](WORKSPACE_FOLDERS_API_DOC_INFO.md) for the equivalent `*Desc` reset pattern in other object types). |
| **Not supported on Pipeline Tables** | Editing a formula column on a Pipeline Table view returns error 7467. |
| **Changing the expression may change the data type** | If the new expression changes the result type (e.g., from numeric to text), any dependent reports/charts relying on the previous data type may behave unexpectedly or show a data type mismatch. |
| **Dependency** | `<formula-id>` → Get Custom Formulas. Column names used in `expression` → Get Table Metadata. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7112 | The new formula expression could not be parsed (syntax error). | Review the expression for correct syntax and quoting. |
| 7113 | The expression references an unknown/unsupported function. | Verify the function name against the Zoho Analytics formula function reference. |
| 7115 / 7116 | The expression references a column that does not exist, or the formula is otherwise invalid. | Verify all column names referenced in the expression. |
| 7160 | Formula columns are not allowed for this user/view combination. | Ensure the user is a Workspace Admin or has Create Formula permission on the view. |
| 7180 / 7181 | The updated formula creates a circular dependency. | Remove the circular reference from the expression. |
| 7301 | User does not have permission. | Ensure the user is a Workspace Admin or has Create Formula permission on the view. |
| 7319 | The view does not belong to the specified workspace. | Confirm `<view-id>` belongs to `<workspace-id>`. |
| 7427 | The specified `<formula-id>` is not a valid formula column on this view. | Verify the `<formula-id>` using Get Custom Formulas. |
| 7467 | Formula columns are not supported on Pipeline Tables. | This API only applies to standard tables/views. |
| 8079 | The required `expression` attribute is missing from CONFIG. | Ensure `expression` is provided in every Edit Custom Formula request. |

---

## 4. Delete Custom Formula

Permanently deletes a custom formula column from the specified view. By default, deletion is blocked if any dependent views (reports, charts, other formulas) reference this formula column.

| Attribute | Value |
|-----------|-------|
| **Method** | DELETE |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/customformulas/<formula-id>` |
| **OAuth Scope** | `ZohoAnalytics.modeling.delete` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace, or any user with Create Formula permission on the view. |
| **Rate Limit** | 30 requests per user per minute (10-minute lockout on breach). |

### CONFIG Parameters

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `deleteDependentViews` | Boolean | No | `false` | If `true`, all dependent views (reports, charts, pivot tables, other formula columns) that reference this formula are also permanently deleted. If `false`, deletion is blocked with error 7277 if any dependents exist. |

### Sample Requests

**Case 1 — Delete a formula column with no dependents**

```http
DELETE /restapi/v2/workspaces/20868000000040672/views/20868000000040795/customformulas/320862000000625897 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={}
```

**Case 2 — Delete a formula column and cascade-delete all dependent views**

```http
DELETE /restapi/v2/workspaces/20868000000040672/views/20868000000040795/customformulas/320862000000625897 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"deleteDependentViews":true}
```

**Case 3 — White label portal user deleting a formula column**

```http
DELETE /restapi/v2/workspaces/20868000000040672/views/20868000000040795/customformulas/320862000000625897 HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.cccccc.dddddd
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Delete Custom Formula returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |
| **Not idempotent** | If `<formula-id>` does not correspond to a formula column on the view (e.g., it's a regular column, or already deleted), error 7107 (column not present) or 7427-equivalent "not a formula column" behaviour is returned rather than a silent success. |
| **`deleteDependentViews: true` is permanent** | All dependent reports, charts, pivot tables, and other formula columns that reference this formula are permanently deleted. This cannot be undone. |
| **DDL lock check** | If the view is locked due to an in-progress schema change, the request is rejected until the lock clears. |
| **Not supported on Pipeline Tables** | Deleting a formula column from a Pipeline Table view returns error 7467. |
| **Dependency** | `<formula-id>` → Get Custom Formulas. Before deleting, consider checking dependent views/formulas via [Get Column Dependents](COLUMNS_API_DOC_INFO.md#6-get-column-dependents), since a formula column's ID can also be passed as a regular `<column-id>` to that API. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7107 | The specified column ID does not exist in the view. | Verify `<formula-id>` using Get Custom Formulas. |
| 7160 | Formula columns are not allowed for this user/view combination. | Ensure the user is a Workspace Admin or has Create Formula permission on the view. |
| 7277 | The formula column has dependent views; deletion blocked. | Use Get Column Dependents to identify dependents, then either delete them manually first or set `deleteDependentViews: true` to cascade delete. |
| 7301 | User does not have permission. | Ensure the user is a Workspace Admin or has Create Formula permission on the view. |
| 7319 | The view does not belong to the specified workspace. | Confirm `<view-id>` belongs to `<workspace-id>`. |
| 7427 | The specified column is not a custom formula column. | Verify `<formula-id>` refers to a formula column, not a regular column, using Get Custom Formulas. |
| 7467 | Formula columns are not supported on Pipeline Tables. | This API only applies to standard tables/views. |

---

## 5. Copy Custom Formulas

Copies one or more custom formula columns (by name) from a view in the source workspace to the equivalent view in a destination workspace. This is typically used to replicate formula logic across workspaces owned by the same organisation (or across organisations the caller administers).

> **Cross-organisation copy header:** Similar to Copy Workspace, when an Org Admin copies formulas into a workspace belonging to a *different* organisation than the one resolved from the OAuth token, the destination organisation must be specified using the `ZANALYTICS-DEST-ORGID` header. See [Appendix A](#appendix-a--common-http-headers) for details.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/formulas/copy` |
| **OAuth Scope** | `ZohoAnalytics.modeling.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the source workspace. |
| **ZANALYTICS-DEST-ORGID Header** | Conditionally required — set this when the destination workspace belongs to a different organisation than the one identified by `ZANALYTICS-ORGID` (Org Admin cross-org scenario). |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin of the destination organisation. This API is **not** available to Workspace Admins or any custom-permission user — only Account Admin / Org Admin roles are authorized. |
| **Custom Domain** | **Not available** via White Label / Client Portal. |

### CONFIG Parameters

| Parameter | Type | Mandatory | Description |
|-----------|------|-----------|-------------|
| `formulaColumnNames` | JSONArray of String | **Yes** | Array of formula column **display names** (not IDs) from the source view to copy. Max 1000 entries. |
| `destWorkspaceId` | Long | **Yes** | ID of the destination workspace where the formulas will be copied to. Must contain a view with the same structure/columns as the source view. |
| `workspaceKey` | String | Conditionally required | The destination workspace's secret key (see [Get Workspace SecretKey](WORKSPACE_OPERATIONS_API_DOC_INFO.md)). Required when the destination workspace belongs to a different organisation than the source. Not required for same-organisation copies. |

### Sample Requests

**Case 1 — Copy a single formula within the same organisation**

```http
POST /restapi/v2/workspaces/20868000000040672/views/20868000000040795/formulas/copy HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"formulaColumnNames":["Total Amount"],"destWorkspaceId":20868000000045000}
```

**Case 2 — Copy multiple formulas across organisations (Org Admin, cross-org)**

```http
POST /restapi/v2/workspaces/20868000000040672/views/20868000000040795/formulas/copy HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
ZANALYTICS-DEST-ORGID: 700000987654
Content-Type: application/x-www-form-urlencoded

CONFIG={"formulaColumnNames":["Total Amount","Order Status"],"destWorkspaceId":20868000000099000,"workspaceKey":"a1b2c3d4e5f6g7h8"}
```

**Case 3 — Account Admin copying formulas to a workspace in a different org (destination org resolved via ZANALYTICS-ORGID)**

```http
POST /restapi/v2/workspaces/20868000000040672/views/20868000000040795/formulas/copy HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000987654
Content-Type: application/x-www-form-urlencoded

CONFIG={"formulaColumnNames":["Full Name"],"destWorkspaceId":20868000000099000,"workspaceKey":"a1b2c3d4e5f6g7h8"}
```

### Sample Responses

**HTTP 204 No Content**

This API returns no response body on success — only an HTTP 204 status code is returned to external API callers.

### Response Fields

No response body is returned for this API. Success is indicated solely by the HTTP 204 status code. To verify the copy succeeded, call Get Custom Formulas on the destination view and confirm the formula names now appear there.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Formulas are matched by name, not ID** | `formulaColumnNames` takes the display names of the source formulas (as seen in Get Custom Formulas), not their `formulaId` values. |
| **Destination view is resolved automatically** | The API does not take a destination view ID — the destination view is matched internally based on the table/view structure in `destWorkspaceId`. Ensure the destination workspace has an equivalent view with matching source columns before copying. |
| **Only Account Admin / Org Admin can call this API** | Unlike most modeling APIs (which accept Workspace Admin), this API is restricted to organisation-level administrators, reflecting its cross-workspace/cross-org nature. |
| **`workspaceKey` required only for cross-organisation copies** | If the destination workspace belongs to the same organisation as the source (as resolved from `ZANALYTICS-ORGID`/`ZANALYTICS-DEST-ORGID`), `workspaceKey` can be omitted. For a different organisation, the destination workspace's secret key must be supplied, or the request fails with error 15007. |
| **No response payload — verify via Get Custom Formulas** | Since this API returns HTTP 204 with no body, always follow up with Get Custom Formulas on the destination view to confirm which formulas were successfully copied. |
| **Not available via White Label/Client Portal** | This API is disabled for custom-domain contexts, matching Copy Workspace and other organisation-level administrative APIs. |
| **Dependency** | `formulaColumnNames` → Get Custom Formulas (on the source view). `destWorkspaceId` → Get Workspace List. `workspaceKey` → Get Workspace SecretKey (destination workspace). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7301 | User does not have permission. | Ensure the user is an Account Admin or Organization Admin of the destination organisation. |
| 7319 | The source view does not belong to the specified workspace. | Confirm `<view-id>` belongs to the workspace identified by `<workspace-id>`. |
| 8058 | The organisation ID specified in `ZANALYTICS-DEST-ORGID` does not exist. | Verify the destination organisation ID. |
| 15007 | The copy operation is not allowed — the destination workspace's organisation does not match the caller's organisation, and no valid `workspaceKey` was supplied (or it does not match). | Supply the correct `workspaceKey` for the destination workspace (see Get Workspace SecretKey), or perform the copy within the same organisation. |

---

## Appendix A – Common HTTP Headers

| Header | Value | Required | Notes |
|--------|-------|----------|-------|
| `Authorization` | `Zoho-oauthtoken <oauth-token>` | **Mandatory** | OAuth 2.0 access token of the calling user. |
| `ZANALYTICS-ORGID` | Organisation ID | **Mandatory** for all APIs | For Copy Custom Formulas, this identifies the **source** workspace's organisation (or, for Account Admins doing a cross-org copy, the destination organisation — see below). |
| `ZANALYTICS-DEST-ORGID` | Destination Organisation ID | Conditionally required (Copy Custom Formulas only) | Used when an **Organization Admin** with access to multiple organisations copies formulas into a workspace belonging to a different organisation than the one set in `ZANALYTICS-ORGID`. Not needed for Account Admins, who instead set `ZANALYTICS-ORGID` directly to the destination organisation. |
| `Content-Type` | `application/x-www-form-urlencoded` | Required for POST/PUT with body | Not required for GET requests without CONFIG. |

> **White Label / Client Portal:** Get Custom Formulas, Add Custom Formula, Edit Custom Formula, and Delete Custom Formula are all available via portal domain URLs when the caller has the required permission. **Copy Custom Formulas is NOT available** via portal domain URLs — it is an organisation-administration API restricted to the standard `analyticsapi.zoho.com` host.

---

## Appendix B – OAuth Scope Summary

| API | Method | Scope |
|-----|--------|-------|
| Get Custom Formulas | GET | `ZohoAnalytics.metadata.read` |
| Add Custom Formula | POST | `ZohoAnalytics.modeling.create` |
| Edit Custom Formula | PUT | `ZohoAnalytics.modeling.update` |
| Delete Custom Formula | DELETE | `ZohoAnalytics.modeling.delete` |
| Copy Custom Formulas | POST | `ZohoAnalytics.modeling.create` |

---

## Appendix C – API-Specific Notes and Behaviours

### Get Custom Formulas

- **Entry point for the other three same-view APIs.** The `formulaId` values returned here are required for Edit and Delete.
- **Does not expose the expression.** If you need to review or diff a formula's logic before editing, you must maintain your own record of the expression text externally — this API only returns `formulaId` and `formulaName`.
- **Dependency chain:** Get View List → Get Custom Formulas → Edit/Delete Custom Formula.

### Add Custom Formula

- **Column references must exactly match display names.** Use Get Table Metadata beforehand to confirm the exact spelling/casing of columns referenced in the `expression`.
- **Data type is inferred, not declared.** There is no `dataType` parameter — the formula's result type is determined by the expression itself.
- **Dependency chain:** Get View List → Get Table Metadata (verify column names) → Add Custom Formula → response `formulaId`.

### Edit Custom Formula

- **Cannot rename the formula.** The `formulaName` field is not accepted by this API, unlike Create Formula. This is a deliberate asymmetry between the two APIs — plan integrations accordingly (a rename requires delete + recreate).
- **Full expression replacement only.** There is no way to patch a sub-part of the expression; always resend the complete formula text.
- **Dependency chain:** Get Custom Formulas (`formulaId`) → Edit Custom Formula.

### Delete Custom Formula

- **Not idempotent.** Deleting a non-existent or already-deleted formula ID returns an error, not a silent success.
- **Use `deleteDependentViews` cautiously.** As with [Delete Column](COLUMNS_API_DOC_INFO.md#3-delete-column), cascading deletes of dependent reports/charts/formulas are irreversible.
- **Dependency chain:** Get Custom Formulas (`formulaId`) → (optional) Get Column Dependents → Delete Custom Formula.

### Copy Custom Formulas

- **Restricted to Account Admin / Org Admin only** — the only API in this document (and one of the few in the whole API suite) that excludes Workspace Admins entirely.
- **Matches formulas by name across workspaces.** This implies the destination view must already have a compatible schema (same base columns the formula's expression references) for the copy to succeed.
- **Cross-org copy requires `ZANALYTICS-DEST-ORGID` + `workspaceKey` (Org Admin) or `ZANALYTICS-ORGID` set to the destination org + `workspaceKey` (Account Admin)** — identical pattern to Copy Workspace. See [WORKSPACE_OPERATIONS_API_DOC_INFO.md](WORKSPACE_OPERATIONS_API_DOC_INFO.md) for the full explanation of this cross-org header mechanism.
- **No response body.** Always verify success via Get Custom Formulas on the destination view.
- **Dependency chain:** Get Custom Formulas (source view, to get exact `formulaName` values) → Get Workspace SecretKey (destination workspace, if cross-org) → Copy Custom Formulas → Get Custom Formulas (destination view, to verify).

---

## Appendix D – General Response Payload Notes

| Field / Behaviour | Detail |
|-------------------|--------|
| **`formulaId` vs `columnId`** | A formula column's `formulaId` (as returned by these APIs) is the same underlying value as its `columnId` in Get Table Metadata and Get Column Dependents. Formula columns are a special case of table/view columns. |
| **Empty response bodies are common in this API set** | Edit Custom Formula, Delete Custom Formula, and Copy Custom Formulas all return no JSON payload on success — only an HTTP `204 No Content` status. Always design integrations to treat the HTTP status code as the success indicator rather than parsing a response body. |
| **`customFormulas` naming convention** | Despite the underlying URL path supporting both `customformulas` and `formulacolumns`, the JSON response key is always `customFormulas` (camelCase) when the `customformulas` path is used — use this document's path consistently to avoid ambiguity. |
| **Formula expressions are workspace-local** | An expression valid in one view cannot be blindly reused in another unless the referenced column names exist there too — this is precisely what Copy Custom Formulas automates, provided the destination view has matching columns. |
