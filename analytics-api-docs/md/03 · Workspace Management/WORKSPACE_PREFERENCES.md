# Zoho Analytics V2 REST API — Workspace Preferences

These APIs manage per-user workspace preferences — marking a workspace as the **default** (the workspace that opens on login) and managing **favourites** (starred workspaces for quick access).

> **Per-user scope:** Both default and favourite preferences are stored individually per user. Marking a workspace as default or favourite for one user has no effect on any other user's preferences.

> **Default vs Favourite:**
> - **Default workspace** — each user can have at most **one** default workspace at a time. Setting a new default automatically replaces the previous one. The default workspace is indicated by `isDefault: true` in workspace listing responses.
> - **Favourite workspaces** — a user can mark **multiple** workspaces as favourite simultaneously. Favouriting is an additive preference with no exclusivity constraint.

---

## Index

| # | API Name | Method | URL |
|---|----------|--------|-----|
| 1 | [Add Default Workspace](#1-add-default-workspace) | POST | `/restapi/v2/workspaces/<workspace-id>/default` |
| 2 | [Remove Default Workspace](#2-remove-default-workspace) | DELETE | `/restapi/v2/workspaces/<workspace-id>/default` |
| 3 | [Add Favourite Workspace](#3-add-favourite-workspace) | POST | `/restapi/v2/workspaces/<workspace-id>/favorite` |
| 4 | [Remove Favourite Workspace](#4-remove-favourite-workspace) | DELETE | `/restapi/v2/workspaces/<workspace-id>/favorite` |

---

## 1. Add Default Workspace

Marks the specified workspace as the calling user's default workspace. The default workspace is the one that opens automatically when the user logs in to Zoho Analytics.

A user can have only one default workspace at a time. If the user already has a different workspace set as default, that previous default is silently replaced — no error is raised. Calling this API on a workspace that is already the user's default succeeds without error (idempotent).

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/default` |
| **OAuth Scope** | `ZohoAnalytics.metadata.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin, or a Shared User, or a Group Member of the workspace, or any user with at least Read permission on a view within the workspace. |

> This API has no CONFIG parameter and no request body.

### Sample Requests

**Case 1 — Mark a workspace as default (Account Admin)**

```http
POST /restapi/v2/workspaces/466206000000071000/default HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Shared user setting their default workspace**

```http
POST /restapi/v2/workspaces/466206000000071000/default HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.aaaaaa.bbbbbb
ZANALYTICS-ORGID: 700000123456
```

**Case 3 — Client Portal user setting their default workspace (via portal domain)**

```http
POST /restapi/v2/workspaces/38190000004180410/default HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.cccccc.dddddd
ZANALYTICS-ORGID: 57058019
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Add Default Workspace returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |
| **Replaces any existing default silently** | If the user already has a different workspace set as default, the previous default is replaced without error. Only one default workspace is allowed per user. |
| **Idempotent** | Calling this API with the workspace that is already the user's default succeeds without error and makes no change. |
| **Access requirement** | The user must have at least one view shared with them in the workspace (i.e. any path to the workspace). Users with no access to any view in the workspace cannot set it as default (error 7301). |
| **No CONFIG or request body** | The workspace is identified solely by `<workspace-id>` in the URL. |
| **`isDefault` flag in list responses** | After calling this API, the workspace appears with `isDefault: true` in Get All Workspace List and Get Shared Workspace List responses. Use those APIs to verify the change. |
| **Dependency** | `<workspace-id>` → Get All Workspace List or Get Shared Workspace List. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify `<workspace-id>`. |
| 7301 | The user has no access to the specified workspace — no views have been shared with them, and they are not a Workspace Admin. | Ensure the user is a workspace member or has at least one view shared with them before marking it as default. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.metadata.update`. |

---

## 2. Remove Default Workspace

Removes the default workspace designation from the specified workspace for the calling user. After this operation, the user has no default workspace set.

Unlike Add Default Workspace, this API is **not idempotent** — if the specified workspace is not currently the user's default, the call fails with error **7415**. Verify the user's current default using Get All Workspace List (which returns `isDefault: true` for the current default) before calling this API.

| Attribute | Value |
|-----------|-------|
| **Method** | DELETE |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/default` |
| **OAuth Scope** | `ZohoAnalytics.metadata.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin, or a Shared User, or a Group Member of the workspace, or any user with at least Read permission on a view within the workspace. |

> This API has no CONFIG parameter and no request body.

### Sample Requests

**Case 1 — Remove the default designation from a workspace**

```http
DELETE /restapi/v2/workspaces/466206000000071000/default HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Shared user removing their default workspace**

```http
DELETE /restapi/v2/workspaces/466206000000071000/default HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.aaaaaa.bbbbbb
ZANALYTICS-ORGID: 700000123456
```

**Case 3 — Client Portal user removing their default workspace**

```http
DELETE /restapi/v2/workspaces/38190000004180410/default HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.cccccc.dddddd
ZANALYTICS-ORGID: 57058019
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

**Workspace not currently set as default (error)**

```json
{
  "status": "failure",
  "summary": "WORKSPACE_NOT_MARKED_AS_DEFAULT",
  "data": {
    "errorCode": 7415,
    "errorMessage": "The workspace is not marked as the default workspace."
  }
}
```

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Remove Default Workspace returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |
| **NOT idempotent — fails if not currently default** | Unlike Remove Favourite Workspace (which silently no-ops), this API returns error 7415 if the workspace is not the user's current default. Always verify `isDefault: true` in Get All Workspace List before calling. |
| **Contrast with Add Default Workspace** | Add Default Workspace is idempotent (calling it twice is safe). Remove Default Workspace is not — the second call on the same workspace will fail with 7415. |
| **After removal, user has no default workspace** | A new default must be set explicitly using Add Default Workspace. |
| **No CONFIG or request body** | The workspace is identified solely by `<workspace-id>` in the URL. |
| **Dependency** | `<workspace-id>` → Get All Workspace List. Confirm `isDefault: true` on the target workspace before calling. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify `<workspace-id>`. |
| 7301 | The user has no access to the specified workspace. | Ensure the user has at least one view shared with them in the workspace. |
| 7415 | The specified workspace is not the calling user's current default workspace. This API does not succeed silently for non-default workspaces. | Use Get All Workspace List to identify the workspace with `isDefault: true`, then call this API with that workspace ID. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.metadata.update`. |

---

## 3. Add Favourite Workspace

Adds the specified workspace to the calling user's list of favourite workspaces. Favourited workspaces are typically surfaced at the top of workspace listings for quick navigation.

A user can favourite multiple workspaces simultaneously — there is no exclusivity constraint. If the workspace is already in the user's favourites, this call succeeds silently without error (idempotent).

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/favorite` |
| **OAuth Scope** | `ZohoAnalytics.metadata.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin, or a Shared User, or a Group Member of the workspace, or any user with at least Read permission on a view within the workspace. |

> This API has no CONFIG parameter and no request body.

### Sample Requests

**Case 1 — Add a workspace to favourites (Workspace Admin)**

```http
POST /restapi/v2/workspaces/466206000000071000/favorite HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Shared user favouriting a workspace they have view access in**

```http
POST /restapi/v2/workspaces/466206000000071000/favorite HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.aaaaaa.bbbbbb
ZANALYTICS-ORGID: 700000123456
```

**Case 3 — Client Portal user favouriting their portal workspace**

```http
POST /restapi/v2/workspaces/38190000004180410/favorite HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.cccccc.dddddd
ZANALYTICS-ORGID: 57058019
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Add Favourite Workspace returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |
| **Idempotent** | If the workspace is already in the user's favourites, calling this API again succeeds without error and makes no change. |
| **Multiple favourites allowed** | There is no limit on the number of workspaces a user can mark as favourite. |
| **Access requirement** | The user must have at least one view shared with them in the workspace. Without access, the call fails with error 7301. |
| **No CONFIG or request body** | The workspace is identified solely by `<workspace-id>` in the URL. |
| **Dependency** | `<workspace-id>` → Get All Workspace List or Get Shared Workspace List. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify `<workspace-id>`. |
| 7301 | The user has no access to the specified workspace. | Ensure the user is a workspace member or has at least one view shared with them before adding it to favourites. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.metadata.update`. |

---

## 4. Remove Favourite Workspace

Removes the specified workspace from the calling user's list of favourite workspaces. If the workspace is not currently in the user's favourites, this call succeeds silently without error (idempotent).

| Attribute | Value |
|-----------|-------|
| **Method** | DELETE |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/favorite` |
| **OAuth Scope** | `ZohoAnalytics.metadata.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be a Workspace Admin, or a Shared User, or a Group Member of the workspace, or any user with at least Read permission on a view within the workspace. |

> This API has no CONFIG parameter and no request body.

### Sample Requests

**Case 1 — Remove a workspace from favourites**

```http
DELETE /restapi/v2/workspaces/466206000000071000/favorite HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Shared user removing a workspace from their favourites**

```http
DELETE /restapi/v2/workspaces/466206000000071000/favorite HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.aaaaaa.bbbbbb
ZANALYTICS-ORGID: 700000123456
```

**Case 3 — Client Portal user removing a workspace from their favourites**

```http
DELETE /restapi/v2/workspaces/38190000004180410/favorite HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.cccccc.dddddd
ZANALYTICS-ORGID: 57058019
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Remove Favourite Workspace returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |
| **Idempotent — no error if not in favourites** | Unlike Remove Default Workspace (which fails with 7415 if not set as default), this API silently succeeds even if the workspace is not currently in the user's favourites. |
| **Contrast with Remove Default Workspace** | Remove Default Workspace is NOT idempotent; Remove Favourite Workspace IS idempotent. This is the key behavioural asymmetry between the two "remove" operations. |
| **No CONFIG or request body** | The workspace is identified solely by `<workspace-id>` in the URL. |
| **Dependency** | `<workspace-id>` → Get All Workspace List or Get Shared Workspace List. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify `<workspace-id>`. |
| 7301 | The user has no access to the specified workspace. | Ensure the user has at least one view shared with them in the workspace. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.metadata.update`. |

---

## Appendix A – Common HTTP Headers

| Header | Value | Required | Notes |
|--------|-------|----------|-------|
| `Authorization` | `Zoho-oauthtoken <oauth-token>` | **Mandatory** | OAuth 2.0 access token of the calling user. |
| `ZANALYTICS-ORGID` | Organisation ID | **Mandatory** for all 4 APIs | Organisation ID of the workspace. |

> None of these 4 APIs require a request body or `Content-Type` header — they are POST/DELETE operations with no payload.

---

## Appendix B – OAuth Scope Summary

| API | Method | Scope |
|-----|--------|-------|
| Add Default Workspace | POST | `ZohoAnalytics.metadata.update` |
| Remove Default Workspace | DELETE | `ZohoAnalytics.metadata.update` |
| Add Favourite Workspace | POST | `ZohoAnalytics.metadata.update` |
| Remove Favourite Workspace | DELETE | `ZohoAnalytics.metadata.update` |

---

## Appendix C – API-Specific Notes and Behaviours

### Default vs Favourite — Behavioural Comparison

| Aspect | Default Workspace | Favourite Workspace |
|--------|-------------------|---------------------|
| How many per user | **Exactly one** (or none) | **Multiple** — no limit |
| Adding when already set/added | Replaces existing default silently | Silently no-ops (idempotent) |
| Removing when not set/added | **Fails with error 7415** | Silently no-ops (idempotent) |
| Visibility in workspace lists | `isDefault: true` in Get All / Owned / Shared response | Not exposed as a distinct field in standard list responses |
| Purpose | Opens on login | Quick navigation / starred workspaces |
| User scope | Per user, per org | Per user, per org |

### Add Default Workspace

| Scenario | Behaviour |
|----------|-----------|
| User has no existing default | The specified workspace is set as the user's default. |
| User already has a different workspace as default | The previous default is silently replaced. No error is raised for the switch. |
| Calling with the same workspace already set as default | Succeeds silently — idempotent. |
| User loses workspace access after setting default | The default preference is still stored. However, the workspace will not be presented as accessible until access is restored. |

### Remove Default Workspace

| Scenario | Behaviour |
|----------|-----------|
| Workspace is currently the user's default | Default is removed. The user has no default workspace until they set a new one. |
| Workspace is **not** the user's current default | **Fails with error 7415.** This is the primary failure case — use Get All Workspace List to confirm `isDefault: true` before calling this API. |
| Workspace ID is valid but user has no access | Fails with error 7301. |
| Calling immediately after Add Default | Succeeds — the workspace was just set and can be unset in sequence. |

### Add Favourite Workspace

| Scenario | Behaviour |
|----------|-----------|
| Workspace not yet in favourites | Added to the user's favourites list. |
| Workspace already in favourites | Succeeds silently — idempotent. No duplicate entry is created. |
| User can mark any workspace they have access to | Access is checked at the workspace level (any shared view). There is no additional permission required beyond basic read access. |

### Remove Favourite Workspace

| Scenario | Behaviour |
|----------|-----------|
| Workspace is in the user's favourites | Removed from the favourites list. |
| Workspace is **not** in the user's favourites | Succeeds silently — idempotent. Unlike Remove Default, this does not error. |

### White Label / Client Portal Behaviour

| Scenario | Behaviour |
|----------|-----------|
| Portal user adding a default/favourite workspace | Preferences are stored scoped to the portal user's organisation namespace. Portal users and standard Zoho Analytics users maintain separate preference stores even if they access the same workspace. |
| Portal user accessing via custom domain URL | The workspace must be accessible via that portal domain (shared with the portal user). If the workspace is not accessible in the portal domain context, the access check fails with 7301. |
| Account Admin (Client Portal Admin) managing preferences | Uses the standard Zoho Analytics namespace. The admin's preferences are independent of portal user preferences. |
