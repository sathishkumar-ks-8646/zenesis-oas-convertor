"""
One handler per vendor extension, selected by `rules.json`.

Adding support for a newly-discovered `x-zenesis-*` key means adding an entry
to rules.json. It only means writing Python if the key needs a transform that
none of the existing actions cover.
"""

import html
import json
import re

# --------------------------------------------------------------------- text

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")
_WORD = re.compile(r"[a-z0-9]{5,}")


def plain(text):
    """Strip HTML tags, unescape entities, collapse whitespace."""
    return _WS.sub(" ", html.unescape(_TAG.sub(" ", text or ""))).strip()


def resolve_pointer(pointer, root):
    """Resolve a local JSON Pointer such as '#/components/schemas/Foo'."""
    if not isinstance(pointer, str) or not pointer.startswith("#/"):
        return None
    node = root
    for raw in pointer[2:].split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(node, list):
            try:
                node = node[int(token)]
            except (ValueError, IndexError):
                return None
        elif isinstance(node, dict) and token in node:
            node = node[token]
        else:
            return None
    return node


def reachable_text(node, root):
    """
    Every description/summary/title reachable from `node`, following local
    $refs, flattened into one lowercase blob for containment checks.
    """
    parts, seen = [], set()

    def walk(current):
        if isinstance(current, dict):
            ref = current.get("$ref")
            if isinstance(ref, str) and ref not in seen:
                seen.add(ref)
                walk(resolve_pointer(ref, root))
            for key, value in current.items():
                if key in ("description", "summary", "title") and isinstance(value, str):
                    parts.append(value)
                walk(value)
        elif isinstance(current, list):
            for value in current:
                walk(value)

    walk(node)
    return plain(" ".join(parts)).lower()


def covered_by(text, haystack, threshold=0.6):
    """True when most meaningful words of `text` already appear in `haystack`."""
    words = _WORD.findall(plain(text).lower())
    if not words:
        return True
    return sum(1 for w in words if w in haystack) / len(words) >= threshold


# ----------------------------------------------------------------- handlers
# Each handler receives:
#   node      the dict the vendor key was found on
#   key       the vendor key name
#   value     the value, already popped off `node`
#   ctx       ConversionContext (root document, enclosing operation, options)
#   path      JSONPath of `node`, for warning messages
#   report    Report to record counts and warnings on


def handle_drop(node, key, value, ctx, path, report):
    """Remove the key. Optional `verify` checks warn when content would be lost."""
    rule = ctx.rule(key)
    verify = rule.get("verify")

    if verify == "equals_sibling":
        sibling = rule.get("sibling", "summary")
        if value != node.get(sibling):
            report.warn(
                path,
                "%s is %r but sibling %r is %r -- the value is being lost"
                % (key, value, sibling, node.get(sibling)),
            )

    elif verify == "text_covered":
        # Only the designated content fields carry prose. Sibling keys such as
        # `type: "editor"` are structural and would produce noise.
        fields = rule.get("text_fields", ["value"])
        haystack = reachable_text(ctx.operation or node, ctx.root)
        for text in _collect_field_strings(value, fields):
            flat = plain(text)
            if flat and not covered_by(flat, haystack):
                snippet = flat if len(flat) <= 120 else flat[:117] + "..."
                report.warn(
                    path,
                    "dropping prose that appears nowhere else in this operation: %r"
                    % snippet,
                )

    report.hit("%s dropped" % key)


def handle_keep(node, key, value, ctx, path, report):
    """Put the key back untouched."""
    node[key] = value
    report.hit("%s kept" % key)


def handle_enum_descriptions(node, key, value, ctx, path, report):
    """
    x-zenesis-enums-desc (positional array) ->
        x-enumDescriptions  keyed by enum value, order-independent
        x-enum-varnames     when the enum is integer-coded, so SDK generators
                            emit Delimiter.COMMA rather than Delimiter._0
    """
    values = node.get("enum")

    if not isinstance(value, list):
        report.warn(path, "%s is not a list; dropped" % key)
        return
    if not values:
        report.warn(path, "%s has no sibling `enum`; dropped" % key)
        return
    if len(values) != len(value):
        report.warn(
            path,
            "enum has %d values but %d labels -- positional alignment is broken, "
            "so the labels were dropped rather than guessed"
            % (len(values), len(value)),
        )
        return
    if len({str(v) for v in values}) != len(values):
        report.warn(path, "enum has duplicate values; cannot key a map by them; dropped")
        return

    node["x-enumDescriptions"] = {str(v): str(d) for v, d in zip(values, value)}
    report.hit("x-enumDescriptions written")

    if ctx.options.get("emit_enum_varnames", True) and all(
        not isinstance(v, str) for v in values
    ):
        node["x-enum-varnames"] = [
            re.sub(r"[^A-Za-z0-9]+", "_", str(d)).strip("_").upper() for d in value
        ]
        report.hit("x-enum-varnames written")


def handle_fold_status_codes(node, key, value, ctx, path, report):
    """
    x-zenesis-statuscodes is an error-code catalogue -- real API documentation
    that would be invisible to Swagger UI, SDK docs and MCP tool descriptions
    if simply deleted. Render it as a Markdown table appended to the enclosing
    operation's description.

    Note it is attached to the 200 response in the source specs even though
    every entry is an error, which is why the table goes on the operation
    rather than on the response it was found under.
    """
    target = ctx.operation if ctx.operation is not None else node

    if not isinstance(value, list) or not value:
        report.warn(path, "%s is empty or not a list; dropped" % key)
        return

    heading = ctx.rule(key).get("heading", "Error codes")
    rows = ["| Code | Meaning | Resolution |", "| --- | --- | --- |"]
    for entry in value:
        if not isinstance(entry, dict):
            continue
        rows.append(
            "| %s | %s | %s |"
            % (
                _cell(entry.get("name")),
                _cell(entry.get("description")),
                _cell(entry.get("resolution")),
            )
        )

    if len(rows) == 2:
        report.warn(path, "%s had no usable entries; dropped" % key)
        return

    table = "**%s**\n\n%s" % (heading, "\n".join(rows))
    existing = target.get("description") or ""

    if heading.lower() in existing.lower():
        report.warn(
            path,
            "operation description already contains a %r section; %s not folded in "
            "to avoid duplicating it" % (heading, key),
        )
        return

    target["description"] = (existing + "\n\n" + table).strip()
    report.hit("%s folded into description" % key)


def handle_fold_throttles(node, key, value, ctx, path, report):
    """
    x-zenesis-security carries rate limits:

        {"throttles": [{"duration": 60, "threshold": 7, "lock-period": 300}]}

    Rate limits are something every caller needs and no standard OpenAPI field
    holds, so render them as prose on the enclosing operation rather than
    discarding them.
    """
    target = ctx.operation if ctx.operation is not None else node
    throttles = value.get("throttles") if isinstance(value, dict) else None

    if not isinstance(throttles, list) or not throttles:
        report.warn(path, "%s has no usable `throttles`; dropped" % key)
        return

    extra = [k for k in value if k != "throttles"]
    if extra:
        report.warn(
            path,
            "%s has unhandled key(s) %s alongside `throttles`; only the "
            "throttles were kept" % (key, ", ".join(sorted(extra))),
        )

    lines = []
    for throttle in throttles:
        if not isinstance(throttle, dict):
            continue
        threshold = throttle.get("threshold")
        duration = throttle.get("duration")
        lock = throttle.get("lock-period", throttle.get("lockPeriod"))
        if threshold is None or duration is None:
            continue
        sentence = "Up to %s request%s per %s second%s." % (
            threshold, "" if threshold == 1 else "s",
            duration, "" if duration == 1 else "s",
        )
        if lock is not None:
            sentence += (" Exceeding this blocks further calls for %s seconds."
                         % lock)
        lines.append("- " + sentence)

    if not lines:
        report.warn(path, "%s had no usable throttle entries; dropped" % key)
        return

    heading = ctx.rule(key).get("heading", "Rate limit")
    if heading.lower() in (target.get("description") or "").lower():
        report.warn(
            path,
            "operation description already contains a %r section; %s not folded "
            "in to avoid duplicating it" % (heading, key),
        )
        return

    block = "**%s**\n\n%s" % (heading, "\n".join(lines))
    target["description"] = ((target.get("description") or "") + "\n\n" + block).strip()
    report.hit("%s folded into description" % key)


_BLOCKQUOTE = re.compile(r"<blockquote>(.*?)</blockquote>", re.DOTALL | re.IGNORECASE)


def html_to_markdown(source):
    """
    Convert the small HTML vocabulary Zenesis uses into Markdown.

    The section bodies only ever contain <b>, <code>, <li>, <ul>, <br>,
    <blockquote> and <span>, so a regex pipeline is faithful here. It is not a
    general HTML converter and is not meant to be.
    """
    text = source or ""
    text = re.sub(r"</?span[^>]*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<b>(.*?)</b>", r"**\1**", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<code>(.*?)</code>", r"`\1`", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(
        r"<li>(.*?)</li>",
        lambda m: "- " + _WS.sub(" ", m.group(1)).strip() + "\n",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    text = re.sub(r"</?ul>", "\n", text, flags=re.IGNORECASE)

    def quote(match):
        lines = [line.rstrip() for line in match.group(1).splitlines()]

        collapsed = []
        for line in lines:
            if line.strip():
                collapsed.append(line)
            elif collapsed and collapsed[-1] != "":
                collapsed.append("")          # at most one blank in a row

        while collapsed and collapsed[0] == "":
            collapsed.pop(0)
        while collapsed and collapsed[-1] == "":
            collapsed.pop()

        # Consecutive list items read better without blank lines between them.
        tightened = []
        for index, line in enumerate(collapsed):
            following = collapsed[index + 1] if index + 1 < len(collapsed) else ""
            if (
                line == ""
                and tightened
                and tightened[-1].startswith("- ")
                and following.startswith("- ")
            ):
                continue
            tightened.append(line)

        return "\n".join("> " + line if line else ">" for line in tightened)

    text = _BLOCKQUOTE.sub(quote, text)
    text = _TAG.sub("", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def handle_fold_sections(node, key, value, ctx, path, report):
    """
    x-zenesis-sections holds HTML note blocks. Much of it restates the
    operation description, but a substantial minority carries constraints
    that exist nowhere else -- 204-with-no-body behaviour, permission
    requirements, casing rules.

    Convert each block to Markdown and append it to the operation description,
    skipping any block whose text the operation already covers so re-stating
    does not duplicate.
    """
    target = ctx.operation if ctx.operation is not None else node
    rule = ctx.rule(key)
    fields = rule.get("text_fields", ["value"])
    skip_covered = rule.get("skip_covered", True)

    haystack = reachable_text(target, ctx.root)
    blocks, skipped = [], 0

    for raw in _collect_field_strings(value, fields):
        flat = plain(raw)
        if not flat:
            continue
        if skip_covered and covered_by(flat, haystack):
            skipped += 1
            continue
        markdown = html_to_markdown(raw)
        if markdown and markdown not in blocks:
            blocks.append(markdown)

    if skipped:
        report.hit("%s block already in description, skipped" % key, skipped)

    if not blocks:
        report.hit("%s dropped (fully redundant)" % key)
        return

    heading = rule.get("heading", "Notes")
    body = "\n\n".join(blocks)
    if heading:
        body = "**%s**\n\n%s" % (heading, body)

    target["description"] = ((target.get("description") or "") + "\n\n" + body).strip()
    report.hit("%s folded into description" % key, len(blocks))


def _cell(text):
    """Make a value safe for a single Markdown table cell."""
    return plain(str(text if text is not None else "")).replace("|", "\\|")


def _collect_field_strings(value, fields):
    """
    Strings stored under any of `fields`, at any depth.

    Scoped deliberately: x-zenesis-sections entries look like
    {"type": "editor", "value": "<p>...</p>"}, and only `value` is prose.
    """
    if isinstance(value, dict):
        for key, item in value.items():
            if key in fields and isinstance(item, str):
                yield item
            else:
                yield from _collect_field_strings(item, fields)
    elif isinstance(value, list):
        for item in value:
            yield from _collect_field_strings(item, fields)


HANDLERS = {
    "drop": handle_drop,
    "keep": handle_keep,
    "enum_descriptions": handle_enum_descriptions,
    "fold_status_codes": handle_fold_status_codes,
    "fold_throttles": handle_fold_throttles,
    "fold_sections": handle_fold_sections,
}


# ------------------------------------------------------------------- config

DEFAULT_RULES = {
    "vendor_prefix": "x-zenesis-",
    "unknown_key_policy": "warn",
    "options": {"unswap_examples": True, "emit_enum_varnames": True},
    "rules": {
        "x-zenesis-title": {"action": "drop", "verify": "equals_sibling", "sibling": "summary"},
        "x-zenesis-doc": {"action": "drop"},
        "x-zenesis-usecase-tag": {"action": "drop"},
        "x-zenesis-sections": {
            "action": "fold_sections",
            "heading": "Notes",
            "text_fields": ["value"],
            "skip_covered": True,
        },
        "x-zenesis-enums-desc": {"action": "enum_descriptions"},
        "x-zenesis-statuscodes": {"action": "fold_status_codes", "heading": "Error codes"},
        "x-zenesis-security": {"action": "fold_throttles", "heading": "Rate limit"},
        # Provenance marker inside x-zenesis-sections naming the shared-note key
        # it was copied from. The note text is materialised alongside it, so
        # dropping the marker loses nothing.
        "x-zenesis-shared-note": {"action": "drop"},
        # The shared-note catalogue on $.components. An authoring aid: every
        # note is already inlined at each use site.
        "x-zenesis-shared-notes": {"action": "drop"},
        # Help-site page title on a Tag Object. Renderer navigation, not API
        # semantics.
        "x-zenesis-description-pageName": {"action": "drop"},
    },
}


def load_rules(path=None):
    if path is None:
        return json.loads(json.dumps(DEFAULT_RULES))
    with open(path, encoding="utf-8") as handle:
        config = json.load(handle)

    merged = json.loads(json.dumps(DEFAULT_RULES))
    merged.update({k: v for k, v in config.items() if k not in ("rules", "options")})
    merged["rules"] = config.get("rules", merged["rules"])
    merged["options"].update(config.get("options", {}))

    for key, rule in merged["rules"].items():
        action = rule.get("action")
        if action not in HANDLERS:
            raise ValueError(
                "rule %r uses unknown action %r; valid actions are %s"
                % (key, action, ", ".join(sorted(HANDLERS)))
            )
    if merged.get("unknown_key_policy") not in ("warn", "drop", "keep", "error"):
        raise ValueError(
            "unknown_key_policy must be one of: warn, drop, keep, error"
        )
    return merged
