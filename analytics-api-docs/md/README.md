# md - narrative API reference

One folder per domain, one Markdown file per API group. This is where behaviour is explained: what an
object is, which CONFIG attributes a call accepts, what the server does that the schema cannot express,
and what an integrator gets wrong if they do not read it.

The OpenAPI in [`../zenesis-oas/`](../zenesis-oas/README.md) is the contract; these documents are the
reason the contract looks the way it does. Both are authored, neither is generated from the other.

## Layout

```
md/
└── <NN · Domain Title>/
    └── <GROUP_NAME>.md
```

| Folder | Groups | Specification |
|---|---|---|
| `01 · Organization Management` | 1 | `org-management-grouped-api.json` |
| `02 · User & Groups` | 4 | `user-groups-grouped-api.json` |
| `03 · Workspace Management` | 4 | `workspace-management-grouped-api.json` |
| `04 · Data Modeling & Schema` | 7 | `data-modeling-schema-grouped-api.json` |
| `05 · Data Operations` | 6 | `data-operations-grouped-api.json` |
| `06 · Views Management` | 5 | `views-management-grouped-api.json` |
| `07 · Reports & Dashboards` | 2 | `reports-dashboards-grouped-api.json` |
| `08 · Share & Publish` | 4 | `share-publish-grouped-api.json` |
| `09 · Schedules & Alerts` | 1 | `schedules-alerts-grouped-api.json` |
| `10 · DSML` | 1 | `dsml-grouped-api.json` |

## Naming

- Domain folders are `NN · Title`: a two-digit number, a space, a **middle dot** (U+00B7, not a hyphen
  or a bullet), a space, then the title. The numbers run consecutively from `01` and set the order the
  domains appear in the documentation site.
- Group files are `UPPER_SNAKE_CASE.md`. One file per tag declared in that domain's OpenAPI document -
  no more, no fewer. `TABLE_AND_SCHEMA.md` pairs with the tag `Table & Schema`; the pairing is recorded
  in the `DOMAINS` table in [`../tools/validate_api_docs.py`](../tools/validate_api_docs.py) because it
  is not always mechanical (`EMBED_URL.md` pairs with the tag `Embed`).

## Document structure

Each file opens with a single H1, then the sections the group needs - concept explanation, index table,
cross-cutting behaviour - and then one section per endpoint:

```markdown
# Zoho Analytics V2 REST API — Email Schedules

## What is an "Email Schedule" in Zoho Analytics?
...
## Index
| # | API Name | Method | URL |
...
## 1. Get Email Schedules
## 2. Create Email Schedule
```

**The `## N. Title` heading is a join key, not decoration.** The OKF builder in `okf-bundle` matches
each heading against the OpenAPI operation whose `x-zenesis-title` (else `summary`) is the same string.
Rename an endpoint in one place only and the build emits a `WARN` and produces an endpoint document
with no schema. Rename in both.

## When editing

- Change the markdown, the OpenAPI operation and the SDK samples in the same commit. A behaviour note
  that contradicts the schema is worse than no note.
- Keep the index table at the top of the file in step with the sections below it.
- Relative links between group documents resolve on GitHub and in a clone; keep them relative.
- Adding a group means: a new `.md` file here, a new tag and its operations in the domain
  specification, snippets in the samples file, and a new row in `DOMAINS`. The validator fails until
  all four exist.
