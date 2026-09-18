# View Preferences APIs – Documentation

This document describes the V2 **View Preferences** REST APIs of Zoho Analytics — specifically, marking and unmarking individual views (reports, tables, dashboards, etc.) as favourites for the authenticated user.

> Notes that apply to every API in this document:
> - All requests are authenticated via OAuth (`Authorization: Zoho-oauthtoken <token>`).
> - Both APIs are **workspace-scoped** and require the `ZANALYTICS-ORGID` header.
> - `ZohoAnalytics_Server_URI` depends on the data centre (`analyticsapi.zoho.com`, `.eu`, etc.).
> - Favourite status is **per-user** — marking a view as a favourite only affects the authenticated user's preference. Other users are not affected.
> - Both APIs have **no request body or CONFIG parameter**.
> - Both APIs return **HTTP 204 No Content** on success (empty body).

---

## Index

| # | API Name | Method | URL |
|---|----------|--------|-----|
| 1 | Add Favourite View | POST | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/favorite` |
| 2 | Remove Favourite View | DELETE | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/favorite` |

---

## 1. Add Favourite View

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/favorite` |
| **OAuth Scope** | `ZohoAnalytics.metadata.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** |
| **Permission Required** | The authenticated user must have at least **Read Only** permission on the view. This includes Account Admins, Organization Admins, Workspace Admins, View Owners, and any user explicitly granted Read Only or higher access to the view. |

> This API has no CONFIG parameter. All inputs are provided via URL path parameters only.

### Behaviour

- Adds the specified view to the **favourites list of the authenticated user**.
- Has no effect on other users' favourite preferences.
- If the view is already marked as a favourite by this user, the call succeeds silently (idempotent — no error is raised).
- The resulting `isFavorite: true` value is reflected in listing API responses (e.g., Get All Dashboards, Get Shared Dashboards) for the same user.

### Sample Requests

**Case 1 — Mark a chart view as favourite**

```http
POST /restapi/v2/workspaces/466206000000071000/views/466206000000105001/favorite HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Mark a dashboard as favourite**

```http
POST /restapi/v2/workspaces/466206000000071000/views/466206000000106002/favorite HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

### Sample Response

**HTTP 204 No Content** — No response body is returned on success.

```
HTTP/1.1 204 No Content
```

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify the `<workspace-id>` in the URL is correct and accessible. |
| 7104 | View not found. | Verify the `<view-id>` exists in the specified workspace. |
| 7301 | User does not have permission to mark this view as a favourite. | Ensure the user has at least Read Only permission on the view. |
| 7319 | The specified view does not belong to the specified workspace. | Ensure both `<workspace-id>` and `<view-id>` are consistent and correct. |
| 8535 | Invalid OAuth token. | Provide a valid, non-expired token with scope `ZohoAnalytics.metadata.update`. |

---

## 2. Remove Favourite View

| Attribute | Value |
|-----------|-------|
| **Method** | DELETE |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/favorite` |
| **OAuth Scope** | `ZohoAnalytics.metadata.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** |
| **Permission Required** | The authenticated user must have at least **Read Only** permission on the view. This includes Account Admins, Organization Admins, Workspace Admins, View Owners, and any user explicitly granted Read Only or higher access to the view. |

> This API has no CONFIG parameter. All inputs are provided via URL path parameters only.

### Behaviour

- Removes the specified view from the **favourites list of the authenticated user**.
- Has no effect on other users' favourite preferences.
- If the view is not currently marked as a favourite by this user, the call succeeds silently (idempotent — no error is raised).
- The resulting `isFavorite: false` (or absent) value is reflected in listing API responses for the same user.

### Sample Requests

**Case 1 — Remove a chart view from favourites**

```http
DELETE /restapi/v2/workspaces/466206000000071000/views/466206000000105001/favorite HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Remove a dashboard from favourites**

```http
DELETE /restapi/v2/workspaces/466206000000071000/views/466206000000106002/favorite HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

### Sample Response

**HTTP 204 No Content** — No response body is returned on success.

```
HTTP/1.1 204 No Content
```

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify the `<workspace-id>` in the URL is correct and accessible. |
| 7104 | View not found. | Verify the `<view-id>` exists in the specified workspace. |
| 7301 | User does not have permission to modify favourites for this view. | Ensure the user has at least Read Only permission on the view. |
| 7319 | The specified view does not belong to the specified workspace. | Ensure both `<workspace-id>` and `<view-id>` are consistent and correct. |
| 8535 | Invalid OAuth token. | Provide a valid, non-expired token with scope `ZohoAnalytics.metadata.update`. |

---

## Appendix A – Common HTTP Headers

| Header | Value | Required | Description |
|--------|-------|----------|-------------|
| `Authorization` | `Zoho-oauthtoken <oauth-token>` | **Mandatory** | OAuth 2.0 access token of the calling user. |
| `ZANALYTICS-ORGID` | Organization ID string | **Mandatory** | Organization ID of the workspace. Obtainable from listing API responses as the `orgId` field. |

> No `Content-Type` header is required — neither API sends a request body.

Example:

```http
POST /restapi/v2/workspaces/466206000000071000/views/466206000000105001/favorite HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

---

## Appendix B – OAuth Scope Summary

| API | HTTP Method | Scope |
|-----|-------------|-------|
| Add Favourite View | POST | `ZohoAnalytics.metadata.update` |
| Remove Favourite View | DELETE | `ZohoAnalytics.metadata.update` |

---

## Appendix C – Behaviour Notes

| Topic | Detail |
|-------|--------|
| **User-scoped preference** | Favourite status is stored per user (keyed by the authenticated user's ID). Marking or unmarking a view as a favourite does not affect any other user's view of the same resource. |
| **Reflected in listing APIs** | After a successful Add, the `isFavorite` field in listing API responses (e.g., Get All Dashboards, Get Shared Dashboards) returns `true` for the same user. After a Remove, it returns `false` or is absent. |
| **Idempotent operations** | Both APIs are safe to call multiple times. Adding a view that is already a favourite, or removing one that is not, succeeds without error. |
| **Applicable view types** | Any view type that a user can access with Read Only or higher permission can be marked as a favourite: Tables, Analysis Views (charts), Pivot Tables, Summary Views, Dashboards, Query Tables, and others. |
| **No CONFIG parameter** | Neither API accepts a CONFIG request parameter. The only inputs are the URL path parameters `<workspace-id>` and `<view-id>`. |
| **HTTP method choice** | `POST` is used for Add (not `PUT`) because the favourite entry is a new association being created. `DELETE` removes the association. Both use the same URL path with the `/favorite` suffix. |
| **Response** | Both APIs return HTTP 204 No Content with an empty body on success. There is no JSON response envelope for these operations. |
