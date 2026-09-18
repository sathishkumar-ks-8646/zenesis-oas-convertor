"""
Read, write and apply OpenAPI Overlay 1.0.0 documents.

Two directions:

  derive(original, converted)  builds the overlays that turn the converted
                               document back into the original. Because it is
                               a diff, it is complete by construction -- it
                               cannot forget a rule.

  apply(document, overlay)     runs an overlay, per the Overlay 1.0.0 spec:
                               `update` merges, `remove` deletes the target.
"""

from .jsonpath import escape, find, parse

OVERLAY_VERSION = "1.0.0"

MIGRATION_NOTES = {
    "x-zenesis-title": "Identical to `summary`. Make the renderer fall back to it.",
    "x-zenesis-sections": "HTML restatement of `description`. Retire it.",
    "x-zenesis-enums-desc": "Positional array. Read x-enumDescriptions instead.",
    "x-zenesis-doc": "Renderer layout config.",
    "x-zenesis-usecase-tag": "Renderer grouping key.",
    "x-zenesis-statuscodes": "Now a Markdown table in the operation description.",
}


def document(title, actions, version="1.0.0"):
    return {
        "overlay": OVERLAY_VERSION,
        "info": {"title": title, "version": version},
        "actions": actions,
    }


def apply(doc, overlay, report=None, label=""):
    """Apply one overlay in place. Returns (applied, unmatched)."""
    applied = unmatched = 0

    for action in overlay.get("actions", []):
        target = action.get("target")
        if not target:
            unmatched += 1
            continue

        matches = list(find(doc, parse(target)))
        if not matches:
            unmatched += 1
            if report is not None:
                report.warn(target, "%soverlay target matched nothing" % label)
            continue

        if action.get("remove"):
            # Deepest-first, so list indices stay valid while deleting.
            for parent, key, _ in reversed(matches):
                if parent is None:
                    continue
                try:
                    del parent[key]
                    applied += 1
                except (KeyError, IndexError, TypeError):
                    unmatched += 1
        else:
            update = action.get("update", {})
            for _, _, node in matches:
                if isinstance(node, dict):
                    node.update(update)
                    applied += 1
                else:
                    unmatched += 1

    return applied, unmatched


def derive(original, converted, live_keys=()):
    """
    Diff `converted` against `original` and return (live, compat) action lists.

    Keys named in `live_keys` are genuine vendor configuration and go to the
    live overlay. Everything else -- duplicated titles, HTML restatements,
    positional enum arrays, the example field swap -- goes to the compat
    overlay, which exists to be shrunk to nothing.
    """
    live, compat, removes = [], [], []

    def walk(before, after, path):
        if isinstance(before, dict) and isinstance(after, dict):
            restore = {}
            for key, value in before.items():
                if key not in after:
                    restore[key] = value
                elif not isinstance(value, (dict, list)) and value != after[key]:
                    restore[key] = value  # a scalar changed: the example swap
                else:
                    walk(value, after[key], path + escape(key))

            for key, value in restore.items():
                action = {"target": path, "update": {key: value}}
                note = MIGRATION_NOTES.get(key)
                if key in ("summary", "description"):
                    note = "Re-swaps the example fields for the current renderer."
                if note:
                    action["x-migration"] = note
                (live if key in live_keys else compat).append(action)

            for key in after:
                if key not in before:
                    removes.append(
                        {
                            "target": path + escape(key),
                            "remove": True,
                            "x-migration": "Optional. Only needed for byte-identical "
                            "output; the Zenesis renderer ignores unknown keys.",
                        }
                    )

        elif isinstance(before, list) and isinstance(after, list) and len(before) == len(after):
            for index, (b, a) in enumerate(zip(before, after)):
                walk(b, a, "%s[%d]" % (path, index))

    walk(original, converted, "$")
    return live, compat + removes
