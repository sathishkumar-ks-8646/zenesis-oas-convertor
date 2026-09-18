# Zoho Analytics V2 REST API — Data Sync & Connectivity

This document covers the five REST APIs that manage the **datasources** of a workspace — the connections Zoho Analytics uses to pull data in from outside, the schedules that drive them, and the record of what the last pull actually did.

## What these APIs are for

Every table in Zoho Analytics that is not hand-built has a **datasource** behind it: a cloud database, a local database reached through Zoho Databridge, an FTP or web-hosted file, a cloud-storage bucket, a business application connected through an integration connector, a live-connect database, or a snapshot. These five APIs let you inspect those datasources, trigger a pull on demand, repair a connection whose credentials or host have changed, and read the outcome of the last pull.

They do **not** create datasources, and they do not load data supplied in the request. Creating a connection is done in the Zoho Analytics interface; pushing data into a table is [Synchronous Data Import](SYNC_DATA_IMPORT_API_DOC_INFO.md) or [Asynchronous & Batch Data Import](ASYNC_DATA_IMPORT_API_DOC_INFO.md).

| | Data sync (this document) | Data import |
|---|---|---|
| **Where the data comes from** | A datasource Zoho Analytics already knows about | The request payload |
| **Who initiates the transfer** | Zoho Analytics pulls | The caller pushes |
| **What you supply** | A datasource ID or view ID, and optionally credentials | The file or rows themselves |
| **Typical use** | "Refresh this table from its source, now" | "Load this file into a table" |

---

## Index

| # | API Name | Method | URL |
|---|----------|--------|-----|
| 1 | [Sync Data](#1-sync-data) | POST | `/restapi/v2/workspaces/<workspace-id>/datasources/<datasource-id>/sync` |
| 2 | [Refetch Data](#2-refetch-data) | POST | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/sync` |
| 3 | [Update Datasource Connection](#3-update-datasource-connection) | PUT | `/restapi/v2/workspaces/<workspace-id>/datasources/<datasource-id>` |
| 4 | [Get Datasources](#4-get-datasources) | GET | `/restapi/v2/workspaces/<workspace-id>/datasources` |
| 5 | [Get Last Import Details](#5-get-last-import-details) | GET | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/importdetails` |

> Notes that apply to all five APIs:
> - All require the `ZANALYTICS-ORGID` header.
> - All are **disabled in Client Portal / White Label request contexts.** A request arriving through a custom domain is rejected with `7301` before any business logic runs.
> - None of them creates a datasource. A connection must already exist.

---

## How the Five APIs Relate

[Get Datasources](#4-get-datasources) is the entry point: it is the only API that hands you a `datasourceId`, a `syncIntervalId`, and the `viewId` of every table each datasource feeds. Everything else consumes one of those three.

```
                       4. Get Datasources
                     (GET .../datasources)
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
   datasourceId          syncIntervalId          tableDetails[].viewId
        │                       │                       │
        ├───────────────────────┘                       │
        ▼                                               ▼
  1. Sync Data                                    2. Refetch Data
  (whole datasource,                              (one table only)
   optionally one interval)                             │
        │                                               │
        └───────────────────┬───────────────────────────┘
                            ▼
                 5. Get Last Import Details
              (GET .../views/<view-id>/importdetails)
                     — did the pull work?

  datasourceId ──► 3. Update Datasource Connection
                   (repair host / credentials, then sync again)
```

| Relationship | Detail |
|--------------|--------|
| **`datasourceId` has exactly one source** | It is returned only by [Get Datasources](#4-get-datasources), as `dataSources[].datasourceId`. It is the `<datasource-id>` for [Sync Data](#1-sync-data) and [Update Datasource Connection](#3-update-datasource-connection). No other API in the suite returns it. |
| **`syncIntervalId` also has exactly one source** | [Get Datasources](#4-get-datasources) returns it as `dataSources[].syncIntervals[].syncIntervalId`. It becomes **mandatory** for [Sync Data](#1-sync-data) as soon as a datasource has more than one sync interval. |
| **`viewId` comes from the datasource listing too** | `dataSources[].tableDetails[].viewId` (or `dataSources[].syncIntervals[].tableDetails[].viewId`) tells you which tables a datasource feeds. Those are the IDs [Refetch Data](#2-refetch-data) and [Get Last Import Details](#5-get-last-import-details) accept. [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) also returns view IDs, but it does not tell you which have a datasource behind them. |
| **Sync Data and Refetch Data work at different levels** | [Sync Data](#1-sync-data) pulls a **whole datasource** — every table it feeds. [Refetch Data](#2-refetch-data) pulls **one table**. See [Two Levels of Sync](#two-levels-of-sync). |
| **Neither sync API reports its outcome** | Both return `204` with no body. The only way to find out whether the pull succeeded is [Get Last Import Details](#5-get-last-import-details) for a table, or the `lastDataSyncStatus` fields from [Get Datasources](#4-get-datasources) for the datasource. |
| **Update Datasource Connection is the repair path** | When `lastDataSyncStatus` reports a connection failure, [Update Datasource Connection](#3-update-datasource-connection) is how you correct the host, port, or credentials — then re-run [Sync Data](#1-sync-data). It applies only to database-style connections; see its own section. |
| **The sync quota is shared and visible** | `syncUsed` and `totalSyncAllowed` from [Get Datasources](#4-get-datasources) report the manual-sync quota that [Sync Data](#1-sync-data) consumes. Read them before triggering a sync rather than catching `19000048`. |
| **Data arriving through these APIs is read back with the Row and Export APIs** | Once a sync lands, the data is ordinary table data — [Get Rows](ROW_API_DOC_INFO.md), [Export Data from a View](SYNC_DATA_EXPORT_API_DOC_INFO.md#1-export-data-from-a-view), and the reporting APIs all apply. |

### Typical sequences

**Refresh everything behind one datasource and confirm it worked**

```
Get Datasources → datasourceId, tableDetails[].viewId
   → Sync Data (204)
   → Get Last Import Details for each viewId → lastImportStatus
```

**Refresh a single table**

```
Get Datasources → tableDetails[].viewId
   → Refetch Data (204)
   → Get Last Import Details → lastImportStatus, rows.success
```

**A connection has started failing**

```
Get Datasources → lastDataSyncStatus reports a failure
   → Update Datasource Connection (new host / credentials, 204)
   → Sync Data (204)
   → Get Last Import Details → confirm recovery
```

**A datasource with several schedules**

```
Get Datasources → syncIntervals[].syncIntervalId
   → Sync Data with {"syncIntervalId": "..."}   ← mandatory here
```

---

## Two Levels of Sync

[Sync Data](#1-sync-data) and [Refetch Data](#2-refetch-data) look similar and are not interchangeable.

| | [Sync Data](#1-sync-data) | [Refetch Data](#2-refetch-data) |
|---|---|---|
| **Addressed by** | `<datasource-id>` | `<view-id>` |
| **Scope** | The whole datasource — every table it feeds | One table |
| **Multiple schedules** | Can target one via `syncIntervalId`; mandatory when more than one exists | Not applicable |
| **Incremental vs full** | Follows the datasource's own configuration | Selectable with `isFullFetch` |
| **Consumes the manual-sync quota** | Yes | Yes |
| **Permission** | Create Table **or** Sync Data on the workspace | Sync Data on the workspace, or ownership of the view |
| **Typical use** | Scheduled refresh triggered early | One table is stale or failed while others succeeded |

> If a table has no datasource behind it — a hand-built table, or one loaded only by the import APIs — [Refetch Data](#2-refetch-data) fails with `18056`. There is nothing to refetch from.

---

## Source Types

The shape of a datasource entry, and which APIs apply to it, depend on what kind of source it is.

| Source family | Examples | Has `datasourceId` | `syncIntervals` | Updatable by [Update Datasource Connection](#3-update-datasource-connection) |
|---------------|----------|:------------------:|:---------------:|:----------------------------:|
| **Cloud / local databases** | Amazon RDS, Redshift, Azure SQL, Snowflake, BigQuery, Athena, MongoDB Atlas, Databricks | ✓ | ✓ | ✓ |
| **Analytics / data-lake tables, OData, Elasticsearch, local files** | Zoho Analytics workspace tables, OData feeds, data-lake tables | ✓ | ✓ | – |
| **Live Connect** | A database queried live rather than imported | ✓ | – | ✓ (credentials only) |
| **File and web sources** | FTP / SFTP, web URL, cloud storage, MS Access, workbooks | ✓ | – | – |
| **Integration connectors** | Zoho CRM, Zoho Desk, Google Analytics, Salesforce and similar | ✓ | – | – |
| **Local drive uploads** | Files uploaded from a desktop | – | – | – |
| **Snapshots** | A point-in-time copy of another table | – | – | – |

Local-drive and snapshot entries appear in [Get Datasources](#4-get-datasources) with a name and their table list only — they carry no `datasourceId`, so neither [Sync Data](#1-sync-data) nor [Update Datasource Connection](#3-update-datasource-connection) can address them.

---

## Limitations

These are the limits that apply with **default settings**.

| Limitation | Value | Enforced by |
|------------|-------|-------------|
| **Manual syncs per datasource connection** | **5 per day.** The counter resets daily and is reported as `syncUsed` against `totalSyncAllowed` by [Get Datasources](#4-get-datasources). Both [Sync Data](#1-sync-data) and [Refetch Data](#2-refetch-data) consume it. | `19000048` |
| **One sync at a time per table** | A table already being synced cannot be synced again until the current run finishes. | `18072` |
| **Repeated rapid calls are throttled** | [Sync Data](#1-sync-data) and [Refetch Data](#2-refetch-data) are additionally rate limited per user. A burst of calls in quick succession is locked out for a short cool-off period. | Framework-level rejection |
| **`syncIntervalId` becomes mandatory above one interval** | A datasource with more than one sync interval cannot be synced as a whole. | `8182` |
| **`CONFIG` length — Sync Data / Refetch Data** | **3,000** characters. | `8507` |
| **`CONFIG` length — Update Datasource Connection** | **1,000,000** characters. | `8507` |
| **`userName`, `password` length** | **1,000** characters. | `8507` |
| **`hostName`, `instanceName`, `warehouseName`, `projectId`, `cloudDatabaseName`, `schemaName`, `s3OutputLocation`, SSH tunnel fields** | **10,000** characters each. | `8507` |
| **`connectionString` length** | **20,000** characters. | `8507` |
| **`catalogName`, `workgroupName` length** | **150** characters each. | `8507` |
| **`dataLocation` length** | **30** characters. | `8507` |
| **Datasource creation** | **Not supported by any API in this document.** Connections are created in the Zoho Analytics interface. | — |
| **Client Portal / White Label** | All five APIs are unavailable through a custom domain. | `7301` |

> **Read the quota before spending it.** `syncUsed` and `totalSyncAllowed` are returned by [Get Datasources](#4-get-datasources) for every connection. Checking them is cheaper than discovering the limit through `19000048`, and it is the only way to know how many manual syncs remain today.

---

## Permission Model

| API | Who may call it |
|-----|-----------------|
| [Sync Data](#1-sync-data) | An Account Admin or Organization Admin, or a Workspace Admin, or any user with **Create Table** or **Sync Data** permission on the workspace. |
| [Refetch Data](#2-refetch-data) | An Account Admin or Organization Admin, or a Workspace Admin, or the View Owner, or any user with **Sync Data** permission on the workspace. |
| [Update Datasource Connection](#3-update-datasource-connection) | An Account Admin or Organization Admin, or a Workspace Admin, or any user with **Create Table** or **Edit Datasource** permission on the workspace. |
| [Get Datasources](#4-get-datasources) | An Account Admin or Organization Admin, or a Workspace Admin, or any user with **View Datasource** or **Create Table** permission on the workspace. |
| [Get Last Import Details](#5-get-last-import-details) | An Account Admin or Organization Admin, or a Workspace Admin, or the View Owner, or any user with **View Datasource** or an import permission on the view. |

One further gate applies to every API here:

| Gate | Behaviour |
|------|-----------|
| **Client Portal / White Label** | All five are unavailable through a custom domain and are rejected with `7301` before the permission check runs. |

> **View Datasource is narrower than Create Table.** A caller holding only **Create Table** gets the datasource list, but connection details belonging to sources they did not create are filtered out. Grant **View Datasource** for a complete listing.

---

## 1. Sync Data

Triggers an immediate pull for a whole datasource — every table it feeds.

| Attribute | Value |
|-----------|-------|
| **URL** | `/restapi/v2/workspaces/<workspace-id>/datasources/<datasource-id>/sync` |
| **HTTP Method** | `POST` |
| **OAuth Scope** | `ZohoAnalytics.metadata.create` |
| **Mandatory Header** | `ZANALYTICS-ORGID` |
| **CONFIG** | Optional |
| **Success Status** | **`204 No Content`** — no response body |

**Path parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `<workspace-id>` | Long | ID of the workspace that owns the datasource. |
| `<datasource-id>` | Long | `dataSources[].datasourceId` from [Get Datasources](#4-get-datasources). |

### CONFIG Parameters

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `syncIntervalId` | Long | Conditional | — | Targets one sync interval of the datasource. **Mandatory when the datasource has more than one sync interval**, otherwise the call fails with `8182`. Omit for a single-interval datasource. An ID that belongs to a different datasource fails with `8183`. Obtain it from `dataSources[].syncIntervals[].syncIntervalId`. |
| `userName` | String | Conditional | — | Username for the source, up to 1,000 characters. Required only for sources that ask for credentials at fetch time — FTP/SFTP-hosted workbooks and MS Access sources. Ignored by every other source type. |
| `password` | String | Conditional | — | Password matching `userName`, up to 1,000 characters. |

> `isFullFetch` is not read by this API. Whether a pull is incremental or complete follows the datasource's own configuration. To choose explicitly, use [Refetch Data](#2-refetch-data) on the individual table.

### Sample Requests

**Case 1 — a single-interval datasource, no CONFIG at all**

```http
POST /restapi/v2/workspaces/466206000000071000/datasources/466206000000081000/sync HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

Most datasources need nothing beyond the path.

**Case 2 — a datasource with several sync intervals**

```http
POST /restapi/v2/workspaces/466206000000071000/datasources/466206000000081000/sync HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"syncIntervalId":"466206000000082000"}
```

Without `syncIntervalId` this same call fails with `8182`.

**Case 3 — an FTP-hosted workbook that asks for credentials**

```http
POST /restapi/v2/workspaces/466206000000071000/datasources/466206000000081500/sync HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"userName":"zylker_ftp","password":"Zoho@123"}
```

### Sample Responses

**HTTP 204 No Content — the sync was initiated**

```
HTTP/1.1 204 No Content
```

There is no response body. A `204` means the pull has been **started**, not that it has finished or succeeded.

**HTTP 403 Forbidden — the datasource has several intervals and none was named**

```json
{
  "status": "failure",
  "summary": "SYNC_CANNOT_BE_INITIATED_FOR_CONNECTOR_WITH_MULTIPLE_SCHEDULES",
  "data": {
    "errorCode": 8182,
    "errorMessage": "Sync cannot be initiated for a datasource with multiple schedules. Provide a syncIntervalId."
  }
}
```

**HTTP 400 Bad Request — the daily manual-sync quota is exhausted**

```json
{
  "status": "failure",
  "summary": "CONN_SYNCNOW_CNT_EXCEEDED",
  "data": {
    "errorCode": 19000048,
    "errorMessage": "You have exceeded the maximum number of manual syncs allowed for this connection."
  }
}
```

### Response Fields

**None.** This API returns `204 No Content` with an empty body. To learn what the sync did, call [Get Last Import Details](#5-get-last-import-details) for a table it feeds, or re-read `lastDataSyncStatus` from [Get Datasources](#4-get-datasources).

### Notes & Behaviour

| Behaviour | Detail |
|-----------|--------|
| **204 means "started", not "finished"** | The pull runs in the background. A datasource with many tables may still be loading long after the response has been returned. |
| **There is no job ID and no polling endpoint** | Unlike the import and export job APIs, the sync APIs expose no handle on the run. Progress is observed through the table's import details. |
| **It consumes the daily manual-sync quota** | Five per connection per day; the counter resets daily. Check `syncUsed` against `totalSyncAllowed` first. |
| **`syncIntervalId` is conditionally mandatory** | Its necessity depends on the datasource's configuration, not on anything in the request. Read `syncIntervals` from [Get Datasources](#4-get-datasources) to know which case you are in. |
| **`CONFIG` is optional** | For a single-interval datasource that stores its own credentials — the common case — the path alone is enough. |
| **`userName` and `password` are for the source, not for Zoho Analytics** | They are the credentials of the FTP server or MS Access file being fetched. They are treated as sensitive and excluded from request logging. |
| **It cannot address local-drive uploads or snapshots** | Those entries carry no `datasourceId`. A snapshot is refreshed with [Refetch Data](#2-refetch-data) on its target table. |
| **A datasource ID from another workspace fails** | `18061`. IDs are not portable between workspaces. |
| **Dependency chain:** | [Get Datasources](#4-get-datasources) → `datasourceId` (+ `syncIntervalId` when present) → Sync Data → [Get Last Import Details](#5-get-last-import-details). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7301 | `SECURITY_NOT_PERMITTED` — The request came through a Client Portal / White Label domain, or the caller lacks Create Table and Sync Data permission on the workspace. | Call from the standard API host with one of the two permissions. |
| 8079 | `ATTRIBUTE_NOT_PRESENT_IN_JSON_CONFIGURATION` — A mandatory attribute is missing. | The message names the attribute. |
| 8182 | `SYNC_CANNOT_BE_INITIATED_FOR_CONNECTOR_WITH_MULTIPLE_SCHEDULES` — The datasource has more than one sync interval and none was named. | Send `syncIntervalId`; read the options from [Get Datasources](#4-get-datasources). |
| 8183 | `SCHEDULE_ID_NOT_ASSOCIATED_WITH_CONNECTOR` — The `syncIntervalId` does not belong to this datasource. | Use a `syncIntervalId` listed under this datasource's `syncIntervals`. |
| 8507 | `MORE_THAN_MAX_LENGTH` — `CONFIG` exceeds 3,000 characters, or a credential exceeds 1,000. | Shorten the value. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token carrying `ZohoAnalytics.metadata.create`. |
| 18061 | `CONNECTION_ID_NOT_ASSOSIATED_FOR_WORKSPACE` — The datasource ID does not exist in this workspace, or the source type cannot be synced this way (HTTP 404). | Verify `<datasource-id>` with [Get Datasources](#4-get-datasources). |
| 18073 | `DATASOURCE_SYNC_INPROGRESS` — A sync for this datasource is already running. | Wait for the running sync to finish. |
| 19000048 | `CONN_SYNCNOW_CNT_EXCEEDED` — The daily manual-sync quota for this connection is exhausted. | Wait for the daily reset, or rely on the configured schedule. |

---

## 2. Refetch Data

Triggers an immediate pull for **one table** from whatever datasource sits behind it.

| Attribute | Value |
|-----------|-------|
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/sync` |
| **HTTP Method** | `POST` |
| **OAuth Scope** | `ZohoAnalytics.metadata.create` |
| **Mandatory Header** | `ZANALYTICS-ORGID` |
| **CONFIG** | Optional |
| **Success Status** | **`204 No Content`** — no response body |

**Path parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `<workspace-id>` | Long | ID of the workspace that owns the view. |
| `<view-id>` | Long | ID of the table to refresh. Must belong to `<workspace-id>` and must have a datasource behind it. |

### CONFIG Parameters

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `isFullFetch` | Boolean | No | `false` | Selects the fetch mode for database-backed tables — cloud and local databases, OData feeds, local files, Analytics-workspace tables, Elasticsearch, and data-lake tables. `false` fetches only what has changed since the last pull; `true` re-reads the source completely. Ignored by file, web, connector, and snapshot sources, which always fetch in full. |
| `userName` | String | Conditional | — | Username for the source, up to 1,000 characters. Required only for FTP/SFTP and web-hosted files whose credentials are not stored with the source. |
| `password` | String | Conditional | — | Password matching `userName`, up to 1,000 characters. |

> `syncIntervalId` is not read by this API. A table belongs to exactly one interval, so there is nothing to choose.

### Sample Requests

**Case 1 — refresh one table, stored credentials, incremental**

```http
POST /restapi/v2/workspaces/466206000000071000/views/466206000000072000/sync HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — a full re-read of a cloud-database table**

```http
POST /restapi/v2/workspaces/466206000000071000/views/466206000000072000/sync HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"isFullFetch":true}
```

Use this when incremental fetches have drifted from the source — for example after rows were deleted at the source, which an incremental pull will not notice.

**Case 3 — a web-hosted file behind basic authentication**

```http
POST /restapi/v2/workspaces/466206000000071000/views/466206000000072500/sync HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"userName":"zylker_web","password":"Zoho@123"}
```

### Sample Responses

**HTTP 204 No Content — the refetch was initiated**

```
HTTP/1.1 204 No Content
```

**HTTP 400 Bad Request — the table has no datasource**

```json
{
  "status": "failure",
  "summary": "NO_SOURCE_AVAILABLE_FOR_TABLE",
  "data": {
    "errorCode": 18056,
    "errorMessage": "No source is available for this table."
  }
}
```

**HTTP 400 Bad Request — a sync for this table is already running**

```json
{
  "status": "failure",
  "summary": "TABLE_SYNC_INPROGRESS",
  "data": {
    "errorCode": 18072,
    "errorMessage": "A sync is already in progress for this table."
  }
}
```

### Response Fields

**None.** This API returns `204 No Content` with an empty body. Call [Get Last Import Details](#5-get-last-import-details) on the same `<view-id>` to see what the refetch did.

### Notes & Behaviour

| Behaviour | Detail |
|-----------|--------|
| **204 means "started", not "finished"** | The pull runs in the background; the response says nothing about rows loaded. |
| **`isFullFetch` only applies to database-style sources** | For file, web, connector, and snapshot sources every fetch is a full one, and the attribute has no effect. |
| **`isFullFetch` defaults to incremental** | Sending no CONFIG is equivalent to `{"isFullFetch": false}`. |
| **An incremental fetch will not notice deletions at the source** | Rows removed upstream stay in the Zoho Analytics table until a full fetch replaces the data. This is the main reason to send `isFullFetch: true`. |
| **One refetch at a time per table** | A second call while the first is running fails with `18072`, not a queue. |
| **A table without a datasource cannot be refetched** | `18056`. Hand-built tables and tables loaded only by the import APIs have nothing to pull from. |
| **It consumes the daily manual-sync quota** | The same five-per-connection-per-day allowance that [Sync Data](#1-sync-data) draws on. |
| **A snapshot table is refreshed here** | Snapshot entries carry no `datasourceId`, so [Sync Data](#1-sync-data) cannot address them; refetching the target table re-runs the snapshot. |
| **The view must belong to the workspace in the path** | A view ID from a different workspace is rejected. |
| **Dependency chain:** | [Get Datasources](#4-get-datasources) → `tableDetails[].viewId` → Refetch Data → [Get Last Import Details](#5-get-last-import-details). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7104 | `META_OBJECT_NOT_PRESENT` — The view does not exist. | Verify `<view-id>` with [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list). |
| 7301 | `SECURITY_NOT_PERMITTED` — The request came through a Client Portal / White Label domain, or the caller is neither an admin nor the View Owner and lacks Sync Data permission. | Call from the standard API host with the required permission. |
| 8507 | `MORE_THAN_MAX_LENGTH` — `CONFIG` exceeds 3,000 characters, or a credential exceeds 1,000. | Shorten the value. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token carrying `ZohoAnalytics.metadata.create`. |
| 18056 | `NO_SOURCE_AVAILABLE_FOR_TABLE` — The table has no datasource behind it. | Refetch only tables fed by a datasource; use the import APIs otherwise. |
| 18072 | `TABLE_SYNC_INPROGRESS` — A sync for this table is already running. | Wait for it to finish, then retry. |
| 19000048 | `CONN_SYNCNOW_CNT_EXCEEDED` — The daily manual-sync quota for this connection is exhausted. | Wait for the daily reset, or rely on the configured schedule. |

---

## 3. Update Datasource Connection

Updates the connection details of a **database-style datasource** — host, port, credentials, and the service-specific settings that go with them.

| Attribute | Value |
|-----------|-------|
| **URL** | `/restapi/v2/workspaces/<workspace-id>/datasources/<datasource-id>` |
| **HTTP Method** | `PUT` |
| **OAuth Scope** | `ZohoAnalytics.metadata.update` |
| **Mandatory Header** | `ZANALYTICS-ORGID` |
| **CONFIG** | **Mandatory** |
| **Success Status** | **`204 No Content`** — no response body |

**Path parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `<workspace-id>` | Long | ID of the workspace that owns the datasource. |
| `<datasource-id>` | Long | `dataSources[].datasourceId` of a **database** connection. |

> **This API applies only to database connections** — cloud databases, local databases reached through Zoho Databridge, and Live Connect databases. File, web, cloud-storage, integration-connector, snapshot, and local-drive datasources are not editable through it, and a `datasourceId` belonging to one of those is rejected with `18061`.

### CONFIG Parameters

**Always required**

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `serviceName` | String | **Yes** | The cloud service hosting the database. See [`serviceName` values](#servicename-values). An unrecognised value fails with `18057`. |
| `hostName` | String | **Yes** | Service endpoint or hostname, up to 10,000 characters. For **AMAZON ATHENA** send the AWS region instead; for **SNOWFLAKE** send the full account name. |
| `userName` | String | **Yes** | Login username for the database, up to 1,000 characters. |

**Commonly required**

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `databaseType` | String | Conditional | — | The database engine. **Mandatory whenever the chosen `serviceName` supports more than one engine**, otherwise `8079`. Omit only when the service has exactly one. A combination that does not exist fails with `18055`. |
| `password` | String | No | — | Login password, up to 1,000 characters. Omit to leave the stored password unchanged. |
| `port` | Long | No | Engine default | Database port. When omitted, the default port of the chosen `databaseType` is used. |
| `cloudDatabaseName` | String | No | — | Name of the database on the service, up to 10,000 characters. |
| `instanceName` | String | No | — | For **SQLSERVER**, the named instance. Omit to use the default instance. |
| `schemaName` | String | No | `""` | Schema to connect to, up to 10,000 characters. |

**Service-specific**

| Attribute | Type | Applies to | Description |
|-----------|------|------------|-------------|
| `warehouseName` | String | Snowflake | Warehouse to run queries on, up to 10,000 characters. |
| `s3OutputLocation` | String | Amazon Athena | S3 path where query results are written, up to 10,000 characters. |
| `workgroupName` | String | Amazon Athena, Amazon Redshift Serverless | Workgroup name, up to 150 characters. |
| `dataLocation` | String | Amazon Athena, Google BigQuery | Region or data location, up to 30 characters. |
| `projectId` | String | Google BigQuery | Project ID, up to 10,000 characters. |
| `sId` | String | Oracle | Oracle System ID (SID), up to 10,000 characters. |
| `catalogName` | String | Databricks and catalog-based engines | Catalog to connect to, up to 150 characters. Defaults to the engine's own default catalog when omitted for Databricks. |
| `httpPath` | String | Databricks | HTTP path of the SQL warehouse or cluster. |
| `refreshToken` | String | OAuth-authenticated services | OAuth refresh token, up to 1,000 characters. |
| `accessToken` | String | OAuth-authenticated services | OAuth access token, up to 1,000 characters. |
| `connectionString` | String | MongoDB variants, ODBC, OLEDB, HFSQL | Full connection string, up to 20,000 characters. For ODBC, OLEDB, and HFSQL this replaces the host/port/credential fields. |
| `authSource` | String | MongoDB variants | Authentication database, up to 1,000 characters. |
| `connType` | Integer | MongoDB variants | How the connection is expressed. `1` individual fields (host, port, user), `2` a single `connectionString`. For every other engine this is derived from `databaseType` and any value sent is replaced. |

**Transport security**

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `useSSL` | Boolean | No | `false` | Whether the connection uses SSL. |
| `useSSLCertificate` | Boolean | No | `false` | Whether a client SSL certificate is presented. |
| `useSSH` | Boolean | No | `false` | Whether the connection is tunnelled over SSH. When `false`, all `sshTunnel*` attributes are ignored. |
| `sshTunnelHost` | String | Conditional | `""` | SSH tunnel hostname, up to 10,000 characters. Required when `useSSH` is `true`. |
| `sshTunnelPort` | Long | Conditional | `""` | SSH tunnel port. |
| `sshTunnelUsername` | String | Conditional | `""` | SSH tunnel username, up to 10,000 characters. |
| `sshTunnelPassword` | String | Conditional | `""` | SSH tunnel password or passphrase, up to 10,000 characters. |
| `sshTunnelAuthType` | Integer | No | `0` | SSH authentication method. `0` password, `1` public key. |

#### `serviceName` values

| Value | Notes |
|-------|-------|
| `AMAZON RDS` | Supports several engines — `databaseType` is required. |
| `AMAZON REDSHIFT` | |
| `MICROSOFT AZURE` | Supports several engines — `databaseType` is required. |
| `GOOGLE CLOUD SQL` | Supports several engines — `databaseType` is required. |
| `HEROKU POSTGRESQL` | |
| `LOCAL DATABASE` | A database reached through Zoho Databridge. Supports many engines. |
| `SNOWFLAKE` | Send the account name as `hostName`, and `warehouseName`. |
| `AMAZON ATHENA` | Send the AWS region as `hostName`, plus `s3OutputLocation`. |
| `GOOGLE BIG QUERY` | Send `projectId`. |
| `PANOPLY` | |
| `RACKSPACE CLOUD` | |
| `IBM CLOUD` | |
| `ORACLE CLOUD` | |
| `OTHER CLOUD SERVICES` | For a database not covered by a named service. |
| `MONGODB ATLAS` | Uses `connectionString` / `authSource` / `connType`. |
| `AMAZON DOCUMENTDB` | Uses `connectionString` / `authSource` / `connType`. |
| `SINGLESTORE` | |
| `DIGITALOCEAN` | |
| `AMAZON LIGHTSAIL` | |
| `YELLOWBRICK` | |
| `DATABRICKS` | Send `httpPath` and, optionally, `catalogName`. |

Values are matched case-insensitively.

### Sample Requests

**Case 1 — rotate the password on an Amazon RDS MySQL connection**

The minimum useful update: the three mandatory attributes plus the new credential.

```http
PUT /restapi/v2/workspaces/466206000000071000/datasources/466206000000081000 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded
```

```json
{
  "serviceName": "AMAZON RDS",
  "databaseType": "MYSQL",
  "hostName": "zylker.abcdef.us-east-1.rds.amazonaws.com",
  "port": 3306,
  "userName": "zylkeradmin",
  "password": "Zoho@123",
  "cloudDatabaseName": "sales_db",
  "useSSL": true
}
```

**Case 2 — a Snowflake connection, covering the service-specific attributes**

```json
{
  "serviceName": "SNOWFLAKE",
  "databaseType": "SNOWFLAKE",
  "hostName": "zylker-sales.us-east-1",
  "userName": "ZYLKER_ANALYTICS",
  "password": "Zoho@123",
  "cloudDatabaseName": "SALES_DB",
  "warehouseName": "COMPUTE_WH",
  "schemaName": "PUBLIC"
}
```

**Case 3 — a local database reached over an SSH tunnel**

Covers the whole transport-security group in one call.

```json
{
  "serviceName": "LOCAL DATABASE",
  "databaseType": "POSTGRESQL",
  "hostName": "10.0.0.14",
  "port": 5432,
  "userName": "zylker_ro",
  "password": "Zoho@123",
  "cloudDatabaseName": "warehouse",
  "schemaName": "public",
  "useSSL": true,
  "useSSLCertificate": false,
  "useSSH": true,
  "sshTunnelHost": "bastion.zylker.com",
  "sshTunnelPort": 22,
  "sshTunnelUsername": "tunneluser",
  "sshTunnelPassword": "Zoho@456",
  "sshTunnelAuthType": 0
}
```

**Case 4 — Amazon Athena, where `hostName` carries a region**

```json
{
  "serviceName": "AMAZON ATHENA",
  "databaseType": "AMAZON ATHENA",
  "hostName": "us-east-1",
  "userName": "AKIAIOSFODNN7EXAMPLE",
  "password": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
  "s3OutputLocation": "s3://zylker-athena-results/",
  "workgroupName": "primary",
  "dataLocation": "us-east-1"
}
```

### Sample Responses

**HTTP 204 No Content — the connection was updated**

```
HTTP/1.1 204 No Content
```

**HTTP 400 Bad Request — `serviceName` is not recognised**

```json
{
  "status": "failure",
  "summary": "INVALID_CLOUD_SERVICENAME",
  "data": {
    "errorCode": 18057,
    "errorMessage": "Invalid cloud service name."
  }
}
```

**HTTP 400 Bad Request — the engine does not belong to that service**

```json
{
  "status": "failure",
  "summary": "DBTYPE_SERVICENAME_NOTMACHED",
  "data": {
    "errorCode": 18055,
    "errorMessage": "The given database type does not match the given service name."
  }
}
```

**HTTP 400 Bad Request — attempting to change the engine of a Live Connect database**

```json
{
  "status": "failure",
  "summary": "DBTYPE_CANNOT_BE_UPDATED_FOR_LIVECONNECT_DB",
  "data": {
    "errorCode": 18063,
    "errorMessage": "Database type cannot be updated for a live connect database."
  }
}
```

### Response Fields

**None.** This API returns `204 No Content` with an empty body. Confirm the update by re-reading [Get Datasources](#4-get-datasources), or by running [Sync Data](#1-sync-data) and checking the outcome.

### Notes & Behaviour

| Behaviour | Detail |
|-----------|--------|
| **It is a full replace of the connection, not a patch** | Attributes you omit are reset to their defaults rather than preserved. Always resend the complete connection definition, changing only what you intend to change. `password` is the one practical exception — omitting it keeps the stored password. |
| **`serviceName`, `hostName`, and `userName` are always mandatory** | Even when only the password is changing. |
| **`databaseType` is conditionally mandatory** | Required whenever the chosen service supports more than one engine. When the service has exactly one, it is inferred. Omitting it for a multi-engine service fails with `8079` naming `databaseType`. |
| **Live Connect connections are partly frozen** | `serviceName` cannot be changed (`18064`) and `databaseType` cannot be changed (`18063`). Credentials, host, and port can. |
| **`connType`, `authSource`, and `connectionString` are honoured only for MongoDB variants** | For every other engine the server derives them from `databaseType` and replaces whatever was sent. |
| **`useSSH` is the master switch for the tunnel** | With `useSSH` absent or `false`, all `sshTunnel*` attributes are ignored and stored empty. |
| **Every credential and endpoint field is treated as sensitive** | Host names, usernames, passwords, tokens, and connection strings are excluded from request logging. |
| **The connection is not tested by this call** | A `204` means the details were stored, not that they work. Run [Sync Data](#1-sync-data) and check the result to confirm. |
| **It cannot create a datasource** | The `<datasource-id>` must already exist. A file, web, connector, or snapshot ID is rejected with `18061`. |
| **Dependency chain:** | [Get Datasources](#4-get-datasources) → `datasourceId` → Update Datasource Connection → [Sync Data](#1-sync-data) → [Get Last Import Details](#5-get-last-import-details). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7301 | `SECURITY_NOT_PERMITTED` — The request came through a Client Portal / White Label domain, or the caller lacks Create Table and Edit Datasource permission on the workspace. | Call from the standard API host with one of the two permissions. |
| 8077 | `EMPTY_JSON_CONFIGURATION` — `CONFIG` was not sent, or was sent empty. | Send a CONFIG object with at least `serviceName`, `hostName`, and `userName`. |
| 8078 | `EMPTY_JSON_ATTRIBUTE_FOUND` — A mandatory attribute was sent blank. | The message names the attribute. |
| 8079 | `ATTRIBUTE_NOT_PRESENT_IN_JSON_CONFIGURATION` — A mandatory attribute is missing — usually `databaseType` for a service that supports several engines. | The message names the attribute. |
| 8504 | `LESS_THAN_MIN_OCCURANCE` — `CONFIG` is missing entirely. | Send the CONFIG object. |
| 8507 | `MORE_THAN_MAX_LENGTH` — An attribute exceeds its length limit. | See [Limitations](#limitations). |
| 8509 | `PATTERN_NOT_MATCHED` — `serviceName` or `databaseType` is not one of the accepted values. | Send a value from [`serviceName` values](#servicename-values). |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token carrying `ZohoAnalytics.metadata.update`. |
| 18055 | `DBTYPE_SERVICENAME_NOTMACHED` — The `databaseType` is not available for the given `serviceName`. | Pick an engine the service actually offers. |
| 18057 | `INVALID_CLOUD_SERVICENAME` — `serviceName` is not a recognised service. | Send a value from [`serviceName` values](#servicename-values). |
| 18061 | `CONNECTION_ID_NOT_ASSOSIATED_FOR_WORKSPACE` — The datasource ID does not exist in this workspace, or is not a database connection (HTTP 404). | Verify `<datasource-id>` with [Get Datasources](#4-get-datasources). |
| 18063 | `DBTYPE_CANNOT_BE_UPDATED_FOR_LIVECONNECT_DB` — `databaseType` differs from the stored one on a Live Connect database. | Resend the existing `databaseType`. |
| 18064 | `SERVICE_NAME_CANNOT_BE_UPDATED_FOR_LIVECONNECT_DB` — `serviceName` differs from the stored one on a Live Connect database. | Resend the existing `serviceName`. |

---

## 4. Get Datasources

Lists every datasource in a workspace, the tables each one feeds, and the state of their last sync.

| Attribute | Value |
|-----------|-------|
| **URL** | `/restapi/v2/workspaces/<workspace-id>/datasources` |
| **HTTP Method** | `GET` |
| **OAuth Scope** | `ZohoAnalytics.metadata.read` |
| **Mandatory Header** | `ZANALYTICS-ORGID` |
| **CONFIG** | This API takes no CONFIG fields |
| **Success Status** | `200 OK` with a JSON body |

**Path parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `<workspace-id>` | Long | ID of the workspace whose datasources are listed. |

### Sample Requests

```http
GET /restapi/v2/workspaces/466206000000071000/datasources HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

There is nothing else to send.

### Sample Responses

**HTTP 200 OK — a cloud database with two sync intervals**

Multi-interval datasources report their schedules under `syncIntervals`, each with its own tables.

```json
{
  "status": "success",
  "summary": "Fetch Datasources",
  "data": {
    "dataSources": [
      {
        "datasourceName": "Amazon RDS MySQL",
        "datasourceId": "466206000000081000",
        "source": "relmodel",
        "totalSyncAllowed": "5",
        "syncIntervals": [
          {
            "syncIntervalId": "466206000000082000",
            "lastDataSyncStatus": "Success",
            "lastDataSyncTime": "03 August, 2026 03:39:16 PM IST",
            "schedule": "Every 15 Minutes",
            "nextScheduleTime": "03 August, 2026 03:54:16 PM IST",
            "syncUsed": "1",
            "tableDetails": [
              {
                "viewName": "Sales",
                "viewId": "466206000000072000",
                "sourceName": "sales",
                "lastSyncTime": "03 August, 2026 03:39:13 PM IST",
                "syncStatus": "Success"
              }
            ]
          },
          {
            "syncIntervalId": "466206000000082500",
            "lastDataSyncStatus": "Success",
            "lastDataSyncTime": "03 August, 2026 02:00:04 PM IST",
            "schedule": "Daily",
            "nextScheduleTime": "04 August, 2026 02:00:00 PM IST",
            "syncUsed": "0",
            "tableDetails": [
              {
                "viewName": "Targets",
                "viewId": "466206000000072500",
                "sourceName": "targets",
                "lastSyncTime": "03 August, 2026 02:00:01 PM IST",
                "syncStatus": "Success"
              }
            ]
          }
        ]
      }
    ]
  }
}
```

**HTTP 200 OK — a mix of source types in one workspace**

A file source, an integration connector, a Live Connect database, a local-drive upload, and a snapshot. Note how the fields differ between them.

```json
{
  "status": "success",
  "summary": "Fetch Datasources",
  "data": {
    "dataSources": [
      {
        "datasourceName": "Monthly Sales CSV",
        "datasourceId": "466206000000083000",
        "source": "https://files.zylker.com/monthly-sales.csv",
        "fileType": "csv",
        "authType": "basic",
        "lastDataSyncStatus": "Success",
        "lastDataSyncTime": "03 August, 2026 06:00:12 AM IST",
        "schedule": "Daily",
        "nextScheduleTime": "04 August, 2026 06:00:00 AM IST",
        "syncUsed": "0",
        "totalSyncAllowed": "5",
        "tableDetails": [
          {
            "viewName": "MonthlySales",
            "viewId": "466206000000073000",
            "sourceName": "monthly-sales.csv",
            "lastSyncTime": "03 August, 2026 06:00:10 AM IST",
            "syncStatus": "Success"
          }
        ]
      },
      {
        "datasourceName": "Zoho CRM",
        "datasourceId": "466206000000084000",
        "source": "zylker_crm",
        "lastDataSyncStatus": "Failed",
        "lastDataSyncTime": "03 August, 2026 05:00:41 AM IST",
        "schedule": "Every 3 Hours",
        "nextScheduleTime": "03 August, 2026 08:00:00 AM IST",
        "syncUsed": "2",
        "totalSyncAllowed": "5"
      },
      {
        "datasourceName": "Warehouse PostgreSQL",
        "datasourceId": "466206000000085000",
        "source": "warehouse",
        "databridgeName": "zylker-bridge-01",
        "databridgeStatus": "active",
        "lastDesignSyncStatus": "Success",
        "lastDesignSyncTime": "01 August, 2026 11:20:05 AM IST",
        "schedule": "Not Applicable",
        "syncUsed": "0",
        "totalSyncAllowed": "5",
        "tableDetails": [
          {
            "viewName": "Orders",
            "viewId": "466206000000074000",
            "sourceName": "public.orders"
          }
        ]
      },
      {
        "datasourceName": "Local Drive",
        "tableDetails": [
          {
            "viewName": "RegionLookup",
            "viewId": "466206000000075000",
            "sourceName": "region-lookup.xlsx",
            "lastSyncTime": "28 July, 2026 04:12:33 PM IST",
            "syncStatus": "Success"
          }
        ]
      },
      {
        "datasourceName": "Snapshot",
        "tableDetails": [
          {
            "viewName": "Sales_Snapshot_July",
            "viewId": "466206000000076000",
            "sourceName": "Sales",
            "lastSyncTime": "31 July, 2026 11:59:00 PM IST",
            "syncStatus": "Success",
            "schedule": "Monthly",
            "nextScheduleTime": "31 August, 2026 11:59:00 PM IST",
            "status": "active"
          }
        ]
      }
    ]
  }
}
```

**HTTP 200 OK — a workspace with no datasources**

```json
{
  "status": "success",
  "summary": "Fetch Datasources",
  "data": {
    "dataSources": []
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | String | `"success"` on success. |
| `summary` | String | `"Fetch Datasources"`. |
| `data` | Object | Wrapper. |
| `data.dataSources` | Array | One entry per datasource. Empty when the workspace has none. |
| `dataSources[].datasourceName` | String | Display name of the datasource. For local-drive uploads and snapshots this is the family name (`"Local Drive"`, `"Snapshot"`) rather than an individual connection. |
| `dataSources[].datasourceId` | String | ID of the datasource, as a string. The `<datasource-id>` for [Sync Data](#1-sync-data) and [Update Datasource Connection](#3-update-datasource-connection). **Absent** for local-drive uploads and snapshots. |
| `dataSources[].source` | String | The underlying source identifier — a database name, a URL, or the connected account. |
| `dataSources[].fileType` | String | Format of the source file. Present for file-based datasources only. |
| `dataSources[].authType` | String | Authentication method used to reach the source. Present for sources that authenticate. |
| `dataSources[].databridgeName` | String | Name of the Zoho Databridge agent relaying the connection. Present for local-database sources only. |
| `dataSources[].databridgeStatus` | String | Current state of that agent. Present for local-database sources only. |
| `dataSources[].lastDataSyncStatus` | String | Outcome of the last data sync. Present when the datasource has a single sync interval; otherwise it appears inside each `syncIntervals` entry. Absent for Live Connect. |
| `dataSources[].lastDataSyncTime` | String | When data was last synced, formatted `dd MMMM, yyyy hh:mm:ss a z`. Absent for Live Connect. |
| `dataSources[].schedule` | String | The configured sync schedule, as displayed text (`"Every 15 Minutes"`, `"Daily"`, `"Not Applicable"`). |
| `dataSources[].nextScheduleTime` | String | When the next scheduled sync will run. Absent for Live Connect. |
| `dataSources[].syncUsed` | String | Manual syncs already used today for this connection. |
| `dataSources[].totalSyncAllowed` | String | Manual syncs permitted per day for this connection. |
| `dataSources[].lastDesignSyncStatus` | String | Outcome of the last **schema** sync. Live Connect only — a Live Connect datasource syncs its structure, not its data. |
| `dataSources[].lastDesignSyncTime` | String | When the schema was last synced. Live Connect only; empty string when it has never run. |
| `dataSources[].syncIntervalId` | String | ID of the datasource's single sync interval. Present only when there is exactly one; otherwise use `syncIntervals`. |
| `dataSources[].syncIntervals` | Array | One entry per configured sync interval. Present when the datasource supports multiple schedules. |
| `dataSources[].syncIntervals[].syncIntervalId` | String | ID of this interval. Send it as `syncIntervalId` to [Sync Data](#1-sync-data). |
| `dataSources[].syncIntervals[].lastDataSyncStatus` | String | Outcome of this interval's last run. |
| `dataSources[].syncIntervals[].lastDataSyncTime` | String | When this interval last ran. |
| `dataSources[].syncIntervals[].schedule` | String | This interval's schedule. |
| `dataSources[].syncIntervals[].nextScheduleTime` | String | When this interval will next run. |
| `dataSources[].syncIntervals[].syncUsed` | String | Manual syncs already used today for this interval. |
| `dataSources[].syncIntervals[].tableDetails` | Array | Tables fed by this interval. Same shape as `dataSources[].tableDetails`. |
| `dataSources[].tableDetails` | Array | Tables fed by this datasource. Present for non-connector sources. |
| `dataSources[].tableDetails[].viewName` | String | Name of the table in Zoho Analytics. |
| `dataSources[].tableDetails[].viewId` | String | ID of the table, as a string. The `<view-id>` for [Refetch Data](#2-refetch-data) and [Get Last Import Details](#5-get-last-import-details). |
| `dataSources[].tableDetails[].sourceName` | String | Name of the corresponding object at the source. |
| `dataSources[].tableDetails[].lastSyncTime` | String | When this table was last synced. |
| `dataSources[].tableDetails[].syncStatus` | String | Outcome of this table's last sync. |
| `dataSources[].tableDetails[].schedule` | String | Snapshot entries only — the snapshot's own schedule. |
| `dataSources[].tableDetails[].nextScheduleTime` | String | Snapshot entries only — when the snapshot next runs. |
| `dataSources[].tableDetails[].status` | String | Snapshot entries only — `"active"` or `"inactive"`. |

### Notes & Behaviour

| Behaviour | Detail |
|-----------|--------|
| **This is the only source of `datasourceId`, `syncIntervalId`, and the datasource-to-table mapping** | Three of the other four APIs depend on IDs that appear nowhere else. |
| **The entry shape varies by source type** | A field's absence is meaningful, not an error. Test for keys rather than assuming a fixed schema — see [Source Types](#source-types). |
| **Single-interval and multi-interval datasources report differently** | With one interval the sync fields sit directly on the datasource; with several they move into `syncIntervals`, and the top-level `syncIntervalId` disappears. Handle both. |
| **Live Connect reports a design sync, not a data sync** | `lastDesignSyncStatus` and `lastDesignSyncTime` replace the data-sync fields, because a Live Connect datasource keeps its structure in step rather than copying rows. |
| **Integration connectors report no tables** | Connector entries omit `tableDetails` entirely; the tables they populate are visible through [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list). |
| **Local-drive and snapshot entries have no `datasourceId`** | They cannot be synced or updated through this suite. A snapshot's target table can still be refreshed with [Refetch Data](#2-refetch-data). |
| **Every value is a string** | Including IDs, counts, and `syncUsed` / `totalSyncAllowed`. Nothing in the response is a JSON number. |
| **Times are pre-formatted display strings** | `dd MMMM, yyyy hh:mm:ss a z` — not epoch values and not ISO 8601. Parse against that pattern or treat them as opaque. |
| **A caller with only Create Table sees a reduced list** | Connection details for sources they did not create are filtered out. Grant **View Datasource** for the full picture. |
| **Dependency chain:** | Get Datasources → `datasourceId` → [Sync Data](#1-sync-data) / [Update Datasource Connection](#3-update-datasource-connection); → `tableDetails[].viewId` → [Refetch Data](#2-refetch-data) / [Get Last Import Details](#5-get-last-import-details). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7301 | `SECURITY_NOT_PERMITTED` — The request came through a Client Portal / White Label domain, or the caller lacks View Datasource and Create Table permission on the workspace. | Call from the standard API host with one of the two permissions. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token carrying `ZohoAnalytics.metadata.read`. |

---

## 5. Get Last Import Details

Reports what the most recent load into a table actually did — when it ran, whether it succeeded, and how many rows and columns landed.

| Attribute | Value |
|-----------|-------|
| **URL** | `/restapi/v2/workspaces/<workspace-id>/views/<view-id>/importdetails` |
| **HTTP Method** | `GET` |
| **OAuth Scope** | `ZohoAnalytics.metadata.read` |
| **Mandatory Header** | `ZANALYTICS-ORGID` |
| **CONFIG** | This API takes no CONFIG fields |
| **Success Status** | `200 OK` with a JSON body |

**Path parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `<workspace-id>` | Long | ID of the workspace that owns the view. |
| `<view-id>` | Long | ID of the table to report on. Must belong to `<workspace-id>`. |

This API covers **every** kind of load, not only datasource syncs. A table last written by [Import Data into an Existing Table (Synchronous)](SYNC_DATA_IMPORT_API_DOC_INFO.md#2-import-data-into-an-existing-table-synchronous) reports that import here too.

### Sample Requests

```http
GET /restapi/v2/workspaces/466206000000071000/views/466206000000072000/importdetails HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

### Sample Responses

**HTTP 200 OK — a clean load**

```json
{
  "status": "success",
  "summary": "Fetch last import details",
  "data": {
    "viewName": "Sales",
    "lastImportTime": "03 August, 2026 03:39:16 PM IST",
    "lastImportStatus": "Success",
    "columns": {
      "total": "7",
      "success": "7"
    },
    "rows": {
      "total": "755",
      "success": "755",
      "warning": "0",
      "failed": "0"
    },
    "importErrors": ""
  }
}
```

**HTTP 200 OK — some rows did not land**

```json
{
  "status": "success",
  "summary": "Fetch last import details",
  "data": {
    "viewName": "Sales",
    "lastImportTime": "03 August, 2026 03:39:16 PM IST",
    "lastImportStatus": "Partial Success",
    "columns": {
      "total": "7",
      "success": "7"
    },
    "rows": {
      "total": "755",
      "success": "740",
      "warning": "9",
      "failed": "6"
    },
    "importErrors": "<nobr>Line 42 : Invalid value for the column Order Date</NOBR><br><nobr>Line 88 : Invalid value for the column Sales</NOBR><br>"
  }
}
```

**HTTP 200 OK — a table loaded from an email attachment**

```json
{
  "status": "success",
  "summary": "Fetch last import details",
  "data": {
    "viewName": "InboundLeads",
    "lastImportTime": "02 August, 2026 09:14:02 AM IST",
    "lastImportStatus": "Success",
    "importSentFromEmail": "leads@zylker.com",
    "columns": {
      "total": "5",
      "success": "5"
    },
    "rows": {
      "total": "120",
      "success": "120",
      "warning": "0",
      "failed": "0"
    },
    "importErrors": ""
  }
}
```

**HTTP 200 OK — the table has never been loaded**

```json
{
  "status": "success",
  "summary": "Fetch last import details",
  "data": {}
}
```

An empty `data` object is a valid success. It means no import has ever run against this table.

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | String | `"success"` on success. |
| `summary` | String | `"Fetch last import details"`. |
| `data` | Object | Details of the last load. **Empty (`{}`) when the table has never been loaded.** |
| `data.viewName` | String | Display name of the table. |
| `data.lastImportTime` | String | When the load ran, formatted `dd MMMM, yyyy hh:mm:ss a z`. |
| `data.lastImportStatus` | String | `"Success"`, `"Partial Success"`, or `"Failed"`. See [`lastImportStatus` values](#lastimportstatus-values). |
| `data.importSentFromEmail` | String | For tables loaded from an emailed attachment, the sender's address. Absent for every other source. |
| `data.columns` | Object | Column counts. |
| `data.columns.total` | String | Columns present in the incoming data. |
| `data.columns.success` | String | Columns loaded successfully. |
| `data.rows` | Object | Row counts. |
| `data.rows.total` | String | Rows present in the incoming data. |
| `data.rows.success` | String | Rows loaded successfully. |
| `data.rows.warning` | String | Rows loaded with a value reset or truncated. |
| `data.rows.failed` | String | Rows rejected outright. |
| `data.importErrors` | String | An HTML fragment describing each offending line, field, and value. Empty (`""`) when the load was clean. Display or log it — do not parse it. |

#### `lastImportStatus` values

| Value | Meaning |
|-------|---------|
| `Success` | Every row loaded, and no errors were reported. Also returned when the source had nothing new, so no rows changed. |
| `Partial Success` | Some rows loaded and some did not — `rows.success` is below `rows.total`, or `warning` or `failed` is above zero. |
| `Failed` | The load did not complete. |

### Notes & Behaviour

| Behaviour | Detail |
|-----------|--------|
| **An empty `data` object is a success, not an error** | It simply means the table has never been loaded. Test for the absence of `viewName` before reading any other field. |
| **It reports the last load from any path** | A datasource sync, a refetch, or an import API call — whichever ran most recently. The response does not say which. |
| **`Success` covers "nothing changed"** | When a sync finds no new data, the counts come back as `-1` and the status is still `Success`. Do not read `rows.success` as "rows written" without checking `rows.total`. |
| **All counts are strings** | `"755"`, not `755`. Convert before arithmetic. |
| **`importErrors` is markup, not data** | It is a fragment of `<nobr>…</NOBR><br>` HTML. Render or log it; do not attempt to parse fields out of it. |
| **`lastImportTime` is a pre-formatted display string** | `dd MMMM, yyyy hh:mm:ss a z`. Not epoch, not ISO 8601. |
| **It is the only outcome report for the two sync APIs** | Both return `204`, so this is where you find out whether a sync worked. |
| **`importSentFromEmail` is conditional** | Present only for tables fed by emailed attachments. |
| **Dependency chain:** | [Get Datasources](#4-get-datasources) → `tableDetails[].viewId`, or [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → `<view-id>` → [Sync Data](#1-sync-data) / [Refetch Data](#2-refetch-data) → Get Last Import Details. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7104 | `META_OBJECT_NOT_PRESENT` — The view does not exist. | Verify `<view-id>` with [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list). |
| 7301 | `SECURITY_NOT_PERMITTED` — The request came through a Client Portal / White Label domain, or the caller is neither an admin nor the View Owner and lacks View Datasource or an import permission on the view. | Call from the standard API host with the required permission. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token carrying `ZohoAnalytics.metadata.read`. |

---

## Appendix A – Common HTTP Headers

| Header | Value | Required | Description |
|--------|-------|----------|-------------|
| `Authorization` | `Zoho-oauthtoken <oauth-token>` | **Mandatory** | OAuth 2.0 access token of the calling user, carrying the scope for the API being called — see [Appendix B](#appendix-b--oauth-scope-summary). |
| `ZANALYTICS-ORGID` | Organization ID string | **Mandatory** | Organization ID of the workspace. Required by all five APIs. |
| `Content-Type` | `application/x-www-form-urlencoded` | Conditional | Required by [Sync Data](#1-sync-data), [Refetch Data](#2-refetch-data), and [Update Datasource Connection](#3-update-datasource-connection) when a CONFIG is sent. |

> **`ZANALYTICS-DEST-ORGID` is not used by any of these APIs.** That header applies only to cross-organization copy operations (Copy Workspace, [Copy Views](VIEW_OPERATIONS_API_DOC_INFO.md#2-copy-views), Copy Formulas), which target a destination organization.

Example (a full refetch of one table):

```http
POST /restapi/v2/workspaces/466206000000071000/views/466206000000072000/sync HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG=%7B%22isFullFetch%22%3Atrue%7D
```

---

## Appendix B – OAuth Scope Summary

| API | HTTP Method | Scope |
|-----|-------------|-------|
| Sync Data | POST | `ZohoAnalytics.metadata.create` |
| Refetch Data | POST | `ZohoAnalytics.metadata.create` |
| Update Datasource Connection | PUT | `ZohoAnalytics.metadata.update` |
| Get Datasources | GET | `ZohoAnalytics.metadata.read` |
| Get Last Import Details | GET | `ZohoAnalytics.metadata.read` |

> All five sit in the **`metadata`** scope family rather than `data`, because they operate on the plumbing that moves data rather than on the data itself. A token scoped for `ZohoAnalytics.data.*` — enough for the import and export APIs — will not authorise any of them. Note also that the two sync APIs use `metadata.create` even though nothing is created: the scope follows the HTTP method, and both are `POST`.

---

## Appendix C – API-Specific Notes and Behaviours

### Sync Data

- **The whole datasource moves, not one table.** If a datasource feeds twenty tables, this pulls all twenty. When only one is stale, [Refetch Data](#2-refetch-data) is the cheaper instrument — and both draw on the same daily quota.
- **`syncIntervalId` is mandatory or forbidden depending on data you do not have in hand.** Nothing in the request tells you which case applies; you have to have read `syncIntervals` from [Get Datasources](#4-get-datasources) first. An integration that skips the listing call will meet `8182` in production the first time someone adds a second schedule.
- **The quota is per connection and resets daily.** Five manual syncs is not many for an active integration. Read `syncUsed` and `totalSyncAllowed` and decide, rather than catching `19000048` and retrying.
- **`204` is the whole response.** There is no job ID, no queue position, and no polling endpoint. The pull's outcome lives in [Get Last Import Details](#5-get-last-import-details), one table at a time.
- **Credentials in CONFIG are for the source system.** They are supplied per call for sources that do not store them, and are excluded from request logging.
- **Dependency chain:** [Get Datasources](#4-get-datasources) → `datasourceId` (+ `syncIntervalId`) → Sync Data → [Get Last Import Details](#5-get-last-import-details).

### Refetch Data

- **`isFullFetch` is the attribute that matters, and its default is the surprising one.** Incremental is the default, and an incremental fetch will not remove rows that were deleted at the source. A table that has silently drifted needs `isFullFetch: true`.
- **It is the only way to refresh a snapshot.** Snapshot datasources carry no `datasourceId`, so [Sync Data](#1-sync-data) cannot reach them; refetching the snapshot's target table re-runs it.
- **`18056` means the table has no source, not that the source failed.** Hand-built tables and tables loaded only through the import APIs will always return it — that is a design fact, not a fault to retry.
- **`18072` is a concurrency guard, not a rate limit.** One refetch per table at a time; the fix is to wait for the running one, not to back off and retry blindly.
- **It draws on the same quota as [Sync Data](#1-sync-data).** Refetching twenty tables individually is not a way around the five-per-connection ceiling.
- **Dependency chain:** [Get Datasources](#4-get-datasources) → `tableDetails[].viewId` → Refetch Data → [Get Last Import Details](#5-get-last-import-details).

### Update Datasource Connection

- **It replaces the connection rather than patching it.** This is the single most consequential behaviour of this API: omitted attributes are reset, not preserved. Fetch the current definition, change one field, and resend everything.
- **Three attributes are mandatory on every call**, even a password rotation: `serviceName`, `hostName`, `userName`.
- **`databaseType` is required more often than it looks.** Most named services support several engines, so in practice it is mandatory. Omitting it yields `8079` naming `databaseType`, which reads like a missing-field bug rather than a service-capability rule.
- **`hostName` does not always mean a host.** For Amazon Athena it carries the AWS region; for Snowflake, the account name. Sending a URL there is the most common cause of a connection that stores cleanly and then fails to sync.
- **Live Connect connections are half-frozen.** Credentials and endpoint can change; `serviceName` (`18064`) and `databaseType` (`18063`) cannot. To change the engine, rebuild the connection in the interface.
- **`connType`, `authSource`, and `connectionString` only survive for MongoDB variants.** For every other engine the server overwrites them from `databaseType`.
- **A `204` is not a connectivity test.** The details are stored, nothing is dialled. Run [Sync Data](#1-sync-data) and read the result to know whether they work.
- **It cannot create a connection**, and it cannot touch file, web, cloud-storage, connector, snapshot, or local-drive datasources — `18061` for all of them.
- **Dependency chain:** [Get Datasources](#4-get-datasources) → `datasourceId` → Update Datasource Connection → [Sync Data](#1-sync-data) → [Get Last Import Details](#5-get-last-import-details).

### Get Datasources

- **It is the map for this entire document.** `datasourceId`, `syncIntervalId`, and the datasource-to-`viewId` mapping appear in no other response anywhere in the V2 surface. Every integration here starts with this call.
- **The response is polymorphic by design.** Six source families produce six field shapes. Writing a strict deserialiser against one sample will break on the next workspace — key presence is the contract, not a fixed schema.
- **The single-interval / multi-interval split is the sharpest edge.** One interval puts the sync fields on the datasource; two or more move them into `syncIntervals` and remove the top-level `syncIntervalId`. The same datasource changes shape the moment an administrator adds a schedule.
- **Live Connect reports schema syncs, not data syncs.** Looking for `lastDataSyncStatus` on a Live Connect entry finds nothing; the fields are `lastDesignSyncStatus` and `lastDesignSyncTime`.
- **Two entries have no ID at all.** Local-drive uploads and snapshots list their tables but expose no `datasourceId`, which is exactly why neither [Sync Data](#1-sync-data) nor [Update Datasource Connection](#3-update-datasource-connection) can address them.
- **It is also the quota display.** `syncUsed` / `totalSyncAllowed` are the only place the manual-sync allowance is visible.
- **Timestamps are display strings, not machine values.** `03 August, 2026 03:39:16 PM IST` — rendered in a fixed pattern, not epoch or ISO 8601.
- **Dependency chain:** Get Datasources → everything else in this document.

### Get Last Import Details

- **It is the outcome report for two APIs that have none.** [Sync Data](#1-sync-data) and [Refetch Data](#2-refetch-data) both return `204`; this is where the result surfaces.
- **An empty `data` object is the "never loaded" signal**, and it arrives with HTTP `200` and `status: "success"`. Code that assumes `data.viewName` exists will fail on a freshly created table.
- **It does not say what performed the load.** A datasource sync and an import API call are indistinguishable here. If you need to attribute a load, record it yourself.
- **`Success` does not imply rows were written.** A sync that found nothing new reports `Success` with counts of `-1`. Compare `rows.success` against `rows.total` before drawing conclusions.
- **`Partial Success` is the one to alert on.** It means data landed but not all of it — the failure mode most likely to go unnoticed, because nothing errored.
- **`importErrors` is HTML.** Display or log it; it is not structured data and its shape is not guaranteed.
- **Dependency chain:** [Get Datasources](#4-get-datasources) → `tableDetails[].viewId` → [Sync Data](#1-sync-data) / [Refetch Data](#2-refetch-data) → Get Last Import Details.

---

## Appendix D – General Response Payload Notes

| Field / Behaviour | Detail |
|-------------------|--------|
| **Three APIs return 204, two return 200** | [Sync Data](#1-sync-data), [Refetch Data](#2-refetch-data), and [Update Datasource Connection](#3-update-datasource-connection) return `204 No Content` with an empty body. [Get Datasources](#4-get-datasources) and [Get Last Import Details](#5-get-last-import-details) return `200` with the standard envelope. |
| **A 204 confirms acceptance, not completion** | For the two sync APIs it means the pull was started; for the update API it means the details were stored. Neither implies the operation worked. |
| **Failure responses share one shape** | `{"status": "failure", "summary": "<ERROR_NAME>", "data": {"errorCode": <n>, "errorMessage": "<text>"}}`. `summary` on failure is the error's symbolic name (for example `NO_SOURCE_AVAILABLE_FOR_TABLE`), not a localised sentence. |
| **Every value in a success `data` object is a string** | IDs, counts, quotas, and statuses alike. Nothing is a JSON number or boolean. |
| **Timestamps use one fixed display format** | `dd MMMM, yyyy hh:mm:ss a z`, for example `03 August, 2026 03:39:16 PM IST`. This applies to `lastDataSyncTime`, `lastSyncTime`, `nextScheduleTime`, `lastDesignSyncTime`, and `lastImportTime`. |
| **Field presence is conditional and meaningful** | Both `200` responses omit fields that do not apply to the source or the situation. Absence carries information; test for keys. |
| **`data` can be legitimately empty** | `{"dataSources": []}` for a workspace with no datasources, and `{}` for a table that has never been loaded. Both are successes. |
| **Status vocabularies differ between the two read APIs** | [Get Datasources](#4-get-datasources) reports sync statuses as source-provided display text; [Get Last Import Details](#5-get-last-import-details) reports a fixed three-value set. Do not compare them directly. |
| **Credentials never appear in a response** | Usernames, passwords, tokens, and connection strings are write-only. [Get Datasources](#4-get-datasources) reports the host and the account, never the secret. |

---

## Appendix E – Enum and Value Reference

**`sshTunnelAuthType`** — [Update Datasource Connection](#3-update-datasource-connection), default `0`

| Value | Authentication method |
|-------|-----------------------|
| `0` | Password |
| `1` | Public key |

**`connType`** — [Update Datasource Connection](#3-update-datasource-connection), MongoDB variants only

| Value | Connection style |
|-------|------------------|
| `1` | Individual fields — `hostName`, `port`, `userName`, `password` |
| `2` | A single `connectionString` |

**`isFullFetch`** — [Refetch Data](#2-refetch-data), default `false`

| Value | Fetch mode |
|-------|------------|
| `false` | Incremental — only data changed since the last pull |
| `true` | Full — the source is re-read completely |

**`lastImportStatus`** — [Get Last Import Details](#5-get-last-import-details)

| Value | Meaning |
|-------|---------|
| `Success` | Everything loaded, or nothing needed loading |
| `Partial Success` | Some rows loaded, some did not |
| `Failed` | The load did not complete |

**`databridgeStatus`** — [Get Datasources](#4-get-datasources), local-database sources only

| Value | Meaning |
|-------|---------|
| `active` | The Zoho Databridge agent is connected |
| `inactive` | The agent is not reachable |

**`status`** (inside `tableDetails`) — [Get Datasources](#4-get-datasources), snapshot entries only

| Value | Meaning |
|-------|---------|
| `active` | The snapshot schedule is running |
| `inactive` | The snapshot schedule is paused |

**`serviceName`** — see [`serviceName` values](#servicename-values) in [Update Datasource Connection](#3-update-datasource-connection).

---

## Appendix F – CONFIG Attribute Availability by API

`✓` accepted and acted on, `–` not accepted or has no effect.

| Attribute | Sync Data | Refetch Data | Update Datasource Connection |
|-----------|:---------:|:------------:|:----------------------------:|
| `userName` | ✓ | ✓ | ✓ **mandatory** |
| `password` | ✓ | ✓ | ✓ |
| `syncIntervalId` | ✓ | – | – |
| `isFullFetch` | – | ✓ | – |
| `serviceName` | – | – | ✓ **mandatory** |
| `hostName` | – | – | ✓ **mandatory** |
| `databaseType` | – | – | ✓ conditional |
| `port`, `cloudDatabaseName`, `instanceName`, `schemaName` | – | – | ✓ |
| `warehouseName`, `s3OutputLocation`, `workgroupName`, `dataLocation`, `projectId`, `sId`, `catalogName`, `httpPath` | – | – | ✓ |
| `refreshToken`, `accessToken` | – | – | ✓ |
| `connectionString`, `authSource`, `connType` | – | – | ✓ MongoDB variants only |
| `useSSL`, `useSSLCertificate` | – | – | ✓ |
| `useSSH`, `sshTunnelHost`, `sshTunnelPort`, `sshTunnelUsername`, `sshTunnelPassword`, `sshTunnelAuthType` | – | – | ✓ |

[Get Datasources](#4-get-datasources) and [Get Last Import Details](#5-get-last-import-details) take no CONFIG attributes at all.
