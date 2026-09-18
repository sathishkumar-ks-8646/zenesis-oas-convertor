# Zoho Analytics V2 REST API — White Label Domain Workspace Access

These APIs control whether a specific workspace is accessible through the organisation's **White Label / Client Portal** domain. When enabled, the workspace (and its shared views) becomes reachable by users who log in via the configured custom portal domain URL (e.g., `https://reports.clientbrand.com`). When disabled, the workspace is hidden from the portal domain — portal users can no longer access it through the custom domain URL.

---

## Prerequisites and Concepts

### White Label / Client Portal

White Label (also known as Client Portal) is a Zoho Analytics feature that allows organisations to embed analytics under their own branded domain. The Account Admin configures a custom domain (e.g., `reports.clientbrand.com`) through Zoho Analytics settings. Users can then access Zoho Analytics dashboards and reports via that branded domain without seeing Zoho branding.

### Workspace Domain Access

By default, a workspace is **not enabled** for White Label domain access after creation. An admin must explicitly enable it using the **Enable Workspace for Domain Access** API before portal users can access it through the custom domain. This allows fine-grained control over which workspaces are exposed through the portal.

- **Enabled:** The workspace is listed and accessible when users log in through the portal domain URL. Views shared with portal users appear under the custom domain.
- **Disabled:** The workspace is invisible to users accessing via the portal domain. It is still fully accessible via the standard `analyticsapi.zoho.com` URL for non-portal users.

### Permission Requirements for These APIs

These APIs require **two conditions** to be met simultaneously:

1. **The caller** must be an Account Admin or Organization Admin of the workspace's organisation.
2. **The workspace's Account Admin** must have an active White Label / Client Portal domain configured for the organisation.

If the organisation has no White Label domain set up, these APIs will return a permission error even for Account Admins — there is no portal domain to enable or disable the workspace for.

---

## Index

| # | API Name | Method | URL |
|---|----------|--------|-----|
| 1 | [Enable Workspace for Domain Access](#1-enable-workspace-for-domain-access) | POST | `/restapi/v2/workspaces/<workspace-id>/wlaccess` |
| 2 | [Disable Workspace for Domain Access](#2-disable-workspace-for-domain-access) | DELETE | `/restapi/v2/workspaces/<workspace-id>/wlaccess` |

---

## 1. Enable Workspace for Domain Access

Enables the specified workspace for access through the organisation's White Label / Client Portal domain. Once enabled, the workspace becomes visible and accessible to users who log in via the configured custom domain URL.

The portal domain is automatically resolved from the workspace's Account Admin's White Label configuration — no domain name parameter is required. Each workspace can only be associated with one portal domain (the Account Admin's configured domain).

Calling this API on a workspace that is already enabled for domain access fails with error **12049**.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/wlaccess` |
| **OAuth Scope** | `ZohoAnalytics.metadata.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin of the workspace's organisation, **and** the workspace's Account Admin must have a White Label / Client Portal domain configured. |

> This API has no CONFIG parameter and no request body.

### Sample Requests

**Case 1 — Account Admin enabling a workspace for their portal domain**

The caller is the Account Admin who has a White Label domain (`reports.clientbrand.com`) configured. This enables the workspace so users on that portal can access it.

```http
POST /restapi/v2/workspaces/466206000000071000/wlaccess HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Organization Admin enabling a workspace on behalf of the org's portal**

An Org Admin in an organisation with an active White Label setup enabling a workspace for portal access.

```http
POST /restapi/v2/workspaces/466206000000071000/wlaccess HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.aaaaaa.bbbbbb
ZANALYTICS-ORGID: 700000123456
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

**Workspace already enabled (error)**

```json
{
  "status": "failure",
  "summary": "WORKSPACE_ALREADY_ENABLED_FOR_DOMAIN_ACCESS",
  "data": {
    "errorCode": 12049,
    "errorMessage": "The workspace is already enabled for domain access."
  }
}
```

**Caller's org has no White Label domain configured (permission error)**

```json
{
  "status": "failure",
  "summary": "SECURITY_NOT_PERMITTED",
  "data": {
    "errorCode": 7301,
    "errorMessage": "You do not have the permission to do this operation."
  }
}
```

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Enable Workspace for Domain Access returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify `<workspace-id>`. |
| 7301 | The caller is not an Account Admin or Organization Admin of the workspace's organisation, **or** the workspace's Account Admin does not have a White Label / Client Portal domain configured. | Ensure the caller is an org admin and that the organisation has an active White Label domain setup. |
| 12049 | The workspace is already enabled for White Label domain access. Calling Enable on an already-enabled workspace is not idempotent. | Check the current domain access state before calling. Use Disable first if you need to re-enable (e.g., after domain reconfiguration). |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.metadata.update`. |

---

## 2. Disable Workspace for Domain Access

Removes the specified workspace from the organisation's White Label / Client Portal domain. Once disabled, the workspace is no longer accessible to users who log in via the custom portal domain URL. Users who had access via the portal immediately lose that access.

> **Impact on portal users:** Disabling a workspace does not remove any view-level sharing or user memberships. It only gates access via the portal domain URL. The workspace and its data remain intact and accessible via the standard Zoho Analytics URL for non-portal users.

Calling this API on a workspace that is not currently enabled for domain access fails with error **12050**.

| Attribute | Value |
|-----------|-------|
| **Method** | DELETE |
| **URL** | `/restapi/v2/workspaces/<workspace-id>/wlaccess` |
| **OAuth Scope** | `ZohoAnalytics.metadata.update` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin of the workspace's organisation, **and** the workspace's Account Admin must have a White Label / Client Portal domain configured. |

> This API has no CONFIG parameter and no request body.

### Sample Requests

**Case 1 — Account Admin disabling a workspace from the portal domain**

```http
DELETE /restapi/v2/workspaces/466206000000071000/wlaccess HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Organization Admin disabling a workspace from the portal**

```http
DELETE /restapi/v2/workspaces/466206000000071000/wlaccess HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.aaaaaa.bbbbbb
ZANALYTICS-ORGID: 700000123456
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. There is no JSON payload to parse on success; check only the HTTP status code.

**Workspace not currently enabled for domain access (error)**

```json
{
  "status": "failure",
  "summary": "WORKSPACE_ALREADY_DISABLED_FOR_DOMAIN_ACCESS",
  "data": {
    "errorCode": 12050,
    "errorMessage": "The workspace is already disabled for domain access."
  }
}
```

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Disable Workspace for Domain Access returns a bare HTTP `204 No Content` on success — no `status`/`summary` JSON to parse. |

### Error Codes

| Error-Code | Reason | Solution |
|-----------:|--------|----------|
| 7103 | Workspace not found. | Verify `<workspace-id>`. |
| 7301 | The caller is not an Account Admin or Organization Admin of the workspace's organisation, or the organisation has no White Label domain. | Ensure the caller has admin access and the org has a configured White Label domain. |
| 12050 | The workspace is not currently enabled for White Label domain access. Calling Disable on an already-disabled workspace is not idempotent. | Verify the current state before calling. Only call Disable on workspaces previously enabled via Enable Workspace for Domain Access. |
| 8535 | Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.metadata.update`. |

---

## Appendix A – Common HTTP Headers

| Header | Value | Required | Notes |
|--------|-------|----------|-------|
| `Authorization` | `Zoho-oauthtoken <oauth-token>` | **Mandatory** | OAuth 2.0 access token of the calling user. Must be Account Admin or Org Admin of an org with a White Label domain. |
| `ZANALYTICS-ORGID` | Organisation ID | **Mandatory** | Organisation ID of the workspace. |

> Neither API accepts a request body or CONFIG parameter. No `Content-Type` header is required.

---

## Appendix B – OAuth Scope Summary

| API | Method | Scope |
|-----|--------|-------|
| Enable Workspace for Domain Access | POST | `ZohoAnalytics.metadata.update` |
| Disable Workspace for Domain Access | DELETE | `ZohoAnalytics.metadata.update` |

---

## Appendix C – Operational Notes and Failure Cases

### White Label Prerequisites

| Condition | Required For |
|-----------|-------------|
| Organisation has a White Label / Client Portal domain configured | **Mandatory** for both APIs. Without this, even Account Admins get a 7301 error. |
| Caller is Account Admin or Org Admin | **Mandatory**. Regular Workspace Admins and shared users cannot call these APIs. |
| Domain is automatically resolved | The portal domain is resolved from the workspace's Account Admin's White Label configuration — it is not passed as a parameter. An org can have at most one associated portal domain per workspace. |

### Enable Workspace for Domain Access

| Scenario | Behaviour |
|----------|-----------|
| Workspace not yet enabled | Domain ID is written to the workspace's domain configuration. Portal users can now access the workspace via the custom domain URL. |
| Workspace already enabled | **Fails with error 12049.** Unlike similar toggle APIs (e.g., favourites), this is not idempotent. Check current state before calling. |
| Organisation has no White Label domain | **Fails with error 7301.** The API requires a configured portal domain to associate the workspace with. Set up the White Label domain in Zoho Analytics settings first. |
| Multiple workspaces in the same org | Each workspace must be individually enabled. Enabling one workspace does not affect others. |
| New workspace created in an org with existing portal | The workspace starts **disabled** by default. It must be explicitly enabled before portal users can access it. |

### Disable Workspace for Domain Access

| Scenario | Behaviour |
|----------|-----------|
| Workspace currently enabled | Domain ID is cleared from the workspace configuration. Portal users immediately lose access via the custom domain URL. |
| Workspace not enabled (already disabled) | **Fails with error 12050.** Not idempotent. |
| Impact on portal user memberships | Disabling does not remove users from the workspace or revoke view-level sharing. The workspace and its data remain intact. Portal users who are also standard Zoho Analytics users can still access the workspace at `analyticsapi.zoho.com`. Only portal-domain-only users (users who exist exclusively as portal users) lose meaningful access. |
| Impact on shared views | View-level shares are preserved. If the workspace is later re-enabled, portal users will regain access without any re-sharing required. |
| Re-enabling after disable | Call Enable Workspace for Domain Access again. The previous domain association is restored using the Account Admin's current White Label configuration. |

### Enable ↔ Disable State Machine

```
[Created — Disabled by default]
         |
         | POST /wlaccess (Enable)
         ↓
 [Enabled for Domain Access]  ──── POST /wlaccess ──→  Error 12049
         |
         | DELETE /wlaccess (Disable)
         ↓
    [Disabled]  ─────────────── DELETE /wlaccess ──→  Error 12050
         |
         | POST /wlaccess (Re-enable)
         ↓
 [Enabled for Domain Access]
```

### Comparison with Similar APIs

| Aspect | Enable/Disable WL Access | Add/Remove Default Workspace | Add/Remove Favourite |
|--------|--------------------------|------------------------------|----------------------|
| Idempotent enable | **No** — error 12049 on double-enable | Yes (silently replaces) | Yes (silently no-ops) |
| Idempotent disable | **No** — error 12050 on double-disable | No — error 7415 | Yes (silently no-ops) |
| Caller scope | Account Admin / Org Admin only | Any user with workspace access | Any user with workspace access |
| Effect scope | Affects all portal domain users | Per-user preference only | Per-user preference only |
| Prerequisite | Active White Label domain on the org | None | None |
