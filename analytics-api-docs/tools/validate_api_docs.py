#!/usr/bin/env python3
"""Validate the Zoho Analytics API source export.

Checks the three things a consumer of this repository depends on:
naming (folders and files follow the export convention), completeness
(every domain has markdown, a spec and samples, and every documented group
exists in both), and integrity (the JSON parses, samples point at real
operations, and no unknown vendor extension has appeared).

Standard library only, Python 3.8+. Run from anywhere:

    python3 tools/validate_api_docs.py

Exits 0 when errors=0. Warnings never fail the run on their own; pass
--strict to fail on them too.
"""

import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD_DIR = os.path.join(ROOT, 'md')
OAS_DIR = os.path.join(ROOT, 'zenesis-oas')
SAMPLES_DIR = os.path.join(ROOT, 'zenesis-oas-samples')
COMMON_FILE = os.path.join(ROOT, 'zoho-analytics-api-common.json')

HTTP_METHODS = ('get', 'post', 'put', 'delete', 'patch', 'head', 'options', 'trace')

# The inventory. Nothing is discovered: a file that is not listed here is
# reported as unexpected, and a listed file that is missing is an error.
#
#   (markdown folder, OpenAPI file stem, [(markdown stem, OpenAPI tag), ...])
DOMAINS = [
    ("01 · Organization Management", "org-management", [
        ("ORG_INFO_AND_SETTINGS", "Org Info & Settings"),
    ]),
    ("02 · User & Groups", "user-groups", [
        ("ORG_USERS", "Org Users"),
        ("CUSTOM_ROLES", "Custom Roles"),
        ("WORKSPACE_USERS", "Workspace Users"),
        ("WORKSPACE_GROUPS", "Workspace Groups"),
    ]),
    ("03 · Workspace Management", "workspace-management", [
        ("WORKSPACE_OPERATIONS", "Workspace Operations"),
        ("WORKSPACE_PREFERENCES", "Workspace Preferences"),
        ("WORKSPACE_FOLDERS", "Workspace Folders"),
        ("DOMAIN_AND_WHITE_LABEL", "Domain & White Label"),
    ]),
    ("04 · Data Modeling & Schema", "data-modeling-schema", [
        ("TABLE_AND_SCHEMA", "Table & Schema"),
        ("COLUMNS", "Columns"),
        ("LOOKUPS_AND_RELATIONSHIPS", "Lookups & Relationships"),
        ("QUERY_TABLES", "Query Tables"),
        ("FORMULA_COLUMNS", "Formula Columns"),
        ("AGGREGATE_FORMULAS", "Aggregate Formulas"),
        ("WORKSPACE_VARIABLES", "Workspace Variables"),
    ]),
    ("05 · Data Operations", "data-operations", [
        ("ROW_OPERATIONS", "Row Operations"),
        ("SYNC_DATA_IMPORT", "Data Import (Synchronous)"),
        ("ASYNC_DATA_IMPORT", "Data Import (Asynchronous)"),
        ("SYNC_DATA_EXPORT", "Data Export (Synchronous)"),
        ("ASYNC_DATA_EXPORT", "Data Export (Asynchronous)"),
        ("DATA_SYNC_AND_CONNECTIVITY", "Data Sync & Connectivity"),
    ]),
    ("06 · Views Management", "views-management", [
        ("VIEW_OPERATIONS", "View Operations"),
        ("AUTO_ANALYSIS", "Auto Analysis"),
        ("VIEW_PREFERENCES", "View Preferences"),
        ("TAGS", "Tags"),
        ("TRASH_MANAGEMENT", "Trash Management"),
    ]),
    ("07 · Reports & Dashboards", "reports-dashboards", [
        ("REPORTS", "Reports"),
        ("DASHBOARDS", "Dashboard"),
    ]),
    ("08 · Share & Publish", "share-publish", [
        ("SHARING", "Sharing"),
        ("PUBLISH", "Publish"),
        ("EMBED_URL", "Embed"),
        ("SLIDESHOW_MANAGEMENT", "Slideshow Management"),
    ]),
    ("09 · Schedules & Alerts", "schedules-alerts", [
        ("EMAIL_SCHEDULES", "Email Schedules"),
    ]),
    ("10 · DSML", "dsml", [
        ("AUTOML_ANALYSIS", "AutoML Analysis"),
    ]),
]

# Vendor extensions the converter knows how to handle. Keep in step with
# `rules.json` in zenesis-oas-convertor: a key that appears here but not there
# is dropped silently by the converter, and the reverse is dead configuration.
KNOWN_VENDOR_KEYS = {
    'x-zenesis-title',
    'x-zenesis-doc',
    'x-zenesis-usecase-tag',
    'x-zenesis-sections',
    'x-zenesis-enums-desc',
    'x-zenesis-statuscodes',
    'x-zenesis-security',
    'x-zenesis-shared-note',
    'x-zenesis-shared-notes',
    'x-zenesis-description-pageName',
}

# The error-response model. Every operation carries one success response and
# these two error responses, each a $ref into the shared common file.
SUCCESS_CODES = ('200', '201', '204')
ERROR_CODES = {
    '4XX': '#/components/responses/CommonErrorResponse',
    '500': '#/components/responses/UnexpectedErrorResponse',
}

MD_STEM_RE = re.compile(r'^[A-Z0-9]+(?:_[A-Z0-9]+)*$')
MD_FOLDER_RE = re.compile(r'^(\d{2}) · (.+)$')

errors = []
warnings = []


def error(msg):
    errors.append(msg)
    print('ERROR ' + msg)


def warn(msg):
    warnings.append(msg)
    print('WARN  ' + msg)


def load_json(path):
    try:
        with open(path, encoding='utf-8') as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        error('%s: invalid JSON: %s' % (rel(path), exc))
    except OSError as exc:
        error('%s: cannot read: %s' % (rel(path), exc))
    return None


def rel(path):
    return os.path.relpath(path, ROOT)


def walk_keys(node, found):
    """Collect every `x-` key anywhere in the document."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key.startswith('x-'):
                found.add(key)
            walk_keys(value, found)
    elif isinstance(node, list):
        for value in node:
            walk_keys(value, found)


def check_layout():
    for name, path in (('md', MD_DIR), ('zenesis-oas', OAS_DIR),
                       ('zenesis-oas-samples', SAMPLES_DIR)):
        if not os.path.isdir(path):
            error('missing required directory %s/' % name)
    if not os.path.isfile(COMMON_FILE):
        error('missing zoho-analytics-api-common.json')


def check_markdown():
    """Folder and file naming, and one markdown file per documented group."""
    if not os.path.isdir(MD_DIR):
        return
    present = sorted(d for d in os.listdir(MD_DIR)
                     if os.path.isdir(os.path.join(MD_DIR, d)))
    expected = [d[0] for d in DOMAINS]

    for folder in present:
        match = MD_FOLDER_RE.match(folder)
        if not match:
            error('md/%s: folder name must be "NN · Title" with a middle dot '
                  '(U+00B7)' % folder)
        if folder not in expected:
            error('md/%s: folder is not listed in DOMAINS in '
                  'tools/validate_api_docs.py' % folder)

    for index, (folder, _stem, groups) in enumerate(DOMAINS, start=1):
        path = os.path.join(MD_DIR, folder)
        if not os.path.isdir(path):
            error('md/%s: listed in DOMAINS but not present' % folder)
            continue
        if not folder.startswith('%02d · ' % index):
            error('md/%s: expected prefix "%02d · "; domain folders are '
                  'numbered consecutively from 01' % (folder, index))

        files = sorted(f for f in os.listdir(path) if not f.startswith('.'))
        for name in files:
            if not name.endswith('.md'):
                error('md/%s/%s: only .md files belong here' % (folder, name))
                continue
            stem = name[:-3]
            if not MD_STEM_RE.match(stem):
                error('md/%s/%s: file name must be UPPER_SNAKE_CASE.md'
                      % (folder, name))
            if stem not in [g[0] for g in groups]:
                error('md/%s/%s: group is not listed in DOMAINS in '
                      'tools/validate_api_docs.py' % (folder, name))

        for stem, _tag in groups:
            if stem + '.md' not in files:
                error('md/%s/%s.md: listed in DOMAINS but not present'
                      % (folder, stem))
                continue
            check_markdown_body(os.path.join(path, stem + '.md'))


def check_markdown_body(path):
    with open(path, encoding='utf-8') as fh:
        lines = fh.read().splitlines()
    if not lines or not lines[0].startswith('# '):
        error('%s: must open with a single H1 title line' % rel(path))
    if not any(re.match(r'^## \d+\. ', line) for line in lines):
        warn('%s: no "## N. Title" endpoint section found; the OKF builder '
             'joins endpoints on those headings' % rel(path))


def check_specs():
    """Every domain has a spec and a samples file, and they agree."""
    expected_specs = {stem + '-grouped-api.json' for _f, stem, _g in DOMAINS}
    expected_samples = {stem + '-grouped-api-samples.json'
                        for _f, stem, _g in DOMAINS}

    for directory, expected, suffix in (
            (OAS_DIR, expected_specs, '-grouped-api.json'),
            (SAMPLES_DIR, expected_samples, '-grouped-api-samples.json')):
        if not os.path.isdir(directory):
            continue
        for name in sorted(os.listdir(directory)):
            if name.startswith('.') or name == 'README.md':
                continue
            if not name.endswith(suffix):
                error('%s/%s: file name must end with "%s"'
                      % (os.path.basename(directory), name, suffix))
            elif name not in expected:
                error('%s/%s: domain is not listed in DOMAINS in '
                      'tools/validate_api_docs.py'
                      % (os.path.basename(directory), name))

    total_paths = total_ops = 0
    vendor_keys = set()

    for folder, stem, groups in DOMAINS:
        spec_path = os.path.join(OAS_DIR, stem + '-grouped-api.json')
        samples_path = os.path.join(
            SAMPLES_DIR, stem + '-grouped-api-samples.json')

        if not os.path.isfile(spec_path):
            error('zenesis-oas/%s-grouped-api.json: missing (domain "%s")'
                  % (stem, folder))
            continue
        if not os.path.isfile(samples_path):
            error('zenesis-oas-samples/%s-grouped-api-samples.json: missing '
                  '(domain "%s")' % (stem, folder))

        spec = load_json(spec_path)
        if spec is None:
            continue
        walk_keys(spec, vendor_keys)

        if not str(spec.get('openapi', '')).startswith('3.'):
            error('%s: openapi version must be 3.x, found %r'
                  % (rel(spec_path), spec.get('openapi')))
        if 'info' not in spec or 'paths' not in spec:
            error('%s: an OpenAPI document needs "info" and "paths"'
                  % rel(spec_path))
            continue

        declared_tags = [t.get('name') for t in spec.get('tags', [])]
        for _md_stem, tag in groups:
            if tag not in declared_tags:
                error('%s: tag %r is expected by DOMAINS but is not declared '
                      'in the document' % (rel(spec_path), tag))
        for tag in declared_tags:
            if tag not in [g[1] for g in groups]:
                error('%s: tag %r has no markdown group in md/%s; add the '
                      'document and list it in DOMAINS'
                      % (rel(spec_path), tag, folder))

        operations = {}
        for path, item in spec['paths'].items():
            total_paths += 1
            if not path.startswith('/'):
                error('%s: path %r must start with "/"' % (rel(spec_path), path))
            for method, operation in item.items():
                if method not in HTTP_METHODS:
                    continue
                total_ops += 1
                operations.setdefault(path, set()).add(method)
                title = operation.get('x-zenesis-title') or operation.get('summary')
                if not title:
                    error('%s: %s %s has neither x-zenesis-title nor summary; '
                          'the OKF builder joins endpoints by title'
                          % (rel(spec_path), method.upper(), path))
                elif (operation.get('x-zenesis-title')
                      and operation.get('summary')
                      and operation['x-zenesis-title'].strip()
                      != operation['summary'].strip()):
                    warn('%s: %s %s has x-zenesis-title %r != summary %r; the '
                         'converter drops the title and would lose that text'
                         % (rel(spec_path), method.upper(), path,
                            operation['x-zenesis-title'], operation['summary']))
                for tag in operation.get('tags', []) or []:
                    if tag not in declared_tags:
                        error('%s: %s %s is tagged %r, which the document does '
                              'not declare' % (rel(spec_path), method.upper(),
                                               path, tag))
                if not operation.get('tags'):
                    error('%s: %s %s has no tag, so it belongs to no group'
                          % (rel(spec_path), method.upper(), path))
                check_responses(spec_path, method, path,
                                operation.get('responses', {}))

        samples = load_json(samples_path) if os.path.isfile(samples_path) else None
        if not isinstance(samples, dict):
            if samples is not None:
                error('%s: samples must be an object keyed by path'
                      % rel(samples_path))
            continue
        for path, by_method in samples.items():
            if path not in operations:
                error('%s: samples for %r, which the spec does not define'
                      % (rel(samples_path), path))
                continue
            if not isinstance(by_method, dict):
                error('%s: %r must map a method to its snippets'
                      % (rel(samples_path), path))
                continue
            for method in by_method:
                if method.lower() not in operations[path]:
                    error('%s: samples for %s %s, which the spec does not define'
                          % (rel(samples_path), method.upper(), path))
        for path in operations:
            if path not in samples:
                warn('%s: no SDK samples for %s' % (rel(samples_path), path))

    unknown = sorted(k for k in vendor_keys
                     if k.startswith('x-zenesis-') and k not in KNOWN_VENDOR_KEYS)
    for key in unknown:
        error('%s is used in zenesis-oas/ but has no rule in the converter; '
              'add it to rules.json in zenesis-oas-convertor and to '
              'KNOWN_VENDOR_KEYS here' % key)
    unused = sorted(KNOWN_VENDOR_KEYS - vendor_keys)
    for key in unused:
        warn('%s is declared known but appears in no spec' % key)

    return total_paths, total_ops


def check_responses(spec_path, method, path, responses):
    """Every operation models errors the same way: one success response, a
    `4XX` and a `500` that reference the shared error responses, and no
    `default`. The error-code table (`x-zenesis-statuscodes`) rides on the
    success response, which is where the converter and the OKF builder look."""
    where = '%s: %s %s' % (rel(spec_path), method.upper(), path)
    success = [c for c in SUCCESS_CODES if c in responses]
    if len(success) != 1:
        error('%s must have exactly one success response (%s), found %s'
              % (where, '/'.join(SUCCESS_CODES), success or 'none'))
    if 'default' in responses:
        error('%s uses a "default" response; model errors as "4XX" and "500" '
              'like every other operation' % where)
    for code in ERROR_CODES:
        response = responses.get(code)
        if not isinstance(response, dict):
            error('%s is missing the "%s" error response' % (where, code))
        elif not str(response.get('$ref', '')).endswith(ERROR_CODES[code]):
            error('%s: "%s" must $ref the shared %s, found %r'
                  % (where, code, ERROR_CODES[code].split('/')[-1],
                     response.get('$ref')))
    for code, response in responses.items():
        if (isinstance(response, dict) and 'x-zenesis-statuscodes' in response
                and code not in SUCCESS_CODES):
            error('%s: x-zenesis-statuscodes sits on the "%s" response; it '
                  'belongs on the success response' % (where, code))


def check_common():
    if not os.path.isfile(COMMON_FILE):
        return
    common = load_json(COMMON_FILE)
    if common is None:
        return
    components = common.get('components')
    if not isinstance(components, dict):
        error('zoho-analytics-api-common.json: expected a "components" object')
        return
    schemes = components.get('securitySchemes', {})
    if 'iam-oauth2-schema' not in schemes:
        error('zoho-analytics-api-common.json: securitySchemes must define '
              '"iam-oauth2-schema"; every operation references it')


def check_strays():
    allowed = {
        'md', 'zenesis-oas', 'zenesis-oas-samples', 'tools', '.git', '.github',
        'zoho-analytics-api-common.json', 'README.md', 'CHANGELOG.md',
        'LICENSE.md', 'CLAUDE.md', '.gitignore',
    }
    for name in sorted(os.listdir(ROOT)):
        if name not in allowed and not name.startswith('.'):
            warn('%s: unexpected entry at the repository root; this repository '
                 'holds API source documents only' % name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--strict', action='store_true',
                        help='exit non-zero on warnings as well as errors')
    args = parser.parse_args()

    check_layout()
    check_markdown()
    counts = check_specs()
    check_common()
    check_strays()

    groups = sum(len(d[2]) for d in DOMAINS)
    paths, ops = counts if counts else (0, 0)
    print('domains=%d groups=%d paths=%d operations=%d errors=%d warnings=%d'
          % (len(DOMAINS), groups, paths, ops, len(errors), len(warnings)))
    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
