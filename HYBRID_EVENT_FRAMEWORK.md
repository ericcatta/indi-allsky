# Hybrid AllSky Event Framework

## 1. Purpose

The Hybrid AllSky Event Framework is the architectural contract for every future event-related capability in Hybrid AllSky.

It defines how observations become event candidates, how candidates become timelines, how timelines are classified, how evidence is reviewed, how validated datasets are built, and how future detectors and AI modules may participate without compromising reproducibility or scientific accountability.

This framework is intentionally detector-agnostic.

It does not know how to detect meteors.
It does not know how RMS works.
It does not know how satellites, aircraft, aurora, lightning, birds, insects, or lens artifacts are recognized.

Instead, it defines the common lifecycle, data contracts, review process, validation process, and promotion path that every detector must follow.

The long-term goal is not merely to operate an AllSky camera.

The long-term goal is to build a scientific observatory capable of understanding what happened in the sky during the night.

### 1.1 Relationship to the Broader Hybrid Architecture

Hybrid AllSky as a complete platform transforms sky observations into verifiable knowledge.

The broader conceptual flow is:

```text
Reality
  -> Observation
  -> Evidence
  -> Knowledge
```

This document defines only the Event Framework.

The Event Framework lives inside the Evidence layer. It governs evidence that represents possible, suspected, reviewed, or confirmed events.

The name Event Framework remains correct because this document governs the lifecycle of event-related evidence:

- EventCandidate.
- EventTimeline.
- EventClassification.
- EventReview.
- EventValidation.
- Event promotion.

The broader Evidence and Knowledge paradigm must not force every project concept into an event.

Future Hybrid AllSky frameworks may manage non-event evidence such as:

- Sky quality.
- Observatory health.
- Weather.
- SQM.
- Seeing.
- Environmental statistics.
- Long-term equipment performance.

Those frameworks may share metadata, provenance, review, and dataset principles with the Event Framework, but they should not be incorrectly modeled as event detectors unless they produce event-like evidence.

## 2. System Context

Hybrid AllSky is organized into layered responsibilities.

### 2.1 Acquisition Layer

The acquisition layer produces frame data.

Responsibilities:

- Camera capture.
- Multi-camera coordination.
- Profile-specific camera configuration.
- Exposure control.
- Gain control.
- Capture timing.
- Runtime camera health.
- Frame identity.

The Event Framework must never directly control acquisition.

Event systems may observe acquisition metadata, but they must not change exposure, gain, capture cadence, camera selection, or scheduler behavior unless a future architecture explicitly defines an operational feedback channel.

### 2.2 Processing Layer

The processing layer transforms frames into usable scientific and operational metadata.

Responsibilities:

- Calibration.
- Debayering.
- White balance.
- Hybrid AWB.
- Metering.
- Quality score.
- Quality flags.
- Frame metadata.
- Dashboard analytics.
- Metadata health.

The Event Framework consumes this layer.

It must not duplicate frame processing logic unless a detector explicitly owns a separate analysis product.

### 2.3 Environmental Intelligence

Environmental Intelligence interprets observing conditions.

Current and future signals include:

- Sky condition.
- Cloud condition.
- Sky trend.
- Possible condensation.
- Transparency.
- Weather awareness.
- Sky quality.

The Event Framework treats environmental intelligence as context, not as event detection.

Environmental signals can explain why an event candidate may be unreliable, suppressed, promoted, or classified as environmental rather than astronomical.

### 2.4 Event Intelligence Framework

The Event Framework is the common substrate for event reasoning.

Responsibilities:

- Event candidate contract.
- Event timeline contract.
- Event classification contract.
- Event review contract.
- Validation state.
- Promotion pipeline.
- Detector contract.
- Dataset contract.
- Auditability.
- Explainability.
- Versioning.

The framework does not implement detector-specific science.

### 2.5 Event Detectors

Event detectors are independent modules that plug into the framework.

Examples:

- Meteor detector.
- RMS integration.
- Meteor count estimator.
- Satellite detector.
- Aircraft detector.
- Aurora detector.
- Lightning detector.
- Bird detector.
- Insect detector.
- Lens artifact detector.
- Unknown event detector.
- Future detectors.

Each detector must follow the same contract.

### 2.6 AI Intelligence

AI consumes the Event Framework.

AI is not the primary detector.

AI may assist with:

- Classification support.
- False positive triage.
- Review summaries.
- Observatory reports.
- Natural language queries.
- Trend interpretation.
- Training data exploration.
- Recommendation generation.

AI must not replace explainability.

AI outputs must be treated as additional evidence with provenance, confidence, model version, and review state.

## 3. Design Principles

### 3.1 Profile-First

Every event artifact must preserve camera profile identity.

Required identity context:

- `camera_id`.
- `profile_id`.
- Camera role when known.
- Camera interface when relevant.
- Profile configuration version or reference when available.

No detector may assume a single global camera.

### 3.2 Multi-Camera

The framework must support simultaneous independent cameras.

Events may be:

- Single-camera.
- Multi-camera correlated.
- Camera-specific.
- Profile-specific.
- Cross-profile.

The default assumption is isolation.

Cross-camera association must be explicit and explainable.

One physical phenomenon may produce multiple camera-specific timelines.

Those timelines must not be silently merged.

Cross-camera association creates a higher-level event relationship that references the source timelines and explains why they are believed to describe the same physical phenomenon.

Association evidence may include:

- Timestamp overlap.
- Directional or geometric consistency.
- Similar candidate reasons.
- Similar environmental context.
- External detector agreement.
- Site or node timing metadata.

### 3.3 Explainability-First

Every decision must be able to answer:

Why did you make this decision?

This applies to:

- Candidate creation.
- Candidate suppression.
- Timeline grouping.
- Classification.
- Confidence assignment.
- Review decisions.
- Validation decisions.
- Promotion decisions.

No hidden decisions are allowed.

### 3.4 Shadow-First

New algorithms begin in shadow mode.

Shadow mode means:

- Observe only.
- Persist diagnostics.
- Do not affect capture.
- Do not affect exposure.
- Do not affect gain.
- Do not affect scheduling.
- Do not affect notifications.
- Do not affect public output.

Runtime influence requires explicit promotion.

### 3.5 Conservative Promotion

Algorithms must not move directly from implementation to production.

Every detector must pass through the promotion pipeline defined in this document.

### 3.6 Deterministic Behavior

Given the same inputs, configuration, detector version, and model version, the framework should produce the same result.

Randomness must be avoided or recorded.

### 3.7 Offline Validation Before Runtime

Offline validation is mandatory before runtime enablement.

Runtime integration must not be the first place an algorithm is evaluated.

### 3.8 Reproducibility

Every event output must include enough provenance to reproduce the decision later.

Required provenance includes:

- Input frame ids.
- Input metadata.
- Detector version.
- Configuration snapshot or reference.
- Rule version.
- Model version if AI is involved.
- Runtime mode.
- Timestamp.

### 3.9 Auditability

Every event lifecycle transition must be auditable.

The framework must preserve:

- What changed.
- When it changed.
- Why it changed.
- Which component or human changed it.

### 3.10 No Hidden Decisions

Suppression, promotion, classification, and rejection must all be represented explicitly.

Silence is not an acceptable decision record.

### 3.11 Autonomous Operation with Optional Human Review

Human review is a first-class capability, but it is not a requirement for normal operation.

The system must be able to operate fully autonomously.

Manual review enriches trust, improves ground truth, and strengthens datasets, but autonomous validation policies may promote events when evidence is strong enough and the configured site/profile policy allows it.

Manual review is required only for high-risk promotion, benchmark dataset inclusion, disputed or ambiguous evidence, or cases where the configured policy explicitly requires human approval.

Automated validation must remain explainable and auditable.

## 4. Event Lifecycle

The canonical lifecycle is:

```text
Raw Frames
  -> Frame Metadata
  -> Quality Context
  -> Environmental Context
  -> Event Candidate
  -> Event Timeline
  -> Event Classification
  -> Optional Event Review
  -> Validation Gate
  -> Promotion Pipeline
  -> Runtime Detector
  -> Historical Dataset
  -> AI Training / AI Assistance
```

### 4.1 Raw Frames

Raw frames are the observational source.

They are not events.

They may produce event evidence.

### 4.2 Frame Metadata

Frame metadata provides structured context.

Examples:

- Timestamp.
- Camera id.
- Profile id.
- Exposure.
- Gain.
- Meter value.
- Target meter.
- Capture status.
- Quality score.
- Quality flags.
- Image path.

Frame metadata is the first stable layer of event reasoning.

### 4.3 Quality Context

Quality context explains whether a frame is suitable for event reasoning.

Examples:

- Nominal quality.
- Low meter.
- High meter.
- Exposure adjusting.
- Meter near edge.
- Capture error.
- Exposure max.
- Gain max.

Quality context may suppress event candidates or reduce confidence.

### 4.4 Environmental Context

Environmental context describes the sky and observing conditions.

Examples:

- Sky condition.
- Cloud condition.
- Sky trend.
- Possible condensation.
- Future transparency score.
- Future weather context.

Environmental context may explain false positives, environmental events, poor reliability, or observing limitations.

### 4.5 EventCandidate

An EventCandidate is a frame or moment that may be interesting.

It is not a classified event.

It must not imply meteor, satellite, aircraft, aurora, or any real-world event type.

Candidate requirements:

- Shadow-only by default.
- Detector-agnostic.
- Multi-camera safe.
- Profile-aware.
- Reason-coded.
- Explainable.
- Conservative.

Candidate examples:

- Brightness spike.
- Quality drop.
- Condensation onset.
- Sky condition transition.
- Unknown anomaly.

### 4.6 EventTimeline

An EventTimeline groups nearby candidates into a temporal segment.

It is not a classification.

Timeline requirements:

- Same camera/profile unless explicitly cross-camera.
- Defined start and end timestamps.
- Candidate ids.
- Reason aggregation.
- Quality summary.
- Environmental summary.
- Shadow-only by default.

### 4.7 EventClassification

EventClassification assigns an interpreted label to an EventTimeline.

Classification is separate from detection.

Required distinction:

- `unclassified`: not processed by a classifier.
- `unknown_event`: processed, but no rule matched.

Classification requirements:

- Method.
- Version.
- Confidence.
- Rules matched.
- Features used.
- Alternative labels.
- Explainability.
- Status.

### 4.8 EventReview

EventReview is the structured human or automated review layer.

It evaluates whether an event classification is plausible, useful, false positive, uncertain, or validated.

Review never mutates raw evidence.

It appends interpretation.

### 4.9 EventValidation

EventValidation records the final validation state of an event.

Validation state may be manual, automated, or hybrid.

Validation is required before an event becomes part of a trusted historical dataset.

Validation may be satisfied by a human reviewer, a deterministic validation policy, external detector agreement, cross-camera agreement, high-confidence rule-based evidence, or a configured site/profile policy.

### 4.10 Promotion Pipeline

Promotion determines whether an algorithm can move toward runtime use.

Promotion is about algorithm maturity, not individual event validity.

### 4.11 Runtime Detector

A Runtime Detector is a detector that has passed enough validation to run automatically during normal operation.

Runtime detectors may still remain shadow-only.

Operational influence is a separate promotion level.

### 4.12 Historical Dataset

The historical dataset contains reviewed and validated event records.

It must preserve true positives, false positives, uncertain cases, environmental cases, and unknown events.

### 4.13 AI Training / AI Assistance

AI modules consume validated datasets, review history, metadata, and classification history.

AI must preserve provenance and explainability.

## 5. Promotion Pipeline

Every detector must follow this pipeline.

```text
Idea
  -> Design Note
  -> Prototype
  -> Offline Test
  -> Shadow Mode
  -> Offline Validation
  -> Validation Gate
  -> Night Benchmark
  -> Regression Validation
  -> Limited Runtime Enablement
  -> Production
  -> Continuous Monitoring
```

### 5.1 Idea

An idea describes a possible detector or event signal.

It has no implementation authority.

Required:

- Problem statement.
- Expected signal.
- Expected false positives.
- Required inputs.
- Risk assessment.

### 5.2 Design Note

A design note defines the detector approach before implementation.

Required:

- Inputs.
- Outputs.
- Candidate reasons.
- Timeline behavior.
- Classification labels if any.
- Explainability format.
- Expected limitations.
- Validation plan.

### 5.3 Prototype

A prototype is allowed to be incomplete.

It must not affect runtime.

It should run on controlled data.

### 5.4 Offline Test

The detector is evaluated against synthetic and historical data.

Required:

- Positive examples.
- Negative examples.
- Edge cases.
- Malformed input cases.
- Multi-camera cases.

### 5.5 Shadow Mode

The detector runs against real metadata or frames without affecting operation.

Required:

- Diagnostics.
- Persistence.
- Failure isolation.
- No operational decisions.

### 5.6 Offline Validation

Outputs are reviewed outside runtime.

Required:

- Count of generated candidates.
- Count of timelines.
- Classification distribution.
- False positive estimate.
- Missed event examples if known.

### 5.7 Validation Gate

The validation gate determines whether detector outputs have enough evidence to move forward.

The gate may be satisfied by:

- Human review.
- Strong deterministic evidence.
- External detector agreement such as RMS.
- Cross-camera agreement.
- High-confidence rule-based evidence.
- A configured site/profile policy.

Required evidence:

- Reviewable or auditable evidence.
- Clear reasons.
- Confidence or uncertainty.
- Frame references.
- Environmental context.
- Validation policy used.
- Actor or component that satisfied the gate.

Human review remains available at this stage, but it is not mandatory for low-risk autonomous operation.

### 5.8 Night Benchmark

The detector is evaluated across complete nights.

Required:

- Clear nights.
- Cloudy nights.
- Mixed nights.
- Day/night boundary.
- Multi-camera behavior.
- Known poor data nights.

### 5.9 Regression Validation

The detector must not degrade previously validated behavior.

Required:

- Stable test corpus.
- Known false positive set.
- Known positive set.
- Version comparison.

### 5.10 Limited Runtime Enablement

The detector may run automatically in shadow mode or read-only mode.

It still must not produce notifications or operational changes unless separately approved.

### 5.11 Production

Production means the detector is trusted for its approved scope.

Production does not imply perfect accuracy.

It implies monitored, versioned, explainable, and reviewed behavior.

### 5.12 Continuous Monitoring

Every production detector must remain monitored.

Required:

- Output counts.
- Confidence distribution.
- Suppression counts.
- Failure counts.
- Drift indicators.
- Version history.

### 5.13 Detector Risk Levels

Promotion requirements become stricter as detector risk increases.

Risk levels:

- `low`: dashboard/report-only outputs with no external action.
- `medium`: counts, statistics, summaries, trend reports, or internal observatory records.
- `high`: notifications, public claims, benchmark dataset inclusion, dataset export, or any output likely to be treated as authoritative.

Low-risk detectors may rely on deterministic validation policy and monitoring after sufficient offline and shadow validation.

Medium-risk detectors require stronger regression evidence, night benchmarks, and explicit uncertainty reporting.

High-risk detectors require the strictest validation. This may include human review, external detector agreement, cross-camera agreement, curated benchmark testing, or an explicitly approved site/profile policy.

No detector may silently promote itself to a higher risk level.

## 6. Event Review Contract

An EventReview must provide enough information for a human or future AI assistant to understand and audit an event.

Required fields:

- Review id.
- Event id.
- Timeline id.
- Candidate ids.
- Camera id.
- Profile id.
- Camera role.
- Start timestamp.
- End timestamp.
- Duration.
- Frame ids.
- Image paths.
- Preview paths when available.
- Detector outputs.
- Classification label.
- Classification confidence.
- Classification method.
- Classification version.
- Rules matched.
- Alternative labels.
- Candidate reasons.
- Suppression reasons if any.
- Quality context.
- Environmental context.
- Capture context.
- Exposure/gain context.
- Detector-specific evidence.
- Human notes.
- Review state.
- Validation state.
- Reviewer identity if available.
- Review timestamp.
- Review history.
- Explainability payload.

### 6.1 Review Actor Types

Review actors may include:

- `human_reviewer`.
- `automated_validation_policy`.
- `deterministic_detector`.
- `external_detector`, such as RMS.
- `cross_camera_association`.
- `ai_assisted_reviewer`.

AI may support review, classification, explanation, and summary.

AI must not silently create ground truth.

AI-generated conclusions must remain explainable, traceable to evidence, and marked with model provenance.

### 6.2 Review State

Allowed review states should include:

- `unreviewed`.
- `needs_review`.
- `reviewed`.
- `deferred`.
- `rejected`.
- `accepted`.

### 6.3 Validation State

Allowed validation states should include:

- `unvalidated`.
- `validated_true_positive`.
- `validated_false_positive`.
- `validated_uncertain`.
- `validated_environmental`.
- `validated_artifact`.
- `validated_unknown`.

### 6.4 Review History

Review history is append-only.

Each entry should include:

- Timestamp.
- Actor.
- Previous state.
- New state.
- Reason.
- Notes.

## 7. Event Dataset Architecture

The Event Dataset is the long-term scientific memory of Hybrid AllSky.

It must contain more than successful detections.

It must preserve:

- True positives.
- False positives.
- Uncertain events.
- Environmental events.
- Lens artifacts.
- Capture failures.
- Unknown events.
- Suppressed candidates.
- Rejected classifications.

### 7.1 Dataset Units

Dataset units should include:

- Frame record.
- Candidate record.
- Timeline record.
- Classification record.
- Review record.
- Validation record.
- Detector run record.
- Dataset export record.

### 7.2 Dataset Trust Tiers

Event data should be organized into explicit trust tiers.

Suggested tiers:

- `tier_0_raw_observations`: raw frames and frame metadata without event interpretation.
- `tier_1_event_hypotheses`: shadow candidates, timelines, and unvalidated classifications.
- `tier_2_automatically_validated_events`: events promoted by deterministic or configured automated validation policy.
- `tier_3_human_reviewed_events`: events reviewed by a human actor.
- `tier_4_ground_truth_events`: events accepted as ground truth with strong provenance and review history.
- `tier_5_trusted_benchmark_dataset`: curated datasets suitable for regression validation, detector comparison, publication, or training reference.

Higher tiers must preserve links to lower-tier evidence.

Promotion between tiers must be explicit, auditable, and reversible by later review.

### 7.3 Validated Events

Validated events are trusted examples.

They must include:

- Evidence.
- Classification.
- Review state.
- Validation state.
- Provenance.
- Detector versions.
- Human review history.

### 7.4 False Positives

False positives are scientifically valuable.

They must be preserved because they train future detectors and AI modules to avoid repeated mistakes.

False positive records should include:

- Original detector output.
- Why it was false.
- Which signals were misleading.
- Environmental context.
- Correct label if known.

### 7.5 Unknown Events

Unknown events must not be discarded.

They may become useful after future detectors improve.

Unknown events should preserve all evidence and review notes.

### 7.6 Dataset Versioning

Datasets must be versioned.

Dataset version metadata should include:

- Export timestamp.
- Source date range.
- Included cameras.
- Included profiles.
- Detector versions.
- Review policy version.
- Validation policy version.

### 7.7 AI Dataset Use

AI training data should be derived only from reviewed or explicitly marked weakly supervised data.

AI datasets must preserve:

- Labels.
- Review provenance.
- Confidence.
- Ambiguity.
- False positive category.
- Environmental context.
- Detector history.

## 8. Schema and ID Governance

Long-lived scientific datasets require stable identity and schema governance.

Every persisted event object must include a `schema_version`.

Schema versions must change when persisted structure, required fields, field semantics, or validation expectations change.

### 8.1 Stable Identifiers

Stable identifiers should exist for:

- EventCandidate.
- EventTimeline.
- EventClassification.
- EventReview.
- EventValidation.
- Detector run.
- Camera.
- Profile.
- Site.
- Node.
- Dataset export.

Identifiers must remain stable across offline processing, remote processing, repeated analytics runs, and delayed classification.

### 8.2 Migration Expectations

Historical event datasets may live for years.

Schema migration rules must therefore be explicit.

Migration expectations:

- New readers should tolerate older schema versions when practical.
- Migration tools should preserve original evidence.
- Derived fields may be regenerated, but raw evidence must not be overwritten.
- Deprecated fields should remain readable until a formal migration removes them.
- Migration actions must be recorded in dataset provenance.

### 8.3 Remote and Offline Provenance

Remote or offline processors must record:

- Source node.
- Processing node.
- Input paths or object references.
- Input timestamps.
- Processing timestamp.
- Detector or classifier version.
- Configuration reference.
- Compute mode.
- Processing delay.

Delayed results must be marked as delayed and must not silently replace newer evidence without an explicit update record.

### 8.4 Stale Result Handling

Delayed processors may produce outputs after configuration, schemas, or source data have changed.

Stale results must be detectable.

Stale result records should include:

- Source evidence version.
- Current evidence version if known.
- Staleness reason.
- Whether the result was accepted, ignored, or queued for review.

## 9. Detector Contract

Every detector must conform to the same contract.

### 9.1 Detector Identity

Required:

- Detector id.
- Detector name.
- Detector version.
- Detector type.
- Maintainer.
- Runtime mode.
- Supported cameras/profiles.
- Supported input types.
- Compute expectations.
- Supported deployment modes.

### 9.2 Inputs

Detector inputs must be explicit.

Possible inputs:

- Frame metadata.
- Quality context.
- Environmental context.
- Image file.
- Raw frame.
- Candidate timeline.
- Previous frames.
- External catalog.
- RMS output.
- Weather data.
- Manual annotations.

The detector must declare which inputs are required, optional, and ignored.

### 9.3 Compute Expectations

Every detector must declare its compute expectations before promotion.

Required declarations:

- Expected CPU cost.
- Expected memory cost.
- Expected disk I/O cost.
- Expected GPU or accelerator needs if any.
- Whether it can run on Raspberry Pi 5.
- Whether it can run in realtime.
- Whether it can run delayed.
- Whether it can run offline.
- Whether it can run remotely.
- Whether it can be interrupted safely.
- Whether it can resume from partial work.
- Expected runtime per frame, timeline, or night.
- Expected storage growth.

No event capability should be abandoned merely because it is too heavy for the Raspberry Pi.

Heavy detectors must instead be designed as optional, asynchronous, offline, remote, or distributed components.

### 9.4 Outputs

Detector outputs must be structured.

Possible outputs:

- EventCandidate.
- EventTimeline.
- EventClassification.
- Detector evidence.
- Suppression reason.
- Diagnostic counters.
- Failure record.

### 9.5 Confidence

Confidence must be bounded and documented.

Confidence is not truth.

Confidence must explain:

- What increased confidence.
- What reduced confidence.
- Whether confidence is calibrated.
- Whether confidence is comparable across detectors.

### 9.6 Explainability

Detector explainability must include:

- Rules matched.
- Features used.
- Thresholds used.
- Input values.
- Alternative explanations.
- Suppression reasons.
- Uncertainty reasons.

### 9.7 Validation

Detector validation must include:

- Synthetic tests.
- Historical tests.
- Multi-camera tests.
- Negative examples.
- Regression corpus.
- Runtime shadow report.

### 9.8 Promotion

Detector promotion state must be recorded.

Allowed promotion states:

- `idea`.
- `prototype`.
- `offline_test`.
- `shadow`.
- `offline_validated`.
- `validation_gate`.
- `night_benchmark`.
- `regression_validated`.
- `limited_runtime`.
- `production`.
- `deprecated`.

### 9.9 Regression

Every detector must have regression expectations before production.

Regression checks should include:

- Candidate count stability.
- False positive drift.
- Missed known events.
- Runtime failure rate.
- Performance cost.
- Multi-camera isolation.

### 9.10 Versioning

Any change that can alter detector output requires a version change.

Versioned components:

- Code.
- Rules.
- Thresholds.
- Model files.
- External catalogs.
- Configuration defaults.

## 10. RMS Integration Contract

RMS is a detector provider, not the Event Framework.

RMS integration must map RMS outputs into the common contracts.

RMS must provide or be wrapped to provide:

- Candidate ids.
- Timeline ids.
- Frame references.
- Meteor-specific evidence.
- Confidence.
- Detector version.
- RMS configuration.
- Explainability.
- Failure records.

The framework must not assume RMS is always present.

The framework must not make meteor-specific concepts mandatory for non-meteor detectors.

## 11. AI Contract

AI integrates after the Event Framework, not before it.

AI consumes:

- Validated events.
- Reviewed events.
- False positives.
- Unknown events.
- Candidate timelines.
- Metadata.
- Environmental context.
- Classification history.
- Detector diagnostics.
- Human review notes.

AI may produce:

- Suggested labels.
- Summary text.
- Anomaly descriptions.
- Review assistance.
- False positive explanations.
- Search and query answers.
- Recommendations.

AI must not:

- Replace detector explainability.
- Hide uncertainty.
- Mutate historical evidence.
- Promote events without provenance.
- Override human validation without a recorded decision.

### 11.1 AI Output Requirements

Every AI output must include:

- Model id.
- Model version.
- Prompt or task version when applicable.
- Input references.
- Output timestamp.
- Confidence or uncertainty description.
- Explanation.
- Review state.

### 11.2 AI and Event Detection

AI may assist event interpretation.

AI is not the primary event detection architecture.

Detection should remain reproducible and explainable through deterministic metadata, detectors, rules, RMS outputs, or reviewed datasets.

## 12. Compute Architecture and Deployment Modes

The Raspberry Pi 5 remains the preferred acquisition-first node.

It is responsible for reliable camera operation, profile-specific capture, exposure/gain control, metadata persistence, and basic operational observability.

The Event Framework must not assume that all processing runs on the acquisition device.

The framework must support capabilities that are too expensive for the Raspberry Pi by making them optional, asynchronous, delayed, offline, remote, or distributed.

### 12.1 Acquisition-First Principle

Acquisition reliability has priority over event intelligence.

Heavy processing must never compromise:

- Capture reliability.
- Camera health.
- Exposure/gain control.
- Metadata persistence.
- Image saving.
- Basic dashboard availability.

If compute resources are constrained, event processing must degrade first.

Capture must continue.

### 12.2 Standalone Raspberry Pi Mode

Standalone mode is the baseline deployment.

In this mode, the Raspberry Pi runs:

- Acquisition.
- Basic processing.
- Metadata generation.
- Quality scoring.
- Environmental diagnostics.
- Lightweight event framework components.
- Dashboard.

Detectors running in this mode must declare that they are suitable for Pi-local execution.

Heavy detectors may be disabled by default in standalone mode.

### 12.3 Offline Processing Mode

Offline mode processes already captured data.

It may run on the Raspberry Pi, a workstation, a server, or another environment.

Offline processing is appropriate for:

- Historical dataset analysis.
- Detector development.
- Regression validation.
- Night benchmarks.
- AI-assisted review.
- Expensive classification.

Offline mode must preserve reproducibility by recording input paths, versions, configuration, and timestamps.

### 12.4 Raspberry Pi Plus External Processing Node

Hybrid deployments may use the Raspberry Pi as the acquisition node and an external machine as the processing node.

The external node may run:

- Heavy event detectors.
- RMS.
- AI classification.
- Cross-night analytics.
- Dataset exports.
- Review tooling.

The Raspberry Pi must remain functional if the external node is offline.

Event outputs may arrive late.

Delayed results must be marked with processing timestamps and source node identity.

### 12.5 Remote Processing Mode

Remote processing may occur on a server or cloud-like host.

Remote mode must be optional.

Remote mode must not be required for basic observatory operation.

Remote processing should use explicit transfer, queue, or sync mechanisms with auditable state.

Failures must be visible but non-fatal to acquisition.

### 12.6 Distributed Observatory Mode

Future deployments may include multiple acquisition nodes.

Distributed mode must support:

- Multiple Raspberry Pi acquisition nodes.
- Multiple camera profiles.
- Site identity.
- Node identity.
- Clock synchronization metadata.
- Cross-node event correlation.
- Delayed cross-node classification.

No detector may assume all frames come from one physical system.

### 12.7 Compute Mode Declaration

Every detector must declare supported compute modes.

Allowed compute modes:

- `realtime`.
- `near_realtime`.
- `delayed`.
- `offline`.
- `remote`.
- `distributed`.

The declaration must state whether the mode is required, optional, experimental, or unsupported.

### 12.8 Asynchronous Processing

Heavy processing should be asynchronous by default.

Asynchronous detectors must define:

- Input queue or input discovery mechanism.
- Output persistence path.
- Retry behavior.
- Partial failure behavior.
- Idempotency behavior.
- Maximum expected delay.
- How duplicate work is avoided.

### 12.9 Compute Failure Isolation

Compute failures must not affect acquisition.

If heavy processing fails:

- Capture continues.
- Metadata continues.
- Dashboard indicates delayed or failed processing.
- Diagnostics record the failure.
- No event evidence is silently discarded.

### 12.10 Capability Preservation

The framework must not reject a future scientific capability because it is too heavy for the Raspberry Pi.

Instead, the capability must be assigned an appropriate compute mode.

Examples:

- Lightweight metadata rule: Pi realtime or near-realtime.
- RMS meteor analysis: offline, delayed, or external node.
- AI classification: remote or offline.
- Cross-camera/cross-node correlation: delayed or distributed.
- Dataset training: offline.

## 13. Operational Modes

The framework supports multiple operational modes.

### 13.1 Offline

Offline mode reads historical data and produces diagnostics or outputs without touching runtime.

### 13.2 Shadow

Shadow mode runs near runtime but has no operational effect.

### 13.3 Read-Only

Read-only mode exposes results in dashboards or reports.

### 13.4 Advisory

Advisory mode may produce recommendations but not execute them.

### 13.5 Operational

Operational mode may affect notifications, publishing, or future control loops.

Operational mode requires explicit promotion and monitoring.

## 14. Failure Handling

Event systems must fail closed and isolated.

Failures must not:

- Stop capture.
- Stop image processing.
- Stop metadata persistence.
- Change exposure.
- Change gain.
- Block dashboard loading.

Failures must:

- Be logged.
- Be counted.
- Be visible in diagnostics.
- Preserve partial valid outputs when safe.

## 15. Suppression Architecture

Suppression is a first-class decision.

Suppression occurs when a possible candidate is intentionally not emitted.

Suppression must be measurable.

Suppression records should include:

- Suppression reason.
- Trigger that would have fired.
- Quality context.
- Environmental context.
- Detector id.
- Detector version.
- Timestamp.
- Camera id.
- Profile id.

Suppression examples:

- Exposure adjusting.
- Meter near edge.
- Capture error.
- Cloud interference.
- Condensation possible.
- Rate limit.
- Duplicate event.
- Insufficient evidence.

Suppression analytics are required before production promotion.

## 16. Reproducibility Requirements

Every event artifact should be reproducible from stored inputs.

Minimum reproducibility context:

- Source frames.
- Source metadata.
- Candidate rules.
- Timeline grouping config.
- Classification rules.
- Detector version.
- Configuration.
- Environment context.
- Quality context.
- Timestamp.

If a result cannot be reproduced, it must be marked as non-reproducible.

## 17. Audit Requirements

Every major event artifact must answer:

- What produced this?
- When was it produced?
- Which inputs were used?
- Which rules matched?
- Which rules did not match?
- What was suppressed?
- What confidence was assigned?
- What changed after review?
- Who or what changed it?
- Which version of the algorithm was used?

## 18. Long-Term Architecture Direction

The Event Framework should evolve toward:

- Stable event contracts.
- Reviewed event datasets.
- Detector-specific plugins.
- Offline benchmark suites.
- Runtime shadow dashboards.
- Cross-camera correlation.
- Human review workflow.
- AI-assisted review.
- Observatory-level nightly reports.
- Natural language observatory queries.

The framework must remain conservative.

It must prefer missing a speculative claim over producing an unexplained false certainty.

## 19. Non-Goals

The Event Framework does not:

- Define meteor detection algorithms.
- Implement RMS.
- Classify satellites.
- Classify aircraft.
- Detect aurora.
- Detect lightning.
- Detect birds or insects.
- Perform AI classification.
- Control capture.
- Control exposure.
- Control gain.
- Send notifications by default.
- Replace human review where human review is required by policy.

These capabilities may be implemented by future detectors or modules that comply with this architecture.

## 20. Architectural Summary

The Event Framework is the layer that turns AllSky observations into auditable scientific knowledge.

It provides the contracts, lifecycle, review process, validation process, and promotion discipline needed for long-term evolution.

Its central promise is simple:

Every event decision must be explainable, reproducible, reviewable, and safe.
