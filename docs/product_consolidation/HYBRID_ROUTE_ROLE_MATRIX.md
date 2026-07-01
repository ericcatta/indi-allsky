# Hybrid Route Role Matrix

This matrix classifies the `/modern-admin/*` route family by product role.

It is not a replacement for `HYBRID_UI_INVENTORY_REPORT.md` or
`tools/hybrid_ui_ownership_map.json`. The inventory remains the technical
route list; this document is the product consolidation lens used to decide
what may be Product, Advanced, Developer, legacy fallback, or external/shared
surface.

## Purpose

Hybrid should feel like a standalone product, not a fork with a new skin. The
route structure currently contains both the new Product UI and operational
surfaces inherited or wrapped from Classic. Classifying the route roles prevents
future work from flattening everything into "Modern Admin" again.

## Classification Rules

| Role | Meaning | User posture | Cleanup stance |
| --- | --- | --- | --- |
| Primary Product | Part of the frozen product journey. | Default user path. | Protect. Do not demote or remove. |
| Product Context | Product-adjacent support or context page. | Helps explain the product, but is not the main journey. | Protect if linked to Product spine. |
| Advanced / Operational | Useful operator workflow. | For users managing cameras, media, storage, uploads, or observatory tools. | Keep; simplify only with evidence. |
| Developer / Diagnostics | Admin, logs, users, tasks, low-level system, restore, or raw internals. | Low-frequency technical use. | Keep out of primary product path. |
| Legacy Fallback Wrapper | Hybrid shell around Classic or action-heavy behavior. | Compatibility bridge. | Keep until safe native replacement exists. |
| Shell / Safety Utility | Supports the shell or safe-action metadata. | Infrastructure, not a page. | Keep minimal and audited. |
| External / Dynamic Compatibility | Dynamic bridge or URL pattern whose consumers are not fully known. | Compatibility surface. | Do not remove before runtime evidence. |

## Route Families

### Primary Product

| Route or pattern | Role | Product decision | Risk | Notes |
| --- | --- | --- | --- | --- |
| `/modern-admin` | Primary Product entry | Keep as Product entry/redirect to Now. | Medium | Must continue to feel like Hybrid home, not legacy dashboard. |
| `/modern-admin/now` | Primary Product | Protect. | High | Home surface; carries DATA001-DATA006 bounded summaries. |
| `/modern-admin/highlights` | Primary Product | Protect. | High | Attention layer; must not collapse into Gallery/Event list. |
| `/modern-admin/moment` | Primary Product | Protect. | Medium | Static identifier-less v1; future data needs careful identifier strategy. |
| `/modern-admin/output` | Primary Product | Protect. | Medium | Static identifier-less v1; do not turn into media gallery. |
| `/modern-admin/sky-cycle` | Primary Product / Context | Protect. | Medium | Product context for day/night/cycle summaries. |
| `/modern-admin/library` | Primary Product | Protect. | Medium | Product memory model; not a generic gallery. |
| `/modern-admin/observatory` | Primary Product health | Protect. | Medium | Readiness summary; should not become System/Developer. |

### Shell And Safety Utilities

| Route or pattern | Role | Product decision | Risk | Notes |
| --- | --- | --- | --- | --- |
| `/modern-admin/mode/<mode>` | Shell / Safety Utility | Keep minimal. | Low-medium | UI preference route; not product content. |
| `/modern-admin/safe-action/dry-run` | Shell / Safety Utility | Keep audited and non-mutative. | High | POST route, but intended as safety metadata. Do not expand without safe-action registry. |

### Camera And Capture Operations

| Route or pattern | Role | Product decision | Risk | Notes |
| --- | --- | --- | --- | --- |
| `/modern-admin/cameras` | Advanced / Operational | Keep as primary operational camera surface. | High | Protected multicamera/profile work. |
| `/modern-admin/cameras/add` | Advanced / Operational | Keep. | High | Camera/profile lifecycle; avoid settings-key changes. |
| `/modern-admin/cameras/info` | Advanced / Operational | Keep. | Medium | Wraps camera/lens information. |
| `/modern-admin/cameras/adu-history` | Advanced / Operational | Keep. | Medium | Diagnostic capture history. |
| `/modern-admin/cameras/image-lag` | Advanced / Operational | Keep. | Medium | Capture timing diagnostic. |
| `/modern-admin/cameras/dark-library` | Advanced / Operational | Keep. | Medium-high | Operational calibration library; avoid filesystem assumptions. |
| `/modern-admin/cameras/mask-base` | Advanced / Operational | Keep. | Medium-high | Mask/source-related support; avoid media/path leakage. |
| `/modern-admin/cameras/detect-indi` | Developer / Diagnostics | Keep out of primary product path. | High | Hardware/service discovery action surface. |
| `/modern-admin/cameras/start-indi` | Developer / Diagnostics | Keep out of primary product path. | High | Service/action risk. |
| `/modern-admin/capture/service` | Developer / Diagnostics | Keep out of primary product path. | High | Capture service action/control surface. |

### Media And Source Operations

| Route or pattern | Role | Product decision | Risk | Notes |
| --- | --- | --- | --- | --- |
| `/modern-admin/loop` | Advanced / Operational | Keep. | Medium | Operational latest/loop viewing, not Product Now. |
| `/modern-admin/media/gallery` | Advanced / Operational | Keep. | Medium-high | Browsing surface; do not merge with Library without contract. |
| `/modern-admin/media/gallery/page` | Advanced / Operational | Keep. | Medium-high | Pagination/detail support; static consumers may be incomplete. |
| `/modern-admin/media/images` | Advanced / Operational | Keep. | Medium-high | Image metadata browsing. |
| `/modern-admin/media/images/<int:image_id>` | Advanced / Operational | Keep. | Medium-high | Detail route; avoid path/URL leakage. |
| `/modern-admin/media/timelapses` | Advanced / Operational | Keep. | Medium-high | Generated media browsing. |
| `/modern-admin/media/timelapses/<int:video_id>` | Advanced / Operational | Keep. | Medium-high | Detail route; no Product Output replacement yet. |
| `/modern-admin/media/keograms` | Advanced / Operational | Keep. | Medium-high | Generated media browsing. |
| `/modern-admin/media/startrails` | Advanced / Operational | Keep. | Medium-high | Generated media browsing. |
| `/modern-admin/media/startrail-videos` | Advanced / Operational | Keep. | Medium-high | Generated media browsing. |
| `/modern-admin/media/mini-timelapses` | Advanced / Operational | Keep. | Medium-high | Generated media browsing. |
| `/modern-admin/media/panorama` | Advanced / Operational | Keep. | Medium-high | Generated media browsing. |
| `/modern-admin/media/panorama-loop` | Advanced / Operational | Keep. | Medium-high | Generated media browsing. |
| `/modern-admin/media/raw` | Advanced / Operational | Keep. | High | Source-sensitive; no RAW reads in Product path. |
| `/modern-admin/media/fits` | Advanced / Operational | Keep. | High | Source-sensitive; source trust owns summaries. |
| `/modern-admin/fits` | Advanced / Operational | Keep. | High | FITS browser/detail family. |
| `/modern-admin/fits/<int:fits_id>` | Advanced / Operational | Keep. | High | Detail route; avoid raw file exposure. |
| `/modern-admin/media/public-endpoints` | Developer / Diagnostics | Keep as compatibility reference. | Medium | Documents public/latest endpoints rather than Product content. |

### Observatory Advanced Context

| Route or pattern | Role | Product decision | Risk | Notes |
| --- | --- | --- | --- | --- |
| `/modern-admin/observatory/sqm` | Advanced / Operational | Keep under Observatory tools. | Medium | Runtime/data-source ownership needs care. |
| `/modern-admin/observatory/charts` | Advanced / Operational | Keep. | Medium | Charting surface; avoid broad queries. |
| `/modern-admin/observatory/sensor-panel` | Advanced / Operational | Keep. | Medium | Sensor ownership still needs Environmental discovery. |
| `/modern-admin/observatory/astropanel` | Advanced / Operational | Keep. | Medium | Environmental/astro context. |
| `/modern-admin/observatory/virtualsky` | Advanced / Operational | Keep. | Medium | Static asset dependencies need later verification. |
| `/modern-admin/observatory/realtime-keogram` | Advanced / Operational | Keep. | Medium-high | Media/runtime surface. |
| `/modern-admin/observatory/long-term-keogram` | Advanced / Operational | Keep. | Medium-high | Media/runtime surface. |

### Storage, Uploads, And Integrations

| Route or pattern | Role | Product decision | Risk | Notes |
| --- | --- | --- | --- | --- |
| `/modern-admin/storage` | Advanced / Operational | Keep. | Medium | Operational storage summary. |
| `/modern-admin/storage/file-space-usage` | Advanced / Operational | Keep. | Medium | Storage diagnostic; performance-sensitive. |
| `/modern-admin/uploads` | Advanced / Operational | Keep. | Medium-high | Integration/upload overview. |
| `/modern-admin/uploads/<provider_slug>` | Advanced / Operational | Keep. | Medium-high | Integration detail; provider-specific. |
| `/modern-admin/youtube` | Advanced / Operational | Keep. | High | OAuth/integration-adjacent; do not simplify casually. |

### Settings

| Route or pattern | Role | Product decision | Risk | Notes |
| --- | --- | --- | --- | --- |
| `/modern-admin/settings` | Advanced / Operational | Keep until Settings Contract Review. | High | Inventory/entry surface, not final Product language. |
| `/modern-admin/settings/basic` | Advanced / Operational | Keep. | High | Preview/read-only stance must be verified. |
| `/modern-admin/settings/advanced` | Advanced / Operational | Keep. | High | Preview/read-only stance must be verified. |
| `/modern-admin/settings/developer` | Developer / Diagnostics | Keep. | High | Raw/internals-oriented settings. |
| `/modern-admin/settings/ready` | Advanced / Operational | Keep. | High | Readiness preview. |
| `/modern-admin/settings/analytics` | Advanced / Operational | Keep. | High | Analytics ownership needs Settings Contract Review. |
| `/modern-admin/settings/storage` | Advanced / Operational | Keep. | High | Storage settings are operational, not Product health. |
| `/modern-admin/settings/notifications` | Advanced / Operational | Keep. | High | Notification settings; credentials/policy risk. |
| `/modern-admin/settings/camera-profile` | Advanced / Operational | Protect. | Critical | Profile-first setting ownership. |
| `/modern-admin/settings/camera-connection` | Advanced / Operational | Protect. | Critical | Hardware/config risk. |
| `/modern-admin/settings/exposure-gain` | Advanced / Operational | Protect. | Critical | Capture quality risk. |
| `/modern-admin/settings/auto-exposure-gain` | Advanced / Operational | Protect. | Critical | Capture automation risk. |
| `/modern-admin/settings/hybrid-awb` | Advanced / Operational | Protect. | High | Image processing/capture quality risk. |
| `/modern-admin/settings/acquisition-save` | Advanced / Operational | Protect. | High | Source preservation risk. |
| `/modern-admin/settings/fits-source` | Advanced / Operational | Protect. | High | Scientific source ownership. |
| `/modern-admin/settings/full` | Developer / Diagnostics | Keep as fallback. | Critical | Raw/full compatibility surface. |
| `/modern-admin/settings/capture` | Advanced / Operational | Protect. | Critical | Capture behavior risk. |
| `/modern-admin/settings/cameras` | Advanced / Operational | Protect. | Critical | Multicamera/profile behavior risk. |

### System, Users, Tasks, Logs, And Restore

| Route or pattern | Role | Product decision | Risk | Notes |
| --- | --- | --- | --- | --- |
| `/modern-admin/system` | Developer / Diagnostics | Keep out of primary product path. | Medium-high | System overview. |
| `/modern-admin/system/info` | Developer / Diagnostics | Keep. | Medium | System diagnostics. |
| `/modern-admin/system/support` | Developer / Diagnostics | Keep. | Medium | Support diagnostics. |
| `/modern-admin/system/log` | Developer / Diagnostics | Keep. | High | Log access. |
| `/modern-admin/system/log/<log_name>` | Developer / Diagnostics | Keep. | High | Log detail/download-adjacent risk. |
| `/modern-admin/tasks` | Developer / Diagnostics | Keep. | Medium-high | Task queue internals. |
| `/modern-admin/tasks/<int:task_id>` | Developer / Diagnostics | Keep. | Medium-high | Task detail. |
| `/modern-admin/users` | Developer / Diagnostics | Keep. | High | Auth/user administration. |
| `/modern-admin/users/<int:user_id>` | Developer / Diagnostics | Keep. | High | User detail/admin. |
| `/modern-admin/notifications` | Advanced / Operational | Keep. | Medium-high | Operational alerts, not Product Highlights. |
| `/modern-admin/notifications/<int:notification_id>` | Advanced / Operational | Keep. | Medium-high | Alert detail. |
| `/modern-admin/config-history` | Developer / Diagnostics | Keep. | High | Config audit/history. |
| `/modern-admin/config-restore` | Developer / Diagnostics | Keep. | Critical | Restore workflow; mutation-adjacent. |
| `/modern-admin/config-restore/<int:config_id>` | Developer / Diagnostics | Keep. | Critical | Restore detail; no simplification without safe-action plan. |
| `/modern-admin/updates` | Developer / Diagnostics | Keep. | Medium-high | Update/admin surface. |

### Legacy Fallback Wrappers

| Route or pattern | Role | Product decision | Risk | Notes |
| --- | --- | --- | --- | --- |
| `/modern-admin/storage/drives` | Legacy Fallback Wrapper | Keep until native safe contract exists. | High | Drive/system mutation risk. |
| `/modern-admin/system/config` | Legacy Fallback Wrapper | Keep until Settings Contract Review. | Critical | Full config behavior. |
| `/modern-admin/system/network` | Legacy Fallback Wrapper | Keep until native safe contract exists. | High | Network/system mutation risk. |
| `/modern-admin/system/gpio-control` | Legacy Fallback Wrapper | Keep until native safe contract exists. | High | Hardware mutation risk. |
| `/modern-admin/tools/camera-simulator` | Legacy Fallback Wrapper | Keep. | Medium-high | Tool wrapper. |
| `/modern-admin/tools/generate` | Legacy Fallback Wrapper | Keep. | High | Media generation action risk. |
| `/modern-admin/tools/focus` | Legacy Fallback Wrapper | Keep. | High | Hardware/control risk. |
| `/modern-admin/tools/process-fits` | Legacy Fallback Wrapper | Keep. | High | FITS/media processing risk. |
| `/modern-admin/tools/image-circle-helper` | Legacy Fallback Wrapper | Keep. | Medium-high | Media helper. |

### Dynamic Compatibility

| Route or pattern | Role | Product decision | Risk | Notes |
| --- | --- | --- | --- | --- |
| `/modern-admin/classic/<classic_page>` | External / Dynamic Compatibility | Keep until manual route walk proves it unnecessary. | Medium-high | Static inventory cannot prove all consumers. |

## Consolidation Decisions

1. The Product spine is intentionally small: Now, Highlights, Moment, Output, Sky Cycle, Library, Observatory.
2. Camera, media, storage, uploads, settings, system, users, logs, tasks, and tools are valuable, but they are not the default product story.
3. Settings should remain P0 after this matrix because nearly every settings route is high or critical risk.
4. Safe-control wrappers should not be "cleaned up" before a Safe Action Registry exists.
5. Media browsing should not be merged with Library or Output Detail until identifier strategy and media/source policy are defined.
6. Observatory subroutes are Advanced context; Observatory itself remains the Product health summary.

## Backlog Impact

Completed:

- P0 Route Role Matrix.

Reprioritized:

- Settings Contract Review remains P0 and becomes the next recommended step. This matrix shows settings are the largest high-risk route family and the most likely place for Hybrid to feel like a fork if ownership stays unclear.
- Product Spine Regression Checklist remains P0 but should follow Settings Contract Review, because the Product spine is already stable and tested while settings still lack a formal contract.
- Safe Action Registry Discovery remains P1, but it should not start until settings and wrapper ownership are clearer.

## Verification

This document is based on:

- `HYBRID_UI_INVENTORY_REPORT.md`
- `tools/hybrid_ui_ownership_map.json`
- `docs/product_consolidation/HYBRID_PRODUCT_CONSOLIDATION_AUDIT.md`
- static inspection of `indi_allsky/flask/views.py`

No runtime behavior was changed.
