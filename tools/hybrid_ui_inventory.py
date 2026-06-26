#!/usr/bin/env python3
"""Static inventory for Hybrid AllSky UI routes, templates, and assets.

This script is intentionally read-only for application code.  It does not
import the Flask app, open a database, or require runtime configuration.
It scans files with standard-library regexes and writes a Markdown report.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
FLASK_DIR = REPO_ROOT / "indi_allsky" / "flask"
TEMPLATE_DIR = FLASK_DIR / "templates"
STATIC_DIR = FLASK_DIR / "static"
REPORT_PATH = REPO_ROOT / "HYBRID_UI_INVENTORY_REPORT.md"


ADD_URL_RE = re.compile(r"bp_[A-Za-z0-9_]+\.add_url_rule\(\s*['\"]([^'\"]+)['\"](?P<rest>.*)")
VIEW_RE = re.compile(
    r"view_func\s*=\s*([A-Za-z_][A-Za-z0-9_]*)\.as_view\(\s*['\"]([^'\"]+)['\"](?P<args>[^)]*)\)"
)
TEMPLATE_NAME_RE = re.compile(r"template_name\s*=\s*['\"]([^'\"]+)['\"]")
METHODS_RE = re.compile(r"methods\s*=\s*\[([^\]]+)\]")
ROUTE_DECORATOR_RE = re.compile(r"@bp_[A-Za-z0-9_]+\.route\(\s*['\"]([^'\"]+)['\"](?P<rest>[^)]*)\)")
DEF_RE = re.compile(r"\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")
CLASS_RE = re.compile(r"^class\s+([A-Za-z_][A-Za-z0-9_]*)\(([^)]*)\):")

EXTENDS_RE = re.compile(r"{%\s*extends\s+['\"]([^'\"]+)['\"]\s*%}")
INCLUDE_RE = re.compile(r"{%\s*include\s+['\"]([^'\"]+)['\"]")
STATIC_ASSET_RE = re.compile(
    r"url_for\(\s*['\"]indi_allsky\.static['\"]\s*,\s*filename\s*=\s*['\"]([^'\"]+)['\"]"
)
URL_FOR_ENDPOINT_RE = re.compile(r"url_for\(\s*['\"]indi_allsky\.([^'\"]+)['\"]")
FETCH_LITERAL_RE = re.compile(r"fetch\(\s*['\"]([^'\"]+)['\"]")
AJAX_URL_RE = re.compile(r"url\s*:\s*['\"]([^'\"]+)['\"]")
AXIOS_LITERAL_RE = re.compile(r"axios\.[A-Za-z]+\(\s*['\"]([^'\"]+)['\"]")


@dataclass
class RouteEntry:
    route: str
    methods: list[str]
    endpoint: str
    view: str
    file: str
    line: int
    template: str = ""
    classification: str = "unknown"
    notes: list[str] = field(default_factory=list)


@dataclass
class TemplateEntry:
    name: str
    path: str
    extends: list[str] = field(default_factory=list)
    includes: list[str] = field(default_factory=list)
    included_by: list[str] = field(default_factory=list)
    extended_by: list[str] = field(default_factory=list)
    route_consumers: list[str] = field(default_factory=list)
    js_assets: list[str] = field(default_factory=list)
    css_assets: list[str] = field(default_factory=list)
    endpoint_refs: list[str] = field(default_factory=list)
    api_literals: list[str] = field(default_factory=list)
    classification: str = "unknown"


@dataclass
class AssetEntry:
    name: str
    path: str
    referenced_by_templates: list[str] = field(default_factory=list)
    api_endpoints_called: list[str] = field(default_factory=list)
    classification: str = "unknown"


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def md(value: object) -> str:
    text = str(value) if value is not None else ""
    text = text.replace("|", "\\|").replace("\n", " ")
    return text if text else "-"


def join(values: Iterable[str]) -> str:
    items = [str(v) for v in values if str(v)]
    return ", ".join(sorted(set(items))) if items else "-"


def parse_methods(rest: str) -> list[str]:
    match = METHODS_RE.search(rest)
    if not match:
        return ["GET"]
    methods = re.findall(r"['\"]([^'\"]+)['\"]", match.group(1))
    return sorted(set(methods)) or ["GET"]


def classify_route(route: str, endpoint: str, view: str, template: str) -> str:
    route_l = route.lower()
    endpoint_l = endpoint.lower()
    view_l = view.lower()
    template_l = template.lower()

    if route_l.startswith("/sync/v1") or route_l.startswith("/action"):
        return "external_api"
    if route_l.startswith("/modern-admin"):
        if "safe_controls" in template_l or "safecontrol" in view_l:
            return "modern_wrapper"
        return "modern"
    if route_l.startswith("/ajax") or route_l.startswith("/js") or "ajax" in view_l or "json" in view_l:
        return "shared_api"
    if route in {"/", "/index"} or route_l.startswith("/latest") or route_l.startswith("/images"):
        return "public"
    if "api" in endpoint_l or "json" in endpoint_l:
        return "shared_api"
    return "classic"


def classify_template(name: str) -> str:
    if name.startswith("modern_admin/"):
        return "modern"
    if name in {"base.html", "login.html"} or name.startswith("include/"):
        return "shared_api"
    return "classic"


def classify_asset(name: str, referenced_by: list[str]) -> str:
    if name.startswith("modern_admin/"):
        return "modern"
    if not referenced_by:
        return "unknown"
    classes = {classify_template(t) for t in referenced_by}
    if "modern" in classes and ("classic" in classes or "shared_api" in classes):
        return "shared_api"
    if "modern" in classes:
        return "modern"
    if "classic" in classes:
        return "classic"
    return "unknown"


def parse_routes() -> tuple[list[RouteEntry], dict[str, str], list[str]]:
    routes: list[RouteEntry] = []
    class_bases: dict[str, str] = {}
    warnings: list[str] = []

    if not FLASK_DIR.exists():
        return routes, class_bases, [f"Missing Flask directory: {rel(FLASK_DIR)}"]

    for path in sorted(FLASK_DIR.glob("*.py")):
        text = read_text(path)
        lines = text.splitlines()
        for line_no, line in enumerate(lines, start=1):
            class_match = CLASS_RE.match(line)
            if class_match:
                class_bases[class_match.group(1)] = class_match.group(2)

            add_match = ADD_URL_RE.search(line)
            if add_match:
                route = add_match.group(1)
                rest = add_match.group("rest")
                view_match = VIEW_RE.search(rest)
                view = view_match.group(1) if view_match else ""
                endpoint = view_match.group(2) if view_match else ""
                template_match = TEMPLATE_NAME_RE.search(rest)
                template = template_match.group(1) if template_match else ""
                entry = RouteEntry(
                    route=route,
                    methods=parse_methods(rest),
                    endpoint=endpoint or view or route,
                    view=view or endpoint or "-",
                    file=rel(path),
                    line=line_no,
                    template=template,
                )
                entry.classification = classify_route(entry.route, entry.endpoint, entry.view, entry.template)
                if class_bases.get(view):
                    entry.notes.append(f"bases: {class_bases[view]}")
                routes.append(entry)
                continue

            decorator_match = ROUTE_DECORATOR_RE.search(line)
            if decorator_match:
                route = decorator_match.group(1)
                rest = decorator_match.group("rest")
                endpoint = ""
                for later in lines[line_no: min(line_no + 20, len(lines))]:
                    def_match = DEF_RE.match(later)
                    if def_match:
                        endpoint = def_match.group(1)
                        break
                entry = RouteEntry(
                    route=route,
                    methods=parse_methods(rest),
                    endpoint=endpoint or route,
                    view=endpoint or "-",
                    file=rel(path),
                    line=line_no,
                )
                entry.classification = classify_route(entry.route, entry.endpoint, entry.view, entry.template)
                entry.notes.append("decorator route")
                routes.append(entry)

    return sorted(routes, key=lambda r: (r.route, r.file, r.line)), class_bases, warnings


def parse_templates(routes: list[RouteEntry]) -> tuple[dict[str, TemplateEntry], list[str]]:
    templates: dict[str, TemplateEntry] = {}
    warnings: list[str] = []

    if not TEMPLATE_DIR.exists():
        return templates, [f"Missing template directory: {rel(TEMPLATE_DIR)}"]

    route_by_template: dict[str, list[str]] = defaultdict(list)
    for route in routes:
        if route.template:
            route_by_template[route.template].append(route.route)

    for path in sorted(TEMPLATE_DIR.rglob("*.html")):
        name = path.relative_to(TEMPLATE_DIR).as_posix()
        text = read_text(path)
        entry = TemplateEntry(name=name, path=rel(path), classification=classify_template(name))
        entry.extends = sorted(set(EXTENDS_RE.findall(text)))
        entry.includes = sorted(set(INCLUDE_RE.findall(text)))
        assets = sorted(set(STATIC_ASSET_RE.findall(text)))
        entry.js_assets = [a for a in assets if a.endswith(".js")]
        entry.css_assets = [a for a in assets if a.endswith(".css")]
        entry.endpoint_refs = sorted(set(URL_FOR_ENDPOINT_RE.findall(text)))
        entry.api_literals = sorted(set(extract_api_literals(text)))
        entry.route_consumers = sorted(set(route_by_template.get(name, [])))
        templates[name] = entry

    for template in templates.values():
        for included in template.includes:
            if included in templates:
                templates[included].included_by.append(template.name)
        for extended in template.extends:
            if extended in templates:
                templates[extended].extended_by.append(template.name)

    for template in templates.values():
        template.included_by = sorted(set(template.included_by))
        template.extended_by = sorted(set(template.extended_by))

    return templates, warnings


def extract_api_literals(text: str) -> list[str]:
    endpoints: list[str] = []
    endpoints.extend(FETCH_LITERAL_RE.findall(text))
    endpoints.extend(AXIOS_LITERAL_RE.findall(text))
    for ajax_match in re.finditer(r"\$\.ajax\s*\((?P<body>.*?)\)", text, flags=re.DOTALL):
        endpoints.extend(AJAX_URL_RE.findall(ajax_match.group("body")))
    if "XMLHttpRequest" in text:
        for open_match in re.finditer(r"\.open\(\s*['\"][A-Z]+['\"]\s*,\s*['\"]([^'\"]+)['\"]", text):
            endpoints.append(open_match.group(1))
    return endpoints


def parse_assets(templates: dict[str, TemplateEntry]) -> tuple[dict[str, AssetEntry], dict[str, AssetEntry], list[str]]:
    js_assets: dict[str, AssetEntry] = {}
    css_assets: dict[str, AssetEntry] = {}
    warnings: list[str] = []

    if not STATIC_DIR.exists():
        return js_assets, css_assets, [f"Missing static directory: {rel(STATIC_DIR)}"]

    referenced_js: dict[str, list[str]] = defaultdict(list)
    referenced_css: dict[str, list[str]] = defaultdict(list)
    for template in templates.values():
        for asset in template.js_assets:
            referenced_js[asset].append(template.name)
        for asset in template.css_assets:
            referenced_css[asset].append(template.name)

    for path in sorted(STATIC_DIR.rglob("*.js")):
        name = path.relative_to(STATIC_DIR).as_posix()
        text = read_text(path)
        refs = sorted(set(referenced_js.get(name, [])))
        endpoints = sorted(set(extract_api_literals(text) + URL_FOR_ENDPOINT_RE.findall(text)))
        js_assets[name] = AssetEntry(
            name=name,
            path=rel(path),
            referenced_by_templates=refs,
            api_endpoints_called=endpoints,
            classification=classify_asset(name, refs),
        )

    for path in sorted(STATIC_DIR.rglob("*.css")):
        name = path.relative_to(STATIC_DIR).as_posix()
        refs = sorted(set(referenced_css.get(name, [])))
        css_assets[name] = AssetEntry(
            name=name,
            path=rel(path),
            referenced_by_templates=refs,
            classification=classify_asset(name, refs),
        )

    return js_assets, css_assets, warnings


def build_endpoint_matrix(
    routes: list[RouteEntry],
    templates: dict[str, TemplateEntry],
    js_assets: dict[str, AssetEntry],
) -> dict[str, dict[str, set[str]]]:
    matrix: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    defined = {route.endpoint: route for route in routes}

    for template in templates.values():
        for endpoint in template.endpoint_refs:
            matrix[endpoint]["called_by_templates"].add(template.name)
        for literal in template.api_literals:
            matrix[literal]["called_by_templates"].add(template.name)

    for asset in js_assets.values():
        for endpoint in asset.api_endpoints_called:
            matrix[endpoint]["called_by_js"].add(asset.name)

    for endpoint in defined:
        matrix[endpoint]["defined_by_route"].add(defined[endpoint].route)

    return matrix


def table(headers: list[str], rows: list[list[object]]) -> str:
    lines = [
        "| " + " | ".join(md(h) for h in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(md(cell) for cell in row) + " |")
    return "\n".join(lines)


def render_report(
    routes: list[RouteEntry],
    templates: dict[str, TemplateEntry],
    js_assets: dict[str, AssetEntry],
    css_assets: dict[str, AssetEntry],
    endpoint_matrix: dict[str, dict[str, set[str]]],
    warnings: list[str],
) -> str:
    template_orphans = [
        t for t in templates.values()
        if not t.route_consumers and not t.included_by and not t.extended_by
    ]
    js_orphans = [a for a in js_assets.values() if not a.referenced_by_templates]
    css_orphans = [a for a in css_assets.values() if not a.referenced_by_templates]
    consumed_endpoints = {
        endpoint
        for endpoint, consumers in endpoint_matrix.items()
        if consumers.get("called_by_templates") or consumers.get("called_by_js")
    }
    routes_without_static_consumers = [
        r for r in routes
        if r.endpoint not in consumed_endpoints
    ]

    lines: list[str] = []
    lines.append("# HYBRID UI INVENTORY REPORT")
    lines.append("")
    lines.append("Generated by `tools/hybrid_ui_inventory.py` using static filesystem analysis only.")
    lines.append("")
    lines.append("## 1. Summary")
    lines.append("")
    lines.append(table(
        ["Metric", "Count"],
        [
            ["Routes found", len(routes)],
            ["Templates found", len(templates)],
            ["JavaScript files found", len(js_assets)],
            ["CSS files found", len(css_assets)],
            ["Endpoint/API references found", len(endpoint_matrix)],
            ["Possible template orphan candidates", len(template_orphans)],
            ["Possible JS orphan candidates", len(js_orphans)],
            ["Possible CSS orphan candidates", len(css_orphans)],
            ["Routes/API without static consumers", len(routes_without_static_consumers)],
        ],
    ))
    if warnings:
        lines.append("")
        lines.append("Warnings:")
        for warning in warnings:
            lines.append(f"- {warning}")
    lines.append("")

    lines.append("## 2. Route Inventory")
    lines.append("")
    lines.append(table(
        ["Route", "Methods", "Endpoint/function", "File", "Line", "Template", "Classification", "Notes"],
        [
            [
                r.route,
                join(r.methods),
                f"{r.endpoint} / {r.view}",
                r.file,
                r.line,
                r.template,
                r.classification,
                join(r.notes),
            ]
            for r in routes
        ],
    ))
    lines.append("")

    lines.append("## 3. Template Inventory")
    lines.append("")
    lines.append(table(
        [
            "Template",
            "Path",
            "Extends",
            "Includes",
            "Included by",
            "Route consumer",
            "JS assets",
            "CSS assets",
            "Classification",
            "Orphan candidate",
        ],
        [
            [
                t.name,
                t.path,
                join(t.extends),
                join(t.includes),
                join(t.included_by),
                join(t.route_consumers),
                join(t.js_assets),
                join(t.css_assets),
                t.classification,
                "yes" if t in template_orphans else "no",
            ]
            for t in sorted(templates.values(), key=lambda item: item.name)
        ],
    ))
    lines.append("")

    lines.append("## 4. JavaScript Inventory")
    lines.append("")
    lines.append(table(
        ["JS file", "Path", "Referenced by templates", "API/endpoints called", "Classification", "Orphan candidate"],
        [
            [
                a.name,
                a.path,
                join(a.referenced_by_templates),
                join(a.api_endpoints_called),
                a.classification,
                "yes" if a in js_orphans else "no",
            ]
            for a in sorted(js_assets.values(), key=lambda item: item.name)
        ],
    ))
    lines.append("")

    lines.append("## 5. CSS Inventory")
    lines.append("")
    lines.append(table(
        ["CSS file", "Path", "Referenced by templates", "Classification", "Orphan candidate"],
        [
            [
                a.name,
                a.path,
                join(a.referenced_by_templates),
                a.classification,
                "yes" if a in css_orphans else "no",
            ]
            for a in sorted(css_assets.values(), key=lambda item: item.name)
        ],
    ))
    lines.append("")

    lines.append("## 6. API / Endpoint Consumer Matrix")
    lines.append("")
    defined_routes = {r.endpoint: r for r in routes}
    endpoint_rows: list[list[object]] = []
    for endpoint in sorted(endpoint_matrix):
        consumers = endpoint_matrix[endpoint]
        defined_route = join(consumers.get("defined_by_route", set()))
        route_entry = defined_routes.get(endpoint)
        classification = route_entry.classification if route_entry else "unknown"
        notes = []
        if not route_entry:
            notes.append("not matched to static route definition")
        if not consumers.get("called_by_templates") and not consumers.get("called_by_js"):
            notes.append("no static consumer found")
        endpoint_rows.append([
            endpoint,
            join(consumers.get("called_by_js", set())),
            defined_route,
            classification,
            join(notes),
        ])
    lines.append(table(
        ["Endpoint", "Called by JS", "Defined by route", "Classification", "Notes"],
        endpoint_rows,
    ))
    lines.append("")

    lines.append("## 7. Orphan Candidates")
    lines.append("")
    lines.append("These are static-analysis candidates only. They are not proof that code is unused.")
    lines.append("")
    lines.append("### Template orphan candidates")
    lines.append("")
    lines.append(table(
        ["Template", "Path", "Classification", "Reason"],
        [[t.name, t.path, t.classification, "no route consumer, include, or extends reference found"] for t in template_orphans],
    ))
    lines.append("")
    lines.append("### JavaScript orphan candidates")
    lines.append("")
    lines.append(table(
        ["JS file", "Path", "Classification", "Reason"],
        [[a.name, a.path, a.classification, "no static template reference found"] for a in js_orphans],
    ))
    lines.append("")
    lines.append("### CSS orphan candidates")
    lines.append("")
    lines.append(table(
        ["CSS file", "Path", "Classification", "Reason"],
        [[a.name, a.path, a.classification, "no static template reference found"] for a in css_orphans],
    ))
    lines.append("")
    lines.append("### Routes/API without static consumers")
    lines.append("")
    lines.append(table(
        ["Route", "Endpoint", "Classification", "Note"],
        [
            [
                r.route,
                r.endpoint,
                r.classification,
                "candidate only; page routes may be reached directly or by external users/scripts",
            ]
            for r in routes_without_static_consumers
        ],
    ))
    lines.append("")

    lines.append("## 8. Unknowns")
    lines.append("")
    lines.extend([
        "- Static analysis cannot know whether users bookmark or manually visit a route.",
        "- Static analysis cannot detect API consumers in mobile apps, shell scripts, browser extensions, or external integrations.",
        "- Dynamically constructed `url_for()` endpoint names may not be resolved.",
        "- Dynamically included templates and dynamically loaded assets may be missed.",
        "- Inline JavaScript building endpoint strings at runtime may be partially detected only as literals.",
        "- Blueprint routing behavior and inherited Flask view behavior are inferred, not executed.",
    ])
    lines.append("")

    lines.append("## 9. Recommended Next Step")
    lines.append("")
    lines.append(
        "Use this report as a repeatable baseline, then add a non-invasive route/template "
        "classification allowlist file that records known Classic, Modern, shared API, and "
        "external API ownership. Regenerate the inventory after each UI consolidation "
        "micro-step and compare the diff before removing any legacy surface."
    )
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    routes, _class_bases, route_warnings = parse_routes()
    templates, template_warnings = parse_templates(routes)
    js_assets, css_assets, asset_warnings = parse_assets(templates)
    endpoint_matrix = build_endpoint_matrix(routes, templates, js_assets)
    report = render_report(
        routes,
        templates,
        js_assets,
        css_assets,
        endpoint_matrix,
        route_warnings + template_warnings + asset_warnings,
    )
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Wrote {REPORT_PATH.relative_to(REPO_ROOT)}")
    print(f"routes={len(routes)} templates={len(templates)} js={len(js_assets)} css={len(css_assets)} endpoints={len(endpoint_matrix)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
