# Vibe Thinker Skills

Standalone, shareable skills for [Zo Computer](https://zo.computer).

This repo is the canonical home for Vibe Thinker's portable skills — the ones that can be installed and used independently without depending on private workspace infrastructure or internal orchestration systems.

## Installation

Install any skill into your Zo workspace:

```bash
slug="<skill-slug>"; dest="Skills"; repo="https://github.com/thevibethinker/vibe-thinker-skills/archive/refs/heads/main.tar.gz"; archive_root="vibe-thinker-skills-main"; mkdir -p "$dest" && curl -L "$repo" | tar -xz -C "$dest" --strip-components=1 "$archive_root/$slug"
```

Or clone the full collection:

```bash
git clone https://github.com/thevibethinker/vibe-thinker-skills.git
```

## Included Skills (29)

| Skill | Description |
|-------|-------------|
| [booking-metadata-calendar](./booking-metadata-calendar/) | Parse booking requests into structured metadata and calendar-ready payloads. |
| [branded-pdf](./branded-pdf/) | Generate clean, branded PDFs from markdown. |
| [claude-code-window-primer](./claude-code-window-primer/) | Prime Claude Code usage windows so resets land during useful work hours. |
| [close](./close/) | Universal close skill. Just say "close" and it auto-routes to the right close skill (thread-close, drop-close, or build-close) based on SESSION_STATE context. |
| [debono-thinking-hats](./debono-thinking-hats/) | Portable Six Thinking Hats persona system for structured parallel thinking. |
| [drop-close](./drop-close/) | Close Pulse worker (Drop) threads. Writes structured deposit JSON for orchestrator review. Does NOT commit - that's the orchestrator's job. For normal threads use thread-close. For post-build synthesis use build-close. |
| [fillout-survey-monitor](./fillout-survey-monitor/) | Automated monitoring of Fillout survey changes with intelligent refresh triggering. |
| [frontend](./frontend/) | Generate high-quality landing pages with anti-slop guardrails. |
| [frontend-design](./frontend-design/) | Create polished, intentional frontend interfaces with strong visual quality. |
| [frontend-design-anthropic](./frontend-design-anthropic/) | Imported frontend design skill focused on high-quality interface work. |
| [ga4-analytics](./ga4-analytics/) | Pull Google Analytics 4 traffic stats for a website with configurable reporting windows and breakdowns. |
| [gamma](./gamma/) | Generate presentations, webpages, and social content using Gamma's API. |
| [landing-page-generator](./landing-page-generator/) | Self-contained landing-page generator with bundled design foundations, anti-slop references, reusable templates, and target file-structure guidance. |
| [meeting-ingestion](./meeting-ingestion/) | Unified skill for ingesting meeting transcripts from Google Drive and orchestrating the processing pipeline. |
| [krisp-meeting-blocks](./krisp-meeting-blocks/) | Portable Krisp transcript ingestion and meeting block pipeline with zo.space webhook template, monthly archive, v3-style add-on blocks, and owner notifications for partial/review meetings. |
| [meme-factory](./meme-factory/) | Generate memes with memegen.link templates and text controls. |
| [mentor-handler](./mentor-handler/) | Handle escalation requests from partner instances and provide mentor guidance based on precedent and context analysis. |
| [persona-optimization](./persona-optimization/) | Persona agency bootloader for Zo Computer with hard-switch rules and methodology injection. |
| [pitch-deck-evaluator](./pitch-deck-evaluator/) | Evaluate pre-seed and seed pitch decks through multiple investor frames with a reusable rubric, deterministic local scoring, and opt-in named-VC POV guardrails. |
| [prompt-to-skill](./prompt-to-skill/) | Turn complex prompts into reusable skill structures. |
| [rapid-context-extractor](./rapid-context-extractor/) | Prepare structured packets for deeper source analysis and teaching. |
| [remotion](./remotion/) | Create code-driven videos with React and Remotion. |
| [startup-memo-generator](./startup-memo-generator/) | Generate gated, analytics-enabled founder memo pages for investors, customers, and vendors on zo.space. |
| [systematic-debugging](./systematic-debugging/) | Apply a disciplined debugging process before proposing fixes. |
| [text-commute-info](./text-commute-info/) | Fetch commute details and text them to the user. |
| [text-to-diagram](./text-to-diagram/) | Convert text into Excalidraw-ready visual structures. |
| [workspace-doc-sync-starter](./workspace-doc-sync-starter/) | Standalone starter kit for synchronized AI workspace docs across multiple harnesses. Includes shared canonical docs, thin adapters, identity-layer files, systemprefs decomposition guidance, and a scaffold script. |
| [zo-create-site](./zo-create-site/) | Scaffold a site hosted on Zo. |

## What this repo excludes

This collection intentionally excludes:
- private or company-specific skills
- workspace-bound automation and orchestration
- Zo-internal infrastructure skills
- duplicate platform connection skills already better housed elsewhere

## Contributing

Skills follow the [Agent Skills](https://agentskills.io/specification) spec.
Each skill should include a `SKILL.md` with clear frontmatter and portable instructions.

## Portability Notes

This collection aims to keep each skill understandable and installable outside the author's private workspace.

- Some skills are zero-dependency; others require paid APIs, secrets, browser access, or Zo-specific capabilities.
- Each skill should state required accounts/secrets, any message-sending or automation behavior, and any workspace/runtime assumptions.
- When a skill includes opinionated example assets or service shapes, treat them as examples to adapt rather than defaults to reuse unchanged.

## License

MIT
