---
created: 2026-04-13
last_edited: 2026-04-13
version: 1.0
provenance: con_HfUUximXBPXjU7iq
---

# Target File Structures

Use this file to keep output grounded in the actual file shape of the requested target. The skill should not emit vague "here is some code" output. It should match one of these structures.

## 1. Standalone HTML

Use when the user wants a single drop-in file.

Expected structure:

```text
landing-page/
  index.html
```

Rules:

- one self-contained `index.html`
- include `<meta charset>` and `<meta name="viewport">`
- inline any custom CSS in `<style>`
- inline any small interaction logic in `<script>`
- avoid extra asset assumptions unless the user provides them

Best for:

- quick demos
- shareable mockups
- static marketing pages

## 2. React + Tailwind

Use when the user wants a component that can slot into a normal React app.

Expected structure:

```text
src/
  App.tsx
  main.tsx
  styles.css
```

Minimum deliverable:

- primary page component, usually `App.tsx`
- note any extra requirements such as font loading or asset placement

Rules:

- write a real React component, not pseudo-JSX
- keep styling in Tailwind classes unless the target explicitly uses CSS files
- only add interactivity when the brief needs it

## 3. Next.js App Router

Use when the target is a Next.js site using the App Router.

Expected structure:

```text
app/
  page.tsx
  layout.tsx
components/
  ...
public/
  ...
```

Minimum deliverable:

- `app/page.tsx`
- any supporting component files only if the page genuinely benefits from decomposition

Rules:

- default to server components
- add `"use client"` only when interactivity requires it
- mention any expected `next/font` or `next/image` usage if relevant

## 4. Zo.space Page Route

Use when the user wants a Zo.space landing page.

Expected structure:

```text
route: /your-path
type: page
default export React component
```

Minimum deliverable:

- one default-export React component suitable for the route file body

Rules:

- write a single-file page route unless a split is explicitly requested
- use Tailwind classes
- use `lucide-react` for icons if icons are needed
- keep any asset references explicit

## 5. Template Capture

Use when the user wants to preserve a finished direction as a reusable template.

Expected structure:

```text
templates/
  your-template.yaml
```

Rules:

- start from `templates/_TEMPLATE.yaml`
- fill every required field
- keep section variants concrete
- write `style_notes` with enough specificity that the template is reusable

## Output Discipline

For every target, return:

- the selected target name
- the expected file path or route path
- any assumptions about fonts, assets, or framework setup

If the requested target does not match one of the structures above, define the structure explicitly before generating code.
