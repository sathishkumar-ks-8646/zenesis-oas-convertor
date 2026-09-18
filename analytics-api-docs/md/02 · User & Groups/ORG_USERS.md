# Zoho Analytics V2 REST API — Organisation User Management

These APIs allow Account Admins and Organization Admins to manage the users who belong to a Zoho Analytics organisation — including listing, adding, removing, activating, deactivating, and changing the org-level role of users. A separate API returns the list of users holding the Organization Admin role.

> **Note:** All user management APIs operate at the **organisation level** — they govern a user's membership and role within the org, not their access to individual workspaces. Workspace-level sharing is handled separately by workspace share APIs.

> **White Label / Client Portal Note:** Zoho Analytics supports Client Portal (White Label) deployments where an org may have one or more custom-branded portal domains. When the Account Admin of an org is also a Client Portal Admin, user management operations can be scoped to a specific portal domain using the `domainName` field in CONFIG. Users belonging to a portal domain are managed independently of the main org domain. The `domainName` must be a valid portal domain owned by the Account Admin of the org.

---

## Index

| # | API Name | Method | URL |
|---|----------|--------|-----|
| 1 | [Get Users](#1-get-users) | GET | `/restapi/v2/users` |
| 2 | [Add Users](#2-add-users) | POST | `/restapi/v2/users` |
| 3 | [Remove Users](#3-remove-users) | DELETE | `/restapi/v2/users` |
| 4 | [Activate Users](#4-activate-users) | PUT | `/restapi/v2/users/active` |
| 5 | [Deactivate Users](#5-deactivate-users) | PUT | `/restapi/v2/users/inactive` |
| 6 | [Change User Role](#6-change-user-role) | PUT | `/restapi/v2/users/role` |
| 7 | [Get Org Admins](#7-get-org-admins) | GET | `/restapi/v2/orgadmins` |

---

## 1. Get Users

Returns the list of all users who are members of the specified organisation, along with their current status (active/inactive) and org-level role.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/users` |
| **OAuth Scope** | `ZohoAnalytics.usermanagement.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID whose user list to retrieve. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin of the specified organisation. |

> This API has no CONFIG parameter.

### Sample Requests

**Case 1 — Account Admin listing all org users**

```http
GET /restapi/v2/users HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Org Admin listing users for their org**

```http
GET /restapi/v2/users HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.aaaaaa.bbbbbb
ZANALYTICS-ORGID: 700000654321
```

**Case 3 — Account Admin who is also a Client Portal Admin (users include `domainName` field)**

```http
GET /restapi/v2/users HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

### Sample Responses

**HTTP 200 OK**

**Case 1 — Org with mixed roles (Account Admin perspective)**
```json
{
  "status": "success",
  "summary": "Get users",
  "data": {
    "users": [
      {
        "emailId": "admin@acme.com",
        "status": true,
        "role": "Account Admin"
      },
      {
        "emailId": "orgadmin@acme.com",
        "status": true,
        "role": "Organization Admin"
      },
      {
        "emailId": "analyst@acme.com",
        "status": true,
        "role": "User"
      },
      {
        "emailId": "viewer1@acme.com",
        "status": true,
        "role": "Viewer"
      },
      {
        "emailId": "inactive.user@acme.com",
        "status": false,
        "role": "User"
      }
    ]
  }
}
```

**Case 2 — Org with only a few members (no Org Admins)**
```json
{
  "status": "success",
  "summary": "Get users",
  "data": {
    "users": [
      {
        "emailId": "owner@example.com",
        "status": true,
        "role": "Account Admin"
      },
      {
        "emailId": "user1@example.com",
        "status": true,
        "role": "User"
      },
      {
        "emailId": "viewer@example.com",
        "status": true,
        "role": "Viewer"
      }
    ]
  }
}
```

**Case 3 — Client Portal Admin response (each user entry includes `domainName`)**

When the Account Admin is also a Client Portal Admin, the response includes a `domainName` field for every user indicating which portal domain they belong to. Users added via the standard Zoho Analytics domain show the default analytics domain, while users added via a custom client portal show their portal's domain URL.

```json
{
  "status": "success",
  "summary": "Get users",
  "data": {
    "users": [
      {
        "emailId": "admin@example.com",
        "status": true,
        "role": "Account Admin",
        "domainName": "analytics.zoho.com"
      },
      {
        "emailId": "standard.user@example.com",
        "status": true,
        "role": "User",
        "domainName": "analytics.zoho.com"
      },
      {
        "emailId": "portal.user1@client.com",
        "status": true,
        "role": "User",
        "domainName": "reports.clientbrand.com"
      },
      {
        "emailId": "portal.user2@client.com",
        "status": true,
        "role": "Viewer",
        "domainName": "reports.clientbrand.com"
      },
      {
        "emailId": "portal.user3@partner.com",
        "status": false,
        "role": "User",
        "domainName": "analytics.partnerportal.io"
      }
    ]
  }
}
```

> **`domainName` in response:** Only present when the Account Admin is a Client Portal Admin. The value distinguishes which portal domain each user was added through — allowing the admin to identify users by their portal context. Users added via the standard org (without a custom domain) show the default Zoho Analytics domain.

#### Response Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `data.users` | Array | List of all users in the organisation. |
| `users[].emailId` | String | Email address of the user. |
| `users[].status` | Boolean | `true` if the user is currently active (can log in and use the org). `false` if the user has been deactivated. |
| `users[].role` | String | The user's current org-level role. Possible values: `"Account Admin"`, `"Organization Admin"`, `"User"`, `"Viewer"`. |
| `users[].domainName` | String | *(Present only when the Account Admin is also a Client Portal Admin.)* The portal domain through which this user was added. Users added via the standard org show the default analytics domain URL. Users added via a custom client portal show that portal's domain URL. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Organisation not found. | Verify the `ZANALYTICS-ORGID` header value. |
| 7301 | User is not an Account Admin or Organization Admin of the organisation. | Only Account Admins and Organization Admins can list org users. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.usermanagement.read`. |

---

## 2. Add Users

Adds one or more users to the specified organisation. The invited users receive an email notification. If the users are new to Zoho, they are prompted to create a Zoho account before accepting the invitation.

> **Confirmed account requirement:** The calling user's Zoho account must be confirmed (email-verified) to invoke this API.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/users` |
| **OAuth Scope** | `ZohoAnalytics.usermanagement.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID to add users to. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin of the specified organisation. |

### CONFIG Parameter

CONFIG is **mandatory**. It must be sent as a form-encoded body parameter named `CONFIG`.

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `emailIds` | Array of Strings | **Yes** | — | List of email addresses to invite. Maximum of 1000 email IDs per request. Each entry must be a valid email address. |
| `role` | String | No | `"USER"` | The org-level role to assign to the added users. Allowed values: `"USER"` (standard user), `"ORGADMIN"` (Organization Admin), `"VIEWER"` (read-only Viewer). When omitted, defaults to `"USER"`. **Note:** Organization Admins calling this API can only assign `"USER"` or `"VIEWER"` roles — they cannot assign `"ORGADMIN"`. Only Account Admins can grant the Org Admin role. |
| `domainName` | String | No | `null` | Custom domain name for client portal-based user management. When provided, the user is added in the context of the specified custom portal domain. When omitted, users are added to the standard Zoho Analytics org. **Note:** The `"ORGADMIN"` role cannot be assigned via a custom domain (`domainName`); this combination will fail with error **6089**. |

### Sample Requests

**Case 1 — Add two users with default User role**

```http
POST /restapi/v2/users HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["alice@example.com","bob@example.com"]}
```

**Case 2 — Add a user with Viewer role**

```http
POST /restapi/v2/users HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["viewer@example.com"],"role":"VIEWER"}
```

**Case 3 — Add a user with Org Admin role (Account Admin only)**

```http
POST /restapi/v2/users HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["orgadmin@example.com"],"role":"ORGADMIN"}
```

**Case 4 — Add users to a specific Client Portal domain**

When the Account Admin manages multiple client portals, this scopes the addition to a single portal. Users added this way are associated with that portal domain and appear as portal users in the Get Users response.

```http
POST /restapi/v2/users HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["client.user1@client.com","client.user2@client.com"],"role":"USER","domainName":"reports.clientbrand.com"}
```

**Case 5 — Add a Viewer to a specific Client Portal domain**

```http
POST /restapi/v2/users HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["readonly.client@client.com"],"role":"VIEWER","domainName":"reports.clientbrand.com"}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Add Users returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Organisation not found. | Verify the `ZANALYTICS-ORGID` header value. |
| 7301 | User is not an Account Admin or Organization Admin of the organisation. | Ensure the caller has the required role. |
| 6004 | Adding these users would exceed the organisation's user seat limit under the current plan. | Upgrade the plan to accommodate more users, or remove unused user accounts before adding new ones. |
| 6026 | The current plan does not support adding extra users (free plan restriction). | Upgrade to a paid plan to invite additional users. |
| 6071 | One or more of the specified email addresses is already a member of this organisation. | Remove already-existing email addresses from the `emailIds` list and retry. |
| 6089 | Attempted to assign `"ORGADMIN"` role via a custom domain (`domainName`). Organization Admin role cannot be assigned through a custom portal domain. | Omit `domainName` when assigning the `"ORGADMIN"` role, or use a different role for domain-based additions. |
| 8060 | The specified `domainName` does not exist. | Provide a valid client portal domain name configured for the org. |
| 8061 | The specified `domainName` does not belong to the calling user or the org's Account Admin. | Use a domain name that is administered by the Account Admin of this organisation. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.usermanagement.create`. |

---

## 3. Remove Users

Removes one or more users from the specified organisation. Removed users immediately lose access to all workspaces and views in the org.

> **This is a permanent operation.** Removed users must be re-invited via Add Users to regain access. All workspace-level share permissions for the removed users are also revoked.

> **Confirmed account requirement:** The calling user's Zoho account must be confirmed (email-verified) to invoke this API.

| Attribute | Value |
|-----------|-------|
| **Method** | DELETE |
| **URL** | `/restapi/v2/users` |
| **OAuth Scope** | `ZohoAnalytics.usermanagement.delete` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID to remove users from. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin of the specified organisation. |

### CONFIG Parameter

CONFIG is **mandatory**. It must be sent as a form-encoded body parameter named `CONFIG`.

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `emailIds` | Array of Strings | **Yes** | — | List of email addresses of users to remove. Maximum 1000 per request. All specified email addresses must already be members of the organisation; if any are not, the entire request fails with error **8114**. |
| `domainName` | String | No | `null` | Custom domain name for client portal-based operations. When provided, the removal is scoped to the specified custom portal domain context. When omitted, users are removed from the standard org. |

### Sample Requests

**Case 1 — Remove a single user from the org**

```http
DELETE /restapi/v2/users HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["exemployee@example.com"]}
```

**Case 2 — Remove multiple users at once**

```http
DELETE /restapi/v2/users HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["user1@example.com","user2@example.com","user3@example.com"]}
```

**Case 3 — Remove users from a specific Client Portal domain**

Scopes the removal to a single portal. Only users belonging to the specified portal domain are affected. Users on other portals or the main org are not touched.

```http
DELETE /restapi/v2/users HTTP/1.1
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
| **Success response has no body** | Remove Users returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Organisation not found. | Verify the `ZANALYTICS-ORGID` header value. |
| 7301 | User is not an Account Admin or Organization Admin of the organisation. | Ensure the caller has the required role. |
| 8114 | One or more specified email addresses are not members of this organisation. | Verify all email IDs using the Get Users API before calling Remove Users. |
| 8060 | The specified `domainName` does not exist. | Provide a valid client portal domain name configured for the org. |
| 8061 | The specified `domainName` does not belong to the calling user or the org's Account Admin. | Use a domain name administered by the Account Admin of this organisation. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.usermanagement.delete`. |

---

## 4. Activate Users

Reactivates one or more previously deactivated users in the specified organisation. Once activated, users regain access to the org and all workspaces they were previously shared with.

> **Confirmed account requirement:** The calling user's Zoho account must be confirmed (email-verified) to invoke this API.

| Attribute | Value |
|-----------|-------|
| **Method** | PUT |
| **URL** | `/restapi/v2/users/active` |
| **OAuth Scope** | `ZohoAnalytics.usermanagement.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID where users should be activated. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin of the specified organisation. |

### CONFIG Parameter

CONFIG is **mandatory**. It must be sent as a form-encoded body parameter named `CONFIG`.

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `emailIds` | Array of Strings | **Yes** | — | List of email addresses to activate. Maximum 1000 per request. All specified email addresses must already be members of this organisation; users not in the org will cause the request to fail with error **8114**. |
| `domainName` | String | No | `null` | Custom domain name for client portal-based activation. When provided, the activation is scoped to the custom portal domain context. When omitted, standard org activation applies. |

### Sample Requests

**Case 1 — Reactivate a single user**

```http
PUT /restapi/v2/users/active HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["returning.employee@example.com"]}
```

**Case 2 — Reactivate multiple users**

```http
PUT /restapi/v2/users/active HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["user1@example.com","user2@example.com"]}
```

**Case 3 — Reactivate a user in a specific Client Portal domain**

```http
PUT /restapi/v2/users/active HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["returning.portal.user@client.com"],"domainName":"reports.clientbrand.com"}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Activate Users returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Organisation not found. | Verify the `ZANALYTICS-ORGID` header value. |
| 7301 | User is not an Account Admin or Organization Admin of the organisation. | Ensure the caller has the required role. |
| 6004 | Activating these users would exceed the organisation's user seat limit. | Check current user count via Get Resource Details. Upgrade the plan or remove unused users before reactivating. |
| 8114 | One or more specified email addresses are not members of this organisation. | Verify all email IDs using Get Users before calling this API. |
| 8060 | The specified `domainName` does not exist. | Provide a valid client portal domain name configured for the org. |
| 8061 | The specified `domainName` does not belong to the calling user or the org's Account Admin. | Use a domain name administered by the Account Admin of this organisation. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.usermanagement.update`. |

---

## 5. Deactivate Users

Deactivates one or more users in the specified organisation. Deactivated users cannot log in or access any workspaces in the org. Their data and permissions are retained and can be restored by reactivating them. This is the recommended approach for temporary suspension (e.g., extended leave) rather than permanent removal.

> **Confirmed account requirement:** The calling user's Zoho account must be confirmed (email-verified) to invoke this API.

| Attribute | Value |
|-----------|-------|
| **Method** | PUT |
| **URL** | `/restapi/v2/users/inactive` |
| **OAuth Scope** | `ZohoAnalytics.usermanagement.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID where users should be deactivated. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin of the specified organisation. |

### CONFIG Parameter

CONFIG is **mandatory**. It must be sent as a form-encoded body parameter named `CONFIG`.

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `emailIds` | Array of Strings | **Yes** | — | List of email addresses to deactivate. Maximum 1000 per request. All specified email addresses must already be members of this organisation; non-members cause the request to fail with error **8114**. |
| `domainName` | String | No | `null` | Custom domain name for client portal-based deactivation. When provided, the deactivation is scoped to the custom portal domain context. When omitted, standard org deactivation applies. |

### Sample Requests

**Case 1 — Deactivate a user on leave**

```http
PUT /restapi/v2/users/inactive HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["on.leave@example.com"]}
```

**Case 2 — Deactivate multiple users**

```http
PUT /restapi/v2/users/inactive HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["contractor1@example.com","contractor2@example.com"]}
```

**Case 3 — Deactivate a user in a specific Client Portal domain**

Temporarily suspends a portal user's access. Their portal-specific shares and permissions are preserved and restored upon reactivation.

```http
PUT /restapi/v2/users/inactive HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["suspended.portal.user@client.com"],"domainName":"reports.clientbrand.com"}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Deactivate Users returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Organisation not found. | Verify the `ZANALYTICS-ORGID` header value. |
| 7301 | User is not an Account Admin or Organization Admin of the organisation. | Ensure the caller has the required role. |
| 8114 | One or more specified email addresses are not members of this organisation. | Verify all email IDs using Get Users before calling this API. |
| 8060 | The specified `domainName` does not exist. | Provide a valid client portal domain name configured for the org. |
| 8061 | The specified `domainName` does not belong to the calling user or the org's Account Admin. | Use a domain name administered by the Account Admin of this organisation. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.usermanagement.update`. |

---

## 6. Change User Role

Changes the org-level role of one or more users in the specified organisation. Role changes take effect immediately — the user's access permissions across all workspaces adjust to reflect the new role.

> **Confirmed account requirement:** The calling user's Zoho account must be confirmed (email-verified) to invoke this API.

| Attribute | Value |
|-----------|-------|
| **Method** | PUT |
| **URL** | `/restapi/v2/users/role` |
| **OAuth Scope** | `ZohoAnalytics.usermanagement.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID where the role change should apply. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin of the specified organisation. |

### CONFIG Parameter

CONFIG is **mandatory**. It must be sent as a form-encoded body parameter named `CONFIG`.

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `emailIds` | Array of Strings | **Yes** | — | List of email addresses whose role should be changed. Maximum 1000 per request. All specified email addresses must already be members of this organisation; non-members cause the request to fail with error **8114**. The same target role is applied to all users in the list. |
| `role` | String | **Yes** | — | The new org-level role to assign to all specified users. Allowed values: `"USER"` (standard user), `"ORGADMIN"` (Organization Admin), `"VIEWER"` (read-only Viewer). **Note:** Organization Admins calling this API can only assign `"USER"` or `"VIEWER"` — they cannot promote users to `"ORGADMIN"`. Only Account Admins can assign the `"ORGADMIN"` role. |
| `domainName` | String | No | `null` | Custom domain name for client portal-based role changes. When omitted, the standard org context is used. When provided, the role change applies within the specified custom portal domain. **Note:** The `"ORGADMIN"` role cannot be assigned via a custom domain; this combination will fail with error **6089**. |

### Role Values Reference

| `role` Value | Display Name | Description |
|-------------|--------------|-------------|
| `"USER"` | User | Standard user. Can own and manage workspaces they create, and access workspaces shared with them. |
| `"ORGADMIN"` | Organization Admin | Can manage users and workspaces across the org. Cannot exceed Account Admin privileges. Account Admin only. |
| `"VIEWER"` | Viewer | Read-only access. Can view reports and dashboards shared with them but cannot create or modify data. |

### Sample Requests

**Case 1 — Promote a user to Organization Admin**

```http
PUT /restapi/v2/users/role HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["analyst@example.com"],"role":"ORGADMIN"}
```

**Case 2 — Downgrade multiple users to Viewer role**

```http
PUT /restapi/v2/users/role HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["contractor1@example.com","contractor2@example.com"],"role":"VIEWER"}
```

**Case 3 — Reset an Org Admin back to standard User**

```http
PUT /restapi/v2/users/role HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["formeradmin@example.com"],"role":"USER"}
```

**Case 4 — Change role of a user within a specific Client Portal domain**

Role changes within a portal domain are scoped to that portal. The user's role on the main org or other portals is unaffected.

```http
PUT /restapi/v2/users/role HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["portal.user@client.com"],"role":"VIEWER","domainName":"reports.clientbrand.com"}
```

> **Note:** `"ORGADMIN"` cannot be assigned via `domainName`. This combination always fails with error **6089** regardless of the caller's role.

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Change User Role returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Organisation not found. | Verify the `ZANALYTICS-ORGID` header value. |
| 7301 | User is not an Account Admin or Organization Admin. | Ensure the caller has the required org-level role. |
| 6089 | Attempted to assign `"ORGADMIN"` role via `domainName` (custom domain). | Omit `domainName` when assigning the Org Admin role. |
| 8114 | One or more specified email addresses are not members of this organisation. | Verify all email IDs using Get Users before calling this API. |
| 8060 | The specified `domainName` does not exist. | Provide a valid client portal domain name configured for the org. |
| 8061 | The specified `domainName` does not belong to the calling user or the org's Account Admin. | Use a domain name administered by the Account Admin of this organisation. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.usermanagement.update`. |

---

## 7. Get Org Admins

Returns the list of email addresses of users who currently hold the **Organization Admin** role in the specified organisation. This is a read-only API accessible only to the Account Admin of the organisation.

> **Access restriction:** Unlike the other user management APIs which are accessible to both Account Admin and Organization Admin, this API is **restricted to Account Admin only**. Organization Admins cannot call this API.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/orgadmins` |
| **OAuth Scope** | `ZohoAnalytics.share.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID whose Org Admins to retrieve. |
| **Permission Required** | The authenticated user must be the **Account Admin** of the specified organisation. |

> This API has no CONFIG parameter.

### Sample Requests

**Case 1 — Account Admin listing all Org Admins**

```http
GET /restapi/v2/orgadmins HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

### Sample Responses

**HTTP 200 OK**

**Case 1 — Organisation with one Org Admin**
```json
{
  "status": "success",
  "summary": "Get org admins",
  "data": {
    "orgAdmins": [
      "orgadmin@example.com"
    ]
  }
}
```

**Case 2 — Organisation with multiple Org Admins**
```json
{
  "status": "success",
  "summary": "Get org admins",
  "data": {
    "orgAdmins": [
      "orgadmin1@example.com",
      "orgadmin2@example.com",
      "regional.admin@example.com"
    ]
  }
}
```

**Case 3 — Organisation with no Org Admins assigned**
```json
{
  "status": "success",
  "summary": "Get org admins",
  "data": {
    "orgAdmins": []
  }
}
```

#### Response Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `data.orgAdmins` | Array of Strings | Email addresses of all users who currently hold the Organization Admin role in the org. Returns an empty array if no Org Admins are currently assigned. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Organisation not found. | Verify the `ZANALYTICS-ORGID` header value. |
| 7301 | The calling user is not the Account Admin of the organisation. | This API is strictly restricted to the Account Admin. Organization Admins and other roles cannot call this endpoint. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.share.read`. |

---

## Appendix A – Common HTTP Headers

| Header | Value | Required | Notes |
|--------|-------|----------|-------|
| `Authorization` | `Zoho-oauthtoken <oauth-token>` | **Mandatory** | OAuth 2.0 access token of the calling user. |
| `ZANALYTICS-ORGID` | Organisation ID | **Mandatory** for all APIs | Use the `orgId` value from the Get Org List response. |
| `Content-Type` | `application/x-www-form-urlencoded` | Required for POST/PUT/DELETE | Add Users, Remove Users, Activate Users, Deactivate Users, and Change User Role send CONFIG as a form-encoded body parameter. Get Users and Get Org Admins have no body. |

---

## Appendix B – OAuth Scope Summary

| API | Method | Scope |
|-----|--------|-------|
| Get Users | GET | `ZohoAnalytics.usermanagement.read` |
| Add Users | POST | `ZohoAnalytics.usermanagement.create` |
| Remove Users | DELETE | `ZohoAnalytics.usermanagement.delete` |
| Activate Users | PUT | `ZohoAnalytics.usermanagement.update` |
| Deactivate Users | PUT | `ZohoAnalytics.usermanagement.update` |
| Change User Role | PUT | `ZohoAnalytics.usermanagement.update` |
| Get Org Admins | GET | `ZohoAnalytics.share.read` |

---

## Appendix C – Operational Notes and Failure Cases

### Org-Level vs Workspace-Level Role

| Concept | Description |
|---------|-------------|
| **Org-level role** (`role` in Get/Add/Change User APIs) | Determines what the user can do across the entire organisation — create workspaces, manage users, etc. Values: `Account Admin`, `Organization Admin`, `User`, `Viewer`. |
| **Workspace-level role** | Determines what the user can do within a specific workspace — read, design, share, etc. Managed via workspace share APIs, not these user management APIs. |
| **Relationship** | A user's org-level role is a ceiling on their capabilities, but workspace-level permissions can be more granular. A `User` at org level can be a `Workspace Admin` for a specific workspace they own. A `Viewer` at org level can only ever have read access regardless of workspace-level share. |

### Get Users

| Scenario | Behaviour |
|----------|-----------|
| Org has only one user (the Account Admin) | Returns a single entry with `role: "Account Admin"`. |
| User is deactivated | Appears in the list with `status: false`. Deactivated users are included in the result — they are not removed from the list. |
| Organization Admin calls Get Users | Allowed — Org Admins can view the full user list. |

### Add Users

| Scenario | Behaviour |
|----------|-----------|
| Adding a user who already exists in the org | Fails with error **6071** for that email. The entire batch fails — no users from the request are added. |
| `role` omitted | Defaults to `"USER"`. The invited user joins as a standard user. |
| Org Admin adds a user with `role="ORGADMIN"` | Fails — Organization Admins cannot grant the Org Admin role. Only Account Admins can assign `"ORGADMIN"`. |
| Adding more users than the plan's seat limit | Fails with error **6004** before any users are added. The entire batch is rejected. Check current usage with Get Resource Details. |
| Adding a user on a Free plan | Free plans do not support extra users beyond the included allocation. Fails with error **6026**. |
| `domainName` + `role="ORGADMIN"` combination | Always fails with error **6089** regardless of the caller's role. Org Admin role is not assignable via custom domain context. |
| Invited user has not yet accepted | The invitation is pending. The user is not listed in Get Users until they accept and join. |

### Remove Users

| Scenario | Behaviour |
|----------|-----------|
| Attempting to remove the Account Admin | The Account Admin (org owner) cannot be removed by this API. The request will fail. Transfer ownership first if removal is needed. |
| Removing a user who is not in the org | Fails with error **8114** for the entire batch. Use Get Users to validate membership before calling this API. |
| Removing a user who owns workspaces | The user's workspaces are not automatically deleted. The workspaces remain but ownership may need to be transferred separately. Workspace contents remain intact after user removal. |
| Partial batch with mix of valid and invalid emails | The request fails as a whole on the first non-member email. No users are removed if any email in the batch is invalid. |

### Activate Users

| Scenario | Behaviour |
|----------|-----------|
| Activating an already-active user | The request succeeds silently (idempotent). No error is raised for already-active users. |
| User seat limit reached at reactivation time | Fails with error **6004**. A user who was previously deactivated still occupies a seat in terms of plan limits when reactivated. Remove unused users or upgrade the plan first. |
| Activating a user not in the org | Fails with error **8114**. The user must be a member of the org (even if currently deactivated) to be reactivated. |

### Deactivate Users

| Scenario | Behaviour |
|----------|-----------|
| Deactivating an already-inactive user | The request succeeds silently (idempotent). No error is raised for already-deactivated users. |
| Deactivated user's workspace shares | All workspace shares are preserved but the user cannot access them while deactivated. Upon reactivation, all prior shares are restored. |
| Attempting to deactivate the Account Admin | Not permitted. The org owner (Account Admin) cannot be deactivated through this API. |
| Deactivate vs Remove | Deactivate is reversible — user data, shares, and role are preserved. Remove is permanent — shares are revoked and the user must be re-invited. Use Deactivate for temporary suspension. |

### Change User Role

| Scenario | Behaviour |
|----------|-----------|
| Promoting a `"USER"` to `"ORGADMIN"` by an Org Admin | Not allowed — Org Admins cannot grant the Org Admin role. Fails with a permission error (7301). Only Account Admins can do this. |
| Demoting an `"ORGADMIN"` back to `"USER"` | Allowed by Account Admin. The former Org Admin immediately loses org-wide management capabilities. Their workspace-level permissions (if any) are unaffected. |
| Changing role of a deactivated user | Allowed. The role change takes effect. When the user is reactivated, they will have the new role. |
| Changing role of a user not in the org | Fails with error **8114**. Verify membership with Get Users first. |
| Setting `role="VIEWER"` for a user who owns workspaces | The user becomes read-only at the org level. However, workspaces they own are not automatically transferred. They may still have Workspace Admin access on those specific workspaces. |
| Applying the same role the user already has | The request succeeds silently (idempotent). No error is raised. |

### Get Org Admins

| Scenario | Behaviour |
|----------|-----------|
| No Organization Admins have been assigned | Returns HTTP 200 with an empty `orgAdmins` array. All admin operations are handled by the Account Admin only. |
| Org Admin calls Get Org Admins | Fails with error **7301** — this endpoint is restricted to the Account Admin only. Unlike the other user management APIs that allow Org Admins, this one requires the Account Admin. |
| Relationship to Add/Change User Role APIs | Org Admins are users whose `role` in the Change User Role API was set to `"ORGADMIN"`. This API is a convenience endpoint that filters for only that role — equivalent to filtering Get Users results where `role = "Organization Admin"`. |

### White Label / Client Portal Domain Behaviour

| Scenario | Behaviour |
|----------|-----------|
| `domainName` omitted in all write APIs | Operation applies to the standard Zoho Analytics domain (default org context). Users are managed as regular org members. |
| `domainName` provided but the domain does not exist | All write APIs (Add, Remove, Activate, Deactivate, Change Role) fail with error **8060** before any change is made. |
| `domainName` provided but belongs to a different Account Admin | Fails with error **8061**. Only domains owned by the Account Admin of the specified org are valid. An Org Admin providing a `domainName` that they do not administer also triggers 8061. |
| Caller is not a Client Portal Admin and provides `domainName` | Fails with error **8061**. The `domainName` parameter is only meaningful when the Account Admin of the org has Client Portal Admin status. |
| `role="ORGADMIN"` + `domainName` in Add Users or Change User Role | Always fails with error **6089**. Organization Admin is an org-level concept and cannot be assigned to a portal-scoped user. Use `role="USER"` or `role="VIEWER"` for portal domain operations. |
| Get Users when Account Admin is a Client Portal Admin | Every user entry in the response includes a `domainName` field. Users added via the standard Zoho Analytics org show the default analytics domain URL. Users added via a specific client portal show that portal's custom domain URL. This allows the admin to distinguish portal membership at a glance. |
| Get Users when Account Admin is NOT a Client Portal Admin | The `domainName` field is absent from all user entries in the response. Only `emailId`, `status`, and `role` are returned. |
| A user added via a portal domain — can they access the main org? | No. Portal-domain users are scoped to their portal. They access analytics only through the portal's branded URL. They do not appear as standard org members on `analytics.zoho.com`. |
| Remove a portal user without specifying `domainName` | The user is looked up in the default (standard) org context. If they were added via a portal domain only and do not exist in the standard org, the request fails with error **8114**. Always specify `domainName` when managing portal-scoped users. |
| Multiple client portals under the same org | Each portal domain is managed independently. Specify the target `domainName` in each API call. A user can be a member of multiple portals simultaneously — their membership in one portal is unaffected by operations on another. |
