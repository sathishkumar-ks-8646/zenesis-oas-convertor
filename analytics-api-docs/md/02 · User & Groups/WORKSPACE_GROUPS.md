# Zoho Analytics V2 REST API — Workspace Groups

Workspace Groups are named collections of users within a specific workspace. Groups allow you to manage view-level sharing permissions in bulk — instead of granting access to individual users, you can share views with a group and all members receive that access simultaneously. Managing group membership is the only way to batch-update sharing permissions for multiple users at once.

> **Workspace-Level Scope:** Groups are scoped to a single workspace. A group created in one workspace is not accessible in another workspace. Members must already be users of the workspace (or the specified portal domain) to be added to a group.

> **White Label / Client Portal:** When the Account Admin is a Client Portal Admin, groups can be scoped to a specific portal domain using the `domainName` field during creation. Group list and detail responses include `domainName` per group in portal contexts. Members are automatically matched to their portal domain when `domainName` is set on the group.

---

## Index

| # | API Name | Method | URL |
|---|----------|--------|-----|
| 1 | [Get Group List](#1-get-group-list) | GET | `/restapi/v2/workspaces/<workspace-id>/groups` |
| 2 | [Create Group](#2-create-group) | POST | `/restapi/v2/workspaces/<workspace-id>/groups` |
| 3 | [Rename Group](#3-rename-group) | PUT | `/restapi/v2/workspaces/<workspace-id>/groups/<group-id>` |
| 4 | [Add Group Members](#4-add-group-members) | POST | `/restapi/v2/workspaces/<workspace-id>/groups/<group-id>/members` |
| 5 | [Remove Group Members](#5-remove-group-members) | DELETE | `/restapi/v2/workspaces/<workspace-id>/groups/<group-id>/members` |
| 6 | [Delete Group](#6-delete-group) | DELETE | `/restapi/v2/workspaces/<workspace-id>/groups/<group-id>` |
| 7 | [Get Group Details](#7-get-group-details) | GET | `/restapi/v2/workspaces/<workspace-id>/groups/<group-id>` |

---

## 1. Get Group List

Returns all groups defined in the specified workspace, along with their descriptions and current member lists.

When the Account Admin is a Client Portal Admin, each group entry includes a `domainName` field indicating which portal domain the group was created for. Custom domain users (users visiting via a portal URL) see only the groups that belong to their portal domain.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/groups` |
| **OAuth Scope** | `ZohoAnalytics.share.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace. Account Admins and Organization Admins also have access. |

> This API has no CONFIG parameter.

### Sample Requests

**Case 1 — Account Admin listing all groups in a workspace**

```http
GET /restapi/v2/workspaces/466206000000071000/groups HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Workspace Admin listing groups in their workspace**

```http
GET /restapi/v2/workspaces/466206000000071000/groups HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.aaaaaa.bbbbbb
ZANALYTICS-ORGID: 700000123456
```

**Case 3 — Client Portal Admin listing groups (includes portal domain context)**

```http
GET /restapi/v2/workspaces/466206000000071000/groups HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

### Sample Responses

**HTTP 200 OK**

**Case 1 — Standard org (no Client Portal) — multiple groups with different membership**
```json
{
  "status": "success",
  "summary": "Get groups",
  "data": {
    "groups": [
      {
        "groupId": "320862000000276835",
        "groupName": "Finance Team",
        "groupDesc": "Finance department workspace users",
        "groupMembers": ["alice@acme.com"]
      },
      {
        "groupId": "320862000000286056",
        "groupName": "Analytics Team",
        "groupDesc": "",
        "groupMembers": ["bob@acme.com", "carol@acme.com", "dave@acme.com"]
      }
    ]
  }
}
```

**Case 2 — Workspace with one empty group (no members yet)**
```json
{
  "status": "success",
  "summary": "Get groups",
  "data": {
    "groups": [
      {
        "groupId": "320862000000310001",
        "groupName": "Onboarding",
        "groupDesc": "New joiners pending workspace access",
        "groupMembers": []
      }
    ]
  }
}
```

**Case 3 — Client Portal Admin response (each group includes `domainName`)**

When the Account Admin is a Client Portal Admin, every group entry includes `domainName` so the admin can distinguish standard org groups from portal-domain groups.

```json
{
  "status": "success",
  "summary": "Get groups",
  "data": {
    "groups": [
      {
        "groupId": "38190000004182920",
        "groupName": "Portal Analysts",
        "groupDesc": "",
        "domainName": "reports.clientbrand.com",
        "groupMembers": ["portal.user1@client.com", "portal.user2@client.com"]
      },
      {
        "groupId": "38190000004189049",
        "groupName": "Internal Team",
        "groupDesc": "",
        "domainName": "analytics.zoho.com",
        "groupMembers": ["analyst@acme.com"]
      }
    ]
  }
}
```

#### Response Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `data.groups` | Array | All groups defined in this workspace. An empty array when no groups exist. |
| `groups[].groupId` | String | Unique identifier for the group. Use this value as `<group-id>` in all group-specific API calls. |
| `groups[].groupName` | String | Display name of the group. Unique within the workspace. |
| `groups[].groupDesc` | String | Optional description. Empty string `""` when not set. |
| `groups[].groupMembers` | Array of Strings | Email addresses of all current group members. Empty array when the group has no members. |
| `groups[].domainName` | String | *(Present only when Account Admin is a Client Portal Admin.)* The portal domain this group was created for. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Filtered by portal domain for custom domain users** | Users accessing via a portal URL only see groups that belong to their portal domain. The full group list (across all domains) is only visible to Workspace Admins and Client Portal Admins. |
| **`domainName` in response** | Only included in each group object when the Account Admin is a Client Portal Admin. Standard org responses do not include `domainName`. |
| **Dependency for other APIs** | The `groupId` values returned here are required in the URL (`<group-id>`) for Rename Group, Add Group Members, Remove Group Members, Delete Group, and Get Group Details. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify `<workspace-id>`. |
| 7301 | User is not a Workspace Admin, Account Admin, or Organization Admin of the workspace. | Ensure the caller has at least Workspace Admin access. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.share.read`. |

---

## 2. Create Group

Creates a new group in the specified workspace and optionally adds initial members to it. The group name must be unique within the workspace. An optional invitation email can be sent to the initial members at creation time.

> **Confirmed account requirement:** The calling user's Zoho account must be confirmed (email-verified) to invoke this API.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/groups` |
| **OAuth Scope** | `ZohoAnalytics.share.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace. Account Admins and Organization Admins also have access. |

### CONFIG Parameter

CONFIG is **mandatory**. It must be sent as a form-encoded body parameter named `CONFIG`.

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `groupName` | String | **Yes** | — | Display name for the new group. Must be unique within the workspace. Empty or blank values are rejected. |
| `emailIds` | Array of Strings | **Yes** | — | Email addresses of the initial group members. Min 1, max 1000 entries. Members must already be workspace users (or members of the specified portal domain). |
| `groupDesc` | String | No | `""` | A short description of the group's purpose. Max 200 characters. When omitted, defaults to an empty string. |
| `domainName` | String | No | `null` | Client portal domain for portal-scoped groups. When provided, the group is associated with the specified portal domain. All `emailIds` must belong to users within that portal domain. When omitted, the group is created in the standard Zoho Analytics domain context. |
| `inviteMail` | Boolean | No | `false` | When `false` (default): no email is sent to the initial members. When `true`: an invitation email is sent to all newly added group members informing them of their group access. |
| `mailSubject` | String | No | `""` | Custom subject line for the invitation email. Only relevant when `inviteMail` is `true`. Max 500 characters. |
| `mailMessage` | String | No | `""` | Custom message body for the invitation email. Supports basic HTML. Only relevant when `inviteMail` is `true`. Max 5000 characters. |

### Sample Requests

**Case 1 — Create a group with initial members and no invitation email**

```http
POST /restapi/v2/workspaces/466206000000071000/groups HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"groupName":"Finance Team","emailIds":["alice@acme.com","bob@acme.com"]}
```

**Case 2 — Create a group with a description and send an invitation email**

```http
POST /restapi/v2/workspaces/466206000000071000/groups HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"groupName":"Analytics Team","groupDesc":"Cross-functional analytics stakeholders","emailIds":["carol@acme.com","dave@acme.com"],"inviteMail":true,"mailSubject":"You've been added to the Analytics Team group","mailMessage":"Hi,<br>You now have access to the Analytics workspace group. Please log in to view your shared reports."}
```

**Case 3 — Client Portal: create a group scoped to a portal domain**

```http
POST /restapi/v2/workspaces/466206000000071000/groups HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"groupName":"Portal Analysts","emailIds":["portal.user1@client.com","portal.user2@client.com"],"domainName":"reports.clientbrand.com","inviteMail":true}
```

### Sample Responses

**HTTP 200 OK** — Group created successfully.

```json
{
  "status": "success",
  "summary": "Create group",
  "data": {
    "groupId": "320862000000295001"
  }
}
```

#### Response Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `data.groupId` | String | Unique identifier of the newly created group. Use this as `<group-id>` in subsequent group API calls. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **`domainName` is set at creation only** | Once a group is created with a `domainName`, that portal domain association cannot be changed. To change the domain, delete the group and recreate it. |
| **Omitting `domainName`** | Creates an org-wide group. All workspace users (regardless of portal domain) can be added as members. |
| **`emailIds` members at creation** | These users are added as initial group members. The same email appearing multiple times is handled as a single addition. |
| **`inviteMail=true` does not block creation** | If email delivery fails, the group and its members are still created. Email failures do not roll back the operation. |
| **Response** | Only the new `groupId` is returned. Use Get Group Details to retrieve the full group record. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify `<workspace-id>`. |
| 7282 | A group with the same name already exists in this workspace. Group names must be unique per workspace. | Choose a different name for the group. |
| 7301 | User is not a Workspace Admin, Account Admin, or Organization Admin of the workspace. | Ensure the caller has at least Workspace Admin access. |
| 8060 | The specified `domainName` does not exist. | Provide a valid client portal domain name configured for the org. |
| 8061 | The specified `domainName` does not belong to the org's Account Admin. | Use a domain administered by the Account Admin of this organisation. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.share.create`. |

---

## 3. Rename Group

Updates the name and/or description of an existing group in the specified workspace. Both fields are replaced atomically — if `groupDesc` is omitted, the description is reset to an empty string.

| Attribute | Value |
|-----------|-------|
| **Method** | PUT |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/groups/<group-id>` |
| **OAuth Scope** | `ZohoAnalytics.share.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace. Account Admins and Organization Admins also have access. |

### CONFIG Parameter

CONFIG is **mandatory**. It must be sent as a form-encoded body parameter named `CONFIG`.

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `groupName` | String | **Yes** | — | New display name for the group. Must be unique within the workspace. Cannot be empty or blank. |
| `groupDesc` | String | No | `""` | New description for the group. Max 200 characters. When omitted, the description is reset to an empty string — the previous description is **not** preserved. Always pass the existing description if you only intend to update the name. |

### Sample Requests

**Case 1 — Rename a group (description not provided → reset to empty)**

```http
PUT /restapi/v2/workspaces/466206000000071000/groups/320862000000276835 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"groupName":"Finance & Accounts Team"}
```

**Case 2 — Rename and update description simultaneously**

```http
PUT /restapi/v2/workspaces/466206000000071000/groups/320862000000276835 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"groupName":"Finance & Accounts Team","groupDesc":"Finance, accounts payable, and treasury users"}
```

**Case 3 — Update only description (keep existing name, pass it explicitly)**

```http
PUT /restapi/v2/workspaces/466206000000071000/groups/320862000000276835 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"groupName":"Finance Team","groupDesc":"Updated: Finance and procurement access group"}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Rename Group returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |
| **`groupDesc` is RESET on omission** | If `groupDesc` is not included in the request, the group's existing description is permanently overwritten with an empty string. Always include the current `groupDesc` value (read from Get Group Details) to preserve it. |
| **Renaming to the same name** | Succeeds without error (idempotent for the name). |
| **Dependency** | `<group-id>` in the URL must be obtained from Get Group List. The current `groupDesc` should also be read from Get Group Details before calling this API if you want to preserve the description. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify `<workspace-id>`. |
| 7282 | The new group name is already used by another group in this workspace. | Choose a name not already in use. |
| 7301 | User is not a Workspace Admin, Account Admin, or Organization Admin of the workspace. | Ensure the caller has at least Workspace Admin access. |
| 7338 | The specified `<group-id>` does not belong to this workspace. | Verify the group ID belongs to the correct workspace using Get Group List. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.share.update`. |

---

## 4. Add Group Members

Adds one or more users to an existing group. Users must already have access to the workspace (or the portal domain the group belongs to) before they can be added as group members. An optional invitation email can be sent to the newly added members.

> **Note:** There is no explicit `domainName` field for this API. The group itself carries its domain association (set at creation). The domain context is automatically resolved from the group's identity. Members to be added must be users within the domain that the group belongs to.

> **Confirmed account requirement:** The calling user's Zoho account must be confirmed (email-verified) to invoke this API.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/groups/<group-id>/members` |
| **OAuth Scope** | `ZohoAnalytics.share.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace. Account Admins and Organization Admins also have access. |

### CONFIG Parameter

CONFIG is **mandatory**. It must be sent as a form-encoded body parameter named `CONFIG`.

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `emailIds` | Array of Strings | **Yes** | — | Email addresses to add to the group. Min 1, max 1000 entries. All users must be existing workspace members within the group's domain context. |
| `inviteMail` | Boolean | No | `false` | When `false` (default): no email is sent. When `true`: an invitation email is sent to all newly added members informing them of their group access. If a user was already a group member, no email is sent for that user — only genuinely new additions receive the email. |
| `mailSubject` | String | No | `""` | Custom subject line for the invitation email. Only relevant when `inviteMail` is `true`. Max 500 characters. |
| `mailMessage` | String | No | `""` | Custom message body for the invitation email. Supports basic HTML. Only relevant when `inviteMail` is `true`. Max 5000 characters. |

### Sample Requests

**Case 1 — Add members silently**

```http
POST /restapi/v2/workspaces/466206000000071000/groups/320862000000276835/members HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["eve@acme.com","frank@acme.com"]}
```

**Case 2 — Add a member and send an invitation email with custom message**

```http
POST /restapi/v2/workspaces/466206000000071000/groups/320862000000276835/members HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["grace@acme.com"],"inviteMail":true,"mailSubject":"You've been added to Finance Team","mailMessage":"Hi Grace,<br>You now have group access to Finance Team reports. Please log in to view them."}
```

**Case 3 — Client Portal: add a portal user to a portal-domain group**

For groups scoped to a portal domain, add members who belong to that same portal domain. The domain association is carried by the group itself — no `domainName` field is needed in the request.

```http
POST /restapi/v2/workspaces/466206000000071000/groups/38190000004182920/members HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["portal.user3@client.com"],"inviteMail":true}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Add Group Members returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |
| **Members must already be workspace users** | Users must have been added to the workspace (via Add Workspace Users) before they can be added to a group. |
| **Adding an existing member is silently skipped** | If a user is already in the group, they are not added again and no error is raised. Only genuinely new members receive an invitation email when `inviteMail=true`. |
| **No `domainName` in this request** | The portal domain context is inherited from the group itself (set at creation). Do not include `domainName` when adding members. |
| **`inviteMail=true` does not block the add** | Email delivery failures do not roll back the member addition. |
| **Dependency** | `<group-id>` → Get Group List. User email addresses → Get Workspace Users. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify `<workspace-id>`. |
| 7301 | User is not a Workspace Admin, Account Admin, or Organization Admin of the workspace. | Ensure the caller has at least Workspace Admin access. |
| 7338 | The specified `<group-id>` does not belong to this workspace. | Verify the group ID using Get Group List. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.share.create`. |

---

## 5. Remove Group Members

Removes one or more members from a group. Removed users lose any view-level access that was granted exclusively through group membership in this group. Their other access (workspace membership, direct sharing on views, membership in other groups) is unaffected.

> **Confirmed account requirement:** The calling user's Zoho account must be confirmed (email-verified) to invoke this API.

| Attribute | Value |
|-----------|-------|
| **Method** | DELETE |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/groups/<group-id>/members` |
| **OAuth Scope** | `ZohoAnalytics.share.delete` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace. Account Admins and Organization Admins also have access. |

### CONFIG Parameter

CONFIG is **mandatory**. It must be sent as a form-encoded body parameter named `CONFIG`.

| Field | Type | Mandatory | Default | Description |
|-------|------|-----------|---------|-------------|
| `emailIds` | Array of Strings | **Yes** | — | Email addresses of the members to remove from the group. Min 1, max 1000 entries. |
| `notifyUser` | Boolean | No | `false` | When `false` (default): removal is silent — no email is sent to the removed members. When `true`: a notification email is sent to each removed member informing them that their group access has been revoked. |

### Sample Requests

**Case 1 — Remove a member silently**

```http
DELETE /restapi/v2/workspaces/466206000000071000/groups/320862000000276835/members HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["alice@acme.com"]}
```

**Case 2 — Remove multiple members and send a notification email**

```http
DELETE /restapi/v2/workspaces/466206000000071000/groups/320862000000276835/members HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["alice@acme.com","bob@acme.com"],"notifyUser":true}
```

**Case 3 — Client Portal: remove a portal user from a portal-domain group**

```http
DELETE /restapi/v2/workspaces/466206000000071000/groups/38190000004182920/members HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"emailIds":["portal.user2@client.com"]}
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Remove Group Members returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |
| **Removing a non-member is silently ignored** | If an email address is not a member of the group, the operation proceeds without error for the remaining valid members. |
| **Impact on view sharing** | If the removed user's only access to a shared view was through this group, they lose that access immediately. Access via direct sharing or other groups is not affected. |
| **`notifyUser=true` does not block removal** | Email delivery failures do not roll back the member removal. |
| **No `domainName` in this request** | Portal domain context is inherited from the group. |
| **Dependency** | `<group-id>` → Get Group List. Member emails → Get Group Details. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify `<workspace-id>`. |
| 7301 | User is not a Workspace Admin, Account Admin, or Organization Admin of the workspace. | Ensure the caller has at least Workspace Admin access. |
| 7338 | The specified `<group-id>` does not belong to this workspace. | Verify the group ID using Get Group List. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.share.delete`. |

---

## 6. Delete Group

Permanently deletes a group from the workspace. This operation is irreversible. All view-level access grants that were based on this group's membership are immediately revoked for all former members (unless those members have access through other means — direct sharing, other groups, or workspace-level roles).

> **Confirmed account requirement:** The calling user's Zoho account must be confirmed (email-verified) to invoke this API.

| Attribute | Value |
|-----------|-------|
| **Method** | DELETE |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/groups/<group-id>` |
| **OAuth Scope** | `ZohoAnalytics.share.delete` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace. Account Admins and Organization Admins also have access. |

> This API has no CONFIG parameter.

### Sample Requests

**Case 1 — Delete a group**

```http
DELETE /restapi/v2/workspaces/466206000000071000/groups/320862000000276835 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Client Portal Admin deleting a portal-domain group**

```http
DELETE /restapi/v2/workspaces/466206000000071000/groups/38190000004182920 HTTP/1.1
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
| **Success response has no body** | Delete Group returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |
| **Cascading view access revocation** | When a group is deleted, all view shares granted exclusively via that group are revoked for every affected member simultaneously. Users with direct sharing or membership in other groups sharing the same views are unaffected. |
| **No CONFIG parameter** | The group is identified solely by `<group-id>` in the URL. No request body is needed. |
| **Permanent deletion** | There is no soft-delete or trash mechanism. Once deleted, the group and its sharing configuration cannot be restored. |
| **Dependency** | `<group-id>` → Get Group List. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify `<workspace-id>`. |
| 7301 | User is not a Workspace Admin, Account Admin, or Organization Admin of the workspace. | Ensure the caller has at least Workspace Admin access. |
| 7338 | The specified `<group-id>` does not belong to this workspace. | Verify the group ID using Get Group List. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.share.delete`. |

---

## 7. Get Group Details

Returns the full details of a single group — its name, description, and complete member list.

For Client Portal Admins or users visiting via a custom portal domain URL, the response also includes `domainName` indicating which portal domain the group belongs to.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/groups/<group-id>` |
| **OAuth Scope** | `ZohoAnalytics.share.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin of the specified workspace. Account Admins and Organization Admins also have access. |

> This API has no CONFIG parameter.

### Sample Requests

**Case 1 — Get details of a specific group**

```http
GET /restapi/v2/workspaces/466206000000071000/groups/320862000000286056 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Client Portal Admin fetching details of a portal-domain group**

```http
GET /restapi/v2/workspaces/466206000000071000/groups/38190000004182920 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

### Sample Responses

**HTTP 200 OK**

**Case 1 — Standard org group details**
```json
{
  "status": "success",
  "summary": "Get group details",
  "data": {
    "groups": {
      "groupId": "320862000000286056",
      "groupName": "Analytics Team",
      "groupDesc": "Cross-functional analytics stakeholders",
      "groupMembers": ["bob@acme.com", "carol@acme.com", "dave@acme.com"]
    }
  }
}
```

**Case 2 — Client Portal Admin response (includes `domainName`)**
```json
{
  "status": "success",
  "summary": "Get group details",
  "data": {
    "groups": {
      "groupId": "38190000004182920",
      "groupName": "Portal Analysts",
      "groupDesc": "",
      "domainName": "reports.clientbrand.com",
      "groupMembers": ["portal.user1@client.com", "portal.user2@client.com"]
    }
  }
}
```

**Case 3 — Invalid or cross-workspace group ID**
```json
{
  "status": "failure",
  "summary": "GRPID_NOT_BELONGS_TO_DB",
  "data": {
    "errorCode": 7338,
    "errorMessage": "Group(s) does not belongs to current workspace"
  }
}
```

> **`data.groups` is an object, not an array.** Unlike Get Group List (which returns `groups` as an array), Get Group Details returns `groups` as a single JSON object.

#### Response Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `data.groups` | Object | A single group object (not an array — unlike the list API). |
| `groups.groupId` | String | Unique identifier of the group. |
| `groups.groupName` | String | Current display name of the group. |
| `groups.groupDesc` | String | Current description. Empty string `""` when not set. |
| `groups.groupMembers` | Array of Strings | Email addresses of all current members. |
| `groups.domainName` | String | *(Present when Account Admin is a Client Portal Admin, or when accessed via a custom portal domain URL.)* The portal domain this group belongs to. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **More detailed than Get Group List** | Returns a single group object with its full member list, description, and (when applicable) portal domain name. Use Get Group List to discover `groupId` values, then call this API for details on a specific group. |
| **`domainName` visibility** | Included in the response when the Account Admin is a Client Portal Admin **or** when the request is made via a custom portal domain URL — broader than Get Group List (which only shows `domainName` for Client Portal Admins). |
| **Response structure difference from Get Group List** | Get Group List returns `data.groups` (array). Get Group Details returns a single group object directly under `data`. |
| **Dependency** | `<group-id>` → Get Group List. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify `<workspace-id>`. |
| 7301 | User is not a Workspace Admin, Account Admin, or Organization Admin of the workspace. | Ensure the caller has at least Workspace Admin access. |
| 7338 | The specified `<group-id>` does not belong to this workspace. | Retrieve the correct group ID from Get Group List. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.share.read`. |

---

## Appendix A – Common HTTP Headers

| Header | Value | Required | Notes |
|--------|-------|----------|-------|
| `Authorization` | `Zoho-oauthtoken <oauth-token>` | **Mandatory** | OAuth 2.0 access token of the calling user. |
| `ZANALYTICS-ORGID` | Organisation ID | **Mandatory** for all APIs | Organisation ID of the workspace being managed. |
| `Content-Type` | `application/x-www-form-urlencoded` | Required for POST/PUT/DELETE | Create Group, Rename Group, Add Group Members, and Remove Group Members send CONFIG as a form-encoded body parameter. GET APIs and Delete Group (no CONFIG) do not require this header. |

---

## Appendix B – OAuth Scope Summary

| API | Method | Scope |
|-----|--------|-------|
| Get Group List | GET | `ZohoAnalytics.share.read` |
| Create Group | POST | `ZohoAnalytics.share.create` |
| Rename Group | PUT | `ZohoAnalytics.share.update` |
| Add Group Members | POST | `ZohoAnalytics.share.create` |
| Remove Group Members | DELETE | `ZohoAnalytics.share.delete` |
| Delete Group | DELETE | `ZohoAnalytics.share.delete` |
| Get Group Details | GET | `ZohoAnalytics.share.read` |

---

## Appendix C – API-Specific Notes and Behaviours

### Groups and View Sharing

Groups are the building block for bulk view-level access management. When a view is shared with a group, every current and future member of that group inherits that sharing. This means:

- **Adding a member to a group** immediately grants them access to all views currently shared with that group.
- **Removing a member from a group** immediately revokes the group-based access for that view — but only if the user has no other path to the view (direct sharing or membership in another group with the same share).
- **Deleting a group** revokes all group-based view access for every member simultaneously.

### Create Group

| Scenario | Behaviour |
|----------|-----------|
| `groupName` is empty or whitespace | Rejected immediately. Group names must be non-empty. |
| Duplicate `groupName` in same workspace | Fails with error **7282**. Group names are unique per workspace — the same name can exist in different workspaces. |
| `emailIds` contains a user not in the workspace | The request may partially succeed or fail depending on the portal domain context. Ensure all listed users are already workspace members. |
| `emailIds` contains a user already added to the group | For creation, all `emailIds` become members of the new group. No duplicate check is performed. |
| `inviteMail=true` with no `mailSubject` or `mailMessage` | The invitation is sent with default system-generated subject and message text. |
| `inviteMail=true` but email delivery fails | The group and its members are still created successfully. Email delivery failures do not roll back the operation. |
| `domainName` provided | The group is scoped to that portal domain. All `emailIds` must be users within that portal domain. Standard Zoho Analytics domain users cannot be added to a portal-domain group. |

### Rename Group

| Scenario | Behaviour |
|----------|-----------|
| `groupDesc` omitted | The description is **reset to an empty string**. It is not preserved from the previous value. Always include the existing description if you only intend to rename. |
| Renaming to the current name | Succeeds (idempotent for the name itself). |
| Renaming to a name used by another group in the same workspace | Fails with error **7282**. |
| Group ID from a different workspace | Fails with error **7338**. |

### Add Group Members

| Scenario | Behaviour |
|----------|-----------|
| Adding a user already in the group | Silently skipped. No error is raised. Only users genuinely new to the group receive an invitation email when `inviteMail=true`. |
| Adding a user not in the workspace | The behaviour depends on the portal context. In standard orgs, only workspace users can be group members. Add the user to the workspace first. |
| No `domainName` field | The domain context is resolved automatically from the group's existing domain association. The group was scoped to a domain at creation, and that scoping is preserved. |
| `inviteMail=true` but email delivery fails | Members are still added. Email failures do not roll back the operation. |

### Remove Group Members

| Scenario | Behaviour |
|----------|-----------|
| Removing a user not in the group | Silently processed. No error is raised. |
| Removing all members from a group | Allowed. The group continues to exist with zero members. It can be repopulated or deleted later. |
| `notifyUser=true` but email delivery fails | Members are still removed. Email failures do not roll back the operation. |
| Impact on shared views | If the user's only path to a shared view was through this group membership, they immediately lose access. If they also have direct sharing or membership in another group sharing the same view, access is retained. |

### Delete Group

| Scenario | Behaviour |
|----------|-----------|
| Group has active members | The group is deleted regardless. All members' group-based view access is revoked immediately. |
| Group is used in active view shares | All view shares that reference this group are also removed. Users who accessed views exclusively via this group will lose that access immediately. Users with direct sharing or other group access on the same views are unaffected. |
| Group ID from a different workspace | Fails with error **7338**. The group must belong to the same workspace specified in the URL. |
| Deletion is permanent | There is no soft-delete or trash mechanism for groups. Once deleted, the group and its sharing configuration cannot be restored. |

### Get Group Details vs. Get Group List

| Aspect | Get Group List | Get Group Details |
|--------|----------------|-------------------|
| URL | `.../groups` | `.../groups/<group-id>` |
| `data.groups` type | **Array** of group objects | **Single** group object |
| `domainName` in response | Only when Account Admin is a Client Portal Admin | When Account Admin is a Client Portal Admin **or** when accessed via a custom portal domain URL |
| Use case | Enumerate all groups; discover `groupId` values | Inspect a known group's current member list |

### White Label / Client Portal Domain Behaviour

| Scenario | Behaviour |
|----------|-----------|
| `domainName` provided in Create Group but does not exist | Fails with error **8060** before the group is created. |
| `domainName` belongs to a different org's Account Admin | Fails with error **8061**. |
| Standard domain user calling Get Group List via a portal URL | Returns only groups belonging to the portal's domain (not all workspace groups). |
| Client Portal Admin calling Get Group List | Returns all groups across all domain contexts. Each group entry includes `domainName`. |
| Client Portal Admin calling Get Group Details | Response includes `domainName` regardless of which domain the group belongs to. |
| Standard domain user calling Get Group Details via a portal URL | Response includes `domainName` showing the group's portal domain. |
| Adding members to a portal-domain group | Members must belong to the group's portal domain. Standard org users cannot be added to a portal-domain group. Do not include `domainName` in Add/Remove Group Members calls — the domain is determined by the group. |
| WL Workspace Admin (portal domain with restricted workspace access) | Cannot call any group APIs. Returns error **7301** — WL Workspace Admins do not have access in disabled-workspace portal contexts. |
