# zenesis-oas

Convert Zenesis-flavoured OpenAPI documents into clean, vendor-neutral OpenAPI 3.x.

Point it at a folder of JSON specs and it writes a folder of standards-compliant
ones. No dependencies, no network, no config required to start.

The specs themselves are not stored here. They are the `zenesis-oas/` folder of
[analytics-api-docs](https://github.com/sathishkumar-ks-8646/analytics-api-docs),
included as a git submodule and pinned to one commit, so every conversion states
which revision of the source it came from.

```bash
git clone --recurse-submodules https://github.com/sathishkumar-ks-8646/zenesis-oas-convertor.git
python3 -m zenesis_oas inventory analytics-api-docs/zenesis-oas/        # what vendor keys are in here?
python3 -m zenesis_oas convert   analytics-api-docs/zenesis-oas/ dist/  # write clean OpenAPI
python3 -m zenesis_oas verify    analytics-api-docs/zenesis-oas/        # prove nothing was lost
```

Or, with the Makefile:

```bash
make inventory
make convert
make check      # inventory + tests + verify, this is what CI runs
```

## Requirements

Python 3.8 or newer. That is the entire list — the package imports only the
standard library, so it runs on any build agent without a pip install.

Git, for the specs: clone with `--recurse-submodules`, or run `make sources`
after a plain clone. Every Make target that reads specs depends on it.

`make check` optionally validates output with `openapi-spec-validator`; the CI
workflow installs it in a separate step you can delete if your runners are
offline.

## The problem this solves

A Zenesis spec is already valid OpenAPI 3.1 — vendor extensions are legal
anywhere, and every conformant tool ignores keys beginning with `x-`. So this
is not a format conversion. It is a *separation*, and it does three jobs:

1. **Removes renderer-only decoration** so the published spec carries no
   Zenesis-specific keys.
2. **Rewrites private conventions into ecosystem ones.** `x-zenesis-enums-desc`
   becomes `x-enumDescriptions` (which Redocly renders) and `x-enum-varnames`
   (which SDK generators read to emit `Delimiter.COMMA` instead of
   `Delimiter._0`).
3. **Fixes what is actually wrong.** Zenesis stores the short label of an
   Example Object in `description` and the long prose in `summary`, which is
   the reverse of the specification. Any standard renderer shows those the
   wrong way round. The converter swaps them back.
4. **Rescues content that has nowhere standard to live.** Error-code tables,
   rate limits and HTML note blocks are folded into the operation description
   as Markdown, so they reach Swagger UI, SDK docs and MCP tool descriptions
   instead of being deleted.

The whole point is that nothing is lost quietly. Content that would vanish
gets either rewritten into a standard field or reported as a warning.

## Commands

| Command | Purpose |
| --- | --- |
| `inventory SRC` | List every vendor key found, with counts and an example location. Exits non-zero if any key has no rule. **Run this first when adding specs.** |
| `convert SRC DST` | Write clean OpenAPI. `SRC` may be a file or a directory. Exits non-zero if any file produced warnings. |
| `overlay SRC --out DIR` | Regenerate the Overlay 1.0.0 documents that turn converted output back into the source. |
| `verify SRC [--overlays DIR]` | Prove `converted + overlays == original`, byte for byte. |

Every command accepts `--rules FILE` to use a custom `rules.json`.

## Updating the specs

Specs are edited in the analytics-api-docs repository, never here. When a
change lands on its `main`, move the pin and re-check:

```bash
make update-sources   # pin -> tip of analytics-api-docs main; prints the commits that came in
make inventory        # does every vendor key still have a rule?
make check            # tests + verify
```

If `verify` reports `round trip lost data`, the vendor-key content of that
spec changed and the committed overlay is stale: run `make overlays`, re-run
`make verify`, and commit the pin together with the regenerated overlays. That
diff *is* the review of what changed upstream.

`make inventory` ends in one of two ways.

**Every key already has a rule.** Nothing to do — `make convert` handles it.

**A key has no rule.** Inventory marks it `<-- NOT IN rules.json` and exits 1.
Add an entry to `rules.json` choosing how to handle it. See
[docs/CONVERSION.md](docs/CONVERSION.md) for the available actions. Only a key
needing a genuinely new *transform* requires Python.

This is the mechanism that keeps the tool from rotting as Zenesis grows new
conventions. A new key can never be dropped silently.

## Configuring behaviour

`rules.json` holds one entry per vendor extension:

```json
{
  "vendor_prefix": "x-zenesis-",
  "unknown_key_policy": "warn",
  "options": { "unswap_examples": true, "emit_enum_varnames": true },
  "rules": {
    "x-zenesis-title": { "action": "drop", "verify": "equals_sibling", "sibling": "summary" },
    "x-zenesis-enums-desc": { "action": "enum_descriptions" },
    "x-zenesis-statuscodes": { "action": "fold_status_codes", "heading": "Error codes" }
  }
}
```

Actions: `drop`, `keep`, `enum_descriptions`, `fold_sections`,
`fold_status_codes`, `fold_throttles`.
`unknown_key_policy`: `warn` (default), `drop`, `keep`, `error`.

## Warnings are the product

The converter never guesses. When something looks wrong it says so and leaves
the data alone rather than producing plausible-looking damage.

- A `x-zenesis-title` that differs from `summary` → the text would be lost
- Prose in `x-zenesis-sections` that appears nowhere else in the operation
- An `enum` whose length does not match its label array → dropped, not aligned by guess
- An example where `summary` is already shorter than `description` → left untouched
- Any vendor key with no rule

`make convert` and `make verify` exit non-zero when warnings appear, so these
block a release rather than scrolling past in a log.

## Repository layout

```
analytics-api-docs/   git submodule -> the analytics-api-docs repository, pinned to one commit
  └─ zenesis-oas/     the source Zenesis JSON the converter reads
dist/         generated clean OpenAPI      <- gitignored, this is what you publish
overlays/     generated Overlay 1.0.0      <- committed, so vendor drift shows in review
rules.json    how each vendor key is handled
zenesis_oas/  the package
tests/        standard-library test suite
```

## Should I use the converter or an overlay?

The converter, almost always.

An [OpenAPI Overlay](https://spec.openapis.org/overlay/v1.0.0.html) is a
declarative document of `target`/`update` actions applied to a base spec. This
repo generates overlays, but only as an *audit artifact*: they prove the
conversion is lossless, and a diff in `overlays/` during review shows exactly
when someone introduced a new Zenesis convention.

Overlays cannot replace the converter, for two reasons. Their targets are
JSONPath pointers into one specific document, so they are not reusable across
files. And their actions carry literal values, not transforms — an overlay can
delete a key but cannot convert a positional array into a keyed map or swap two
fields.

`overlays/strip-zenesis.overlay.json` is the one exception: it uses recursive
descent, so it works unchanged on any Zenesis spec. It can only delete, so it
discards enum labels rather than converting them, and it silently ignores keys
it does not enumerate. Use it only when you need a standards-only step that
another team's Overlay tooling can run.

## Publishing

`dist/` is what your users consume. Serve it at a stable URL and link it from
the docs site — that URL is the entire user-facing surface of this work.
Developers point Swagger UI, Redoc, `openapi-generator`, or an MCP server at it
and it works.

The Zenesis renderer keeps reading analytics-api-docs exactly as it does today.
Nothing about the authoring workflow changes.

## Development

```bash
make test                              # unit tests
python3 -m unittest discover -s tests -v
pip install -e .                       # optional, gives you a `zenesis-oas` command
```
