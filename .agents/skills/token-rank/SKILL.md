---
name: token-rank
description: Generate a local-only Vibe Coding token rank avatar, share card, or Xiaohongshu/Rednote share pack from ccusage-compatible coding-agent token usage. Use when the user asks for token usage levels, token等级卡, QQ-style token badges, vibe coding rank cards, style-led fantasy animal avatars, 小红书传播图/封面/轮播, or visual summaries of local Codex, Claude Code, Gemini CLI, OpenCode, OpenClaw, Hermes Agent, Cursor-compatible adapters, or similar coding-agent token usage. The user must specify avatar, card, or xhs-pack.
---

# Token Rank

Generate a shareable Vibe Coding token rank avatar or card from local coding-agent usage.

## Hard Rules

1. Require an explicit output mode: `avatar` / `头像`, `card` / `卡片`, or `xhs-pack` / `小红书分享包`.
   If the mode is missing, do not read local usage data. Ask only:
   `请指定“头像”“卡片”或“小红书分享包”，例如：生成卡片，昵称=灵狐，统计最近30天。`
2. Use local read-only usage data only. Do not upload logs, expose prompts, inspect project source for personality data, or show raw session content.
3. Prefer the bundled script: `scripts/token_rank_card.py`.
4. Prefer an already installed `ccusage`. Do not download or run `bunx` / `npx` / `pnpm dlx` unless the user explicitly allows temporary runners; then pass `--allow-download-runner`.
5. Treat Cursor Agent and unsupported tools as external adapters. Only include them when the user provides a read-only JSON command through `--extra-command`.
6. Prefer Codex built-in image generation (`image_gen`, GPT-image-2) when it is available in the session. Use the script to collect usage and assemble one complete image prompt, then call `image_gen` once for the whole avatar/card.
7. If `image_gen` is unavailable, use the deterministic SVG fallback from the script.
8. Reply with generated file paths, level summary, and warnings. Do not paste full SVG content.
9. For 小红书 / XHS / Rednote sharing, read `references/xhs-share-pack.md` and prefer `--mode xhs-pack` over a single card.

## Data Collection

Default command:

```bash
ccusage daily --json --no-cost
```

The script also tries source-focused reports for breakdowns:

```text
claude,codex,gemini,opencode,openclaw,hermes,amp,droid,codebuff,pi,goose,kilo,kimi,qwen,copilot
```

Cursor or other sources must be provided as a local read-only JSON adapter:

```bash
--extra-command "cursor:cursor-usage --json"
```

Adapter output should be ccusage-compatible, for example:

```json
{
  "daily": [
    {"date": "2026-06-24", "totalTokens": 1234567}
  ]
}
```

When available, parse `modelBreakdowns`, `modelsUsed`, `modelName`, or `model` fields to compute top model names. Use source-focused ccusage reports for top agent names. If exact model totals are unavailable, do not invent model rankings.

## Ranking Model

Use weighted tokens for ranking when detailed fields exist:

```text
weighted = input + output + cache_creation + 0.25 * cache_read
```

If detailed fields are missing, use `totalTokens`.

Default profile is `sqrt`, a QQ-style entertainment curve:

```text
scoreTokens = totalWeighted + avgDailyWeighted(windowDays) * windowDays
levelFloat = 3 * sqrt(scoreTokens / 1,000,000)
level = floor(levelFloat), with minimum Lv.1 when any usage exists
```

This keeps occasional usage low while allowing heavy sustained usage to reach T medals:

```text
100K score tokens -> about Lv.1
500K score tokens -> about Lv.3
1M score tokens   -> about Lv.4
3M score tokens   -> about Lv.7
```

Use `--level-profile benchmark` only when a compressed scale is preferred. Use `--level-profile linear` to reproduce the old 1M tokens = 1 level behavior.

QQ-style symbols:

```text
1 star = 1 level
1 moon = 4 stars
1 sun = 4 moons
1 crown = 4 suns
1 T medal = 4 crowns
```

Preserve the full QQ decomposition in summary JSON as `fullSymbols`. Displayed card badges must show only the highest two non-zero tiers for clarity, repeated one by one and wrapped across lines if needed. Do not show lower-tier leftovers on the card once two higher tiers are visible, and never use multiplication notation such as `x2` or `×2`.

This is an entertainment rank, not a bill.

Total tokens and weighted tokens always use every collected record in the selected date range for rank scoring and summary context. The `windowDays` setting controls the default visible usage window. With default `windowDays = 30`, visible card metrics use raw, non-weighted tokens:

```text
headline total = raw tokens from max(firstDate, windowEnd - 29 days) through windowEnd
headline daily = max(including-current-day daily average, excluding-current-day daily average)
including-current-day daily average = headline total / effectiveWindowDays
excluding-current-day daily average = raw tokens from the previous completed windowDays calendar days / effective completed days, only when the current local day is inside the selected window
effectiveWindowDays = 30, or fewer when the first detected record is newer than 30 days
```

This prevents an early-in-the-day card generation from understating the visible daily average. The card still shows the current-window headline total.

Do not show weighted/cache-adjusted tokens as visible usage metrics on the card. Weighted tokens may remain in summary JSON and rank scoring internals.

Streak fields are separate:

```text
activeDays = count of distinct active days in the selected range
currentStreakDays = consecutive active days ending at --until or today
latestActiveStreakDays = consecutive active days ending at the latest active day
longestStreakDays = longest consecutive run in the selected range
```

Cards display `currentStreakDays` as `连续天数`; summary JSON keeps all four fields.

## Rendering

When Codex image generation is available:

1. Read `references/image-prompts.md`.
2. Run the script with `--prompt-only` or `--emit-image-prompt` so it collects local usage, computes rank/streaks/copy, and writes a complete `image_gen` prompt.
3. Read the generated `.image-prompt.txt`.
4. Call the built-in `image_gen` tool once with that full prompt. The generated image should contain the whole avatar/card, including text, badges, metrics, and visual design.
5. Copy or move the selected generated image from `$CODEX_HOME/generated_images/...` into the project/workspace when the asset is project-bound.

This workflow accepts ordinary image-model text imperfections. The prompt should still ask for large readable nickname, level, total token, daily average, and streak values, but do not add a later SVG text pass unless the user explicitly asks for deterministic typography.

If `image_gen` is not available, run the script without `--prompt-only` and use the deterministic SVG fallback.

Avatar mode:

- With `image_gen`: generate one complete square style-led fantasy animal avatar bitmap.
- Fallback: generate a 512x512 SVG pixel fantasy animal avatar.
- Use nickname, level, token volume, dominant source, selected style, and `variationSeed` as the creative seed. The script defaults to a fresh random `variationSeed` for each run; pass `--variation-seed stable` or a custom string to reproduce a look.
- Do not render real people or realistic portraits.

Card mode:

- With `image_gen`: generate one complete vertical share-card bitmap from the script-authored prompt.
- Fallback: generate a 1080x1350 SVG share card.
- Include nickname, avatar, level, QQ-style symbols, visible-window raw token total, visible-window raw daily average, current streak days, top 2 agent names, top 2 model names, one elegant metric-aware line, and the local-read-only note.
- Use a single concise card title: `Token Rank`. Do not render the old two-line title/subtitle pair (`VIBE TOKEN RANK` plus `本机 Agent Token 修行卡`) in generated cards.
- Keep visible cards concise and premium. Do not show historical total, active days, latest/longest streak, exact comma-separated token counts, date ranges, rank score, weighted tokens, or source token values unless the user asks for a data-heavy version.
- Render visible QQ-style badges from the highest two non-zero tiers only. Repeat icons one by one, allow line wrapping, and hide lower-tier leftovers. Keep full decomposition in JSON only.
- Show top agents/models as low-emphasis name-only metadata chips in weak visual positions such as footer rails, lower corners, side captions, or faint stamp strips. Do not show token values for agents/models. Do not let them compete with nickname, level, badges, animal portrait, or the three core metrics.
- Render the highest-tier T medal as a wordless prestige icon: no letter `T`, no Chinese/English text, no label underneath. It should look clearly more advanced than crowns through scale, halo, facets, or ceremonial framing.
- Keep the creature identity varied. Treat the named mythic animal as a loose seed and use the script-provided shape/material/pose/accent variation lines; do not repeatedly default to standard dragons, qilins, foxes, wolves, or humanoid mascots unless the selected style requires that silhouette.
- For image generation, let the default random `variationSeed` increase creature variety across repeated runs. Use `--variation-seed stable` or a custom value only when the user wants reproducible prompts.
- If the environment supports `rsvg-convert`, ImageMagick, macOS `sips`, or `cairosvg`, `--png` may also export PNG.

For AI image generation, read `references/image-prompts.md`. Let `image_gen` create the whole visual in one pass; only use SVG/HTML for the fallback path.

XHS share-pack mode:

- Use when the user asks for 小红书传播、封面、轮播、分享包、爆款笔记文案, or public social spread.
- Read `references/xhs-share-pack.md`.
- Run the script with `--mode xhs-pack`; it outputs five image prompts plus `xhs-caption.zh-CN.md`, `manifest.json`, and `summary.json`.
- Generate each page with `image_gen` separately. Do not combine the five pages into one collage.
- Default to `--public-safe` when preparing assets for public sharing unless the user explicitly wants exact/private metrics.
- Use Chinese approximate visible units for XHS, such as `约300亿`, while keeping exact raw values in summary JSON.
- Keep top agents/models as tiny name-only chips. Public-safe mode may still show the names, but never the per-agent or per-model token values.

Visual style presets are controlled with `--visual-style`; default is `01`. Final curated presets:

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

Use `01` for the original printed wanted-poster look: huge `WANTED` header, central portrait-photo panel, `DEAD OR ALIVE` line, oversized nickname and bounty value, aged newsprint parchment, and small stamp-like rank metrics.

All styles must stay original and open-source-safe. Do not mention or copy any existing anime/manga franchise, sports league, fashion brand, magazine, card game, social template, character, logo, flag, skull mark, typography, or exact proprietary layout.

## Common Commands

Generate a card:

```bash
python3 .agents/skills/token-rank/scripts/token_rank_card.py \
  --mode card \
  --nickname "灵狐" \
  --prompt-only \
  --output ./token-rank
```

Then read `./token-rank.image-prompt.txt` and call `image_gen` once with that prompt.

Generate a deterministic fallback card:

```bash
python3 .agents/skills/token-rank/scripts/token_rank_card.py \
  --mode card \
  --nickname "灵狐" \
  --output ./token-rank \
  --png
```

Generate a card prompt while also keeping an SVG fallback:

```bash
python3 .agents/skills/token-rank/scripts/token_rank_card.py \
  --mode card \
  --nickname "灵狐" \
  --emit-image-prompt \
  --output ./token-rank \
  --png
```

Generate an avatar:

```bash
python3 .agents/skills/token-rank/scripts/token_rank_card.py \
  --mode avatar \
  --nickname "灵狐" \
  --visual-style 01 \
  --prompt-only \
  --output ./token-rank-avatar
```

Then read `./token-rank-avatar.image-prompt.txt` and call `image_gen` once with that prompt.

Generate a Xiaohongshu share pack:

```bash
python3 .agents/skills/token-rank/scripts/token_rank_card.py \
  --mode xhs-pack \
  --nickname "灵狐" \
  --visual-style 01 \
  --public-safe \
  --output ./xhs-share-pack
```

Then read each `./xhs-share-pack/*.image-prompt.txt` and call `image_gen` once per page. Use `./xhs-share-pack/xhs-caption.zh-CN.md` as the draft post copy.

Generate a single XHS-ready card prompt:

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

Allow temporary ccusage runners:

```bash
python3 .agents/skills/token-rank/scripts/token_rank_card.py \
  --mode card \
  --nickname "灵狐" \
  --allow-download-runner \
  --prompt-only \
  --output ./token-rank
```

Use a custom date range:

```bash
python3 .agents/skills/token-rank/scripts/token_rank_card.py \
  --mode card \
  --nickname "灵狐" \
  --since 2026-06-01 \
  --until 2026-06-26 \
  --prompt-only \
  --output ./token-rank
```

Include Cursor through a user-supplied adapter:

```bash
python3 .agents/skills/token-rank/scripts/token_rank_card.py \
  --mode card \
  --nickname "Cursor兽" \
  --extra-command "cursor:cursor-usage --json" \
  --prompt-only \
  --output ./token-rank
```

## Reply Format

After generation, reply in the user's language:

```text
已生成：
- 图片：./token-rank.png
- 生图 Prompt：./token-rank.image-prompt.txt
- 摘要：./token-rank.summary.json

等级：Lv.72 1皇冠 2月亮
统计：近30天总量 30.00B，近30天日均 1.00B，连续天数 18
注意：Cursor 未接入；如需纳入，请提供只读 JSON 导出命令。
```

If no data is detected, still generate an unawakened avatar/card and say:
`没有检测到本机 ccusage-compatible token 数据。`
