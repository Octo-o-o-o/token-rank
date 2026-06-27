# Token Rank

一个 Codex Skill：从本机 coding-agent token 用量生成可分享的 Vibe Coding 等级头像或等级卡。

它适合让用户在 Codex 里一句话生成自己的本机 Agent Token 修行卡。默认支持 `ccusage` 可读取的 Codex、Claude Code、Gemini CLI、OpenCode、OpenClaw、Hermes Agent 等来源；Cursor Agent 通过用户提供的只读 JSON 适配器接入。

English README: [README.md](README.md)

## 能生成什么

- `头像`：Codex 会话里有内置 `image_gen` / GPT-image-2 时，一次生成完整的风格化玄幻动物头像；没有时降级为 512x512 确定性 SVG。
- `卡片`：有 `image_gen` 时，一次生成完整分享卡位图，默认只展示昵称、头像、等级、无字等级徽记、近30天总量、近30天日均、连续天数、Top agent/model 名称小标签和一句优雅文案；没有时降级为 1080x1350 SVG。
- `小红书分享包`：生成小红书 / Rednote 可用的轮播 prompt 包，包含 3:4 封面、等级卡正文页、等级符号说明页、复刻教程页、风格选择页、发布文案和 manifest。
- 如果环境有 `rsvg-convert`、ImageMagick、macOS `sips` 或 `cairosvg`，可以额外导出 PNG。

## 最新图库

下面这组 demo 使用 Codex 内置 `image_gen` 生成，数据来自 `Octo-o-o-o` 的本机只读 `ccusage` 快照：`Lv.446`、`近30天总量 29.79B`、`近30天日均 993.10M`、`连续天数 81`。对应 prompt 和 summary 文件保存在 [`docs/gallery/latest`](docs/gallery/latest)。

| # | 风格 | 头像 | 卡片 |
|---|---|---|---|
| 01 | 印刷悬赏令 | <img src="docs/gallery/latest/01-avatar.png" width="88" alt="01 印刷悬赏令头像"> | <img src="docs/gallery/latest/01-card.png" width="132" alt="01 印刷悬赏令卡片"> |
| 02 | 哥特黑塔罗 | <img src="docs/gallery/latest/02-avatar.png" width="88" alt="02 哥特黑塔罗头像"> | <img src="docs/gallery/latest/02-card.png" width="132" alt="02 哥特黑塔罗卡片"> |
| 03 | Riso 独立小报 | <img src="docs/gallery/latest/03-avatar.png" width="88" alt="03 Riso 独立小报头像"> | <img src="docs/gallery/latest/03-card.png" width="132" alt="03 Riso 独立小报卡片"> |
| 04 | 植物炼金 | <img src="docs/gallery/latest/04-avatar.png" width="88" alt="04 植物炼金头像"> | <img src="docs/gallery/latest/04-card.png" width="132" alt="04 植物炼金卡片"> |
| 05 | 黑白终端海报 | <img src="docs/gallery/latest/05-avatar.png" width="88" alt="05 黑白终端海报头像"> | <img src="docs/gallery/latest/05-card.png" width="132" alt="05 黑白终端海报卡片"> |
| 06 | 彩窗圣像 | <img src="docs/gallery/latest/06-avatar.png" width="88" alt="06 彩窗圣像头像"> | <img src="docs/gallery/latest/06-card.png" width="132" alt="06 彩窗圣像卡片"> |
| 07 | 符石图腾 | <img src="docs/gallery/latest/07-avatar.png" width="88" alt="07 符石图腾头像"> | <img src="docs/gallery/latest/07-card.png" width="132" alt="07 符石图腾卡片"> |
| 08 | 留白 Ins Story | <img src="docs/gallery/latest/08-avatar.png" width="88" alt="08 留白 Ins Story 头像"> | <img src="docs/gallery/latest/08-card.png" width="132" alt="08 留白 Ins Story 卡片"> |
| 09 | 编辑杂志封面 | <img src="docs/gallery/latest/09-avatar.png" width="88" alt="09 编辑杂志封面头像"> | <img src="docs/gallery/latest/09-card.png" width="132" alt="09 编辑杂志封面卡片"> |
| 10 | 时装拟人造型 | <img src="docs/gallery/latest/10-avatar.png" width="88" alt="10 时装拟人造型头像"> | <img src="docs/gallery/latest/10-card.png" width="132" alt="10 时装拟人造型卡片"> |
| 11 | 极简会员通行证 | <img src="docs/gallery/latest/11-avatar.png" width="88" alt="11 极简会员通行证头像"> | <img src="docs/gallery/latest/11-card.png" width="132" alt="11 极简会员通行证卡片"> |
| 12 | 跑者号码布 | <img src="docs/gallery/latest/12-avatar.png" width="88" alt="12 跑者号码布头像"> | <img src="docs/gallery/latest/12-card.png" width="132" alt="12 跑者号码布卡片"> |

## 安装

本仓库中的 skill 位于：

```text
.agents/skills/token-rank
```

安装到用户级 Codex Skills：

```bash
mkdir -p ~/.agents/skills
cp -R .agents/skills/token-rank ~/.agents/skills/
```

如果只在当前仓库使用，从仓库根目录打开 Codex 并显式调用该 skill 即可。

## 在 Codex 里使用

```text
使用 $token-rank，生成卡片，昵称=灵狐，统计最近30天。
```

```text
使用 $token-rank，生成头像，昵称=月影。
```

如果用户没有说明“头像”或“卡片”，skill 必须先追问模式，不能读取本机数据。

## 命令行使用

生成卡片 prompt，并交给 Codex 内置 `image_gen` 一次出图：

```bash
python3 .agents/skills/token-rank/scripts/token_rank_card.py \
  --mode card \
  --nickname "灵狐" \
  --prompt-only \
  --output ./token-rank
```

然后读取：

```text
./token-rank.image-prompt.txt
```

把完整 prompt 交给 `image_gen`，并把生成的图片保存到项目目录。

生成头像 prompt：

```bash
python3 .agents/skills/token-rank/scripts/token_rank_card.py \
  --mode avatar \
  --nickname "灵狐" \
  --visual-style 01 \
  --prompt-only \
  --output ./token-rank-avatar
```

可选生图风格：

```text
01 印刷悬赏令
02 哥特黑塔罗
03 Riso 独立小报
04 植物炼金
05 黑白终端海报
06 彩窗圣像
07 符石图腾
08 留白 Ins Story
09 编辑杂志封面
10 时装拟人造型
11 极简会员通行证
12 跑者号码布
```

`01` 是原创印刷悬赏令风格：顶部大号 `WANTED`、中间肖像照片框、`DEAD OR ALIVE` 行、超大的昵称和赏金额、旧报纸羊皮纸质感，以及小印章式等级指标。所有风格都必须保持原创、适合开源：不要复刻任何现成动漫/漫画 IP、运动联盟、时装品牌、杂志、卡牌游戏、社交模板、角色、Logo、队标、旗帜、骷髅标志、字体或专有版式。

生成小红书 / Rednote 分享包：

```bash
python3 .agents/skills/token-rank/scripts/token_rank_card.py \
  --mode xhs-pack \
  --nickname "灵狐" \
  --visual-style 01 \
  --public-safe \
  --output ./xhs-share-pack
```

它会输出 5 个独立的 `*.image-prompt.txt`、`xhs-caption.zh-CN.md`、`manifest.json` 和 `summary.json`。每个 prompt 都单独交给 Codex 内置 `image_gen` 出图，不要一次生成五页拼图。

如果只想生成单张小红书比例卡片 prompt：

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

小红书模式使用 `1080x1440` / `3:4`，把关键文字和主体放进中心 1:1 安全区，并默认使用适合公开分享的中文近似单位，例如 `约300亿`。

生成 SVG 兜底卡片：

```bash
python3 .agents/skills/token-rank/scripts/token_rank_card.py \
  --mode card \
  --nickname "灵狐" \
  --output ./token-rank \
  --png
```

只有在你允许临时运行 `bunx` / `npx` / `pnpm dlx` 时，才加：

```bash
python3 .agents/skills/token-rank/scripts/token_rank_card.py \
  --mode card \
  --nickname "灵狐" \
  --allow-download-runner \
  --prompt-only \
  --output ./token-rank
```

纳入 Cursor 的方式是用户自己提供本地只读 JSON 导出命令：

```bash
python3 .agents/skills/token-rank/scripts/token_rank_card.py \
  --mode card \
  --nickname "Cursor兽" \
  --extra-command "cursor:cursor-usage --json" \
  --prompt-only \
  --output ./token-rank
```

## 等级算法

默认使用加权 token：

```text
weighted = input + output + cache_creation + 0.25 * cache_read
```

如果没有明细字段，则使用 `totalTokens`。

默认 `sqrt` 模型：

```text
scoreTokens = totalWeighted + avgDailyWeighted(windowDays) * windowDays
level = floor(3 * sqrt(scoreTokens / 1,000,000))
```

少量使用大约落在 Lv.1-Lv.7；持续高强度使用可以进入 T 勋章。需要压缩尺度时可用 `--level-profile benchmark`，需要旧版 `1M token = 1级` 时可用 `--level-profile linear`。

QQ 风格等级符号：

```text
1 星星 = 1级
1 月亮 = 4星星
1 太阳 = 4月亮
1 皇冠 = 4太阳
1 T勋章 = 4皇冠
```

完整分解会保留在 summary JSON 的 `fullSymbols` 中。卡片和生图 prompt 的可见徽章只显示最高两个非零档位，并逐个重复、必要时换行。例如高等级只显示一个无字神徽加两个皇冠，剩余太阳/月亮/星星不再出现在卡面上，以保证视觉清楚。可见徽章行绝不能使用 `x2` 或 `×2` 这类乘法写法。

这张卡是娱乐化等级卡，不是账单凭证。

等级计算可以保留加权 token，但卡片可见用量默认使用原始 `totalTokens`，不展示 weighted/cache-adjusted 这种“更值钱”的 token。默认主指标显示 `近30天总量` 和 `近30天日均`；日均会同时计算“包含今天的当前窗口均值”和“不包含今天的完整窗口均值”，取更大的一个，避免用户在一天刚开始生成卡片时被低估。如果最早检测到的数据不足 30 天，则按实际覆盖天数显示 `全部N天总量` 和 `全部N天日均`。连续指标会分别输出 `activeDays`、`currentStreakDays`、`latestActiveStreakDays` 和 `longestStreakDays`，卡片上显示 `currentStreakDays`。

默认卡片保持简洁、高级、按编号风格主导，不做数据仪表盘；不展示历史总量、活跃天数、最长/最新连续、精确长数字、日期范围、修行指数、weighted token 或来源 token 数值。最高级 T 勋章渲染为无字徽记：不写字母 T，不写“T勋章”，不在图标下加标签，并通过光晕、棱镜、八角宝石或冠冕光芒表现为比皇冠更高级。

如果本机数据里能可靠解析，卡片会在弱视觉位置展示 Top 2 agents 和 Top 2 models 的名称小标签，例如页脚、角落、侧边 caption 或淡印章区域。它们只是来源感提示，不显示 agent/model 对应的 token 数值。

## 隐私规则

Skill 默认只运行本机只读统计命令并生成本地文件。不要上传原始日志，不要展示 prompt 或会话内容，不要读取项目源码做画像，也不要默认解析 Cursor 私有数据库。未稳定支持的工具应通过显式只读 JSON 适配器接入。

卡片固定包含：

```text
本地只读生成 · Token 等级仅供娱乐展示
```

## 兜底 Prompt

如果不安装 skill，可以直接复制：

```text
.agents/skills/token-rank/examples/one-shot-prompt.md
```

## 生图 Prompt

如果当前 Codex 会话有内置 `image_gen` / GPT-image-2，推荐流程是让脚本先产出完整整图 prompt，再把这段 prompt 一次性交给 `image_gen`。头像和卡片的视觉、文字、等级符号、数字都交给生图模型完成；允许存在普通生图模型的细小文字误差，但 prompt 会要求昵称、等级、总 token、日均 token 和连续天数足够大、足够清晰。

生成 prompt：

```bash
python3 .agents/skills/token-rank/scripts/token_rank_card.py \
  --mode card \
  --nickname "灵狐" \
  --prompt-only \
  --output ./token-rank
```

prompt 参考：

```text
.agents/skills/token-rank/references/image-prompts.md
```

没有 `image_gen` 时，使用脚本的 SVG 降级方案。
