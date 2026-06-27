# Xiaohongshu Share Pack

Use this reference when the user asks for 小红书 / XHS / Rednote sharing, viral spread, carousel posts, covers, captions, or public-safe sharing assets.

## Standard Output

Generate a share pack instead of only one card:

```bash
python3 .agents/skills/token-rank/scripts/token_rank_card.py \
  --mode xhs-pack \
  --nickname "灵狐" \
  --visual-style 01 \
  --public-safe \
  --output ./xhs-share-pack
```

The script writes:

- `01-cover.image-prompt.txt`: feed-safe cover hook.
- `02-rank-card.image-prompt.txt`: full rank card page.
- `03-badge-guide.image-prompt.txt`: badge ladder explainer.
- `04-how-to.image-prompt.txt`: reproduction/how-to page.
- `05-style-picker.image-prompt.txt`: 12-style picker page.
- `xhs-caption.zh-CN.md`: titles, body, tags, and comment CTA.
- `manifest.json`: machine-readable file list and metric snapshot.
- `summary.json`: usage/rank summary.

Pass each `.image-prompt.txt` to Codex built-in `image_gen` separately and save the generated images next to the prompts.

## Platform Rules

- Use `1080x1440` / `3:4` as the default XHS canvas.
- Keep primary text and the main subject inside the central square preview-safe area.
- Use one message per page. A cover should be understood in under two seconds.
- Prefer large Chinese hooks, short supporting copy, and strong negative space.
- Use simplified public metrics by default: Chinese units such as `约300亿`, not exact comma-separated numbers.
- `--public-safe` should omit source/model value details and round visible values.
- Show top 2 agents and top 2 models only as tiny name chips in weaker visual positions, such as a lower corner, side caption, footer rail, or faint stamp. Do not show per-agent or per-model token values.
- Never show raw logs, session text, date ranges, weighted/cache-adjusted tokens, source token values, QR codes, screenshots, or private paths.

## Carousel Structure

1. **Cover**: large hook + nickname/rank + one impressive metric.
2. **Rank Card**: the actual aesthetic artifact.
3. **Badge Guide**: explain the star/moon/sun/crown/wordless prestige-medal ladder.
4. **How-To**: show how others can reproduce it in Codex.
5. **Style Picker**: show all 12 style names and invite comments.

## Prompt Quality

- The cover hook should be 8-18 Chinese characters when possible, or split into two short lines.
- Do not make the cover a dense data dashboard.
- Do not imitate existing social templates, manga IP, magazine layouts, sports marks, fashion brands, logos, or proprietary poster styles.
- Keep the T-tier medal wordless. In XHS pages call it `神徽` when text explanation is needed, but the icon itself must contain no `T` or label.
- On card/cover pages, show only the highest two non-zero badge tiers. Repeat icons one by one and wrap if needed; do not show lower-tier leftovers and do not use `x2` / `×2`.
- Use a saved-worthy tone: elegant, surprising, and slightly personal, not exaggerated financial or billing language.

## Caption Pattern

Generate `xhs-caption.zh-CN.md` with:

- 3-5 title options.
- A short first-person body.
- A privacy/entertainment clarification.
- 8-12 hashtags.
- One comment CTA asking users for nickname/style choice.
