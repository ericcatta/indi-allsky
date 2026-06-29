#!/usr/bin/env python3
"""Generate a read-only inventory report for Hybrid settings ownership.

This script intentionally does not import application runtime code, Flask,
database models, or configuration modules.  It validates the machine-readable
settings ownership map and writes a Markdown report for review.
"""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
MAP_PATH = REPO_ROOT / "tools" / "hybrid_settings_ownership_map.json"
REPORT_PATH = REPO_ROOT / "HYBRID_SETTINGS_INVENTORY_REPORT.md"

REQUIRED_GROUP_FIELDS = (
    "owner",
    "level",
    "status",
    "current_surfaces",
    "risk",
    "do_not_move_yet",
    "notes",
)

PREVIEW_STATUSES = {"dedicated_read_only", "final_read_only"}


class SettingsInventoryError(Exception):
    """Raised when the settings ownership map is invalid."""


def load_map(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SettingsInventoryError(f"Settings ownership map not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SettingsInventoryError(
            f"Invalid JSON in {path}: line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    except OSError as exc:
        raise SettingsInventoryError(f"Unable to read {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise SettingsInventoryError("Settings ownership map root must be a JSON object")
    return data


def allowed_values(data: dict[str, Any], key: str) -> set[str]:
    allowed = data.get("allowed_values", {}).get(key, [])
    if not isinstance(allowed, list):
        return set()
    return {str(value) for value in allowed}


def validate_map(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    groups = data.get("groups")
    if not isinstance(groups, dict) or not groups:
        raise SettingsInventoryError("Settings ownership map must contain a non-empty 'groups' object")

    allowed_owners = allowed_values(data, "owner")
    allowed_levels = allowed_values(data, "level")
    allowed_statuses = allowed_values(data, "status")
    allowed_risks = allowed_values(data, "risk")

    errors: list[str] = []

    for group_id, group in sorted(groups.items()):
        if not isinstance(group, dict):
            errors.append(f"{group_id}: group entry must be an object")
            continue

        for field in REQUIRED_GROUP_FIELDS:
            if field not in group:
                errors.append(f"{group_id}: missing required field '{field}'")

        if "owner" in group and allowed_owners and group["owner"] not in allowed_owners:
            errors.append(f"{group_id}: invalid owner '{group['owner']}'")
        if "level" in group and allowed_levels and group["level"] not in allowed_levels:
            errors.append(f"{group_id}: invalid level '{group['level']}'")
        if "status" in group and allowed_statuses and group["status"] not in allowed_statuses:
            errors.append(f"{group_id}: invalid status '{group['status']}'")
        if "risk" in group and allowed_risks and group["risk"] not in allowed_risks:
            errors.append(f"{group_id}: invalid risk '{group['risk']}'")

        if "current_surfaces" in group and not isinstance(group["current_surfaces"], list):
            errors.append(f"{group_id}: current_surfaces must be a list")
        if "notes" in group and not isinstance(group["notes"], list):
            errors.append(f"{group_id}: notes must be a list")
        if "do_not_move_yet" in group and not isinstance(group["do_not_move_yet"], bool):
            errors.append(f"{group_id}: do_not_move_yet must be a boolean")
        if "preview_route" in group and group["preview_route"] is not None and not isinstance(group["preview_route"], str):
            errors.append(f"{group_id}: preview_route must be a string or null")
        if "preview_status" in group and group["preview_status"] is not None and group["preview_status"] not in PREVIEW_STATUSES:
            errors.append(f"{group_id}: preview_status must be one of {sorted(PREVIEW_STATUSES)} or null")

    if errors:
        joined = "\n".join(f"- {error}" for error in errors)
        raise SettingsInventoryError(f"Invalid settings ownership map:\n{joined}")

    return groups


def md(value: object) -> str:
    text = str(value) if value is not None else ""
    text = text.replace("|", "\\|").replace("\n", " ")
    return text if text else "-"


def join(values: list[object]) -> str:
    items = [str(value) for value in values if str(value)]
    return ", ".join(items) if items else "-"


def group_rows(groups: dict[str, dict[str, Any]]) -> list[str]:
    rows = [
        "| Group | Label | Owner | Level | Status | Risk | Preview route | Preview status | Do not move yet? | Current surfaces | Notes |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for group_id, group in sorted(groups.items()):
        rows.append(
            "| {group_id} | {label} | {owner} | {level} | {status} | {risk} | {preview_route} | {preview_status} | {do_not_move} | {surfaces} | {notes} |".format(
                group_id=md(group_id),
                label=md(group.get("label", group_id)),
                owner=md(group["owner"]),
                level=md(group["level"]),
                status=md(group["status"]),
                risk=md(group["risk"]),
                preview_route=md(group.get("preview_route")),
                preview_status=md(group.get("preview_status")),
                do_not_move=md(group["do_not_move_yet"]),
                surfaces=md(join(group["current_surfaces"])),
                notes=md(join(group["notes"])),
            )
        )
    return rows


def count_rows(title: str, counts: Counter[str]) -> list[str]:
    rows = [f"### {title}", "", "| Value | Count |", "| --- | ---: |"]
    for value, count in sorted(counts.items()):
        rows.append(f"| {md(value)} | {count} |")
    if not counts:
        rows.append("| - | 0 |")
    return rows


def list_groups(title: str, groups: dict[str, dict[str, Any]], predicate, include_preview: bool = False) -> list[str]:
    matches = [
        (group_id, group)
        for group_id, group in sorted(groups.items())
        if predicate(group)
    ]
    rows = [f"## {title}", ""]
    if not matches:
        rows.append("- None")
        return rows

    if include_preview:
        rows.extend(["| Group | Label | Owner | Level | Status | Risk | Preview route | Do not move yet? |", "| --- | --- | --- | --- | --- | --- | --- | --- |"])
    else:
        rows.extend(["| Group | Label | Owner | Status | Risk | Do not move yet? |", "| --- | --- | --- | --- | --- | --- |"])
    for group_id, group in matches:
        if include_preview:
            rows.append(
                f"| {md(group_id)} | {md(group.get('label', group_id))} | {md(group['owner'])} | {md(group['level'])} | {md(group['status'])} | {md(group['risk'])} | {md(group.get('preview_route'))} | {md(group['do_not_move_yet'])} |"
            )
        else:
            rows.append(
                f"| {md(group_id)} | {md(group.get('label', group_id))} | {md(group['owner'])} | {md(group['status'])} | {md(group['risk'])} | {md(group['do_not_move_yet'])} |"
            )
    return rows


def render_report(data: dict[str, Any], groups: dict[str, dict[str, Any]]) -> str:
    owners = Counter(group["owner"] for group in groups.values())
    levels = Counter(group["level"] for group in groups.values())
    statuses = Counter(group["status"] for group in groups.values())
    risks = Counter(group["risk"] for group in groups.values())
    do_not_move_count = sum(1 for group in groups.values() if group["do_not_move_yet"])
    high_risk_count = risks.get("high", 0)
    preview_groups = {
        group_id: group
        for group_id, group in groups.items()
        if group.get("preview_status") in PREVIEW_STATUSES and group.get("preview_route")
    }
    final_preview_groups = {
        group_id: group
        for group_id, group in preview_groups.items()
        if group.get("preview_status") == "final_read_only"
    }
    dedicated_not_final_groups = {
        group_id: group
        for group_id, group in preview_groups.items()
        if group.get("preview_status") == "dedicated_read_only"
    }
    preview_route_count = len({group.get("preview_route") for group in preview_groups.values()})
    preview_basic_count = sum(1 for group in preview_groups.values() if group["level"] == "basic")
    preview_advanced_count = sum(1 for group in preview_groups.values() if group["level"] == "advanced")
    preview_developer_count = sum(1 for group in preview_groups.values() if group["level"] == "developer")
    preview_do_not_move_count = sum(1 for group in preview_groups.values() if group["do_not_move_yet"])
    final_route_count = len({group.get("preview_route") for group in final_preview_groups.values()})
    final_basic_count = sum(1 for group in final_preview_groups.values() if group["level"] == "basic")
    final_advanced_count = sum(1 for group in final_preview_groups.values() if group["level"] == "advanced")
    final_developer_count = sum(1 for group in final_preview_groups.values() if group["level"] == "developer")

    lines: list[str] = [
        "# HYBRID SETTINGS INVENTORY REPORT",
        "",
        "Generated by `tools/hybrid_settings_inventory.py` from `tools/hybrid_settings_ownership_map.json`.",
        "",
        "This report is read-only metadata. It does not modify runtime configuration, UI, database state, or Classic behavior.",
        "",
        "## Summary",
        "",
        f"- Schema version: `{md(data.get('schema_version', 'unknown'))}`",
        f"- Total groups: {len(groups)}",
        f"- High-risk groups: {high_risk_count}",
        f"- `do_not_move_yet` groups: {do_not_move_count}",
        f"- Groups with dedicated preview: {len(preview_groups)}",
        f"- Dedicated preview routes: {preview_route_count}",
        f"- Basic groups with preview: {preview_basic_count}",
        f"- Advanced groups with preview: {preview_advanced_count}",
        f"- Developer groups with preview: {preview_developer_count}",
        f"- `do_not_move_yet` groups with preview: {preview_do_not_move_count}",
        f"- Final read-only groups: {len(final_preview_groups)}",
        f"- Final read-only routes: {final_route_count}",
        f"- Final read-only Basic groups: {final_basic_count}",
        f"- Final read-only Advanced groups: {final_advanced_count}",
        f"- Final read-only Developer groups: {final_developer_count}",
        f"- Dedicated-but-not-final groups: {len(dedicated_not_final_groups)}",
        "",
    ]

    lines.extend(count_rows("Counts By Owner", owners))
    lines.append("")
    lines.extend(count_rows("Counts By Level", levels))
    lines.append("")
    lines.extend(count_rows("Counts By Status", statuses))
    lines.append("")
    lines.extend(count_rows("Counts By Risk", risks))
    lines.append("")
    lines.extend(list_groups("Basic Groups", groups, lambda group: group["level"] == "basic"))
    lines.append("")
    lines.extend(list_groups("Advanced Groups", groups, lambda group: group["level"] == "advanced"))
    lines.append("")
    lines.extend(list_groups("Developer Groups", groups, lambda group: group["level"] == "developer"))
    lines.append("")
    lines.extend(list_groups("High-Risk Groups", groups, lambda group: group["risk"] == "high"))
    lines.append("")
    lines.extend(list_groups("Do Not Move Yet Groups", groups, lambda group: group["do_not_move_yet"]))
    lines.append("")
    lines.extend(
        list_groups(
            "Groups With Dedicated Preview",
            groups,
            lambda group: group.get("preview_status") in PREVIEW_STATUSES and bool(group.get("preview_route")),
            include_preview=True,
        )
    )
    lines.append("")
    lines.extend(
        list_groups(
            "Final Read-Only Product Pages",
            groups,
            lambda group: group.get("preview_status") == "final_read_only" and bool(group.get("preview_route")),
            include_preview=True,
        )
    )
    lines.append("")
    lines.extend(
        list_groups(
            "Dedicated Preview But Not Final",
            groups,
            lambda group: group.get("preview_status") == "dedicated_read_only" and bool(group.get("preview_route")),
            include_preview=True,
        )
    )
    lines.append("")
    lines.extend(
        list_groups(
            "Groups Without Dedicated Preview",
            groups,
            lambda group: not (group.get("preview_status") in PREVIEW_STATUSES and group.get("preview_route")),
            include_preview=True,
        )
    )
    lines.append("")
    lines.extend(
        list_groups(
            "Do Not Move Yet Groups With Preview",
            groups,
            lambda group: group["do_not_move_yet"] and group.get("preview_status") in PREVIEW_STATUSES and bool(group.get("preview_route")),
            include_preview=True,
        )
    )
    lines.append("")
    lines.extend(
        [
            "## Full Matrix",
            "",
            *group_rows(groups),
            "",
            "## Notes",
            "",
            "- `do_not_move_yet` means the group should not be moved into active redesigned settings UI yet.",
            "- `preview_status=dedicated_read_only` means a product-preview page exists, but it is not a config editor.",
            "- `preview_status=final_read_only` means the page has been upgraded from preview inventory to a final read-only product layout. It is still not a config editor.",
            "- High-risk groups usually involve profile/camera ownership, credentials, filesystem paths, hardware, restore/download behavior, or mutating actions.",
            "- This inventory is intentionally separate from runtime configuration and can be reviewed before any UI wiring.",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> int:
    try:
        data = load_map(MAP_PATH)
        groups = validate_map(data)
    except SettingsInventoryError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    REPORT_PATH.write_text(render_report(data, groups), encoding="utf-8")
    print(f"Wrote {REPORT_PATH.relative_to(REPO_ROOT)}")
    print(f"Groups: {len(groups)}")
    print(f"High risk: {sum(1 for group in groups.values() if group['risk'] == 'high')}")
    print(f"Do not move yet: {sum(1 for group in groups.values() if group['do_not_move_yet'])}")
    print(
        "Dedicated preview groups: {0}".format(
            sum(
                1
                for group in groups.values()
                if group.get("preview_status") in PREVIEW_STATUSES and group.get("preview_route")
            )
        )
    )
    print(
        "Final read-only groups: {0}".format(
            sum(
                1
                for group in groups.values()
                if group.get("preview_status") == "final_read_only" and group.get("preview_route")
            )
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
