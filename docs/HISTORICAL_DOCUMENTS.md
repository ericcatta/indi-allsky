# Historical Hybrid documents

These 19 reports were removed from the current documentation because they record
completed design, migration or review stages. They had no incoming references in
the tracked documentation, runtime, scripts or tests when reviewed. Their claims
about Classic dependencies, static product pages, readiness and unfinished porting
apply to their original checkpoints; they do not describe the current application
or certify the installed Raspberry Pi release.

For current work use the [Hybrid guide](HYBRID_GUIDE.md),
[current acceptance work](HYBRID_ACCEPTANCE_REMAINING.md) and
[deployment and rollback record](../HYBRID_DEPLOYMENT.md).

## Removed reports

All paths below were relative to the repository root.

| Historical path | Reason for removal from current documentation |
| --- | --- |
| `EMERGENCY_PRODUCT_UI_CORRECTION.md` | Earlier Product UI correction record. |
| `HYBRID_NOW_AFTER_REAL_DATA_REVIEW.md` | Earlier metadata-stage Now review. |
| `HYBRID_NOW_CURRENT_PHASE_SOURCE_REVIEW.md` | Earlier current-phase source review. |
| `HYBRID_NOW_LATEST_FRAME_SOURCE_REVIEW.md` | Earlier latest-frame source review. |
| `HYBRID_NOW_RUNTIME_SAFETY_REVIEW.md` | Earlier Now runtime safety checkpoint. |
| `HYBRID_NOW_RUNTIME_WIRING_REVIEW.md` | Earlier Now runtime wiring checkpoint. |
| `HYBRID_PRODUCT_CONSOLIDATION_CLOSURE.md` | Completed migration phase handoff with superseded Classic blockers. |
| `HYBRID_PRODUCT_CONSOLIDATION_MATRIX.md` | Earlier consolidation ownership snapshot. |
| `HYBRID_PRODUCT_FLOW_STRESS_TEST.md` | Earlier product-flow review. |
| `HYBRID_PRODUCT_UI_V1_BACKLOG.md` | Superseded Product UI V1 work queue. |
| `HYBRID_PRODUCT_UI_V1_CONSISTENCY_REVIEW.md` | Earlier V1 visual consistency review. |
| `HYBRID_SKY_CYCLE_REPORT_REVIEW.md` | Earlier Sky Cycle implementation review. |
| `HYBRID_TASK_QUEUE_PORTING_PLAN.md` | Completed frontend porting plan. |
| `HYBRID_UI_CONSISTENCY_SWEEP.md` | Earlier visual consistency sweep. |
| `HYBRID_UI_COVERAGE_AUDIT.md` | Pre-retirement shell coverage snapshot. |
| `RASPBERRY_READINESS_AUDIT.md` | Pre-deployment alpha readiness assessment. |
| `RELEASE_CANDIDATE_CLEANUP_EXECUTION.md` | Earlier local bytecode cleanup record. |
| `TARGETED_PERFORMANCE_MEDIA_LOOP_AUDIT.md` | Earlier operational-page performance checkpoint. |
| `VISUAL_REDESIGN_PASS_001.md` | Earlier visual redesign pass record. |

## Recover one historical report

The complete original files remain available at commit
`2a094d9fc315adc1940044ac31f2f4f2f3ac0ed6`. Inspect one report with:

```sh
git show 2a094d9fc315adc1940044ac31f2f4f2f3ac0ed6:RASPBERRY_READINESS_AUDIT.md
```

To save a copy for research outside the checkout:

```sh
git show 2a094d9fc315adc1940044ac31f2f4f2f3ac0ed6:RASPBERRY_READINESS_AUDIT.md > /tmp/RASPBERRY_READINESS_AUDIT.md
```

Substitute a path from the table to inspect another report. Recover individual
files only; restoring the entire historical tree would reintroduce obsolete
application code and overwrite current work. Reading or recovering a report does
not restore its historical assumptions as present-day requirements.

## Removed generated and obsolete images

The same cleanup removes six Classic UI screenshots (`content/webui_home.png`,
`webui_chart01.png`, `webui_chart02.png`, `webui_images.png`, `webui_systeminfo.png`
and `webui_timelapse_mono.png`). Their only consumers were the obsolete README
screenshots; they do not document Hybrid.

Six reproducible denoise demonstration outputs were also removed from
`examples/DENOISE PR TEST ENVIRONMENT/Test Output/`: `real_02_star_mask.png`,
`real_06_overlay.png`, `real_08a_wavelet.png`, `real_08b_bilateral.png`,
`real_08c_gaussian_blur.png` and `real_08d_median_blur.png`. The demonstration script
can regenerate them; exact ignore entries prevent recommitting these outputs.
The source photographs and `real_01_input.png` test fixture remain in place.

These 12 removed images total 40,281,598 bytes in the checkout. Git history still
retains the originals; this cleanup does not rewrite history or promise an equal
reduction in clone size. Runtime assets, shared JavaScript libraries, release
evidence and private/local files were not removed.
