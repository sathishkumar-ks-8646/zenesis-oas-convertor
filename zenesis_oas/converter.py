"""Walk an OpenAPI document and apply the configured vendor-extension rules."""

import copy

from . import rules as rulesmod
from .jsonpath import escape
from .report import Report

HTTP_METHODS = {
    "get", "put", "post", "delete", "options", "head", "patch", "trace",
}


class ConversionContext:
    """Everything a handler needs beyond the node it is editing."""

    def __init__(self, root, config):
        self.root = root
        self.config = config
        self.options = config.get("options", {})
        self.operation = None

    def rule(self, key):
        return self.config["rules"].get(key, {})


def convert(document, config=None, label=None, in_place=False):
    """
    Convert a Zenesis-flavoured OpenAPI document to clean OpenAPI 3.x.

    Returns (converted_document, Report). The input is copied unless
    `in_place` is true.
    """
    config = config or rulesmod.load_rules()
    doc = document if in_place else copy.deepcopy(document)

    report = Report(label)
    version = doc.get("openapi", "")
    if not isinstance(version, str) or not version.startswith("3."):
        report.warn(
            "$.openapi",
            "`openapi` is %r, not 3.x -- refusing to convert"
            % (version or "<missing>"),
        )
        return doc, report

    ctx = ConversionContext(doc, config)
    _walk(doc, "$", ctx, report)
    return doc, report


def _child_kind(kind, key):
    """
    Track where we are in the OpenAPI structure:

        root  --"paths"-->  paths  --URL-->  pathitem  --"get"-->  operation

    Anything else is "other". Knowing the enclosing operation matters because
    handlers such as fold_status_codes need to write to it, not to whichever
    nested object happened to carry the extension.
    """
    if kind == "root" and key == "paths":
        return "paths"
    if kind == "paths":
        return "pathitem"
    if kind == "pathitem" and key in HTTP_METHODS:
        return "operation"
    return "other"


def _walk(node, path, ctx, report, kind="root", key_from_parent=None):
    if isinstance(node, dict):
        previous_operation = ctx.operation
        if kind == "operation":
            ctx.operation = node

        _apply_rules(node, path, ctx, report)

        if ctx.options.get("unswap_examples", True) and key_from_parent == "examples":
            _unswap(node, path, report)

        for key, value in list(node.items()):
            _walk(
                value,
                path + escape(key),
                ctx,
                report,
                kind=_child_kind(kind, key),
                key_from_parent=key,
            )

        ctx.operation = previous_operation

    elif isinstance(node, list):
        for index, value in enumerate(node):
            _walk(value, "%s[%d]" % (path, index), ctx, report,
                  kind="other", key_from_parent=key_from_parent)


def _apply_rules(node, path, ctx, report):
    prefix = ctx.config.get("vendor_prefix", "x-zenesis-")
    policy = ctx.config.get("unknown_key_policy", "warn")

    for key in [k for k in node if isinstance(k, str) and k.startswith(prefix)]:
        rule = ctx.config["rules"].get(key)

        if rule is None:
            if policy == "keep":
                report.hit("%s kept (unknown key, policy=keep)" % key)
                continue
            if policy == "error":
                raise ValueError(
                    "unknown vendor key %r at %s (unknown_key_policy=error)"
                    % (key, path)
                )
            if policy == "warn":
                report.warn(
                    path,
                    "unrecognised vendor key %r -- dropped. Add it to rules.json "
                    "to choose how it is handled." % key,
                )
            node.pop(key)
            report.hit("%s dropped (unknown key)" % key)
            continue

        value = node.pop(key)
        rulesmod.HANDLERS[rule["action"]](node, key, value, ctx, path, report)


def _unswap(examples, path, report):
    """
    Zenesis stores the short label in `description` and the long prose in
    `summary`, which is the reverse of the OpenAPI Example Object. Swap them
    back, but only where the length heuristic agrees -- otherwise warn and
    leave the example alone.
    """
    for name, example in examples.items():
        if not isinstance(example, dict):
            continue
        summary, description = example.get("summary"), example.get("description")
        if not (isinstance(summary, str) and isinstance(description, str)):
            continue
        if len(summary) <= len(description):
            report.warn(
                path + escape(name),
                "`summary` is not longer than `description`; this example may "
                "already follow spec semantics, so it was left untouched",
            )
            continue
        example["summary"], example["description"] = description, summary
        report.hit("example summary/description un-swapped")


def inventory(document, prefix="x-zenesis-"):
    """Count every vendor extension in a document, with one example location."""
    found = {}

    def walk(node, path):
        if isinstance(node, dict):
            for key, value in node.items():
                if isinstance(key, str) and key.startswith(prefix):
                    entry = found.setdefault(key, {"count": 0, "example": path})
                    entry["count"] += 1
                walk(value, path + escape(key))
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, "%s[%d]" % (path, index))

    walk(document, "$")
    return found
