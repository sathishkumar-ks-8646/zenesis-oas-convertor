# Zoho Analytics V2 REST API — Workspace User Management

These APIs manage users and administrators at the **workspace level** — controlling who has access to a specific workspace, their role within it, and their active/inactive status. They complement the org-level user management APIs and operate on a single workspace at a time.

> **Workspace-Level vs Org-Level:** Org-level user management controls membership in the organisation (who is a member at all). Workspace-level management controls which of those members can access a specific workspace and in what capacity.

> **White Label / Client Portal:** When the org's Account Admin is also a Client Portal Admin, workspace user operations can be scoped to a specific portal domain using the `domainName` field. Users belonging to a portal domain are listed and managed separately from standard Zoho Analytics users.

---

## Index

| # | API Name | Method | URL |
|---|----------|--------|-----|
| 1 | [Get Workspace Users](#1-get-workspace-users) | GET | `/restapi/v2/workspaces/<workspace-id>/users` |
| 2 | [Add Workspace Users](#2-add-workspace-users) | POST | `/restapi/v2/workspaces/<workspace-id>/users` |
| 3 | [Remove Workspace Users](#3-remove-workspace-users) | DELETE | `/restapi/v2/workspaces/<workspace-id>/users` |
| 4 | [Change Workspace Users Status](#4-change-workspace-users-status) | PUT | `/restapi/v2/workspaces/<workspace-id>/users/status` |
| 5 | [Change Workspace Users Role](#5-change-workspace-users-role) | PUT | `/restapi/v2/workspaces/<workspace-id>/users/role` |
| 6 | [Get Workspace Admins](#6-get-workspace-admins) | GET | `/restapi/v2/workspaces/<workspace-id>/admins` |
| 7 | [Add Workspace Admins](#7-add-workspace-admins) | POST | `/restapi/v2/workspaces/<workspace-id>/admins` |
| 8 | [Remove Workspace Admins](#8-remove-workspace-admins) | DELETE | `/restapi/v2/workspaces/<workspace-id>/admins` |

---

## 1. Get Workspace Users

Returns the list of all users who have access to the specified workspace, along with their workspace-level role and active status.

The response includes the Account Admin, Organisation Admins, Workspace Admins, standard Users, and any users assigned to custom roles. When the org's Account Admin is a Client Portal Admin, each user entry also includes a `domainName` field indicating which portal domain the user was added through.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/users` |
| **OAuth Scope** | `ZohoAnalytics.usermanagement.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace. Account Admins and Organization Admins also have access. |

> This API has no CONFIG parameter.

### Sample Requests

**Case 1 — Account Admin listing all workspace users**

```http
GET /restapi/v2/workspaces/466206000000071000/users HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Workspace Admin listing users for their workspace**

```http
GET /restapi/v2/workspaces/466206000000071000/users HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.aaaaaa.bbbbbb
ZANALYTICS-ORGID: 700000123456
```

**Case 3 — Client Portal Admin listing workspace users (portal context)**

```http
GET /restapi/v2/workspaces/466206000000071000/users HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

### Sample Responses

**HTTP 200 OK**

**Case 1 — Standard org (no client portal) — users with mixed roles**
```json
{
  "status": "success",
  "summary": "Get workspace users",
  "data": {
    "users": [
      { "emailId": "admin@acme.com", "status": true, "role": "Account Admin" },
      { "emailId": "orgadmin@acme.com", "status": true, "role": "Organization Admin" },
      { "emailId": "wsadmin1@acme.com", "status": true, "role": "Workspace Admin" },
      { "emailId": "wsadmin2@acme.com", "status": true, "role": "Workspace Admin" },
      { "emailId": "user1@acme.com", "status": true, "role": "User" },
      { "emailId": "user2@acme.com", "status": false, "role": "User" }
    ]
  }
}
```

**Case 2 — Workspace with custom role users and deactivated users**
```json
{
  "status": "success",
  "summary": "Get workspace users",
  "data": {
    "users": [
      { "emailId": "admin@acme.com", "status": true, "role": "Account Admin" },
      { "emailId": "orgadmin@acme.com", "status": true, "role": "Organization Admin" },
      { "emailId": "wsadmin@acme.com", "status": true, "role": "Workspace Admin" },
      { "emailId": "analyst1@acme.com", "status": true, "role": "AnalystRole" },
      { "emailId": "analyst2@acme.com", "status": false, "role": "AnalystRole" },
      { "emailId": "user1@acme.com", "status": true, "role": "User" }
    ]
  }
}
```

**Case 3 — Client Portal Admin response (users include `domainName`)**

When the Account Admin is a Client Portal Admin, the response includes `domainName` for every user, allowing the admin to distinguish which portal domain each user was added through.

```json
{
  "status": "success",
  "summary": "Get workspace users",
  "data": {
    "users": [
      { "emailId": "admin@acme.com", "status": true, "role": "Account Admin", "domainName": "analytics.zoho.com" },
      { "emailId": "orgadmin@acme.com", "status": true, "role": "Organization Admin", "domainName": "analytics.zoho.com" },
      { "emailId": "wsadmin@acme.com", "status": true, "role": "Workspace Admin", "domainName": "analytics.zoho.com" },
      { "emailId": "portal.user1@client.com", "status": true, "role": "User", "domainName": "reports.clientbrand.com" },
      { "emailId": "portal.user2@client.com", "status": false, "role": "User", "domainName": "reports.clientbrand.com" }
    ]
  }
}
```

#### Response Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `data.users` | Array | All users with access to this workspace. |
| `users[].emailId` | String | Email address of the user. |
| `users[].status` | Boolean | `true` = active (can access the workspace). `false` = deactivated (access suspended). |
| `users[].role` | String | Workspace-level role. Values: `"Account Admin"`, `"Organization Admin"`, `"Workspace Admin"`, `"User"`, or a custom role name defined in the org. |
| `users[].domainName` | String | *(Present only when Account Admin is a Client Portal Admin.)* The portal domain the user was added through. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **`domainName` in response** | Only present in each user entry when the Account Admin is a Client Portal Admin. Standard org responses return users without `domainName`. |
| **Deactivated users are included** | Users with `status: false` (deactivated) still appear in the list. They are not removed from the workspace upon deactivation. |
| **Custom role users** | Users with a custom role appear in the list with `role` set to the exact custom role name as defined in the org. |
| **Dependency for other APIs** | User email addresses returned here are needed as input for Add Workspace Users, Remove Workspace Users, Change Workspace Users Status, Change Workspace Users Role, and as reference when managing groups. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify `<workspace-id>`. |
| 7301 | User is not a Workspace Admin, Account Admin, or Organization Admin of the workspace. | Ensure the caller has at least Workspace Admin access to the workspace. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.usermanagement.read`. |

---

## 2. Add Workspace Users

Adds one or more users to the specified workspace with a given workspace-level role. Supports two modes:

- **Simple mode** — add a flat list of emails all with the same role.
- **Bulk mode** — add multiple groups of users, each group with a different role or domain, in a single request. Up to 20 groups per request.

> **Confirmed account requirement:** The calling user's Zoho account must be confirmed (email-verified) to invoke this API.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/users` |
| **OAuth Scope** | `ZohoAnalytics.usermanagement.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace. Account Admins and Organization Admins also have access. |

### CONFIG Parameter

CONFIG is **mandatory**. It must be sent as a form-encoded body parameter named `CONFIG`.

**Simple mode** (single role for all emails):

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `emailIds` | Array of Strings | **Yes** | — | List of email addresses to add. Max 1000 entries. |
| `role` | String | No | `"USER"` | Workspace-level role to assign. Allowed values: `"WORKSPACEADMIN"` (Workspace Admin), `"USER"` (standard user), or the exact name of a custom role defined in the org. When omitted, defaults to `"USER"`. |
| `domainName` | String | No | `null` | Client portal domain for portal-scoped additions. When omitted, users are added in the standard Zoho Analytics domain context. |

**Bulk mode** (different roles or domains per group):

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `users` | Array of Objects | **Yes** | — | Up to 20 user-group objects. Each object contains `emailIds` (required), `role`, and optionally `domainName`. When `users` is present, the root `emailIds`/`role`/`domainName` fields are ignored. |
| `users[].emailIds` | Array of Strings | **Yes** | — | Email addresses for this group. Max 1000 per group. |
| `users[].role` | String | No | `"USER"` | Workspace-level role for this group. Same allowed values as simple mode. |
| `users[].domainName` | String | No | `null` | Portal domain for this group. Allows adding users from different portals in one request. |

### Sample Requests

**Case 1 — Simple mode: add two standard users**

```http
POST /restapi/v2/workspaces/466206000000071000/users HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["alice@acme.com","bob@acme.com"],"role":"USER"}
```

**Case 2 — Simple mode: add a Workspace Admin**

```http
POST /restapi/v2/workspaces/466206000000071000/users HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["wsadmin@acme.com"],"role":"WORKSPACEADMIN"}
```

**Case 3 — Bulk mode: add two groups with different roles in one call**

```http
POST /restapi/v2/workspaces/466206000000071000/users HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"users":[{"emailIds":["lead.analyst@acme.com"],"role":"WORKSPACEADMIN"},{"emailIds":["viewer1@acme.com","viewer2@acme.com"],"role":"USER"}]}
```

**Case 4 — Client Portal: add portal users with a specific domain**

```http
POST /restapi/v2/workspaces/466206000000071000/users HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["portal.user@client.com"],"role":"USER","domainName":"reports.clientbrand.com"}
```

**Case 5 — Bulk mode with mixed portal domains**

```http
POST /restapi/v2/workspaces/466206000000071000/users HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"users":[{"emailIds":["user1@client.com","user2@client.com"],"role":"USER","domainName":"reports.clientbrand.com"},{"emailIds":["partner@partner.io"],"role":"USER","domainName":"analytics.partnerportal.io"}]}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Add Workspace Users returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |
| **`role` defaults to `"USER"` if omitted** | When `role` is not specified in a user entry, the user is added with the workspace-level User role. |
| **Adding an existing workspace user** | If the user is already in the workspace, their role is updated to the specified role. This is idempotent for the same role — re-adding with the same role succeeds silently. |
| **Custom role must exist in the org** | The `role` value must exactly match an existing custom role name. Invalid role names fail with error 7550. |
| **Portal users require `domainName`** | Portal-only users do not exist in the standard Zoho Analytics domain. Always specify `domainName` when adding users who belong to a portal domain. |
| **Bulk mode maximum: 20 groups per request** | Each element in the `users` array can have different `emailIds` and `role`. The array is capped at 20 entries — split larger operations. |
| **Dependency** | No prerequisite API call needed to construct the request. To verify additions, call Get Workspace Users afterward. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify `<workspace-id>`. |
| 7301 | User is not a Workspace Admin, Account Admin, or Organization Admin of the workspace. | Ensure the caller has at least Workspace Admin access. |
| 7550 | The specified `role` name does not exist as a custom role in the org. | Use `"WORKSPACEADMIN"`, `"USER"`, or an exact custom role name from the org. |
| 8060 | The specified `domainName` does not exist. | Provide a valid client portal domain name configured for the org. |
| 8061 | The specified `domainName` does not belong to the org's Account Admin. | Use a domain administered by the Account Admin of this organisation. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.usermanagement.create`. |

---

## 3. Remove Workspace Users

Removes one or more users from the specified workspace. Removed users lose all access to this workspace immediately. Their membership in the organisation and access to other workspaces is unaffected.

> **Confirmed account requirement:** The calling user's Zoho account must be confirmed (email-verified) to invoke this API.

| Attribute | Value |
|-----------|-------|
| **Method** | DELETE |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/users` |
| **OAuth Scope** | `ZohoAnalytics.usermanagement.delete` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace. Account Admins and Organization Admins also have access. |

### CONFIG Parameter

CONFIG is **mandatory**. It must be sent as a form-encoded body parameter named `CONFIG`.

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `emailIds` | Array of Strings | **Yes** | — | List of email addresses to remove from the workspace. Max 1000 entries. |
| `domainName` | String | No | `null` | Client portal domain for portal-scoped removal. When provided, removes users who were added via that specific portal domain. When omitted, removes users from the standard Zoho Analytics domain context. |

### Sample Requests

**Case 1 — Remove a single user from the workspace**

```http
DELETE /restapi/v2/workspaces/466206000000071000/users HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["contractor@acme.com"]}
```

**Case 2 — Remove multiple users at once**

```http
DELETE /restapi/v2/workspaces/466206000000071000/users HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["user1@acme.com","user2@acme.com","user3@acme.com"]}
```

**Case 3 — Client Portal: remove a portal user from a specific domain**

```http
DELETE /restapi/v2/workspaces/466206000000071000/users HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["former.client@client.com"],"domainName":"reports.clientbrand.com"}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Remove Workspace Users returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |
| **Removes user completely from the workspace** | Unlike [Remove Workspace Admins](#8-remove-workspace-admins), which only demotes, this API removes the user's entire workspace access — including any shared views, group memberships within the workspace, and admin role if applicable. |
| **All sharing permissions revoked** | All view-level and workspace-level access for the removed user is deleted immediately. |
| **Portal users require `domainName`** | If the user was added via a portal domain, specify the same `domainName` to target the correct user record. Without `domainName`, the lookup is done in the standard domain and the portal user will not be found. |
| **Dependency** | User email addresses → Get Workspace Users. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify `<workspace-id>`. |
| 7301 | User is not a Workspace Admin, Account Admin, or Organization Admin of the workspace. | Ensure the caller has at least Workspace Admin access. |
| 8060 | The specified `domainName` does not exist. | Provide a valid client portal domain name. |
| 8061 | The specified `domainName` does not belong to the org's Account Admin. | Use a domain administered by the Account Admin of this organisation. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.usermanagement.delete`. |

---

## 4. Change Workspace Users Status

Activates or deactivates one or more users in the specified workspace. The `operation` field is mandatory and determines whether users are activated or deactivated.

- **Activate** (`"activate"`): Restores a deactivated user's access to the workspace.
- **Deactivate** (`"deactivate"`): Suspends access without removing the user. Their role and permissions are preserved and restored upon reactivation.

> **Permission note:** This API is restricted to the **Account Admin** only, regardless of the workspace-level role. Workspace Admins and Organization Admins cannot call this API.

> **Confirmed account requirement:** The calling user's Zoho account must be confirmed (email-verified) to invoke this API.

| Attribute | Value |
|-----------|-------|
| **Method** | PUT |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/users/status` |
| **OAuth Scope** | `ZohoAnalytics.usermanagement.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be the **Account Admin** of the organisation that owns the workspace. |

### CONFIG Parameter

CONFIG is **mandatory**. It must be sent as a form-encoded body parameter named `CONFIG`.

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `emailIds` | Array of Strings | **Yes** | — | List of email addresses whose status should be changed. Max 1000 entries. |
| `operation` | String | **Yes** | — | The status operation to perform. Allowed values: `"activate"` (restore access) or `"deactivate"` (suspend access). Any other value fails with error **8119**. |
| `domainName` | String | No | `null` | Client portal domain for portal-scoped operations. When provided, the status change applies to users within that specific portal domain. |

### Sample Requests

**Case 1 — Deactivate a user in the workspace**

```http
PUT /restapi/v2/workspaces/466206000000071000/users/status HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["on.leave@acme.com"],"operation":"deactivate"}
```

**Case 2 — Reactivate multiple users**

```http
PUT /restapi/v2/workspaces/466206000000071000/users/status HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["user1@acme.com","user2@acme.com"],"operation":"activate"}
```

**Case 3 — Client Portal: deactivate a portal user**

```http
PUT /restapi/v2/workspaces/466206000000071000/users/status HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["portal.user@client.com"],"operation":"deactivate","domainName":"reports.clientbrand.com"}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

**Permission denied (Workspace Admin or Org Admin attempting this API)**

```json
{
  "status": "failure",
  "summary": "SECURITY_NOT_PERMITTED",
  "data": {
    "errorCode": 7301,
    "errorMessage": "You do not have the permission to do this operation. Only Account Admin has the permission."
  }
}
```

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Change Workspace Users Status returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |
| **Account Admin only** | Only Account Admins can call this API. Workspace Admins attempting this call will receive error 7301. |
| **`operation` values are case-sensitive** | Only `"activate"` and `"deactivate"` (lowercase) are valid. `"Activate"` or `"ACTIVATE"` will fail with error 8119. |
| **Idempotent status change** | Activating an already-active user or deactivating an already-inactive user both succeed silently. |
| **User data is preserved during deactivation** | All shares, roles, and permissions are retained. Reactivating the user restores their access exactly as it was. |
| **Dependency** | User email addresses → Get Workspace Users. `operation` must be `"activate"` or `"deactivate"`. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify `<workspace-id>`. |
| 7301 | User is not the Account Admin of the organisation. Only Account Admin can change workspace user status. | Use the Account Admin credentials. |
| 8060 | The specified `domainName` does not exist. | Provide a valid client portal domain name. |
| 8061 | The specified `domainName` does not belong to the org's Account Admin. | Use a domain administered by the Account Admin. |
| 8119 | Invalid value for `operation`. Only `"activate"` and `"deactivate"` are accepted. | Pass exactly `"activate"` or `"deactivate"` in the `operation` field. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.usermanagement.update`. |

---

## 5. Change Workspace Users Role

Changes the workspace-level role of one or more users in the specified workspace. Supports the same two modes as Add Workspace Users:

- **Simple mode** — change all specified emails to the same role.
- **Bulk mode** — change multiple groups of users to different roles in one request (up to 20 groups).

> **Permission note:** This API requires **Account Admin or Organization Admin** access. Workspace Admins cannot call this API.

> **Confirmed account requirement:** The calling user's Zoho account must be confirmed (email-verified) to invoke this API.

| Attribute | Value |
|-----------|-------|
| **Method** | PUT |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/users/role` |
| **OAuth Scope** | `ZohoAnalytics.usermanagement.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin of the organisation that owns the workspace. |

### CONFIG Parameter

CONFIG is **mandatory**. It must be sent as a form-encoded body parameter named `CONFIG`.

**Simple mode:**

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `emailIds` | Array of Strings | **Yes** | — | Email addresses whose role should be changed. Max 1000 entries. |
| `role` | String | **Yes** | — | New workspace-level role. Allowed values: `"WORKSPACEADMIN"`, `"USER"`, or a custom role name defined in the org. |
| `domainName` | String | No | `null` | Portal domain for portal-scoped role changes. |

**Bulk mode:**

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `users` | Array of Objects | **Yes** | — | Up to 20 user-group objects. Each object requires `emailIds` and `role`. |
| `users[].emailIds` | Array of Strings | **Yes** | — | Email addresses for this group. Max 1000 per group. |
| `users[].role` | String | **Yes** | — | New role for this group. Same allowed values as simple mode. |
| `users[].domainName` | String | No | `null` | Portal domain for this group. |

### Sample Requests

**Case 1 — Promote a user to Workspace Admin**

```http
PUT /restapi/v2/workspaces/466206000000071000/users/role HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["senior.analyst@acme.com"],"role":"WORKSPACEADMIN"}
```

**Case 2 — Bulk mode: change two groups to different roles**

```http
PUT /restapi/v2/workspaces/466206000000071000/users/role HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"users":[{"emailIds":["user1@acme.com","user2@acme.com"],"role":"WORKSPACEADMIN"},{"emailIds":["user3@acme.com","user4@acme.com"],"role":"USER"}]}
```

**Case 3 — Assign a custom role**

```http
PUT /restapi/v2/workspaces/466206000000071000/users/role HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["analyst@acme.com"],"role":"AnalystRole"}
```

**Case 4 — Client Portal: change role of a portal user**

```http
PUT /restapi/v2/workspaces/466206000000071000/users/role HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["portal.user@client.com"],"role":"USER","domainName":"reports.clientbrand.com"}
```

**Case 5 — Bulk mode with mixed portal domains**

```http
PUT /restapi/v2/workspaces/466206000000071000/users/role HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"users":[{"emailIds":["user1@client.com"],"role":"WORKSPACEADMIN","domainName":"reports.clientbrand.com"},{"emailIds":["partner@partner.io"],"role":"USER","domainName":"analytics.partnerportal.io"}]}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Change Workspace Users Role returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |
| **Requires Account Admin or Organization Admin** | Workspace Admins cannot change user roles. This prevents Workspace Admins from self-promoting or demoting other admins. |
| **Same role assignment is idempotent** | Setting a user to the role they already have succeeds without error. |
| **Demoting a Workspace Admin** | Assigning `"USER"` to a current Workspace Admin removes their admin capabilities immediately. Their workspace access continues as a regular User. |
| **`role` value must be a valid workspace role** | Use `"WORKSPACEADMIN"`, `"USER"`, or the exact name of a custom role defined in the org. Invalid values fail with error 7550. |
| **Portal users require `domainName`** | Specify `domainName` for users in a portal domain to ensure the correct user record is updated. |
| **Bulk mode maximum: 20 entries** | The `users` array is capped at 20 entries per request. Split larger operations into multiple calls. |
| **Dependency** | User email addresses → Get Workspace Users. Valid role names for custom roles → org-level role management APIs. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify `<workspace-id>`. |
| 7301 | User is not an Account Admin or Organization Admin of the organisation. Workspace Admins cannot call this API. | Use Account Admin or Organization Admin credentials. |
| 7550 | The specified `role` name does not exist as a custom role in the org. | Use `"WORKSPACEADMIN"`, `"USER"`, or an exact custom role name. |
| 8060 | The specified `domainName` does not exist. | Provide a valid client portal domain name. |
| 8061 | The specified `domainName` does not belong to the org's Account Admin. | Use a domain administered by the Account Admin. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.usermanagement.update`. |

---

## 6. Get Workspace Admins

Returns the list of users who currently hold the **Workspace Admin** role in the specified workspace. When the org's Account Admin is a Client Portal Admin, the response groups admins by portal domain — showing standard org admins and portal-domain admins separately, each with a `domainName`.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/admins` |
| **OAuth Scope** | `ZohoAnalytics.share.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin of the organisation that owns the workspace. |

> This API has no CONFIG parameter.

### Sample Requests

**Case 1 — Account Admin listing workspace admins**

```http
GET /restapi/v2/workspaces/466206000000071000/admins HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Org Admin listing workspace admins**

```http
GET /restapi/v2/workspaces/466206000000071000/admins HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.aaaaaa.bbbbbb
ZANALYTICS-ORGID: 700000123456
```

**Case 3 — Client Portal Admin listing workspace admins by domain**

```http
GET /restapi/v2/workspaces/466206000000071000/admins HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

### Sample Responses

**HTTP 200 OK**

**Case 1 — Standard org (no Client Portal) — single group**
```json
{
  "status": "success",
  "summary": "Get workspace admins",
  "data": {
    "workspaceAdmins": [
      {
        "adminMembers": ["wsadmin@acme.com"]
      }
    ]
  }
}
```

**Case 2 — Multiple Workspace Admins**
```json
{
  "status": "success",
  "summary": "Get workspace admins",
  "data": {
    "workspaceAdmins": [
      {
        "adminMembers": ["wsadmin1@acme.com", "wsadmin2@acme.com", "wsadmin3@acme.com"]
      }
    ]
  }
}
```

**Case 3 — Client Portal Admin response (admins grouped by domain)**

When the Account Admin is a Client Portal Admin, the response returns two groups: one for standard Zoho Analytics domain admins, and one for the client portal domain admins. Each group includes a `domainName` field.

```json
{
  "status": "success",
  "summary": "Get workspace admins",
  "data": {
    "workspaceAdmins": [
      {
        "adminMembers": ["wsadmin@acme.com"],
        "domainName": "analytics.zoho.com"
      },
      {
        "adminMembers": ["portal.admin@client.com"],
        "domainName": "reports.clientbrand.com"
      }
    ]
  }
}
```

> **`workspaceAdmins` is always an array.** In a standard org (non-portal), it has one entry without `domainName`. For Client Portal Admins, it has two entries — one per domain context — each with `domainName`.

#### Response Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `workspaceAdmins` | Array | One or two admin group objects. |
| `workspaceAdmins[].adminMembers` | Array of Strings | Email addresses of users with Workspace Admin role in this domain context. |
| `workspaceAdmins[].domainName` | String | *(Present only for Client Portal Admin orgs.)* The portal domain this admin group belongs to. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Returns workspace-level admins only** | This API lists users who have the Workspace Admin role. Account Admins and Org Admins are not listed here even though they have effective workspace-level admin access. |
| **`domainName` per admin group** | When the Account Admin is a Client Portal Admin, the response groups admins by domain (`workspaceAdmins` contains entries for the standard domain and each portal domain). |
| **Relationship to Get Workspace Users** | Get Workspace Users returns all users including admins; this API returns only the admins subset. Use this API when you only need the admin list (e.g., before calling Remove Workspace Admins). |
| **Dependency for other APIs** | Admin email addresses returned here are needed as input for Remove Workspace Admins. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify `<workspace-id>`. |
| 7301 | User is not an Account Admin or Organization Admin of the organisation. | Workspace Admins and regular users cannot call this API. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.share.read`. |

---

## 7. Add Workspace Admins

Grants the Workspace Admin role to one or more users in the specified workspace. Users must already be members of the workspace (or the specified portal domain). Existing Workspace Admins in the `emailIds` list are silently skipped — no error is raised for duplicates.

> **Viewer restriction:** Users who hold the org-level Viewer role cannot be promoted to Workspace Admin. Attempting to add a Viewer as a Workspace Admin fails with error **7390**.

> **Confirmed account requirement:** The calling user's Zoho account must be confirmed (email-verified) to invoke this API.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/admins` |
| **OAuth Scope** | `ZohoAnalytics.share.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin of the organisation that owns the workspace. |

### CONFIG Parameter

CONFIG is **mandatory**. It must be sent as a form-encoded body parameter named `CONFIG`.

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `emailIds` | Array of Strings | **Yes** | — | Email addresses to promote to Workspace Admin. Max 1000 entries. Existing admins in the list are silently skipped without error. |
| `domainName` | String | No | `null` | Client portal domain for portal-scoped promotion. When provided, grants Workspace Admin status for users in the specified portal domain. When omitted, applies to the standard org domain. |
| `inviteMail` | Boolean | No | `false` | When `false` (default): no email is sent to the newly added Workspace Admins. When `true`: an invitation/notification email is sent to each newly added admin informing them of their new access. |

### Sample Requests

**Case 1 — Promote a user to Workspace Admin without sending an invitation email**

```http
POST /restapi/v2/workspaces/466206000000071000/admins HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["newadmin@acme.com"]}
```

**Case 2 — Promote multiple users and send invitation emails**

```http
POST /restapi/v2/workspaces/466206000000071000/admins HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["admin1@acme.com","admin2@acme.com"],"inviteMail":true}
```

**Case 3 — Client Portal: promote a portal user to Workspace Admin in their portal domain**

```http
POST /restapi/v2/workspaces/466206000000071000/admins HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["portal.admin@client.com"],"domainName":"reports.clientbrand.com","inviteMail":true}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Add Workspace Admins returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |
| **User must already be in the workspace** | The user must have been added to the workspace (via Add Workspace Users) before they can be promoted to Workspace Admin. |
| **Viewer-role users cannot be promoted** | If any email in the batch belongs to an org-level Viewer, the entire batch fails with error 7390. Change their org role to User first via the org-level role management API. |
| **Adding an existing admin is silently skipped** | Duplicate additions do not raise an error. Only genuinely new admins receive an invitation email when `inviteMail=true`. |
| **`inviteMail=true` does not block the promotion** | Email delivery failures do not roll back the admin promotion. |
| **Dependency** | User email addresses → Get Workspace Users (to confirm users are already in the workspace). |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify `<workspace-id>`. |
| 7301 | User is not an Account Admin or Organization Admin of the organisation. | Only Account Admins and Organization Admins can manage Workspace Admins. |
| 7390 | One or more of the specified users holds the org-level Viewer role and cannot be promoted to Workspace Admin. | Viewers cannot be Workspace Admins. Change their org-level role to `"USER"` first via the Change User Role API. |
| 8060 | The specified `domainName` does not exist. | Provide a valid client portal domain name. |
| 8061 | The specified `domainName` does not belong to the org's Account Admin. | Use a domain administered by the Account Admin. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.share.create`. |

---

## 8. Remove Workspace Admins

Revokes the Workspace Admin role from one or more users in the specified workspace. All specified email addresses must currently hold Workspace Admin status in the workspace — a user who is not a Workspace Admin causes the entire request to fail with error **8040**.

> **Confirmed account requirement:** The calling user's Zoho account must be confirmed (email-verified) to invoke this API.

| Attribute | Value |
|-----------|-------|
| **Method** | DELETE |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/admins` |
| **OAuth Scope** | `ZohoAnalytics.share.delete` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin of the organisation that owns the workspace. |

### CONFIG Parameter

CONFIG is **mandatory**. It must be sent as a form-encoded body parameter named `CONFIG`.

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `emailIds` | Array of Strings | **Yes** | — | Email addresses of Workspace Admins to demote. Max 1000 entries. Every email in the list must currently be a Workspace Admin of this workspace; a non-admin email causes the entire request to fail. |
| `domainName` | String | No | `null` | Client portal domain for portal-scoped demotion. When provided, removes admin status for users in the specified portal domain. When omitted, applies to the standard org domain. |
| `notifyMail` | Boolean | No | `false` | When `false` (default): no email is sent to the removed admins. When `true`: a notification email is sent to each removed admin informing them that their Workspace Admin access has been revoked. |

### Sample Requests

**Case 1 — Demote a Workspace Admin silently**

```http
DELETE /restapi/v2/workspaces/466206000000071000/admins HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["formeradmin@acme.com"]}
```

**Case 2 — Demote and send a notification email**

```http
DELETE /restapi/v2/workspaces/466206000000071000/admins HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["admin1@acme.com","admin2@acme.com"],"notifyMail":true}
```

**Case 3 — Client Portal: revoke Workspace Admin from a portal user**

```http
DELETE /restapi/v2/workspaces/466206000000071000/admins HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["portal.admin@client.com"],"domainName":"reports.clientbrand.com"}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Remove Workspace Admins returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |
| **Demotes only — does not remove from workspace** | This API revokes the Workspace Admin role. The user remains in the workspace as a regular User with their existing view-level access. To completely remove a user from the workspace, use [Remove Workspace Users](#3-remove-workspace-users) instead. |
| **Non-admin email causes entire batch to fail** | If any email in `emailIds` is not currently a Workspace Admin, error 8040 is returned and zero demotions are applied. Always verify current admin membership using Get Workspace Admins before calling. |
| **`notifyMail=true` does not block removal** | Email delivery failures do not roll back the demotion. |
| **Removing the last Workspace Admin** | Allowed. The workspace will have no Workspace Admins. Only Account Admin and Org Admin can then manage the workspace. |
| **Dependency** | Admin email addresses → Get Workspace Admins. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify `<workspace-id>`. |
| 7301 | User is not an Account Admin or Organization Admin of the organisation. | Only Account Admins and Organization Admins can manage Workspace Admins. |
| 8040 | One or more specified email addresses are not currently Workspace Admins in this workspace. | Verify all email addresses are current Workspace Admins using Get Workspace Admins before calling this API. |
| 8060 | The specified `domainName` does not exist. | Provide a valid client portal domain name. |
| 8061 | The specified `domainName` does not belong to the org's Account Admin. | Use a domain administered by the Account Admin. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.share.delete`. |

---

## Appendix A – Common HTTP Headers

| Header | Value | Required | Notes |
|--------|-------|----------|-------|
| `Authorization` | `Zoho-oauthtoken <oauth-token>` | **Mandatory** | OAuth 2.0 access token of the calling user. |
| `ZANALYTICS-ORGID` | Organisation ID | **Mandatory** for all APIs | Organisation ID of the workspace being managed. |
| `Content-Type` | `application/x-www-form-urlencoded` | Required for POST/PUT/DELETE | Add Workspace Users, Remove Workspace Users, Change Workspace Users Status, Change Workspace Users Role, Add Workspace Admins, and Remove Workspace Admins send CONFIG as a form-encoded body parameter. Get Workspace Users and Get Workspace Admins have no body. |

---

## Appendix B – OAuth Scope Summary

| API | Method | Scope |
|-----|--------|-------|
| Get Workspace Users | GET | `ZohoAnalytics.usermanagement.read` |
| Add Workspace Users | POST | `ZohoAnalytics.usermanagement.create` |
| Remove Workspace Users | DELETE | `ZohoAnalytics.usermanagement.delete` |
| Change Workspace Users Status | PUT | `ZohoAnalytics.usermanagement.update` |
| Change Workspace Users Role | PUT | `ZohoAnalytics.usermanagement.update` |
| Get Workspace Admins | GET | `ZohoAnalytics.share.read` |
| Add Workspace Admins | POST | `ZohoAnalytics.share.create` |
| Remove Workspace Admins | DELETE | `ZohoAnalytics.share.delete` |

---

## Appendix C – API-Specific Notes and Behaviours

### Permission Summary

| API | Minimum Required Role |
|-----|-----------------------|
| Get Workspace Users | Workspace Admin |
| Add Workspace Users | Workspace Admin |
| Remove Workspace Users | Workspace Admin |
| Change Workspace Users Status | **Account Admin only** |
| Change Workspace Users Role | Account Admin or Organization Admin |
| Get Workspace Admins | Account Admin or Organization Admin |
| Add Workspace Admins | Account Admin or Organization Admin |
| Remove Workspace Admins | Account Admin or Organization Admin |

> **Key asymmetry:** [Add Workspace Users](#2-add-workspace-users) and [Remove Workspace Users](#3-remove-workspace-users) can be done by Workspace Admins, but [Change Workspace Users Status](#4-change-workspace-users-status) and [Change Workspace Users Role](#5-change-workspace-users-role) require Account Admin or higher. This prevents Workspace Admins from promoting themselves or blocking other users.

### Workspace Role Values

| `role` Value | Display Name | Description |
|-------------|--------------|-------------|
| `"WORKSPACEADMIN"` | Workspace Admin | Full access to the workspace — can add/remove users, create and delete views, manage shares. |
| `"USER"` | User | Can access views shared with them. Cannot manage workspace settings or users unless specifically shared with Design Modify permission. |
| Custom role name | (as defined) | A role name exactly matching a custom role defined in the org. Must exist — invalid names fail with error **7550**. |

> **Note:** `"VIEWER"` is an org-level role, not a workspace-level role value. At workspace level, Viewers appear as `"User"` in the response. The distinction is enforced at the org level.

### Get Workspace Users

| Scenario | Behaviour |
|----------|-----------|
| Custom role users | Appear in the list with `role` set to the exact custom role name as defined in the org (not a numeric ID). |
| Deactivated users | Appear in the list with `status: false`. They are not removed. |
| `domainName` in response | Only present when the Account Admin is a Client Portal Admin. Standard org users show the default analytics domain; portal users show their portal's domain. |
| Org Admin viewing another admin's workspace | Allowed — Org Admins have visibility into all workspaces in their org. |

### Add Workspace Users

| Scenario | Behaviour |
|----------|-----------|
| `role` omitted | Defaults to `"USER"`. |
| User already has access to the workspace | They are added again with the specified role. If the user already exists with a different role, the role is updated. |
| Bulk mode (`users` array) with 21 or more groups | Rejected at validation — max 20 groups per request. Split into multiple calls. |
| Custom role name not found in the org | Fails with error **7550**. The role name must exactly match an existing custom role. |
| Portal user added without `domainName` | Added to the standard domain context. If the user is a portal-only user without a standard Zoho account, the addition may fail. Always specify `domainName` for portal users. |

### Remove Workspace Users

| Scenario | Behaviour |
|----------|-----------|
| Removing a user who is not in the workspace | The behaviour depends on the portal context. In the standard domain, the user is simply not found and the call may succeed silently or fail depending on the underlying operation. Verify membership using Get Workspace Users first. |
| Removing a Workspace Admin via this API | Allowed. The user is removed from the workspace entirely (loses all access, including admin). To demote without removing, use [Remove Workspace Admins](#8-remove-workspace-admins) instead. |
| Portal user removed without `domainName` | Looked up in the standard domain. If the user was added only via a portal domain, they will not be found in the standard context. Always specify `domainName` when managing portal users. |

### Change Workspace Users Status

| Scenario | Behaviour |
|----------|-----------|
| Workspace Admin calls this API | Fails with error **7301** — "Only Account Admin has the permission." |
| `operation` value other than `"activate"` or `"deactivate"` | Fails with error **8119** before any changes are made. The field is case-sensitive — `"Activate"` or `"ACTIVATE"` are invalid. |
| Activating an already-active user | Succeeds silently (idempotent). |
| Deactivating an already-inactive user | Succeeds silently (idempotent). |
| User's workspace-level data after deactivation | All shares, roles, and permissions are preserved. Restored exactly upon reactivation. |

### Change Workspace Users Role

| Scenario | Behaviour |
|----------|-----------|
| Workspace Admin calls this API | Fails with error **7301** — this API requires Account Admin or Organization Admin. |
| Bulk mode `users` array exceeding 20 entries | Rejected at validation. Split into multiple calls. |
| Same role already assigned | Succeeds silently (idempotent). |
| Demoting a Workspace Admin to User | Allowed. The user loses admin capabilities immediately. Their workspace access continues as a User. |
| Portal user role change without `domainName` | Attempted in the standard domain context. If the user is only in a portal domain, they will not be found. Always specify `domainName` for portal users. |

### Add Workspace Admins

| Scenario | Behaviour |
|----------|-----------|
| User already a Workspace Admin | Silently skipped without error. Only users who are not yet admins are processed. |
| Viewer-role user in `emailIds` | Fails with error **7390** before any changes. All emails in the batch are rejected. To promote a Viewer, first change their org-level role to `"USER"` via the Change User Role API, then add them as Workspace Admin. |
| `inviteMail=true` but email delivery fails | The admin promotion is still committed. Email failures are logged but do not roll back the transaction. |
| Portal admin added without `domainName` | Processed in the standard domain. If the user is a portal-only user, use `domainName` to scope the operation to their portal. |

### Remove Workspace Admins

| Scenario | Behaviour |
|----------|-----------|
| Non-admin email in `emailIds` | Fails with error **8040** for that email. The entire batch is rejected — no demotions are applied. Use Get Workspace Admins to verify current admin membership before calling. |
| Removing the last Workspace Admin | Allowed. The workspace will have no Workspace Admins. Only Account Admin and Org Admin can then manage the workspace. |
| `notifyMail=true` but email delivery fails | The admin removal is still committed. Email failures are logged but do not roll back the transaction. |
| Difference from Remove Workspace Users | Remove Workspace Admins only **demotes** (revokes the admin role) — the user retains workspace access as a regular User. [Remove Workspace Users](#3-remove-workspace-users) **completely removes** the user from the workspace. |

### White Label / Client Portal Domain Behaviour

| Scenario | Behaviour |
|----------|-----------|
| `domainName` omitted | All operations apply to the standard Zoho Analytics domain. |
| `domainName` provided but does not exist | Fails with error **8060** before any changes. |
| `domainName` provided but not owned by the org's Account Admin | Fails with error **8061**. |
| Get Workspace Users — Client Portal Admin | Every user entry includes `domainName`. Standard users show the default analytics domain URL; portal users show their portal's custom domain URL. |
| Get Workspace Admins — Client Portal Admin | Response contains two groups in `workspaceAdmins`: one for the standard domain and one for the portal domain, each with `domainName`. |
| Bulk Add/Change Role with mixed portal domains | Use the `users` array in bulk mode, setting `domainName` per group. Each group is processed in its own portal context. |
| Portal user operations without specifying `domainName` | Operations are attempted in the standard domain. Portal-only users do not exist in the standard domain and will not be found. Always specify `domainName` when the user was added via a portal. |
