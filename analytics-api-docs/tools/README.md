# tools

One standard-library Python script (3.8+). It locates the repository by its own path, so the working
directory does not matter.

| Script | Reads | Writes | Purpose |
|---|---|---|---|
| `validate_api_docs.py` | `md/`, `zenesis-oas/`, `zenesis-oas-samples/`, `zoho-analytics-api-common.json` | nothing | Naming, completeness and integrity of the export. Prints `domains=… groups=… paths=… operations=… errors=… warnings=…`. Exits non-zero when `errors` is non-zero, or on any warning with `--strict`. |

```bash
python3 tools/validate_api_docs.py
python3 tools/validate_api_docs.py --strict     # what CI runs
```

## What it checks

**Naming.** Domain folders are `NN · Title` numbered consecutively from `01`; group files are
`UPPER_SNAKE_CASE.md`; specification and samples files end in `-grouped-api.json` and
`-grouped-api-samples.json`.

**Completeness.** Every domain in `DOMAINS` has a markdown folder, a specification and a samples file.
Every group has a markdown file *and* a tag in the specification, and every declared tag has a group.
Every operation carries a tag the document declares and a title the OKF builder can join on.

**Response model.** Every operation has exactly one success response (`200`/`201`/`204`), a `4XX` and a
`500` that `$ref` the shared `CommonErrorResponse` and `UnexpectedErrorResponse`, and no `default`.
`x-zenesis-statuscodes` sits on the success response.

**Integrity.** All JSON parses. Samples name only paths and methods the specification defines. The
common file defines `iam-oauth2-schema`. No `x-zenesis-*` key appears that the converter has no rule
for.

## The DOMAINS table

Nothing is discovered by scanning. `DOMAINS` in `validate_api_docs.py` lists every domain folder, its
specification slug, and each `(markdown stem, OpenAPI tag)` pair - the same shape as the `DOMAINS`
table in `okf-bundle/tools/build_okf.py`, which is the other place that has to know this mapping.

Adding a group or a domain starts here: add the row, run the validator, and it names each of the files
still missing.

## Keeping in step with the converter

`KNOWN_VENDOR_KEYS` mirrors the `rules` object of `rules.json` in
[zenesis-oas-convertor](https://github.com/sathishkumar-ks-8646/zenesis-oas-convertor). A key in the specs
but not in that set is an error here; a key in the set that appears in no spec is a warning, which
usually means a convention was retired and the rule can go too.
