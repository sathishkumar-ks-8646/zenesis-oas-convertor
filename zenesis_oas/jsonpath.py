"""
A deliberately small JSONPath implementation, sufficient for OpenAPI Overlay
targets and with no third-party dependency.

Supported:
    $                       the document root
    $.paths                 bare-word key
    $.paths['/a/{b}']       quoted key (slashes, braces, hyphens, dots)
    $.oneOf[0]              array index
    $.paths.*               wildcard over dict keys or list items
    $.oneOf[*]              same, bracket form
    $..['x-zenesis-title']  recursive descent, matches at any depth

Not supported: filter expressions ?(), slices [1:3], unions [0,1]. If you need
those, run the overlay through Redocly CLI or Speakeasy CLI -- the documents
this package writes are standard Overlay 1.0.0 and both tools read them as-is.
"""

import re

WILDCARD = object()
DESCEND = object()

_SEGMENT = re.compile(
    r"""
      \.\.                                  # recursive descent
    | \.(?P<bare>[A-Za-z_][A-Za-z0-9_]*)    # .name
    | \.(?P<star>\*)                        # .*
    | \['(?P<quoted>(?:[^'\\]|\\.)*)'\]     # ['any key']
    | \[(?P<index>\d+)\]                    # [0]
    | \[(?P<istar>\*)\]                     # [*]
    """,
    re.VERBOSE,
)


class JSONPathError(ValueError):
    pass


def parse(target):
    """'$.paths.*.get' -> ['paths', WILDCARD, 'get']"""
    if not target.startswith("$"):
        raise JSONPathError("target must start with '$': %r" % target)

    pos, segments = 1, []
    while pos < len(target):
        match = _SEGMENT.match(target, pos)
        if not match:
            raise JSONPathError(
                "cannot parse target at offset %d: %r" % (pos, target)
            )
        if match.group(0) == "..":
            segments.append(DESCEND)
        elif match.group("bare") is not None:
            segments.append(match.group("bare"))
        elif match.group("star") is not None or match.group("istar") is not None:
            segments.append(WILDCARD)
        elif match.group("quoted") is not None:
            segments.append(
                match.group("quoted").replace("\\'", "'").replace("\\\\", "\\")
            )
        else:
            segments.append(int(match.group("index")))
        pos = match.end()
    return segments


def _children(node):
    if isinstance(node, dict):
        return list(node.items())
    if isinstance(node, list):
        return list(enumerate(node))
    return []


def find(document, segments):
    """
    Yield (parent, key, value) for every match.

    `parent` is None only when the whole document matches, which happens for
    the bare target "$". Callers that mutate should skip those.
    """
    if not segments:
        yield None, None, document
        return

    head, rest = segments[0], segments[1:]

    if head is DESCEND:
        # `..` matches here and at every level below.
        seen = set()
        for result in find(document, rest):
            if id(result[2]) not in seen:
                seen.add(id(result[2]))
                yield result
        for _, child in _children(document):
            for result in find(child, segments):
                if id(result[2]) not in seen:
                    seen.add(id(result[2]))
                    yield result
        return

    if head is WILDCARD:
        for key, child in _children(document):
            for parent, k, value in find(child, rest):
                yield (document, key, child) if parent is None else (parent, k, value)
        return

    if isinstance(head, int):
        if not isinstance(document, list) or head >= len(document):
            return
    elif not isinstance(document, dict) or head not in document:
        return

    child = document[head]
    for parent, k, value in find(child, rest):
        yield (document, head, child) if parent is None else (parent, k, value)


def escape(key):
    """Render a dict key as a JSONPath segment, quoting when necessary."""
    if isinstance(key, int):
        return "[%d]" % key
    return "." + key if key.isidentifier() else "['%s']" % key.replace("'", "\\'")
