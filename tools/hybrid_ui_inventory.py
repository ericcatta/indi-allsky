#!/usr/bin/env python3
"""Static inventory for Hybrid AllSky UI routes, templates, and assets.

This script is intentionally read-only for application code.  It does not
import the Flask app, open a database, or require runtime configuration.
It scans files with standard-library regexes and writes a Markdown report.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
import fnmatch
import json
from pathlib import Path
import re
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
FLASK_DIR = REPO_ROOT / "indi_allsky" / "flask"
TEMPLATE_DIR = FLASK_DIR / "templates"
STATIC_DIR = FLASK_DIR / "static"
REPORT_PATH = REPO_ROOT / "HYBRID_UI_INVENTORY_REPORT.md"
OWNERSHIP_MAP_PATH = REPO_ROOT / "tools" / "hybrid_ui_ownership_map.json"


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


def load_ownership_map() -> tuple[dict, list[str]]:
    if not OWNERSHIP_MAP_PATH.exists():
        return {}, [f"Ownership map not found: {rel(OWNERSHIP_MAP_PATH)}"]

    try:
        data = json.loads(OWNERSHIP_MAP_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [f"Invalid ownership map JSON: {rel(OWNERSHIP_MAP_PATH)} line {exc.lineno}: {exc.msg}"]
    except OSError as exc:
        return {}, [f"Unable to read ownership map {rel(OWNERSHIP_MAP_PATH)}: {exc}"]

    if not isinstance(data, dict) or not isinstance(data.get("owners"), dict):
        return {}, [f"Ownership map has no valid owners object: {rel(OWNERSHIP_MAP_PATH)}"]

    return data, []


def ownership_entries(ownership_map: dict, kind: str) -> list[tuple[str, str]]:
    key = {
        "route": "routes",
        "template": "templates",
        "asset": "assets",
        "api": "apis",
    }[kind]
    entries: list[tuple[str, str]] = []
    for owner, owner_data in ownership_map.get("owners", {}).items():
        if not isinstance(owner_data, dict):
            continue
        for pattern in owner_data.get(key, []) or []:
            entries.append((owner, str(pattern)))
    return entries


def declared_owners(ownership_map: dict, kind: str, value: str) -> list[str]:
    owners = [
        owner
        for owner, pattern in ownership_entries(ownership_map, kind)
        if fnmatch.fnmatchcase(value, pattern)
    ]
    return sorted(set(owners))


def feature_items(ownership_map: dict, kind: str) -> list[tuple[str, str]]:
    key = {
        "route": "routes",
        "template": "templates",
        "asset": "assets",
        "api": "apis",
    }[kind]
    items: list[tuple[str, str]] = []
    for feature_key, feature in ownership_map.get("features", {}).items():
        if not isinstance(feature, dict):
            continue
        for pattern in feature.get(key, []) or []:
            items.append((str(feature_key), str(pattern)))
    return items


def linked_features(ownership_map: dict, kind: str, value: str) -> list[str]:
    features = [
        feature_key
        for feature_key, pattern in feature_items(ownership_map, kind)
        if fnmatch.fnmatchcase(value, pattern)
    ]
    return sorted(set(features))


def ownership_mismatch(classification: str, owners: list[str]) -> str:
    if not owners:
        return "-"
    return "no" if classification in owners else "yes"


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


def declared_ownership_summary_rows(ownership_map: dict) -> list[list[object]]:
    rows: list[list[object]] = []
    for owner, owner_data in ownership_map.get("owners", {}).items():
        if not isinstance(owner_data, dict):
            continue
        rows.append([
            owner,
            len(owner_data.get("routes", []) or []),
            len(owner_data.get("templates", []) or []),
            len(owner_data.get("assets", []) or []),
            len(owner_data.get("apis", []) or []),
            len(owner_data.get("features", []) or []),
        ])
    return rows


def build_ownership_mismatches(
    routes: list[RouteEntry],
    templates: dict[str, TemplateEntry],
    js_assets: dict[str, AssetEntry],
    css_assets: dict[str, AssetEntry],
    endpoint_matrix: dict[str, dict[str, set[str]]],
    endpoint_to_route: dict[str, str],
    ownership_map: dict,
) -> list[list[object]]:
    rows: list[list[object]] = []
    for route in routes:
        owners = declared_owners(ownership_map, "route", route.route)
        if owners and route.classification not in owners:
            rows.append(["route", route.route, route.classification, join(owners), "declared route ownership differs"])

    for template in templates.values():
        owners = declared_owners(ownership_map, "template", template.name)
        if owners and template.classification not in owners:
            rows.append(["template", template.name, template.classification, join(owners), "declared template ownership differs"])

    for asset in sorted({**js_assets, **css_assets}.values(), key=lambda item: item.name):
        owners = declared_owners(ownership_map, "asset", asset.name)
        if owners and asset.classification not in owners:
            rows.append(["asset", asset.name, asset.classification, join(owners), "declared asset ownership differs"])

    defined_routes = {route.endpoint: route for route in routes}
    for endpoint in sorted(endpoint_matrix):
        route = defined_routes.get(endpoint)
        classification = route.classification if route else "unknown"
        owners = declared_owners(ownership_map, "api", endpoint)
        if endpoint_to_route.get(endpoint):
            owners = sorted(set(owners + declared_owners(ownership_map, "api", endpoint_to_route[endpoint])))
        if owners and classification not in owners:
            rows.append(["api", endpoint, classification, join(owners), "declared API ownership differs"])

    return rows


def build_undeclared_items(
    routes: list[RouteEntry],
    templates: dict[str, TemplateEntry],
    js_assets: dict[str, AssetEntry],
    css_assets: dict[str, AssetEntry],
    endpoint_matrix: dict[str, dict[str, set[str]]],
    endpoint_to_route: dict[str, str],
    ownership_map: dict,
) -> list[list[object]]:
    rows: list[list[object]] = []
    for route in routes:
        if not declared_owners(ownership_map, "route", route.route):
            rows.append(["route", route.route, route.classification, "not yet declared in ownership map"])

    for template in sorted(templates.values(), key=lambda item: item.name):
        if not declared_owners(ownership_map, "template", template.name):
            rows.append(["template", template.name, template.classification, "not yet declared in ownership map"])

    for asset in sorted({**js_assets, **css_assets}.values(), key=lambda item: item.name):
        if not declared_owners(ownership_map, "asset", asset.name):
            rows.append(["asset", asset.name, asset.classification, "not yet declared in ownership map"])

    defined_routes = {route.endpoint: route for route in routes}
    for endpoint in sorted(endpoint_matrix):
        route = defined_routes.get(endpoint)
        owners = declared_owners(ownership_map, "api", endpoint)
        if endpoint_to_route.get(endpoint):
            owners = sorted(set(owners + declared_owners(ownership_map, "api", endpoint_to_route[endpoint])))
        if owners:
            continue
        classification = route.classification if route else "unknown"
        rows.append(["api", endpoint, classification, "not yet declared in ownership map"])

    return rows


def build_declared_missing(found_by_kind: dict[str, list[str]], ownership_map: dict) -> list[list[object]]:
    rows: list[list[object]] = []
    for kind in ("route", "template", "asset", "api"):
        found_values = found_by_kind[kind]
        for owner, pattern in ownership_entries(ownership_map, kind):
            if not any(fnmatch.fnmatchcase(value, pattern) for value in found_values):
                rows.append([owner, kind, pattern, "declared pattern did not match static inventory"])
    return rows


def feature_summary(ownership_map: dict) -> dict[str, int]:
    features = ownership_map.get("features", {})
    counts = {
        "total": 0,
        "protected": 0,
        "classic_only": 0,
        "wrapper": 0,
        "shared_public_external": 0,
        "needs_verification": 0,
    }
    for feature in features.values():
        if not isinstance(feature, dict):
            continue
        counts["total"] += 1
        status = str(feature.get("status", "UNKNOWN"))
        owner = str(feature.get("owner", "unknown"))
        if feature.get("protected") is True or status == "PROTECTED MODERN WORK":
            counts["protected"] += 1
        if status == "CLASSIC ONLY":
            counts["classic_only"] += 1
        if status == "WRAPPER ONLY" or owner == "modern_wrapper":
            counts["wrapper"] += 1
        if status in {"SHARED LEGACY", "SHARED ACTIVE", "PUBLIC ACTIVE", "EXTERNAL API"} or owner in {"shared_api", "public", "external_api"}:
            counts["shared_public_external"] += 1
        if status in {"NEEDS VERIFICATION", "UNKNOWN"}:
            counts["needs_verification"] += 1
    return counts


def current_unknown_feature_matches(feature_linkage_counts: list[list[object]]) -> int:
    for row in feature_linkage_counts:
        if row and row[0] == "unknown_needs_verification":
            return int(row[6])
    return 0


def feature_summary_rows(ownership_map: dict) -> list[list[object]]:
    rows: list[list[object]] = []
    for feature_key, feature in sorted(ownership_map.get("features", {}).items()):
        if not isinstance(feature, dict):
            continue
        rows.append([
            feature_key,
            feature.get("label", feature_key),
            feature.get("status", "UNKNOWN"),
            feature.get("owner", "unknown"),
            feature.get("porting_priority", "unknown"),
            "yes" if feature.get("protected") is True else "no",
            len(feature.get("routes", []) or []),
            len(feature.get("templates", []) or []),
            len(feature.get("assets", []) or []),
            len(feature.get("apis", []) or []),
            len(feature.get("config_keys", []) or []),
            feature.get("modern_gap", ""),
            feature.get("removal_risk", ""),
        ])
    return rows


def feature_list_rows(ownership_map: dict, predicate) -> list[list[object]]:
    rows: list[list[object]] = []
    for feature_key, feature in sorted(ownership_map.get("features", {}).items()):
        if not isinstance(feature, dict) or not predicate(feature):
            continue
        rows.append([
            feature_key,
            feature.get("label", feature_key),
            feature.get("status", "UNKNOWN"),
            feature.get("owner", "unknown"),
            feature.get("porting_priority", "unknown"),
            feature.get("modern_gap", ""),
            feature.get("removal_risk", ""),
        ])
    return rows


def build_inventory_without_feature_links(
    routes: list[RouteEntry],
    templates: dict[str, TemplateEntry],
    js_assets: dict[str, AssetEntry],
    css_assets: dict[str, AssetEntry],
    endpoint_matrix: dict[str, dict[str, set[str]]],
    endpoint_to_route: dict[str, str],
    ownership_map: dict,
) -> list[list[object]]:
    rows: list[list[object]] = []
    for route in routes:
        if not linked_features(ownership_map, "route", route.route):
            rows.append(["route", route.route, route.classification, "no feature route pattern matched"])

    for template in sorted(templates.values(), key=lambda item: item.name):
        if not linked_features(ownership_map, "template", template.name):
            rows.append(["template", template.name, template.classification, "no feature template pattern matched"])

    for asset in sorted({**js_assets, **css_assets}.values(), key=lambda item: item.name):
        if not linked_features(ownership_map, "asset", asset.name):
            rows.append(["asset", asset.name, asset.classification, "no feature asset pattern matched"])

    defined_routes = {route.endpoint: route for route in routes}
    for endpoint in sorted(endpoint_matrix):
        route = defined_routes.get(endpoint)
        features = linked_features(ownership_map, "api", endpoint)
        if endpoint_to_route.get(endpoint):
            route_value = endpoint_to_route[endpoint]
            features = sorted(set(
                features
                + linked_features(ownership_map, "api", route_value)
                + linked_features(ownership_map, "route", route_value)
            ))
        if features:
            continue
        classification = route.classification if route else "unknown"
        rows.append(["api", endpoint, classification, "no feature API pattern matched"])

    return rows


def build_feature_linkage_count_rows(
    routes: list[RouteEntry],
    templates: dict[str, TemplateEntry],
    js_assets: dict[str, AssetEntry],
    css_assets: dict[str, AssetEntry],
    endpoint_matrix: dict[str, dict[str, set[str]]],
    endpoint_to_route: dict[str, str],
    ownership_map: dict,
) -> list[list[object]]:
    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for route in routes:
        for feature in linked_features(ownership_map, "route", route.route):
            counts[feature]["routes"] += 1

    for template in templates.values():
        for feature in linked_features(ownership_map, "template", template.name):
            counts[feature]["templates"] += 1

    for asset in {**js_assets, **css_assets}.values():
        for feature in linked_features(ownership_map, "asset", asset.name):
            counts[feature]["assets"] += 1

    defined_routes = {route.endpoint: route for route in routes}
    for endpoint in endpoint_matrix:
        features = linked_features(ownership_map, "api", endpoint)
        if endpoint_to_route.get(endpoint):
            route_value = endpoint_to_route[endpoint]
            features = sorted(set(
                features
                + linked_features(ownership_map, "api", route_value)
                + linked_features(ownership_map, "route", route_value)
            ))
        if endpoint in defined_routes and not features:
            features = linked_features(ownership_map, "route", defined_routes[endpoint].route)
        for feature in features:
            counts[feature]["apis"] += 1

    rows: list[list[object]] = []
    for feature_key, feature in sorted(ownership_map.get("features", {}).items()):
        if not isinstance(feature, dict):
            continue
        route_count = counts[feature_key]["routes"]
        template_count = counts[feature_key]["templates"]
        asset_count = counts[feature_key]["assets"]
        api_count = counts[feature_key]["apis"]
        if route_count + template_count + asset_count + api_count == 0:
            continue
        rows.append([
            feature_key,
            feature.get("label", feature_key),
            route_count,
            template_count,
            asset_count,
            api_count,
            route_count + template_count + asset_count + api_count,
        ])
    rows.sort(key=lambda row: (-int(row[6]), str(row[0])))
    return rows


def render_report(
    routes: list[RouteEntry],
    templates: dict[str, TemplateEntry],
    js_assets: dict[str, AssetEntry],
    css_assets: dict[str, AssetEntry],
    endpoint_matrix: dict[str, dict[str, set[str]]],
    ownership_map: dict,
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
    all_assets = {**js_assets, **css_assets}
    endpoint_to_route = {
        route.endpoint: route.route
        for route in routes
    }
    found_by_kind = {
        "route": sorted({route.route for route in routes}),
        "template": sorted(templates),
        "asset": sorted(all_assets),
        "api": sorted(set(endpoint_matrix) | {route.route for route in routes}),
    }
    feature_counts = feature_summary(ownership_map)
    mismatches = build_ownership_mismatches(routes, templates, js_assets, css_assets, endpoint_matrix, endpoint_to_route, ownership_map)
    undeclared = build_undeclared_items(routes, templates, js_assets, css_assets, endpoint_matrix, endpoint_to_route, ownership_map)
    declared_missing = build_declared_missing(found_by_kind, ownership_map)
    unlinked_inventory = build_inventory_without_feature_links(
        routes,
        templates,
        js_assets,
        css_assets,
        endpoint_matrix,
        endpoint_to_route,
        ownership_map,
    )
    feature_linkage_counts = build_feature_linkage_count_rows(
        routes,
        templates,
        js_assets,
        css_assets,
        endpoint_matrix,
        endpoint_to_route,
        ownership_map,
    )
    unknown_matches = current_unknown_feature_matches(feature_linkage_counts)

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
            ["Ownership mismatches", len(mismatches)],
            ["Undeclared inventory items", len(undeclared)],
            ["Declared but not found", len(declared_missing)],
            ["Previous known inventory items not linked to any feature", 166],
            ["Features mapped", feature_counts["total"]],
            ["Protected features", feature_counts["protected"]],
            ["Classic-only features", feature_counts["classic_only"]],
            ["Wrapper features", feature_counts["wrapper"]],
            ["Shared/public/external features", feature_counts["shared_public_external"]],
            ["Features needing verification", feature_counts["needs_verification"]],
            ["Inventory items not linked to any feature", len(unlinked_inventory)],
            ["Previous known unknown_needs_verification matches", 511],
            ["Current unknown_needs_verification matches", unknown_matches],
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
        [
            "Route",
            "Methods",
            "Endpoint/function",
            "File",
            "Line",
            "Template",
            "Classification",
            "Declared ownership",
            "Mismatch",
            "Notes",
        ],
        [
            [
                r.route,
                join(r.methods),
                f"{r.endpoint} / {r.view}",
                r.file,
                r.line,
                r.template,
                r.classification,
                join(declared_owners(ownership_map, "route", r.route)),
                ownership_mismatch(r.classification, declared_owners(ownership_map, "route", r.route)),
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
            "Declared ownership",
            "Mismatch",
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
                join(declared_owners(ownership_map, "template", t.name)),
                ownership_mismatch(t.classification, declared_owners(ownership_map, "template", t.name)),
                "yes" if t in template_orphans else "no",
            ]
            for t in sorted(templates.values(), key=lambda item: item.name)
        ],
    ))
    lines.append("")

    lines.append("## 4. JavaScript Inventory")
    lines.append("")
    lines.append(table(
        [
            "JS file",
            "Path",
            "Referenced by templates",
            "API/endpoints called",
            "Classification",
            "Declared ownership",
            "Mismatch",
            "Orphan candidate",
        ],
        [
            [
                a.name,
                a.path,
                join(a.referenced_by_templates),
                join(a.api_endpoints_called),
                a.classification,
                join(declared_owners(ownership_map, "asset", a.name)),
                ownership_mismatch(a.classification, declared_owners(ownership_map, "asset", a.name)),
                "yes" if a in js_orphans else "no",
            ]
            for a in sorted(js_assets.values(), key=lambda item: item.name)
        ],
    ))
    lines.append("")

    lines.append("## 5. CSS Inventory")
    lines.append("")
    lines.append(table(
        ["CSS file", "Path", "Referenced by templates", "Classification", "Declared ownership", "Mismatch", "Orphan candidate"],
        [
            [
                a.name,
                a.path,
                join(a.referenced_by_templates),
                a.classification,
                join(declared_owners(ownership_map, "asset", a.name)),
                ownership_mismatch(a.classification, declared_owners(ownership_map, "asset", a.name)),
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
        api_owners = declared_owners(ownership_map, "api", endpoint)
        if route_entry:
            api_owners = sorted(set(api_owners + declared_owners(ownership_map, "api", route_entry.route)))
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
            join(api_owners),
            ownership_mismatch(classification, api_owners),
            join(notes),
        ])
    lines.append(table(
        ["Endpoint", "Called by JS", "Defined by route", "Classification", "Declared ownership", "Mismatch", "Notes"],
        endpoint_rows,
    ))
    lines.append("")

    lines.append("## 6.1 Declared Ownership Summary")
    lines.append("")
    lines.append(table(
        ["Owner", "Routes", "Templates", "Assets", "APIs", "Features"],
        declared_ownership_summary_rows(ownership_map),
    ))
    lines.append("")

    lines.append("## 6.2 Ownership Mismatches")
    lines.append("")
    lines.append("Mismatch means the declared ownership differs from the static inferred classification. It can indicate wrappers, shared usage, or incomplete detection; it is not automatically an error.")
    lines.append("")
    lines.append(table(
        ["Kind", "Item", "Inferred", "Declared", "Note"],
        mismatches,
    ))
    lines.append("")

    lines.append("## 6.3 Undeclared Inventory Items")
    lines.append("")
    lines.append(table(
        ["Kind", "Item", "Inferred classification", "Note"],
        undeclared,
    ))
    lines.append("")

    lines.append("## 6.4 Declared But Not Found")
    lines.append("")
    lines.append(table(
        ["Owner", "Kind", "Pattern", "Note"],
        declared_missing,
    ))
    lines.append("")

    lines.append("## 6.5 Feature Ownership Summary")
    lines.append("")
    lines.append(table(
        ["Metric", "Count"],
        [
            ["Features mapped", feature_counts["total"]],
            ["Protected Modern Work features", feature_counts["protected"]],
            ["Classic-only features", feature_counts["classic_only"]],
            ["Wrapper features", feature_counts["wrapper"]],
            ["Shared/public/external features", feature_counts["shared_public_external"]],
            ["Features needing verification", feature_counts["needs_verification"]],
        ],
    ))
    lines.append("")

    lines.append("## 6.6 Feature Coverage Matrix")
    lines.append("")
    lines.append(table(
        [
            "Feature key",
            "Label",
            "Status",
            "Owner",
            "Priority",
            "Protected",
            "Routes",
            "Templates",
            "Assets",
            "APIs",
            "Config keys",
            "Modern gap",
            "Removal risk",
        ],
        feature_summary_rows(ownership_map),
    ))
    lines.append("")

    lines.append("## 6.7 Protected Modern Work Coverage")
    lines.append("")
    lines.append(table(
        ["Feature key", "Label", "Status", "Owner", "Priority", "Modern gap", "Removal risk"],
        feature_list_rows(ownership_map, lambda feature: feature.get("protected") is True or feature.get("status") == "PROTECTED MODERN WORK"),
    ))
    lines.append("")

    lines.append("## 6.8 Classic-only Feature List")
    lines.append("")
    lines.append(table(
        ["Feature key", "Label", "Status", "Owner", "Priority", "Modern gap", "Removal risk"],
        feature_list_rows(ownership_map, lambda feature: feature.get("status") == "CLASSIC ONLY"),
    ))
    lines.append("")

    lines.append("## 6.9 Wrapper Feature List")
    lines.append("")
    lines.append(table(
        ["Feature key", "Label", "Status", "Owner", "Priority", "Modern gap", "Removal risk"],
        feature_list_rows(ownership_map, lambda feature: feature.get("status") == "WRAPPER ONLY" or feature.get("owner") == "modern_wrapper"),
    ))
    lines.append("")

    lines.append("## 6.10 Features Marked NEEDS VERIFICATION")
    lines.append("")
    lines.append(table(
        ["Feature key", "Label", "Status", "Owner", "Priority", "Modern gap", "Removal risk"],
        feature_list_rows(ownership_map, lambda feature: feature.get("status") in {"NEEDS VERIFICATION", "UNKNOWN"}),
    ))
    lines.append("")

    lines.append("## 6.11 Inventory Items Not Linked To Any Feature")
    lines.append("")
    lines.append("Previous known count before this fine-mapping pass: 166.")
    lines.append("")
    lines.append(table(
        ["Kind", "Item", "Inferred classification", "Note"],
        unlinked_inventory,
    ))
    lines.append("")

    lines.append("## 6.11.1 Unknown Needs Verification Refinement")
    lines.append("")
    lines.append(table(
        ["Metric", "Count"],
        [
            ["Previous known unknown_needs_verification matches", 511],
            ["Current unknown_needs_verification matches", unknown_matches],
        ],
    ))
    lines.append("")
    if unknown_matches:
        lines.append("Remaining unknown items are listed through the `unknown_needs_verification` rows in Feature Linkage Counts.")
    else:
        lines.append("No inventory item currently relies on `unknown_needs_verification` for feature linkage. The feature remains as an explicit future fallback only.")
    lines.append("")
    lines.append("Primary reclassification targets in this pass: Public media endpoints, Direct navigation routes, System Info/Support, Sensors, Camera Profiles/Multi-camera, Image Lag, Bad Pixel/Defect Maps, Classic UI shell, and Dynamically loaded assets.")
    lines.append("")

    lines.append("## 6.12 Feature Linkage Counts")
    lines.append("")
    lines.append("These counts show which feature declarations matched the most inventory items. Items may match more than one feature; broad catch-all categories are intentionally visible here.")
    lines.append("")
    lines.append(table(
        ["Feature key", "Label", "Routes", "Templates", "Assets", "APIs", "Total matches"],
        feature_linkage_counts,
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
    ownership_map, ownership_warnings = load_ownership_map()
    report = render_report(
        routes,
        templates,
        js_assets,
        css_assets,
        endpoint_matrix,
        ownership_map,
        route_warnings + template_warnings + asset_warnings + ownership_warnings,
    )
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Wrote {REPORT_PATH.relative_to(REPO_ROOT)}")
    print(f"routes={len(routes)} templates={len(templates)} js={len(js_assets)} css={len(css_assets)} endpoints={len(endpoint_matrix)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
