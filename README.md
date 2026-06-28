# Token Rank

A Codex Skill for generating a local-only Vibe Coding token rank avatar or share card from coding-agent token usage.

It is designed for users who want to ask Codex for a shareable rank card based on local usage from tools such as Codex, Claude Code, Gemini CLI, OpenCode, OpenClaw, Hermes Agent, and other `ccusage`-compatible sources. Cursor Agent can be included through a user-supplied read-only JSON adapter.

Chinese README: [README.zh-CN.md](README.zh-CN.md)

## What It Generates

- `avatar`: when Codex built-in `image_gen` / GPT-image-2 is available, the skill generates one complete style-led fantasy animal avatar bitmap; otherwise it falls back to a 512x512 deterministic SVG.
- `card`: when `image_gen` is available, the skill generates one complete share-card bitmap with nickname, avatar, level, wordless rank badges, visible-window total, visible-window daily average, current streak days, top agent/model name chips, and one elegant line of copy; otherwise it falls back to a 1080x1350 SVG.
- `xhs-pack`: generates a Xiaohongshu/Rednote-ready carousel prompt pack with a 3:4 cover, rank-card page, badge explainer, how-to page, style picker, caption draft, and manifest.
- Optional PNG export when `rsvg-convert`, ImageMagick, macOS `sips`, or `cairosvg` is available.

## Latest Gallery

This demo gallery was generated with Codex built-in `image_gen` from a local-only `ccusage` snapshot for `Octo-o-o-o`: `Lv.446`, `近30天总量 29.79B`, `近30天日均 993.10M`, `连续天数 81`. Prompt and summary files live in [`docs/gallery/latest`](docs/gallery/latest).

| # | Style | Avatar | Card |
|---|---|---|---|
| 01 | Wanted Newsprint | <img src="docs/gallery/latest/01-avatar.png" width="88" alt="01 Wanted Newsprint avatar"> | <img src="docs/gallery/latest/01-card.png" width="132" alt="01 Wanted Newsprint card"> |
| 02 | Gothic Black Tarot | <img src="docs/gallery/latest/02-avatar.png" width="88" alt="02 Gothic Black Tarot avatar"> | <img src="docs/gallery/latest/02-card.png" width="132" alt="02 Gothic Black Tarot card"> |
| 03 | Risograph Zine | <img src="docs/gallery/latest/03-avatar.png" width="88" alt="03 Risograph Zine avatar"> | <img src="docs/gallery/latest/03-card.png" width="132" alt="03 Risograph Zine card"> |
| 04 | Botanical Alchemy | <img src="docs/gallery/latest/04-avatar.png" width="88" alt="04 Botanical Alchemy avatar"> | <img src="docs/gallery/latest/04-card.png" width="132" alt="04 Botanical Alchemy card"> |
| 05 | Mono Terminal Poster | <img src="docs/gallery/latest/05-avatar.png" width="88" alt="05 Mono Terminal Poster avatar"> | <img src="docs/gallery/latest/05-card.png" width="132" alt="05 Mono Terminal Poster card"> |
| 06 | Stained Glass Icon | <img src="docs/gallery/latest/06-avatar.png" width="88" alt="06 Stained Glass Icon avatar"> | <img src="docs/gallery/latest/06-card.png" width="132" alt="06 Stained Glass Icon card"> |
| 07 | Rune Totem | <img src="docs/gallery/latest/07-avatar.png" width="88" alt="07 Rune Totem avatar"> | <img src="docs/gallery/latest/07-card.png" width="132" alt="07 Rune Totem card"> |
| 08 | Airy Instagram Story | <img src="docs/gallery/latest/08-avatar.png" width="88" alt="08 Airy Instagram Story avatar"> | <img src="docs/gallery/latest/08-card.png" width="132" alt="08 Airy Instagram Story card"> |
| 09 | Editorial Magazine Cover | <img src="docs/gallery/latest/09-avatar.png" width="88" alt="09 Editorial Magazine Cover avatar"> | <img src="docs/gallery/latest/09-card.png" width="132" alt="09 Editorial Magazine Cover card"> |
| 10 | Fashion Lookbook Anthro | <img src="docs/gallery/latest/10-avatar.png" width="88" alt="10 Fashion Lookbook Anthro avatar"> | <img src="docs/gallery/latest/10-card.png" width="132" alt="10 Fashion Lookbook Anthro card"> |
| 11 | Luxury Membership Pass | <img src="docs/gallery/latest/11-avatar.png" width="88" alt="11 Luxury Membership Pass avatar"> | <img src="docs/gallery/latest/11-card.png" width="132" alt="11 Luxury Membership Pass card"> |
| 12 | Running Club Bib | <img src="docs/gallery/latest/12-avatar.png" width="88" alt="12 Running Club Bib avatar"> | <img src="docs/gallery/latest/12-card.png" width="132" alt="12 Running Club Bib card"> |

## Install

This repository stores the skill in:

```text
.agents/skills/token-rank
```

To install globally:

```bash
mkdir -p ~/.agents/skills
cp -R .agents/skills/token-rank ~/.agents/skills/
```

To use it inside this repository, open Codex from the repository root and ask for the skill explicitly.

## Usage In Codex

```text
Use $token-rank to generate a card, nickname=灵狐, window=30 days.
```

```text
Use $token-rank to generate an avatar, nickname=月影.
```

If the request does not say `avatar` or `card`, the skill must ask for the mode before reading local usage data.

## Recommended Skill Prompts

Use these prompts directly in Codex after installing the skill. Always specify `card`, `avatar`, or `xhs-pack`.

```text
Use $token-rank to generate a card. Nickname=灵狐, use the default recent-30-day metrics, visual-style=01.
```

```text
Use $token-rank to generate an avatar. Nickname=月影, visual-style=08, use local token usage as the seed.
```

```text
Use $token-rank to generate a Xiaohongshu share pack. Nickname=灵狐, visual-style=01, public-safe, use approximate Chinese units.
```

```text
Use $token-rank to generate a card. Nickname=Octo-o-o-o, visual-style=11, platform=xhs, public-safe, only show the three core metrics and weak top-agent/model chips.
```

```text
Use $token-rank to generate a card. Nickname=Cursor兽, include Cursor through this read-only adapter: extra-command="cursor:cursor-usage --json".
```

```text
Use $token-rank to generate a card prompt only. Nickname=灵狐, visual-style=06, do not render SVG, write the complete image_gen prompt so I can generate the image separately.
```

## CLI Usage

Generate a full card prompt, then pass it to Codex built-in `image_gen` in one shot:

```bash
python3 .agents/skills/token-rank/scripts/token_rank_card.py \
  --mode card \
  --nickname "灵狐" \
  --prompt-only \
  --output ./token-rank
```

Then read:

```text
./token-rank.image-prompt.txt
```

Pass the complete prompt to `image_gen`, then save the generated bitmap into the project.

Creature variation is randomized by default for image-generation prompts. Use `--variation-seed stable` for a reproducible prompt, or pass any custom string such as `--variation-seed octo-blue-runner`.

Generate an avatar prompt:

```bash
python3 .agents/skills/token-rank/scripts/token_rank_card.py \
  --mode avatar \
  --nickname "灵狐" \
  --visual-style 01 \
  --prompt-only \
  --output ./token-rank-avatar
```

Visual style presets:

```text
01 Wanted Newsprint
02 Gothic Black Tarot
03 Risograph Zine
04 Botanical Alchemy
05 Mono Terminal Poster
06 Stained Glass Icon
07 Rune Totem
08 Airy Instagram Story
09 Editorial Magazine Cover
10 Fashion Lookbook Anthro
11 Luxury Membership Pass
12 Running Club Bib
```

`01` is the original printed wanted-poster style: huge `WANTED` header, central portrait-photo panel, `DEAD OR ALIVE` line, oversized nickname and bounty value, aged newsprint parchment, and small stamp-like rank metrics. All styles must stay original and open-source-safe; do not copy existing anime/manga IP, sports leagues, fashion brands, magazines, card games, social templates, characters, logos, team marks, flags, skull marks, typography, or exact proprietary layouts.

Generate a Xiaohongshu/Rednote share pack:

```bash
python3 .agents/skills/token-rank/scripts/token_rank_card.py \
  --mode xhs-pack \
  --nickname "灵狐" \
  --visual-style 01 \
  --public-safe \
  --output ./xhs-share-pack
```

This writes five separate `*.image-prompt.txt` files, `xhs-caption.zh-CN.md`, `manifest.json`, and `summary.json`. Pass each prompt to Codex built-in `image_gen` separately; do not generate a five-page collage in one image.

For a single XHS-ready card prompt:

```bash
python3 .agents/skills/token-rank/scripts/token_rank_card.py \
  --mode card \
  --nickname "灵狐" \
  --platform xhs \
  --display-unit zh \
  --public-safe \
  --prompt-only \
  --output ./xhs-rank-card
```

XHS mode uses `1080x1440` / `3:4`, keeps key content inside the central square preview-safe area, and defaults to public-friendly Chinese approximate units such as `约300亿`.

Generate a deterministic SVG fallback card:

```bash
python3 .agents/skills/token-rank/scripts/token_rank_card.py \
  --mode card \
  --nickname "灵狐" \
  --output ./token-rank \
  --png
```

Allow temporary `ccusage` runners only when you accept running `bunx` / `npx` / `pnpm dlx`:

```bash
python3 .agents/skills/token-rank/scripts/token_rank_card.py \
  --mode card \
  --nickname "灵狐" \
  --allow-download-runner \
  --prompt-only \
  --output ./token-rank
```

Include Cursor through a local read-only adapter:

```bash
python3 .agents/skills/token-rank/scripts/token_rank_card.py \
  --mode card \
  --nickname "Cursor兽" \
  --extra-command "cursor:cursor-usage --json" \
  --prompt-only \
  --output ./token-rank
```

## Ranking Model

The default `sqrt` profile uses weighted tokens:

```text
weighted = input + output + cache_creation + 0.25 * cache_read
```

If detailed fields are unavailable, it falls back to `totalTokens`.

The default level curve is:

```text
scoreTokens = totalWeighted + avgDailyWeighted(windowDays) * windowDays
level = floor(3 * sqrt(scoreTokens / 1,000,000))
```

This keeps light usage around Lv.1-Lv.7 while allowing sustained heavy usage to reach T medals. Use `--level-profile benchmark` for a compressed scale or `--level-profile linear` for the old 1M tokens = 1 level behavior.

QQ-style symbols:

```text
1 star = 1 level
1 moon = 4 stars
1 sun = 4 moons
1 crown = 4 suns
1 T medal = 4 crowns
```

The full decomposition is preserved in summary JSON as `fullSymbols`. Cards and image prompts display only the highest two non-zero tiers, repeated one by one and wrapped across lines when needed. For example, a high rank may show one wordless prestige medal plus two crowns, while lower sun/moon/star leftovers stay hidden for visual clarity. The visible badge row must never use multiplication notation such as `x2` or `×2`.

This card is for entertainment and sharing. It is not a billing document.

Rank scoring may keep using weighted tokens, but visible usage metrics on cards use raw `totalTokens`; weighted/cache-adjusted tokens should not be shown as a "more valuable" token count. By default, the headline card metrics are `近30天总量` and `近30天日均`. The daily average is the larger of the current-window average including today and the previous completed-window average excluding today, so early-day card generation is not unfairly low. If the earliest detected record is newer than 30 days, the card uses the actual coverage and shows `全部N天总量` and `全部N天日均`. Streaks are reported separately: `activeDays`, `currentStreakDays`, `latestActiveStreakDays`, and `longestStreakDays`; cards display `currentStreakDays`.

Default cards should feel concise, premium, and style-led, not like dense data dashboards. They should not show historical total, active days, latest/longest streak, exact long numbers, date range, rank score, weighted tokens, or source token values unless the user asks for a data-heavy version. The highest-tier T medal is rendered as a wordless prestige emblem: no letter T, no "T勋章" text, no label underneath, and visually above crowns through halo, facets, octagonal gem form, or ceremonial light.

When available, cards include the top 2 agents and top 2 models as small name-only metadata chips in low-emphasis areas such as the footer, lower corner, side caption, or faint stamp strip. They are provenance hints, not extra metrics, so token values are not shown.

## Privacy

The skill runs local read-only usage commands and renders local files. It should not upload raw logs, expose prompt text, inspect source code for profiling, or parse private Cursor databases. Unsupported tools should be connected through explicit read-only JSON adapters.

Generated cards include:

```text
Local read-only · Token rank for fun
```

## One-Shot Prompt

If you do not want to install the skill, copy:

```text
.agents/skills/token-rank/examples/one-shot-prompt.md
```

## Image Generation

When Codex built-in `image_gen` / GPT-image-2 is available, the preferred workflow is script-generated prompt first, then one-shot image generation. The avatar/card art, text, rank symbols, and numbers all go into the generated bitmap. Normal image-model text imperfections are acceptable, but the prompt asks for the nickname, level, total token, daily average, and current streak to be large and clear.

By default, each run writes a fresh `variationSeed` into the prompt so repeated generations produce more varied creature silhouettes and materials. Use `--variation-seed stable` or a custom seed when you want to reproduce a specific look.

Generate the prompt:

```bash
python3 .agents/skills/token-rank/scripts/token_rank_card.py \
  --mode card \
  --nickname "灵狐" \
  --prompt-only \
  --output ./token-rank
```

Prompt guide:

```text
.agents/skills/token-rank/references/image-prompts.md
```

If `image_gen` is unavailable, use the script's SVG fallback.
