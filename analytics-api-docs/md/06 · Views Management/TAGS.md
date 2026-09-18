# Zoho Analytics V2 REST API — Tags

This document covers the ten **Tag** REST APIs of Zoho Analytics — the APIs that create the coloured labels a workspace uses to organise its views, and that attach those labels to tables, reports, dashboards, and every other view type.

## What a tag is

A tag is a **workspace-scoped label** with two properties: a `name` and a `colorCode`. On its own it does nothing. Its value comes from being **associated** with views, so that a workspace with hundreds of objects can be filtered down to "everything tagged Finance" or "everything tagged Deprecated".

That gives the family two halves that are easy to confuse:

| | Tag lifecycle | Tag ↔ view association |
|---|---|---|
| **What it manages** | The tag object itself | The link between a tag and a view |
| **APIs** | [Create Tag](#4-create-tag), [Update Tag](#5-update-tag), [Delete Tag](#6-delete-tag), [Get Tags List](#1-get-tags-list) | The remaining six |
| **Deleting the tag** | Removes the tag everywhere | — |
| **Removing an association** | — | Leaves both the tag and the view intact |

Associations are a plain many-to-many relationship: one tag can label many views, and one view can carry up to ten tags.

---

## Index

| # | API Name | Method | URL |
|---|----------|--------|-----|
| 1 | [Get Tags List](#1-get-tags-list) | GET | `/restapi/v2/workspaces/<workspace-id>/tags` |
| 2 | [Get Tagged Views](#2-get-tagged-views) | GET | `/restapi/v2/workspaces/<workspace-id>/tags/<tag-id>/views` |
| 3 | [Get View Tags](#3-get-view-tags) | GET | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/tags` |
| 4 | [Create Tag](#4-create-tag) | POST | `/restapi/v2/workspaces/<workspace-id>/tags` |
| 5 | [Update Tag](#5-update-tag) | PUT | `/restapi/v2/workspaces/<workspace-id>/tags/<tag-id>` |
| 6 | [Delete Tag](#6-delete-tag) | DELETE | `/restapi/v2/workspaces/<workspace-id>/tags/<tag-id>` |
| 7 | [Add Tag To Multiple Views](#7-add-tag-to-multiple-views) | POST | `/restapi/v2/workspaces/<workspace-id>/tags/<tag-id>/views` |
| 8 | [Remove Tag From Multiple Views](#8-remove-tag-from-multiple-views) | DELETE | `/restapi/v2/workspaces/<workspace-id>/tags/<tag-id>/views` |
| 9 | [Add Multiple Tags To View](#9-add-multiple-tags-to-view) | POST | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/tags` |
| 10 | [Remove Multiple Tags From View](#10-remove-multiple-tags-from-view) | DELETE | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/tags` |

> Notes that apply to all ten APIs:
> - All require the `ZANALYTICS-ORGID` header.
> - All are **available in Client Portal / White Label contexts**.
> - Tags belong to exactly one workspace. A tag can never be attached to a view in a different workspace.
> - **Four APIs return a body; six return `204 No Content`.** See [Appendix D](#appendix-d--general-response-payload-notes).

---

## How the Ten APIs Relate

[Create Tag](#4-create-tag) is the only source of a `tagId`, and it is the ID every other tag-side API needs. Everything else either reads the graph or edits one edge of it.

```
          4. Create Tag  ──►  data.tagId
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
   5. Update Tag            6. Delete Tag          ┌── association ──┐
   (rename / recolour)      (removes the tag       │                 │
                             AND every one of      ▼                 ▼
                             its associations)  7. Add Tag      9. Add Multiple
                                                To Multiple      Tags To View
                                                Views            (view side)
                                                (tag side)            │
                                                   │                  │
                                                   ▼                  ▼
                                                8. Remove Tag    10. Remove Multiple
                                                From Multiple        Tags From View
                                                Views
        ┌──────────────────── read back ────────────────────┐
        ▼                          ▼                        ▼
  1. Get Tags List        2. Get Tagged Views        3. Get View Tags
  (every tag in the       (which views carry         (which tags a
   workspace)              this tag)                  view carries)
```

| Relationship | Detail |
|--------------|--------|
| **`tagId` has exactly one origin** | [Create Tag](#4-create-tag) returns it as `data.tagId`. [Get Tags List](#1-get-tags-list) and [Get View Tags](#3-get-view-tags) return it afterwards as `tags[].id`. Every other tag-side API takes it in the path or in `tagIds`. |
| **`viewId` comes from outside this family** | No tag API creates a view. Get view IDs from [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list), or read them back from [Get Tagged Views](#2-get-tagged-views) as `views[].id`. |
| **The tag-side and view-side association APIs edit the same table from opposite ends** | [Add Tag To Multiple Views](#7-add-tag-to-multiple-views) attaches **one tag to many views**; [Add Multiple Tags To View](#9-add-multiple-tags-to-view) attaches **many tags to one view**. The resulting associations are indistinguishable. Their **permission rules differ** — see [The Two Sides of an Association](#the-two-sides-of-an-association). |
| **The two read-back APIs are inverses** | [Get Tagged Views](#2-get-tagged-views) answers "which views carry tag X"; [Get View Tags](#3-get-view-tags) answers "which tags does view Y carry". Together they let you walk the association graph in either direction. |
| **[Delete Tag](#6-delete-tag) cascades; the removal APIs do not** | Deleting a tag removes the tag *and* every association it had. [Remove Tag From Multiple Views](#8-remove-tag-from-multiple-views) removes associations only — the tag survives and can be re-attached. |
| **[Update Tag](#5-update-tag) never touches associations** | Renaming or recolouring a tag leaves every association in place. Views tagged before the rename are still tagged after it. |
| **The ten-tag ceiling is enforced on both add paths** | Both [Add Tag To Multiple Views](#7-add-tag-to-multiple-views) and [Add Multiple Tags To View](#9-add-multiple-tags-to-view) validate it before writing anything. See [Limitations](#limitations). |
| **Verification is always a read-back** | Six of the ten APIs return `204` with no body. The only way to confirm what changed is [Get Tags List](#1-get-tags-list), [Get Tagged Views](#2-get-tagged-views), or [Get View Tags](#3-get-view-tags). |
| **Tags are metadata, not data** | They never affect rows, sharing, or permissions. A tag is a label for organising a workspace; it does not grant or restrict access to anything. |

### Typical sequences

**Create a tag and apply it across a set of views**

```
Create Tag {"name":"Finance","colorCode":"#1da043"}  →  data.tagId
   → Add Tag To Multiple Views {"viewIds":[...]}     →  204
   → Get Tagged Views                                →  confirm the list
```

**Label one dashboard with several existing tags**

```
Get Tags List                                        →  tags[].id
   → Add Multiple Tags To View {"tagIds":[...]}      →  204
   → Get View Tags                                   →  confirm
```

**Retire a tag completely**

```
Delete Tag   →  204   (tag and all its associations disappear together)
   → Get Tags List  →  the tag is gone
```

**Strip one view back to no tags at all**

```
Remove Multiple Tags From View {"dissociateAll": true}  →  204
   → Get View Tags  →  {"tags": []}
```

---

## The Two Sides of an Association

The tag-side and view-side association APIs write the same association table, but they are **not** interchangeable, because they check different permissions.

| | Tag side — [Add Tag To Multiple Views](#7-add-tag-to-multiple-views) / [Remove Tag From Multiple Views](#8-remove-tag-from-multiple-views) | View side — [Add Multiple Tags To View](#9-add-multiple-tags-to-view) / [Remove Multiple Tags From View](#10-remove-multiple-tags-from-view) |
|---|---|---|
| **Path** | `/tags/<tag-id>/views` | `/views/<view-id>/tags` |
| **Fixed end** | One tag | One view |
| **CONFIG carries** | `viewIds` | `tagIds` |
| **Who may call it** | An Account Admin or Organization Admin, or a Workspace Admin | Any of those, **or** the View Owner, **or** any user with Edit Design permission on the view |
| **Batch shape** | Many views at once | Many tags at once |

The consequence in practice: **a View Owner who is not a Workspace Admin can tag their own view, but cannot use the tag-side APIs at all** — even to attach a tag to that very same view. If your integration runs as a non-admin user, it must use the view-side APIs.

> Read-only users are blocked from all four association APIs regardless of any other permission, with error `8180`.

---

## Limitations

These are the limits that apply with **default settings**.

| Limitation | Value | Enforced by |
|------------|-------|-------------|
| **Tags per view** | **10.** Counted across all tags on the view, not per request. | `8181` |
| **`viewIds` per request** | **1–1000** entries. | `8547` |
| **`tagIds` per request** | **1–1000** entries. | `8547` |
| **Tag name length** | **100** characters. | `8507` |
| **Tag name uniqueness** | A tag name must be unique **within the workspace**. | `8174` |
| **`colorCode` format** | A hex colour only — `#RRGGBB` or `#RGB`. Colour keywords are not accepted. | `8509` |
| **`CONFIG` length — association APIs** | **1,000,000** characters, with the `viewIds` / `tagIds` array itself capped at **50,000** characters. | `8507` |
| **`CONFIG` length — Get Tagged Views** | **1,000** characters. | `8507` |
| **Cross-workspace association** | **Not possible.** Every view in `viewIds` must belong to `<workspace-id>`, and every tag in `tagIds` must exist in it. | `8184` |
| **Tag creation from the view side** | **Not supported.** [Add Multiple Tags To View](#9-add-multiple-tags-to-view) only accepts IDs of tags that already exist. Create them first with [Create Tag](#4-create-tag). | `8184` |
| **Bulk tag creation** | **Not supported.** [Create Tag](#4-create-tag) creates exactly one tag per call. |  — |
| **Renaming via Create** | **Not possible.** A second [Create Tag](#4-create-tag) with an existing name fails rather than returning the existing tag. | `8174` |

> **The ten-tag ceiling counts what is already there.** A view holding 8 tags accepts 2 more; a request adding 3 fails outright with `8181` and **nothing is written** — the check runs before the insert, so the operation is all-or-nothing.

---

## Permission Model

| API | Who may call it |
|-----|-----------------|
| [Get Tags List](#1-get-tags-list) | Any user with access to the workspace — Account Admin, Organization Admin, Workspace Admin, or any shared user, including custom roles. |
| [Get Tagged Views](#2-get-tagged-views) | Any user with access to the workspace. The returned list is **filtered to the views that caller can see**. |
| [Get View Tags](#3-get-view-tags) | Any user with **Read** permission on the view. |
| [Create Tag](#4-create-tag) | An Account Admin or Organization Admin, or a Workspace Admin. |
| [Update Tag](#5-update-tag) | An Account Admin or Organization Admin, or a Workspace Admin. |
| [Delete Tag](#6-delete-tag) | An Account Admin or Organization Admin, or a Workspace Admin. |
| [Add Tag To Multiple Views](#7-add-tag-to-multiple-views) | An Account Admin or Organization Admin, or a Workspace Admin. **Not** the View Owner. |
| [Remove Tag From Multiple Views](#8-remove-tag-from-multiple-views) | An Account Admin or Organization Admin, or a Workspace Admin. **Not** the View Owner. |
| [Add Multiple Tags To View](#9-add-multiple-tags-to-view) | An Account Admin or Organization Admin, or a Workspace Admin, or the View Owner, or any user with **Edit Design** permission on the view. |
| [Remove Multiple Tags From View](#10-remove-multiple-tags-from-view) | An Account Admin or Organization Admin, or a Workspace Admin, or the View Owner, or any user with **Edit Design** permission on the view. |

| Gate | Behaviour |
|------|-----------|
| **Read-only users** | Blocked from all four association APIs (7, 8, 9, 10) with `8180`, whatever else they hold. They can still call the three read APIs. |
| **Client Portal / White Label** | All ten APIs are **available** through a custom domain, subject to the same permissions. |

> **Reading is broad, writing is narrow.** Any user who can open the workspace can list its tags; only administrators can change them. This is deliberate — tags are a shared organising vocabulary, so they are readable by everyone and editable by few.

---

## The `colorCode` Attribute

`colorCode` is a hex colour string, and it is validated twice — first against the accepted pattern, then by the tag service.

**Accepted:** `#` followed by exactly **6** hex digits (`#e72d35`) or exactly **3** hex digits (`#f90`). Case-insensitive.

**Rejected:** colour keywords (`red`, `blue`), `rgb()` notation, 8-digit values with alpha (`#e72d35ff`), and a bare hex value with no leading `#` (`e72d35`). All fail with `8509` before the request reaches the tag service.

Colours observed in real workspaces include `#e72d35`, `#f5a623`, `#55acee`, and `#1da043`. Zoho Analytics does not restrict you to a palette — any valid hex value is stored and returned exactly as sent.

```json
{ "name": "Finance", "colorCode": "#1da043" }
```

> `colorCode` is presentation only. It affects how the tag is drawn in the Zoho Analytics interface and nothing else — two tags may share a colour, and the colour plays no part in matching or filtering.

---

## 1. Get Tags List

Returns every tag that exists in the workspace.

| Attribute | Value |
|-----------|-------|
| **URL** | `/restapi/v2/workspaces/<workspace-id>/tags` |
| **HTTP Method** | `GET` |
| **OAuth Scope** | `ZohoAnalytics.metadata.read` |
| **Mandatory Header** | `ZANALYTICS-ORGID` |
| **CONFIG** | This API takes no CONFIG fields |
| **Success Status** | `200 OK` with a JSON body |

**Path parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `<workspace-id>` | Long | ID of the workspace whose tags are listed. |

### Sample Requests

```http
GET /restapi/v2/workspaces/320873000000419001/tags HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

There is nothing else to send.

### Sample Responses

**HTTP 200 OK — a workspace with four tags**

```json
{
  "status": "success",
  "summary": "Get tags",
  "data": {
    "tags": [
      {
        "id": "320873000000425158",
        "name": "Tag_AccountAdmin_1_Updated",
        "colorCode": "#e72d35"
      },
      {
        "id": "320873000000419779",
        "name": "Tag_AccountAdmin_2",
        "colorCode": "#f5a623"
      },
      {
        "id": "320873000000421641",
        "name": "Tag_OrgAdmin_1_Updated",
        "colorCode": "#55acee"
      },
      {
        "id": "320873000000424199",
        "name": "Tag_WkAdmin_1_Updated",
        "colorCode": "#f5a623"
      }
    ]
  }
}
```

Note that two different tags share `#f5a623` — colours are not unique.

**HTTP 200 OK — a workspace with no tags**

```json
{
  "status": "success",
  "summary": "Get tags",
  "data": {
    "tags": []
  }
}
```

An empty array is a success, not an error.

**HTTP 403 Forbidden — the caller cannot reach the workspace**

```json
{
  "status": "failure",
  "summary": "SECURITY_NOT_PERMITTED",
  "data": {
    "errorCode": 7301,
    "errorMessage": "You do not have the permission to perform this operation."
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | String | `"success"` on success. |
| `summary` | String | `"Get tags"`. |
| `data` | Object | Wrapper. |
| `data.tags` | Array | Every tag in the workspace. Empty when there are none. |
| `data.tags[].id` | String | ID of the tag, **as a string**. This is the `<tag-id>` for [Update Tag](#5-update-tag), [Delete Tag](#6-delete-tag), [Get Tagged Views](#2-get-tagged-views), [Add Tag To Multiple Views](#7-add-tag-to-multiple-views), and [Remove Tag From Multiple Views](#8-remove-tag-from-multiple-views), and the `tagIds` value for [Add Multiple Tags To View](#9-add-multiple-tags-to-view) and [Remove Multiple Tags From View](#10-remove-multiple-tags-from-view). |
| `data.tags[].name` | String | Display name of the tag, unique within the workspace. |
| `data.tags[].colorCode` | String | Hex colour, returned exactly as it was stored. |

### Notes & Behaviour

| Behaviour | Detail |
|-----------|--------|
| **It lists tags, not associations** | A tag appears here whether or not it is attached to anything. To find out what a tag labels, call [Get Tagged Views](#2-get-tagged-views). |
| **Every user who can open the workspace can read it** | Including shared users on custom roles. Tags are a shared vocabulary, so the read is deliberately unrestricted. |
| **Ordering is not guaranteed** | Do not depend on the array order. Sort client-side if you need a stable presentation. |
| **`id` is a string** | Even though it is numerically a long. Do not parse it into a fixed-width integer type. |
| **There is no pagination** | The full tag list is returned in one response. The per-view ceiling keeps workspaces from accumulating unbounded tags in practice. |
| **An empty list is a success** | `{"tags": []}` with HTTP 200. |
| **Dependency chain:** | Get Tags List → `tags[].id` → [Add Multiple Tags To View](#9-add-multiple-tags-to-view) / [Get Tagged Views](#2-get-tagged-views) / [Update Tag](#5-update-tag). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7103 | `META_OBJECT_NOT_PRESENT` — The workspace does not exist. | Verify `<workspace-id>`. |
| 7301 | `SECURITY_NOT_PERMITTED` — The caller has no access to the workspace. | Ensure the workspace is shared with the calling user. |
| 7390 | `WORKSPACE_NOT_BELONGS_TO_ORG` — The workspace does not belong to the organization in `ZANALYTICS-ORGID`. | Send the organization ID that owns the workspace. |
| 8083 | `ORGID_NOT_PRESENT_IN_THE_HEADER` — The `ZANALYTICS-ORGID` header is missing. | Add the header. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token carrying `ZohoAnalytics.metadata.read`. |

---

## 2. Get Tagged Views

Returns the views that carry a given tag.

| Attribute | Value |
|-----------|-------|
| **URL** | `/restapi/v2/workspaces/<workspace-id>/tags/<tag-id>/views` |
| **HTTP Method** | `GET` |
| **OAuth Scope** | `ZohoAnalytics.metadata.read` |
| **Mandatory Header** | `ZANALYTICS-ORGID` |
| **CONFIG** | Optional |
| **Success Status** | `200 OK` with a JSON body |

**Path parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `<workspace-id>` | Long | ID of the workspace that owns the tag. |
| `<tag-id>` | Long | ID of the tag. Must exist in `<workspace-id>`, otherwise `8184`. |

### CONFIG Parameters

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | Integer | No | unlimited | Maximum number of views to return. Omit to return all of them. |
| `offset` | Integer | No | `0` | Number of views to skip before collecting the result. Used with `limit` to page through a large association list. |

### Sample Requests

**Case 1 — every view carrying the tag**

```http
GET /restapi/v2/workspaces/320873000000419001/tags/320873000000425158/views HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — the second page of ten**

```http
GET /restapi/v2/workspaces/320873000000419001/tags/320873000000425158/views HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

```json
{
  "limit": 10,
  "offset": 10
}
```

As this is a `GET`, the CONFIG travels as a stringified, URL-encoded query parameter — see [Appendix A](#appendix-a--common-http-headers).

### Sample Responses

**HTTP 200 OK — a tag spanning four view types**

```json
{
  "status": "success",
  "summary": "Get tagged views",
  "data": {
    "views": [
      {
        "id": "20867000000038313",
        "name": "Sales_Table",
        "type": "Table"
      },
      {
        "id": "20867000000038314",
        "name": "Dashboard_1",
        "type": "Dashboard"
      },
      {
        "id": "20867000000038319",
        "name": "Chart1",
        "type": "AnalysisView"
      },
      {
        "id": "20867000000038322",
        "name": "Pivot",
        "type": "Pivot"
      }
    ]
  }
}
```

**HTTP 200 OK — the tag exists but labels nothing**

```json
{
  "status": "success",
  "summary": "Get tagged views",
  "data": {
    "views": []
  }
}
```

This is also what you get immediately after [Remove Tag From Multiple Views](#8-remove-tag-from-multiple-views) with `dissociateAll: true`.

**HTTP 403 Forbidden — the tag does not exist in this workspace**

```json
{
  "status": "failure",
  "summary": "VIEW_OR_TAG_NOT_PRESENT_IN_DB_TO_TAG",
  "data": {
    "errorCode": 8184,
    "errorMessage": "View/Tag not present or duplicated in db."
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | String | `"success"` on success. |
| `summary` | String | `"Get tagged views"`. |
| `data` | Object | Wrapper. |
| `data.views` | Array | Views carrying the tag that the caller is entitled to see. Empty when there are none. |
| `data.views[].id` | String | ID of the view, **as a string**. The `<view-id>` for [Get View Tags](#3-get-view-tags), [Add Multiple Tags To View](#9-add-multiple-tags-to-view), and [Remove Multiple Tags From View](#10-remove-multiple-tags-from-view). |
| `data.views[].name` | String | Display name of the view. |
| `data.views[].type` | String | View type. See [View `type` values](#view-type-values). |

#### View `type` values

| Value | View type |
|-------|-----------|
| `Table` | A table |
| `Report` | A tabular view |
| `AnalysisView` | A chart view |
| `Pivot` | A pivot view |
| `SummaryView` | A summary view |
| `TableView` | A table view |
| `QueryTable` | A query table |
| `Dashboard` | A dashboard |
| `WIDGET` | A dashboard widget |
| `Tab` | A dashboard tab |
| `PipelineTable` | A pipeline table |
| `DataModelObject` | A data model object |

### Notes & Behaviour

| Behaviour | Detail |
|-----------|--------|
| **The result is filtered to what the caller can see** | Two users calling this with the same `<tag-id>` can legitimately get different lists. A shared user sees only the tagged views shared with them; an administrator sees all of them. Do not treat the response as the complete association set unless the caller is an administrator. |
| **`limit` and `offset` are the only paging controls** | No cursor and no total count are returned, so you cannot tell from one response whether more pages exist. Request `limit + 1` and check whether you got an extra row, or keep paging until a short page comes back. |
| **A non-existent tag is an error, not an empty list** | `8184`. An empty `views` array means the tag exists and labels nothing. |
| **It is the inverse of [Get View Tags](#3-get-view-tags)** | Same association table, read from the other end. |
| **Every value is a string** | Including `id`. `type` is a name, never a numeric code. |
| **Ordering is not guaranteed** | Sort client-side if presentation order matters. |
| **Dependency chain:** | [Get Tags List](#1-get-tags-list) or [Create Tag](#4-create-tag) → `<tag-id>` → Get Tagged Views → `views[].id`. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7103 | `META_OBJECT_NOT_PRESENT` — The workspace does not exist. | Verify `<workspace-id>`. |
| 7301 | `SECURITY_NOT_PERMITTED` — The caller has no access to the workspace. | Ensure the workspace is shared with the calling user. |
| 7390 | `WORKSPACE_NOT_BELONGS_TO_ORG` — The workspace does not belong to the organization in `ZANALYTICS-ORGID`. | Send the organization ID that owns the workspace. |
| 8083 | `ORGID_NOT_PRESENT_IN_THE_HEADER` — The `ZANALYTICS-ORGID` header is missing. | Add the header. |
| 8184 | `VIEW_OR_TAG_NOT_PRESENT_IN_DB_TO_TAG` — The tag does not exist in this workspace. | Verify `<tag-id>` with [Get Tags List](#1-get-tags-list). |
| 8507 | `MORE_THAN_MAX_LENGTH` — `CONFIG` exceeds 1,000 characters. | Send only `limit` and `offset`. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token carrying `ZohoAnalytics.metadata.read`. |

---

## 3. Get View Tags

Returns the tags attached to a given view.

| Attribute | Value |
|-----------|-------|
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/tags` |
| **HTTP Method** | `GET` |
| **OAuth Scope** | `ZohoAnalytics.metadata.read` |
| **Mandatory Header** | `ZANALYTICS-ORGID` |
| **CONFIG** | This API takes no CONFIG fields |
| **Success Status** | `200 OK` with a JSON body |

**Path parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `<workspace-id>` | Long | ID of the workspace that owns the view. |
| `<view-id>` | Long | ID of the view. Must belong to `<workspace-id>`. |

### Sample Requests

```http
GET /restapi/v2/workspaces/320873000000419001/views/20867000000038313/tags HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

### Sample Responses

**HTTP 200 OK — a view carrying four tags**

```json
{
  "status": "success",
  "summary": "Get view tags",
  "data": {
    "tags": [
      {
        "id": "320873000000425158",
        "name": "Tag_AccountAdmin_1_Updated",
        "colorCode": "#e72d35"
      },
      {
        "id": "320873000000419779",
        "name": "Tag_AccountAdmin_2",
        "colorCode": "#f5a623"
      },
      {
        "id": "320873000000421641",
        "name": "Tag_OrgAdmin_1_Updated",
        "colorCode": "#55acee"
      },
      {
        "id": "320873000000424199",
        "name": "Tag_WkAdmin_1_Updated",
        "colorCode": "#f5a623"
      }
    ]
  }
}
```

**HTTP 200 OK — an untagged view**

```json
{
  "status": "success",
  "summary": "Get view tags",
  "data": {
    "tags": []
  }
}
```

This is what [Remove Multiple Tags From View](#10-remove-multiple-tags-from-view) with `dissociateAll: true` leaves behind.

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | String | `"success"` on success. |
| `summary` | String | `"Get view tags"`. |
| `data` | Object | Wrapper. |
| `data.tags` | Array | Tags attached to the view — at most 10 entries. Empty when the view is untagged. |
| `data.tags[].id` | String | ID of the tag, **as a string**. |
| `data.tags[].name` | String | Display name of the tag. |
| `data.tags[].colorCode` | String | Hex colour of the tag. |

### Notes & Behaviour

| Behaviour | Detail |
|-----------|--------|
| **The array length is the current tag count** | Count it before calling [Add Multiple Tags To View](#9-add-multiple-tags-to-view) to know how many of the ten slots remain, rather than catching `8181`. |
| **It needs only Read permission on the view** | Narrower than the workspace-wide check the other two read APIs use, but still open to any shared user who can open the view. |
| **The response shape is identical to [Get Tags List](#1-get-tags-list)** | Same `tags[]` array, same three fields. Only the `summary` and the scope of the result differ. |
| **It is the inverse of [Get Tagged Views](#2-get-tagged-views)** | Same association table, read from the other end. |
| **There is no pagination** | The ten-tag ceiling makes it unnecessary. |
| **The view must belong to the workspace in the path** | A view ID from another workspace is rejected. |
| **Dependency chain:** | [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) or [Get Tagged Views](#2-get-tagged-views) → `<view-id>` → Get View Tags → `tags[].id`. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7104 | `META_OBJECT_NOT_PRESENT` — The view does not exist. | Verify `<view-id>` with [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list). |
| 7301 | `SECURITY_NOT_PERMITTED` — The caller lacks Read permission on the view, or the view does not belong to `<workspace-id>`. | Ensure the view is shared with the calling user. |
| 7390 | `WORKSPACE_NOT_BELONGS_TO_ORG` — The workspace does not belong to the organization in `ZANALYTICS-ORGID`. | Send the organization ID that owns the workspace. |
| 8083 | `ORGID_NOT_PRESENT_IN_THE_HEADER` — The `ZANALYTICS-ORGID` header is missing. | Add the header. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token carrying `ZohoAnalytics.metadata.read`. |

---

## 4. Create Tag

Creates one tag in the workspace.

| Attribute | Value |
|-----------|-------|
| **URL** | `/restapi/v2/workspaces/<workspace-id>/tags` |
| **HTTP Method** | `POST` |
| **OAuth Scope** | `ZohoAnalytics.modeling.create` |
| **Mandatory Header** | `ZANALYTICS-ORGID` |
| **CONFIG** | **Mandatory** |
| **Success Status** | `200 OK` with a JSON body carrying `data.tagId` |

**Path parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `<workspace-id>` | Long | ID of the workspace the tag is created in. |

### CONFIG Parameters

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | String | **Yes** | — | Display name of the tag, 1–100 characters. Must be unique within the workspace, otherwise `8174`. |
| `colorCode` | String | **Yes** | — | Hex colour, `#RRGGBB` or `#RGB`. See [The `colorCode` Attribute](#the-colorcode-attribute). |

### Sample Requests

**Case 1 — a tag with a six-digit colour**

```http
POST /restapi/v2/workspaces/320873000000419001/tags HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded
```

```json
{
  "name": "Tag_AccountAdmin_1",
  "colorCode": "#55acee"
}
```

**Case 2 — a second tag in the same workspace**

Names must differ; colours need not.

```json
{
  "name": "Tag_AccountAdmin_2",
  "colorCode": "#f5a623"
}
```

**Case 3 — the three-digit colour form**

```json
{
  "name": "Finance",
  "colorCode": "#1da"
}
```

### Sample Responses

**HTTP 200 OK — the tag was created**

```json
{
  "status": "success",
  "summary": "Create Tag",
  "data": {
    "tagId": "20867000000038794"
  }
}
```

**HTTP 403 Forbidden — the name is already taken in this workspace**

```json
{
  "status": "failure",
  "summary": "DUPLICATE_TAG_NAME_FOUND",
  "data": {
    "errorCode": 8174,
    "errorMessage": "Duplicate tag found. Kindly Check the tags given."
  }
}
```

**HTTP 403 Forbidden — the caller is not an administrator**

```json
{
  "status": "failure",
  "summary": "DONT_HAVE_PERMISSION_TO_CREATE_TAGS",
  "data": {
    "errorCode": 8179,
    "errorMessage": "You don't have permission to create new tag."
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | String | `"success"` on success. |
| `summary` | String | `"Create Tag"` — note the capital `T`, unlike the lower-case summaries of the read APIs. |
| `data` | Object | Wrapper. |
| `data.tagId` | String | ID of the new tag, **as a string**. This is the only place it is returned; capture it. It becomes `<tag-id>` for [Get Tagged Views](#2-get-tagged-views), [Update Tag](#5-update-tag), [Delete Tag](#6-delete-tag), [Add Tag To Multiple Views](#7-add-tag-to-multiple-views), and [Remove Tag From Multiple Views](#8-remove-tag-from-multiple-views), and a `tagIds` entry for [Add Multiple Tags To View](#9-add-multiple-tags-to-view) and [Remove Multiple Tags From View](#10-remove-multiple-tags-from-view). |

### Notes & Behaviour

| Behaviour | Detail |
|-----------|--------|
| **The response key is `tagId`, not `id`** | The read APIs return the same value as `tags[].id`. The two names refer to the same thing. |
| **One tag per call** | There is no bulk-create variant. Creating twenty tags takes twenty calls. |
| **A created tag labels nothing** | Creation and association are separate steps. Follow with [Add Tag To Multiple Views](#7-add-tag-to-multiple-views) or [Add Multiple Tags To View](#9-add-multiple-tags-to-view). |
| **Name uniqueness is per workspace** | The same name may exist in two different workspaces as two unrelated tags. |
| **It is not an upsert** | Re-creating an existing name fails with `8174` rather than returning the existing tag. To find out whether a name is taken, read [Get Tags List](#1-get-tags-list) first. |
| **Both attributes are mandatory** | Unlike [Update Tag](#5-update-tag), which accepts either one alone. |
| **Dependency chain:** | Create Tag → `data.tagId` → [Add Tag To Multiple Views](#7-add-tag-to-multiple-views) → [Get Tagged Views](#2-get-tagged-views). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7103 | `META_OBJECT_NOT_PRESENT` — The workspace does not exist. | Verify `<workspace-id>`. |
| 7301 | `SECURITY_NOT_PERMITTED` — The caller cannot access the workspace. | Ensure the workspace is shared with the calling user. |
| 7390 | `WORKSPACE_NOT_BELONGS_TO_ORG` — The workspace does not belong to the organization in `ZANALYTICS-ORGID`. | Send the organization ID that owns the workspace. |
| 8079 | `ATTRIBUTE_NOT_PRESENT_IN_JSON_CONFIGURATION` — `name` or `colorCode` is missing. | The message names the attribute; both are mandatory. |
| 8083 | `ORGID_NOT_PRESENT_IN_THE_HEADER` — The `ZANALYTICS-ORGID` header is missing. | Add the header. |
| 8174 | `DUPLICATE_TAG_NAME_FOUND` — A tag with this name already exists in the workspace. | Choose a different name, or reuse the existing tag's ID. |
| 8179 | `DONT_HAVE_PERMISSION_TO_CREATE_TAGS` — The caller is not an Account Admin, Organization Admin, or Workspace Admin. | Call as an administrator of the workspace. |
| 8504 | `LESS_THAN_MIN_OCCURANCE` — `CONFIG` was not sent. | Send a CONFIG object containing `name` and `colorCode`. |
| 8507 | `MORE_THAN_MAX_LENGTH` — `name` exceeds 100 characters. | Shorten the name. |
| 8509 | `PATTERN_NOT_MATCHED` — `colorCode` is not a valid hex colour. | Send `#RRGGBB` or `#RGB`. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token carrying `ZohoAnalytics.modeling.create`. |

---

## 5. Update Tag

Renames a tag, recolours it, or both.

| Attribute | Value |
|-----------|-------|
| **URL** | `/restapi/v2/workspaces/<workspace-id>/tags/<tag-id>` |
| **HTTP Method** | `PUT` |
| **OAuth Scope** | `ZohoAnalytics.modeling.update` |
| **Mandatory Header** | `ZANALYTICS-ORGID` |
| **CONFIG** | **Mandatory** |
| **Success Status** | **`204 No Content`** — no response body |

**Path parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `<workspace-id>` | Long | ID of the workspace that owns the tag. |
| `<tag-id>` | Long | ID of the tag to update. Must exist in `<workspace-id>`, otherwise `8187`. |

### CONFIG Parameters

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | String | Conditional | unchanged | New display name, 1–100 characters. Must be unique within the workspace, otherwise `8174`. Omit to leave the name unchanged. |
| `colorCode` | String | Conditional | unchanged | New hex colour, `#RRGGBB` or `#RGB`. Omit to leave the colour unchanged. |

> **At least one of the two must be present.** Sending a CONFIG with neither — or with both empty — fails with `8182`. This is a genuine partial update: the attribute you omit is preserved, not reset.

### Sample Requests

**Case 1 — rename and recolour together**

```http
PUT /restapi/v2/workspaces/320873000000419001/tags/320873000000425158 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded
```

```json
{
  "name": "Tag_AccountAdmin_1_Updated",
  "colorCode": "#e72d35"
}
```

**Case 2 — recolour only, keeping the name**

```json
{
  "colorCode": "#1da043"
}
```

**Case 3 — rename only, keeping the colour**

```json
{
  "name": "Finance_Archive"
}
```

### Sample Responses

**HTTP 204 No Content — the tag was updated**

```
HTTP/1.1 204 No Content
```

There is no response body. Read the new values back with [Get Tags List](#1-get-tags-list).

**HTTP 400 Bad Request — neither attribute was supplied**

```json
{
  "status": "failure",
  "summary": "CANNOT_UPDATE_THE_TAG",
  "data": {
    "errorCode": 8182,
    "errorMessage": "You don't have permission to update a tag."
  }
}
```

Despite the wording of the message, this code is raised when the CONFIG carries nothing to change.

**HTTP 400 Bad Request — the tag does not exist**

```json
{
  "status": "failure",
  "summary": "TAG_NOT_PRESENT_IN_DB",
  "data": {
    "errorCode": 8187,
    "errorMessage": "Tag is not present in db to delete/update."
  }
}
```

### Response Fields

**None.** This API returns `204 No Content` with an empty body. Confirm the change with [Get Tags List](#1-get-tags-list).

### Notes & Behaviour

| Behaviour | Detail |
|-----------|--------|
| **It is a genuine partial update** | Omitted attributes keep their stored values. This is the opposite of most V2 update APIs, which replace the whole definition. |
| **Associations are untouched** | Every view tagged before the update is still tagged after it. Renaming is safe for existing links. |
| **The name uniqueness check still applies** | Renaming onto an existing name fails with `8174`. |
| **`8182` means "nothing to update", not a permission problem** | Its message text reads like a permission error, but a permission failure surfaces as `8179`. Check whether your CONFIG actually contained `name` or `colorCode`. |
| **Renaming to the current name is accepted** | It is not treated as a duplicate of itself. |
| **There is no bulk update** | One tag per call. |
| **Dependency chain:** | [Get Tags List](#1-get-tags-list) or [Create Tag](#4-create-tag) → `<tag-id>` → Update Tag → [Get Tags List](#1-get-tags-list) to verify. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7103 | `META_OBJECT_NOT_PRESENT` — The workspace does not exist. | Verify `<workspace-id>`. |
| 7301 | `SECURITY_NOT_PERMITTED` — The caller cannot access the workspace. | Ensure the workspace is shared with the calling user. |
| 7390 | `WORKSPACE_NOT_BELONGS_TO_ORG` — The workspace does not belong to the organization in `ZANALYTICS-ORGID`. | Send the organization ID that owns the workspace. |
| 8083 | `ORGID_NOT_PRESENT_IN_THE_HEADER` — The `ZANALYTICS-ORGID` header is missing. | Add the header. |
| 8174 | `DUPLICATE_TAG_NAME_FOUND` — Another tag in the workspace already uses this name. | Choose a different name. |
| 8179 | `DONT_HAVE_PERMISSION_TO_CREATE_TAGS` — The caller is not an Account Admin, Organization Admin, or Workspace Admin. | Call as an administrator of the workspace. |
| 8182 | `CANNOT_UPDATE_THE_TAG` — The CONFIG contained neither `name` nor `colorCode`. | Send at least one of the two. |
| 8185 | `CANNOT_DELETE_OR_UPDATE_TAG` — The update matched no row. | Verify `<tag-id>` with [Get Tags List](#1-get-tags-list). |
| 8187 | `TAG_NOT_PRESENT_IN_DB` — The tag does not exist in this workspace. | Verify `<tag-id>` with [Get Tags List](#1-get-tags-list). |
| 8504 | `LESS_THAN_MIN_OCCURANCE` — `CONFIG` was not sent. | Send a CONFIG object. |
| 8507 | `MORE_THAN_MAX_LENGTH` — `name` exceeds 100 characters. | Shorten the name. |
| 8509 | `PATTERN_NOT_MATCHED` — `colorCode` is not a valid hex colour. | Send `#RRGGBB` or `#RGB`. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token carrying `ZohoAnalytics.modeling.update`. |

---

## 6. Delete Tag

Deletes a tag and every association it has.

| Attribute | Value |
|-----------|-------|
| **URL** | `/restapi/v2/workspaces/<workspace-id>/tags/<tag-id>` |
| **HTTP Method** | `DELETE` |
| **OAuth Scope** | `ZohoAnalytics.modeling.delete` |
| **Mandatory Header** | `ZANALYTICS-ORGID` |
| **CONFIG** | This API takes no CONFIG fields |
| **Success Status** | **`204 No Content`** — no response body |

**Path parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `<workspace-id>` | Long | ID of the workspace that owns the tag. |
| `<tag-id>` | Long | ID of the tag to delete. Must exist in `<workspace-id>`. |

### Sample Requests

```http
DELETE /restapi/v2/workspaces/320873000000419001/tags/320873000000425158 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

There is nothing else to send.

### Sample Responses

**HTTP 204 No Content — the tag was deleted**

```
HTTP/1.1 204 No Content
```

**HTTP 200 OK — reading the tag list afterwards**

```json
{
  "status": "success",
  "summary": "Get tags",
  "data": {
    "tags": []
  }
}
```

**HTTP 403 Forbidden — the tag does not exist**

```json
{
  "status": "failure",
  "summary": "VIEW_OR_TAG_NOT_PRESENT_IN_DB_TO_TAG",
  "data": {
    "errorCode": 8184,
    "errorMessage": "View/Tag not present or duplicated in db."
  }
}
```

### Response Fields

**None.** This API returns `204 No Content` with an empty body. Confirm with [Get Tags List](#1-get-tags-list).

### Notes & Behaviour

| Behaviour | Detail |
|-----------|--------|
| **It cascades to every association** | Deleting a tag silently removes it from every view it labelled. The views themselves are untouched — only the label disappears. |
| **There is no confirmation and no undo** | The response does not report how many associations were removed, and the tag cannot be restored. Read [Get Tagged Views](#2-get-tagged-views) first if you need to know the blast radius. |
| **Re-creating the name afterwards produces a different tag** | The new tag gets a new `tagId` and carries none of the old associations. |
| **To keep the tag but clear its links** | Use [Remove Tag From Multiple Views](#8-remove-tag-from-multiple-views) with `dissociateAll: true` instead. It removes every association without deleting the tag. |
| **One tag per call** | There is no bulk-delete variant. |
| **Dependency chain:** | [Get Tags List](#1-get-tags-list) → `<tag-id>` → (optionally [Get Tagged Views](#2-get-tagged-views) to see what will be unlinked) → Delete Tag. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7103 | `META_OBJECT_NOT_PRESENT` — The workspace does not exist. | Verify `<workspace-id>`. |
| 7301 | `SECURITY_NOT_PERMITTED` — The caller cannot access the workspace. | Ensure the workspace is shared with the calling user. |
| 7390 | `WORKSPACE_NOT_BELONGS_TO_ORG` — The workspace does not belong to the organization in `ZANALYTICS-ORGID`. | Send the organization ID that owns the workspace. |
| 8083 | `ORGID_NOT_PRESENT_IN_THE_HEADER` — The `ZANALYTICS-ORGID` header is missing. | Add the header. |
| 8179 | `DONT_HAVE_PERMISSION_TO_CREATE_TAGS` — The caller is not an Account Admin, Organization Admin, or Workspace Admin. | Call as an administrator of the workspace. |
| 8184 | `VIEW_OR_TAG_NOT_PRESENT_IN_DB_TO_TAG` — The tag does not exist in this workspace. | Verify `<tag-id>` with [Get Tags List](#1-get-tags-list). |
| 8185 | `CANNOT_DELETE_OR_UPDATE_TAG` — The delete matched no row. | Verify `<tag-id>` with [Get Tags List](#1-get-tags-list). |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token carrying `ZohoAnalytics.modeling.delete`. |

---

## 7. Add Tag To Multiple Views

Attaches **one tag** to a batch of views.

| Attribute | Value |
|-----------|-------|
| **URL** | `/restapi/v2/workspaces/<workspace-id>/tags/<tag-id>/views` |
| **HTTP Method** | `POST` |
| **OAuth Scope** | `ZohoAnalytics.modeling.create` |
| **Mandatory Header** | `ZANALYTICS-ORGID` |
| **CONFIG** | **Mandatory** |
| **Success Status** | **`204 No Content`** — no response body |

**Path parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `<workspace-id>` | Long | ID of the workspace that owns both the tag and the views. |
| `<tag-id>` | Long | ID of the tag to attach. Must exist in `<workspace-id>`, otherwise `8184`. |

### CONFIG Parameters

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `viewIds` | JSONArray of Long | **Yes** | — | IDs of the views to attach the tag to, 1–1000 entries. Every ID must belong to `<workspace-id>`, otherwise `8184`. Duplicates within the array are collapsed. |

### Sample Requests

**Case 1 — attach the tag to one view**

```http
POST /restapi/v2/workspaces/320873000000419001/tags/320873000000425158/views HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded
```

```json
{
  "viewIds": ["20867000000038313"]
}
```

**Case 2 — attach it across a mixed batch of view types**

One call can span tables, dashboards, charts, and pivots.

```json
{
  "viewIds": [
    "20867000000038313",
    "20867000000038314",
    "20867000000038319",
    "20867000000038322"
  ]
}
```

### Sample Responses

**HTTP 204 No Content — the tag was attached**

```
HTTP/1.1 204 No Content
```

**HTTP 403 Forbidden — a view would exceed its ten-tag ceiling**

```json
{
  "status": "failure",
  "summary": "TAG_COUNT_EXCEEDS",
  "data": {
    "errorCode": 8181,
    "errorMessage": "Tags on the views [\"20867000000038314\"] exceeds allowed tag limit."
  }
}
```

The message names the offending views. Nothing was written for any view in the batch.

**HTTP 403 Forbidden — a read-only user attempted the call**

```json
{
  "status": "failure",
  "summary": "DONT_HAVE_PERMISSION_TO_ASSOCIATE_AND_UNASSOCIATE_TAGS",
  "data": {
    "errorCode": 8180,
    "errorMessage": "You don't have permission to associate/unassociate a tag."
  }
}
```

### Response Fields

**None.** This API returns `204 No Content` with an empty body. Confirm with [Get Tagged Views](#2-get-tagged-views).

### Notes & Behaviour

| Behaviour | Detail |
|-----------|--------|
| **It is idempotent per pair** | A `(view, tag)` pair that already exists is skipped rather than duplicated or rejected. Re-sending the same request is safe and still returns `204`. |
| **Duplicate IDs in `viewIds` are collapsed** | Sending the same view twice in one array counts once. |
| **The batch is all-or-nothing** | Validation — workspace membership, tag existence, and the ten-tag ceiling — runs across the whole batch before anything is written. One bad view ID means no view gets tagged. |
| **Administrators only** | Unlike its view-side counterpart [Add Multiple Tags To View](#9-add-multiple-tags-to-view), a View Owner cannot call this. See [The Two Sides of an Association](#the-two-sides-of-an-association). |
| **Read-only users are blocked outright** | `8180`, regardless of any other permission. |
| **`8184` covers two different mistakes** | Either the tag does not exist in the workspace, or one of the `viewIds` does not. The message does not distinguish them — verify both with [Get Tags List](#1-get-tags-list) and [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list). |
| **No count is returned** | The response does not say how many associations were new versus already present. |
| **Dependency chain:** | [Create Tag](#4-create-tag) → `<tag-id>`; [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → `viewIds` → Add Tag To Multiple Views → [Get Tagged Views](#2-get-tagged-views). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7103 | `META_OBJECT_NOT_PRESENT` — The workspace does not exist. | Verify `<workspace-id>`. |
| 7301 | `SECURITY_NOT_PERMITTED` — The caller is not an Account Admin, Organization Admin, or Workspace Admin. | Call as an administrator, or use [Add Multiple Tags To View](#9-add-multiple-tags-to-view) instead. |
| 7390 | `WORKSPACE_NOT_BELONGS_TO_ORG` — The workspace does not belong to the organization in `ZANALYTICS-ORGID`. | Send the organization ID that owns the workspace. |
| 8079 | `ATTRIBUTE_NOT_PRESENT_IN_JSON_CONFIGURATION` — `viewIds` is missing. | Send a `viewIds` array. |
| 8083 | `ORGID_NOT_PRESENT_IN_THE_HEADER` — The `ZANALYTICS-ORGID` header is missing. | Add the header. |
| 8180 | `DONT_HAVE_PERMISSION_TO_ASSOCIATE_AND_UNASSOCIATE_TAGS` — The caller is a read-only user. | Associations cannot be changed by read-only users. |
| 8181 | `TAG_COUNT_EXCEEDS` — One or more views would exceed 10 tags. The message lists them. | Remove tags from those views first, or drop them from the batch. |
| 8184 | `VIEW_OR_TAG_NOT_PRESENT_IN_DB_TO_TAG` — The tag or one of the views does not exist in this workspace. | Verify both sets of IDs. |
| 8504 | `LESS_THAN_MIN_OCCURANCE` — `CONFIG` was not sent, or `viewIds` is missing. | Send a CONFIG object containing `viewIds`. |
| 8507 | `MORE_THAN_MAX_LENGTH` — `viewIds` exceeds 50,000 characters. | Split the batch. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token carrying `ZohoAnalytics.modeling.create`. |
| 8547 | `ARRAY_SIZE_OUT_OF_RANGE` — `viewIds` is empty or exceeds 1000 entries. | Send between 1 and 1000 view IDs. |

---

## 8. Remove Tag From Multiple Views

Detaches **one tag** from a batch of views, or from every view at once.

| Attribute | Value |
|-----------|-------|
| **URL** | `/restapi/v2/workspaces/<workspace-id>/tags/<tag-id>/views` |
| **HTTP Method** | `DELETE` |
| **OAuth Scope** | `ZohoAnalytics.modeling.delete` |
| **Mandatory Header** | `ZANALYTICS-ORGID` |
| **CONFIG** | **Mandatory** |
| **Success Status** | **`204 No Content`** — no response body |

**Path parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `<workspace-id>` | Long | ID of the workspace that owns the tag and the views. |
| `<tag-id>` | Long | ID of the tag to detach. Must exist in `<workspace-id>`. |

### CONFIG Parameters

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `viewIds` | JSONArray of Long | Conditional | — | IDs of the views to detach the tag from, 1–1000 entries. **Required unless `dissociateAll` is `true`**; an empty or absent array with `dissociateAll` off fails with `8201`. |
| `dissociateAll` | Boolean | No | `false` | When `true`, the tag is detached from **every** view in the workspace and `viewIds` is ignored. |

> Exactly one of the two mechanisms applies. Either name the views, or set `dissociateAll` to `true`.

### Sample Requests

**Case 1 — detach the tag from named views**

```http
DELETE /restapi/v2/workspaces/320873000000419001/tags/320873000000425158/views HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded
```

```json
{
  "viewIds": ["20867000000038313"]
}
```

**Case 2 — detach the tag from every view, keeping the tag itself**

```json
{
  "dissociateAll": true
}
```

Afterwards [Get Tagged Views](#2-get-tagged-views) returns `{"views": []}`, and the tag is still listed by [Get Tags List](#1-get-tags-list).

**Case 3 — `dissociateAll` explicitly off, with named views**

Equivalent to Case 1; useful when the flag is always present in a generated payload.

```json
{
  "viewIds": ["20867000000038313"],
  "dissociateAll": false
}
```

### Sample Responses

**HTTP 204 No Content — the associations were removed**

```
HTTP/1.1 204 No Content
```

**HTTP 200 OK — reading the tagged views afterwards**

```json
{
  "status": "success",
  "summary": "Get tagged views",
  "data": {
    "views": []
  }
}
```

**HTTP 400 Bad Request — neither `viewIds` nor `dissociateAll` was usable**

```json
{
  "status": "failure",
  "summary": "INVALID_CONFIGURATION_REMOVE_VIEWS_LINKED_WITH_TAG",
  "data": {
    "errorCode": 8201,
    "errorMessage": "Invalid configuration. Kindly provide valid viewIds or set 'removeAll' to 'true' to remove all views linked with the tag."
  }
}
```

> The message text names `removeAll`; the attribute this API actually accepts is **`dissociateAll`**.

### Response Fields

**None.** This API returns `204 No Content` with an empty body. Confirm with [Get Tagged Views](#2-get-tagged-views).

### Notes & Behaviour

| Behaviour | Detail |
|-----------|--------|
| **The tag survives** | Only the links are removed. This is the difference from [Delete Tag](#6-delete-tag), which removes the tag as well. |
| **`dissociateAll` overrides `viewIds`** | When `true`, any `viewIds` sent alongside it is ignored and the tag is stripped from every view. |
| **`dissociateAll: true` has no scope limit** | It reaches every view in the workspace, including views the caller may not otherwise interact with. Confirm the blast radius with [Get Tagged Views](#2-get-tagged-views) first. |
| **Detaching a tag that was never attached is not an error** | The operation is defined by the end state, not by how many rows changed. |
| **Administrators only** | Same restriction as [Add Tag To Multiple Views](#7-add-tag-to-multiple-views); a View Owner must use [Remove Multiple Tags From View](#10-remove-multiple-tags-from-view). |
| **Read-only users are blocked outright** | `8180`. |
| **No count is returned** | The response does not report how many associations were removed. |
| **Dependency chain:** | [Get Tagged Views](#2-get-tagged-views) → `views[].id` → Remove Tag From Multiple Views → [Get Tagged Views](#2-get-tagged-views) to verify. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7103 | `META_OBJECT_NOT_PRESENT` — The workspace does not exist. | Verify `<workspace-id>`. |
| 7301 | `SECURITY_NOT_PERMITTED` — The caller is not an Account Admin, Organization Admin, or Workspace Admin. | Call as an administrator, or use [Remove Multiple Tags From View](#10-remove-multiple-tags-from-view) instead. |
| 7390 | `WORKSPACE_NOT_BELONGS_TO_ORG` — The workspace does not belong to the organization in `ZANALYTICS-ORGID`. | Send the organization ID that owns the workspace. |
| 8083 | `ORGID_NOT_PRESENT_IN_THE_HEADER` — The `ZANALYTICS-ORGID` header is missing. | Add the header. |
| 8180 | `DONT_HAVE_PERMISSION_TO_ASSOCIATE_AND_UNASSOCIATE_TAGS` — The caller is a read-only user. | Associations cannot be changed by read-only users. |
| 8184 | `VIEW_OR_TAG_NOT_PRESENT_IN_DB_TO_TAG` — The tag or one of the views does not exist in this workspace. | Verify both sets of IDs. |
| 8201 | `INVALID_CONFIGURATION_REMOVE_VIEWS_LINKED_WITH_TAG` — `viewIds` is empty or absent and `dissociateAll` is not `true`. | Send a non-empty `viewIds`, or set `dissociateAll` to `true`. |
| 8504 | `LESS_THAN_MIN_OCCURANCE` — `CONFIG` was not sent. | Send a CONFIG object. |
| 8507 | `MORE_THAN_MAX_LENGTH` — `viewIds` exceeds 50,000 characters. | Split the batch. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token carrying `ZohoAnalytics.modeling.delete`. |
| 8547 | `ARRAY_SIZE_OUT_OF_RANGE` — `viewIds` exceeds 1000 entries. | Send at most 1000 view IDs, or use `dissociateAll`. |

---

## 9. Add Multiple Tags To View

Attaches a batch of **tags** to one view.

| Attribute | Value |
|-----------|-------|
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/tags` |
| **HTTP Method** | `POST` |
| **OAuth Scope** | `ZohoAnalytics.modeling.create` |
| **Mandatory Header** | `ZANALYTICS-ORGID` |
| **CONFIG** | **Mandatory** |
| **Success Status** | **`204 No Content`** — no response body |

**Path parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `<workspace-id>` | Long | ID of the workspace that owns the view and the tags. |
| `<view-id>` | Long | ID of the view to tag. Must belong to `<workspace-id>`. |

### CONFIG Parameters

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `tagIds` | JSONArray of Long | **Yes** | — | IDs of the tags to attach, 1–1000 entries. Every tag must already exist in `<workspace-id>`, otherwise `8184`. Duplicates within the array are collapsed. |

> This API **cannot create tags**. It only links existing ones — create them first with [Create Tag](#4-create-tag).

### Sample Requests

**Case 1 — attach two existing tags to a view**

```http
POST /restapi/v2/workspaces/320873000000419001/views/20867000000038313/tags HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded
```

```json
{
  "tagIds": [
    "320873000000425158",
    "320873000000419779"
  ]
}
```

**Case 2 — attach a single tag**

```json
{
  "tagIds": ["320873000000421641"]
}
```

### Sample Responses

**HTTP 204 No Content — the tags were attached**

```
HTTP/1.1 204 No Content
```

**HTTP 403 Forbidden — the view would end up with more than ten tags**

```json
{
  "status": "failure",
  "summary": "TAG_COUNT_EXCEEDS",
  "data": {
    "errorCode": 8181,
    "errorMessage": "Tags on the views [\"20867000000038313\"] exceeds allowed tag limit."
  }
}
```

**HTTP 403 Forbidden — one of the tag IDs does not exist**

```json
{
  "status": "failure",
  "summary": "VIEW_OR_TAG_NOT_PRESENT_IN_DB_TO_TAG",
  "data": {
    "errorCode": 8184,
    "errorMessage": "View/Tag not present or duplicated in db."
  }
}
```

### Response Fields

**None.** This API returns `204 No Content` with an empty body. Confirm with [Get View Tags](#3-get-view-tags).

### Notes & Behaviour

| Behaviour | Detail |
|-----------|--------|
| **It is idempotent per pair** | Tags already on the view are skipped, not duplicated or rejected. Re-sending the same request returns `204`. |
| **Already-attached tags do not count against the ceiling** | Sending ten tags to a view that already carries five of them adds only the five new ones, and passes the limit check. |
| **The batch is all-or-nothing** | The ten-tag check and the existence checks run before anything is written. |
| **This is the API a non-admin should use** | The View Owner and anyone with Edit Design permission on the view can call it, which is not true of [Add Tag To Multiple Views](#7-add-tag-to-multiple-views). |
| **Read-only users are blocked outright** | `8180`, even if they own the view. |
| **Duplicate IDs in `tagIds` are collapsed** | Sending the same tag twice counts once. |
| **No count is returned** | The response does not say how many tags were newly attached. |
| **Dependency chain:** | [Get Tags List](#1-get-tags-list) → `tagIds`; [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → `<view-id>` → Add Multiple Tags To View → [Get View Tags](#3-get-view-tags). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7104 | `META_OBJECT_NOT_PRESENT` — The view does not exist. | Verify `<view-id>` with [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list). |
| 7301 | `SECURITY_NOT_PERMITTED` — The caller lacks Edit Design permission on the view, or the view does not belong to `<workspace-id>`. | Call as an administrator, the View Owner, or a user with Edit Design permission. |
| 7390 | `WORKSPACE_NOT_BELONGS_TO_ORG` — The workspace does not belong to the organization in `ZANALYTICS-ORGID`. | Send the organization ID that owns the workspace. |
| 8079 | `ATTRIBUTE_NOT_PRESENT_IN_JSON_CONFIGURATION` — `tagIds` is missing. | Send a `tagIds` array. |
| 8083 | `ORGID_NOT_PRESENT_IN_THE_HEADER` — The `ZANALYTICS-ORGID` header is missing. | Add the header. |
| 8180 | `DONT_HAVE_PERMISSION_TO_ASSOCIATE_AND_UNASSOCIATE_TAGS` — The caller is a read-only user. | Associations cannot be changed by read-only users. |
| 8181 | `TAG_COUNT_EXCEEDS` — The view would exceed 10 tags. | Remove some tags first, or send fewer. |
| 8184 | `VIEW_OR_TAG_NOT_PRESENT_IN_DB_TO_TAG` — One of the tags does not exist in this workspace. | Verify the IDs with [Get Tags List](#1-get-tags-list). Create missing tags with [Create Tag](#4-create-tag). |
| 8504 | `LESS_THAN_MIN_OCCURANCE` — `CONFIG` was not sent, or `tagIds` is missing. | Send a CONFIG object containing `tagIds`. |
| 8507 | `MORE_THAN_MAX_LENGTH` — `tagIds` exceeds 50,000 characters. | Split the batch. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token carrying `ZohoAnalytics.modeling.create`. |
| 8547 | `ARRAY_SIZE_OUT_OF_RANGE` — `tagIds` is empty or exceeds 1000 entries. | Send between 1 and 1000 tag IDs. |

---

## 10. Remove Multiple Tags From View

Detaches a batch of **tags** from one view, or clears the view entirely.

| Attribute | Value |
|-----------|-------|
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/tags` |
| **HTTP Method** | `DELETE` |
| **OAuth Scope** | `ZohoAnalytics.modeling.delete` |
| **Mandatory Header** | `ZANALYTICS-ORGID` |
| **CONFIG** | **Mandatory** |
| **Success Status** | **`204 No Content`** — no response body |

**Path parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `<workspace-id>` | Long | ID of the workspace that owns the view and the tags. |
| `<view-id>` | Long | ID of the view. Must belong to `<workspace-id>`. |

### CONFIG Parameters

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `tagIds` | JSONArray of Long | Conditional | — | IDs of the tags to detach, 1–1000 entries. **Required unless `dissociateAll` is `true`**; an empty or absent array with `dissociateAll` off fails with `8202`. |
| `dissociateAll` | Boolean | No | `false` | When `true`, **every** tag is detached from the view and `tagIds` is ignored. |

### Sample Requests

**Case 1 — detach one named tag**

```http
DELETE /restapi/v2/workspaces/320873000000419001/views/20867000000038313/tags HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded
```

```json
{
  "tagIds": ["320873000000419779"]
}
```

**Case 2 — clear every tag from the view**

```json
{
  "dissociateAll": true
}
```

**Case 3 — `dissociateAll` explicitly off, with named tags**

```json
{
  "tagIds": ["320873000000425158"],
  "dissociateAll": false
}
```

### Sample Responses

**HTTP 204 No Content — the tags were detached**

```
HTTP/1.1 204 No Content
```

**HTTP 200 OK — reading the view's tags afterwards**

```json
{
  "status": "success",
  "summary": "Get view tags",
  "data": {
    "tags": []
  }
}
```

**HTTP 400 Bad Request — neither `tagIds` nor `dissociateAll` was usable**

```json
{
  "status": "failure",
  "summary": "INVALID_CONFIGURATION_REMOVE_TAGS_FOR_VIEW",
  "data": {
    "errorCode": 8202,
    "errorMessage": "Invalid configuration. Kindly provide valid tagIds or set 'removeAll' to 'true' to remove all tags from the view."
  }
}
```

> The message text names `removeAll`; the attribute this API actually accepts is **`dissociateAll`**.

### Response Fields

**None.** This API returns `204 No Content` with an empty body. Confirm with [Get View Tags](#3-get-view-tags).

### Notes & Behaviour

| Behaviour | Detail |
|-----------|--------|
| **The tags survive** | Only this view's links are removed. The tags remain in the workspace and stay attached to every other view. |
| **`dissociateAll` overrides `tagIds`** | When `true`, any `tagIds` sent alongside it is ignored. |
| **`dissociateAll: true` is scoped to this one view** | Unlike its tag-side counterpart, the blast radius is a single view — which makes it the safe way to reset a view's labels. |
| **Detaching a tag that was not attached is not an error** | The operation is defined by the end state. |
| **It frees slots against the ten-tag ceiling** | Use it before [Add Multiple Tags To View](#9-add-multiple-tags-to-view) when a view is at the limit. |
| **The View Owner can call it** | Same permission rule as [Add Multiple Tags To View](#9-add-multiple-tags-to-view). |
| **Read-only users are blocked outright** | `8180`. |
| **Dependency chain:** | [Get View Tags](#3-get-view-tags) → `tags[].id` → Remove Multiple Tags From View → [Get View Tags](#3-get-view-tags) to verify. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7104 | `META_OBJECT_NOT_PRESENT` — The view does not exist. | Verify `<view-id>` with [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list). |
| 7301 | `SECURITY_NOT_PERMITTED` — The caller lacks Edit Design permission on the view, or the view does not belong to `<workspace-id>`. | Call as an administrator, the View Owner, or a user with Edit Design permission. |
| 7390 | `WORKSPACE_NOT_BELONGS_TO_ORG` — The workspace does not belong to the organization in `ZANALYTICS-ORGID`. | Send the organization ID that owns the workspace. |
| 8083 | `ORGID_NOT_PRESENT_IN_THE_HEADER` — The `ZANALYTICS-ORGID` header is missing. | Add the header. |
| 8180 | `DONT_HAVE_PERMISSION_TO_ASSOCIATE_AND_UNASSOCIATE_TAGS` — The caller is a read-only user. | Associations cannot be changed by read-only users. |
| 8184 | `VIEW_OR_TAG_NOT_PRESENT_IN_DB_TO_TAG` — One of the tags does not exist in this workspace. | Verify the IDs with [Get View Tags](#3-get-view-tags). |
| 8202 | `INVALID_CONFIGURATION_REMOVE_TAGS_FOR_VIEW` — `tagIds` is empty or absent and `dissociateAll` is not `true`. | Send a non-empty `tagIds`, or set `dissociateAll` to `true`. |
| 8504 | `LESS_THAN_MIN_OCCURANCE` — `CONFIG` was not sent. | Send a CONFIG object. |
| 8507 | `MORE_THAN_MAX_LENGTH` — `tagIds` exceeds 50,000 characters. | Split the batch. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token carrying `ZohoAnalytics.modeling.delete`. |
| 8547 | `ARRAY_SIZE_OUT_OF_RANGE` — `tagIds` exceeds 1000 entries. | Send at most 1000 tag IDs, or use `dissociateAll`. |

---

## Appendix A – Common HTTP Headers

| Header | Value | Required | Description |
|--------|-------|----------|-------------|
| `Authorization` | `Zoho-oauthtoken <oauth-token>` | **Mandatory** | OAuth 2.0 access token of the calling user, carrying the scope for the API being called — see [Appendix B](#appendix-b--oauth-scope-summary). |
| `ZANALYTICS-ORGID` | Organization ID string | **Mandatory** | Organization ID of the workspace. Required by all ten APIs. |
| `Content-Type` | `application/x-www-form-urlencoded` | Conditional | Required by the six APIs that carry a CONFIG body — 4, 5, 7, 8, 9, and 10. |

> **`ZANALYTICS-DEST-ORGID` is not used by any of these APIs.** That header applies only to cross-organization copy operations (Copy Workspace, [Copy Views](VIEW_OPERATIONS_API_DOC_INFO.md#2-copy-views), Copy Formulas), which target a destination organization.

The `CONFIG` JSON is sent as the URL-encoded value of a form parameter named `CONFIG` on `POST`, `PUT`, and `DELETE`:

```http
POST /restapi/v2/workspaces/320873000000419001/tags/320873000000425158/views HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG=%7B%22viewIds%22%3A%5B%2220867000000038313%22%5D%7D
```

The decoded `CONFIG` above is `{"viewIds":["20867000000038313"]}`.

On [Get Tagged Views](#2-get-tagged-views) — the one `GET` that accepts a CONFIG — it travels in the query string instead:

```http
GET /restapi/v2/workspaces/320873000000419001/tags/320873000000425158/views?CONFIG=%7B%22limit%22%3A10%2C%22offset%22%3A10%7D HTTP/1.1
```

---

## Appendix B – OAuth Scope Summary

| API | HTTP Method | Scope |
|-----|-------------|-------|
| Get Tags List | GET | `ZohoAnalytics.metadata.read` |
| Get Tagged Views | GET | `ZohoAnalytics.metadata.read` |
| Get View Tags | GET | `ZohoAnalytics.metadata.read` |
| Create Tag | POST | `ZohoAnalytics.modeling.create` |
| Update Tag | PUT | `ZohoAnalytics.modeling.update` |
| Delete Tag | DELETE | `ZohoAnalytics.modeling.delete` |
| Add Tag To Multiple Views | POST | `ZohoAnalytics.modeling.create` |
| Remove Tag From Multiple Views | DELETE | `ZohoAnalytics.modeling.delete` |
| Add Multiple Tags To View | POST | `ZohoAnalytics.modeling.create` |
| Remove Multiple Tags From View | DELETE | `ZohoAnalytics.modeling.delete` |

> **The family spans two scope groups.** Reading tags is `metadata`; changing them is `modeling`. An integration that both reads and writes tags therefore needs scopes from both groups — `ZohoAnalytics.metadata.read` plus the three `modeling` operations, or the broader `ZohoAnalytics.metadata.ALL` and `ZohoAnalytics.modeling.ALL`. The scope always follows the HTTP method, which is why attaching a tag is `create` and detaching one is `delete` even though neither creates nor deletes a tag object.

---

## Appendix C – API-Specific Notes and Behaviours

### Get Tags List

- **It is the cheapest way to resolve a tag name to an ID.** There is no lookup-by-name endpoint, so name-driven integrations list all tags and match client-side.
- **It shows tags, not usage.** A tag attached to nothing looks identical to one attached to five hundred views. Pair it with [Get Tagged Views](#2-get-tagged-views) if usage matters.
- **Readable by everyone with workspace access**, including custom roles — verified against real responses for account-admin, org-admin, workspace-admin, and custom-role callers, all identical.
- **Dependency chain:** Get Tags List → `tags[].id` → every tag-side API.

### Get Tagged Views

- **The result is permission-filtered, which makes it a poor audit tool.** A non-administrator sees only the tagged views shared with them, so "how many views carry this tag" can only be answered reliably by an administrator.
- **`limit` / `offset` paging is blind.** No total and no cursor come back, so you cannot tell whether another page exists without asking for one.
- **A missing tag raises `8184` rather than returning an empty list**, which distinguishes "tag gone" from "tag unused" — a useful signal worth branching on.
- **`type` is a name, never a number.** `Table`, `AnalysisView`, `Dashboard`, and so on — see [View `type` values](#view-type-values).
- **Dependency chain:** [Create Tag](#4-create-tag) / [Get Tags List](#1-get-tags-list) → `<tag-id>` → Get Tagged Views → `views[].id`.

### Get View Tags

- **It is the pre-flight check for the ten-tag ceiling.** The length of `tags[]` tells you how many slots are free before you call [Add Multiple Tags To View](#9-add-multiple-tags-to-view).
- **It needs only Read on the view**, so a shared user can always see how their view is labelled even when they cannot change it.
- **Its response shape is identical to [Get Tags List](#1-get-tags-list)**, so one parser serves both.
- **Dependency chain:** [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → `<view-id>` → Get View Tags → `tags[].id`.

### Create Tag

- **This is the only place a `tagId` is minted.** Capture `data.tagId` from the response; there is no create-and-associate shortcut.
- **The response key is `tagId` while every read API calls the same value `id`.** The inconsistency is real — normalise it in your client.
- **It is not idempotent and not an upsert.** Re-running a create script fails on the second pass with `8174` instead of quietly succeeding. Read [Get Tags List](#1-get-tags-list) first if your script must be re-runnable.
- **`summary` is `"Create Tag"` with a capital `T`**, unlike the lower-case summaries the read APIs return. Do not match on summary text.
- **Dependency chain:** Create Tag → `data.tagId` → [Add Tag To Multiple Views](#7-add-tag-to-multiple-views).

### Update Tag

- **It is one of the few genuine partial updates in the V2 surface.** Send only what changes; the rest is preserved. Most sibling update APIs replace the whole definition, so do not generalise this behaviour.
- **`8182` is misleadingly worded.** Its message reads as a permission denial, but it means the CONFIG had neither `name` nor `colorCode`. A real permission failure is `8179`.
- **Renaming never breaks associations.** The link is by ID, so every tagged view stays tagged.
- **Dependency chain:** [Get Tags List](#1-get-tags-list) → `<tag-id>` → Update Tag → [Get Tags List](#1-get-tags-list).

### Delete Tag

- **It is the only destructive API in the family**, and it cascades: the tag and all of its associations go together, with no report of how many links were removed.
- **Check the blast radius first.** [Get Tagged Views](#2-get-tagged-views) is the only way to see what will be unlinked, and it must be called before the delete.
- **If you only want to clear the links, this is the wrong API.** Use [Remove Tag From Multiple Views](#8-remove-tag-from-multiple-views) with `dissociateAll: true`.
- **Dependency chain:** [Get Tags List](#1-get-tags-list) → `<tag-id>` → [Get Tagged Views](#2-get-tagged-views) → Delete Tag.

### Add Tag To Multiple Views

- **Its permission rule is the trap in this family.** It needs workspace administration, so a View Owner cannot use it even on their own view. If your integration runs as a non-admin, use [Add Multiple Tags To View](#9-add-multiple-tags-to-view) instead — one call per view rather than one call per tag.
- **The batch is validated as a whole.** One bad view ID, or one view already at ten tags, and nothing is written for any view in the request.
- **It is safely re-runnable.** Existing pairs are skipped rather than rejected, so a retry after a network failure is harmless.
- **`8181` names the offending views in the error message**, which is what makes it recoverable — drop those views and resend.
- **Dependency chain:** [Create Tag](#4-create-tag) → `<tag-id>`; [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → `viewIds` → Add Tag To Multiple Views.

### Remove Tag From Multiple Views

- **`dissociateAll: true` is the widest-reaching operation here.** It strips the tag from every view in the workspace in one call, with no confirmation and no count returned. Treat it as a workspace-level action.
- **The error message tells you to use `removeAll`, which does not exist.** The attribute is `dissociateAll`; ignore the message text.
- **It is the non-destructive alternative to [Delete Tag](#6-delete-tag)** when you want to keep the tag for reuse.
- **Administrators only**, like its sibling.
- **Dependency chain:** [Get Tagged Views](#2-get-tagged-views) → `views[].id` → Remove Tag From Multiple Views.

### Add Multiple Tags To View

- **This is the API to reach for when the caller is not an administrator.** The View Owner and anyone with Edit Design permission can call it, which is the practical difference from [Add Tag To Multiple Views](#7-add-tag-to-multiple-views).
- **Already-attached tags are free.** They are skipped, and they do not count towards the ten-tag check — so re-sending a superset of the current tags is safe.
- **It cannot create tags.** Every ID in `tagIds` must already exist; a typo surfaces as `8184`, not as a silently created tag.
- **Read-only users are blocked even on views they own**, with `8180`.
- **Dependency chain:** [Get Tags List](#1-get-tags-list) → `tagIds` → Add Multiple Tags To View → [Get View Tags](#3-get-view-tags).

### Remove Multiple Tags From View

- **`dissociateAll: true` here is narrow and safe** — it clears one view — which is the opposite of the same flag on [Remove Tag From Multiple Views](#8-remove-tag-from-multiple-views). Read the endpoint, not just the flag.
- **It is how you make room at the ten-tag ceiling** before adding more.
- **The same `removeAll` wording bug appears in its error message**; the attribute is `dissociateAll`.
- **Dependency chain:** [Get View Tags](#3-get-view-tags) → `tags[].id` → Remove Multiple Tags From View.

---

## Appendix D – General Response Payload Notes

| Field / Behaviour | Detail |
|-------------------|--------|
| **Four APIs return a body, six return 204** | [Get Tags List](#1-get-tags-list), [Get Tagged Views](#2-get-tagged-views), [Get View Tags](#3-get-view-tags), and [Create Tag](#4-create-tag) return `200` with the standard envelope. The six mutating association and lifecycle APIs return `204 No Content` with an empty body. |
| **A 204 carries no confirmation of scope** | None of the six reports how many rows changed. Verification is always a follow-up read. |
| **Failure responses share one shape** | `{"status": "failure", "summary": "<ERROR_NAME>", "data": {"errorCode": <n>, "errorMessage": "<text>"}}`. `summary` on failure is the error's symbolic name (for example `TAG_COUNT_EXCEEDS`), not a localised sentence. |
| **Success `summary` values differ per API** | `"Get tags"`, `"Get tagged views"`, `"Get view tags"`, and `"Create Tag"`. Only the last is capitalised. Do not branch on summary text. |
| **Every value inside `data` is a string** | `id`, `tagId`, and `views[].id` are all JSON strings, never numbers, even though they are numerically longs. |
| **Empty collections are successes** | `{"tags": []}` and `{"views": []}` both come back with HTTP 200. They mean "nothing matched", never "not found". |
| **The two tag-shaped responses are interchangeable** | [Get Tags List](#1-get-tags-list) and [Get View Tags](#3-get-view-tags) both return `data.tags[]` with `id`, `name`, and `colorCode`. |
| **`colorCode` round-trips exactly** | It is returned in the same case and form it was stored in. |
| **Ordering is never guaranteed** | Neither `tags[]` nor `views[]` has a defined order. Sort client-side. |
| **There is no `count` field anywhere** | Neither read API reports a total, so array length is the only measure available. |

---

## Appendix E – Enum and Value Reference

**`type`** — returned by [Get Tagged Views](#2-get-tagged-views) as `views[].type`

| Value | View type |
|-------|-----------|
| `Table` | A table |
| `Report` | A tabular view |
| `AnalysisView` | A chart view |
| `Pivot` | A pivot view |
| `SummaryView` | A summary view |
| `TableView` | A table view |
| `QueryTable` | A query table |
| `Dashboard` | A dashboard |
| `WIDGET` | A dashboard widget |
| `Tab` | A dashboard tab |
| `PipelineTable` | A pipeline table |
| `DataModelObject` | A data model object |

**`colorCode`** — accepted by [Create Tag](#4-create-tag) and [Update Tag](#5-update-tag)

| Form | Example | Accepted |
|------|---------|:--------:|
| Six hex digits with `#` | `#e72d35` | ✓ |
| Three hex digits with `#` | `#f90` | ✓ |
| Colour keyword | `red` | – |
| Hex without `#` | `e72d35` | – |
| Eight hex digits with alpha | `#e72d35ff` | – |
| `rgb()` notation | `rgb(231,45,53)` | – |

**`dissociateAll`** — accepted by [Remove Tag From Multiple Views](#8-remove-tag-from-multiple-views) and [Remove Multiple Tags From View](#10-remove-multiple-tags-from-view), default `false`

| Value | Behaviour on Remove Tag From Multiple Views | Behaviour on Remove Multiple Tags From View |
|-------|--------------------|---------------------|
| `false` | Detach the tag from the views named in `viewIds`. | Detach the tags named in `tagIds` from the view. |
| `true` | Detach the tag from **every view in the workspace**; `viewIds` is ignored. | Detach **every tag** from this one view; `tagIds` is ignored. |

**`status`** — present on every response that has a body

| Value | Meaning |
|-------|---------|
| `success` | The request succeeded. |
| `failure` | The request failed; `data.errorCode` carries the reason. |

---

## Appendix F – CONFIG Attribute Availability by API

`✓` accepted, `–` not accepted by that API.

| Attribute | 1 Get Tags List | 2 Get Tagged Views | 3 Get View Tags | 4 Create Tag | 5 Update Tag | 6 Delete Tag | 7 Add Tag To Views | 8 Remove Tag From Views | 9 Add Tags To View | 10 Remove Tags From View |
|-----------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `name` | – | – | – | ✓ **mandatory** | ✓ conditional | – | – | – | – | – |
| `colorCode` | – | – | – | ✓ **mandatory** | ✓ conditional | – | – | – | – | – |
| `viewIds` | – | – | – | – | – | – | ✓ **mandatory** | ✓ conditional | – | – |
| `tagIds` | – | – | – | – | – | – | – | – | ✓ **mandatory** | ✓ conditional |
| `dissociateAll` | – | – | – | – | – | – | – | ✓ | – | ✓ |
| `limit` | – | ✓ | – | – | – | – | – | – | – | – |
| `offset` | – | ✓ | – | – | – | – | – | – | – | – |

[Get Tags List](#1-get-tags-list), [Get View Tags](#3-get-view-tags), and [Delete Tag](#6-delete-tag) take no CONFIG at all.

---

## Appendix G – Tag Object Model and Association Rules

**The tag object**

| Field | Type | Description |
|-------|------|-------------|
| `id` / `tagId` | String | Identifier of the tag. Returned as `tagId` by [Create Tag](#4-create-tag) and as `id` by the read APIs — the same value under two names. |
| `name` | String | Display name, 1–100 characters, unique within the workspace. |
| `colorCode` | String | Hex colour, `#RRGGBB` or `#RGB`. Presentation only. |

**Association rules**

1. A tag is **workspace-scoped**. It can only be attached to views in the same workspace; there is no cross-workspace or organization-wide tag.
2. A single view carries at most **10** tags.
3. A single tag may label any number of views, subject only to the 1000-per-request batch size.
4. Attaching an already-attached `(view, tag)` pair is a **no-op**, not an error.
5. Detaching a pair that was never attached is likewise a no-op.
6. Deleting a tag removes every association it had.
7. Deleting a view removes every association that view had.
8. Renaming or recolouring a tag leaves all associations intact.
9. Tags carry no permissions. Attaching one neither grants nor restricts access to the view.
