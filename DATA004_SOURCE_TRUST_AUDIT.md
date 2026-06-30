# DATA004 - Source Trust Summary Audit

## Verdict

GO WITH GUARDS.

Hybrid can expose a first Source Trust Summary using bounded database metadata only. It cannot yet prove filesystem preservation, RAW/FITS readability, or output-to-source lineage.

## Product Question

The summary must answer, cautiously:

- do we have source metadata behind the latest observations?
- do RAW/FITS source records exist for the current camera?
- are generated outputs backed by verified lineage?
- what should the user trust, and what remains unknown?

## Candidate Sources

### Latest frame metadata

Location: `IndiAllSkyDbImageTable`, already integrated through DATA001.

Pros:

- camera-scoped;
- bounded latest-row query already implemented;
- provides latest frame evidence.

Cons:

- it is the display/image metadata, not source preservation;
- does not prove RAW/FITS exists.

Decision: use as supporting evidence only.

### Generated output metadata

Location: DATA002 generated-output table descriptors.

Pros:

- proves derived outputs exist;
- metadata-only and bounded.

Cons:

- no source lineage relationship is connected yet;
- output existence does not prove original source preservation.

Decision: do not use as trust proof in DATA004.

### FITS source metadata

Location: `IndiAllSkyDbFitsImageTable`.

Pros:

- dedicated source table;
- camera-scoped;
- indexed by `createDate`;
- metadata fields can be allowlisted.

Cons:

- filename/path/URL fields exist and must be forbidden;
- row existence does not prove file presence without filesystem verification.

Decision: allowed.

### RAW source metadata

Location: `IndiAllSkyDbRawImageTable`.

Pros:

- dedicated source table;
- camera-scoped;
- indexed by `createDate`;
- metadata fields can be allowlisted.

Cons:

- filename/path/URL fields exist and must be forbidden;
- row existence does not prove file presence without filesystem verification.

Decision: allowed.

### Existing media/source helpers

Location: file/media helpers, upload helpers, existing URL helpers.

Decision: forbidden for DATA004 because they can expose filenames, paths, URLs, storage keys, thumbnails, or filesystem behavior.

## Allowed Metadata Fields

Allowed from RAW/FITS source rows:

- `id`
- `camera_id`
- `createDate` as timestamp label
- `dayDate`
- `night`
- `uploaded`
- `exposure`
- `gain`
- `binmode`
- `fileSize`
- `width`
- `height`

Derived fields:

- `source_type`
- `source_label`

## Forbidden Fields and Behaviors

Always forbidden:

- `filename`
- path or relative path;
- URL;
- `remote_url`;
- `s3_key`;
- `thumbnail_uuid`;
- raw ORM row;
- raw JSON `data`;
- filesystem helpers;
- media helpers;
- preview/download/share helpers;
- `exists()`;
- `stat()`;
- `open()`;
- RAW/FITS reads.

## Bounded Query Strategy

For each allowed source table:

```text
SELECT allowlisted metadata
FROM fitsimage/rawimage
WHERE camera_id = current_camera_id
ORDER BY createDate DESC
LIMIT 1
```

Implementation may use descriptor-injected query objects. The repository must still call `limit(1).first()` per descriptor.

## Risk Audit

- Row existence is not file existence.
- RAW/FITS metadata may be stale.
- FITS and RAW coverage may differ by configuration.
- There is no output-to-source lineage yet.
- Camera context may be missing.
- One descriptor can fail while another succeeds.
- Product UI must not imply scientific source verification.

## Integration Scope

DATA004 integrates only Now.

Moment Detail and Output Detail remain static/fake because identifier-specific source lineage does not exist yet. Observatory is intentionally excluded to avoid turning source trust into a health dashboard.

## Stop Conditions

Stop or fallback if implementation requires:

- filesystem checks;
- source file reads;
- preview/media access;
- output lineage claims;
- unbounded queries;
- raw helper reuse;
- path/filename/URL exposure.
