# zenesis-oas-samples - SDK code snippets

The runnable examples that accompany each operation, in nine languages. One file per domain, named
`<domain-slug>-grouped-api-samples.json` to pair with `<domain-slug>-grouped-api.json` in
[`../zenesis-oas/`](../zenesis-oas/README.md).

They are kept out of the specifications on purpose: the snippets are large, they change independently
of the contract, and a diff on one should not be a diff on the other.

Coverage today is complete - all 180 operations, all nine languages.

## Shape

A document is an object keyed by path, then by HTTP method, then by language:

```jsonc
{
  "/restapi/v2/workspaces/{workspace-id}/emailschedules": {
    "post": {
      "Curl":   { "snippets": [ { "code": "curl \"https://analyticsapi.zoho.com/…\" -X 'POST' …" } ] },
      "Python": { "snippets": [ { "code": "…" } ] }
    }
  }
}
```

Language keys, in the order the documentation site renders them:
`Curl`, `C#`, `Go`, `Java`, `Php`, `Python`, `Node`, `Ruby`, `Deluge`.

The path and method keys must name an operation that the domain's specification actually defines -
samples for an operation that no longer exists are a validation error, and an operation with no samples
is a warning.

## Conventions inside a snippet

- The path templates are filled in with the same illustrative IDs across every language, so a reader
  comparing two tabs sees one example, not two.
- Credentials are placeholders - `<access_token>`, `<org-id>` - never a real token.
- `https://analyticsapi.zoho.com` is the host in every snippet. Data-centre variants are explained in
  the reference prose, not duplicated here.
- The `CONFIG` payload in a snippet should match the example in the operation's schema. If you change
  one, change the other.

## When editing

Add or update snippets in the same commit as the operation they document. When adding a path, provide
all nine languages: a partially populated method renders as an empty tab on the documentation site.
