# Conversion reference

What each rule does, how to add one, and what to fix upstream.

## Actions

### `drop`

Removes the key. Optionally verifies first, and warns instead of staying quiet
when the check fails.

```json
{ "action": "drop", "verify": "equals_sibling", "sibling": "summary" }
{ "action": "drop", "verify": "text_covered", "text_fields": ["value"] }
{ "action": "drop" }
```

| `verify` | Checks |
| --- | --- |
| `equals_sibling` | The value is identical to a named sibling field. Warns if not, since the difference would be lost. |
| `text_covered` | Prose in `text_fields` already appears in the enclosing operation's `description` / `summary` / `title`, following local `$ref`s. Warns if not. |
| *(omitted)* | Nothing. Use for pure renderer config with no prose. |

### `keep`

Leaves the key in place. Use for genuine vendor data you want in the published
spec.

### `enum_descriptions`

`x-zenesis-enums-desc` is a positional array parallel to `enum`. Reordering the
enum silently shifts every label. This action rewrites it as a keyed map:

```jsonc
// before
"enum": [0, 1, 2],
"x-zenesis-enums-desc": ["COMMA", "TAB", "SEMICOLON"]

// after
"enum": [0, 1, 2],
"x-enumDescriptions": { "0": "COMMA", "1": "TAB", "2": "SEMICOLON" },
"x-enum-varnames": ["COMMA", "TAB", "SEMICOLON"]
```

`x-enumDescriptions` is Redocly's spelling and renders as an option table.
`x-enum-varnames` is emitted only for integer-coded enums, where the labels are
symbolic *names* rather than prose — SDK generators read it to produce
`Delimiter.COMMA` instead of `Delimiter._0`.

Refuses and warns on: length mismatch, duplicate enum values, no sibling `enum`.
Set `options.emit_enum_varnames` to `false` to suppress the second key.

### `fold_sections`

`x-zenesis-sections` holds HTML note blocks. Roughly two thirds restate the
operation description; the rest carry constraints that exist nowhere else --
204-with-no-body behaviour, permission requirements, axis-casing rules.

Each block is converted to Markdown and appended to the enclosing operation's
description, **unless** the operation already covers that text. Across the ten
Zoho Analytics specs that means 122 blocks skipped as duplicates, 97 sections
fully redundant, and 70 blocks preserved that a plain `drop` would have lost.

```json
{ "action": "fold_sections", "heading": "Notes", "skip_covered": true, "text_fields": ["value"] }
```

Set `skip_covered` to `false` to fold everything regardless, or switch the
action to `drop` with `verify: text_covered` to delete instead and be warned
about what is lost.

The HTML converter handles exactly the vocabulary Zenesis uses -- `<b>`,
`<code>`, `<li>`, `<ul>`, `<br>`, `<blockquote>`, `<span>`. It is not a general
HTML converter. A new tag would pass through as plain text with the tag
stripped.

### `fold_throttles`

`x-zenesis-security` carries rate limits:

```json
{ "throttles": [{ "duration": 60, "threshold": 7, "lock-period": 300 }] }
```

No standard OpenAPI field holds rate limits, and every caller needs them, so
they are rendered as prose on the operation:

> **Rate limit**
>
> - Up to 7 requests per 60 seconds. Exceeding this blocks further calls for 300 seconds.

Warns if any key other than `throttles` appears, so a future addition is not
silently discarded.

### `fold_status_codes`

`x-zenesis-statuscodes` is an error-code catalogue: a list of
`{name, description, resolution}`. This is real API documentation, so deleting
it would strip content that developers and AI agents need.

The action renders it as a Markdown table appended to the enclosing
**operation** description. Note it appears on the `200` response in the source
specs even though every entry is an error, which is why the table goes on the
operation rather than the response it was attached to.

```json
{ "action": "fold_status_codes", "heading": "Error codes" }
```

Skips and warns if the description already contains the heading, so re-running
never duplicates the table.

## Adding a rule for a new key

`make inventory` names any key without a rule. Then decide:

| The key is... | Use |
| --- | --- |
| A duplicate of a standard field | `drop` with `verify: equals_sibling` |
| HTML restating prose already present | `drop` with `verify: text_covered` |
| Pure renderer layout config | `drop` |
| Real vendor data to publish | `keep` |
| Content needing a new shape | a new handler in `rules.py` |

Only the last requires Python: add a function to `zenesis_oas/rules.py` with
the signature `(node, key, value, ctx, path, report)` and register it in
`HANDLERS`. Add a test in `tests/test_zenesis_oas.py` alongside it.

## Fixing the source instead

Several rules exist only because the Zenesis renderer needs something it should
not. Each of these can be retired by changing the renderer, which is strictly
better than converting around it forever:

| Change the renderer to... | Retires |
| --- | --- |
| Read `summary` as the example label and `description` as the prose | 83 field swaps |
| Fall back to `summary` when `x-zenesis-title` is absent | 32 duplicate titles |
| Read `x-enumDescriptions` | 79 positional arrays |
| Stop requiring `x-zenesis-sections` (the prose is already in `description`) | 18 HTML blocks |

The swap is the one worth doing regardless of everything else in this repo. It
is the only item that produces genuinely *wrong* output in standard tooling
rather than merely redundant output.

## Shared notes

`reports-dashboards` carries a note catalogue at
`$.components['x-zenesis-shared-notes']`, and each use site tags its copy with
`x-zenesis-shared-note` naming the catalogue key.

All 43 references resolve, and every materialised `value` is byte-identical to
its catalogue entry, so both keys are dropped: the prose is already inline at
each use site and `fold_sections` carries it into the description. If that
invariant ever breaks -- a note edited in the catalogue but not propagated --
the converter will not notice, because it only ever reads the inlined copy.
Keep the propagation step in the authoring workflow.

## Overlays

`make overlays` writes two documents per spec:

- `<name>.live.overlay.json` — genuine Zenesis config (`x-zenesis-usecase-tag`,
  `x-zenesis-doc`)
- `<name>.compat.overlay.json` — everything else, with an `x-migration` note on
  each action explaining what to change so it can be deleted

They are derived by diffing the original against the converted output, so they
are complete by construction — the generator cannot forget a rule the converter
applies. `make verify` reapplies them and asserts byte equality with the source.

Commit them. A diff in `overlays/` during code review is the signal that
somebody added a new vendor convention.
