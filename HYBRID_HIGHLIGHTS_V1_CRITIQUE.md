# Hybrid Highlights v1 Critique

## Purpose

This is a product critique, not an implementation review.

It evaluates whether Highlights v1 actually expresses the idea of a curated
attention object, and whether the product should continue implementing it or
pause for more design work.

## Real Score

Highlights v1 score: 5.8/10.

The concept is strong.

The implementation is safe.

The product experience is not there yet.

The prototype is a good technical contract and a weak attention experience. It
proves that a sanitized Highlights view model can exist, but it does not yet
prove that Highlights feels like the center of Hybrid AllSky.

## What Works

Highlights v1 gets several important things right:

- it formalizes Highlight as a first-class product surface;
- it does not confuse Highlight with a mutative action;
- it separates Highlight from Favorite in the copy;
- it supports multiple target kinds: Moment, Output, Sky Cycle, Observatory
  issue;
- it carries selection reason, confidence, evidence, source trust, related
  output status, and review status;
- it is read-only and RPi5-safe;
- it avoids detector, database, filesystem, RAW/FITS, media, download, share,
  and action coupling;
- it is testable and contract-first;
- it makes "Hybrid suggests; user decides" visible;
- it exposes the right future risk: source trust must exist before Highlights
  can be trusted.

That is a solid foundation.

But it is still a foundation.

## What Does Not Work

### It Does Not Yet Feel Like Attention

Highlights should feel like:

> These are the few things worth your time.

The current page feels more like:

> Here are four example records from a new contract.

That is a big difference.

Attention is selective, ranked, opinionated, and calm. The current prototype is
enumerative. It shows examples, but it does not create a strong sense of
priority.

### It Is Too Contract-Driven

The page exposes contract thinking too visibly:

- contract name;
- contract version;
- source;
- placeholder status;
- allowed origins;
- safe action counts;
- repeated "pending backend contract" language.

Those are honest, but they make the surface feel like Developer mode. The
prototype is technically correct, but product-thin.

### It Is Too Symmetric

Every card has similar visual weight.

But Highlights should not be symmetric. A meteor candidate, an all-clear cycle,
a storage warning, and a generated timelapse should not feel equivalent.

The product should communicate:

- primary attention;
- secondary attention;
- operational warning;
- background suggestion;
- dismissed/noise.

The current model has the metadata for this direction, but the experience does
not yet express it.

### It Does Not Yet Prove Now -> Highlights

The Now link is technically natural.

The mental flow is not proven.

A user clicking Highlights from Now should feel:

> Ah, this is what Hybrid thinks I should inspect.

Today they would feel:

> This is a prototype list of possible future things.

That is acceptable for v1, but not sufficient before connecting real data.

### It Risks Becoming A Gallery

The generated timelapse candidate is useful, but without stronger rules
Highlights could drift toward "nice media list".

If Highlights becomes a gallery, it fails.

Highlights must prioritize why something matters, not merely whether it looks
good.

### It Risks Becoming Notifications 2.0

The observatory issue Highlight is correct in principle.

But if every warning becomes a Highlight, the surface becomes notification
noise.

Highlights should not be a dumping ground for alerts. Only issues that affect
trust, source preservation, output validity, or user attention deserve
promotion.

### It Risks Becoming AI Theater

The future AI clear-window example is useful as a placeholder, but dangerous.

If AI-generated Highlights are not explainable, reversible, and clearly marked
as suggestions, they will weaken trust.

Highlights must not become:

> The system says this is interesting.

They must become:

> The system thinks this is interesting because of these bounded signals, and
> you can accept or reject that.

## The Biggest Risk

The biggest risk is that Highlights becomes a bucket of "interesting things"
instead of a disciplined attention layer.

If that happens, Hybrid will have added a new domain object but not improved the
morning experience.

The product would still ask the user to interpret a list.

The real goal is to reduce interpretation load.

## Where The Prototype Betrays The Concept

Highlights v1 says that Highlights are curated attention objects, but the page
does not yet feel curated.

It betrays the concept in five ways:

1. It shows too much scaffolding language.
2. It gives all placeholder Highlights similar importance.
3. It does not create a clear "start here" moment.
4. It treats review queue and selection policy as peer content rather than
   background trust.
5. It still feels like a product contract rendered on screen.

None of these are fatal.

They are a warning: do not connect real data until the experience model is
clearer.

## How Highlights Should Feel

Highlights should feel like a calm attention briefing.

Not:

- gallery;
- admin panel;
- notification inbox;
- detector output table;
- AI recommendation feed;
- debug contract viewer.

It should feel like:

- the short list of what mattered;
- the product's best explanation of why it mattered;
- the fastest path to evidence, source, output, or issue detail;
- a trustworthy filter between continuous capture and human attention.

The user should immediately understand:

- this is the most important thing;
- this is visual/shareable;
- this is scientifically interesting;
- this affects trust;
- this is only a suggestion;
- this can be ignored or confirmed later.

The emotional shape should be:

> Hybrid looked through the cycle for me. Here is what deserves my time.

## Criteria Review

### 1. Is It Really A Curated Attention Object?

Partially.

The data model says yes. The experience says "prototype list".

Score: 6/10.

### 2. Different From Moment?

Conceptually yes.

Visually not strongly enough. The meteor card still reads like a Moment teaser.

Score: 7/10.

### 3. Different From Output?

Conceptually yes.

The generated timelapse card risks becoming an Output card with extra words.

Score: 6.5/10.

### 4. Different From Favorite?

Mostly yes.

The copy explicitly explains the difference, but Favorite is still represented
as status text rather than a separate user decision layer.

Score: 7/10.

### 5. Different From Gallery?

Not proven.

Because there is no real media yet, it avoids being a gallery. But once media is
added, this will be fragile.

Score: 5.5/10.

### 6. Explains Why Something Merits Attention?

Structurally yes.

Emotionally weak. The reasons are placeholders and repeat contract language.

Score: 6/10.

### 7. Is Now -> Highlights Natural?

Yes in architecture.

Not yet in experience.

Score: 6.5/10.

### 8. Helps In First 30 Seconds?

Not yet.

It helps a product architect. It does not yet help an astrophotographer.

Score: 5/10.

### 9. Tone Scientific/Astrophotographic?

Mostly yes.

It avoids poetic and consumer language. It is slightly too technical.

Score: 7/10.

### 10. Product Or Admin Panel?

Leaning product, but still contract/admin-adjacent.

Score: 6/10.

### 11. Too Contract-Driven?

Yes.

This is the core weakness.

Score: 4.5/10.

### 12. Too Fake/Static?

Yes, but intentionally.

The problem is not fake data. The problem is that the fake state dominates the
experience.

Score: 5/10.

## What Not To Implement Yet

Do not implement:

- real detector Highlight candidates;
- AI ranking;
- user confirm/favorite/ignore/archive actions;
- media thumbnails;
- preview URLs;
- source lineage traversal;
- output share/download;
- notification routing;
- Library integration;
- automatic suppression/ranking logic;
- any mutative safe action UI.

These would make the prototype feel more real while the experience model is
still underdesigned.

## What To Do Before More Code

Before the next implementation mission, design the Highlight experience model.

Specifically define:

- what the first 30 seconds of Highlights should feel like;
- how many Highlights should be shown by default;
- how primary vs secondary attention is expressed;
- how operational warnings differ from visual/science Highlights;
- how an all-clear cycle becomes useful without becoming noise;
- how AI suggestions are marked;
- how user decisions appear without implementing actions yet;
- how Highlight cards avoid looking like gallery cards;
- how Source Trust appears without making every card dense;
- how Highlights connects to Now without becoming a second dashboard.

This should be a Product Design mission, not code.

## Recommendation

Recommendation: stop implementation and design user journeys.

Do not harden the contract next.

The contract is already strong enough for v1. More fields will make it more
complete technically and less clear experientially.

The next mission should be:

> Design the Highlights first-30-seconds experience.

It should answer:

- what does the user see first;
- what is the primary Highlight;
- how does the user know why it matters;
- how does the user distinguish Moment, Output, Observatory issue, and
  all-clear Highlight;
- what should never be shown in Basic;
- what is deferred to detail pages;
- what makes the page feel like product intelligence rather than a contract
  viewer.

## Final Verdict

Highlights is absolutely the right concept.

Highlights v1 is not yet the right product experience.

It was not a mistake to implement it, because it made the gap visible. But it
would be a mistake to keep expanding it as code before redesigning the
experience.

The product needs less schema now and more taste.
