# Zoho Analytics V2 REST API — AutoML

This document covers the V2 **AutoML** REST APIs of Zoho Analytics — the APIs that train machine-learning models on a table, inspect the trained models, deploy a chosen model to score new data on a schedule, run predictions on demand, and explore hypothetical predictions.

## What is "AutoML" in Zoho Analytics?

AutoML lets you build predictive models directly on Zoho Analytics tables without writing code. The feature is organised as a strict four-level hierarchy, and almost every API in this document operates on one level of it:

```
Workspace
└── Analysis            ← created from ONE training table + a target column + a feature list
    └── Model           ← one model per algorithm you configured; created automatically by training
        └── Deployment  ← scores an input table into an output table, on a schedule or on demand
```

| Level | Created by | Deleted by | Notes |
|-------|-----------|-----------|-------|
| **Analysis** | [Create AutoML Analysis](#5-create-automl-analysis) | [Delete AutoML Analysis](#6-delete-automl-analysis) | The training job. One analysis = one training table + one target column + one feature set + one or more algorithms. |
| **Model** | **Not created directly.** One model is generated per algorithm listed in the `algorithms` object when the analysis is created. | [Delete AutoML Analysis Model](#7-delete-automl-analysis-model) | Each model trains independently and carries its own score, training status, and hyperparameters. |
| **Deployment** | [Create AutoML Analysis Deployment](#8-create-automl-analysis-deployment) | [Delete AutoML Analysis Model Deployment](#10-delete-automl-analysis-model-deployment) | Binds one model to an input table and an output table. **A model can have at most one deployment.** |

> **There is no "train model" API and no "update analysis" API.** Training starts automatically when the analysis is created, and none of the four levels can be edited afterwards — an analysis, a model, and a deployment are all create-and-delete objects. To change a feature list, a target column, or an algorithm's hyperparameters, delete the analysis and create a new one.

> Notes that apply to every API in this document:
> - All requests are authenticated via OAuth (`Authorization: Zoho-oauthtoken <token>`). The four read APIs use the **`metadata`** scope family; the seven write APIs use the **`modeling`** scope family — see [Appendix B](#appendix-b--oauth-scope-summary).
> - All eleven APIs require the `ZANALYTICS-ORGID` header. Ten are workspace-scoped under `/restapi/v2/automl/workspaces/<workspace-id>/...`; only [Get AutoML Analysis In Org](#1-get-automl-analysis-in-org) is organization-scoped.
> - **All eleven APIs are disabled in Client Portal / White Label request contexts.** A request that arrives through a custom domain is rejected with `7301` before any business logic runs — see [White Label / Client Portal Behaviour](#white-label--client-portal-behaviour).
> - **AutoML must be enabled for the organization**, and the organization must be within its AutoML plan limit. Otherwise every call fails with `21000014` — see [Feature Enablement and Plan Limits](#feature-enablement-and-plan-limits).
> - Permissions are **owner-only**: there is no permission-based alternative for a non-owner. See [Permission Model](#permission-model).
> - None of these APIs accepts a `criteria` attribute. Rows are selected by choosing the training table and input table, not by a filter expression.

---

## Index

| # | API Name | Method | URL |
|---|----------|--------|-----|
| 1 | [Get AutoML Analysis In Org](#1-get-automl-analysis-in-org) | GET | `/restapi/v2/automl/analysis` |
| 2 | [Get AutoML Analysis In Workspace](#2-get-automl-analysis-in-workspace) | GET | `/restapi/v2/automl/workspaces/<workspace-id>/analysis` |
| 3 | [Get AutoML Analysis Details](#3-get-automl-analysis-details) | GET | `/restapi/v2/automl/workspaces/<workspace-id>/analysis/<analysis-id>` |
| 4 | [Get Deployments For A Model](#4-get-deployments-for-a-model) | GET | `/restapi/v2/automl/workspaces/<workspace-id>/analysis/<analysis-id>/models/<model-id>/deployments` |
| 5 | [Create AutoML Analysis](#5-create-automl-analysis) | POST | `/restapi/v2/automl/workspaces/<workspace-id>/analysis` |
| 6 | [Delete AutoML Analysis](#6-delete-automl-analysis) | DELETE | `/restapi/v2/automl/workspaces/<workspace-id>/analysis/<analysis-id>` |
| 7 | [Delete AutoML Analysis Model](#7-delete-automl-analysis-model) | DELETE | `/restapi/v2/automl/workspaces/<workspace-id>/analysis/<analysis-id>/models/<model-id>` |
| 8 | [Create AutoML Analysis Deployment](#8-create-automl-analysis-deployment) | POST | `/restapi/v2/automl/workspaces/<workspace-id>/analysis/<analysis-id>/models/<model-id>/deployments` |
| 9 | [Run AutoML Analysis](#9-run-automl-analysis) | POST | `/restapi/v2/automl/workspaces/<workspace-id>/analysis/<analysis-id>/deployments/<deployment-id>/execute` |
| 10 | [Delete AutoML Analysis Model Deployment](#10-delete-automl-analysis-model-deployment) | DELETE | `/restapi/v2/automl/workspaces/<workspace-id>/analysis/<analysis-id>/deployments/<deployment-id>` |
| 11 | [AutoML What If Analysis](#11-automl-what-if-analysis) | POST | `/restapi/v2/automl/workspaces/<workspace-id>/analysis/<analysis-id>/models/<model-id>/whatif` |

---

## How the APIs Depend on Each Other

Every AutoML API needs IDs produced by an earlier one. This is the end-to-end order, and there is no way to skip a step.

### The full lifecycle

```
 [Get View List]                     → trainingTableId  (a table in the workspace)
        │
        ▼
 5. Create AutoML Analysis           → analysisId
        │   (training starts immediately; one model per algorithm)
        ▼
 3. Get AutoML Analysis Details      → models[].id  (= modelId), models[].trainingStatus
        │   ── poll until trainingStatus is "Completed" ──
        ├──────────────────────────────────────────────┐
        ▼                                              ▼
 8. Create Deployment (needs modelId) → deploymentId   11. What If Analysis (needs modelId)
        │                                                  → one-off prediction, nothing stored
        ▼
 4. Get Deployments For A Model      → deployment status, outputTableId
        │
        ▼
 9. Run AutoML Analysis (needs deploymentId) → scores the input table into the output table
```

### Which ID comes from where

| ID | Produced by | Consumed by |
|----|-------------|-------------|
| `workspaceId` | [Get Workspace List](WORKSPACE_OPERATIONS_API_DOC_INFO.md) | All ten workspace-scoped APIs |
| `trainingTableId`, `inputTableId` | [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) | [Create AutoML Analysis](#5-create-automl-analysis), [Create AutoML Analysis Deployment](#8-create-automl-analysis-deployment) |
| `analysisId` | [Create AutoML Analysis](#5-create-automl-analysis) response, or [Get AutoML Analysis In Org](#1-get-automl-analysis-in-org) / [Get AutoML Analysis In Workspace](#2-get-automl-analysis-in-workspace) | Every API with `<analysis-id>` in its path |
| `modelId` | **[Get AutoML Analysis Details](#3-get-automl-analysis-details) only** (`models[].id`) | Every API with `<model-id>` in its path |
| `deploymentId` | [Create AutoML Analysis Deployment](#8-create-automl-analysis-deployment) response, or [Get Deployments For A Model](#4-get-deployments-for-a-model) | Every API with `<deployment-id>` in its path |
| `outputTableId` | [Create AutoML Analysis Deployment](#8-create-automl-analysis-deployment) response | Read the predictions with the [Row / Export APIs](ROW_API_DOC_INFO.md) |

> **`modelId` has exactly one source.** Models are never returned by the two list APIs — [Get AutoML Analysis Details](#3-get-automl-analysis-details) is the only API that exposes `models[].id`. Any workflow that deploys a model, deletes a model, or runs a What-If must call Get AutoML Analysis Details first.

### Ordering rules enforced by the server

| Rule | Enforced by | Error |
|------|-------------|-------|
| A model cannot be deployed while it is still training | [Create AutoML Analysis Deployment](#8-create-automl-analysis-deployment) | `21000052` |
| A model that failed training cannot be deployed | [Create AutoML Analysis Deployment](#8-create-automl-analysis-deployment) | `21000053` |
| A model can hold **only one** deployment at a time | [Create AutoML Analysis Deployment](#8-create-automl-analysis-deployment) | `21000051` |
| What-If cannot run while the model is still training | [AutoML What If Analysis](#11-automl-what-if-analysis) | `21000043` |
| What-If is not supported by every algorithm | [AutoML What If Analysis](#11-automl-what-if-analysis) | `21000054` |
| The analysis must belong to the workspace in the URL | Every API with `<analysis-id>` in its path | `21000009` |
| The model must belong to the analysis in the URL | Every API with `<model-id>` in its path | `21000010` |
| The deployment must belong to the analysis in the URL | Every API with `<deployment-id>` in its path | `21000012` |

### Cascade on delete

| Deleting… | Also removes |
|---|---|
| An **analysis** ([Delete AutoML Analysis](#6-delete-automl-analysis)) | **Every model under it, and every deployment under those models.** A single call tears down the whole subtree. |
| A **model** ([Delete AutoML Analysis Model](#7-delete-automl-analysis-model)) | The deployment attached to that model, if any. The analysis and its other models survive. |
| A **deployment** ([Delete AutoML Analysis Model Deployment](#10-delete-automl-analysis-model-deployment)) | Only the deployment. The model becomes deployable again (`isDeployed` returns to `false`). |

> Deleting an analysis or a deployment does **not** delete the output table that a deployment created. Prediction data already written to the output table remains in the workspace and must be removed separately with [Delete View](VIEW_OPERATIONS_API_DOC_INFO.md#5-delete-view).

---

## Permission Model

AutoML permissions are stricter than most of the API suite: the check is **workspace ownership**, with no permission-based or custom-role alternative.

| API | Who may call it |
|-----|-----------------|
| [Get AutoML Analysis In Org](#1-get-automl-analysis-in-org) | **Account Admin or Organization Admin only.** A Workspace Admin receives `7301` even for their own workspaces. |
| The other ten APIs | The authenticated user must be an Account Admin or Organization Admin, or the **Workspace Admin (owner) of the workspace named in the URL**. |

Every other role is rejected with `7301` — shared users, group members, and ordinary org users have no AutoML access at all, and a Workspace Admin of workspace A cannot touch an analysis in workspace B.

---

## Feature Enablement and Plan Limits

Before any business logic runs, the write APIs check two things:

| Condition | Error | Message |
|-----------|-------|---------|
| AutoML is not switched on for the organization | `21000014` `AUTOML_NOT_ENABLED` | *"The AutoML Feature is not enabled. Please enable the features from Org Settings > Feature Controls > DSML."* |
| The organization has used up its AutoML allowance | `21000014` `AUTOML_PRICING_EXCEED` | *"AutoML allowed limit exceeded for your plan. Kindly increase the limit to continue to use AutoML."* |

> Both conditions share the numeric code `21000014` and are told apart only by the `summary` field. Match on `summary`, not on `errorCode`, when you need to distinguish "turn the feature on" from "buy more capacity".

---

## White Label / Client Portal Behaviour

All eleven APIs are blocked in Client Portal / White Label request contexts — the same posture as the [Embed URL](EMBEDURL_API_DOC_INFO.md#white-label--client-portal-behaviour) and [Email Schedule](EMAIL_SCHEDULES_API_DOC_INFO.md#white-label--client-portal-behaviour) families.

| Scenario | Result |
|----------|--------|
| The API request arrives **through** a Client Portal / White Label custom domain | **Rejected with `7301`** before any business logic runs. AutoML cannot be managed from a portal-domain context. |
| The API request is sent to the **standard API host** for a workspace that happens to be white-labelled | **Allowed**, and behaves exactly as for any other workspace. |

There is no `domainName` attribute on any AutoML API. Manage AutoML for a white-labelled workspace by calling the standard `analyticsapi.zoho.*` host.

---

## 1. Get AutoML Analysis In Org

Returns every AutoML analysis across **all workspaces** in the organization, each tagged with the workspace it belongs to. This is the organization-wide inventory call.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/automl/analysis` |
| **OAuth Scope** | `ZohoAnalytics.metadata.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID whose analyses are listed. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin of the organization. A Workspace Admin is **not** sufficient. |

> This API has no CONFIG parameter and no workspace in its path.

### Sample Requests

**Case 1 — Standard organization**

```http
GET /restapi/v2/automl/analysis HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — White Label / Client Portal: request sent through the portal domain (rejected)**

```http
GET /restapi/v2/automl/analysis HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
```

### Sample Responses

**HTTP 200 OK — Analyses across two workspaces**

```json
{
    "status": "success",
    "summary": "Get autoML analysis in organization",
    "data": {
        "analysis": [
            {
                "id": "137687000000061115",
                "name": "Workspace1Analysis",
                "predictionType": "Regression",
                "trainingTable": "RealEstate_TrainData",
                "trainingTableId": "137687000000061002",
                "isDraft": false,
                "workspaceId": "137687000271334001",
                "workspaceName": "Real Estate Analytics"
            },
            {
                "id": "137687000000061116",
                "name": "Workspace2Analysis",
                "predictionType": "Classification",
                "trainingTable": "Churn_TrainData",
                "trainingTableId": "137687000000061004",
                "isDraft": false,
                "workspaceId": "137687000271334002",
                "workspaceName": "Customer Analytics"
            }
        ]
    }
}
```

**HTTP 200 OK — Organization with no AutoML analyses**

```json
{
    "status": "success",
    "summary": "Get autoML analysis in organization",
    "data": {
        "analysis": []
    }
}
```

**HTTP 403 Forbidden — Caller is a Workspace Admin, or the request came through a portal domain**

```json
{
    "status": "failure",
    "summary": "SECURITY_NOT_PERMITTED",
    "data": {
        "errorCode": 7301,
        "errorMessage": "You (WorkspaceAdmin) do not have the permission to do this operation. "
    }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `status` | String | `"success"` on a successful call, `"failure"` on error. |
| `summary` | String | Localised operation summary. `"Get autoML analysis in organization"` for this API. |
| `data` | JSONObject | Response payload wrapper. |
| `data.analysis` | JSONArray | One entry per analysis in the organization. **Always present**; empty array `[]` when there are none. |
| `analysis[].id` | String | ID of the analysis, serialised as a **string**. Use as `<analysis-id>` in the workspace-scoped APIs. |
| `analysis[].name` | String | Name of the analysis. Unique within its workspace. |
| `analysis[].predictionType` | String | `"Regression"`, `"Classification"`, or `"Clustering"`. **Returned in title case**, whereas [Create AutoML Analysis](#5-create-automl-analysis) accepts it in upper case — do not compare the two directly. |
| `analysis[].trainingTable` | String | Name of the table the analysis was trained on. |
| `analysis[].trainingTableId` | String | ID of the training table, as a string. |
| `analysis[].isDraft` | Boolean | `true` when the analysis was saved but never trained. Analyses created through this API are never drafts — drafts originate from the Zoho Analytics UI. |
| `analysis[].workspaceId` | String | ID of the workspace holding the analysis. **Only present in this API** — pair it with `id` to address the analysis in the workspace-scoped APIs. |
| `analysis[].workspaceName` | String | Name of that workspace. **Only present in this API.** |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **The only organization-wide AutoML API** | Every other API in this family is scoped to a single workspace. Use this one to find analyses when you do not already know which workspace holds them. |
| **Adds `workspaceId` / `workspaceName`** | These two fields are what make the response actionable — every follow-up call needs the workspace in its path. [Get AutoML Analysis In Workspace](#2-get-automl-analysis-in-workspace) omits them because the workspace is already known. |
| **No models, no deployments** | The response is a flat analysis inventory. Model IDs come only from [Get AutoML Analysis Details](#3-get-automl-analysis-details). |
| **Stricter role gate than the rest of the family** | A Workspace Admin who can fully manage AutoML inside their own workspace still receives `7301` here, because the API is organization-scoped. |
| **Unfiltered and unpaged** | No search, sort, or paging parameters. Filter client-side on `workspaceId`, `predictionType`, or `isDraft`. |
| **Empty array, not an error** | An organization with no analyses returns HTTP 200 with `"analysis": []`. |
| **Not callable from a portal domain** | See [White Label / Client Portal Behaviour](#white-label--client-portal-behaviour). |
| **Dependency chain** | Get AutoML Analysis In Org → `workspaceId` + `id` → [Get AutoML Analysis Details](#3-get-automl-analysis-details). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7301 | `SECURITY_NOT_PERMITTED` — The request came through a Client Portal / White Label domain, or the caller is not an Account Admin / Organization Admin of the organization. | Call from the standard API host as an Account Admin or Organization Admin. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.metadata.read`. |

---

## 2. Get AutoML Analysis In Workspace

Returns every AutoML analysis defined in one workspace. Identical to [Get AutoML Analysis In Org](#1-get-automl-analysis-in-org) except that it is workspace-scoped and therefore omits the workspace fields.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/automl/workspaces/<workspace-id>/analysis` |
| **OAuth Scope** | `ZohoAnalytics.metadata.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or the Workspace Admin (owner) of the specified workspace. |

> This API has no CONFIG parameter.

### Sample Requests

**Case 1 — Standard workspace**

```http
GET /restapi/v2/automl/workspaces/137687000271334001/analysis HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — White Label / Client Portal: request sent through the portal domain (rejected)**

```http
GET /restapi/v2/automl/workspaces/137687000271334009/analysis HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
```

### Sample Responses

**HTTP 200 OK — Workspace with several analyses**

```json
{
    "status": "success",
    "summary": "Get autoML analysis in workspace",
    "data": {
        "analysis": [
            {
                "id": "137687000000061115",
                "name": "PricePredictionAnalysis",
                "predictionType": "Regression",
                "trainingTable": "RealEstate_TrainData",
                "trainingTableId": "137687000000061002",
                "isDraft": false
            },
            {
                "id": "137687000000061117",
                "name": "SegmentationAnalysis",
                "predictionType": "Clustering",
                "trainingTable": "RealEstate_TrainData",
                "trainingTableId": "137687000000061002",
                "isDraft": false
            }
        ]
    }
}
```

**HTTP 200 OK — Workspace with no analyses**

```json
{
    "status": "success",
    "summary": "Get autoML analysis in workspace",
    "data": {
        "analysis": []
    }
}
```

**HTTP 403 Forbidden — Caller is the admin of a different workspace**

```json
{
    "status": "failure",
    "summary": "SECURITY_NOT_PERMITTED",
    "data": {
        "errorCode": 7301,
        "errorMessage": "You (WorkspaceAdmin2) do not have the permission to do this operation. "
    }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `status` | String | `"success"` on a successful call, `"failure"` on error. |
| `summary` | String | Localised operation summary. `"Get autoML analysis in workspace"` for this API. |
| `data` | JSONObject | Response payload wrapper. |
| `data.analysis` | JSONArray | One entry per analysis in the workspace. **Always present**; empty array `[]` when there are none. |
| `analysis[].id` | String | ID of the analysis, as a string. Use as `<analysis-id>`. |
| `analysis[].name` | String | Name of the analysis. Unique within the workspace. |
| `analysis[].predictionType` | String | `"Regression"`, `"Classification"`, or `"Clustering"` — title case, unlike the upper-case request value. |
| `analysis[].trainingTable` | String | Name of the training table. |
| `analysis[].trainingTableId` | String | ID of the training table, as a string. |
| `analysis[].isDraft` | Boolean | `true` for an untrained draft created in the UI. |

> `workspaceId` and `workspaceName` are **not** returned here — they are unique to [Get AutoML Analysis In Org](#1-get-automl-analysis-in-org).

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Same entry shape as the org API, minus two fields** | The per-analysis object is identical except that `workspaceId` and `workspaceName` are absent, because the workspace is already fixed by the URL. |
| **Available to Workspace Admins** | Unlike [Get AutoML Analysis In Org](#1-get-automl-analysis-in-org), the owner of this workspace may call it. |
| **Still no models** | Model IDs require [Get AutoML Analysis Details](#3-get-automl-analysis-details). |
| **Unfiltered and unpaged** | No search, sort, or paging parameters. |
| **Empty array, not an error** | A workspace with no analyses returns HTTP 200 with `"analysis": []`. |
| **Not callable from a portal domain** | See [White Label / Client Portal Behaviour](#white-label--client-portal-behaviour). |
| **Dependency chain** | [Get Workspace List](WORKSPACE_OPERATIONS_API_DOC_INFO.md) → Get AutoML Analysis In Workspace → `id` → [Get AutoML Analysis Details](#3-get-automl-analysis-details). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7103 | `META_OBJECT_NOT_PRESENT` — Workspace not found. | Verify `<workspace-id>` and that the `ZANALYTICS-ORGID` header matches it. |
| 7301 | `SECURITY_NOT_PERMITTED` — The request came through a Client Portal / White Label domain, or the caller does not own this workspace. | Call from the standard API host as an Account Admin, Organization Admin, or the workspace's own admin. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.metadata.read`. |

---

## 3. Get AutoML Analysis Details

Returns the full definition of one analysis **together with every model trained under it** — including each model's ID, score, training status, and hyperparameters. This is the pivotal read in the family: it is the only source of `modelId`.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/automl/workspaces/<workspace-id>/analysis/<analysis-id>` |
| **OAuth Scope** | `ZohoAnalytics.metadata.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or the Workspace Admin (owner) of the specified workspace. |

> This API has no CONFIG parameter.

### Sample Requests

**Case 1 — Standard workspace**

```http
GET /restapi/v2/automl/workspaces/137687000271334001/analysis/137687000000061115 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — White Label / Client Portal: request sent through the portal domain (rejected)**

```http
GET /restapi/v2/automl/workspaces/137687000271334009/analysis/137687000000061119 HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
```

### Sample Responses

**HTTP 200 OK — Regression analysis whose two models are still training**

```json
{
    "status": "success",
    "summary": "Get autoML analysis details",
    "data": {
        "analysis": {
            "id": "137687000000061115",
            "name": "PricePredictionAnalysis",
            "description": "Predicts property price from listing attributes",
            "predictionType": "Regression",
            "trainingTable": "RealEstate_TrainData",
            "trainingTableId": "137687000000061002",
            "targetColumn": "Price",
            "features": [
                "City",
                "Bedrooms",
                "Bathrooms",
                "Garage"
            ],
            "stack": "8 GB",
            "status": "In progress",
            "models": [
                {
                    "id": "137687000000198124",
                    "name": "Random Forest Regression",
                    "score": "0",
                    "trainingStatus": "In Progress",
                    "lastTrainingTime": "28 Jan 2026 20:31:24",
                    "algorithm": {
                        "randomForestRegression": {
                            "minimumSampleSplit": "2",
                            "maximumDepth": "100",
                            "numberOfTrees": "25"
                        }
                    },
                    "isDeployed": false
                },
                {
                    "id": "137687000000198125",
                    "name": "Decision Tree Regression",
                    "score": "0",
                    "trainingStatus": "In Progress",
                    "lastTrainingTime": "28 Jan 2026 20:31:24",
                    "algorithm": {
                        "decisionTreeRegression": {
                            "minimumSampleSplit": "2",
                            "maximumDepth": "100"
                        }
                    },
                    "isDeployed": false
                }
            ]
        }
    }
}
```

**HTTP 200 OK — Classification analysis, training complete and one model already deployed**

```json
{
    "status": "success",
    "summary": "Get autoML analysis details",
    "data": {
        "analysis": {
            "id": "137687000000061116",
            "name": "ChurnPredictionAnalysis",
            "description": "Predicts customer churn",
            "predictionType": "Classification",
            "trainingTable": "Churn_TrainData",
            "trainingTableId": "137687000000061004",
            "targetColumn": "Churned",
            "features": [
                "Region",
                "Tenure",
                "MonthlyCharges"
            ],
            "stack": "16 GB",
            "status": "Completed",
            "models": [
                {
                    "id": "137687000000198130",
                    "name": "Random Forest Classification",
                    "scoreParamName": "Classification Accuracy",
                    "score": "38.95",
                    "trainingStatus": "Completed",
                    "lastTrainingTime": "28 Jan 2026 20:31:24",
                    "algorithm": {
                        "randomForestClassification": {
                            "minimumSampleSplit": "2",
                            "maximumDepth": "6",
                            "numberOfTrees": "25"
                        }
                    },
                    "isDeployed": true
                }
            ]
        }
    }
}
```

**HTTP 400 Bad Request — The analysis belongs to a different workspace**

```json
{
    "status": "failure",
    "summary": "ANALYSIS_NOT_BELONGS_TO_DB",
    "data": {
        "errorCode": 21000009,
        "errorMessage": "The given analysis does not belong to this workspace."
    }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `status` | String | `"success"` on a successful call, `"failure"` on error. |
| `summary` | String | Localised operation summary. `"Get autoML analysis details"` for this API. |
| `data` | JSONObject | Response payload wrapper. |
| `data.analysis` | JSONObject | The analysis definition. Always present on success. |
| `analysis.id` | String | ID of the analysis, as a string. |
| `analysis.name` | String | Name of the analysis. |
| `analysis.description` | String | Free-text description supplied at creation. |
| `analysis.predictionType` | String | `"Regression"`, `"Classification"`, or `"Clustering"` — title case. |
| `analysis.trainingTable` | String | Name of the training table. |
| `analysis.trainingTableId` | String | ID of the training table, as a string. |
| `analysis.targetColumn` | String | The column being predicted. Not meaningful for `Clustering` analyses, which are unsupervised. |
| `analysis.features` | JSONArray of String | Names of the input feature columns, in the order supplied at creation. |
| `analysis.stack` | String | Server memory the analysis runs on, in human-readable form (`"8 GB"`, `"16 GB"`, `"32 GB"`). Corresponds to the numeric `serverOption` that was sent at creation. |
| `analysis.status` | String | Status of the **analysis**, e.g. `"In progress"`, `"Completed"`. **Distinct from the top-level `status` field**, which reports the outcome of the API call itself. |
| `analysis.models` | JSONArray | One entry per algorithm configured at creation. **The only place `modelId` is exposed.** |
| `models[].id` | String | ID of the model, as a string. This is the `<model-id>` for [Get Deployments For A Model](#4-get-deployments-for-a-model), [Delete AutoML Analysis Model](#7-delete-automl-analysis-model), [Create AutoML Analysis Deployment](#8-create-automl-analysis-deployment), [AutoML What If Analysis](#11-automl-what-if-analysis). |
| `models[].name` | String | Display name of the algorithm, e.g. `"Random Forest Regression"`. This is a label, not the `algorithms` key used on the request — that key appears inside `algorithm`. |
| `models[].scoreParamName` | String | Name of the scoring metric, e.g. `"Classification Accuracy"`. The metric depends on the prediction type. Present once the model has been scored. |
| `models[].score` | String | The metric value, **returned as a string** even though it is numeric. Not meaningful until `trainingStatus` is `"Completed"`. |
| `models[].trainingStatus` | String | Training state of this individual model, e.g. `"In Progress"`, `"Completed"`, `"Failed"`. **Poll this field** — a model can only be deployed or used for What-If once it reads `"Completed"`. |
| `models[].lastTrainingTime` | String | When the model was last trained, in `dd MMM yyyy HH:mm:ss` format. |
| `models[].algorithm` | JSONObject | Single-key object: the algorithm key (e.g. `randomForestRegression`) mapped to its hyperparameters. |
| `models[].algorithm.<algorithm>.<parameter>` | String | Each hyperparameter's configured value, **returned as a string** even for parameters documented as Integer or Decimal on the request side. |
| `models[].isDeployed` | Boolean | `true` when a deployment already exists for this model. Because a model may hold only one deployment, `true` means [Create AutoML Analysis Deployment](#8-create-automl-analysis-deployment) will fail with `21000051`. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **The only source of `modelId`** | Neither list API returns models. Any deploy, model-delete, or What-If workflow must call this API first. |
| **This is the polling endpoint** | Training is asynchronous: [Create AutoML Analysis](#5-create-automl-analysis) returns as soon as the job is queued. Poll `models[].trainingStatus` until it reads `"Completed"` before attempting a deployment or a What-If. |
| **Two different `status` fields** | `data.analysis.status` is the training state of the analysis; the top-level `status` is `"success"`/`"failure"` for the HTTP call. Do not confuse them. |
| **Per-model status, not just per-analysis** | Models train independently, so one model may be `"Completed"` while another under the same analysis is still `"In Progress"` or has `"Failed"`. Always check the individual `models[].trainingStatus`. |
| **All numbers come back as strings** | `score` and every hyperparameter value are strings in the response, even though `algorithms` accepts them as numbers on the request. Round-tripping requires converting types. |
| **`isDeployed` is the deployability flag** | Check it before calling [Create AutoML Analysis Deployment](#8-create-automl-analysis-deployment) rather than catching `21000051`. |
| **Case asymmetry on `predictionType`** | Returned title case (`"Regression"`), accepted upper case (`REGRESSION`). |
| **Not callable from a portal domain** | See [White Label / Client Portal Behaviour](#white-label--client-portal-behaviour). |
| **Dependency chain** | [Create AutoML Analysis](#5-create-automl-analysis), [Get AutoML Analysis In Org](#1-get-automl-analysis-in-org), or [Get AutoML Analysis In Workspace](#2-get-automl-analysis-in-workspace) → `analysisId` → Get AutoML Analysis Details → `models[].id` → [Get Deployments For A Model](#4-get-deployments-for-a-model), [Delete AutoML Analysis Model](#7-delete-automl-analysis-model), [Create AutoML Analysis Deployment](#8-create-automl-analysis-deployment), [AutoML What If Analysis](#11-automl-what-if-analysis). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7103 | `META_OBJECT_NOT_PRESENT` — Workspace not found. | Verify `<workspace-id>` and the `ZANALYTICS-ORGID` header. |
| 7301 | `SECURITY_NOT_PERMITTED` — Portal-domain request, or the caller does not own this workspace. | Call from the standard API host as an owner of the workspace. |
| 21000009 | `ANALYSIS_NOT_BELONGS_TO_DB` — The analysis does not belong to the workspace in the URL, or does not exist. | Verify `<analysis-id>` against [Get AutoML Analysis In Workspace](#2-get-automl-analysis-in-workspace). |
| 21000014 | `AUTOML_NOT_ENABLED` / `AUTOML_PRICING_EXCEED` — AutoML is disabled for the organization, or its limit is exhausted. | See [Feature Enablement and Plan Limits](#feature-enablement-and-plan-limits). |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.metadata.read`. |

---

## 4. Get Deployments For A Model

Returns the deployment configured for a model — its input and output tables, schedule outcome, and last run status.

| Attribute | Value |
|-----------|-------|
| **Method** | GET |
| **URL** | `/restapi/v2/automl/workspaces/<workspace-id>/analysis/<analysis-id>/models/<model-id>/deployments` |
| **OAuth Scope** | `ZohoAnalytics.metadata.read` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or the Workspace Admin (owner) of the specified workspace. |

> This API has no CONFIG parameter.

### Sample Requests

**Case 1 — Standard workspace**

```http
GET /restapi/v2/automl/workspaces/137687000271334001/analysis/137687000000061115/models/137687000000198124/deployments HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — White Label / Client Portal: request sent through the portal domain (rejected)**

```http
GET /restapi/v2/automl/workspaces/137687000271334009/analysis/137687000000061119/models/137687000000198140/deployments HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
```

### Sample Responses

**HTTP 200 OK — Deployment whose most recent run is still executing**

```json
{
    "status": "success",
    "summary": "Get deployments for a model",
    "data": {
        "deployments": {
            "deploymentId": "137687000000198176",
            "analysisId": "137687000000061115",
            "inputTable": "RealEstate_TestData",
            "inputTableId": "137687000000061003",
            "outputTable": "PricePredictionOutput",
            "outputTableId": "137687000000198129",
            "status": "In progress",
            "lastDeploymentTime": "28 Jan 2026 20:35:10",
            "outputColumns": [
                "City",
                "Bedrooms",
                "Bathrooms",
                "Garage"
            ],
            "predictionColumn": "PricePrediction",
            "stack": "8 GB",
            "importType": "truncateadd"
        }
    }
}
```

**HTTP 200 OK — Deployment configured with UPDATEADD**

```json
{
    "status": "success",
    "summary": "Get deployments for a model",
    "data": {
        "deployments": {
            "deploymentId": "137687000000198180",
            "analysisId": "137687000000061115",
            "inputTable": "RealEstate_TestData",
            "inputTableId": "137687000000061003",
            "outputTable": "PricePredictionOutput",
            "outputTableId": "137687000000198131",
            "status": "Completed",
            "lastDeploymentTime": "28 Jan 2026 21:05:44",
            "outputColumns": [
                "City",
                "Bedrooms"
            ],
            "predictionColumn": "PricePrediction",
            "stack": "16 GB",
            "importType": "updateadd"
        }
    }
}
```

**HTTP 400 Bad Request — The model does not belong to the analysis in the URL**

```json
{
    "status": "failure",
    "summary": "MODEL_NOT_BELONGS_TO_ANALYSIS",
    "data": {
        "errorCode": 21000010,
        "errorMessage": "The given model does not belong to this analysis."
    }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `status` | String | `"success"` on a successful call, `"failure"` on error. |
| `summary` | String | Localised operation summary. `"Get deployments for a model"` for this API. |
| `data` | JSONObject | Response payload wrapper. |
| `data.deployments` | JSONObject | The deployment configured for the model. **A single object, not an array** — despite the plural key, a model can hold at most one deployment. |
| `deployments.deploymentId` | String | ID of the deployment, as a string. This is the `<deployment-id>` for [Run AutoML Analysis](#9-run-automl-analysis) and [Delete AutoML Analysis Model Deployment](#10-delete-automl-analysis-model-deployment). |
| `deployments.analysisId` | String | ID of the analysis the deployment belongs to. Echoes the URL. |
| `deployments.inputTable` | String | Name of the table whose rows are scored. |
| `deployments.inputTableId` | String | ID of that input table, as a string. |
| `deployments.outputTable` | String | Name of the table the predictions are written to. |
| `deployments.outputTableId` | String | ID of the output table. Use it with the [Row / Export APIs](ROW_API_DOC_INFO.md) to read the predictions. |
| `deployments.status` | String | Status of the **most recent run** of the deployment, e.g. `"In progress"`, `"Completed"`. **Distinct from the top-level `status`.** |
| `deployments.lastDeploymentTime` | String | When the deployment last ran, in `dd MMM yyyy HH:mm:ss` format. |
| `deployments.outputColumns` | JSONArray of String | Columns copied from the input table into the output table alongside the prediction. |
| `deployments.predictionColumn` | String | Name of the column in the output table that holds the predicted value. |
| `deployments.stack` | String | Server memory used for the deployment job (`"8 GB"`, `"16 GB"`, `"32 GB"`). |
| `deployments.importType` | String | How predictions are written to the output table. **Returned in lower case** (`"truncateadd"`, `"append"`, `"updateadd"`), whereas [Create AutoML Analysis Deployment](#8-create-automl-analysis-deployment) expects upper case. |

> `matchingColumns` and the schedule definition are **not** returned, even for an `updateadd` deployment. Retain them yourself if you need to reproduce a deployment.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Plural key, singular value** | `data.deployments` is a JSONObject, not a JSONArray, because the one-deployment-per-model rule makes a list unnecessary. Do not iterate it. |
| **Two different `status` fields** | `deployments.status` is the outcome of the last scoring run; the top-level `status` is the HTTP call result. |
| **The run-status polling endpoint** | [Run AutoML Analysis](#9-run-automl-analysis) returns 204 immediately without a job handle. This API is the only way to observe whether that run finished. |
| **`outputTableId` is the handoff to the data APIs** | The predictions themselves are ordinary table rows — read them with the [Row / Export APIs](ROW_API_DOC_INFO.md) using this ID. |
| **Case asymmetry on `importType`** | Lower case here, upper case on the request. |
| **Schedule is not echoed** | The `scheduleDetails` sent at creation cannot be read back through any API. |
| **Not callable from a portal domain** | See [White Label / Client Portal Behaviour](#white-label--client-portal-behaviour). |
| **Dependency chain** | [Get AutoML Analysis Details](#3-get-automl-analysis-details) → `modelId` → Get Deployments For A Model → `deploymentId` → [Run AutoML Analysis](#9-run-automl-analysis) / [Delete AutoML Analysis Model Deployment](#10-delete-automl-analysis-model-deployment). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7103 | `META_OBJECT_NOT_PRESENT` — Workspace not found. | Verify `<workspace-id>` and the `ZANALYTICS-ORGID` header. |
| 7301 | `SECURITY_NOT_PERMITTED` — Portal-domain request, or the caller does not own this workspace. | Call from the standard API host as an owner of the workspace. |
| 21000009 | `ANALYSIS_NOT_BELONGS_TO_DB` — The analysis is not in this workspace. | Verify `<analysis-id>`. |
| 21000010 | `MODEL_NOT_BELONGS_TO_ANALYSIS` — The model is not part of this analysis. | Verify `<model-id>` via [Get AutoML Analysis Details](#3-get-automl-analysis-details). |
| 21000014 | `AUTOML_NOT_ENABLED` / `AUTOML_PRICING_EXCEED` — AutoML is disabled or over limit. | See [Feature Enablement and Plan Limits](#feature-enablement-and-plan-limits). |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.metadata.read`. |

---

## 5. Create AutoML Analysis

Creates an analysis and **immediately starts training one model per configured algorithm**. Returns as soon as the training job is queued — it does not wait for training to finish.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/automl/workspaces/<workspace-id>/analysis` |
| **OAuth Scope** | `ZohoAnalytics.modeling.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or the Workspace Admin (owner) of the specified workspace. |

### CONFIG Parameters

CONFIG is **mandatory** for this API.

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `name` | String | **Yes** | — | Name of the analysis. Must be **unique within the workspace** (`21000003` otherwise) and **at most 50 characters** (`21000020` otherwise). An empty string is rejected with `21000023`. |
| `trainingTableId` | Long | **Yes** | — | ID of the table the model is trained on. Must belong to `<workspace-id>` (`7319` otherwise). |
| `predictionType` | String (enum) | **Yes** | — | `REGRESSION`, `CLASSIFICATION`, or `CLUSTERING`. Case-insensitive on input. Determines which algorithm keys are valid in `algorithms`. See [`predictionType` Values](#predictiontype-values). |
| `targetColumn` | String | Conditional | — | Name of the column to predict. **Mandatory for `REGRESSION` and `CLASSIFICATION`; not used by `CLUSTERING`**, which is unsupervised. Must exist in the training table (`21000030` otherwise) and must **not** also appear in `features` (`21000048` otherwise). |
| `features` | JSONArray of String | **Yes** | — | Input feature column names from the training table. **Minimum 3, maximum 20** (`21000026` / `21000027`). Duplicates are rejected (`21000047`). Every name must exist in the training table (`21000028`). The one exception is the `maxEntropy` algorithm, which requires **exactly one** feature (`21000024`). |
| `serverOption` | Integer (enum) | **Yes** | — | Server memory for the training job: `1` = 8 GB, `2` = 16 GB, `3` = 32 GB. Any other value fails with `8119`. |
| `algorithms` | JSONObject | **Yes** | — | Algorithm keys mapped to their hyperparameters. **One model is trained per key.** Up to 15 algorithms. See [`algorithms` Values](#algorithms-values). |
| `description` | String | No | — | Free-text description. Maximum 1,000 characters (`21000021` otherwise). |

#### `predictionType` Values

| Value | Meaning | `targetColumn` | Valid algorithm keys |
|-------|---------|----------------|----------------------|
| `REGRESSION` | Predicts a continuous numeric value (e.g. a price). | **Required** | `decisionTreeRegression`, `randomForestRegression`, `olsRegression`, `lassoRegression`, `ridgeRegression`, `svmRegressor`, `gradientBoostingRegression` |
| `CLASSIFICATION` | Predicts a discrete class label (e.g. churn yes/no). | **Required** | `gradientBoostingClassification`, `adaptiveBoost`, `decisionTreeClassification`, `randomForestClassification`, `logisticRegression`, `linearDiscriminantAnalysis`, `maxEntropy` |
| `CLUSTERING` | Groups similar records without a labelled outcome. | **Not used** | `kMeansPP`, `kModes`, `kPrototypes`, `xMeans`, `gMeans` |

> Using an algorithm key that does not belong to the chosen `predictionType` fails with `21000016` `INVALID_ALGORITHM`, naming the offending key.

#### `algorithms` Values

`algorithms` is a JSONObject whose **keys are algorithm names** and whose values are that algorithm's hyperparameter object. Sending three keys trains three models under the same analysis. Every hyperparameter is optional — omitting the object entirely (`{}`) trains the algorithm with its defaults.

| Algorithm key | Prediction type | Hyperparameters |
|---------------|-----------------|-----------------|
| `decisionTreeRegression` | Regression | `minimumSampleSplit` (Integer), `maximumDepth` (Integer) |
| `randomForestRegression` | Regression | `minimumSampleSplit` (Integer), `maximumDepth` (Integer), `numberOfTrees` (Integer) |
| `olsRegression` | Regression | `intercept` (Boolean), `allowAlternateModel` (Boolean) |
| `lassoRegression` | Regression | `tolerance` (Decimal), `shrinkage` (Integer), `maximumIterations` (Integer) |
| `ridgeRegression` | Regression | `shrinkage` (Integer) |
| `svmRegressor` | Regression | `epsilon` (Decimal), `softMargin` (Decimal), `tolerance` (Decimal), `epochs` (Integer) |
| `gradientBoostingRegression` | Regression | `lossFunction` (`LEASTSQUARES` \| `QUANTILE` \| `LEASTABSOLUTEDEVIATION` \| `HUBER`), `maximumDepth`, `maximumNodes`, `nodeSize`, `numberOfTrees` (Integer), `shrinkage`, `subSample` (Decimal) |
| `gradientBoostingClassification` | Classification | Same set as `gradientBoostingRegression` |
| `adaptiveBoost` | Classification | `maximumDepth`, `maximumNodes`, `nodeSize`, `numberOfTrees` (Integer) |
| `decisionTreeClassification` | Classification | `minimumSampleSplit` (Integer), `maximumDepth` (Integer) |
| `randomForestClassification` | Classification | `minimumSampleSplit` (Integer), `maximumDepth` (Integer), `numberOfTrees` (Integer) |
| `logisticRegression` | Classification | `lambda` (Decimal), `maximumIterations` (Integer), `tolerance` (Decimal) |
| `linearDiscriminantAnalysis` | Classification | `tolerance` (Decimal) |
| `maxEntropy` | Classification | `lambda` (Decimal), `maximumIterations` (Integer), `tolerance` (Decimal) |
| `kMeansPP` | Clustering | `clustersCount` (Integer), `kMax` (Integer), `chIndexBasedOptimalK` (Boolean), `calculatePerformanceMetrics` (Boolean) |
| `kModes` | Clustering | `clustersCount`, `minimumClusterCount`, `maximumClusterCount` (Integer), `dissimilarityMeasure` (`BINARY` \| `GLOBAL_FREQUENCY` \| `RELATIVE_FREQUENCY` \| `JARO_WINKLER` \| `LEVENSHTEIN` \| `JACCARD`) |
| `kPrototypes` | Clustering | `clustersCount` (Integer), `kMax` (Integer), `chIndexBasedOptimalK` (Boolean), `gamma` (Decimal) |
| `xMeans` | Clustering | `kMax` (Integer), `maximumIterations` (Integer), `tolerance` (Decimal) |
| `gMeans` | Clustering | `kMax` (Integer), `maximumIterations` (Integer), `tolerance` (Decimal) |

> **`maxEntropy` is exclusive.** If `maxEntropy` is present it must be the **only** key in `algorithms` (`21000025` otherwise), and `features` must contain **exactly one** column (`21000024` otherwise). Every other algorithm requires at least 3 features.
>
> Unknown hyperparameter names fail with `21000018`; out-of-range or wrongly typed values fail with `21000031`–`21000035`.

### Sample Requests

**Case 1 — Regression with a single algorithm, minimal configuration**

```http
POST /restapi/v2/automl/workspaces/137687000271334001/analysis HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "name": "PricePredictionAnalysis",
    "trainingTableId": 137687000000061002,
    "predictionType": "REGRESSION",
    "targetColumn": "Price",
    "features": ["City", "Bedrooms", "Bathrooms"],
    "serverOption": 1,
    "algorithms": {
        "randomForestRegression": {}
    }
}
```

**Case 2 — Regression with description, larger server, and two algorithms with tuned hyperparameters (two models are trained)**

```http
POST /restapi/v2/automl/workspaces/137687000271334001/analysis HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "name": "PricePredictionTuned",
    "description": "Predicts property price from listing attributes",
    "trainingTableId": 137687000000061002,
    "predictionType": "REGRESSION",
    "targetColumn": "Price",
    "features": ["City", "Bedrooms", "Bathrooms", "Garage"],
    "serverOption": 2,
    "algorithms": {
        "randomForestRegression": {
            "minimumSampleSplit": 2,
            "maximumDepth": 20,
            "numberOfTrees": 25
        },
        "ridgeRegression": {
            "shrinkage": 1
        }
    }
}
```

**Case 3 — Classification with a boosted algorithm**

```http
POST /restapi/v2/automl/workspaces/137687000271334001/analysis HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "name": "ChurnPredictionAnalysis",
    "trainingTableId": 137687000000061004,
    "predictionType": "CLASSIFICATION",
    "targetColumn": "Churned",
    "features": ["Region", "Tenure", "MonthlyCharges"],
    "serverOption": 2,
    "algorithms": {
        "gradientBoostingClassification": {
            "lossFunction": "HUBER",
            "numberOfTrees": 50,
            "maximumDepth": 6,
            "shrinkage": 0.1
        }
    }
}
```

**Case 4 — Clustering, with no `targetColumn`**

```http
POST /restapi/v2/automl/workspaces/137687000271334001/analysis HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "name": "SegmentationAnalysis",
    "trainingTableId": 137687000000061002,
    "predictionType": "CLUSTERING",
    "features": ["City", "Bedrooms", "Bathrooms"],
    "serverOption": 1,
    "algorithms": {
        "kMeansPP": {
            "clustersCount": 5,
            "chIndexBasedOptimalK": false,
            "calculatePerformanceMetrics": true
        }
    }
}
```

### Sample Responses

**HTTP 200 OK — Analysis created and training queued**

```json
{
    "status": "success",
    "summary": "Create autoML analysis",
    "data": {
        "id": "137687000000061115"
    }
}
```

**HTTP 400 Bad Request — Duplicate analysis name**

```json
{
    "status": "failure",
    "summary": "ANALYSISNAME_DUPLICATED",
    "data": {
        "errorCode": 21000003,
        "errorMessage": "A similar analysis named PricePredictionAnalysis already exists in this workspace. Please choose a different name."
    }
}
```

**HTTP 400 Bad Request — Algorithm not valid for the chosen prediction type**

```json
{
    "status": "failure",
    "summary": "INVALID_ALGORITHM",
    "data": {
        "errorCode": 21000016,
        "errorMessage": "supportVectorRegression is not a valid algorithm. Please choose a supported algorithm."
    }
}
```

**HTTP 400 Bad Request — AutoML not enabled for the organization**

```json
{
    "status": "failure",
    "summary": "AUTOML_NOT_ENABLED",
    "data": {
        "errorCode": 21000014,
        "errorMessage": "The AutoML Feature is not enabled. Please enable the features from Org Settings > Feature Controls > DSML."
    }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `status` | String | `"success"` on a successful call, `"failure"` on error. |
| `summary` | String | Localised operation summary. `"Create autoML analysis"` for this API. |
| `data` | JSONObject | Response payload wrapper. |
| `data.id` | String | ID of the newly created analysis, as a string. Note the key is **`id`**, not `analysisId`. Use it as `<analysis-id>` everywhere else. |

> **No model IDs are returned.** Models are created asynchronously as training starts — fetch them from [Get AutoML Analysis Details](#3-get-automl-analysis-details).

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Asynchronous — 200 means "queued", not "trained"** | The call returns as soon as the analysis row and its training job exist. Poll `models[].trainingStatus` via [Get AutoML Analysis Details](#3-get-automl-analysis-details) until it reads `"Completed"`. |
| **One algorithm key = one model** | The `algorithms` object is a fan-out: three keys produce three independently trained, independently scored, independently deployable models. This is how you compare algorithms in a single request. |
| **Analyses are immutable** | There is no update API. Changing the training table, target column, feature list, algorithms, or server option means deleting the analysis and creating a new one. |
| **`name` max length is 50, not 60** | The published request template allows 60 characters, but the server rejects anything over 50 with `21000020`. Budget for 50. |
| **Feature count is 3–20** | Below 3 fails with `21000026`; above 20 fails with `21000027`. This is stricter than the 1–100 range in the published schema. The sole exception is `maxEntropy`, which requires exactly 1. |
| **`targetColumn` must not be a feature** | Including the predicted column among the inputs fails with `21000048` — a common mistake that would leak the answer into the model. |
| **`CLUSTERING` takes no `targetColumn`** | It is unsupervised; the attribute is ignored rather than required. |
| **Training table must be in the workspace** | A table from another workspace fails with `7319`, and a non-existent ID surfaces as `7005`. |
| **No `criteria`** | The training set is the whole table. To train on a subset, build a filtered query table or view first and use that as `trainingTableId`. |
| **Not callable from a portal domain** | See [White Label / Client Portal Behaviour](#white-label--client-portal-behaviour). |
| **Dependency chain** | [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → `trainingTableId` → Create AutoML Analysis → `data.id` → [Get AutoML Analysis Details](#3-get-automl-analysis-details). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7005 | `COMMON_INTERNAL_SERVER_ERROR` — Surfaces when `trainingTableId` does not identify a real table. | Verify the ID via [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list). |
| 7103 | `META_OBJECT_NOT_PRESENT` — Workspace not found. | Verify `<workspace-id>` and the `ZANALYTICS-ORGID` header. |
| 7301 | `SECURITY_NOT_PERMITTED` — Portal-domain request, or the caller does not own this workspace. | Call from the standard API host as an owner of the workspace. |
| 7319 | `OBJID_NOT_BELONGS_TO_DB` — The training table belongs to a different workspace. | Use a table from `<workspace-id>`. |
| 8078 | `EMPTY_JSON_ATTRIBUTE_FOUND` — A mandatory attribute was sent empty. | Supply a value. |
| 8079 | `ATTRIBUTE_NOT_PRESENT_IN_JSON_CONFIGURATION` — A mandatory attribute is missing. | The message names the attribute. |
| 8119 | `INVALID_VALUE_FOR_ATTRIBUTE` — `serverOption` or `predictionType` is outside its allowed set. | The message names the attribute and permitted values. |
| 8504 | `LESS_THAN_MIN_OCCURANCE` — CONFIG is absent, or a required key is missing at the template level. | Send a complete CONFIG object. |
| 8547 | `ARRAY_SIZE_OUT_OF_RANGE` — `features` is empty or exceeds the allowed array size. | Send between 3 and 20 feature names. |
| 21000003 | `ANALYSISNAME_DUPLICATED` — An analysis with this `name` already exists in the workspace. | Choose a different name. |
| 21000014 | `AUTOML_NOT_ENABLED` / `AUTOML_PRICING_EXCEED` — AutoML is disabled or over limit. | See [Feature Enablement and Plan Limits](#feature-enablement-and-plan-limits). |
| 21000016 | `INVALID_ALGORITHM` — An algorithm key is not valid for the chosen `predictionType`. | Use a key from [`predictionType` Values](#predictiontype-values). |
| 21000018 | `INVALID_HYPERPARAM` — A hyperparameter name is not recognised for that algorithm. | Use the parameters listed in [`algorithms` Values](#algorithms-values). |
| 21000020 | `ANLAYSIS_NAME_MAXLENGTH` — `name` is longer than 50 characters. | Shorten the name. |
| 21000021 | `DESCRIPTION_MAXLENGTH_ERROR` — `description` exceeds 1,000 characters. | Shorten the description. |
| 21000023 | `ANLAYSIS_NAME_EMPTY` — `name` is an empty string. | Supply a non-empty name. |
| 21000024 | `MAXENTROPY_MIN_FEATURE_ERROR` — `maxEntropy` was used with other than exactly one feature. | Send exactly one feature for `maxEntropy`. |
| 21000025 | `MAXENTROPY_MIN_ALGO_ERROR` — `maxEntropy` was combined with other algorithms. | Send `maxEntropy` on its own. |
| 21000026 | `FEATURES_MIN_ERROR` — Fewer than 3 features supplied. | Send at least 3. |
| 21000027 | `FEATURES_MAX_ERROR` — More than 20 features supplied. | Send at most 20. |
| 21000028 | `FEATURE_MISSING_IN_TABLE_ERROR` — A feature name does not exist in the training table. | Verify names via [Get Columns](COLUMNS_API_DOC_INFO.md). |
| 21000029 | `INVALID_DATATYPE_FOR_FEATURE` — A feature's data type is not usable by the chosen algorithm. | Choose a different column or algorithm. |
| 21000030 | `TARGETCOL_MISSING_IN_TABLE_ERROR` — `targetColumn` does not exist in the training table. | Verify the column name. |
| 21000031–21000035 | `INVALID_DATATYPE_HYPERPARAM_ERROR`, `HYPERPARAM_BTWN_ERROR`, `HYPERPARAM_MINVAL_ERROR`, `HYPERPARAM_MAXVAL_ERROR`, `HYPERPARAM_DROPLIST_ERROR` — A hyperparameter value is the wrong type, out of range, or not in its allowed list. | Correct the value named in the message. |
| 21000047 | `FEATURE_DUPLICATION_ERROR` — `features` contains duplicates. | Remove the duplicates. |
| 21000048 | `TARGETCOL_IN_FEATURELIST_ERROR` — `targetColumn` also appears in `features`. | Remove it from `features`. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.modeling.create`. |

---

## 6. Delete AutoML Analysis

Deletes an analysis **and everything beneath it** — all its models, and all deployments attached to those models.

| Attribute | Value |
|-----------|-------|
| **Method** | DELETE |
| **URL** | `/restapi/v2/automl/workspaces/<workspace-id>/analysis/<analysis-id>` |
| **OAuth Scope** | `ZohoAnalytics.modeling.delete` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or the Workspace Admin (owner) of the specified workspace. |

> This API has no CONFIG parameter.

### Sample Requests

**Case 1 — Standard workspace**

```http
DELETE /restapi/v2/automl/workspaces/137687000271334001/analysis/137687000000061115 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — White Label / Client Portal: request sent through the portal domain (rejected)**

```http
DELETE /restapi/v2/automl/workspaces/137687000271334009/analysis/137687000000061119 HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status.

```
HTTP/1.1 204 No Content
```

**HTTP 403 Forbidden — Caller has no AutoML access in this workspace**

```json
{
    "status": "failure",
    "summary": "SECURITY_NOT_PERMITTED",
    "data": {
        "errorCode": 7301,
        "errorMessage": "You (NormalUser) do not have the permission to do this operation. "
    }
}
```

**HTTP 400 Bad Request — The analysis belongs to a different workspace**

```json
{
    "status": "failure",
    "summary": "ANALYSIS_NOT_BELONGS_TO_DB",
    "data": {
        "errorCode": 21000009,
        "errorMessage": "The given analysis does not belong to this workspace."
    }
}
```

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload (`status`, `summary`, `data.errorCode`, `data.errorMessage`).

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Delete AutoML Analysis returns a bare HTTP `204 No Content` — no `status`/`summary` JSON, and no report of how many models or deployments were removed. |
| **Cascades over the whole subtree** | Every model under the analysis, and every deployment under those models, is deleted in the same call. There is no partial or "detach only" mode. |
| **Output tables survive** | Tables that deployments created, and the prediction rows already written into them, remain in the workspace. Remove them separately with [Delete View](VIEW_OPERATIONS_API_DOC_INFO.md#5-delete-view) if they are no longer needed. |
| **Training table is untouched** | The source table used for training is a normal workspace table and is never affected. |
| **No trash, no restore** | A deleted analysis cannot be recovered. Recreating it produces new analysis, model, and deployment IDs, and training starts from scratch. |
| **Not idempotent** | Deleting the same analysis twice fails with `21000009`, because the ID no longer resolves within the workspace. |
| **Frees AutoML capacity** | Removing an analysis releases the allowance it consumed, so a create that previously failed with `21000014` may then succeed. |
| **Not callable from a portal domain** | See [White Label / Client Portal Behaviour](#white-label--client-portal-behaviour). |
| **Dependency chain** | [Get AutoML Analysis In Workspace](#2-get-automl-analysis-in-workspace) → `analysisId` → Delete AutoML Analysis. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7103 | `META_OBJECT_NOT_PRESENT` — Workspace not found. | Verify `<workspace-id>` and the `ZANALYTICS-ORGID` header. |
| 7301 | `SECURITY_NOT_PERMITTED` — Portal-domain request, or the caller does not own this workspace. | Call from the standard API host as an owner of the workspace. |
| 21000009 | `ANALYSIS_NOT_BELONGS_TO_DB` — The analysis is not in this workspace, or was already deleted. | Verify `<analysis-id>` via [Get AutoML Analysis In Workspace](#2-get-automl-analysis-in-workspace). |
| 21000014 | `AUTOML_NOT_ENABLED` / `AUTOML_PRICING_EXCEED` — AutoML is disabled or over limit. | See [Feature Enablement and Plan Limits](#feature-enablement-and-plan-limits). |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.modeling.delete`. |

---

## 7. Delete AutoML Analysis Model

Deletes one model from an analysis, along with the deployment attached to it. The analysis and its other models are unaffected.

| Attribute | Value |
|-----------|-------|
| **Method** | DELETE |
| **URL** | `/restapi/v2/automl/workspaces/<workspace-id>/analysis/<analysis-id>/models/<model-id>` |
| **OAuth Scope** | `ZohoAnalytics.modeling.delete` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or the Workspace Admin (owner) of the specified workspace. |

> This API has no CONFIG parameter.

### Sample Requests

**Case 1 — Discard a poorly scoring model, keeping the rest of the analysis**

```http
DELETE /restapi/v2/automl/workspaces/137687000271334001/analysis/137687000000061115/models/137687000000198125 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — White Label / Client Portal: request sent through the portal domain (rejected)**

```http
DELETE /restapi/v2/automl/workspaces/137687000271334009/analysis/137687000000061119/models/137687000000198140 HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status.

```
HTTP/1.1 204 No Content
```

**HTTP 400 Bad Request — The model does not belong to the analysis in the URL**

```json
{
    "status": "failure",
    "summary": "MODEL_NOT_BELONGS_TO_ANALYSIS",
    "data": {
        "errorCode": 21000010,
        "errorMessage": "The given model does not belong to this analysis."
    }
}
```

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Delete AutoML Analysis Model returns a bare HTTP `204 No Content`. |
| **Takes the model's deployment with it** | If the model was deployed, that deployment is removed too. The output table and its rows survive. |
| **The analysis survives, even if emptied** | Deleting every model one by one leaves the analysis in place with an empty `models` array; it does not auto-delete. Use [Delete AutoML Analysis](#6-delete-automl-analysis) to remove the whole thing. |
| **Models cannot be recreated individually** | There is no "add model" or "retrain" API. Once deleted, getting that algorithm back means creating a new analysis with it in `algorithms`. |
| **Not idempotent** | A repeat delete fails with `21000010`. |
| **Both path IDs are verified** | The analysis must belong to the workspace (`21000009`) and the model must belong to the analysis (`21000010`) — mismatched IDs are rejected rather than silently ignored. |
| **Not callable from a portal domain** | See [White Label / Client Portal Behaviour](#white-label--client-portal-behaviour). |
| **Dependency chain** | [Get AutoML Analysis Details](#3-get-automl-analysis-details) → `models[].id` → Delete AutoML Analysis Model. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7103 | `META_OBJECT_NOT_PRESENT` — Workspace not found. | Verify `<workspace-id>` and the `ZANALYTICS-ORGID` header. |
| 7301 | `SECURITY_NOT_PERMITTED` — Portal-domain request, or the caller does not own this workspace. | Call from the standard API host as an owner of the workspace. |
| 21000009 | `ANALYSIS_NOT_BELONGS_TO_DB` — The analysis is not in this workspace. | Verify `<analysis-id>`. |
| 21000010 | `MODEL_NOT_BELONGS_TO_ANALYSIS` — The model is not part of this analysis, or was already deleted. | Verify `<model-id>` via [Get AutoML Analysis Details](#3-get-automl-analysis-details). |
| 21000014 | `AUTOML_NOT_ENABLED` / `AUTOML_PRICING_EXCEED` — AutoML is disabled or over limit. | See [Feature Enablement and Plan Limits](#feature-enablement-and-plan-limits). |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.modeling.delete`. |

---

## 8. Create AutoML Analysis Deployment

Binds a trained model to an input table and an output table so that predictions can be generated — on a recurring schedule, on demand, or both. Returns the new deployment ID and the ID of the output table it created.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/automl/workspaces/<workspace-id>/analysis/<analysis-id>/models/<model-id>/deployments` |
| **OAuth Scope** | `ZohoAnalytics.modeling.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or the Workspace Admin (owner) of the specified workspace. |

### CONFIG Parameters

CONFIG is **mandatory** for this API.

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `inputTableId` | Long | **Yes** | — | ID of the table whose rows are scored. Must belong to `<workspace-id>` (`7319` otherwise) and must contain **every feature column the model was trained on** (`21000001` otherwise). |
| `outputTable` | String | **Yes** | — | Name of the table the predictions are written to. Created automatically if it does not exist. Must be non-empty (`21000037`) and at most 100 characters (`21000039`). |
| `outputColumns` | JSONArray of String | **Yes** | — | Columns copied from the input table into the output table alongside the prediction. 1–100 entries; must not be empty (`21000041`) and every name must exist in the input table. |
| `predictionColumn` | String | **Yes** | — | Name of the new column that holds the predicted value. Must be non-empty (`21000036`) and at most 100 characters (`21000040`). |
| `importType` | String (enum) | **Yes** | — | How results are written to the output table. `APPEND`, `TRUNCATEADD`, or `UPDATEADD`. Case-insensitive on input; an unrecognised value fails with `21000022`. See [`importType` Values](#importtype-values). |
| `serverOption` | Integer (enum) | **Yes** | — | Server memory for the scoring job: `1` = 8 GB, `2` = 16 GB, `3` = 32 GB. Any other value fails with `8119`. |
| `scheduleDetails` | JSONObject | **Yes** | — | When the deployment runs automatically. Send `{"calendarFrequency": "none"}` for an on-demand-only deployment. See [`scheduleDetails` Fields](#scheduledetails-fields). |
| `matchingColumns` | JSONArray of String | Conditional | — | **Mandatory when `importType` is `UPDATEADD`**, ignored otherwise. Columns used to match existing output rows. Must be non-empty (`21000038`), exist in the input table, and be a **subset of `outputColumns`** (`21000042` otherwise). 1–100 entries. |
| `timezone` | String | No | Organization default | Timezone the schedule runs in, e.g. `Asia/Kolkata`. Must be a recognised timezone name (`8050` otherwise). |

#### `importType` Values

| Value | Behaviour |
|-------|-----------|
| `TRUNCATEADD` | Deletes all existing rows in the output table, then writes the new predictions. Use for a full refresh. |
| `APPEND` | Adds the new predictions to the output table as additional rows, keeping the existing ones. Use to accumulate a history of runs. |
| `UPDATEADD` | Updates rows whose `matchingColumns` values match, and inserts the rest. Use to keep one current prediction per entity. **Requires `matchingColumns`.** |

#### `scheduleDetails` Fields

| Field | Type | Mandatory | Description |
|-------|------|-----------|--------------|
| `calendarFrequency` | String (enum) | **Yes** | `none`, `hourly`, `daily`, `weekly`, or `monthly`. `none` creates a deployment with no automatic schedule — run it with [Run AutoML Analysis](#9-run-automl-analysis). |
| `interval` | Integer | **Yes** for `hourly` | Hours between runs. Only `1`, `2`, `3`, `6`, and `12` are accepted (`8119` otherwise). |
| `hour` | Integer | **Yes** for `daily`, `weekly`, `monthly` | Hour of the day, **0–23** (`8119` otherwise). |
| `minute` | Integer | **Yes** for `daily`, `weekly`, `monthly` | Minute within the hour. Must be a **multiple of 5 in the range 0–55** (`8119` otherwise). |
| `day` | Integer | **Yes** for `weekly`, `monthly` | For `weekly`, the day of the week, `1` = Sunday … `7` = Saturday. For `monthly`, the day of the month, `1`–`31`, or `99` for the last day of the month. **See the caveat below.** |
| `skipFrequency` | Integer | No | Number of periods to skip between runs. Defaults to `0` (every period). |

> **Caveat on weekly and monthly schedules.** The published request template declares `weekDay`, `monthDay`, and `hourInterval`, but the server does not read any of them — it reads `day` for weekly/monthly and `interval` for hourly. Sending `monthDay` for a monthly schedule fails with `8079` *"Attribute 'day' not present in the JSON configuration"*, and `day` itself is not among the template's declared keys. **Only `none`, `daily`, and `hourly` (using `interval`) are confirmed working.** Until this is resolved, create weekly/monthly deployments with `{"calendarFrequency": "none"}` and drive them from your own scheduler through [Run AutoML Analysis](#9-run-automl-analysis).

### Sample Requests

**Case 1 — On-demand deployment (no schedule), full refresh each run**

```http
POST /restapi/v2/automl/workspaces/137687000271334001/analysis/137687000000061115/models/137687000000198124/deployments HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "inputTableId": 137687000000061003,
    "outputTable": "PricePredictionOutput",
    "outputColumns": ["City", "Bedrooms", "Bathrooms", "Garage"],
    "predictionColumn": "PricePrediction",
    "importType": "TRUNCATEADD",
    "serverOption": 1,
    "scheduleDetails": {
        "calendarFrequency": "none"
    }
}
```

**Case 2 — Daily schedule with a timezone, appending each run's predictions**

```http
POST /restapi/v2/automl/workspaces/137687000271334001/analysis/137687000000061115/models/137687000000198124/deployments HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "inputTableId": 137687000000061003,
    "outputTable": "PricePredictionHistory",
    "outputColumns": ["City", "Bedrooms", "Bathrooms", "Garage"],
    "predictionColumn": "PricePrediction",
    "importType": "APPEND",
    "serverOption": 2,
    "timezone": "Asia/Kolkata",
    "scheduleDetails": {
        "calendarFrequency": "daily",
        "hour": 10,
        "minute": 30
    }
}
```

**Case 3 — Hourly schedule with UPDATEADD and matching columns clubbed together**

```http
POST /restapi/v2/automl/workspaces/137687000271334001/analysis/137687000000061115/models/137687000000198124/deployments HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "inputTableId": 137687000000061003,
    "outputTable": "PricePredictionCurrent",
    "outputColumns": ["City", "Bedrooms", "Bathrooms", "Garage"],
    "predictionColumn": "PricePrediction",
    "importType": "UPDATEADD",
    "matchingColumns": ["City", "Bedrooms"],
    "serverOption": 3,
    "timezone": "Asia/Kolkata",
    "scheduleDetails": {
        "calendarFrequency": "hourly",
        "interval": 3
    }
}
```

**Case 4 — White Label / Client Portal: request sent through the portal domain (rejected)**

```http
POST /restapi/v2/automl/workspaces/137687000271334009/analysis/137687000000061119/models/137687000000198140/deployments HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "inputTableId": 137687000000061013,
    "outputTable": "PortalPredictions",
    "outputColumns": ["Region"],
    "predictionColumn": "Prediction",
    "importType": "TRUNCATEADD",
    "serverOption": 1,
    "scheduleDetails": {
        "calendarFrequency": "none"
    }
}
```

### Sample Responses

**HTTP 200 OK — Deployment created**

```json
{
    "status": "success",
    "summary": "Create autoML analysis deployment",
    "data": {
        "deployments": {
            "outputTableId": "137687000000198129",
            "deploymentId": "137687000000198176"
        }
    }
}
```

**HTTP 400 Bad Request — The model already has a deployment**

```json
{
    "status": "failure",
    "summary": "MODEL_ALREADY_DEPLOYED",
    "data": {
        "errorCode": 21000051,
        "errorMessage": "A deployment already exists for this model."
    }
}
```

**HTTP 400 Bad Request — `serverOption` outside the allowed set**

```json
{
    "status": "failure",
    "summary": "INVALID_VALUE_FOR_ATTRIBUTE",
    "data": {
        "errorCode": 8119,
        "errorMessage": "Invalid value '5' provided for the attribute 'serverOption'. Only '1, 2 and 3' are allowed."
    }
}
```

**HTTP 400 Bad Request — Unrecognised timezone**

```json
{
    "status": "failure",
    "summary": "INVALID_VALUE",
    "data": {
        "errorCode": 8050,
        "errorMessage": "Invalid input: invalid_timezone."
    }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `status` | String | `"success"` on a successful call, `"failure"` on error. |
| `summary` | String | Localised operation summary. `"Create autoML analysis deployment"` for this API. |
| `data` | JSONObject | Response payload wrapper. |
| `data.deployments` | JSONObject | Details of the deployment just created. A single object, not an array. |
| `deployments.deploymentId` | String | ID of the new deployment, as a string. Use as `<deployment-id>` in [Run AutoML Analysis](#9-run-automl-analysis) and [Delete AutoML Analysis Model Deployment](#10-delete-automl-analysis-model-deployment). |
| `deployments.outputTableId` | String | ID of the output table, as a string — newly created if `outputTable` did not already exist. Read the predictions from it with the [Row / Export APIs](ROW_API_DOC_INFO.md). |

> Only these two IDs are returned. The full deployment definition can be read back with [Get Deployments For A Model](#4-get-deployments-for-a-model).

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **The model must be trained first** | Deploying a model that is still training fails with `21000052`; one whose training failed fails with `21000053`. Poll `models[].trainingStatus` via [Get AutoML Analysis Details](#3-get-automl-analysis-details) until it reads `"Completed"`. |
| **One deployment per model** | A second deployment on the same model fails with `21000051`. To change a deployment's configuration, delete it with [Delete AutoML Analysis Model Deployment](#10-delete-automl-analysis-model-deployment) and create a new one — there is no update API. |
| **The output table is created for you** | If `outputTable` does not exist it is created in the workspace, and its ID comes back as `outputTableId`. If it does exist, `importType` decides whether its rows are replaced, appended to, or merged. |
| **The input table must carry the model's features** | Every feature column the analysis was trained on must exist in `inputTableId`, or the call fails with `21000001`. The input table does **not** need the target column. |
| **`matchingColumns` must be a subset of `outputColumns`** | A matching column that is not also written to the output table fails with `21000042` — the merge key has to be present in the destination. |
| **Creating a deployment does not run it** | Nothing is scored until either the schedule fires or [Run AutoML Analysis](#9-run-automl-analysis) is called. With `calendarFrequency: "none"` the deployment only ever runs on demand. |
| **Weekly and monthly schedules are currently unusable** | See the caveat under [`scheduleDetails` Fields](#scheduledetails-fields). |
| **No `criteria`** | The whole input table is scored. To score a subset, point `inputTableId` at a filtered query table or view. |
| **Not callable from a portal domain** | See [White Label / Client Portal Behaviour](#white-label--client-portal-behaviour). |
| **Dependency chain** | [Get AutoML Analysis Details](#3-get-automl-analysis-details) → `modelId` (with `trainingStatus: "Completed"`, `isDeployed: false`) + [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → `inputTableId` → Create Deployment → `deploymentId` → [Run AutoML Analysis](#9-run-automl-analysis). |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7103 | `META_OBJECT_NOT_PRESENT` — Workspace not found. | Verify `<workspace-id>` and the `ZANALYTICS-ORGID` header. |
| 7301 | `SECURITY_NOT_PERMITTED` — Portal-domain request, or the caller does not own this workspace. | Call from the standard API host as an owner of the workspace. |
| 7319 | `OBJID_NOT_BELONGS_TO_DB` — The input table belongs to a different workspace. | Use a table from `<workspace-id>`. |
| 8050 | `INVALID_VALUE` — `timezone` is not a recognised timezone name. | Use a standard timezone identifier such as `Asia/Kolkata`. |
| 8079 | `ATTRIBUTE_NOT_PRESENT_IN_JSON_CONFIGURATION` — A required attribute is missing; for weekly/monthly schedules this reports `'day'`. | The message names the attribute. See the schedule caveat above. |
| 8119 | `INVALID_VALUE_FOR_ATTRIBUTE` — `serverOption`, `hour`, `minute`, or `interval` is outside its permitted set. | The message names the attribute and the allowed values. |
| 8504 | `LESS_THAN_MIN_OCCURANCE` — CONFIG is absent or a mandatory key is missing at the template level. | Send a complete CONFIG object. |
| 8544 | `OUT_OF_RANGE` — A schedule value is outside its declared range. | Correct the value. |
| 21000001 | `FEATURES_NOTAVAILABLEINTABLE_ERROR` — The input table lacks one or more of the model's feature columns. | Use an input table with the same feature columns as the training table. |
| 21000009 | `ANALYSIS_NOT_BELONGS_TO_DB` — The analysis is not in this workspace. | Verify `<analysis-id>`. |
| 21000010 | `MODEL_NOT_BELONGS_TO_ANALYSIS` — The model is not part of this analysis. | Verify `<model-id>`. |
| 21000014 | `AUTOML_NOT_ENABLED` / `AUTOML_PRICING_EXCEED` — AutoML is disabled or over limit. | See [Feature Enablement and Plan Limits](#feature-enablement-and-plan-limits). |
| 21000022 | `INVALID_IMPORTTYPE` — `importType` is not `APPEND`, `TRUNCATEADD`, or `UPDATEADD`. | Use one of the three supported values. |
| 21000036 | `DEPLOY_PREDCOL_EMPTY_ERROR` — `predictionColumn` is empty. | Supply a column name. |
| 21000037 | `DEPLOY_OPTABLE_EMPTY_ERROR` — `outputTable` is empty. | Supply a table name. |
| 21000038 | `DEPLOY_MATCHINGCOL_EMPTY_ERROR` — `importType` is `UPDATEADD` but `matchingColumns` is empty. | Supply at least one matching column. |
| 21000039 | `DEPLOY_OPTABLE_MAXLENGTH_ERROR` — `outputTable` exceeds 100 characters. | Shorten the name. |
| 21000040 | `DEPLOY_PREDCOL_MAXLENGTH_ERROR` — `predictionColumn` exceeds 100 characters. | Shorten the name. |
| 21000041 | `DEPLOY_OPCOLS_EMPTY_ERROR` — `outputColumns` is empty. | Supply at least one column. |
| 21000042 | `DEPLOY_MATCHINGCOL_MISSINGIN_OPCOLS_ERROR` — A matching column is not present in `outputColumns`. | Add it to `outputColumns`. |
| 21000051 | `MODEL_ALREADY_DEPLOYED` — The model already has a deployment. | Delete the existing deployment first, or deploy a different model. |
| 21000052 | `MODEL_INPROGRESS_FOR_DEPLOYMENT` — The model is still training. | Wait until `trainingStatus` is `"Completed"`. |
| 21000053 | `MODEL_FAILED_FOR_DEPLOYMENT` — The model's training failed. | Deploy a different model, or recreate the analysis. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.modeling.create`. |

---

## 9. Run AutoML Analysis

Triggers a deployment immediately — the "run now" action. Scores the input table with the deployed model and writes the results to the output table according to the deployment's `importType`.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/automl/workspaces/<workspace-id>/analysis/<analysis-id>/deployments/<deployment-id>/execute` |
| **OAuth Scope** | `ZohoAnalytics.modeling.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or the Workspace Admin (owner) of the specified workspace. |

> This API has no CONFIG parameter. Note that the path segment is `/deployments/<deployment-id>/execute` — the **model ID does not appear**, unlike the deployment-creation path.

### Sample Requests

**Case 1 — Run an on-demand deployment**

```http
POST /restapi/v2/automl/workspaces/137687000271334001/analysis/137687000000061115/deployments/137687000000198176/execute HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — Force an extra run of a scheduled deployment**

```http
POST /restapi/v2/automl/workspaces/137687000271334001/analysis/137687000000061115/deployments/137687000000198180/execute HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 3 — White Label / Client Portal: request sent through the portal domain (rejected)**

```http
POST /restapi/v2/automl/workspaces/137687000271334009/analysis/137687000000061119/deployments/137687000000198190/execute HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status. The 204 confirms the run was *accepted and started*, not that scoring has finished.

```
HTTP/1.1 204 No Content
```

**HTTP 400 Bad Request — The deployment does not belong to the analysis in the URL**

```json
{
    "status": "failure",
    "summary": "DEPLOYMENT_NOT_BELONGS_TO_ANALYSIS",
    "data": {
        "errorCode": 21000012,
        "errorMessage": "The given deployment does not belong to this analysis."
    }
}
```

**HTTP 403 Forbidden — Caller has no AutoML access in this workspace**

```json
{
    "status": "failure",
    "summary": "SECURITY_NOT_PERMITTED",
    "data": {
        "errorCode": 7301,
        "errorMessage": "You (SharedUser) do not have the permission to do this operation. "
    }
}
```

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload. There is no job ID, row count, or progress handle in the response.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Run AutoML Analysis returns a bare HTTP `204 No Content` — no `status`/`summary` JSON, no job handle, and no row count. |
| **Asynchronous — 204 means "started"** | Scoring proceeds in the background. Poll `deployments.status` via [Get Deployments For A Model](#4-get-deployments-for-a-model) to see when it reaches `"Completed"`. |
| **The path omits the model ID** | Unlike [Create AutoML Analysis Deployment](#8-create-automl-analysis-deployment), this URL is `/analysis/<analysis-id>/deployments/<deployment-id>/execute`. The deployment is addressed under the analysis, not under the model. |
| **It writes real data** | The output table is modified according to the deployment's `importType` — `TRUNCATEADD` will delete its existing rows. There is no dry-run mode. |
| **Works with or without a schedule** | A deployment created with `calendarFrequency: "none"` runs only through this API; a scheduled deployment can additionally be forced to run at any time. |
| **Does not shift the recurring schedule** | A manual run is a one-off; the next scheduled occurrence is unaffected. |
| **Read results from the output table** | The predictions are ordinary rows — fetch them with the [Row / Export APIs](ROW_API_DOC_INFO.md) using `outputTableId`. |
| **Not callable from a portal domain** | See [White Label / Client Portal Behaviour](#white-label--client-portal-behaviour). |
| **Dependency chain** | [Create AutoML Analysis Deployment](#8-create-automl-analysis-deployment) or [Get Deployments For A Model](#4-get-deployments-for-a-model) → `deploymentId` → Run AutoML Analysis → poll [Get Deployments For A Model](#4-get-deployments-for-a-model) → read `outputTableId` with the data APIs. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7103 | `META_OBJECT_NOT_PRESENT` — Workspace not found. | Verify `<workspace-id>` and the `ZANALYTICS-ORGID` header. |
| 7301 | `SECURITY_NOT_PERMITTED` — Portal-domain request, or the caller does not own this workspace. | Call from the standard API host as an owner of the workspace. |
| 21000006 | `DEPLOYMENT_FAILURE` — The scoring job could not be started or failed during execution. | Check that the input table still has the model's feature columns, then retry. |
| 21000009 | `ANALYSIS_NOT_BELONGS_TO_DB` — The analysis is not in this workspace. | Verify `<analysis-id>`. |
| 21000012 | `DEPLOYMENT_NOT_BELONGS_TO_ANALYSIS` — The deployment is not part of this analysis, or does not exist. | Verify `<deployment-id>` via [Get Deployments For A Model](#4-get-deployments-for-a-model). |
| 21000014 | `AUTOML_NOT_ENABLED` / `AUTOML_PRICING_EXCEED` — AutoML is disabled or over limit. | See [Feature Enablement and Plan Limits](#feature-enablement-and-plan-limits). |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.modeling.create`. |

---

## 10. Delete AutoML Analysis Model Deployment

Deletes a deployment. The model becomes deployable again; the analysis, the model, and the output table are unaffected.

| Attribute | Value |
|-----------|-------|
| **Method** | DELETE |
| **URL** | `/restapi/v2/automl/workspaces/<workspace-id>/analysis/<analysis-id>/deployments/<deployment-id>` |
| **OAuth Scope** | `ZohoAnalytics.modeling.delete` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or the Workspace Admin (owner) of the specified workspace. |

> This API has no CONFIG parameter. As with [Run AutoML Analysis](#9-run-automl-analysis), the path addresses the deployment under the **analysis**, not under the model.

### Sample Requests

**Case 1 — Remove a deployment so the model can be redeployed with a different configuration**

```http
DELETE /restapi/v2/automl/workspaces/137687000271334001/analysis/137687000000061115/deployments/137687000000198176 HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
```

**Case 2 — White Label / Client Portal: request sent through the portal domain (rejected)**

```http
DELETE /restapi/v2/automl/workspaces/137687000271334009/analysis/137687000000061119/deployments/137687000000198190 HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
```

### Sample Responses

**HTTP 204 No Content**

This API returns **no response body** on success — only an HTTP `204 No Content` status.

```
HTTP/1.1 204 No Content
```

**HTTP 400 Bad Request — The deployment does not belong to the analysis in the URL**

```json
{
    "status": "failure",
    "summary": "DEPLOYMENT_NOT_BELONGS_TO_ANALYSIS",
    "data": {
        "errorCode": 21000012,
        "errorMessage": "The given deployment does not belong to this analysis."
    }
}
```

### Response Fields

Not applicable — this API never returns a JSON body on success (HTTP 204 No Content). Only failure responses contain a JSON error payload.

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Success response has no body** | Delete Deployment returns a bare HTTP `204 No Content`. |
| **The de-facto "edit deployment" step** | Deployments are immutable, so changing the input table, output table, schedule, or `importType` means deleting the deployment and creating a new one. This API is the first half of that operation. |
| **Frees the model for redeployment** | After deletion `isDeployed` returns to `false` in [Get AutoML Analysis Details](#3-get-automl-analysis-details), and [Create AutoML Analysis Deployment](#8-create-automl-analysis-deployment) will succeed again. |
| **The output table and its rows survive** | Predictions already written remain. A new deployment writing to the same `outputTable` will append to, replace, or merge with them depending on its `importType`. |
| **Cancels future scheduled runs** | Any recurring schedule attached to the deployment stops; a run already in progress is not rolled back. |
| **Not idempotent** | A repeat delete fails with `21000012`. |
| **Not callable from a portal domain** | See [White Label / Client Portal Behaviour](#white-label--client-portal-behaviour). |
| **Dependency chain** | [Get Deployments For A Model](#4-get-deployments-for-a-model) → `deploymentId` → Delete Deployment → (optionally) [Create AutoML Analysis Deployment](#8-create-automl-analysis-deployment) with the new configuration. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7103 | `META_OBJECT_NOT_PRESENT` — Workspace not found. | Verify `<workspace-id>` and the `ZANALYTICS-ORGID` header. |
| 7301 | `SECURITY_NOT_PERMITTED` — Portal-domain request, or the caller does not own this workspace. | Call from the standard API host as an owner of the workspace. |
| 21000009 | `ANALYSIS_NOT_BELONGS_TO_DB` — The analysis is not in this workspace. | Verify `<analysis-id>`. |
| 21000012 | `DEPLOYMENT_NOT_BELONGS_TO_ANALYSIS` — The deployment is not part of this analysis, or was already deleted. | Verify `<deployment-id>` via [Get Deployments For A Model](#4-get-deployments-for-a-model). |
| 21000014 | `AUTOML_NOT_ENABLED` / `AUTOML_PRICING_EXCEED` — AutoML is disabled or over limit. | See [Feature Enablement and Plan Limits](#feature-enablement-and-plan-limits). |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.modeling.delete`. |

---

## 11. AutoML What If Analysis

Generates a **single prediction for a hypothetical set of feature values** — a live "what if I changed these inputs?" query against a trained model. Nothing is stored and no table is written.

| Attribute | Value |
|-----------|-------|
| **Method** | POST |
| **URL** | `/restapi/v2/automl/workspaces/<workspace-id>/analysis/<analysis-id>/models/<model-id>/whatif` |
| **OAuth Scope** | `ZohoAnalytics.modeling.create` |
| **ZANALYTICS-ORGID Header** | **Mandatory** — Organisation ID of the workspace. |
| **Permission Required** | The authenticated user must be an Account Admin or Organization Admin, or the Workspace Admin (owner) of the specified workspace. |

### CONFIG Parameters

CONFIG is **mandatory** for this API.

| Parameter | Type | Mandatory | Default | Description |
|-----------|------|-----------|---------|-------------|
| `features` | JSONObject | **Yes** | — | Feature name → hypothetical value. **Every feature the model was trained on must be present** (`21000050` otherwise); omitting even one is rejected. Keys must be feature column names from the training table; values must match each column's data type. An empty object is rejected with `8078`, and a missing `features` key with `8079`. |

> `features` is a free-form object — the valid keys are exactly the entries of `analysis.features` from [Get AutoML Analysis Details](#3-get-automl-analysis-details). Read that list first rather than guessing.

### Sample Requests

**Case 1 — Predict a price for a hypothetical property**

```http
POST /restapi/v2/automl/workspaces/137687000271334001/analysis/137687000000061115/models/137687000000198124/whatif HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "features": {
        "City": "Bengaluru",
        "Bedrooms": "3",
        "Bathrooms": "2",
        "Garage": "1"
    }
}
```

**Case 2 — Same model, one input changed, to compare outcomes**

```http
POST /restapi/v2/automl/workspaces/137687000271334001/analysis/137687000000061115/models/137687000000198124/whatif HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "features": {
        "City": "Bengaluru",
        "Bedrooms": "5",
        "Bathrooms": "4",
        "Garage": "2"
    }
}
```

**Case 3 — White Label / Client Portal: request sent through the portal domain (rejected)**

```http
POST /restapi/v2/automl/workspaces/137687000271334009/analysis/137687000000061119/models/137687000000198140/whatif HTTP/1.1
Host: portal.customdomain.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000654321
Content-Type: application/x-www-form-urlencoded

CONFIG={
    "features": {
        "Region": "East"
    }
}
```

### Sample Responses

**HTTP 200 OK — Prediction generated (Case 1)**

```json
{
    "status": "success",
    "summary": "AutoML what if analysis",
    "data": {
        "predictions": "7250000",
        "targetColumn": "Price"
    }
}
```

**HTTP 400 Bad Request — A feature used in training is missing from the input**

```json
{
    "status": "failure",
    "summary": "FEATURE_MISSING_IN_WHATIF",
    "data": {
        "errorCode": 21000050,
        "errorMessage": "One or more features used in training the model is missing in the input.Please ensure that all features used in training are included."
    }
}
```

**HTTP 400 Bad Request — The model is still training**

```json
{
    "status": "failure",
    "summary": "MODEL_TRAINING_INPROGRESS",
    "data": {
        "errorCode": 21000043,
        "errorMessage": "Training in progress for the model.Please try again once training is completed."
    }
}
```

**HTTP 400 Bad Request — `features` sent as an empty object**

```json
{
    "status": "failure",
    "summary": "EMPTY_JSON_ATTRIBUTE_FOUND",
    "data": {
        "errorCode": 8078,
        "errorMessage": "The attribute 'features' has an empty value. Kindly provide a valid JSON configuration."
    }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|--------------|
| `status` | String | `"success"` on a successful call, `"failure"` on error. |
| `summary` | String | Localised operation summary. `"AutoML what if analysis"` for this API. |
| `data` | JSONObject | Response payload wrapper. |
| `data.predictions` | String | The value the model predicts for the supplied feature values, **returned as a string** even for a numeric regression target. For a classification model this is the predicted class label. |
| `data.targetColumn` | String | Name of the column being predicted — the analysis's `targetColumn`, echoed for convenience. |

### Notes & Behaviour

| Aspect | Detail |
|--------|--------|
| **Read-only despite being a POST** | Nothing is persisted: no table is written, no deployment is needed, and the model is unchanged. It uses POST only because the feature values travel in a body. |
| **No deployment required** | This is the one way to get a prediction out of a model without creating a deployment — useful for interactive exploration and for validating a model before committing to deploy it. |
| **All training features are mandatory** | Partial input is rejected with `21000050`; the model cannot infer missing values. Read `analysis.features` from [Get AutoML Analysis Details](#3-get-automl-analysis-details) and supply every one. |
| **Extra keys are tolerated** | Feature names that were not part of training are ignored rather than rejected, so a superset of the training features is accepted. |
| **The model must be trained** | Calling it while `trainingStatus` is `"In Progress"` fails with `21000043`. |
| **Not every algorithm supports What-If** | Algorithms without What-If capability fail with `21000054`, naming the algorithm. Clustering models in particular are not universally supported. |
| **Values are sent and returned as strings** | Send numeric features as JSON strings, and expect `predictions` back as a string; convert on your side. |
| **Wrongly typed values surface as `21000006`** | A value that cannot be coerced to the column's data type fails as a deployment/scoring failure rather than a specific type error. |
| **Not callable from a portal domain** | See [White Label / Client Portal Behaviour](#white-label--client-portal-behaviour). |
| **Dependency chain** | [Get AutoML Analysis Details](#3-get-automl-analysis-details) → `models[].id` (with `trainingStatus: "Completed"`) + `analysis.features` → What If Analysis. |

### Error Codes

| Code | Reason | Solution |
|------|--------|----------|
| 7103 | `META_OBJECT_NOT_PRESENT` — Workspace not found. | Verify `<workspace-id>` and the `ZANALYTICS-ORGID` header. |
| 7301 | `SECURITY_NOT_PERMITTED` — Portal-domain request, or the caller does not own this workspace. | Call from the standard API host as an owner of the workspace. |
| 8078 | `EMPTY_JSON_ATTRIBUTE_FOUND` — `features` was sent as an empty object. | Supply every training feature and its value. |
| 8079 | `ATTRIBUTE_NOT_PRESENT_IN_JSON_CONFIGURATION` — `features` is missing from CONFIG. | Include the `features` object. |
| 8504 | `LESS_THAN_MIN_OCCURANCE` — CONFIG is absent. | Send a CONFIG object containing `features`. |
| 21000006 | `DEPLOYMENT_FAILURE` — Scoring failed, typically because a feature value does not match its column's data type. | Send values matching each feature column's type. |
| 21000009 | `ANALYSIS_NOT_BELONGS_TO_DB` — The analysis is not in this workspace. | Verify `<analysis-id>`. |
| 21000010 | `MODEL_NOT_BELONGS_TO_ANALYSIS` — The model is not part of this analysis. | Verify `<model-id>` via [Get AutoML Analysis Details](#3-get-automl-analysis-details). |
| 21000014 | `AUTOML_NOT_ENABLED` / `AUTOML_PRICING_EXCEED` — AutoML is disabled or over limit. | See [Feature Enablement and Plan Limits](#feature-enablement-and-plan-limits). |
| 21000043 | `MODEL_TRAINING_INPROGRESS` — The model is still training. | Wait until `trainingStatus` reads `"Completed"`. |
| 21000050 | `FEATURE_MISSING_IN_WHATIF` — One or more training features are absent from `features`. | Supply every feature listed in `analysis.features`. |
| 21000054 | `WHATIF_NOT_SUPPORTED` — The model's algorithm does not support What-If analysis. | Use a model trained with a supporting algorithm. |
| 8535 | `INVALID_OAUTHTOKEN` — Invalid or expired OAuth token. | Provide a valid token with scope `ZohoAnalytics.modeling.create`. |

---

## Appendix A – Common HTTP Headers

| Header | Value | Required | Description |
|--------|-------|----------|-------------|
| `Authorization` | `Zoho-oauthtoken <oauth-token>` | **Mandatory** | OAuth 2.0 access token of the calling user. Must carry the scope matching the operation (see [Appendix B](#appendix-b--oauth-scope-summary)). |
| `ZANALYTICS-ORGID` | Organization ID string | **Mandatory** | Organization ID. For the ten workspace-scoped APIs it must be the organization that owns `<workspace-id>`; for [Get AutoML Analysis In Org](#1-get-automl-analysis-in-org) it selects the organization whose analyses are listed. |
| `Content-Type` | `application/x-www-form-urlencoded` | Conditional | Required only for the three APIs that send a CONFIG body: [Create AutoML Analysis](#5-create-automl-analysis), [Create AutoML Analysis Deployment](#8-create-automl-analysis-deployment), and [AutoML What If Analysis](#11-automl-what-if-analysis). The other eight send no payload. |
| `Host` | `analyticsapi.zoho.com` (or the DC equivalent) | **Mandatory** | Must be the **standard** Zoho Analytics API host. A request whose host is a Client Portal / White Label custom domain is rejected with `7301` for all eleven APIs — see [White Label / Client Portal Behaviour](#white-label--client-portal-behaviour). |

> **`ZANALYTICS-DEST-ORGID` is not used by any API in this document.** That header applies only to cross-organization copy operations (Copy Workspace, [Copy Views](VIEW_OPERATIONS_API_DOC_INFO.md#2-copy-views), Copy Formulas), which target a destination organization. The AutoML APIs have no cross-org or portal-domain targeting mechanism.

Example:

```http
POST /restapi/v2/automl/workspaces/137687000271334001/analysis HTTP/1.1
Host: analyticsapi.zoho.com
Authorization: Zoho-oauthtoken 1000.xxxxxx.yyyyyy
ZANALYTICS-ORGID: 700000123456
Content-Type: application/x-www-form-urlencoded

CONFIG={"name":"PricePredictionAnalysis","trainingTableId":137687000000061002,"predictionType":"REGRESSION","targetColumn":"Price","features":["City","Bedrooms","Bathrooms"],"serverOption":1,"algorithms":{"randomForestRegression":{}}}
```

---

## Appendix B – OAuth Scope Summary

| API | HTTP Method | Scope |
|-----|-------------|-------|
| Get AutoML Analysis In Org | GET | `ZohoAnalytics.metadata.read` |
| Get AutoML Analysis In Workspace | GET | `ZohoAnalytics.metadata.read` |
| Get AutoML Analysis Details | GET | `ZohoAnalytics.metadata.read` |
| Get Deployments For A Model | GET | `ZohoAnalytics.metadata.read` |
| Create AutoML Analysis | POST | `ZohoAnalytics.modeling.create` |
| Delete AutoML Analysis | DELETE | `ZohoAnalytics.modeling.delete` |
| Delete AutoML Analysis Model | DELETE | `ZohoAnalytics.modeling.delete` |
| Create AutoML Analysis Deployment | POST | `ZohoAnalytics.modeling.create` |
| Run AutoML Analysis | POST | `ZohoAnalytics.modeling.create` |
| Delete AutoML Analysis Model Deployment | DELETE | `ZohoAnalytics.modeling.delete` |
| AutoML What If Analysis | POST | `ZohoAnalytics.modeling.create` |

> This family **spans two scope groups**: the four read APIs use `metadata.read`, and the seven write APIs use `modeling.*`. Any real workflow needs both, because `modeling.*` alone cannot discover the `analysisId`, `modelId`, or `deploymentId` that every write API requires. Note also that **What If Analysis needs `modeling.create`** even though it only reads a prediction — a token holding `metadata.read` alone cannot run it.

---

## Appendix C – API-Specific Notes and Behaviours

### Get AutoML Analysis In Org

- **The only organization-wide AutoML API, and the only one that names the workspace.** `workspaceId` and `workspaceName` appear nowhere else, which makes this the entry point when you do not already know which workspace holds an analysis.
- **A stricter role gate than everything else in the family.** Account Admin or Organization Admin only — a Workspace Admin who can fully manage AutoML inside their own workspace still receives `7301` here. Do not treat a `7301` from this API as evidence that the user has no AutoML access at all; retry with [Get AutoML Analysis In Workspace](#2-get-automl-analysis-in-workspace) against a specific workspace.
- **Inventory only.** No models, no deployments, no feature lists. Every deeper field requires [Get AutoML Analysis Details](#3-get-automl-analysis-details), one analysis at a time.
- **`isDraft` distinguishes UI-created stubs.** Analyses created through the API always begin training immediately and are never drafts; a `true` here means somebody saved an analysis in the Zoho Analytics UI without training it.
- **Dependency chain:** Get AutoML Analysis In Org → `workspaceId` + `id` → [Get AutoML Analysis Details](#3-get-automl-analysis-details).

### Get AutoML Analysis In Workspace

- **The workspace-scoped twin of [Get AutoML Analysis In Org](#1-get-automl-analysis-in-org)**, returning an identical per-analysis object minus `workspaceId` and `workspaceName`. Prefer it whenever the workspace is already known — it is available to Workspace Admins, who cannot call the org-level API at all.
- **Still not a source of `modelId`.** This is the most common misstep in the family: neither list API exposes models, so a deploy or What-If workflow must always pass through [Get AutoML Analysis Details](#3-get-automl-analysis-details).
- **Unfiltered and unpaged**, like every listing API here. Filter client-side.
- **Case asymmetry on `predictionType`.** Title case on read, upper case on write — never round-trip the value without normalising.
- **Dependency chain:** [Get Workspace List](WORKSPACE_OPERATIONS_API_DOC_INFO.md) → Get AutoML Analysis In Workspace → `id` → [Get AutoML Analysis Details](#3-get-automl-analysis-details).

### Get AutoML Analysis Details

- **The hub of the whole family.** It is the sole source of `modelId`, the sole way to see per-model scores and hyperparameters, and the polling endpoint that tells you when training has finished. Four of the eleven APIs are unreachable without calling it first.
- **Poll `models[].trainingStatus`, not `analysis.status`.** Models train independently, so one model can be `"Completed"` and ready to deploy while a sibling is still `"In Progress"` or has `"Failed"`. Deploying or running What-If against a model that is not `"Completed"` fails with `21000052` or `21000043`.
- **Two `status` fields with different meanings.** `data.analysis.status` is the training state; the top-level `status` is the HTTP outcome. Reading the wrong one produces confidently wrong logic.
- **`isDeployed` is the cheap pre-check for deployment.** Consult it rather than discovering `21000051` the hard way.
- **Everything numeric returns as a string.** `score` and every hyperparameter value are strings, even though `algorithms` accepts them as numbers on the request side — a create/read round-trip needs explicit conversion.
- **Dependency chain:** [Create AutoML Analysis](#5-create-automl-analysis) → `analysisId` → Get AutoML Analysis Details → `models[].id` → [Get Deployments For A Model](#4-get-deployments-for-a-model), [Delete AutoML Analysis Model](#7-delete-automl-analysis-model), [Create AutoML Analysis Deployment](#8-create-automl-analysis-deployment), [AutoML What If Analysis](#11-automl-what-if-analysis).

### Get Deployments For A Model

- **A JSONObject behind a plural key.** `data.deployments` is a single object because a model may hold only one deployment. Code that iterates it will break.
- **The only way to observe a run.** [Run AutoML Analysis](#9-run-automl-analysis) returns 204 with no job handle, so `deployments.status` here is the sole progress signal for a scoring job.
- **`outputTableId` is the bridge to the data APIs.** Predictions are ordinary table rows; this ID is what you feed to the [Row / Export APIs](ROW_API_DOC_INFO.md) to actually consume them.
- **The schedule is write-only.** `scheduleDetails` and `matchingColumns` are never echoed by any API, so an integration that wants to reproduce or clone a deployment must retain its own copy of what it sent.
- **Case asymmetry on `importType`.** Lower case on read, upper case on write.
- **Dependency chain:** [Get AutoML Analysis Details](#3-get-automl-analysis-details) → `modelId` → Get Deployments For A Model → `deploymentId` → [Run AutoML Analysis](#9-run-automl-analysis) / [Delete AutoML Analysis Model Deployment](#10-delete-automl-analysis-model-deployment).

### Create AutoML Analysis

- **One request fans out into many models.** Each key in `algorithms` produces its own independently trained, scored, and deployable model. This is the intended way to compare algorithms — send several keys and then pick the best `score` from [Get AutoML Analysis Details](#3-get-automl-analysis-details).
- **Immutable once created.** There is no update API at any level of the hierarchy. Changing the training table, target column, feature list, algorithms, or server option means delete-and-recreate, which invalidates every downstream ID.
- **The published limits are looser than the enforced ones.** `name` is capped at 50 characters (not the documented 60), and `features` must contain 3–20 entries (not the documented 1–100). Both mismatches fail late, at `21000020` / `21000026` / `21000027`.
- **`maxEntropy` is a special case in two directions.** It must be the only algorithm in the request, and it inverts the feature rule by requiring exactly one feature where every other algorithm requires at least three.
- **`targetColumn` must not appear in `features`.** The server rejects it (`21000048`) precisely because it would leak the answer into the model.
- **Clustering takes no target column at all** — it is unsupervised, and the attribute is simply not read.
- **Dependency chain:** [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → `trainingTableId` → Create AutoML Analysis → `data.id` → [Get AutoML Analysis Details](#3-get-automl-analysis-details) to poll training.

### Delete AutoML Analysis

- **204 No Content, no body.** Verified against the implementation.
- **The widest blast radius in the family.** One call removes the analysis, every model under it, and every deployment under those models — including their schedules. There is no partial mode and no confirmation step.
- **Output tables and their data survive.** The prediction tables that deployments created remain in the workspace, orphaned. Clean them up separately with [Delete View](VIEW_OPERATIONS_API_DOC_INFO.md#5-delete-view) if they are no longer wanted.
- **No trash, no restore.** Recreating the analysis produces entirely new IDs at all three levels and retrains from scratch.
- **Frees AutoML capacity**, so a create previously blocked by `21000014` `AUTOML_PRICING_EXCEED` may succeed afterwards.
- **Dependency chain:** [Get AutoML Analysis In Workspace](#2-get-automl-analysis-in-workspace) → `analysisId` → Delete AutoML Analysis.

### Delete AutoML Analysis Model

- **204 No Content, no body.** Verified against the implementation.
- **The pruning tool for a multi-algorithm analysis.** After comparing scores in [Get AutoML Analysis Details](#3-get-automl-analysis-details), delete the models you do not want and keep the winner. The analysis and the surviving models are untouched.
- **It takes the model's deployment with it**, so a deployed model can be removed in one call rather than two.
- **Deleting every model leaves an empty analysis.** The analysis is not auto-removed; use [Delete AutoML Analysis](#6-delete-automl-analysis) for that.
- **Models cannot be regenerated.** There is no add-model or retrain API, so a deleted algorithm can only be recovered by creating a new analysis that includes it.
- **Dependency chain:** [Get AutoML Analysis Details](#3-get-automl-analysis-details) → `models[].id` → Delete AutoML Analysis Model.

### Create AutoML Analysis Deployment

- **The gate with the most preconditions in the family.** The model must exist, belong to the analysis, have finished training (`21000052`), not have failed (`21000053`), and not already be deployed (`21000051`) — and the input table must carry every feature the model was trained on (`21000001`). Check `trainingStatus` and `isDeployed` from [Get AutoML Analysis Details](#3-get-automl-analysis-details) before calling.
- **One deployment per model, and deployments are immutable.** Reconfiguring means [Delete AutoML Analysis Model Deployment](#10-delete-automl-analysis-model-deployment) followed by a fresh create — there is no update API.
- **It creates the output table as a side effect.** A brand-new table appears in the workspace if `outputTable` does not already exist, and its ID is returned as `outputTableId`. Against an existing table, `importType` decides whether rows are replaced (`TRUNCATEADD`), accumulated (`APPEND`), or merged (`UPDATEADD`).
- **`matchingColumns` must be a subset of `outputColumns`.** A merge key that is not written to the destination fails with `21000042`.
- **Creating is not running.** With `calendarFrequency: "none"` nothing happens until [Run AutoML Analysis](#9-run-automl-analysis) is called.
- **Weekly and monthly schedules do not currently work.** The server reads a `day` attribute that the published request template does not declare, while the declared `weekDay` / `monthDay` / `hourInterval` keys are never read. Use `none`, `daily`, or `hourly` and see the caveat under [`scheduleDetails` Fields](#scheduledetails-fields).
- **Dependency chain:** [Get AutoML Analysis Details](#3-get-automl-analysis-details) → `modelId` + [Get View List](VIEW_OPERATIONS_API_DOC_INFO.md#6-get-view-list) → `inputTableId` → Create Deployment → `deploymentId` + `outputTableId`.

### Run AutoML Analysis

- **204 No Content, no body.** Verified against the implementation.
- **The path drops the model ID.** It is `/analysis/<analysis-id>/deployments/<deployment-id>/execute`, not `/models/<model-id>/deployments/...`. Building the URL by analogy with [Create AutoML Analysis Deployment](#8-create-automl-analysis-deployment) produces a 404-class failure.
- **It writes real data with no dry-run.** A `TRUNCATEADD` deployment deletes the output table's existing rows on every run. There is no preview mode and no undo.
- **Asynchronous with no handle.** The 204 means the job started; `deployments.status` from [Get Deployments For A Model](#4-get-deployments-for-a-model) is the only way to learn whether it finished or failed.
- **Independent of the schedule.** It works on unscheduled deployments, forces an extra run on scheduled ones, and never shifts the next scheduled occurrence.
- **Dependency chain:** [Create AutoML Analysis Deployment](#8-create-automl-analysis-deployment) → `deploymentId` → Run AutoML Analysis → poll [Get Deployments For A Model](#4-get-deployments-for-a-model) → read predictions from `outputTableId`.

### Delete AutoML Analysis Model Deployment

- **204 No Content, no body.** Verified against the implementation.
- **It is the first half of "edit a deployment".** Because deployments are immutable, every change of input table, output table, schedule, or `importType` is expressed as delete-then-create. Expect to call it routinely, not exceptionally.
- **It releases the model.** `isDeployed` flips back to `false` and [Create AutoML Analysis Deployment](#8-create-automl-analysis-deployment) succeeds again — this is the only way to clear `21000051`.
- **Data already written stays.** The output table and its prediction rows survive, so a replacement deployment pointed at the same table will interact with the old rows according to its own `importType`.
- **Addressed under the analysis, not the model** — same path shape as [Run AutoML Analysis](#9-run-automl-analysis).
- **Dependency chain:** [Get Deployments For A Model](#4-get-deployments-for-a-model) → `deploymentId` → Delete Deployment → (optionally) [Create AutoML Analysis Deployment](#8-create-automl-analysis-deployment).

### AutoML What If Analysis

- **A read disguised as a POST.** It persists nothing, needs no deployment, and leaves the model unchanged — the POST verb exists only to carry the feature values. It is the fastest way to sanity-check a model before committing to a deployment.
- **All-or-nothing input.** Every feature used in training must be present; a partial `features` object fails with `21000050` rather than substituting defaults. Extra keys beyond the training set are ignored, so a superset is safe.
- **The feature list must be fetched, not guessed.** `analysis.features` from [Get AutoML Analysis Details](#3-get-automl-analysis-details) is the authoritative key set.
- **Not universally supported.** Some algorithms have no What-If capability and fail with `21000054`; the model must also have finished training (`21000043`).
- **Strings in, string out.** Numeric features are sent as JSON strings and `predictions` returns as a string, so both directions need conversion. A value that cannot be coerced to its column's type surfaces as `21000006` rather than a specific type error.
- **Requires a write scope for a read operation.** `modeling.create` is needed even though nothing is created — worth knowing when scoping a read-only integration token.
- **Dependency chain:** [Get AutoML Analysis Details](#3-get-automl-analysis-details) → `models[].id` + `analysis.features` → What If Analysis.

---

## Appendix D – General Response Payload Notes

| Field / Behaviour | Detail |
|-------------------|--------|
| **Four of eleven APIs return 204 with no body** | [Delete AutoML Analysis](#6-delete-automl-analysis), [Delete AutoML Analysis Model](#7-delete-automl-analysis-model), [Run AutoML Analysis](#9-run-automl-analysis), and [Delete AutoML Analysis Model Deployment](#10-delete-automl-analysis-model-deployment) return HTTP **204 No Content** — treat the 2xx status code as the success indicator and never expect or parse a JSON body. The other seven return the standard `{"status", "summary", "data"}` envelope with HTTP 200. |
| **Failure responses always carry a body** | Even for the 204 APIs, errors return `{"status": "failure", "summary": "<ERROR_NAME>", "data": {"errorCode": <n>, "errorMessage": "<text>"}}`. `summary` on failure is the error's symbolic name (e.g. `ANALYSIS_NOT_BELONGS_TO_DB`, `MODEL_ALREADY_DEPLOYED`), not a localised sentence. |
| **AutoML errors occupy the 21000xxx range** | Domain-specific failures use eight-digit codes starting `21000`, clearly separated from the 7xxx/8xxx codes shared with the rest of the API suite. Two distinct conditions share `21000014` and are told apart only by `summary` — see [Feature Enablement and Plan Limits](#feature-enablement-and-plan-limits). |
| **All IDs are strings** | `id`, `trainingTableId`, `models[].id`, `deploymentId`, `outputTableId`, `inputTableId`, and `analysisId` are JSON **strings** in every response, even though the request side accepts `trainingTableId` and `inputTableId` as native numbers. Parse them as strings or longs to avoid precision loss. |
| **Numbers are returned as strings too** | `models[].score` and every hyperparameter value inside `models[].algorithm` come back as strings, despite being sent as numbers. Convert explicitly when round-tripping. |
| **Beware the three nested `status` fields** | The top-level `status` is the HTTP outcome; `data.analysis.status` is the training state of an analysis; `data.deployments.status` is the outcome of the last scoring run. They are unrelated and use different vocabularies. |
| **Case asymmetry between request and response** | `predictionType` is sent upper case (`REGRESSION`) and returned title case (`"Regression"`); `importType` is sent upper case (`TRUNCATEADD`) and returned lower case (`"truncateadd"`). Normalise before comparing. |
| **Plural keys holding single objects** | `data.deployments` is a JSONObject in both [Create AutoML Analysis Deployment](#8-create-automl-analysis-deployment) and [Get Deployments For A Model](#4-get-deployments-for-a-model), because a model may hold at most one deployment. Only `data.analysis` in the two list APIs is genuinely an array — and in [Get AutoML Analysis Details](#3-get-automl-analysis-details) the same key is an object. |
| **Empty array, never a missing key** | `data.analysis` is always present in both list APIs, empty (`[]`) when there is nothing to report. |
| **Create responses return IDs only** | [Create AutoML Analysis](#5-create-automl-analysis) returns just `data.id`, and [Create AutoML Analysis Deployment](#8-create-automl-analysis-deployment) just `deploymentId` and `outputTableId`. Neither echoes the configuration that was sent — confirm it with the corresponding read API. |
| **Write-only configuration** | `algorithms` hyperparameters are readable back through `models[].algorithm`, but a deployment's `scheduleDetails`, `matchingColumns`, and `timezone` are never returned by any API. Retain your own copy if you need to clone or reproduce a deployment. |
