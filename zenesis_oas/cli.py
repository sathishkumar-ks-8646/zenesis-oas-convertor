"""
zenesis-oas -- convert Zenesis-flavoured OpenAPI documents to clean OpenAPI 3.x.

    zenesis-oas inventory analytics-api-docs/zenesis-oas/
    zenesis-oas convert   analytics-api-docs/zenesis-oas/ dist/
    zenesis-oas overlay   analytics-api-docs/zenesis-oas/ --out overlays/
    zenesis-oas verify    analytics-api-docs/zenesis-oas/ --overlays overlays/

Exit codes:  0 success  |  1 warnings or verification failure  |  2 usage error
"""

import argparse
import json
import pathlib
import sys

from . import overlay as overlaymod
from . import rules as rulesmod
from .converter import convert, inventory
from .report import Report

LIVE_KEYS = ("x-zenesis-usecase-tag", "x-zenesis-doc")


# --------------------------------------------------------------------- io

def read_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path, payload, indent=2):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=indent, ensure_ascii=False)
        handle.write("\n")


def collect(source):
    """Resolve a file or directory argument to a sorted list of .json paths."""
    src = pathlib.Path(source)
    if src.is_dir():
        return sorted(src.glob("*.json"))
    if src.is_file():
        return [src]
    raise FileNotFoundError("no such file or directory: %s" % source)


def note(*parts):
    print(*parts, file=sys.stderr)


# --------------------------------------------------------------- commands

def cmd_inventory(args):
    """List every vendor extension across the input specs, before converting."""
    config = rulesmod.load_rules(args.rules)
    prefix = config.get("vendor_prefix", "x-zenesis-")
    known = set(config["rules"])

    totals, examples, unknown = {}, {}, set()

    for path in collect(args.source):
        found = inventory(read_json(path), prefix)
        for key, info in found.items():
            totals[key] = totals.get(key, 0) + info["count"]
            examples.setdefault(key, "%s  %s" % (path.name, info["example"]))
            if key not in known:
                unknown.add(key)

    if not totals:
        note("No %s* extensions found." % prefix)
        return 0

    width = max(len(k) for k in totals)
    note("")
    note("VENDOR EXTENSIONS FOUND")
    note("-" * 74)
    for key in sorted(totals, key=lambda k: -totals[key]):
        flag = "  <-- NOT IN rules.json" if key in unknown else ""
        note("  %-*s  %4d%s" % (width, key, totals[key], flag))
        note("      e.g. %s" % examples[key])
    note("-" * 74)

    if unknown:
        note("")
        note("%d key(s) have no rule. Add them to rules.json before converting,"
             % len(unknown))
        note("or they will be dropped with a warning.")
        return 1
    note("")
    note("Every key has a rule. Safe to convert.")
    return 0


def cmd_convert(args):
    config = rulesmod.load_rules(args.rules)
    sources = collect(args.source)
    dest = pathlib.Path(args.dest)
    many = len(sources) > 1 or pathlib.Path(args.source).is_dir()

    total, failures = Report(), 0

    for path in sources:
        doc, report = convert(read_json(path), config, label=path.name)
        out = dest / path.name if many else dest
        write_json(out, doc, args.indent)

        total.merge(report, prefix="%s  " % path.name)
        if report.warnings:
            failures += 1
        if many and not args.quiet:
            state = ("%d warning(s)" % len(report.warnings)) if report.warnings else "clean"
            note("  %-46s -> %-28s %s" % (path.name, out.name, state))

    if not args.quiet:
        note(total.render())
    if failures and not args.quiet:
        note("")
        note("%d of %d file(s) produced warnings." % (failures, len(sources)))
    return 1 if failures else 0


def cmd_overlay(args):
    """Regenerate the overlays that turn converted output back into the source."""
    config = rulesmod.load_rules(args.rules)
    out_dir = pathlib.Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    for path in collect(args.source):
        original = read_json(path)
        converted, _ = convert(original, config, label=path.name)

        live, compat = overlaymod.derive(original, converted, LIVE_KEYS)
        stem = path.stem

        write_json(
            out_dir / ("%s.live.overlay.json" % stem),
            overlaymod.document("Zenesis renderer configuration - %s" % stem, live),
        )
        write_json(
            out_dir / ("%s.compat.overlay.json" % stem),
            overlaymod.document(
                "Zenesis legacy compatibility - %s - shrink this to zero" % stem, compat
            ),
        )
        note("  %-46s live=%-5d compat=%d" % (path.name, len(live), len(compat)))
    return 0


def cmd_verify(args):
    """
    Prove the conversion is lossless: converted + live + compat == original.

    Any difference means the converter silently changed something the overlays
    do not account for, which is the one failure mode worth blocking a release.
    """
    config = rulesmod.load_rules(args.rules)
    overlays = pathlib.Path(args.overlays) if args.overlays else None
    failures = 0

    for path in collect(args.source):
        original = read_json(path)
        converted, report = convert(original, config, label=path.name)

        if overlays and overlays.is_dir():
            live_doc = read_json(overlays / ("%s.live.overlay.json" % path.stem))
            compat_doc = read_json(overlays / ("%s.compat.overlay.json" % path.stem))
            stale = "committed"
        else:
            live, compat = overlaymod.derive(original, converted, LIVE_KEYS)
            live_doc = overlaymod.document("live", live)
            compat_doc = overlaymod.document("compat", compat)
            stale = "derived"

        overlaymod.apply(converted, live_doc)
        overlaymod.apply(converted, compat_doc)

        if converted == original:
            note("  %-46s OK   round trip lossless (%s overlays)" % (path.name, stale))
        else:
            note("  %-46s FAIL round trip lost data" % path.name)
            failures += 1

        if report.warnings and not args.allow_warnings:
            note("  %-46s FAIL %d conversion warning(s)"
                 % ("", len(report.warnings)))
            for where, message in report.warnings:
                note("        * %s" % message)
                note("            at %s" % where)
            failures += 1

    if failures:
        note("")
        note("VERIFY FAILED (%d problem(s))." % failures)
        return 1
    note("")
    note("VERIFY PASSED.")
    return 0


# -------------------------------------------------------------------- main

def build_parser():
    parser = argparse.ArgumentParser(
        prog="zenesis-oas",
        description="Convert Zenesis-flavoured OpenAPI documents to clean OpenAPI 3.x.",
    )
    parser.add_argument("--rules", metavar="FILE",
                        help="rules.json (defaults to the built-in rules)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("inventory", help="list vendor extensions without converting")
    p.add_argument("source", help="a .json spec or a directory of them")
    p.set_defaults(func=cmd_inventory)

    p = sub.add_parser("convert", help="write clean OpenAPI to the destination")
    p.add_argument("source")
    p.add_argument("dest")
    p.add_argument("--indent", type=int, default=2)
    p.add_argument("--quiet", action="store_true")
    p.set_defaults(func=cmd_convert)

    p = sub.add_parser("overlay", help="regenerate the Overlay 1.0.0 documents")
    p.add_argument("source")
    p.add_argument("dest", nargs="?", help="unused; accepted for symmetry")
    p.add_argument("--out", default="overlays")
    p.set_defaults(func=cmd_overlay)

    p = sub.add_parser("verify", help="prove the conversion loses nothing")
    p.add_argument("source")
    p.add_argument("dest", nargs="?", help="unused; accepted for symmetry")
    p.add_argument("--overlays", help="directory of committed overlays to check against")
    p.add_argument("--allow-warnings", action="store_true",
                   help="do not fail on conversion warnings")
    p.set_defaults(func=cmd_verify)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except FileNotFoundError as error:
        note("error: %s" % error)
        return 2
    except ValueError as error:
        note("error: %s" % error)
        return 2


if __name__ == "__main__":
    sys.exit(main())
