# zenesis-oas - OpenAPI specifications

One OpenAPI 3.1 document per domain, carrying the `x-zenesis-*` vendor extensions the Zenesis
documentation renderer needs. These are valid OpenAPI: vendor extensions are legal anywhere and any
conformant tool ignores `x-` keys. They are hand-edited; nothing generates them.

| File | Groups | Operations |
|---|---|---|
| `org-management-grouped-api.json` | 1 | 4 |
| `user-groups-grouped-api.json` | 4 | 26 |
| `workspace-management-grouped-api.json` | 4 | 24 |
| `data-modeling-schema-grouped-api.json` | 7 | 33 |
| `data-operations-grouped-api.json` | 6 | 20 |
| `views-management-grouped-api.json` | 5 | 27 |
| `reports-dashboards-grouped-api.json` | 2 | 9 |
| `share-publish-grouped-api.json` | 4 | 20 |
| `schedules-alerts-grouped-api.json` | 1 | 6 |
| `dsml-grouped-api.json` | 1 | 11 |
| | **35** | **180** |

## Naming

`<domain-slug>-grouped-api.json`. The slug is the stable identifier of a domain: the samples file is
`<domain-slug>-grouped-api-samples.json`, and both the converter and the OKF builder key off it. It is
deliberately not the markdown folder name - `schedules-alerts` against `09 · Schedules & Alerts` - and
the two are paired in the `DOMAINS` table in
[`../tools/validate_api_docs.py`](../tools/validate_api_docs.py).

## Structure of a document

```jsonc
{
  "openapi": "3.1.0",
  "info":    { "title": "Zoho Analytics API", "version": "v2", "description": "…" },
  "servers": [ … ],
  "tags":    [ { "name": "Email Schedules" } ],      // one per API group
  "paths":   { "/restapi/v2/workspaces/{workspace-id}/emailschedules": { … } },
  "components": { … }
}
```

Every operation must carry a `tag` that the document declares, and a title in `x-zenesis-title` (or
`summary`). Security schemes and the OAuth scopes they grant come from
[`../zoho-analytics-api-common.json`](../zoho-analytics-api-common.json), not from these files.

## Error responses

Every operation models its responses the same way, and the validator enforces it:

```jsonc
"responses": {
  "200": {                                   // exactly one of 200 / 201 / 204
    "description": "…",
    "x-zenesis-statuscodes": [ … ],          // the error-code table rides on the success response
    "content": { … }
  },
  "4XX": { "$ref": "…/zoho-analytics-api-common.json#/components/responses/CommonErrorResponse" },
  "500": { "$ref": "…/zoho-analytics-api-common.json#/components/responses/UnexpectedErrorResponse" }
}
```

`4XX` covers every client error (400, 401, 403, 404 - the exact status is chosen per error code at
runtime) and `500` the server error; both reference the shared responses so the envelope and examples
are defined once. A `default` response is not used. The error-code table sits on the success response
rather than on `4XX` because that is where the converter folds it from and where the OKF builder
reads it.

## Vendor extensions

Ten keys are in use. Each one has a matching rule in `rules.json` in
[zenesis-oas-convertor](https://github.com/sathish-dev-git/zenesis-oas-convertor), which is what turns
these documents into vendor-neutral OpenAPI:

| Key | What the converter does with it |
|---|---|
| `x-zenesis-title` | Dropped after verifying it equals `summary` |
| `x-zenesis-doc` | Dropped |
| `x-zenesis-usecase-tag` | Dropped |
| `x-zenesis-description-pageName` | Dropped |
| `x-zenesis-shared-note`, `x-zenesis-shared-notes` | Dropped |
| `x-zenesis-sections` | Folded into the operation description under a "Notes" heading |
| `x-zenesis-statuscodes` | Folded into the description as an "Error codes" table |
| `x-zenesis-security` | Folded into the description as "Rate limit" |
| `x-zenesis-enums-desc` | Rewritten to `x-enumDescriptions` and `x-enum-varnames` |

**Introducing an eleventh key is a two-repository change.** `python3 tools/validate_api_docs.py` fails
on any `x-zenesis-*` key it does not know, because the converter would otherwise either warn and stall
a release or - if the policy is ever relaxed - drop your content silently. Add the key to
`KNOWN_VENDOR_KEYS` here and a rule to `rules.json` there, in that order.

## When editing

- Keep the JSON valid and the indentation as the exporter writes it, so diffs stay readable.
- If you change an operation's title, change the matching `## N. Title` heading in
  [`../md/`](../md/README.md) too. They are joined by that string.
- `x-zenesis-title` and `summary` must be identical. The validator warns when they diverge, because the
  converter drops the title and the difference is lost.
- Add or update the snippets in [`../zenesis-oas-samples/`](../zenesis-oas-samples/README.md) for any
  path or method you add; samples referring to an operation that no longer exists are an error.
