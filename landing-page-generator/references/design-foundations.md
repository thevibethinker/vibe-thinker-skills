---
created: 2026-04-13
last_edited: 2026-04-13
version: 1.0
provenance: con_HfUUximXBPXjU7iq
---

# Design Foundations

This file contains the design guidance the standalone landing-page skill needs in order to operate without a dependency on another frontend skill.

## Brief Capture

Before deciding anything visual, lock these inputs:

- audience
- offer
- primary action
- proof
- emotional tone
- target platform

Do not pretend a codebase alone can answer those questions. If the brief is thin, ask. If speed matters more than precision, state your assumptions and move.

## Design Direction

Pick one clear point of view and commit to it. Good landing pages feel like they were directed, not assembled.

Useful direction labels:

- editorial authority
- premium restraint
- warm expertise
- technical precision
- playful conviction
- bold challenger

Each direction should answer:

- what emotion should a visitor feel first
- what one thing should be most memorable
- what should visually dominate the first viewport

## Typography

Make typography carry the page before decoration does.

Rules:

- use at most two type families
- create a visible hierarchy between display, heading, subheading, and body
- prefer left alignment for longer text blocks
- keep body line length readable
- use weight and spacing with intention, not random defaults

Avoid:

- generic system-font landing pages unless the concept genuinely calls for restraint
- weak hierarchy where every heading feels the same size
- decorative display faces in dense body copy

## Color

Treat color like a system, not a pile of accents.

Rules:

- choose one dominant hue family
- add one secondary support color only if it earns its place
- use accent color sparingly for CTA, active states, or a specific proof element
- tint neutrals toward the brand mood instead of relying on flat default grays

Avoid:

- blue-purple startup gradients by reflex
- gray text on colored backgrounds
- accent color sprayed across every component

## Layout

Landing pages need rhythm more than symmetry.

Rules:

- vary density across sections
- create at least one strong focal point above the fold
- let some sections breathe and keep others tight
- use asymmetry deliberately when it improves attention flow
- let the story determine section order

Avoid:

- equal-sized cards everywhere
- centering every headline and paragraph
- repeating the same section shell with different copy

## Proof

Proof is part of the design, not an afterthought.

Possible proof surfaces:

- customer logos
- quantified outcomes
- named testimonials
- screenshots
- process timeline
- founder credibility
- product mechanics

Pick the proof form that fits the offer. A consulting page and a product page should not prove trust in the same way.

## Motion

Use motion to support comprehension and emphasis.

Rules:

- favor one or two meaningful moments over constant animation
- entrances should feel controlled, not showy
- interactive states should communicate responsiveness
- honor reduced-motion preferences when you have implementation control

Avoid:

- animating everything on scroll
- bounce and gimmick easing
- long fades that delay access to content

## Copy

Copy should sound specific and human.

Rules:

- make the promise concrete
- avoid inflated marketing language
- keep CTA labels action-specific
- remove any sentence that merely repeats the heading

Avoid:

- "revolutionize your workflow"
- "cutting-edge"
- "seamless integration"
- "get started" when a more specific CTA is possible

## Responsiveness

Mobile is a redesign, not a shrink.

Rules:

- verify hierarchy on small screens
- keep interactive targets touch-friendly
- shorten or re-stack proof modules when needed
- preserve the core story without amputating key sections

## Final Taste Test

Before shipping, ask:

- does this feel like a real design direction
- would this still work if the copy changed
- is there one memorable choice on the page
- does the page look authored rather than auto-filled
