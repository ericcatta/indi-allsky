# Release Candidate Cleanup Execution

This document records the conservative cleanup executed after
`RELEASE_CANDIDATE_CLEANUP_AUDIT.md`.

The cleanup intentionally avoids runtime changes. No routes, templates, Product
UI builders, DATA integrations, Classic surfaces, public routes, sync/action
APIs, JavaScript, CSS, or application behavior were changed.

## What Was Cleaned

Local Python bytecode/cache artifacts were removed from the working tree:

- `__pycache__/` directories;
- `*.pyc` files;
- Python bytecode under application, testing, misc, examples, tools, service,
  and migration folders.

Before cleanup:

- `351` Python bytecode files were present locally;
- `31` `__pycache__` directories were present locally.

After cleanup:

- `0` Python bytecode files remain;
- `0` `__pycache__` directories remain.

These files were not tracked by git, so the cleanup does not change source,
runtime behavior, or release logic. It only removes local generated artifacts.

## What Was Not Touched

The following areas were intentionally left intact:

- Classic routes and templates;
- public/latest/media routes;
- sync/action API routes;
- Modern Product UI routes and templates;
- Product UI builders and validators;
- DATA001-DATA006 adapters/providers/wiring;
- media generation code;
- filesystem/storage helpers;
- camera, sensor, device, filetransfer, and processing modules;
- JavaScript and CSS assets;
- ownership maps;
- settings pages and settings inventory tooling;
- tests and experimental scripts;
- service/install/docker files.

## Documentation Archiving Decision

No documents were moved in this cleanup pass.

The audit identified many documents that are good candidates for future
archiving, especially:

- DATA001-DATA006 discovery/audit/integration/review documents;
- Product UI process reviews;
- older roadmap and porting documents;
- historical Modern Admin planning documents.

They were not moved now because:

- many documents still provide useful Alpha context;
- references between documents have not been fully audited;
- moving dozens of files before the Raspberry pull would create unnecessary
  churn;
- archiving should be done with an index and link-update pass, not as an
  incidental cleanup.

Classification: safe to archive later, not urgent before the first Alpha pull.

## Why This Cleanup Is Conservative

The Release Candidate audit found that most apparent cleanup targets are not
safe deletion targets yet.

Static analysis found route/API/template/asset candidates, but those include:

- direct user routes;
- public bookmarked routes;
- external sync/action APIs;
- Classic fallback behavior;
- dynamically referenced static assets;
- Modern wrappers over legacy tools.

Deleting them before Alpha would risk breaking compatibility without improving
the Product UI.

The only clearly safe cleanup before Alpha was local bytecode/cache removal.

## What Remains For After Alpha

Recommended post-Alpha cleanup sequence:

1. Documentation archive pass
   - create `docs/archive/phase2-data/`;
   - move DATA process documents;
   - create an archive index;
   - update canonical references.

2. Ownership map reconciliation
   - reduce ownership mismatches;
   - reduce undeclared inventory items;
   - keep behavior unchanged.

3. Static asset verification
   - verify DataTables, PhotoSwipe, and VirtualSky orphan candidates;
   - archive demo/test assets only after dynamic usage checks.

4. Experiment archive pass
   - review `testing/benchmark`, `testing/image`, `testing/net`,
     `testing/gpio`, `testing/astrometrics`;
   - review `examples/DENOISE PR TEST ENVIRONMENT`;
   - archive only after detector/denoise direction is decided.

5. Classic separation planning
   - classify Classic routes by dependency;
   - preserve public/latest/media/sync/action compatibility;
   - remove nothing until replacement behavior is verified.

## Verification Intent

This cleanup should be validated with the normal Product UI safety checks:

- Product view model tests;
- Hybrid UI inventory;
- Python compile checks;
- ownership map JSON validation;
- whitespace/diff checks;
- clean repository status.

Any regenerated cache from verification commands remains a local generated
artifact and should not be committed.
