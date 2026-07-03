# Hybrid Product Consolidation Closure

This document closes **Phase 1: Product Consolidation** and hands the project
to **Phase 2: Hybrid Runtime Independence**.

It answers one question:

**What is Hybrid today?**

## 1. Mission Accomplished

Product Consolidation turned Hybrid from an evolved `indi-allsky` fork into a
coherent product architecture with explicit ownership boundaries.

The phase is complete because Hybrid now has:

- a stable Product UI and visual system;
- Product-owned view models and read-only product surfaces;
- bounded real data integrations;
- domain-owned read services for key areas;
- explicit Settings contracts;
- a minimal Action Contract foundation;
- documented Classic-removal blockers.

The remaining work is no longer Product architecture cleanup. It is runtime
replacement.

## 2. Current Architecture

| Pillar | Responsibility | Current State |
| --- | --- | --- |
| Product UI | Defines the user-facing Hybrid experience: Now, Highlights, Moment, Output, Sky Cycle, Library, Observatory. | Stable. Visual system frozen except for bugs, accessibility, responsive fixes, and consistency. |
| Product View Models | Own Product payload shape and product-first language. | Stable. Framework-free, test-covered, and separated from Flask/request/session behavior. |
| Data Integrations | Provide bounded, metadata-only real data to Product surfaces. | DATA001-DATA006 integrated. No preview/media/filesystem expansion implied. |
| Domain Ownership | Moves responsibilities out of Classic-style views into Hybrid-owned services. | Strong for read-only Notifications and Task Status; partial for Media, Camera, Observatory, System. |
| Hybrid Boundaries | Keep Modern/Product-facing wrappers separate from Classic implementation ownership. | Boundaries exist for Product, Observatory tools, Camera tools, System tools, Notifications, Task status, Media metadata, and Media browse. |
| Services | Own query, formatting, display policy, and read-only domain semantics where safe. | Present for Notifications, Task Status, Media Metadata slices, Camera Diagnostics, Observatory Tools, and System Tools. |
| Settings Contracts | Describe existing settings groups without changing keys, defaults, write behavior, or Classic fallback. | Many read-only contracts exist. Write/save/restore remains unresolved. |
| Action Contract | Defines the first metadata-only foundation for safe actions. | Minimal foundation exists via `ModernAdminSafeActionContract`; execution ownership is not complete. |
| Compatibility Layer | Preserves routes, Classic fallback, public/latest media, external APIs, and legacy behavior. | Still required. It is now a known boundary, not an accidental dependency. |

## 3. Domain Ownership

| Domain | Hybrid Ownership | Status | Notes |
| --- | ---: | --- | --- |
| Product UI | 96% | Hybrid-owned | Product spine is stable. Remaining dependency is surrounding compatibility shell, not Product architecture. |
| Notifications | 95% | Effectively Hybrid-owned | Read ownership, acknowledge ownership, result/audit policy, and settings contract are Hybrid-owned. Legacy endpoints remain compatibility surfaces. |
| Task Status | 90% | Hybrid-owned for read-only status | List/detail read services are owned. Queue mutation, retry, purge, and execution remain future Action Contract work. |
| Media Metadata | 68% | Partially Hybrid-owned | Several metadata-only slices are owned. Preview, download, URL generation, public/latest, and filesystem behavior remain Classic blockers. |
| Camera Diagnostics | 74% | Partially Hybrid-owned | Camera Info and Image Lag read-only responsibilities moved into Hybrid services. Camera control, Dark Library, Mask, and calibration/file behavior remain sensitive. |
| Observatory Tools | 70% | Partially Hybrid-owned | SQM, Long-term Keogram display formatting, and VirtualSky defaults have Hybrid ownership. Live/provider/media-backed behavior remains unresolved. |
| System Tools | 70% | Partially Hybrid-owned | Read-only summaries are owned. Support scripts, log export/download, system controls, users/auth remain sensitive. |
| Settings | 48% | Contract-owned, not runtime-owned | Many read-only contracts exist. Full config write/save/restore remains the largest Classic blocker. |
| Safe Actions | 35% | Foundation only | Action metadata contract exists. Most mutative behavior remains outside a complete Hybrid action model. |

## 4. What Is No Longer Classic

The following concepts can now be considered Hybrid-owned:

| Concept | Meaning |
| --- | --- |
| Product spine | Now, Highlights, Moment, Output, Sky Cycle, Library, and Observatory are product surfaces, not Classic pages. |
| Product payloads | Product view models own the Product UI data contract. |
| Product visual system | Hybrid Sky Console is the design baseline. |
| Latest frame metadata | Real bounded metadata is integrated without preview or filesystem access. |
| Latest generated output metadata | Real bounded generated-output metadata is integrated into Now. |
| Current capture status | Product-level capture status is represented without hardware probing. |
| Source trust summary | Product-level trust summary exists without filesystem verification. |
| Highlights metadata | Explainable metadata-based Highlights exist without detector/AI/ranking. |
| Sky Cycle summary | Product-level sky-cycle context exists without reconstructing full history. |
| Notifications read ownership | Notification list/detail formatting and summaries are Hybrid-owned. |
| Notification acknowledge ownership | Acknowledge lookup/result/audit policy is domain-owned; safe action remains orchestrator. |
| Task status read ownership | Queue/detail read status, visibility policy, and formatting are Hybrid-owned. |
| Media metadata slices | Startrail video, Keogram, Startrail, and Mini Timelapse metadata services are Hybrid-owned. |
| Camera diagnostic summaries | Camera Info and Image Lag read-only policy/formatting have Hybrid services. |
| Observatory display policies | SQM summary, Long-term Keogram age display, and VirtualSky context defaults have Hybrid ownership. |
| System read-only summaries | System Info overview and Log Detail display policy moved into System Tools ownership. |
| Settings contracts | Multiple settings groups have read-only Hybrid contracts while preserving existing keys. |
| Settings contract helpers | Shared contract helpers and guardrails reduce duplication. |
| Action metadata foundation | Safe actions can expose stable contract metadata via `ModernAdminSafeActionContract`. |

## 5. Remaining Classic Blockers

These are architectural milestones, not cleanup tasks.

| Blocker | Why It Blocks Classic Removal | Required Milestone |
| --- | --- | --- |
| Settings Write | Classic still owns full config save, restore, history, raw config compatibility, defaults, and rollback risk. | Hybrid Settings write contract with preview, diff, rollback, and unchanged keys. |
| Media Contract | Media behavior includes metadata, previews, downloads, public/latest URLs, FITS/raw viewers, filesystem helpers, cache, and external consumers. | Hybrid Media Contract separating metadata, URL, preview, download, public/latest, and filesystem semantics. |
| Action Contract | Many mutations still live in Classic AJAX, external APIs, system wrappers, and domain handlers. | Domain-owned action services with stable permission, audit, dry-run, execute, and compatibility wrappers. |
| Compatibility Layer | Public routes, `/action/*`, `/sync/v1/*`, OAuth/YouTube, legacy AJAX, and media URLs may have external consumers. | Compatibility baselines and endpoint tests before implementation replacement. |
| Runtime / Providers | Sensors, GPS, camera detection/control, support scripts, system controls, users/auth, network/drives/GPIO are runtime/security-sensitive. | Dedicated runtime/provider/security reviews and one-family replacement plans. |

## 6. Things Intentionally Not Solved

| Area | Reason It Was Postponed |
| --- | --- |
| Detector | Product Consolidation was about ownership and architecture, not scientific detection. Detector work must start from its own design/runtime constraints. |
| Scientific Intelligence | Highlights are explainable metadata-based objects today. AI/ranking/scientific inference is intentionally not active. |
| AI | No AI ranking or interpretation was introduced. Product intelligence remains explainable and reversible. |
| Runtime providers | Sensors, GPS, weather, provider polling, and hardware-backed status remain outside this phase. |
| Sensor runtime | Sensor ownership requires provider/runtime review before Product exposure or settings writes. |
| Media runtime | Preview, download, cache, URL generation, FITS/raw reading, and filesystem behavior remain Classic-removal milestones. |
| Settings write | Read-only contracts exist; write behavior is intentionally not implemented yet. |
| Mutating actions | Safe-action metadata exists; broad action execution ownership is future work. |
| Classic deletion | Classic remains fallback, reference, and compatibility provider until runtime responsibilities are replaced. |

## 7. Next Project Phase

The next phase is:

**Phase 2: Hybrid Runtime Independence**

The goal changes.

Product Consolidation asked:

> Does Hybrid have its own product architecture?

Hybrid Runtime Independence asks:

> Can Hybrid replace Classic runtime responsibilities without changing external
> behavior?

The next phase should focus on:

| Runtime Independence Track | First Useful Step |
| --- | --- |
| Action Contract hardening | Validate every registered safe action exposes stable metadata while preserving registry output and response shape. |
| Settings Write pilot | Add preview/diff/rollback semantics for one already-owned low-risk settings group before any real save expansion. |
| Media Contract pilot | Classify and test media URL/preview/download/public/latest behavior before replacing helpers. |
| Compatibility baselines | Add endpoint tests for public/latest and external action/sync routes. |
| Provider/runtime separation | Review one provider/hardware family at a time before implementation. |

Recommended immediate next mission:

**Safe Action Contract Adoption Guardrails**

This prepares mutation ownership without touching dangerous mutations yet.

## 8. Definition Of Done

Product Consolidation is complete.

Completion means:

- Hybrid has a Product spine.
- Hybrid has a frozen Product Architecture.
- Hybrid has a stable visual system.
- Hybrid has bounded real Product data.
- Hybrid has domain ownership boundaries.
- Hybrid has read-only services for several former Classic-owned areas.
- Hybrid has Settings contracts.
- Hybrid has an Action Contract foundation.
- Hybrid has a current Classic Exit Assessment.
- The remaining blockers are known architectural milestones.

Future work should no longer focus on:

- wrapper extraction for its own sake;
- ownership polishing without runtime impact;
- formatter cleanup unless it removes meaningful duplication;
- adding contract-only Settings slices with no path to write ownership;
- broad audits that repeat existing inventories;
- visual redesign.

Future work should focus on:

- replacing Classic runtime responsibilities behind stable contracts;
- preserving route/API/template behavior while moving ownership;
- adding compatibility tests before changing risky implementation;
- keeping Classic as fallback until each runtime domain has a native Hybrid
  owner.

From this point forward, the project should measure progress by reduced runtime
dependency on Classic, not by additional architecture documentation.
