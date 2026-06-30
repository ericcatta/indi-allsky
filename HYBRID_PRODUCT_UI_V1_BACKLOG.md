# Hybrid Product UI v1 Backlog

## Purpose

This backlog captures the work needed after completing the Product UI v1
skeleton.

It intentionally separates immediate consolidation work from future real-data
integration and v2 product ideas.

The v1 architecture remains frozen:

Now -> Highlights -> Moment -> Output -> Sky Cycle -> Library -> Observatory -> Settings -> Developer / Engine Room

## Must Fix Before Real Data

- Complete a deliberate product navigation pass across the frozen v1 flow.
- Reduce contract-scaffolding language in Basic-facing surfaces.
- Define common presentation rules for product status, data status, confidence,
  source trust, and safety boundaries.
- Confirm every surface clearly distinguishes real data from fake/static
  placeholders.
- Make Highlight, Moment, and Output visually and semantically distinct before
  detector or media data is connected.
- Decide how prototype links represent object targets while IDs are still fake.
- Define the first allowed real provider for each surface before wiring any
  runtime data.
- Keep disabled or future actions visible only as metadata, never as controls.
- Preserve the no-preview, no-filesystem, no-media-read boundary until each
  media path has a dedicated safety review.
- Add a single source of truth for product navigation labels if link growth
  continues.

## Nice Before Real Data

- Extract shared read-only product card/includes if duplication starts to slow
  iteration.
- Add a product navigation map document for Now, Highlights, Moment, Output,
  Sky Cycle, Library, Observatory, Settings, and Developer.
- Improve empty states so they are useful to users, not only honest to
  developers.
- Normalize "back to" and "continue to" language across surfaces.
- Add a consistent visual treatment for not evaluated, future backend contract,
  placeholder, warning, and blocked states.
- Revisit all initial scores after the skeleton is seen as a single flow.
- Add short product-oriented descriptions to ownership entries if tooling needs
  to summarize product surfaces.

## Real Data Phase

- Now: keep latest frame metadata and current phase bounded; do not add preview
  URLs until media safety is reviewed.
- Highlights: connect real suggestions only after explainable evidence and
  source trust contracts exist.
- Moment: start with bounded detector/evidence metadata, not media reads.
- Output: start with metadata-only generated-output summaries, not preview,
  download, share, or regeneration.
- Sky Cycle: connect bounded cycle metadata only after phase and source
  contracts are reviewed.
- Library: begin with paginated metadata indexes only; no filesystem indexing
  or broad search scans.
- Observatory: connect cached or cheap health summaries only; no live hardware,
  camera, network, or filesystem probes in request paths.
- Settings: remain read-only until safe-action and Flask integration blockers
  are resolved.

## v2 Ideas

- Revisit whether Highlights should feel like a page, layer, feed, or attention
  briefing.
- Explore an Attention Briefing v2 that combines Now and Highlights without
  changing the v1 skeleton prematurely.
- Consider replacing "Detail" labels with product-facing object names.
- Consider a unified object-detail shell for Moment, Output, and future Source
  detail.
- Add favorites, tags, saved searches, and user curation after Library has real
  retrieval contracts.
- Create a formal Product Design System for cards, status, evidence, lineage,
  warnings, read-only states, and future safe-action states.
- Consider a richer frontend only if it remains RPi5-first and progressively
  enhanced.

## Do Not Do Next

- Do not add more primary product surfaces.
- Do not wire broad DB queries.
- Do not add real previews, downloads, shares, or media generation.
- Do not add filesystem scans or RAW/FITS reads.
- Do not add mutative actions or execute endpoints.
- Do not turn Library into a generic gallery.
- Do not turn Observatory into Developer or Settings.
- Do not redesign the frozen v1 architecture until the existing skeleton is
  reviewed as a whole.
