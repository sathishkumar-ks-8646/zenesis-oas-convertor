"""Counters and warnings collected during a conversion run."""

import collections


class Report:
    """Accumulates what happened, so the CLI can print it and CI can gate on it."""

    def __init__(self, label=None):
        self.label = label
        self.counts = collections.Counter()
        self.warnings = []

    def hit(self, what, n=1):
        self.counts[what] += n

    def warn(self, where, message):
        self.warnings.append((where, message))

    def merge(self, other, prefix=""):
        self.counts.update(other.counts)
        for where, message in other.warnings:
            self.warnings.append(("%s%s" % (prefix, where), message))

    @property
    def ok(self):
        return not self.warnings

    def render(self, title="CONVERSION REPORT"):
        rule = "=" * 74
        out = ["", rule, title, rule]

        if self.counts:
            width = max(len(k) for k in self.counts)
            for key in sorted(self.counts):
                out.append("  %-*s  %d" % (width, key, self.counts[key]))
        else:
            out.append("  (nothing to do)")

        out.append("")
        if self.warnings:
            out.append("WARNINGS (%d) -- review before publishing:" % len(self.warnings))
            for where, message in self.warnings:
                out.append("  * %s" % message)
                out.append("      at %s" % where)
        else:
            out.append("No warnings.")
        out.append(rule)
        return "\n".join(out)
