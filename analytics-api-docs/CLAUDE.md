# Zoho Analytics API source documents - agent instructions

Read `README.md` for the layout and `tools/README.md` for what is enforced. The
`<domain-slug>-grouped-api` file naming is a contract with the downstream repositories - **never
rename those files.** The folders `md/`, `zenesis-oas/` and `zenesis-oas-samples/` are read by name
by the consumers' build tooling, so renaming one is a change in those repositories too.

The one rule: **an API fact lives in three places, so change all three together** - the group document
in `md/`, the operation in `zenesis-oas/`, and the snippets in `zenesis-oas-samples/`. A markdown
endpoint heading (`## N. Title`) and its operation are joined by title; rename one without the other
and the OKF build silently produces an endpoint with no schema.

```bash
python3 tools/validate_api_docs.py --strict   # must end with errors=0 warnings=0
```

Adding a group or domain starts with a row in the `DOMAINS` table in `tools/validate_api_docs.py`; the
validator then names each file still missing. A new `x-zenesis-*` key also needs a rule in
`rules.json` in `zenesis-oas-convertor`, or the converter cannot handle it.

Nothing here builds or publishes. `zenesis-oas-convertor` and `okf-bundle` include this repository as
a git submodule pinned to a commit on `main`; after a change lands here, move their pin and rebuild -
see "Publishing a change" in `README.md`.
