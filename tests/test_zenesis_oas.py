"""
Test suite. Standard library only -- run with:

    python -m unittest discover -s tests -v
"""

import copy
import json
import pathlib
import unittest

from zenesis_oas import jsonpath, overlay, rules
from zenesis_oas.converter import convert, inventory

SPECS = (pathlib.Path(__file__).resolve().parent.parent
         / "analytics-api-docs" / "zenesis-oas")
LIVE_KEYS = ("x-zenesis-usecase-tag", "x-zenesis-doc")


def minimal(**operation):
    doc = {
        "openapi": "3.1.0",
        "info": {"title": "t", "version": "1"},
        "paths": {"/thing": {"get": dict({"responses": {}}, **operation)}},
    }
    return doc


def the_operation(doc):
    return doc["paths"]["/thing"]["get"]


def doc_tags(doc):
    return json.dumps(doc.get("tags", []))


# --------------------------------------------------------------- jsonpath

class TestJSONPath(unittest.TestCase):
    def setUp(self):
        self.doc = {
            "paths": {"/a": {"get": {"x-t": 1}}, "/b": {"post": {"x-t": 2}}},
            "list": [{"n": 0}, {"n": 1}],
        }

    def test_quoted_key(self):
        found = list(jsonpath.find(self.doc, jsonpath.parse("$.paths['/a'].get")))
        self.assertEqual(found[0][2], {"x-t": 1})

    def test_array_index(self):
        found = list(jsonpath.find(self.doc, jsonpath.parse("$.list[1]")))
        self.assertEqual(found[0][2], {"n": 1})

    def test_wildcard(self):
        found = list(jsonpath.find(self.doc, jsonpath.parse("$.paths.*")))
        self.assertEqual(len(found), 2)

    def test_recursive_descent_finds_every_depth(self):
        found = list(jsonpath.find(self.doc, jsonpath.parse("$..['x-t']")))
        self.assertEqual(sorted(m[2] for m in found), [1, 2])

    def test_no_match_is_empty_not_error(self):
        self.assertEqual(list(jsonpath.find(self.doc, jsonpath.parse("$.nope.deep"))), [])

    def test_bad_target_raises(self):
        with self.assertRaises(jsonpath.JSONPathError):
            jsonpath.parse("paths.get")

    def test_escape_round_trips_awkward_keys(self):
        for key in ("simple", "/restapi/v2/{id}", "x-zenesis-title", "with.dot"):
            doc = {key: "value"}
            target = "$" + jsonpath.escape(key)
            found = list(jsonpath.find(doc, jsonpath.parse(target)))
            self.assertEqual(found[0][2], "value", key)


# ---------------------------------------------------------------- handlers

class TestRules(unittest.TestCase):
    def test_title_identical_to_summary_is_dropped_silently(self):
        doc = minimal(summary="Add a row", **{"x-zenesis-title": "Add a row"})
        out, report = convert(doc)
        self.assertNotIn("x-zenesis-title", the_operation(out))
        self.assertTrue(report.ok, report.warnings)

    def test_title_differing_from_summary_warns(self):
        doc = minimal(summary="Add a row", **{"x-zenesis-title": "Something else"})
        _, report = convert(doc)
        self.assertFalse(report.ok)
        self.assertIn("being lost", report.warnings[0][1])

    def test_string_enum_becomes_keyed_map(self):
        doc = minimal()
        the_operation(doc)["responses"] = {
            "200": {"description": "d", "content": {"application/json": {"schema": {
                "type": "string",
                "enum": ["PLAIN", "EMAIL"],
                "x-zenesis-enums-desc": ["Plain text", "Email address"],
            }}}}
        }
        out, _ = convert(doc)
        schema = out["paths"]["/thing"]["get"]["responses"]["200"]["content"][
            "application/json"]["schema"]
        self.assertEqual(schema["x-enumDescriptions"],
                         {"PLAIN": "Plain text", "EMAIL": "Email address"})
        self.assertNotIn("x-enum-varnames", schema)

    def test_integer_enum_also_gets_varnames(self):
        doc = minimal()
        the_operation(doc)["responses"] = {"200": {"description": "d", "content": {
            "application/json": {"schema": {
                "type": "integer",
                "enum": [0, 1],
                "x-zenesis-enums-desc": ["COMMA", "TAB"],
            }}}}}
        out, _ = convert(doc)
        schema = out["paths"]["/thing"]["get"]["responses"]["200"]["content"][
            "application/json"]["schema"]
        self.assertEqual(schema["x-enumDescriptions"], {"0": "COMMA", "1": "TAB"})
        self.assertEqual(schema["x-enum-varnames"], ["COMMA", "TAB"])

    def test_misaligned_enum_is_dropped_with_a_warning_not_guessed(self):
        doc = minimal()
        the_operation(doc)["responses"] = {"200": {"description": "d", "content": {
            "application/json": {"schema": {
                "enum": ["A", "B", "C"],
                "x-zenesis-enums-desc": ["only", "two"],
            }}}}}
        out, report = convert(doc)
        schema = out["paths"]["/thing"]["get"]["responses"]["200"]["content"][
            "application/json"]["schema"]
        self.assertNotIn("x-enumDescriptions", schema)
        self.assertFalse(report.ok)
        self.assertIn("alignment is broken", report.warnings[0][1])

    def test_examples_are_unswapped(self):
        doc = minimal()
        the_operation(doc)["requestBody"] = {"content": {"application/json": {"examples": {
            "one": {"summary": "A long sentence describing the example.",
                    "description": "Short label"}
        }}}}
        out, _ = convert(doc)
        example = out["paths"]["/thing"]["get"]["requestBody"]["content"][
            "application/json"]["examples"]["one"]
        self.assertEqual(example["summary"], "Short label")
        self.assertTrue(example["description"].startswith("A long sentence"))

    def test_already_correct_example_is_left_alone_and_flagged(self):
        doc = minimal()
        the_operation(doc)["requestBody"] = {"content": {"application/json": {"examples": {
            "one": {"summary": "Short", "description": "A much longer description here."}
        }}}}
        out, report = convert(doc)
        example = out["paths"]["/thing"]["get"]["requestBody"]["content"][
            "application/json"]["examples"]["one"]
        self.assertEqual(example["summary"], "Short")
        self.assertFalse(report.ok)

    def test_status_codes_fold_into_the_operation_not_the_response(self):
        doc = minimal(description="Does a thing.")
        the_operation(doc)["responses"] = {"200": {
            "description": "Successful response",
            "x-zenesis-statuscodes": [
                {"name": "8535", "description": "Bad token.", "resolution": "Refresh it."}
            ],
        }}
        out, report = convert(doc)
        operation = the_operation(out)
        self.assertIn("| 8535 |", operation["description"])
        self.assertIn("Error codes", operation["description"])
        self.assertEqual(operation["responses"]["200"]["description"],
                         "Successful response")
        self.assertTrue(report.ok, report.warnings)

    def test_pipe_in_status_code_text_is_escaped(self):
        doc = minimal(description="d")
        the_operation(doc)["responses"] = {"200": {"description": "ok",
            "x-zenesis-statuscodes": [{"name": "1", "description": "a | b",
                                       "resolution": "c"}]}}
        out, _ = convert(doc)
        self.assertIn("a \\| b", the_operation(out)["description"])

    def test_throttles_fold_into_the_operation(self):
        doc = minimal(description="Creates a thing.")
        the_operation(doc)["x-zenesis-security"] = {
            "throttles": [{"duration": 60, "threshold": 7, "lock-period": 300}]
        }
        out, report = convert(doc)
        description = the_operation(out)["description"]
        self.assertIn("Rate limit", description)
        self.assertIn("Up to 7 requests per 60 seconds", description)
        self.assertIn("blocks further calls for 300 seconds", description)
        self.assertTrue(report.ok, report.warnings)

    def test_throttle_singular_grammar(self):
        doc = minimal(description="d")
        the_operation(doc)["x-zenesis-security"] = {
            "throttles": [{"duration": 1, "threshold": 1}]
        }
        out, _ = convert(doc)
        self.assertIn("Up to 1 request per 1 second.",
                      the_operation(out)["description"])

    def test_unknown_key_beside_throttles_warns(self):
        doc = minimal(description="d")
        the_operation(doc)["x-zenesis-security"] = {
            "throttles": [{"duration": 60, "threshold": 5}],
            "ipAllowlist": ["10.0.0.1"],
        }
        _, report = convert(doc)
        self.assertFalse(report.ok)
        self.assertIn("ipAllowlist", report.warnings[0][1])

    def test_sections_with_new_prose_are_folded_in(self):
        doc = minimal(description="Deletes a column.")
        the_operation(doc)["x-zenesis-sections"] = {
            "apiInfo": {"1": {"type": "editor", "value":
                "<blockquote>Note:<br><span>Returns HTTP 204 with no body.</span></blockquote>"}}
        }
        out, report = convert(doc)
        description = the_operation(out)["description"]
        self.assertIn("Returns HTTP 204 with no body.", description)
        self.assertIn("> ", description)
        self.assertTrue(report.ok, report.warnings)

    def test_sections_already_covered_are_not_duplicated(self):
        prose = ("This endpoint returns HTTP 204 with no response body "
                 "whenever the deletion succeeds.")
        doc = minimal(description=prose)
        the_operation(doc)["x-zenesis-sections"] = {
            "apiInfo": {"1": {"type": "editor", "value": "<p>%s</p>" % prose}}
        }
        out, report = convert(doc)
        self.assertEqual(the_operation(out)["description"], prose)
        self.assertTrue(report.ok, report.warnings)

    def test_shared_note_marker_is_dropped_but_its_text_survives(self):
        doc = minimal(description="Creates a report.")
        the_operation(doc)["x-zenesis-sections"] = {
            "apiRequest": {"1": {
                "type": "editor",
                "x-zenesis-shared-note": "orgIdHeader",
                "value": "<blockquote>The ZANALYTICS-ORGID header is mandatory."
                         "</blockquote>",
            }}
        }
        out, _ = convert(doc)
        description = the_operation(out)["description"]
        self.assertIn("ZANALYTICS-ORGID header is mandatory", description)
        self.assertNotIn("x-zenesis-shared-note", json.dumps(out))

    def test_page_name_on_a_tag_is_dropped(self):
        doc = minimal()
        doc["tags"] = [{"name": "Reports", "description": "d",
                        "x-zenesis-description-pageName": "Reports Overview"}]
        out, report = convert(doc)
        self.assertNotIn("x-zenesis-description-pageName", doc_tags(out))
        self.assertTrue(report.ok, report.warnings)

    def test_html_to_markdown_vocabulary(self):
        from zenesis_oas.rules import html_to_markdown
        self.assertEqual(html_to_markdown("<b>bold</b>"), "**bold**")
        self.assertEqual(html_to_markdown("<code>x</code>"), "`x`")
        self.assertEqual(html_to_markdown("a<br>b"), "a\nb")
        self.assertEqual(html_to_markdown("<ul><li>one</li><li>two</li></ul>"),
                         "- one\n- two")
        self.assertEqual(html_to_markdown("<blockquote>hi</blockquote>"), "> hi")
        self.assertEqual(html_to_markdown("a &amp; b"), "a & b")

    def test_unknown_vendor_key_warns_and_drops(self):
        doc = minimal(**{"x-zenesis-brand-new": True})
        out, report = convert(doc)
        self.assertNotIn("x-zenesis-brand-new", the_operation(out))
        self.assertFalse(report.ok)
        self.assertIn("unrecognised vendor key", report.warnings[0][1])

    def test_unknown_key_policy_keep(self):
        config = rules.load_rules()
        config["unknown_key_policy"] = "keep"
        doc = minimal(**{"x-zenesis-brand-new": True})
        out, report = convert(doc, config)
        self.assertIn("x-zenesis-brand-new", the_operation(out))
        self.assertTrue(report.ok)

    def test_keep_action_retains_the_key(self):
        config = rules.load_rules()
        config["rules"]["x-zenesis-usecase-tag"] = {"action": "keep"}
        doc = minimal(**{"x-zenesis-usecase-tag": "csv"})
        out, _ = convert(doc, config)
        self.assertEqual(the_operation(out)["x-zenesis-usecase-tag"], "csv")

    def test_non_openapi_3_is_refused(self):
        _, report = convert({"swagger": "2.0"})
        self.assertFalse(report.ok)
        self.assertIn("not 3.x", report.warnings[0][1])

    def test_input_document_is_not_mutated(self):
        doc = minimal(summary="s", **{"x-zenesis-title": "s"})
        before = copy.deepcopy(doc)
        convert(doc)
        self.assertEqual(doc, before)

    def test_bad_action_name_is_rejected_at_load(self):
        path = pathlib.Path("/tmp/bad-rules.json")
        path.write_text(json.dumps({"rules": {"x-zenesis-x": {"action": "nope"}}}))
        with self.assertRaises(ValueError):
            rules.load_rules(str(path))


# ------------------------------------------------------ real specs, if present

@unittest.skipUnless(SPECS.is_dir() and any(SPECS.glob("*.json")),
                     "analytics-api-docs submodule not initialised (run: make sources)")
class TestRealSpecs(unittest.TestCase):
    def specs(self):
        return sorted(SPECS.glob("*.json"))

    def test_no_vendor_keys_survive(self):
        for path in self.specs():
            with self.subTest(spec=path.name):
                out, _ = convert(json.loads(path.read_text(encoding="utf-8")))
                self.assertEqual(inventory(out), {})

    def test_round_trip_is_lossless(self):
        for path in self.specs():
            with self.subTest(spec=path.name):
                original = json.loads(path.read_text(encoding="utf-8"))
                converted, _ = convert(original)
                live, compat = overlay.derive(original, converted, LIVE_KEYS)
                overlay.apply(converted, overlay.document("live", live))
                overlay.apply(converted, overlay.document("compat", compat))
                self.assertEqual(converted, original)

    def test_output_is_still_openapi_3(self):
        for path in self.specs():
            with self.subTest(spec=path.name):
                out, _ = convert(json.loads(path.read_text(encoding="utf-8")))
                self.assertTrue(out["openapi"].startswith("3."))
                self.assertIn("paths", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
