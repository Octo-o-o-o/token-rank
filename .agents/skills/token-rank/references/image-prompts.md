# Image Generation Prompts

Use this reference when Codex built-in `image_gen` is available. The preferred workflow is one-shot image generation:

1. Run `scripts/token_rank_card.py --prompt-only` or `--emit-image-prompt`.
2. Read the generated `.image-prompt.txt`.
3. Pass that complete prompt to the built-in `image_gen` tool once.
4. Save the selected generated bitmap into the project/workspace.

The script must assemble the prompt from computed local usage data: nickname, level, QQ-style badges, total tokens, daily average, streaks, top sources, creature, palette, and the elegant metric-aware line.

Do not separately generate an avatar and then compose text unless the user explicitly asks for deterministic typography. Ordinary image-model text imperfections are acceptable for this skill, but the prompt should prioritize large readable nickname, level, total token, daily average, and current streak values.

## Full Card Prompt Requirements

A good card prompt should include:

- Asset type: one-shot share card generated entirely by `image_gen`.
- Canvas: vertical portrait 4:5, intended as a 1080x1350 social card.
- Layout: single `Token Rank` title, nickname, avatar, level band, wrapped QQ-style badge rows, three core metrics, optional source-name chips, elegant line, footer. Do not use a separate subtitle under the title.
- Badge rule: display only the highest two non-zero QQ-style badge tiers, repeat the visible icons one-by-one, and wrap to multiple rows when needed. Do not draw lower-tier leftovers after the top two tiers. Never use multiplication notation such as `x2` or `×2`.
- T-medal visual rule: the highest-tier medal must be a wordless prestige icon. It must contain no letters, no visible `T`, no Chinese/English label, and no small caption. It should look clearly above a crown through scale, luminosity, halo, prismatic facets, or ceremonial framing.
- Metric rule: show raw visible-window token total, raw visible-window daily average, current streak days, level, and top agent/model names only.
- Visible-window rule: default to `近30天总量` and `近30天日均`. If the earliest detected record is newer than 30 days, use `全部N天总量` and `全部N天日均`, where `N` is the actual calendar-day coverage.
- Daily-average rule: the displayed daily average is the larger of the current-window average including today and the previous completed-window average excluding today, so cards generated early in the current day are not unfairly low.
- Token-value rule: do not display weighted/cache-adjusted tokens or any "more valuable" token count. Weighted tokens can exist in internal summary data only.
- Minimal-data rule: visible cards should not show historical total, active days, latest streak, longest streak, exact comma-separated token counts, date ranges, rank score, weighted tokens, source token values, or model token values unless the user explicitly asks for a data-heavy version.
- Top metadata rule: include top 2 agents and top 2 models as small name-only chips in weak visual positions such as a footer rail, lower corner, side caption, tiny paper-label strip, or faint stamp. Do not show token values. Do not let these chips compete with the nickname, level, animal portrait, badge row, or three core metrics.
- Layout-quality rule: prefer a concise premium style-led share card over a dashboard: enough negative space, fewer boxes, no dense mini-tables, no terminal screenshots, and clear typographic hierarchy.
- Visual rule: richer light, denser token constellations, and more ceremonial framing for stronger total/daily/level/streak signals, without explaining this mapping literally.
- Creature variation rule: use the script-provided shape/material/pose/accent lines as strong guidance. Treat the named species as a loose seed, not a fixed mascot; avoid repeatedly defaulting to a standard dragon, qilin, fox, wolf, or humanoid athlete unless the selected style specifically calls for that silhouette.
- Variation seed rule: include the script-generated `variationSeed` as a hidden creative cue only. It should change the animal design across repeated runs, but it must never appear as visible text in the image.
- Text tolerance: minor small-text drift is acceptable; primary nickname, level, total, daily average, and streak should be large and clear.
- Safety: no real people, no brand logos, no screenshots, no watermarks, no QR code.

For `--platform xhs`, the card prompt should additionally request:

- Canvas: `1080x1440`, vertical `3:4`, Xiaohongshu/Rednote-ready.
- Put the primary title, subject, and core metric inside the central square preview-safe area.
- Use Chinese approximate units by default, such as `约300亿`, when public sharing matters.
- Keep the card readable as one carousel page; no dense footnotes, exact long numbers, or source-value panels.

## Full Avatar Prompt Requirements

A good avatar prompt should include:

- Asset type: square avatar generated entirely by `image_gen`.
- Subject: fictional mythic animal, never a human or real person.
- Inputs: nickname, level, badges, token scale, dominant source, and streak as visual inspiration.
- Variation: include a fresh silhouette, material mix, pose, and small accents from the generated prompt so repeated outputs do not look like the same mascot.
- Variation seed: use the generated `variationSeed` to diversify the creature, but do not render the seed as text.
- Style: style-led rendering based on the selected numbered preset, readable at small size, clean silhouette, arcane coding companion.
- Background: match the selected preset, with subtle token/rank hints only when useful.
- Safety: no text, no logos, no watermark, no UI frame.

## Visual Style Presets

Use `--visual-style <number>` with the script. Final curated presets:

- `01` / Wanted Newsprint / 印刷悬赏令: huge `WANTED` header, central portrait-photo panel, `DEAD OR ALIVE` line, oversized bounty value, aged newsprint parchment.
- `02` / Gothic Black Tarot / 哥特黑塔罗: black tarot card, silver ink, cathedral arch, moonlit creature, restrained red stamp.
- `03` / Risograph Zine / Riso 独立小报: coral/teal overprint, visible misregistration, grainy paper, hand-printed labels.
- `04` / Botanical Alchemy / 植物炼金: emerald glass, gold apothecary labels, glowing plants, living familiar.
- `05` / Mono Terminal Poster / 黑白终端海报: e-ink monochrome poster, sparse grid, command-output rhythm.
- `06` / Stained Glass Icon / 彩窗圣像: jewel-toned panels, dark lead lines, luminous rose-window creature.
- `07` / Rune Totem / 符石图腾: carved stone border, icy blue light, guardian spirit, ancient gem medal.
- `08` / Airy Instagram Story / 留白 Ins Story: warm white negative space, tiny relaxed illustration, thin typography.
- `09` / Editorial Magazine Cover / 编辑杂志封面: modern magazine cover, generous margins, confident portrait, feature callouts.
- `10` / Fashion Lookbook Anthro / 时装拟人造型: anthropomorphic animal in oversized minimal jacket, studio lookbook.
- `11` / Luxury Membership Pass / 极简会员通行证: matte ivory card, embossed animal mark, sparse foil lines.
- `12` / Running Club Bib / 跑者号码布: fictional race-bib card, anthropomorphic runner, lap-split metrics.

All presets must stay generic and original: do not reference or copy any anime/manga franchise, sports league, fashion brand, magazine, card game, social template, character, logo, team mark, flag, skull mark, typography, or exact proprietary layout.

## Source-to-Creature Hints

Use the dominant usage source to influence the animal, but keep it original:

- Codex: octopus sage, book wyrm, star-forged owl.
- Claude Code: moon deer, white fox, paper crane spirit.
- Gemini CLI: twin-star bird, mirror-wing beast, astral lynx.
- OpenCode: rune panther, obsidian badger, terminal wolf.
- OpenClaw: golden gryphon, clawed lion, storm manticore.
- Hermes Agent: messenger falcon, wind stag, winged fox.
- Mixed sources: nebula qilin, prism dragon, constellation chimera.

## Prompt Quality Notes

- Use exact visible text lines in the prompt even though image generation may not reproduce them perfectly.
- Keep stats compact, e.g. `30.96B`, not full exact numbers.
- Prefer a bold, memorable badge zone and three large metric values over tiny tables.
- Place top agents/models where the layout has spare visual capacity; they should feel like provenance metadata, not leaderboard data.
- Include the local-only entertainment footer.
- Avoid overly dark, blurred, stock-like, or single-hue designs.

## Xiaohongshu Share Pack Prompt Requirements

When the user asks for 小红书传播、封面、轮播、分享包, or public social sharing, use `references/xhs-share-pack.md` and generate `--mode xhs-pack`.

The share pack uses five separate image prompts:

1. Cover: one large hook, nickname/rank, and one public-safe metric.
2. Rank card: the full aesthetic artifact.
3. Badge guide: the QQ-style badge ladder.
4. How-to: a four-step reproduction flow.
5. Style picker: the 12 available visual styles.

Each prompt should be suitable for one separate `image_gen` call. Do not ask the image model for a five-page collage.
