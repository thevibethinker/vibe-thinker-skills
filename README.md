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

## Included Skills (18)

| Skill | Description |
|-------|-------------|
| [booking-metadata-calendar](./booking-metadata-calendar/) | Parse booking requests into structured metadata and calendar-ready payloads. |
| [branded-pdf](./branded-pdf/) | Generate clean, branded PDFs from markdown. |
| [claude-code-window-primer](./claude-code-window-primer/) | Prime Claude Code usage windows so resets land during useful work hours. |
| [debono-thinking-hats](./debono-thinking-hats/) | Portable Six Thinking Hats persona system for structured parallel thinking. |
| [frontend](./frontend/) | Generate high-quality landing pages with anti-slop guardrails. |
| [landing-page-generator](./landing-page-generator/) | Self-contained landing-page generator with bundled design foundations, anti-slop references, templates, and target file structures. |
| [frontend-design](./frontend-design/) | Create polished, intentional frontend interfaces with strong visual quality. |
| [frontend-design-anthropic](./frontend-design-anthropic/) | Imported frontend design skill focused on high-quality interface work. |
| [gamma](./gamma/) | Generate presentations, webpages, and social content using Gamma's API. |
| [meme-factory](./meme-factory/) | Generate memes with memegen.link templates and text controls. |
| [prompt-to-skill](./prompt-to-skill/) | Turn complex prompts into reusable skill structures. |
| [rapid-context-extractor](./rapid-context-extractor/) | Prepare structured packets for deeper source analysis and teaching. |
| [remotion](./remotion/) | Create code-driven videos with React and Remotion. |
| [systematic-debugging](./systematic-debugging/) | Apply a disciplined debugging process before proposing fixes. |
| [text-commute-info](./text-commute-info/) | Fetch commute details and text them to the user. |
| [text-to-diagram](./text-to-diagram/) | Convert text into Excalidraw-ready visual structures. |
| [vapi](./vapi/) | Integrate Vapi voice agents with booking and webhook flows. |
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

## License

MIT
