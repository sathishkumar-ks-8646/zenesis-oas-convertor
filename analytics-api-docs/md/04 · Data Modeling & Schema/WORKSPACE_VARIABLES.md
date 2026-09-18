# Zoho Analytics V2 REST API — Workspace Variables

This document covers the APIs for creating, editing, deleting, and retrieving **workspace variables** — reusable placeholders (e.g., `${Region}`, `${Target Sales}`) that can be embedded in formula expressions, SQL queries, filters, and reports. Variables allow the same report/formula definition to resolve to different values per user (or per Client Portal domain), without duplicating the underlying view.

## What is a Workspace Variable?

A variable is defined once at the workspace level with a name, a data type, and a **type** that determines how its value is resolved:

- **List** — the variable resolves to one value picked from a fixed list of allowed values, with a default value.
- **Range** — the variable resolves to a numeric value within a min/max bound, incremented by a step size, with a default value.
- **All Values** — a special type with no explicit values; it always represents "every possible value" (used chiefly as a placeholder default with no per-user override).

Each variable can additionally carry **per-user (or per-portal-domain) overrides** — different sets of allowed values, ranges, and defaults for specific email addresses — falling back to a workspace-wide `defaultData` definition for any user not explicitly listed.

---

## Index

| # | API Name | Method | URL |
|---|----------|--------|-----|
| 1 | [Create Variable](#1-create-variable) | POST | `/restapi/v2/workspaces/<workspace-id>/variables` |
| 2 | [Edit Variable](#2-edit-variable) | PUT | `/restapi/v2/workspaces/<workspace-id>/variables/<variable-id>` |
| 3 | [Delete Variable](#3-delete-variable) | DELETE | `/restapi/v2/workspaces/<workspace-id>/variables/<variable-id>` |
| 4 | [Get Variables](#4-get-variables) | GET | `/restapi/v2/workspaces/<workspace-id>/variables` |
| 5 | [Get Variable Details](#5-get-variable-details) | GET | `/restapi/v2/workspaces/<workspace-id>/variables/<variable-id>` |

> **Note on naming:** The two read APIs are documented here as **"Get Variables"** and **"Get Variable Details"** respectively (renamed from "Get Variable List" and "Get Variable Details" for consistency with this API's summary text and the rest of this documentation suite).

---

## 1. Create Variable

Creates a new workspace variable.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/variables` |
| **OAuth Scope** | `ZohoAnalytics.modeling.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin of the specified workspace. |

### CONFIG Parameters

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `variableName` | String | **Yes** | — | Display name of the variable. Must be unique within the workspace (case-insensitive). Cannot start with `system.` or `${`, and cannot end with `}` (these are reserved patterns used internally for system variables). |
| `variableDataType` | Long (enum) | **Yes** | — | The data type that variable values must conform to. See [Variable Data Type Values](#variable-data-type-values) below. |
| `variableType` | Long (enum) | **Yes** | — | Determines how the variable resolves a value: List, Range, or All Values. See [Variable Type Values](#variable-type-values) below. |
| `defaultData` | JSONObject | Conditionally required | — | Workspace-wide fallback values/default used for any user not explicitly listed in `userSpecificData`. **Required for `variableType` = List (`0`) or Range (`1`)**. Not applicable (and ignored) for `variableType` = All Values (`3`). See [defaultData / userSpecificData Fields](#defaultdata--userspecificdata-fields) below. |
| `userSpecificData` | JSONArray | No | `[]` | Array of per-user (or per-portal-domain) override entries. Each entry maps one or more `emailIds` to their own set of values/range/default. See [defaultData / userSpecificData Fields](#defaultdata--userspecificdata-fields) below. |
| `format` | JSONObject | No | `{}` | Display formatting for the variable's value (alignment, decimal places, currency symbol, date format, etc.). See [format Fields](#format-fields) below. |

#### Variable Type Values

| `variableType` | Meaning | Requires `defaultData`? | Requires `userSpecificData` fallback entry? |
|--------------------|---------|--------------------------|-----------------------------------------------|
| `0` | **List** — value chosen from a fixed set of allowed `values`, with one `defaultValue`. | Yes | Optional |
| `1` | **Range** — value chosen from a numeric range (`minValue`/`maxValue`/`stepSize`), with one `defaultValue`. | Yes | Optional |
| `3` | **All Values** — represents every possible value; no explicit list/range/default is defined. | No (ignored if supplied) | Not applicable |

> `variableType = 2` ("Any Value") is a reserved/legacy internal type and is **not accepted** through this API (error 70350 `VARIABLE_INVALID_VARTYPE`).

#### Variable Data Type Values

| `variableDataType` | Meaning | Range (`variableType=1`) Allowed? |
|--------------------------|---------|---------------------------------------|
| `1` | Text (Plain) | **No** — Range is not supported for Text (error 70335 `VARIABLE_RANGE_NOT_ALLOWED_ON_DT`). |
| `4` | Number | Yes |
| `5` | Positive Number | Yes |
| `6` | Decimal Number | Yes |
| `7` | Currency | Yes |
| `8` | Percentage | Yes |

> Any other `variableDataType` value (e.g., Date, Boolean) returns error 70351 `VARIABLE_INVALID_DATATYPE` — variables only support the six data types listed above.

#### `defaultData` / `userSpecificData` Fields

Both `defaultData` (a single JSONObject) and each entry of `userSpecificData` (a JSONArray of JSONObjects) share the same field structure, which varies by `variableType`:

**When `variableType` = List (`0`):**

| Field | Type | Mandatory | Description |
|-------|------|-----------|--------------|
| `values` | JSONArray of String | **Yes** | The list of allowed values for this entry. |
| `defaultValue` | String | **Yes** in `defaultData`; optional in `userSpecificData` entries | The value used when the variable is resolved without further user input. Must be one of the values in `values` (error 70337 `VARIABLE_DEFAULT_VALUE_NOT_PRESENT_IN_LIST` if not). |

**When `variableType` = Range (`1`):**

| Field | Type | Mandatory | Description |
|-------|------|-----------|--------------|
| `minValue` | String (numeric) | **Yes** | Lower bound of the range. |
| `maxValue` | String (numeric) | **Yes** | Upper bound of the range. Must be greater than `minValue` (error 70352 `VARIABLE_RANGE_MIN_LESS_THAN_MAX`). |
| `stepSize` | String (numeric) | **Yes** | Increment step between selectable values. Must be non-zero (error 70354) and must evenly divide the range span (error 70355 `VARIABLE_RANGE_INCR_DIV_EQUALLY_ERR`), and must not exceed the range span itself (error 70353 `VARIABLE_RANGE_INCR_LESSTHAN_RANGESIZE`). |
| `defaultValue` | String (numeric) | **Yes** in `defaultData`; optional in `userSpecificData` entries | Must fall within `[minValue, maxValue]` (error 70356 `VARIABLE_RANGE_DEF_BW_MINMAX_RANGE`). |

**Additional field on `userSpecificData` entries only (not on `defaultData`):**

| Field | Type | Mandatory | Description |
|-------|------|-----------|--------------|
| `emailIds` | JSONArray of String | **Yes** | Email addresses of the users this entry's values/range/default apply to. Each email address may appear in only one `userSpecificData` entry per variable (error 70341 `VARIABLE_DUPLICATE_MAIL_ID_OR_GROUP` on duplicates). Cannot be empty (error 70348 `VARIABLE_EMAIL_NOT_PRESENT`). |
| `domainName` | String | No | Only relevant for White Label/Client Portal workspaces with multiple custom domains. Associates this override entry with a specific portal domain's user base rather than the workspace's default domain. Omit for standard (non-portal) workspaces. |

> **`defaultData` is internally the "everyone else" bucket.** Any user whose email is not present in any `userSpecificData` entry resolves the variable using `defaultData`. There is no separate mechanism to mark a `userSpecificData` entry as the fallback — that role belongs exclusively to the top-level `defaultData` object.

#### `format` Fields

| Field | Type | Applies To | Description |
|-------|------|------------|--------------|
| `alignment` | String | All types | Display alignment, e.g. `"Left"`, `"Right"`. |
| `decimalPlaces` | Integer | Number, Positive Number, Decimal Number, Currency, Percentage | Number of decimal places to display. `-1` means "auto" (no fixed precision). |
| `userLocale` | Boolean | Numeric types | If `true`, formats the number according to the viewing user's locale settings rather than a fixed format. |
| `thousandSeparator` | Integer (enum) | Numeric types | Thousands grouping symbol selector (workspace-locale-dependent numeric code; `0` = none/default). |
| `decimalSeparator` | Integer (enum) | Numeric types | Decimal point symbol selector (workspace-locale-dependent numeric code; `0` = default `.`). |
| `units` | String | Numeric types | Custom unit label appended to the value, e.g. `"kg"`. `"None"` if not set. |
| `currencySymbol` | String | Currency (`7`) only | Locale-formatted currency symbol string, e.g. `"en;US;"`. |
| `showNegativeSign` | Boolean | Currency (`7`) only | Whether negative currency values are shown with a minus sign or parentheses-style formatting. |
| `showPercent` | Boolean | Percentage (`8`) only | Whether the `%` symbol is appended to displayed values. |
| `dateFormat` | String | Not applicable to variables (no Date data type supported) | Reserved field inherited from the shared format template; has no effect for variables. |
| `numberingType` | Integer | Numeric types | Numbering system selector (e.g., standard vs. Indian numbering system). |

### Sample Requests

**Case 1 — List-type Text variable with a per-user override**

```http
POST /restapi/v2/workspaces/137687000271334001/variables HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"variableName":"Region","variableDataType":1,"variableType":0,"defaultData":{"values":["North","South","East","West"],"defaultValue":"North"},"userSpecificData":[{"values":["East","West"],"defaultValue":"East","emailIds":["sales.east@zylker.com"]}],"format":{"alignment":"Left"}}
```

**Case 2 — Range-type Currency variable ("Target Sales")**

```http
POST /restapi/v2/workspaces/137687000271334001/variables HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"variableName":"Target Sales","variableDataType":7,"variableType":1,"defaultData":{"minValue":"10000","maxValue":"100000","stepSize":"5000","defaultValue":"50000"},"format":{"alignment":"Right","currencySymbol":"en;US;","showNegativeSign":true,"decimalPlaces":2}}
```

**Case 3 — All Values-type variable (no default data needed)**

```http
POST /restapi/v2/workspaces/137687000271334001/variables HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"variableName":"All Regions","variableDataType":1,"variableType":3}
```

### Sample Responses

**HTTP 200 OK**

```json
{
  "status": "success",
  "summary": "Create variable",
  "data": {
    "variableId": "137687000006991651"
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `variableId` | String | Unique ID assigned to the newly created variable. Use as `<variable-id>` for Edit/Delete Variable and Get Variable Details. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **`defaultData` is mandatory except for All Values** | Submitting `variableType` 0 (List) or 1 (Range) without `defaultData` returns error 70343 `VARIABLE_NO_VARIABLE_DATA_PRESENT`. |
| **`variableName` uniqueness is case-insensitive** | `"Region"` and `"region"` are treated as the same name and the second create attempt is rejected (error 70323 `DUPLICATE_VARIABLE`). |
| **Reserved name patterns are rejected** | Names starting with `system.` or `${`, or ending with `}`, collide with internal system-variable syntax (e.g., `${Region}`) and are rejected with error 70325 `INVALID_VAR_NAME`. |
| **Range is incompatible with Text** | `variableType: 1` (Range) combined with `variableDataType: 1` (Text) is always rejected — ranges require a numeric data type. |
| **Each email may only appear once across all `userSpecificData` entries** | A given user cannot have two conflicting overrides on the same variable. |
| **White Label domain scoping via `domainName`** | In multi-domain Client Portal setups, omitting `domainName` on a `userSpecificData` entry applies it to the calling/default domain; explicitly setting it scopes the entry to a specific branded portal domain's users. |
| **Dependency** | `<workspace-id>` → Get Workspace List. Once created, `variableId` is referenced by name (as `${variableName}`) inside formula expressions, SQL queries, and report filters — it is not directly embedded by ID in other API payloads. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 70323 | `DUPLICATE_USER_VARIABLE` — A variable with this name already exists in the workspace. | Choose a different `variableName`, or edit the existing variable instead. |
| 70324 | `BLANK_VARIABLE_NAME` — `variableName` is empty. | Provide a non-empty variable name. |
| 70325 | `INVALID_VAR_NAME` — The name uses a reserved pattern (`system.` prefix, `${` prefix, or `}` suffix). | Choose a name that doesn't collide with system-variable syntax. |
| 70335 | `VARIABLE_RANGE_NOT_ALLOWED_ON_DT` — Range type combined with Text data type. | Use a numeric `variableDataType` (4, 5, 6, 7, or 8) when `variableType` is Range. |
| 70336 | `VARIABLE_DATA_NOT_PRESENT` — No usable value entries could be derived from the request. | Ensure `defaultData` (and any `userSpecificData` entries) contain the required fields for the chosen `variableType`. |
| 70337 | `VARIABLE_DEFAULT_VALUE_NOT_PRESENT_IN_LIST` — The `defaultValue` is not one of the `values` supplied for a List-type entry. | Ensure `defaultValue` matches one of the entries in `values`. |
| 70338 / 70339 | `VARIABLE_RANGE_INSUFFICIENT_DATA` / `VARIABLE_RANGE_EXCESS_DATA` — Range entry is missing a required field or has extra unexpected data. | Ensure exactly `minValue`, `maxValue`, and `stepSize` are provided for Range entries. |
| 70340 / 70356 | `VARIABLE_RANGE_DEFAULT_VALUE_OUT_OF_RANGE` / `VARIABLE_RANGE_DEF_BW_MINMAX_RANGE` — The `defaultValue` falls outside `[minValue, maxValue]`. | Ensure `defaultValue` lies within the specified range. |
| 70341 | `VARIABLE_DUPLICATE_MAIL_ID_OR_GROUP` — The same email address appears in more than one `userSpecificData` entry. | Ensure each email address is listed in only one override entry. |
| 70342 | `VARIABLE_ALL_VALUES_NO_VARIABLE_DATA` — `userSpecificData`/`defaultData` were supplied for an All Values-type variable. | Omit `defaultData` and `userSpecificData` entirely when `variableType` is `3`. |
| 70343 | `VARIABLE_NO_VARIABLE_DATA_PRESENT` — `defaultData` is missing for a List or Range-type variable. | Supply `defaultData` with the fields required for the chosen `variableType`. |
| 70348 | `VARIABLE_EMAIL_NOT_PRESENT` — A `userSpecificData` entry has an empty `emailIds` array. | Ensure every `userSpecificData` entry lists at least one email address. |
| 70350 | `VARIABLE_INVALID_VARTYPE` — `variableType` is not one of `0`, `1`, or `3`. | Use only List (`0`), Range (`1`), or All Values (`3`). |
| 70351 | `VARIABLE_INVALID_DATATYPE` — `variableDataType` is not one of the six supported values. | Use only `1`, `4`, `5`, `6`, `7`, or `8`. |
| 70352 | `VARIABLE_RANGE_MIN_LESS_THAN_MAX` — `minValue` is not less than `maxValue`. | Ensure `minValue` < `maxValue`. |
| 70353 | `VARIABLE_RANGE_INCR_LESSTHAN_RANGESIZE` — `stepSize` is larger than the range span. | Reduce `stepSize` so it fits within `maxValue - minValue`. |
| 70354 | `VARIABLE_RANGE_INCR_ZERO_ERR` — `stepSize` is zero. | Provide a non-zero `stepSize`. |
| 70355 | `VARIABLE_RANGE_INCR_DIV_EQUALLY_ERR` — `stepSize` does not evenly divide the range span. | Choose a `stepSize` that evenly divides `maxValue - minValue`. |
| 7301 | User does not have permission. | Ensure the user is an Account Admin, Organization Admin, or Workspace Admin. |

---

## 2. Edit Variable

Updates an existing workspace variable. This API takes the **same CONFIG attributes** as Create Variable and requires the **full variable definition to be resent** — there is no partial/incremental update.

| Attribute | Value |
|-----------|-------|
| **Method** | PUT |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/variables/<variable-id>` |
| **OAuth Scope** | `ZohoAnalytics.modeling.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin of the specified workspace. |

### CONFIG Parameters

Identical structure to [Create Variable](#1-create-variable) — `variableName`, `variableDataType`, `variableType`, `defaultData`, `userSpecificData`, `format` — all resent in full. `variableName` is mandatory even when unchanged, since this API also supports **renaming** the variable.

### Sample Requests

**Case 1 — Rename the variable (all other fields resent unchanged)**

```http
PUT /restapi/v2/workspaces/137687000271334001/variables/137687000006991651 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"variableName":"Sales Region","variableDataType":1,"variableType":0,"defaultData":{"values":["North","South","East","West"],"defaultValue":"North"}}
```

**Case 2 — Update the default value and add a new per-user override**

```http
PUT /restapi/v2/workspaces/137687000271334001/variables/137687000006991651 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"variableName":"Region","variableDataType":1,"variableType":0,"defaultData":{"values":["North","South","East","West"],"defaultValue":"South"},"userSpecificData":[{"values":["East","West"],"defaultValue":"West","emailIds":["sales.east@zylker.com","sales.west@zylker.com"]}]}
```

**Case 3 — Change the format only (values/default resent unchanged)**

```http
PUT /restapi/v2/workspaces/137687000271334001/variables/137687000006991663 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"variableName":"Target Sales","variableDataType":7,"variableType":1,"defaultData":{"minValue":"10000","maxValue":"100000","stepSize":"5000","defaultValue":"50000"},"format":{"alignment":"Right","currencySymbol":"en;GB;","decimalPlaces":0}}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Edit Variable returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |
| **Full resend required, not a partial patch** | Since the CONFIG template is identical to Create Variable, all fields relevant to the variable's current `variableType`/`variableDataType` must be resent — omitting `defaultData`, for example, is treated the same as removing it, not "leave unchanged." |
| **Renaming is supported** | Changing `variableName` in the request renames the variable while preserving its `variableId` and all references to it elsewhere (formulas, filters resolve the name change automatically). |
| **`variableName` uniqueness check excludes itself** | The duplicate-name check compares against all other variables in the workspace, so resending the same current name (unchanged) does not trigger error 70323. |
| **Changing `variableType`/`variableDataType` can be blocked by existing references** | If the variable is used in formulas or reports in a way that is incompatible with the new type/data type, the edit is rejected with error 70358 `VARIABLE_CANNOT_BE_UPDATED` rather than silently breaking those dependents. |
| **Dependency** | `<variable-id>` → Get Variables or Get Variable Details. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 70323 | `DUPLICATE_USER_VARIABLE` — The new `variableName` collides with a different existing variable. | Choose a name not already used by another variable in the workspace. |
| 70324 | `BLANK_VARIABLE_NAME` — `variableName` is empty. | Provide a non-empty variable name. |
| 70325 | `INVALID_VAR_NAME` — The name uses a reserved pattern. | Choose a name that doesn't collide with system-variable syntax. |
| 70329 | `CANT_DELETE_VARIABLE` (`UNAUTHORIZED_VAR_ACTION`) — `<variable-id>` does not exist in this workspace. | Verify `<variable-id>` using Get Variables. |
| 70335 | `VARIABLE_RANGE_NOT_ALLOWED_ON_DT` — Range type combined with Text data type. | Use a numeric `variableDataType` when `variableType` is Range. |
| 70336–70356 | Same value/range/list validation errors as Create Variable (see [Create Variable Error Codes](#error-codes)). | Review the relevant field per the error description. |
| 70358 | `VARIABLE_CANNOT_BE_UPDATED` — The requested type/data type change conflicts with existing formula/report references to this variable. | Remove or update the dependent formulas/reports first, or keep the existing `variableType`/`variableDataType`. |
| 7301 | User does not have permission. | Ensure the user is an Account Admin, Organization Admin, or Workspace Admin. |

---

## 3. Delete Variable

Permanently deletes a workspace variable.

| Attribute | Value |
|-----------|-------|
| **Method** | DELETE |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/variables/<variable-id>` |
| **OAuth Scope** | `ZohoAnalytics.modeling.delete` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin of the specified workspace. |

> This API has no CONFIG parameter.

### Sample Requests

**Case 1 — Delete an unused variable**

```http
DELETE /restapi/v2/workspaces/137687000271334001/variables/137687000006991651 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Attempt to delete a variable still referenced by a formula (fails)**

```http
DELETE /restapi/v2/workspaces/137687000271334001/variables/137687000006991655 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Delete Variable returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |
| **Not idempotent** | Deleting a `<variable-id>` that does not exist (or was already deleted) returns an error, not a silent success. |
| **Blocked if referenced elsewhere** | If the variable is used in any formula, report filter, or SQL query in the workspace, deletion is blocked to avoid breaking those dependents. |
| **No cascade-delete option** | Unlike Delete Column/Delete Aggregate Formula, this API has no `deleteDependentViews`-style flag — dependent references must be manually removed before the variable can be deleted. |
| **Dependency** | `<variable-id>` → Get Variables or Get Variable Details. There is no dedicated "Get Variable Dependents" API in this suite — use Get Table Metadata / formula expressions review to locate references before deleting. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 70321 | `USERVARIABLE_VARIABLE_IN_USE` — The variable is currently referenced elsewhere and cannot be deleted. | Remove all references to this variable (in formulas, filters, SQL queries) before deleting. |
| 70322 | `USERVARIABLE_VARIABLE_IN_USE` (multi-variable form) — One or more of the requested variables are in use. | Same as above; applies when multiple variables are targeted in a single internal delete operation. |
| 70326 | `CANT_DELETE_VARIABLE` — The variable cannot be deleted by this user (ownership restriction). | Ensure the user is an Account Admin, Organization Admin, or Workspace Admin. |
| 70329 | `CANT_DELETE_VARIABLE` (`UNAUTHORIZED_VAR_ACTION`) — `<variable-id>` does not exist in this workspace. | Verify `<variable-id>` using Get Variables. |
| 70357 | `USERVARIABLE_VARIABLE_CANNOT_BE_DELETED` — Deletion blocked due to unresolved references. | Identify and remove dependent formulas/reports, then retry. |
| 7301 | User does not have permission. | Ensure the user is an Account Admin, Organization Admin, or Workspace Admin. |

---

## 4. Get Variables

Returns a summary list of all variables defined in the workspace.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/variables` |
| **OAuth Scope** | `ZohoAnalytics.modeling.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin of the specified workspace. |

> This API has no CONFIG parameter.

### Sample Requests

**Case 1 — Get all variables in the workspace**

```http
GET /restapi/v2/workspaces/137687000271334001/variables HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — White label portal admin fetching the variable list**

```http
GET /restapi/v2/workspaces/137687000271334001/variables HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.cccccc.dddddd
ZANALYTICS-ORGID: 700000123456
```

### Sample Responses

**HTTP 200 OK — Multiple variables of different types**

```json
{
  "status": "success",
  "summary": "Get variables",
  "data": {
    "variables": [
      {
        "variableName": "Region",
        "variableId": "137687000007146340",
        "variableType": "0",
        "variableDataType": "1"
      },
      {
        "variableName": "All Regions",
        "variableId": "137687000007146338",
        "variableType": "3",
        "variableDataType": "1"
      },
      {
        "variableName": "Target Sales",
        "variableId": "137687000007146342",
        "variableType": "1",
        "variableDataType": "4"
      },
      {
        "variableName": "Discount Percent",
        "variableId": "137687000007146352",
        "variableType": "0",
        "variableDataType": "8"
      }
    ]
  }
}
```

**HTTP 200 OK — Workspace with no variables**

```json
{
  "status": "success",
  "summary": "Get variables",
  "data": {
    "variables": []
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `variables` | Array | List of variables defined in the workspace. Empty array if none exist. |
| `variables[].variableName` | String | Display name of the variable. |
| `variables[].variableId` | String | Unique ID of the variable. Use as `<variable-id>` for Edit/Delete Variable and Get Variable Details. |
| `variables[].variableType` | String (numeric enum) | `"0"` = List, `"1"` = Range, `"3"` = All Values. **Returned as a string here**, unlike Get Variable Details where it is returned as a native integer — account for this type difference when parsing. |
| `variables[].variableDataType` | String (numeric enum) | `"1"` = Text, `"4"` = Number, `"5"` = Positive Number, `"6"` = Decimal Number, `"7"` = Currency, `"8"` = Percentage. Also returned as a string here. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Summary only — no values** | This API does not return `defaultData`, `userSpecificData`, or `format` — use Get Variable Details for the full definition of a specific variable. |
| **`variableType`/`variableDataType` are strings here, integers in Get Variable Details** | Be careful when comparing or switching on these fields across the two "read" APIs in this suite — the JSON type differs. |
| **Dependency** | `<workspace-id>` → Get Workspace List. `variableId` values feed into Edit/Delete Variable and Get Variable Details. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7301 | User does not have permission. | Ensure the user is an Account Admin, Organization Admin, or Workspace Admin. |

---

## 5. Get Variable Details

Returns the full definition of a specific variable, including its values/range, all per-user overrides, and display format.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/variables/<variable-id>` |
| **OAuth Scope** | `ZohoAnalytics.modeling.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or a Workspace Admin of the specified workspace. |

> This API has no CONFIG parameter.

### Sample Requests

**Case 1 — Get details of a List-type variable with per-user overrides**

```http
GET /restapi/v2/workspaces/137687000271334001/variables/137687000007146340 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Get details of a Range-type variable**

```http
GET /restapi/v2/workspaces/137687000271334001/variables/137687000007146342 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 3 — Get details of a Currency-formatted variable**

```http
GET /restapi/v2/workspaces/137687000271334001/variables/137687000007146350 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

### Sample Responses

**HTTP 200 OK — List-type variable with two per-user overrides**

```json
{
  "status": "success",
  "summary": "Get variable details",
  "data": {
    "variableName": "Region",
    "variableType": 0,
    "variableDataType": 1,
    "userSpecificData": [
      {
        "values": ["4", "5", "6"],
        "defaultValue": "4",
        "emailIds": ["sales.east@zylker.com"]
      },
      {
        "values": ["7", "8", "9"],
        "defaultValue": "7",
        "emailIds": ["sales.west@zylker.com"]
      }
    ],
    "defaultData": {
      "values": ["1", "2", "3"],
      "defaultValue": "1"
    },
    "format": {
      "alignment": "Left"
    }
  }
}
```

**HTTP 200 OK — Range-type Number variable, no per-user overrides**

```json
{
  "status": "success",
  "summary": "Get variable details",
  "data": {
    "variableName": "Target Sales",
    "variableType": 1,
    "variableDataType": 4,
    "userSpecificData": [],
    "defaultData": {
      "minValue": "1",
      "maxValue": "3",
      "stepSize": "1",
      "defaultValue": "2"
    },
    "format": {
      "alignment": "Right",
      "units": "None",
      "decimalPlaces": -1,
      "userLocale": false,
      "thousandSeparator": 0,
      "decimalSeparator": 0
    }
  }
}
```

**HTTP 200 OK — Currency-formatted variable**

```json
{
  "status": "success",
  "summary": "Get variable details",
  "data": {
    "variableName": "Unit Cost",
    "variableType": 0,
    "variableDataType": 7,
    "userSpecificData": [],
    "defaultData": {
      "values": ["1", "2", "3"],
      "defaultValue": "1"
    },
    "format": {
      "alignment": "Right",
      "currencySymbol": "en;US;",
      "showNegativeSign": true,
      "units": "None",
      "decimalPlaces": 2,
      "userLocale": false,
      "thousandSeparator": 1,
      "decimalSeparator": 0
    }
  }
}
```

**HTTP 200 OK — All Values-type variable**

```json
{
  "status": "success",
  "summary": "Get variable details",
  "data": {
    "variableName": "All Regions",
    "variableType": 3,
    "variableDataType": 1,
    "userSpecificData": [
      {
        "values": ["1", "2", "3"],
        "emailIds": ["sales.orgadmin@zylker.com"]
      }
    ],
    "format": {
      "alignment": "Left"
    }
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `variableName` | String | Display name of the variable. |
| `variableType` | Integer | `0` = List, `1` = Range, `3` = All Values. **Returned as a native integer here**, unlike Get Variables which returns it as a string. |
| `variableDataType` | Integer | `1` = Text, `4` = Number, `5` = Positive Number, `6` = Decimal Number, `7` = Currency, `8` = Percentage. Also a native integer. |
| `userSpecificData` | Array | Per-user override entries. Empty array if no per-user overrides are configured. |
| `userSpecificData[].values` | Array of String | **List type only.** The set of allowed values for the user(s) in this entry. |
| `userSpecificData[].minValue` / `maxValue` / `stepSize` | String | **Range type only.** The numeric bounds and increment for the user(s) in this entry. |
| `userSpecificData[].defaultValue` | String | The default value/range-point applied for the user(s) in this entry. Omitted for **All Values**-type variables, since no default value concept applies. |
| `userSpecificData[].emailIds` | Array of String | Email addresses this override entry applies to. |
| `defaultData` | JSONObject | The workspace-wide fallback definition applied to any user not covered by a `userSpecificData` entry. **Omitted entirely for All Values-type variables** (see the fourth sample above), since there is no fallback value concept for that type. |
| `defaultData.values` / `defaultValue` | Array of String / String | **List type.** Allowed values and the fallback default. |
| `defaultData.minValue` / `maxValue` / `stepSize` / `defaultValue` | String | **Range type.** Numeric bounds, increment, and fallback default. |
| `format` | JSONObject | Display formatting settings. Always present, though its inner keys vary by `variableDataType` (e.g., `currencySymbol`/`showNegativeSign` only appear for Currency; `showPercent` only for Percentage). |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **`variableType`/`variableDataType` are integers here, strings in Get Variables** | The reverse of the type note in Get Variables — this API returns native JSON integers for both fields. |
| **`defaultData` may be entirely absent** | For All Values-type variables, the response has no `defaultData` key at all — check for its presence before accessing its sub-fields. |
| **`format` contents depend on `variableDataType`** | Only inspect `currencySymbol`/`showNegativeSign` when `variableDataType` is `7` (Currency), and only inspect `showPercent` when it is `8` (Percentage) — these keys are omitted for other data types. |
| **Values inside `values`/`minValue`/`maxValue`/`stepSize`/`defaultValue` are always strings** | Even for numeric data types (Number, Currency, etc.), these fields are serialized as strings to preserve precision — parse them into numbers in your application if further calculation is required. |
| **Dependency** | `<variable-id>` → Get Variables. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 70320 | `USERVARIABLE_VARIABLE_NOT_FOUND` — `<variable-id>` does not exist in this workspace. | Verify `<variable-id>` using Get Variables. |
| 7301 | User does not have permission. | Ensure the user is an Account Admin, Organization Admin, or Workspace Admin. |

---

## Appendix A – Common HTTP Headers

| Header | Value | Required | Notes |
|--------|-------|----------|-------|
| `Authorization` | `Zoho-oauthtoken <oauth-token>` | **Mandatory** | OAuth 2.0 access token of the calling user. |
| `ZANALYTICS-ORGID` | Organisation ID | **Mandatory** for all APIs | Organisation ID of the workspace. |
| `Content-Type` | `application/x-www-form-urlencoded` | Required for POST/PUT with body | Not required for GET/DELETE requests without CONFIG. |

> **White Label / Client Portal:** All five variable APIs are available via portal domain URLs when the caller has the required permission. The `domainName` field within `userSpecificData` entries is specifically designed for multi-domain Client Portal scenarios.

---

## Appendix B – OAuth Scope Summary

| API | Method | Scope |
|-----|--------|-------|
| Create Variable | POST | `ZohoAnalytics.modeling.create` |
| Edit Variable | PUT | `ZohoAnalytics.modeling.update` |
| Delete Variable | DELETE | `ZohoAnalytics.modeling.delete` |
| Get Variables | GET | `ZohoAnalytics.modeling.read` |
| Get Variable Details | GET | `ZohoAnalytics.modeling.read` |

---

## Appendix C – API-Specific Notes and Behaviours

### Create Variable

- **Permission is stricter than most modeling APIs in this documentation suite.** There is no permission-based alternative here (e.g., no "Create Formula"/"Design Modify" option) — only Account Admin, Organization Admin, or Workspace Admin roles can create variables. Regular users with granular permissions cannot.
- **`variableType` and `variableDataType` together gate what fields are valid.** Always cross-check the [Variable Type Values](#variable-type-values) and [Variable Data Type Values](#variable-data-type-values) tables before constructing a request — an otherwise well-formed request fails outright if the combination is invalid (e.g., Range + Text).
- **Dependency chain:** Get Workspace List → Create Variable → `variableId` returned in response → reference the variable by name (`${variableName}`) in formulas/filters/SQL.

### Edit Variable

- **This is a full-replace API, not a patch API** — the exact same behavior pattern as [Edit Query Table](QUERY_TABLES_API_DOC_INFO.md#3-edit-query-table), which also requires resending the complete definition. Always fetch the current definition via Get Variable Details first, modify only the fields you intend to change, then resend the full CONFIG.
- **Uniquely among the Edit APIs in this documentation suite, this one supports changing the fundamental "shape" of the object** (`variableType` and `variableDataType`) rather than just its name/values — but doing so is blocked (error 70358) if existing formulas/reports depend on the variable in a way incompatible with the new shape.
- **Dependency chain:** Get Variable Details (fetch current state) → Edit Variable (resend full, modified CONFIG).

### Delete Variable

- **No dedicated "Get Variable Dependents" API exists in this suite**, unlike columns and aggregate formulas which both have their own dependents-lookup endpoints. To determine what references a variable before deleting it, review formula expressions (via [Get Custom Formulas](FORMULA_COLUMNS_API_DOC_INFO.md#1-get-custom-formulas) / [Get Aggregate Formula](AGGREGATE_FORMULAS_API_DOC_INFO.md#1-get-aggregate-formula)) and report/query definitions for `${variableName}` references manually.
- **No cascade-delete flag** — this is a deliberate difference from Delete Column/Delete Aggregate Formula's `deleteDependentViews` option; dependent objects must always be updated or removed manually first.
- **Dependency chain:** Get Variables → (manually verify no formula/report references exist) → Delete Variable.

### Get Variables

- **Lightweight listing, integer-as-string fields.** Use this for building selection UIs or inventories; switch to Get Variable Details only when the full value set is needed, since `variableType`/`variableDataType` here are strings rather than integers.
- **Dependency chain:** Get Workspace List → Get Variables → `variableId` feeds into Get Variable Details / Edit / Delete Variable.

### Get Variable Details

- **The most detailed "read" response in this API family** — includes conditional per-type fields (`values` vs. `minValue`/`maxValue`/`stepSize`) and an optional top-level `defaultData` object that may be entirely absent for All Values-type variables.
- **Always branch your parsing logic on `variableType` first**, then on `variableDataType` for format-specific fields, since the shape of `defaultData`/`userSpecificData` entries and `format` both depend on these two enums.
- **Dependency chain:** Get Variables (`variableId`) → Get Variable Details.

---

## Appendix D – General Response Payload Notes

| Field / Behaviour | Detail |
|-------------------|--------|
| **`variableType`/`variableDataType` type inconsistency across read APIs** | Get Variables returns these as strings (`"0"`, `"1"`); Get Variable Details returns them as native integers (`0`, `1`). This is the most important cross-API parsing note in this document — do not assume consistent JSON types for the same logical field across different endpoints. |
| **All numeric variable values are transmitted as strings** | `values`, `minValue`, `maxValue`, `stepSize`, and `defaultValue` are always JSON strings in both requests and responses, regardless of the variable's numeric `variableDataType` — this preserves precision for large/decimal numbers. |
| **`defaultData` presence is conditional on `variableType`** | Only List (`0`) and Range (`1`) type variables have a `defaultData` object; All Values (`3`) type variables omit it entirely, both in requests (it is ignored/rejected if sent) and in Get Variable Details responses. |
| **Empty response bodies are common for mutating calls** | Edit Variable and Delete Variable both return HTTP **204 No Content** with no JSON body at all — treat the 2xx status code as the success indicator, not the presence/absence of a `status` field. |
| **Variables are referenced by name, not ID, in downstream APIs** | Unlike columns or formulas (referenced by ID in dependents/value APIs), workspace variables are referenced inside formula expressions and SQL queries using their `variableName` wrapped in `${...}` syntax — the `variableId` returned by these APIs is only used for managing the variable definition itself (Edit/Delete/Get Details), not for embedding it elsewhere. |
