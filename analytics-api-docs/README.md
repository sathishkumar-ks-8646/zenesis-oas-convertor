# Zoho Analytics REST API v2 - source documents

The single source of truth for the [Zoho Analytics REST API v2](https://www.zoho.com/analytics/api/v2/)
documentation: the narrative reference in Markdown, the Zenesis-flavoured OpenAPI specifications that
drive the published documentation site, the SDK snippets that accompany them, and the components every
specification shares.

**10 domains, 35 API groups, 119 paths, 180 operations.**

Nothing here is generated. Every downstream artefact - the public OpenAPI, the agent knowledge bundle,
the documentation site - is built from this repository, so a fact is corrected here first and flows
outward from there.

## Layout

| Path | Contents | Consumed by |
|---|---|---|
| [`md/`](md/README.md) | Narrative API reference, one file per API group inside one folder per domain. Prose, CONFIG attribute tables, behaviour notes, examples. | Humans, the documentation site, the OKF builder |
| [`zenesis-oas/`](zenesis-oas/README.md) | OpenAPI 3.1 with `x-zenesis-*` vendor extensions, one file per domain. The machine-readable contract. | The Zenesis renderer, `zenesis-oas-convertor`, the OKF builder |
| [`zenesis-oas-samples/`](zenesis-oas-samples/README.md) | SDK code snippets in 9 languages, keyed by path and method, one file per domain. | The documentation site, the OKF builder |
| `zoho-analytics-api-common.json` | Components shared by every domain: the `iam-oauth2-schema` security scheme with its OAuth scopes, and the common `Error` responses. | All of the above |
| [`tools/`](tools/README.md) | `validate_api_docs.py` - naming, completeness and integrity checks. The only executable thing here. | CI, maintainers |

A domain is named once and that name is repeated in three places. For the schedules domain:

```
md/09 · Schedules & Alerts/EMAIL_SCHEDULES.md              one file per group
zenesis-oas/schedules-alerts-grouped-api.json              one file per domain
zenesis-oas-samples/schedules-alerts-grouped-api-samples.json
```

The `<domain-slug>-grouped-api` file names are the export convention of the documentation system and a
contract with every consumer below - do not rename those. The folder names are read by the consumers'
build tooling (`SPECS` in the converter's Makefile, the `*_DIR` constants in the OKF builder), so a
rename here is a change there too.

## Where these documents go

```
                       ┌─► zenesis-oas-convertor ──► clean OpenAPI 3.x ──► Swagger UI, SDK generators, MCP
analytics-api-docs ────┤
   (you are here)      └─► okf-bundle ──────────────► zoho-analytics-okf (OKF v0.2 bundle for AI agents)
                       │
                       └─► the Zenesis renderer ───► www.zoho.com/analytics/api/v2/
```

| Repository | Role |
|---|---|
| [zenesis-oas-convertor](https://github.com/sathish-dev-git/zenesis-oas-convertor) | Converts `zenesis-oas/` into vendor-neutral OpenAPI: strips `x-zenesis-*`, rewrites private conventions into ecosystem ones, folds error tables and rate limits into descriptions. Reads this repository through its `analytics-api-docs/` submodule. |
| [okf-bundle](https://github.com/sathish-dev-git/okf-bundle) | Build sources for the agent knowledge bundle. Reads `md/`, `zenesis-oas/`, `zenesis-oas-samples/` and the common JSON through its `analytics-api-docs/` submodule. |
| [zoho-analytics-okf](https://github.com/sathish-dev-git/zoho-analytics-okf) | The published Open Knowledge Format bundle that `okf-bundle` generates. |

Neither consumer holds a copy. Each includes this repository as a **git submodule** named
`analytics-api-docs`, tracking `main` and pinned to one commit, so every build states exactly which
revision of the source it was built from. After pushing a change here, move that pin - see
[Publishing a change](#publishing-a-change).

## Quick start

Python 3.8+, standard library only. Run from the repository root.

```bash
python3 tools/validate_api_docs.py        # must end with errors=0
python3 tools/validate_api_docs.py --strict   # warnings fail too; what CI runs
```

Reading an endpoint: find the group in [`md/`](md/README.md) for the behaviour and the CONFIG
attributes, then the matching operation in [`zenesis-oas/`](zenesis-oas/README.md) for the exact
schema. The two are joined by title (`x-zenesis-title`, else `summary`), which is why the titles must
match exactly.

## Conventions

- **Domain folders** are `NN · Title`, numbered consecutively from `01`, separated by a middle dot
  (U+00B7) with a space on each side.
- **Group files** are `UPPER_SNAKE_CASE.md`, one per OpenAPI tag in that domain's specification.
- **Specification files** are `<domain-slug>-grouped-api.json`; samples are
  `<domain-slug>-grouped-api-samples.json`. The slug is stable and is what the converter and the OKF
  builder key off.
- **Every operation carries a tag**, and every tag has a markdown file. That pairing is the definition
  of an API group.
- **Error responses are `4XX` and `500`**, each a `$ref` to the shared responses in the common file,
  never a `default`. The `x-zenesis-statuscodes` table sits on the success response. See
  [`zenesis-oas/README.md`](zenesis-oas/README.md#error-responses).
- **Titles are the join key.** A markdown section `## N. Create Email Schedule` pairs with the operation
  whose `x-zenesis-title` is `Create Email Schedule`. Changing one without the other breaks the bundle
  build.
- **Vendor extensions** are limited to the ten `x-zenesis-*` keys the converter has rules for. A new one
  fails validation here before it can be dropped silently downstream.

The full inventory - every domain, group and tag - lives in the `DOMAINS` table in
[`tools/validate_api_docs.py`](tools/validate_api_docs.py). Nothing is discovered by scanning, so adding
a document means adding a row.

## Making a change

1. Edit the markdown in `md/` and the operation in `zenesis-oas/`, and add or update the snippets in
   `zenesis-oas-samples/`. All three, or the consumers disagree with each other.
2. For a new group or domain, add the row to `DOMAINS` in `tools/validate_api_docs.py` first; the
   validator will then tell you which of the three files is still missing.
3. Run `python3 tools/validate_api_docs.py --strict` and fix everything it reports.
4. Commit the markdown, the specification and the samples together, in one commit.

## Publishing a change

This repository does not build anything. A change reaches users when each consumer moves its submodule
pin to the new commit and rebuilds. Push here first - a pin that points at a commit GitHub does not have
breaks every fresh clone of the consumer.

```bash
# in zenesis-oas-convertor or okf-bundle, after the change here is on main
git submodule update --remote --merge analytics-api-docs   # move the pin to the tip of main
git diff --submodule                                       # review which upstream commits came in
```

Then the consumer's own build, which is what proves the change is sound downstream:

```bash
make check && make convert                                    # zenesis-oas-convertor
python3 tools/build_okf.py && python3 tools/validate_okf.py   # okf-bundle
```

Commit the pin together with whatever the rebuild changed (`overlays/` in the converter, `bundle/` in
okf-bundle), so the consumer's history shows which source revision produced which output. A fresh clone
of a consumer gets the source with `git clone --recurse-submodules`, or `git submodule update --init`
after the fact.

## Versioning

The API version is always v2. This repository versions the *documentation*, in `CHANGELOG.md`, using
semantic versioning: major when an endpoint is removed or renamed or the layout changes, minor when
endpoints, groups or domains are added, patch for corrections and clarifications.

## Licence

See [LICENSE.md](LICENSE.md).
