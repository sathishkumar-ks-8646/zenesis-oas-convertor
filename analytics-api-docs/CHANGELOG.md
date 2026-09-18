# Changelog

All notable changes to these API source documents are recorded here. Versions follow semantic
versioning and describe the documentation, not the API, which is always v2: major for a removed or
renamed endpoint or a layout change, minor for additions, patch for corrections.

## 1.0.0 - 2026-09-16

### Added

- First release of the Zoho Analytics REST API v2 source documents as a repository of their own:
  10 domains, 35 API groups, 119 paths, 180 operations.
- `md/` - narrative reference, one file per API group across ten domain folders.
- `zenesis-oas/` - OpenAPI 3.1 with `x-zenesis-*` extensions, one document per domain.
- `zenesis-oas-samples/` - SDK snippets for all 180 operations in 9 languages
  (cURL, C#, Go, Java, PHP, Python, Node.js, Ruby, Deluge).
- `zoho-analytics-api-common.json` - the `iam-oauth2-schema` security scheme, its OAuth scopes and the
  shared error responses.
- `tools/validate_api_docs.py` - naming, completeness and integrity checks, with the `DOMAINS`
  inventory, and CI running it in `--strict` mode.
- READMEs at the root and in every folder describing the conventions and the downstream consumers.

### Changed

- `user-groups-grouped-api.json`: the 26 operations that modelled errors as an inline `default` response
  now use the `4XX` / `500` `$ref` pair like the other nine specifications, with `x-zenesis-statuscodes`
  moved to the success response. No error codes or descriptions were lost; the validator now enforces
  this model for every operation.

### Notes

- `zenesis-oas-convertor` and `okf-bundle` consume this repository as a git submodule
  (`analytics-api-docs/`, tracking `main`). The copies they previously carried under `specs/` and
  `api-docs/` are removed in the same change.
- Two API groups that the former `okf-bundle/api-docs/` copy did not carry enter the bundle on its first
  build from the submodule: Custom Roles (`02 · User & Groups`) and Tags (`06 · Views Management`).
