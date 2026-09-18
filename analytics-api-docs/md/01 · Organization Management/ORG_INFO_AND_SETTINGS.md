# Zoho Analytics V2 REST API — Organisation Information

These APIs provide information about the organisations, resource usage, subscription plan, and workspace/view identity lookups available to the authenticated user. They are read-only metadata APIs and do not modify any data.

---

## Index

| # | API Name | Method | URL |
|---|----------|--------|-----|
| 1 | [Get Org List](#1-get-org-list) | GET | `/restapi/v2/orgs` |
| 2 | [Get Resource Details](#2-get-resource-details) | GET | `/restapi/v2/resources` |
| 3 | [Get Subscription Details](#3-get-subscription-details) | GET | `/restapi/v2/subscription` |
| 4 | [Get Meta Details From Name](#4-get-meta-details-from-name) | GET | `/restapi/v2/metadetails` |

---

## 1. Get Org List

Returns the list of Zoho Analytics organisations that the authenticated user belongs to. For each organisation, the response includes the user's role within that organisation, the number of workspaces, and plan details.

This is a **user-scoped** API — no `ZANALYTICS-ORGID` header is required. The result reflects the caller's membership across all organisations, not the contents of a single organisation.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/orgs` |
| **OAuth Scope** | `ZohoAnalytics.metadata.read` |
| **ZANALYTICS-ORGID Header** | Not required — user-scoped, returns data across all organisations. |
| **Permission Required** | Any authenticated Zoho Analytics user. |

### CONFIG Parameter

The CONFIG parameter is optional. When provided, it is passed as a query parameter named `CONFIG`.

> **Note:** The `getOrgsConfig` template exposes only one field. All other filtering is implicit — the API always returns only the organisations the authenticated user is a member of.

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| *(none)* | — | — | — | This API takes no CONFIG fields. |

> If you do not need any filtering, omit CONFIG entirely — the API returns all accessible organisations.

### Sample Requests

**Case 1 — Get all organisations for the authenticated user**

```http
GET /restapi/v2/orgs HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
```

**Case 2 — Account Admin who owns one org and is a member of others**

```http
GET /restapi/v2/orgs HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.aaaaaa.bbbbbb
```

### Sample Responses

**HTTP 200 OK**

**Case 1 — Account Admin user in a single org**
```json
{
  "status": "success",
  "summary": "Get organizations",
  "data": {
    "orgs": [
      {
        "orgId": "64036181",
        "orgName": "acme-analytics",
        "orgDesc": "",
        "createdBy": "admin@acme.com",
        "createdByZuId": "64035928",
        "planName": "Enterprise",
        "isDefault": true,
        "numberOfWorkspaces": 41,
        "role": "Account Admin"
      }
    ]
  }
}
```

**Case 2 — Org Admin user who belongs to multiple organisations**
```json
{
  "status": "success",
  "summary": "Get organizations",
  "data": {
    "orgs": [
      {
        "orgId": "64036201",
        "orgName": "dev-team-analytics",
        "orgDesc": "",
        "createdBy": "orgadmin@dev.com",
        "createdByZuId": "64036024",
        "planName": "Premium",
        "isDefault": false,
        "numberOfWorkspaces": 1,
        "role": "Account Admin"
      },
      {
        "orgId": "64036181",
        "orgName": "acme-analytics",
        "orgDesc": "",
        "createdBy": "admin@acme.com",
        "createdByZuId": "64035928",
        "planName": "Enterprise",
        "isDefault": false,
        "numberOfWorkspaces": 41,
        "role": "Organization Admin"
      }
    ]
  }
}
```

**Case 3 — Shared User in another user's org (shows workspaces shared with them)**
```json
{
  "status": "success",
  "summary": "Get organizations",
  "data": {
    "orgs": [
      {
        "orgId": "64036287",
        "orgName": "shared-user-own-org",
        "orgDesc": "",
        "createdBy": "shareduser@test.com",
        "createdByZuId": "64036387",
        "planName": "Premium",
        "isDefault": false,
        "numberOfWorkspaces": 3,
        "role": "Account Admin"
      },
      {
        "orgId": "64036181",
        "orgName": "acme-analytics",
        "orgDesc": "",
        "createdBy": "admin@acme.com",
        "createdByZuId": "64035928",
        "planName": "Enterprise",
        "isDefault": false,
        "numberOfWorkspaces": 18,
        "role": "User"
      }
    ]
  }
}
```

> **`numberOfWorkspaces` interpretation:** For Account Admin and Organization Admin roles, this is the total count of all workspaces in the org. For all other roles (`User`, `Workspace Admin`, etc.), this is the count of workspaces that have been **shared** with the user within that org — not the total workspace count.

**Case 4 — User with no Zoho Analytics organisation memberships**
```json
{
  "status": "success",
  "summary": "Get organizations",
  "data": {
    "orgs": []
  }
}
```

#### Response Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `orgs` | Array | List of organisations the user belongs to. Empty array if the user has no Analytics org membership. |
| `orgs[].orgId` | String | Unique identifier of the organisation. Use this as the `ZANALYTICS-ORGID` header value in workspace-scoped APIs. |
| `orgs[].orgName` | String | Display name of the organisation. |
| `orgs[].orgDesc` | String | Description of the organisation. Empty string if not set. |
| `orgs[].createdBy` | String | Email address of the user who created (owns) this organisation. |
| `orgs[].createdByZuId` | String | Zoho User ID of the organisation creator. |
| `orgs[].planName` | String | Current subscription plan name for this organisation (e.g., `"Enterprise"`, `"Premium"`, `"Basic"`). |
| `orgs[].isDefault` | Boolean | `true` if this is the calling user's default organisation. Only one org per user can have `isDefault: true`. |
| `orgs[].numberOfWorkspaces` | Integer | Number of workspaces visible to the user. For admins: all workspaces in the org. For other roles: only workspaces shared with the user. |
| `orgs[].role` | String | The calling user's role in this organisation. Possible values: `"Account Admin"`, `"Organization Admin"`, `"User"`. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.metadata.read`. |

---

## 2. Get Resource Details

Returns the current resource allocation and usage statistics for the specified organisation. This includes metrics such as user seats, row limits, API units, scheduled imports, and other plan-governed resources. Useful for monitoring usage against plan limits.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/resources` |
| **OAuth Scope** | `ZohoAnalytics.usermanagement.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID to fetch resource details for. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin of the specified organisation. |

> This API has no CONFIG parameter.

### Sample Requests

**Case 1 — Account Admin checking resource usage**

```http
GET /restapi/v2/resources HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Org Admin checking usage for their org**

```http
GET /restapi/v2/resources HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.aaaaaa.bbbbbb
ZANALYTICS-ORGID: 700000654321
```

### Sample Responses

**HTTP 200 OK**

**Case 1 — Enterprise plan with mix of fixed and unlimited resources**
```json
{
  "status": "success",
  "summary": "Get resource details",
  "data": {
    "resourceDetails": [
      {
        "resourceName": "users",
        "resourceUsage": { "allocated": "15", "used": "4", "remaining": "11", "remarks": "" }
      },
      {
        "resourceName": "roUsers",
        "resourceUsage": { "allocated": "25", "used": "2", "remaining": "23", "remarks": "" }
      },
      {
        "resourceName": "workspaces",
        "resourceUsage": { "allocated": "Unlimited", "used": "1", "remaining": "Unlimited", "remarks": "" }
      },
      {
        "resourceName": "rows",
        "resourceUsage": { "allocated": "5000000", "used": "755", "remaining": "4999245", "remarks": "" }
      },
      {
        "resourceName": "queryTables",
        "resourceUsage": { "allocated": "Unlimited", "used": "0", "remaining": "Unlimited", "remarks": "" }
      },
      {
        "resourceName": "archivedrows",
        "resourceUsage": { "allocated": "500000", "used": "null", "remaining": "500000", "remarks": "" }
      },
      {
        "resourceName": "scheduledImports",
        "resourceUsage": { "allocated": "Unlimited", "used": "0", "remaining": "Unlimited", "remarks": "" }
      },
      {
        "resourceName": "scheduledEmails",
        "resourceUsage": { "allocated": "30", "used": "0", "remaining": "30", "remarks": "" }
      },
      {
        "resourceName": "apiUnits",
        "resourceUsage": { "allocated": "30000", "used": "23.3", "remaining": "29976.7", "remarks": "" }
      },
      {
        "resourceName": "scheduledAlerts",
        "resourceUsage": { "allocated": "30", "used": "0", "remaining": "30", "remarks": "" }
      },
      {
        "resourceName": "scheduledSnapshots",
        "resourceUsage": { "allocated": "Unlimited", "used": "0", "remaining": "Unlimited", "remarks": "" }
      },
      {
        "resourceName": "archiveschedule",
        "resourceUsage": { "allocated": "25", "used": "0", "remaining": "25", "remarks": "" }
      },
      {
        "resourceName": "privateLinks",
        "resourceUsage": { "allocated": "15", "used": "0", "remaining": "15", "remarks": "" }
      },
      {
        "resourceName": "actionsByFlow",
        "resourceUsage": { "allocated": "500", "used": "0", "remaining": "500", "remarks": "" }
      }
    ]
  }
}
```

#### Response Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `resourceDetails` | Array | List of resource usage objects, one per resource type. |
| `resourceDetails[].resourceName` | String | Identifier of the resource type. See the Resource Name Reference table below. |
| `resourceDetails[].resourceUsage.allocated` | String | Total allocation for this resource under the current plan. `"Unlimited"` means the plan has no cap on this resource. |
| `resourceDetails[].resourceUsage.used` | String | Amount currently consumed. May be `"null"` for resources where usage tracking is deferred (e.g., `archivedrows`). Fractional values are possible for `apiUnits`. |
| `resourceDetails[].resourceUsage.remaining` | String | Remaining allocation (`allocated - used`). `"Unlimited"` if the resource is uncapped. |
| `resourceDetails[].resourceUsage.remarks` | String | Additional context or notes about the resource limit. Empty string when no remarks apply. |

#### Resource Name Reference

| `resourceName` | Description |
|----------------|-------------|
| `users` | Paid user seats (users who can create and edit views). |
| `roUsers` | Read-only/viewer user seats. |
| `workspaces` | Number of workspaces allowed in the organisation. |
| `rows` | Total number of data rows allowed across all tables. |
| `queryTables` | Number of Query Tables allowed. |
| `archivedrows` | Number of rows allowed in archived (cold storage) tables. |
| `scheduledImports` | Number of scheduled data import jobs allowed. |
| `scheduledEmails` | Number of scheduled email reports allowed per month. |
| `apiUnits` | API unit consumption quota (each API call deducts units based on operation type). |
| `scheduledAlerts` | Number of scheduled alert rules allowed. |
| `scheduledSnapshots` | Number of scheduled snapshot jobs allowed. |
| `archiveschedule` | Number of archive schedule jobs allowed. |
| `financeMultiorgImports` | Number of multi-org Finance integration import pipelines allowed. |
| `privateLinks` | Number of private link connections allowed. |
| `actionsByFlow` | Number of automated flow action triggers allowed per month. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Organisation not found. | Verify the `ZANALYTICS-ORGID` header value. |
| 7301 | User is not an Account Admin or Organization Admin of the specified organisation. | Only Account Admins and Organization Admins can view resource details. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.usermanagement.read`. |

---

## 3. Get Subscription Details

Returns the current subscription plan, add-on details, billing date, and trial status for the specified organisation.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/subscription` |
| **OAuth Scope** | `ZohoAnalytics.usermanagement.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID to fetch subscription details for. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin of the specified organisation. |

> This API has no CONFIG parameter.

### Sample Requests

**Case 1 — Account Admin checking subscription for their org**

```http
GET /restapi/v2/subscription HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Org Admin checking subscription for the org they manage**

```http
GET /restapi/v2/subscription HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.aaaaaa.bbbbbb
ZANALYTICS-ORGID: 700000654321
```

### Sample Responses

**HTTP 200 OK**

**Case 1 — Premium plan, active subscription with add-ons, not on trial**
```json
{
  "status": "success",
  "summary": "Get subscription details",
  "data": {
    "subscription": {
      "planName": "Premium",
      "addOns": "25 Viewers",
      "billingDate": "22 Jun 2021",
      "trialStatus": false
    }
  }
}
```

**Case 2 — Organisation on a trial period (includes `trialEndsOn`)**
```json
{
  "status": "success",
  "summary": "Get subscription details",
  "data": {
    "subscription": {
      "planName": "Enterprise",
      "addOns": "",
      "billingDate": "-1",
      "trialStatus": true,
      "trialEndsOn": "Sat Jul 15 23:59:59 IST 2026"
    }
  }
}
```

**Case 3 — Internal/Ultimate plan (no billing date)**
```json
{
  "status": "success",
  "summary": "Get subscription details",
  "data": {
    "subscription": {
      "planName": "Ultimate",
      "addOns": "",
      "billingDate": "-1",
      "trialStatus": false
    }
  }
}
```

#### Response Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `subscription.planName` | String | Name of the active subscription plan (e.g., `"Basic"`, `"Standard"`, `"Premium"`, `"Enterprise"`, `"Ultimate"`). |
| `subscription.addOns` | String | Description of any add-on purchases (e.g., `"25 Viewers"`). Empty string if no add-ons are active. |
| `subscription.billingDate` | String | Next billing/renewal date in human-readable format (e.g., `"22 Jun 2021"`). Returns `"-1"` if the plan is on a trial, is an internal plan with no billing cycle, or the billing date is not applicable. |
| `subscription.trialStatus` | Boolean | `true` if the organisation is currently on an active trial period. `false` otherwise. |
| `subscription.trialEndsOn` | String | *(Present only when `trialStatus` is `true`)* The date and time when the trial period ends. Format: standard Java date string. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Organisation not found. | Verify the `ZANALYTICS-ORGID` header value. |
| 7301 | User is not an Account Admin or Organization Admin of the specified organisation. | Only Account Admins and Organization Admins can view subscription details. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.usermanagement.read`. |

---

## 4. Get Meta Details From Name

Resolves a workspace (and optionally a view) **by name** to return its numeric IDs. This is useful when you know the human-readable names of a workspace and view but need their IDs to call other workspace-scoped or view-scoped APIs.

- When only `workspaceName` is provided: returns the workspace ID, description, and org ID.
- When both `workspaceName` and `viewName` are provided: additionally returns the view's ID, description, and type.

> **Name uniqueness:** Workspace names are unique within an organisation. View names are unique within a workspace. This API performs an exact, case-sensitive match on the provided names.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/metadetails` |
| **OAuth Scope** | `ZohoAnalytics.metadata.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID in which the workspace exists. |
| **Permission Required** | The authenticated user must have at least Read access on the specified workspace (for workspace-only lookup), or Read access on the specific view (for view lookup). Workspace Admins, Account Admins, Organization Admins, and any user with at least one shared view in the workspace can call this API. |

### CONFIG Parameter

CONFIG is **mandatory** for this API. It must be sent as a query parameter named `CONFIG`.

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `workspaceName` | String | **Yes** | — | The exact display name of the workspace to look up. Must match the workspace name as it appears in the Zoho Analytics UI, including case. Maximum length: 50 characters. |
| `viewName` | String | No | — | The exact display name of a view within the workspace. When provided, the response additionally includes the view's ID, type, and description. When omitted, only workspace information is returned. Maximum length: 50 characters. |

### Sample Requests

**Case 1 — Look up a workspace by name only**

```http
GET /restapi/v2/metadetails?CONFIG={"workspaceName":"Sales Analytics"} HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Look up a workspace and a specific view within it**

```http
GET /restapi/v2/metadetails?CONFIG={"workspaceName":"Sales Analytics","viewName":"Revenue Trend"} HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 3 — Shared user resolving the ID of a view they have access to**

```http
GET /restapi/v2/metadetails?CONFIG={"workspaceName":"V2Api_WhiteLabelUsers_analytics","viewName":"ChartWL1"} HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.aaaaaa.bbbbbb
ZANALYTICS-ORGID: 700000789012
```

### Sample Responses

**HTTP 200 OK**

**Case 1 — Workspace-only lookup**
```json
{
  "status": "success",
  "summary": "Get meta details",
  "data": {
    "workspaces": {
      "workspaceId": "320862000000625871",
      "workspaceName": "Sales Analytics",
      "workspaceDesc": "",
      "orgId": "106044221"
    }
  }
}
```

**Case 2 — Workspace and view lookup (Admin user)**
```json
{
  "status": "success",
  "summary": "Get meta details",
  "data": {
    "workspaces": {
      "workspaceId": "38190000004180410",
      "workspaceName": "Sales Analytics",
      "workspaceDesc": "Main sales reporting workspace",
      "orgId": "57058019"
    },
    "views": {
      "viewId": "38190000004180412",
      "viewName": "Revenue Trend",
      "viewDesc": "",
      "viewType": "AnalysisView"
    }
  }
}
```

**Case 3 — Shared user resolving a view they have access to**
```json
{
  "status": "success",
  "summary": "Get meta details",
  "data": {
    "workspaces": {
      "workspaceId": "38190000004180410",
      "workspaceName": "V2Api_WhiteLabelUsers_analytics",
      "workspaceDesc": "",
      "orgId": "57058019"
    },
    "views": {
      "viewId": "38190000004180412",
      "viewName": "ChartWL1",
      "viewDesc": "",
      "viewType": "AnalysisView"
    }
  }
}
```

**Case 4 — Permission denied (user has no access to the workspace or view)**

```json
{
  "status": "failure",
  "summary": "SECURITY_NOT_PERMITTED",
  "data": {
    "errorCode": 7301,
    "errorMessage": "You do not have the permission to get information. You need to have READ permission to do this operation."
  }
}
```

#### Response Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `data.workspaces.workspaceId` | String | Numeric ID of the workspace. Use this as `<workspace-id>` in workspace-scoped API URLs. |
| `data.workspaces.workspaceName` | String | Display name of the workspace (echoed from the request). |
| `data.workspaces.workspaceDesc` | String | Description of the workspace. Empty string if not set. |
| `data.workspaces.orgId` | String | Organisation ID that owns this workspace. |
| `data.views` | Object | Present only when `viewName` was included in the request. |
| `data.views.viewId` | String | Numeric ID of the view. Use this as `<view-id>` in view-scoped API URLs. |
| `data.views.viewName` | String | Display name of the view (echoed from the request). |
| `data.views.viewDesc` | String | Description of the view. Empty string if not set. |
| `data.views.viewType` | String | Type of the view (e.g., `"Table"`, `"AnalysisView"`, `"Pivot"`, `"SummaryView"`, `"Query Table"`, `"Dashboard"`). |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Organisation not found. | Verify the `ZANALYTICS-ORGID` header value. |
| 7104 | Workspace or view not found by the provided name. | Verify the exact spelling and case of `workspaceName` and `viewName`. Names are case-sensitive. |
| 7301 | User does not have Read access on the workspace or view. | Ensure the workspace or view is shared with the user, or the user has Workspace Admin / Account Admin / Organization Admin role. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.metadata.read`. |

---

## Appendix A – Common HTTP Headers

| Header | Value | Required | Notes |
|--------|-------|----------|-------|
| `Authorization` | `Zoho-oauthtoken <oauth-token>` | **Mandatory** | OAuth 2.0 access token of the calling user. |
| `ZANALYTICS-ORGID` | Organisation ID | Required for Get Resource Details, Get Subscription Details, and Get Meta Details From Name | Not required for **[Get Org List](#1-get-org-list)** — that API is user-scoped across all orgs. Use `orgId` from the Get Org List response as the value for this header. |

---

## Appendix B – OAuth Scope Summary

| API | Method | Scope |
|-----|--------|-------|
| Get Org List | GET | `ZohoAnalytics.metadata.read` |
| Get Resource Details | GET | `ZohoAnalytics.usermanagement.read` |
| Get Subscription Details | GET | `ZohoAnalytics.usermanagement.read` |
| Get Meta Details From Name | GET | `ZohoAnalytics.metadata.read` |

---

## Appendix C – Operational Notes and Failure Cases

### Get Org List

| Scenario | Behaviour |
|----------|-----------|
| User belongs to no Zoho Analytics organisation | Returns HTTP 200 with an empty `orgs` array. No error is raised. |
| User is Account Admin in one org and a regular User in another | Both orgs appear in the list. The `role` field differs per entry. `numberOfWorkspaces` reflects all workspaces for the admin org, and only shared workspaces for the User-role org. |
| `isDefault` field | Only one entry in the list will have `isDefault: true`. This corresponds to the user's primary (default) organisation. If the user has a single org, it is always the default. |
| User is a member of an expired or blocked org | Expired/blocked orgs are suppressed from the response. Only active organisations are returned. |

### Get Resource Details

| Scenario | Behaviour |
|----------|-----------|
| `used` value is `"null"` for a resource | Indicates that usage tracking for that resource is asynchronous or not yet computed. The `remaining` value is calculated from the `allocated` limit assuming `0` actual usage. |
| `allocated` is `"Unlimited"` | The plan places no hard cap on this resource. `remaining` is also `"Unlimited"`. |
| `apiUnits` shows fractional values | API unit consumption is tracked at sub-unit precision. The `used` and `remaining` values may contain decimal values (e.g., `"23.3"`). |
| Workspace Admin or regular user calls this API | The request fails with error **7301** — this API is restricted to Account Admin and Organization Admin only. |

### Get Subscription Details

| Scenario | Behaviour |
|----------|-----------|
| Organisation is on a trial | `trialStatus` is `true` and the `trialEndsOn` field is included with the trial expiry date. `billingDate` may be `"-1"` during trial. |
| Organisation has an internal/ultimate plan | `billingDate` is `"-1"` and `trialStatus` is `false`. These plan types do not follow the standard billing cycle. |
| Organisation has no add-ons purchased | `addOns` is an empty string `""`. |
| Trial has expired | `trialStatus` returns `false`. The org may be on a restricted state. Use Get Resource Details to check current limits. |

### Get Meta Details From Name

| Scenario | Behaviour |
|----------|-----------|
| `workspaceName` is provided but the workspace does not exist in the org | Fails with error **7104**. The lookup is scoped to the organisation in `ZANALYTICS-ORGID` — a workspace by that name in a different org will not be found. |
| `viewName` is provided but the workspace exists and the view does not | Fails with error **7104** for the view. The workspace metadata is not returned in failure responses. |
| Name match is case-sensitive | `"Sales Analytics"` and `"sales analytics"` are treated as different names. Verify the exact case as it appears in the Zoho Analytics UI. |
| User has access to the workspace but not the specific view | When `viewName` is in CONFIG, security is checked specifically against the view. If the view is not accessible to the user, the request fails with error **7301** even if the user can see the workspace. |
| User is a shared user with access to only one view in the workspace | Workspace-only lookup (no `viewName`) succeeds only if the user has any view shared with them in that workspace. If the workspace has views but none are shared with the user, the request fails with **7301**. |
| Using this API to bootstrap other API calls | This is the recommended approach for name-based integrations. Call Get Meta Details From Name to resolve `workspaceId` and `viewId`, then pass those IDs to downstream APIs (Get View Details, Export Data, etc.). This avoids hard-coding numeric IDs which can change across environments. |
