#!/usr/bin/env python3
"""
Token Rank generator.

Local-only, standard-library first:
- reads ccusage-compatible JSON from local commands
- computes a benchmark-calibrated QQ-style token rank
- emits complete image_gen prompts for one-shot bitmap avatar/card generation
- renders deterministic SVG avatar/card fallback output
- optionally exports PNG through local renderers when available
"""
from __future__ import annotations

import argparse
import base64
import dataclasses
import datetime as dt
import hashlib
import html
import json
import math
import mimetypes
import os
import random
import secrets
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


KNOWN_CCUSAGE_SOURCES = [
    "claude",
    "codex",
    "gemini",
    "opencode",
    "openclaw",
    "hermes",
    "amp",
    "droid",
    "codebuff",
    "pi",
    "goose",
    "kilo",
    "kimi",
    "qwen",
    "copilot",
]

SOURCE_LABELS = {
    "all": "All Agents",
    "claude": "Claude Code",
    "codex": "Codex",
    "gemini": "Gemini CLI",
    "opencode": "OpenCode",
    "openclaw": "OpenClaw",
    "hermes": "Hermes Agent",
    "amp": "Amp",
    "droid": "Droid",
    "codebuff": "Codebuff",
    "pi": "pi-agent",
    "goose": "Goose",
    "kilo": "Kilo",
    "kimi": "Kimi",
    "qwen": "Qwen",
    "copilot": "Copilot CLI",
    "cursor": "Cursor Agent",
}

SOURCE_CREATURES = {
    "codex": ["星海章灵", "书卷玄枭", "八腕墨龙", "蓝环机巧章鱼", "星图乌鸦", "晶壳海马"],
    "claude": ["月影灵狐", "白羽纸鹤", "静月鹿灵", "纸翼水獭", "绒角雪豹", "琥珀耳兔"],
    "gemini": ["双星鸾鸟", "镜翼天猫", "星盘猞猁", "双尾星鲸", "棱镜飞蜥", "银环狐蝠"],
    "opencode": ["符文夜豹", "终端玄狼", "黑曜獾灵", "荧线壁虎", "铁羽渡鸦", "霓虹刺猬"],
    "openclaw": ["金爪狮鹫", "风暴蝎尾狮", "曜爪天狮", "赤鬃山猫", "电纹犀鸟", "铜角岩羊"],
    "hermes": ["信风灵隼", "飞翼灵狐", "传令鹿灵", "云足羚羊", "羽冠鼬灵", "风铃飞马"],
    "cursor": ["光标麒麟", "游标星狐", "箭羽灵兽", "流光箭鼬", "星针蜂鸟", "折线灵猫"],
    "mixed": ["星渊麒麟", "棱镜幼龙", "万象奇美拉", "云潮鲲鹿", "星砂貘兽", "晶角鲸马"],
    "all": ["星尘小狐", "晶翼小龙", "雾眠鹿灵", "绒尾星兔", "露光小貘", "铜铃小兽"],
}

CREATURE_MORPHOLOGIES = [
    "unexpected compact silhouette with oversized ears, short legs, and one long ribbon tail",
    "sleek runner silhouette with antlers, fin-like cheek crests, and a split comet tail",
    "round guardian body, tiny wings, gemstone paws, and a floating halo crest",
    "aquatic hybrid body with manta fins, soft horns, and luminous whiskers",
    "bird-mammal silhouette with layered feather cape, small hooves, and a sharp mask-like face",
    "insect-familiar silhouette with glassy wing plates, plush body, and delicate antennae",
    "armored little beast with shell segments, long scarf-like mane, and bright observant eyes",
    "cat-sized chimera with asymmetrical horns, cloud-like fur, and a curled constellation tail",
]

CREATURE_SURFACES = [
    "opal shell, soft fur patches, and small glowing token-like freckles",
    "porcelain face, translucent fins, and brushed-metal edge highlights",
    "velvet dark coat, aurora glass horns, and embroidered circuit-like markings",
    "matte paper texture, ink-wash shadows, and tiny foil sparks",
    "faceted crystal mane, warm enamel scales, and pearlescent claws",
    "wind-worn stone plates, mossy seams, and gentle internal blue light",
    "athletic fabric accents, polished gem joints, and hand-painted streak marks",
    "soft plush silhouette, luminous stitch lines, and constellation dust",
]

CREATURE_POSES = [
    "mid-step as if just entering the frame, calm but alert",
    "curled around the rank emblem like a protective familiar",
    "floating lightly above the layout with a curious sideways glance",
    "leaning forward in a quiet sprint, energetic but elegant",
    "perched on an invisible ledge with one paw raised",
    "turning back over the shoulder, giving the card a candid snapshot feel",
    "sitting upright with ceremonial composure and a small mischievous detail",
    "gliding diagonally through the composition without looking like a standard dragon",
]

CREATURE_ACCENTS = [
    "tiny orbiting token motes",
    "one small celestial compass mark",
    "subtle terminal-grid sparkles",
    "paper talisman ribbons without readable text",
    "miniature glass crown-rays around the head",
    "quiet aurora trail behind the tail",
    "small meteor freckles on the cheeks",
    "low-contrast rune-like geometry with no readable letters",
]

SOURCE_PALETTES = {
    "codex": ("#22D3EE", "#818CF8", "#FDE68A", "#020617", "#F8FAFC"),
    "claude": ("#F97316", "#FDE68A", "#A7F3D0", "#111827", "#FFF7ED"),
    "gemini": ("#60A5FA", "#C084FC", "#F9A8D4", "#0F172A", "#EFF6FF"),
    "opencode": ("#34D399", "#94A3B8", "#FACC15", "#020617", "#ECFDF5"),
    "openclaw": ("#F59E0B", "#EF4444", "#FDE047", "#111827", "#FFFBEB"),
    "hermes": ("#38BDF8", "#2DD4BF", "#F0ABFC", "#082F49", "#F0FDFA"),
    "cursor": ("#A78BFA", "#22C55E", "#FDE047", "#111827", "#FAF5FF"),
    "mixed": ("#F472B6", "#22D3EE", "#FACC15", "#020617", "#F8FAFC"),
    "all": ("#8B5CF6", "#22D3EE", "#FDE68A", "#111827", "#F8FAFC"),
}

DEFAULT_AVG_DAYS = 30
DEFAULT_CACHE_READ_WEIGHT = 0.25
DEFAULT_TOTAL_BENCHMARK = 100_000_000_000
DEFAULT_DAILY_BENCHMARK = 1_000_000_000
DEFAULT_ADVANCED_LEVEL = 64
DEFAULT_LINEAR_UNIT = 1_000_000
DEFAULT_LEVEL_PROFILE = "sqrt"
SQRT_LEVEL_MULTIPLIER = 3.0
DEFAULT_VISUAL_STYLE = "01"
XHS_CANVAS = "1080x1440, vertical 3:4 Xiaohongshu/Rednote-ready image"
XHS_PAGE_SPECS = [
    ("01-cover", "cover"),
    ("02-rank-card", "card"),
    ("03-badge-guide", "badge-guide"),
    ("04-how-to", "how-to"),
    ("05-style-picker", "style-picker"),
]

STYLE_PROFILES = {
    "01": {
        "name": "01 Wanted Newsprint",
        "zh": "01 印刷悬赏令",
        "summary": "classic printed wanted poster, huge WANTED header, portrait-photo panel, bounty line, aged newsprint parchment",
        "avatar": "cropped bounty-photo portrait on aged newsprint parchment, black ink frame, faded sky-blue portrait background, hand-printed adventure texture",
        "card": "single vintage wanted bounty poster, huge WANTED header, central portrait photo panel, DEAD OR ALIVE line, oversized nickname and TOKEN BOUNTY value, aged parchment newsprint, simple black ink border",
        "layout": "wanted poster layout: one main photo, one large name, one large bounty value, small stamp-like rank metrics",
        "palette": "tan parchment, black/brown ink, faded sky blue, muted coral, antique gold accents",
        "template": "wanted",
    },
    "02": {
        "name": "02 Gothic Black Tarot",
        "zh": "02 哥特黑塔罗",
        "summary": "black tarot card, silver ink, cathedral arch, moonlit creature, restrained red stamp",
        "avatar": "moonlit silver animal portrait under a dark cathedral arch, black parchment, silver ink, solemn gothic ornament without readable text",
        "card": "gothic black tarot card, black parchment, silver ink, cathedral arch border, restrained red accent stamps, sacred relic medal, elegant and solemn",
        "layout": "tarot layout: title band, central arched illustration, rank shrine, three small chapel-like metric plaques",
        "palette": "black parchment, bone white, silver ink, muted crimson, faint moon blue",
    },
    "03": {
        "name": "03 Risograph Zine",
        "zh": "03 Riso 独立小报",
        "summary": "risograph zine poster, coral/teal overprint, visible misregistration, grainy paper",
        "avatar": "risograph animal avatar, coral and teal overprint, grainy paper, imperfect registration, charming handmade silhouette",
        "card": "risograph zine poster card, two or three spot colors, visible ink misregistration, rough paper grain, playful mythic animal, stamped metric blocks",
        "layout": "poster-zine layout: relaxed blocks, hand-printed labels, large friendly rank, rough but intentional spacing",
        "palette": "warm cream paper, coral red, teal blue, faded black ink, pale yellow",
    },
    "04": {
        "name": "04 Botanical Alchemy",
        "zh": "04 植物炼金",
        "summary": "botanical alchemy specimen card, emerald glass, gold labels, glowing plants",
        "avatar": "botanical alchemy animal avatar, luminous leaf feathers, emerald-gold particles, glassy dew, living specimen feel",
        "card": "botanical alchemy specimen card, emerald glass, gold apothecary labels, glowing plants, living familiar, elegant laboratory magic",
        "layout": "specimen-card layout: central familiar in a glass-garden scene, brass rank plaque, three apothecary metric labels",
        "palette": "deep green, emerald glass, antique gold, botanical ivory, soft bioluminescent cyan",
    },
    "05": {
        "name": "05 Mono Terminal Poster",
        "zh": "05 黑白终端海报",
        "summary": "monochrome terminal poster, e-ink clarity, sparse grid, editorial restraint",
        "avatar": "black/off-white terminal-style animal silhouette, sparse grid aura, e-ink clarity, no readable code",
        "card": "monochrome terminal poster card, e-ink inspired, sparse grid, few accent pixels, severe and elegant command-output rhythm",
        "layout": "terminal poster layout: large rank and nickname, sparse grid, three clean command-output metric panels",
        "palette": "black, off-white, cool gray, one tiny pale cyan accent",
    },
    "06": {
        "name": "06 Stained Glass Icon",
        "zh": "06 彩窗圣像",
        "summary": "stained-glass icon card, jewel-toned panels, dark lead lines, luminous creature",
        "avatar": "stained-glass animal icon made of luminous glass pieces, dark lead outlines, jewel-tone halo",
        "card": "stained-glass cathedral icon card, jewel-toned panels, luminous animal in a rose window, black lead lines, sacred but modern",
        "layout": "icon-card layout: central rose-window portrait, rank plaque, three small glass medallion metrics",
        "palette": "sapphire, ruby, amber, emerald, black lead lines, warm candlelight",
    },
    "07": {
        "name": "07 Rune Totem",
        "zh": "07 符石图腾",
        "summary": "carved stone totem card, icy blue light, ancient gem medal, guardian spirit",
        "avatar": "animal guardian portrait with carved-stone halo, icy blue glow, ancient gem light, no readable runes",
        "card": "rune totem card, carved stone border, icy blue light, guardian spirit animal, wordless ancient gem medal, engraved rank and metric tablets",
        "layout": "totem layout: stone frame, central guardian, rank carved into stone, metrics on rune-like tablets without readable rune text",
        "palette": "charcoal stone, icy blue, silver, muted slate, small aurora gem color",
    },
    "08": {
        "name": "08 Airy Instagram Story",
        "zh": "08 留白 Ins Story",
        "summary": "airy Instagram-story card, warm white space, tiny relaxed illustration, thin typography",
        "avatar": "minimal animal avatar on warm white background, tiny calm subject, soft shadow, one small token sparkle",
        "card": "airy Instagram story card, 70 percent warm white negative space, small relaxed animal illustration, thin sans typography, muted beige and sky palette",
        "layout": "social-story layout: lots of blank space, small illustration near lower third, understated rank and metrics as elegant captions",
        "palette": "warm white, beige, misty sky blue, soft charcoal, tiny coral dot",
    },
    "09": {
        "name": "09 Editorial Magazine Cover",
        "zh": "09 编辑杂志封面",
        "summary": "modern editorial magazine cover, generous margins, confident portrait, feature-style callouts",
        "avatar": "editorial studio portrait crop of a mythic animal, soft lifestyle lighting, refined magazine-cover polish",
        "card": "modern editorial magazine cover, generous margins, confident animal portrait, refined masthead, feature-style callouts for rank and metrics",
        "layout": "magazine-cover layout: large masthead, portrait crop, side callouts, sophisticated whitespace and hierarchy",
        "palette": "warm gray, ivory, soft black, muted bronze, desaturated blue",
    },
    "10": {
        "name": "10 Fashion Lookbook Anthro",
        "zh": "10 时装拟人造型",
        "summary": "fashion lookbook card, anthropomorphic animal in oversized minimal jacket, studio backdrop",
        "avatar": "anthropomorphic animal fashion portrait in an oversized jacket, relaxed pose, editorial studio light, no logos",
        "card": "fashion lookbook card, anthropomorphic animal in oversized minimal jacket, clean studio backdrop, tiny typography, stylish and relaxed",
        "layout": "lookbook layout: full or half-body fashion portrait, look-number rank, metrics as product-spec captions",
        "palette": "off-white studio, olive gray, charcoal, muted gold, soft shadow",
    },
    "11": {
        "name": "11 Luxury Membership Pass",
        "zh": "11 极简会员通行证",
        "summary": "luxury membership pass, matte ivory, embossed monogram, sparse foil lines",
        "avatar": "embossed animal monogram or profile on matte ivory paper, subtle gold foil, quiet premium surface",
        "card": "luxury membership pass, matte ivory card, small embossed animal monogram mark, large quiet rank, sparse foil metric lines",
        "layout": "membership-pass layout: ultra-minimal white space, embossed mark, large rank, sparse aligned metrics",
        "palette": "matte ivory, black, champagne gold foil, warm gray",
    },
    "12": {
        "name": "12 Running Club Bib",
        "zh": "12 跑者号码布",
        "summary": "fictional running club bib card, anthropomorphic runner, lap-split metrics, clean sport graphics",
        "avatar": "anthropomorphic animal runner with abstract bib shape, dynamic stride, clean sport colors, no logos",
        "card": "fictional running club bib card, anthropomorphic animal runner, race-bib rank number, lap-split metrics, friendly athletic energy",
        "layout": "race-bib layout: huge bib number/rank, action runner, split-time style metric blocks, no real event marks",
        "palette": "white, racing red, cobalt blue, black, small warm highlight",
    },
}


@dataclasses.dataclass
class UsageRecord:
    date: dt.date
    source: str
    total_tokens: int
    weighted_tokens: int
    model_totals: Dict[str, int] = dataclasses.field(default_factory=dict)
    model_weighted_totals: Dict[str, int] = dataclasses.field(default_factory=dict)
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0
    cost_usd: Optional[float] = None
    origin: str = "extra"


@dataclasses.dataclass
class UsageSummary:
    total_tokens: int
    weighted_tokens: int
    input_tokens: int
    output_tokens: int
    cache_creation_tokens: int
    cache_read_tokens: int
    first_date: Optional[dt.date]
    last_date: Optional[dt.date]
    active_days: int
    current_streak_days: int
    latest_active_streak_days: int
    longest_streak_days: int
    avg_calendar_tokens: float
    avg_calendar_weighted_tokens: float
    avg_active_tokens: float
    avg_active_weighted_tokens: float
    current_streak_tokens: int
    current_streak_weighted_tokens: int
    avg_current_streak_tokens: float
    avg_current_streak_weighted_tokens: float
    window_tokens: int
    window_weighted_tokens: int
    effective_window_days: int
    avg_window_tokens: float
    avg_window_weighted_tokens: float
    window_tokens_excluding_today: int
    window_weighted_tokens_excluding_today: int
    effective_window_days_excluding_today: int
    avg_window_tokens_including_today: float
    avg_window_weighted_tokens_including_today: float
    avg_window_tokens_excluding_today: float
    avg_window_weighted_tokens_excluding_today: float
    window_days: int
    source_totals: Dict[str, int]
    source_weighted_totals: Dict[str, int]
    source_window_totals: Dict[str, int]
    source_window_weighted_totals: Dict[str, int]
    model_totals: Dict[str, int]
    model_weighted_totals: Dict[str, int]
    model_window_totals: Dict[str, int]
    model_window_weighted_totals: Dict[str, int]
    records: List[UsageRecord]


@dataclasses.dataclass
class LevelResult:
    level: int
    level_float: float
    profile: str
    total_level: float
    daily_level: float
    linear_score_tokens: int
    total_benchmark: int
    daily_benchmark: int
    advanced_level: int


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def stable_seed(*parts: Any) -> int:
    raw = "|".join(map(str, parts)).encode("utf-8")
    return int(hashlib.sha256(raw).hexdigest()[:16], 16)


def parse_date(value: Any) -> Optional[dt.date]:
    if value is None or value == "":
        return None
    if isinstance(value, dt.date) and not isinstance(value, dt.datetime):
        return value
    text = str(value).strip()
    if len(text) == 8 and text.isdigit():
        try:
            return dt.datetime.strptime(text, "%Y%m%d").date()
        except ValueError:
            return None
    if len(text) >= 10:
        head = text[:10]
        try:
            return dt.datetime.strptime(head, "%Y-%m-%d").date()
        except ValueError:
            pass
    try:
        return dt.datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def get_int(obj: Dict[str, Any], *keys: str) -> int:
    for key in keys:
        if key in obj and obj[key] is not None:
            try:
                return int(float(obj[key]))
            except (TypeError, ValueError):
                pass
    return 0


def get_float(obj: Dict[str, Any], *keys: str) -> Optional[float]:
    for key in keys:
        if key in obj and obj[key] is not None:
            try:
                return float(obj[key])
            except (TypeError, ValueError):
                pass
    return None


def normalize_source(value: Any, fallback: str = "all") -> str:
    source = str(value or fallback).strip().lower().replace(" ", "-")
    aliases = {
        "claude-code": "claude",
        "gemini-cli": "gemini",
        "github-copilot": "copilot",
        "github-copilot-cli": "copilot",
        "pi-agent": "pi",
    }
    return aliases.get(source, source or fallback)


def safe_label(value: Any, max_len: int = 42) -> str:
    text = " ".join(str(value or "").replace("\x00", "").split())
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def model_name_from_obj(obj: Dict[str, Any]) -> str:
    for key in ("modelName", "model_name", "model", "modelId", "model_id", "name"):
        label = safe_label(obj.get(key))
        if label:
            return label
    return ""


def model_token_totals_from_obj(
    obj: Dict[str, Any],
    fallback_total: int,
    fallback_weighted: int,
    cache_read_weight: float,
) -> Tuple[Dict[str, int], Dict[str, int]]:
    raw_totals: Dict[str, int] = {}
    weighted_totals: Dict[str, int] = {}

    def add_model(name: Any, raw_value: int, weighted_value: int) -> None:
        label = safe_label(name)
        if not label:
            return
        if raw_value <= 0 and weighted_value <= 0:
            return
        raw_totals[label] = raw_totals.get(label, 0) + max(0, int(raw_value))
        weighted_totals[label] = weighted_totals.get(label, 0) + max(0, int(weighted_value))

    breakdowns = obj.get("modelBreakdowns") or obj.get("model_breakdowns") or obj.get("models")
    if isinstance(breakdowns, list):
        for item in breakdowns:
            if not isinstance(item, dict):
                continue
            name = model_name_from_obj(item)
            raw = get_int(item, "totalTokens", "total_tokens", "tokens", "tokenCount", "total")
            input_tokens = get_int(item, "inputTokens", "input_tokens", "promptTokens", "prompt_tokens")
            output_tokens = get_int(item, "outputTokens", "output_tokens", "completionTokens", "completion_tokens")
            cache_creation = get_int(
                item,
                "cacheCreationTokens",
                "cache_creation_tokens",
                "cacheCreateTokens",
                "cacheWriteTokens",
                "cacheCreationInputTokens",
            )
            cache_read = get_int(
                item,
                "cacheReadTokens",
                "cache_read_tokens",
                "cachedInputTokens",
                "cacheHitTokens",
                "cacheReadInputTokens",
            )
            detail_sum = input_tokens + output_tokens + cache_creation + cache_read
            if raw <= 0:
                raw = detail_sum
            weighted = (
                input_tokens + output_tokens + cache_creation + int(cache_read * cache_read_weight)
                if detail_sum > 0
                else raw
            )
            add_model(name, raw, weighted)
    elif isinstance(breakdowns, dict):
        for name, value in breakdowns.items():
            if isinstance(value, dict):
                raw = get_int(value, "totalTokens", "total_tokens", "tokens", "tokenCount", "total")
                input_tokens = get_int(value, "inputTokens", "input_tokens", "promptTokens", "prompt_tokens")
                output_tokens = get_int(value, "outputTokens", "output_tokens", "completionTokens", "completion_tokens")
                cache_creation = get_int(
                    value,
                    "cacheCreationTokens",
                    "cache_creation_tokens",
                    "cacheCreateTokens",
                    "cacheWriteTokens",
                    "cacheCreationInputTokens",
                )
                cache_read = get_int(
                    value,
                    "cacheReadTokens",
                    "cache_read_tokens",
                    "cachedInputTokens",
                    "cacheHitTokens",
                    "cacheReadInputTokens",
                )
                detail_sum = input_tokens + output_tokens + cache_creation + cache_read
                if raw <= 0:
                    raw = detail_sum
                weighted = (
                    input_tokens + output_tokens + cache_creation + int(cache_read * cache_read_weight)
                    if detail_sum > 0
                    else raw
                )
                add_model(value.get("modelName") or value.get("model") or name, raw, weighted)
            else:
                try:
                    raw = int(float(value))
                except (TypeError, ValueError):
                    raw = 0
                add_model(name, raw, raw)

    single_model = model_name_from_obj(obj)
    if single_model and not raw_totals:
        add_model(single_model, fallback_total, fallback_weighted)

    return raw_totals, weighted_totals


def record_from_obj(
    obj: Dict[str, Any],
    fallback_source: str,
    origin: str,
    cache_read_weight: float,
) -> Optional[UsageRecord]:
    date_value = (
        obj.get("date")
        or obj.get("day")
        or obj.get("period")
        or obj.get("blockStart")
        or obj.get("firstActivity")
        or obj.get("lastActivity")
        or obj.get("timestamp")
    )
    day = parse_date(date_value)
    if day is None:
        return None

    total = get_int(obj, "totalTokens", "total_tokens", "tokens", "tokenCount", "total")
    input_tokens = get_int(obj, "inputTokens", "input_tokens", "promptTokens", "prompt_tokens")
    output_tokens = get_int(obj, "outputTokens", "output_tokens", "completionTokens", "completion_tokens")
    cache_creation = get_int(
        obj,
        "cacheCreationTokens",
        "cache_creation_tokens",
        "cacheCreateTokens",
        "cacheWriteTokens",
        "cacheCreationInputTokens",
    )
    cache_read = get_int(
        obj,
        "cacheReadTokens",
        "cache_read_tokens",
        "cachedInputTokens",
        "cacheHitTokens",
        "cacheReadInputTokens",
    )
    detail_sum = input_tokens + output_tokens + cache_creation + cache_read
    if total <= 0:
        total = detail_sum
    if total <= 0:
        return None

    if detail_sum > 0:
        weighted = input_tokens + output_tokens + cache_creation + int(cache_read * cache_read_weight)
    else:
        weighted = total

    source = normalize_source(
        obj.get("agent") or obj.get("source") or obj.get("provider") or obj.get("cli"),
        fallback_source,
    )
    model_totals, model_weighted_totals = model_token_totals_from_obj(
        obj,
        total,
        max(0, weighted),
        cache_read_weight,
    )
    return UsageRecord(
        date=day,
        source=source,
        total_tokens=total,
        weighted_tokens=max(0, weighted),
        model_totals=model_totals,
        model_weighted_totals=model_weighted_totals,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_creation_tokens=cache_creation,
        cache_read_tokens=cache_read,
        cost_usd=get_float(obj, "totalCost", "costUSD", "cost_usd", "cost"),
        origin=origin,
    )


def parse_usage_json(
    payload: Any,
    fallback_source: str,
    origin: str,
    cache_read_weight: float,
) -> List[UsageRecord]:
    if isinstance(payload, str):
        payload = json.loads(payload)

    records: List[UsageRecord] = []
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                rec = record_from_obj(item, fallback_source, origin, cache_read_weight)
                if rec:
                    records.append(rec)
        return records

    if not isinstance(payload, dict):
        return records

    direct = record_from_obj(payload, fallback_source, origin, cache_read_weight)
    if direct:
        records.append(direct)

    for key in ("daily", "data", "rows", "items", "entries", "days", "usage"):
        value = payload.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    rec = record_from_obj(item, fallback_source, origin, cache_read_weight)
                    if rec:
                        records.append(rec)

    projects = payload.get("projects")
    if isinstance(projects, dict):
        for days in projects.values():
            if isinstance(days, list):
                for item in days:
                    if isinstance(item, dict):
                        rec = record_from_obj(item, fallback_source, origin, cache_read_weight)
                        if rec:
                            records.append(rec)

    if not records:
        totals = payload.get("totals") or payload.get("summary")
        if isinstance(totals, dict):
            today = dt.date.today()
            synthetic = dict(totals)
            synthetic.setdefault("date", today.isoformat())
            rec = record_from_obj(synthetic, fallback_source, origin, cache_read_weight)
            if rec:
                records.append(rec)

    return records


def run_command(command: Sequence[str], timeout: int) -> Tuple[bool, str, str]:
    try:
        proc = subprocess.run(
            list(command),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    except FileNotFoundError as ex:
        return False, "", str(ex)
    except subprocess.TimeoutExpired:
        return False, "", f"Timed out after {timeout}s"
    if proc.returncode != 0:
        return False, proc.stdout, proc.stderr.strip() or f"exit {proc.returncode}"
    return True, proc.stdout, proc.stderr.strip()


def resolve_ccusage_runner(allow_download_runner: bool) -> Optional[List[str]]:
    if shutil.which("ccusage"):
        return ["ccusage"]
    if not allow_download_runner:
        return None
    if shutil.which("bunx"):
        return ["bunx", "ccusage"]
    if shutil.which("npx"):
        return ["npx", "ccusage@latest"]
    if shutil.which("pnpm"):
        return ["pnpm", "dlx", "ccusage"]
    return None


def collect_from_ccusage(args: argparse.Namespace) -> Tuple[List[UsageRecord], List[str]]:
    runner = resolve_ccusage_runner(args.allow_download_runner)
    warnings: List[str] = []
    if runner is None:
        warnings.append("未找到 ccusage；如需临时运行 bunx/npx/pnpm，请显式加 --allow-download-runner。")
        return [], warnings

    date_args: List[str] = []
    if args.since:
        date_args.extend(["--since", args.since])
    if args.until:
        date_args.extend(["--until", args.until])

    records: List[UsageRecord] = []
    ok, stdout, stderr = run_command(runner + ["daily", "--json", "--no-cost"] + date_args, args.timeout)
    if ok:
        try:
            records.extend(parse_usage_json(stdout, "all", "ccusage-unified", args.cache_read_weight))
        except Exception as ex:  # noqa: BLE001 - JSON shapes vary across ccusage versions.
            warnings.append(f"ccusage 统一报告 JSON 解析失败：{ex}")
    else:
        warnings.append(f"ccusage 统一报告失败：{stderr}")

    if args.skip_source_breakdown:
        return records, warnings

    if args.sources in ("", "auto", "all"):
        sources = KNOWN_CCUSAGE_SOURCES
    else:
        sources = [s.strip().lower() for s in args.sources.split(",") if s.strip()]

    for source in sources:
        if source == "cursor":
            continue
        ok, stdout, stderr = run_command(
            runner + [source, "daily", "--json", "--no-cost"] + date_args,
            args.timeout,
        )
        if not ok:
            if args.verbose:
                warnings.append(f"{source} 聚焦报告不可用：{stderr}")
            continue
        try:
            parsed = parse_usage_json(stdout, source, "ccusage-source", args.cache_read_weight)
            for rec in parsed:
                rec.source = source
            records.extend(parsed)
        except Exception as ex:  # noqa: BLE001
            warnings.append(f"{source} 聚焦报告 JSON 解析失败：{ex}")

    return records, warnings


def collect_from_extra_commands(args: argparse.Namespace) -> Tuple[List[UsageRecord], List[str]]:
    records: List[UsageRecord] = []
    warnings: List[str] = []
    for spec in args.extra_command:
        if ":" not in spec:
            warnings.append(f"忽略 extra-command，格式应为 source:command：{spec}")
            continue
        source, command = spec.split(":", 1)
        source = normalize_source(source)
        try:
            proc = subprocess.run(
                command,
                shell=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=args.timeout,
            )
        except subprocess.TimeoutExpired:
            warnings.append(f"额外适配器超时：{source}")
            continue
        if proc.returncode != 0:
            warnings.append(f"额外适配器失败 {source}：{proc.stderr.strip() or proc.returncode}")
            continue
        try:
            parsed = parse_usage_json(proc.stdout, source, "extra", args.cache_read_weight)
            for rec in parsed:
                rec.source = source
            records.extend(parsed)
        except Exception as ex:  # noqa: BLE001
            warnings.append(f"额外适配器 JSON 解析失败 {source}：{ex}")
    return records, warnings


def summarize(records: List[UsageRecord], window_days: int, window_end: Optional[dt.date]) -> UsageSummary:
    unified = [r for r in records if r.origin == "ccusage-unified"]
    cc_sources = [r for r in records if r.origin == "ccusage-source"]
    extras = [r for r in records if r.origin == "extra"]
    primary = (unified if unified else cc_sources) + extras

    raw_by_day: Dict[dt.date, int] = {}
    weighted_by_day: Dict[dt.date, int] = {}
    input_tokens = output_tokens = cache_creation = cache_read = 0
    for rec in primary:
        raw_by_day[rec.date] = raw_by_day.get(rec.date, 0) + rec.total_tokens
        weighted_by_day[rec.date] = weighted_by_day.get(rec.date, 0) + rec.weighted_tokens
        input_tokens += rec.input_tokens
        output_tokens += rec.output_tokens
        cache_creation += rec.cache_creation_tokens
        cache_read += rec.cache_read_tokens

    total = sum(raw_by_day.values())
    weighted_total = sum(weighted_by_day.values())
    first = min(raw_by_day) if raw_by_day else None
    last = max(raw_by_day) if raw_by_day else None
    active_dates = {day for day, value in raw_by_day.items() if value > 0}
    active_days = len(active_dates)
    calendar_days = ((last - first).days + 1) if first and last else 0
    avg_calendar = total / calendar_days if calendar_days else 0.0
    avg_calendar_weighted = weighted_total / calendar_days if calendar_days else 0.0
    avg_active = total / active_days if active_days else 0.0
    avg_active_weighted = weighted_total / active_days if active_days else 0.0

    if window_end is None:
        window_end = dt.date.today()
    current_streak = consecutive_streak_ending_at(active_dates, window_end)
    latest_active_streak = consecutive_streak_ending_at(active_dates, last) if last else 0
    longest_streak = longest_consecutive_streak(active_dates)
    if current_streak > 0:
        streak_start = window_end - dt.timedelta(days=current_streak - 1)
        current_streak_tokens = sum(value for day, value in raw_by_day.items() if streak_start <= day <= window_end)
        current_streak_weighted = sum(value for day, value in weighted_by_day.items() if streak_start <= day <= window_end)
    else:
        current_streak_tokens = 0
        current_streak_weighted = 0
    avg_current_streak = current_streak_tokens / current_streak if current_streak else 0.0
    avg_current_streak_weighted = current_streak_weighted / current_streak if current_streak else 0.0

    effective_window_days = max(1, window_days)
    effective_window_start: Optional[dt.date] = None
    if raw_by_day:
        nominal_window_start = window_end - dt.timedelta(days=max(1, window_days) - 1)
        effective_window_start = max(nominal_window_start, first) if first else nominal_window_start
        if effective_window_start <= window_end:
            effective_window_days = (window_end - effective_window_start).days + 1
            window_total = sum(value for day, value in raw_by_day.items() if effective_window_start <= day <= window_end)
            window_weighted = sum(value for day, value in weighted_by_day.items() if effective_window_start <= day <= window_end)
        else:
            effective_window_days = 0
            window_total = 0
            window_weighted = 0
    else:
        effective_window_days = 0
        window_total = 0
        window_weighted = 0
    avg_window_including_today = window_total / max(1, effective_window_days)
    avg_window_weighted_including_today = window_weighted / max(1, effective_window_days)

    today = dt.date.today()
    window_total_excluding_today = window_total
    window_weighted_excluding_today = window_weighted
    effective_window_days_excluding_today = effective_window_days
    if raw_by_day and effective_window_start and effective_window_start <= today <= window_end:
        complete_window_end = today - dt.timedelta(days=1)
        nominal_complete_window_start = complete_window_end - dt.timedelta(days=max(1, window_days) - 1)
        effective_complete_window_start = max(nominal_complete_window_start, first) if first else nominal_complete_window_start
        if effective_complete_window_start <= complete_window_end:
            effective_window_days_excluding_today = (complete_window_end - effective_complete_window_start).days + 1
            window_total_excluding_today = sum(
                value for day, value in raw_by_day.items() if effective_complete_window_start <= day <= complete_window_end
            )
            window_weighted_excluding_today = sum(
                value for day, value in weighted_by_day.items() if effective_complete_window_start <= day <= complete_window_end
            )
        else:
            effective_window_days_excluding_today = 0
            window_total_excluding_today = 0
            window_weighted_excluding_today = 0
    avg_window_excluding_today = window_total_excluding_today / max(1, effective_window_days_excluding_today)
    avg_window_weighted_excluding_today = window_weighted_excluding_today / max(
        1, effective_window_days_excluding_today
    )
    avg_window = max(avg_window_including_today, avg_window_excluding_today)
    avg_window_weighted = max(avg_window_weighted_including_today, avg_window_weighted_excluding_today)

    source_totals: Dict[str, int] = {}
    source_weighted: Dict[str, int] = {}
    source_window_totals: Dict[str, int] = {}
    source_window_weighted: Dict[str, int] = {}
    source_basis = cc_sources if cc_sources else unified
    if source_basis:
        for rec in source_basis:
            source_totals[rec.source] = source_totals.get(rec.source, 0) + rec.total_tokens
            source_weighted[rec.source] = source_weighted.get(rec.source, 0) + rec.weighted_tokens
            if effective_window_start and effective_window_start <= rec.date <= window_end:
                source_window_totals[rec.source] = source_window_totals.get(rec.source, 0) + rec.total_tokens
                source_window_weighted[rec.source] = source_window_weighted.get(rec.source, 0) + rec.weighted_tokens
    for rec in extras:
        source_totals[rec.source] = source_totals.get(rec.source, 0) + rec.total_tokens
        source_weighted[rec.source] = source_weighted.get(rec.source, 0) + rec.weighted_tokens
        if effective_window_start and effective_window_start <= rec.date <= window_end:
            source_window_totals[rec.source] = source_window_totals.get(rec.source, 0) + rec.total_tokens
            source_window_weighted[rec.source] = source_window_weighted.get(rec.source, 0) + rec.weighted_tokens

    if not source_totals and total > 0:
        source_totals["all"] = total
        source_weighted["all"] = weighted_total
    if not source_window_totals and window_total > 0:
        source_window_totals["all"] = window_total
        source_window_weighted["all"] = window_weighted

    model_totals: Dict[str, int] = {}
    model_weighted: Dict[str, int] = {}
    model_window_totals: Dict[str, int] = {}
    model_window_weighted: Dict[str, int] = {}
    for rec in primary:
        for model, value in rec.model_totals.items():
            if value <= 0:
                continue
            model_totals[model] = model_totals.get(model, 0) + value
            model_weighted[model] = model_weighted.get(model, 0) + rec.model_weighted_totals.get(model, value)
            if effective_window_start and effective_window_start <= rec.date <= window_end:
                model_window_totals[model] = model_window_totals.get(model, 0) + value
                model_window_weighted[model] = (
                    model_window_weighted.get(model, 0) + rec.model_weighted_totals.get(model, value)
                )

    return UsageSummary(
        total_tokens=total,
        weighted_tokens=weighted_total,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_creation_tokens=cache_creation,
        cache_read_tokens=cache_read,
        first_date=first,
        last_date=last,
        active_days=active_days,
        current_streak_days=current_streak,
        latest_active_streak_days=latest_active_streak,
        longest_streak_days=longest_streak,
        avg_calendar_tokens=avg_calendar,
        avg_calendar_weighted_tokens=avg_calendar_weighted,
        avg_active_tokens=avg_active,
        avg_active_weighted_tokens=avg_active_weighted,
        current_streak_tokens=current_streak_tokens,
        current_streak_weighted_tokens=current_streak_weighted,
        avg_current_streak_tokens=avg_current_streak,
        avg_current_streak_weighted_tokens=avg_current_streak_weighted,
        window_tokens=window_total,
        window_weighted_tokens=window_weighted,
        effective_window_days=effective_window_days,
        avg_window_tokens=avg_window,
        avg_window_weighted_tokens=avg_window_weighted,
        window_tokens_excluding_today=window_total_excluding_today,
        window_weighted_tokens_excluding_today=window_weighted_excluding_today,
        effective_window_days_excluding_today=effective_window_days_excluding_today,
        avg_window_tokens_including_today=avg_window_including_today,
        avg_window_weighted_tokens_including_today=avg_window_weighted_including_today,
        avg_window_tokens_excluding_today=avg_window_excluding_today,
        avg_window_weighted_tokens_excluding_today=avg_window_weighted_excluding_today,
        window_days=window_days,
        source_totals=source_totals,
        source_weighted_totals=source_weighted,
        source_window_totals=source_window_totals,
        source_window_weighted_totals=source_window_weighted,
        model_totals=model_totals,
        model_weighted_totals=model_weighted,
        model_window_totals=model_window_totals,
        model_window_weighted_totals=model_window_weighted,
        records=primary,
    )


def consecutive_streak_ending_at(active_dates: Iterable[dt.date], end_date: Optional[dt.date]) -> int:
    if end_date is None:
        return 0
    active = set(active_dates)
    if end_date not in active:
        return 0
    streak = 0
    cursor = end_date
    while cursor in active:
        streak += 1
        cursor -= dt.timedelta(days=1)
    return streak


def longest_consecutive_streak(active_dates: Iterable[dt.date]) -> int:
    active = set(active_dates)
    longest = 0
    for day in active:
        if day - dt.timedelta(days=1) in active:
            continue
        cursor = day
        streak = 0
        while cursor in active:
            streak += 1
            cursor += dt.timedelta(days=1)
        longest = max(longest, streak)
    return longest


def compute_level(summary: UsageSummary, args: argparse.Namespace) -> LevelResult:
    score = summary.weighted_tokens + summary.window_weighted_tokens
    if args.level_profile == "sqrt":
        score_m = score / max(1, args.unit)
        total_level = SQRT_LEVEL_MULTIPLIER * math.sqrt(max(0.0, summary.weighted_tokens / max(1, args.unit)))
        daily_level = SQRT_LEVEL_MULTIPLIER * math.sqrt(max(0.0, summary.window_weighted_tokens / max(1, args.unit)))
        level_float = SQRT_LEVEL_MULTIPLIER * math.sqrt(max(0.0, score_m))
        level = int(math.floor(level_float))
        if score > 0 and level < 1:
            level = 1
        return LevelResult(
            level=level,
            level_float=level_float,
            profile="sqrt",
            total_level=total_level,
            daily_level=daily_level,
            linear_score_tokens=score,
            total_benchmark=args.total_benchmark,
            daily_benchmark=args.daily_benchmark,
            advanced_level=args.advanced_level,
        )

    if args.level_profile == "linear":
        level_float = score / max(1, args.unit)
        level = int(math.floor(level_float))
        if score > 0 and level < 1:
            level = 1
        return LevelResult(
            level=level,
            level_float=level_float,
            profile="linear",
            total_level=level_float,
            daily_level=0.0,
            linear_score_tokens=score,
            total_benchmark=args.total_benchmark,
            daily_benchmark=args.daily_benchmark,
            advanced_level=args.advanced_level,
        )

    total_level = args.advanced_level * math.sqrt(
        max(0.0, summary.weighted_tokens / max(1, args.total_benchmark))
    )
    daily_level = args.advanced_level * math.sqrt(
        max(0.0, summary.avg_window_weighted_tokens / max(1, args.daily_benchmark))
    )
    level_float = max(total_level, daily_level) + 0.25 * min(total_level, daily_level)
    level = int(math.floor(level_float))
    if (summary.weighted_tokens > 0 or summary.avg_window_weighted_tokens > 0) and level < 1:
        level = 1
    return LevelResult(
        level=level,
        level_float=level_float,
        profile="benchmark",
        total_level=total_level,
        daily_level=daily_level,
        linear_score_tokens=summary.weighted_tokens + summary.window_weighted_tokens,
        total_benchmark=args.total_benchmark,
        daily_benchmark=args.daily_benchmark,
        advanced_level=args.advanced_level,
    )


def decompose_level(level: int) -> Dict[str, int]:
    rest = max(0, int(level))
    t_medal = rest // 256
    rest %= 256
    crown = rest // 64
    rest %= 64
    sun = rest // 16
    rest %= 16
    moon = rest // 4
    star = rest % 4
    return {"t_medal": t_medal, "crown": crown, "sun": sun, "moon": moon, "star": star}


def visible_level_parts(level: int, max_tiers: int = 2) -> Dict[str, int]:
    parts = decompose_level(level)
    visible = {key: 0 for key in parts}
    shown = 0
    for key in ("t_medal", "crown", "sun", "moon", "star"):
        if parts[key] <= 0:
            continue
        if shown >= max_tiers:
            break
        visible[key] = parts[key]
        shown += 1
    return visible


def level_symbols(level: int, max_tiers: Optional[int] = 2) -> str:
    parts = decompose_level(level)
    if max_tiers is not None:
        parts = visible_level_parts(level, max_tiers)
    labels = [
        ("T勋章", parts["t_medal"]),
        ("皇冠", parts["crown"]),
        ("太阳", parts["sun"]),
        ("月亮", parts["moon"]),
        ("星星", parts["star"]),
    ]
    shown = [f"{count}{label}" for label, count in labels if count]
    return " ".join(shown) if shown else "未觉醒"


def full_level_symbols(level: int) -> str:
    return level_symbols(level, max_tiers=None)


def rank_title(level: int) -> str:
    if level >= 256:
        return "终阶 · Token 神兽使"
    if level >= 64:
        return "皇冠 · 造物架构师"
    if level >= 16:
        return "太阳 · 日冕炼码师"
    if level >= 4:
        return "月亮 · 月相织码师"
    if level >= 1:
        return "星星 · 星尘初醒者"
    return "未觉醒 · 等待第一束提示词"


def human_tokens(value: float) -> str:
    value = float(value)
    if value >= 1_000_000_000_000:
        return f"{value / 1_000_000_000_000:.2f}T"
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(int(value))


def human_tokens_zh(value: float, public_safe: bool = False) -> str:
    value = float(value)
    if value >= 100_000_000:
        yi = value / 100_000_000
        if public_safe:
            if yi >= 100:
                return f"约{round(yi / 10) * 10:.0f}亿"
            return f"约{yi:.0f}亿"
        if yi >= 100:
            return f"约{yi:.0f}亿"
        if yi >= 10:
            return f"约{yi:.1f}亿"
        return f"约{yi:.2f}亿"
    if value >= 10_000:
        wan = value / 10_000
        if public_safe:
            return f"约{wan:.0f}万"
        if wan >= 100:
            return f"约{wan:.0f}万"
        return f"约{wan:.1f}万"
    if public_safe and value >= 1000:
        return f"约{round(value / 1000) * 1000:.0f}"
    return f"约{int(round(value))}"


def format_tokens(value: float, display_unit: str = "compact", public_safe: bool = False) -> str:
    if display_unit == "zh":
        return human_tokens_zh(value, public_safe)
    if not public_safe:
        return human_tokens(value)
    value = float(value)
    if value >= 1_000_000_000_000:
        return f"~{value / 1_000_000_000_000:.1f}T"
    if value >= 1_000_000_000:
        return f"~{value / 1_000_000_000:.1f}B"
    if value >= 1_000_000:
        return f"~{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"~{value / 1_000:.0f}K"
    return f"~{int(round(value))}"


def resolve_display_unit(display_unit: str, mode: str, platform: str) -> str:
    if display_unit != "auto":
        return display_unit
    return "zh" if mode == "xhs-pack" or platform == "xhs" else "compact"


def comma_int(value: float) -> str:
    return f"{int(round(value)):,}"


def style_profile(visual_style: str) -> Dict[str, str]:
    return STYLE_PROFILES.get(visual_style, STYLE_PROFILES[DEFAULT_VISUAL_STYLE])


def display_window_prefix(summary: UsageSummary) -> str:
    return display_window_prefix_for_days(summary, summary.effective_window_days)


def display_window_prefix_for_days(summary: UsageSummary, effective_days: int) -> str:
    if effective_days <= 0:
        return f"近{summary.window_days}天"
    if effective_days < summary.window_days:
        return f"全部{effective_days}天"
    return f"近{summary.window_days}天"


def headline_total_metric(summary: UsageSummary) -> Tuple[str, float]:
    return f"{display_window_prefix(summary)}总量", float(summary.window_tokens)


def headline_daily_metric(summary: UsageSummary) -> Tuple[str, float, float]:
    use_excluding_today = summary.avg_window_tokens_excluding_today > summary.avg_window_tokens_including_today
    effective_days = (
        summary.effective_window_days_excluding_today if use_excluding_today else summary.effective_window_days
    )
    return (
        f"{display_window_prefix_for_days(summary, effective_days)}日均",
        summary.avg_window_tokens,
        summary.avg_window_weighted_tokens,
    )


def dominant_source(summary: UsageSummary) -> str:
    source_weighted_totals = summary.source_window_weighted_totals or summary.source_weighted_totals
    ranked = [
        (source, value)
        for source, value in source_weighted_totals.items()
        if source not in ("all", "unknown") and value > 0
    ]
    if not ranked:
        return "all"
    ranked.sort(key=lambda item: item[1], reverse=True)
    if len(ranked) >= 2 and ranked[1][1] >= ranked[0][1] * 0.7:
        return "mixed"
    return ranked[0][0]


def palette_for(source: str, seed: int) -> Tuple[str, str, str, str, str]:
    if source in SOURCE_PALETTES:
        return SOURCE_PALETTES[source]
    palettes = list(SOURCE_PALETTES.values())
    return palettes[seed % len(palettes)]


def pick_creature(nickname: str, level: int, source: str, total: int, visual_style: str = "", variation_seed: str = "") -> str:
    seed = stable_seed("creature-v2", nickname, level, source, total, visual_style, variation_seed)
    if source in SOURCE_CREATURES:
        pool = SOURCE_CREATURES[source]
    elif level >= 64:
        pool = SOURCE_CREATURES["mixed"]
    else:
        pool = SOURCE_CREATURES["all"]
    return pool[seed % len(pool)]


def creature_variation_lines(
    nickname: str,
    level: int,
    source: str,
    total: int,
    visual_style: str,
    variation_seed: str = "",
) -> str:
    rng = random.Random(stable_seed("creature-variation-v2", nickname, level, source, total, visual_style, variation_seed))
    morphology = rng.choice(CREATURE_MORPHOLOGIES)
    surface = rng.choice(CREATURE_SURFACES)
    pose = rng.choice(CREATURE_POSES)
    accents = rng.sample(CREATURE_ACCENTS, 2)
    return "\n".join(
        [
            f"- Shape variation: {morphology}.",
            f"- Surface/material mix: {surface}.",
            f"- Pose/personality: {pose}.",
            f"- Small accents: {accents[0]} and {accents[1]}.",
            "- Randomness rule: treat the named species as a loose seed, not a fixed mascot. Make the creature feel fresh and visibly different across generations; avoid defaulting to a standard dragon, qilin, fox, wolf, or humanoid athlete unless the selected style explicitly needs that silhouette.",
        ]
    )


def elegant_copy(level: int, creature: str) -> str:
    # Kept as fallback for older calls; render_card_svg uses metric-aware copy.
    if level >= 256:
        return f"{creature}已越过万象之门，把每一次提示词炼成可运行的星河。"
    if level >= 64:
        return f"{creature}踏着皇冠光尘前行，复杂系统也在指尖安静成形。"
    if level >= 16:
        return f"{creature}衔来日冕之火，把漫长上下文照成清晰的路径。"
    if level >= 4:
        return f"{creature}在月相之间巡游，灵感被一次次编译成现实。"
    if level >= 1:
        return f"{creature}刚点亮第一颗星，代码的秘境已经回应你的召唤。"
    return "还没有可统计的本机 token 足迹；第一颗星，正在终端深处等待。"


def band(value: float, thresholds: Sequence[float]) -> int:
    result = 0
    for threshold in thresholds:
        if value >= threshold:
            result += 1
    return result


def elegant_metric_copy(level: int, creature: str, summary: UsageSummary) -> str:
    if level <= 0:
        return "还没有可统计的本机 token 足迹；第一颗星，正在终端深处等待。"

    _daily_label, daily_raw, _daily_weighted = headline_daily_metric(summary)
    level_band = band(level, [4, 16, 64, 256])
    total_band = band(summary.window_tokens, [1_000_000, 100_000_000, 10_000_000_000, 100_000_000_000])
    daily_band = band(daily_raw, [100_000, 10_000_000, 1_000_000_000, 10_000_000_000])
    streak_band = band(summary.current_streak_days, [2, 7, 30, 90])
    intensity = level_band + total_band + daily_band + streak_band

    scale_words = ["星尘", "月相", "日冕", "星河", "万象"]
    cadence_words = ["微光", "细流", "潮声", "长潮", "天河"]
    streak_words = ["初醒", "连灯", "长明", "不息", "恒昼"]
    scale = scale_words[min(4, max(level_band, total_band))]
    cadence = cadence_words[min(4, daily_band)]
    streak = streak_words[min(4, streak_band)]

    if intensity >= 13:
        return f"{creature}循着{streak}的{cadence}越过{scale}之门，仍把回声收束成清澈的路径。"
    if intensity >= 10:
        return f"{creature}踏着{streak}的{cadence}前行，让{scale}深处的脉络安静显形。"
    if intensity >= 7:
        return f"{creature}把{cadence}藏进{streak}的步伐里，在{scale}之间照见下一条路径。"
    if intensity >= 4:
        return f"{creature}沿着{cadence}拾起{scale}，让零散灵感慢慢有了形状。"
    return f"{creature}点亮{scale}边缘的{cadence}，第一段旅程已经悄然展开。"


def date_range_text(summary: UsageSummary) -> str:
    if summary.first_date and summary.last_date:
        return f"{summary.first_date.isoformat()} to {summary.last_date.isoformat()}"
    return "no local data detected"


def prompt_badge_rows(level: int, max_per_row: int = 7) -> List[str]:
    parts = visible_level_parts(level, max_tiers=2)
    badges: List[str] = []
    for label, count in [
        ("wordless faceted aurora relic medal icon", parts["t_medal"]),
        ("crown icon", parts["crown"]),
        ("sun icon", parts["sun"]),
        ("moon icon", parts["moon"]),
        ("star icon", parts["star"]),
    ]:
        badges.extend([label] * count)
    if not badges:
        return ["unawakened subtle spark icon"]
    return [
        " / ".join(badges[index : index + max_per_row])
        for index in range(0, len(badges), max_per_row)
    ]


def top_sources_prompt_text(summary: UsageSummary, limit: int = 3) -> str:
    source_totals = summary.source_window_totals or summary.source_totals
    top_sources = [
        (source, value)
        for source, value in sorted(source_totals.items(), key=lambda item: item[1], reverse=True)
        if value > 0
    ][:limit]
    if not top_sources:
        return "No source breakdown detected."
    return " / ".join(SOURCE_LABELS.get(source, source) for source, _value in top_sources)


def top_named_items(
    totals: Dict[str, int],
    limit: int = 2,
    labels: Optional[Dict[str, str]] = None,
    exclude: Sequence[str] = ("all", "unknown", ""),
) -> List[str]:
    excluded = {item.lower() for item in exclude}
    ranked = [
        (name, value)
        for name, value in sorted(totals.items(), key=lambda item: item[1], reverse=True)
        if value > 0 and str(name).strip().lower() not in excluded
    ][:limit]
    result: List[str] = []
    for name, _value in ranked:
        label = labels.get(name, name) if labels else name
        cleaned = safe_label(label, 32)
        if cleaned:
            result.append(cleaned)
    return result


def top_agents(summary: UsageSummary, limit: int = 2) -> List[str]:
    return top_named_items(summary.source_window_totals or summary.source_totals, limit, SOURCE_LABELS)


def top_models(summary: UsageSummary, limit: int = 2) -> List[str]:
    return top_named_items(summary.model_window_totals or summary.model_totals, limit)


def top_metadata_prompt_text(summary: UsageSummary) -> str:
    lines = top_metadata_lines(summary)
    if not lines:
        return "Top agents/models not detected; keep this metadata strip minimal or omit it."
    return "; ".join(lines)


def top_metadata_lines(summary: UsageSummary) -> List[str]:
    agents = top_agents(summary, 2)
    models = top_models(summary, 2)
    parts = []
    if agents:
        parts.append(f"Top agents: {' / '.join(agents)}")
    if models:
        parts.append(f"Top models: {' / '.join(models)}")
    return parts


def wrap_text(text: str, width: int) -> List[str]:
    lines: List[str] = []
    current = ""
    for char in text:
        current += char
        if len(current) >= width:
            lines.append(current)
            current = ""
    if current:
        lines.append(current)
    return lines


def svg_text(
    x: float,
    y: float,
    text: str,
    size: int,
    weight: int = 400,
    fill: str = "#F8FAFC",
    anchor: str = "start",
    opacity: float = 1.0,
) -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" '
        f'font-family="Inter, PingFang SC, Microsoft YaHei, Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}" opacity="{opacity:.2f}">{esc(text)}</text>'
    )


def file_data_uri(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    file_path = Path(path).expanduser()
    if not file_path.exists() or not file_path.is_file():
        return None
    mime = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    encoded = base64.b64encode(file_path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def external_avatar_svg(image_path: str, size: int, accent: str) -> Optional[str]:
    uri = file_data_uri(image_path)
    if uri is None:
        return None
    clip_id = f"avatarClip{stable_seed(image_path, size) % 1_000_000}"
    radius = size * 0.14
    return "\n".join(
        [
            f'<defs><clipPath id="{clip_id}"><rect width="{size}" height="{size}" rx="{radius:.0f}"/></clipPath></defs>',
            f'<image href="{uri}" x="0" y="0" width="{size}" height="{size}" preserveAspectRatio="xMidYMid slice" clip-path="url(#{clip_id})"/>',
            f'<rect x="10" y="10" width="{size - 20}" height="{size - 20}" rx="{size * 0.12:.0f}" fill="none" stroke="{accent}" stroke-width="4" opacity="0.62"/>',
        ]
    )


def avatar_svg(
    nickname: str,
    summary: UsageSummary,
    level_result: LevelResult,
    size: int = 512,
    standalone: bool = True,
    avatar_image: Optional[str] = None,
) -> str:
    source = dominant_source(summary)
    creature = pick_creature(nickname, level_result.level, source, summary.weighted_tokens)
    seed = stable_seed(nickname, creature, level_result.level, summary.weighted_tokens)
    rng = random.Random(seed)
    primary, secondary, accent, bg, fg = palette_for(source, seed)
    external = external_avatar_svg(avatar_image, size, accent) if avatar_image else None
    if external:
        if standalone:
            return f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">\n{external}\n</svg>\n'
        return external
    grid = 24
    cell = size / grid
    pixels: Dict[Tuple[int, int], str] = {}

    def put(x: int, y: int, color: str) -> None:
        if 0 <= x < grid and 0 <= y < grid:
            pixels[(x, y)] = color

    def mirror(x: int, y: int, color: str) -> None:
        put(x, y, color)
        put(grid - 1 - x, y, color)

    for y in range(grid):
        for x in range(grid):
            cx = x + 0.5
            cy = y + 0.5
            body = ((cx - 12) / 6.2) ** 2 + ((cy - 14.4) / 5.8) ** 2 <= 1
            head = ((cx - 12) / 5.2) ** 2 + ((cy - 9.6) / 4.6) ** 2 <= 1
            if body or head:
                color = primary if (x * 3 + y + seed) % 6 else secondary
                put(x, y, color)

    for point in [(6, 7), (6, 6), (7, 5), (7, 6), (8, 7), (5, 8)]:
        mirror(point[0], point[1], secondary)
    if level_result.level >= 16:
        for point in [(8, 5), (9, 4), (10, 5), (14, 5), (15, 4), (16, 5)]:
            put(point[0], point[1], accent)

    if source in ("codex", "mixed") or level_result.level >= 64:
        for point in [(5, 13), (4, 14), (4, 15), (5, 16), (6, 17), (7, 17)]:
            mirror(point[0], point[1], secondary)
            if rng.random() > 0.45:
                mirror(point[0], min(grid - 1, point[1] + 1), accent)
    else:
        for point in [(4, 12), (3, 13), (3, 14), (4, 15), (5, 16)]:
            mirror(point[0], point[1], secondary)

    mirror(9, 10, "#020617")
    mirror(9, 9, fg)
    put(12, 12, "#020617")
    mirror(11, 13, accent)
    put(12, 14, accent)

    sparkle_count = 22 + min(46, max(0, level_result.level // 2))
    for _ in range(sparkle_count):
        x = rng.randrange(grid)
        y = rng.randrange(grid)
        if (x, y) not in pixels and rng.random() > 0.3:
            put(x, y, rng.choice([accent, secondary, fg]))

    rects = [
        f'<rect width="{size}" height="{size}" rx="{size * 0.14:.0f}" fill="{bg}"/>',
        f'<circle cx="{size * 0.50:.1f}" cy="{size * 0.50:.1f}" r="{size * 0.39:.1f}" fill="{secondary}" opacity="0.13"/>',
        f'<circle cx="{size * 0.50:.1f}" cy="{size * 0.50:.1f}" r="{size * 0.29:.1f}" fill="{primary}" opacity="0.12"/>',
    ]
    for (x, y), color in sorted(pixels.items()):
        pad = max(1.0, cell * 0.08)
        rects.append(
            f'<rect x="{x * cell + pad:.2f}" y="{y * cell + pad:.2f}" '
            f'width="{cell - 2 * pad:.2f}" height="{cell - 2 * pad:.2f}" '
            f'rx="{cell * 0.08:.2f}" fill="{color}"/>'
        )
    rects.append(f'<rect x="10" y="10" width="{size - 20}" height="{size - 20}" rx="{size * 0.12:.0f}" fill="none" stroke="{accent}" stroke-width="4" opacity="0.55"/>')

    body = "\n".join(rects)
    if standalone:
        return f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">\n{body}\n</svg>\n'
    return body


def level_badges_svg(x: int, y: int, level: int, accent: str, fg: str) -> str:
    badge_parts = visible_level_parts(level, max_tiers=2)
    parts = []
    specs = [
        ("◆", badge_parts["t_medal"], "#FDE68A"),
        ("♛", badge_parts["crown"], accent),
        ("☀", badge_parts["sun"], "#FACC15"),
        ("◐", badge_parts["moon"], "#93C5FD"),
        ("★", badge_parts["star"], "#E5E7EB"),
    ]
    badge_w = 46
    badge_h = 46
    gap = 8
    line_gap = 8
    max_x = 940
    cursor = x
    row_y = y
    for label, count, color in specs:
        if count <= 0:
            continue
        for _ in range(count):
            if cursor + badge_w > max_x:
                cursor = x
                row_y += badge_h + line_gap
            parts.append(f'<rect x="{cursor}" y="{row_y}" width="{badge_w}" height="{badge_h}" rx="16" fill="{color}" opacity="0.18"/>')
            parts.append(svg_text(cursor + badge_w / 2, row_y + 32, label, 26, 800, fg, anchor="middle"))
            cursor += badge_w + gap
    if not parts:
        parts.append(svg_text(x, y + 36, "未觉醒", 26, 700, "#CBD5E1"))
    return "\n".join(parts)


def render_card_svg(
    nickname: str,
    summary: UsageSummary,
    level_result: LevelResult,
    avatar_image: Optional[str] = None,
    background_image: Optional[str] = None,
) -> str:
    width, height = 1080, 1350
    source = dominant_source(summary)
    creature = pick_creature(nickname, level_result.level, source, summary.weighted_tokens)
    seed = stable_seed(nickname, creature, level_result.level, summary.weighted_tokens)
    rng = random.Random(seed)
    primary, secondary, accent, bg, fg = palette_for(source, seed)
    avatar = avatar_svg(nickname, summary, level_result, size=380, standalone=False, avatar_image=avatar_image)
    background_uri = file_data_uri(background_image)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<defs>",
        f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{bg}"/><stop offset="0.52" stop-color="#111827"/><stop offset="1" stop-color="#020617"/></linearGradient>',
        f'<linearGradient id="edge" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{secondary}"/><stop offset="1" stop-color="{primary}"/></linearGradient>',
        '<filter id="shadow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="18" stdDeviation="24" flood-color="#000000" flood-opacity="0.38"/></filter>',
        "</defs>",
        '<rect width="1080" height="1350" fill="url(#bg)"/>',
    ]
    if background_uri:
        parts.append(f'<image href="{background_uri}" x="0" y="0" width="{width}" height="{height}" preserveAspectRatio="xMidYMid slice" opacity="0.40"/>')
        parts.append('<rect width="1080" height="1350" fill="#020617" opacity="0.42"/>')

    for _ in range(110):
        x = rng.randint(28, width - 28)
        y = rng.randint(28, height - 28)
        radius = rng.choice([2, 2, 3, 4])
        color = rng.choice([primary, secondary, accent, "#FFFFFF"])
        opacity = rng.uniform(0.08, 0.30)
        parts.append(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{color}" opacity="{opacity:.2f}"/>')

    parts.extend(
        [
            '<g filter="url(#shadow)">',
            '<rect x="70" y="74" width="940" height="1202" rx="48" fill="#0B1020" opacity="0.91"/>',
            '<rect x="70" y="74" width="940" height="1202" rx="48" fill="none" stroke="url(#edge)" stroke-width="4" opacity="0.90"/>',
            "</g>",
            svg_text(120, 160, "Token Rank", 36, 800, accent, opacity=0.95),
            svg_text(120, 242, nickname[:18], 62, 850, fg),
            f'<rect x="350" y="315" width="380" height="380" rx="64" fill="{secondary}" opacity="0.10"/>',
            f'<g transform="translate(350 315)">{avatar}</g>',
            f'<rect x="120" y="742" width="840" height="182" rx="32" fill="{primary}" opacity="0.14"/>',
            svg_text(160, 813, f"Lv.{level_result.level}", 62, 900, fg),
            svg_text(160, 869, rank_title(level_result.level), 30, 750, accent),
            level_badges_svg(574, 790, level_result.level, accent, fg),
        ]
    )

    for line_index, line in enumerate(wrap_text(elegant_metric_copy(level_result.level, creature, summary), 28)[:2]):
        parts.append(svg_text(540, 970 + line_index * 36, line, 28, 520, "#E2E8F0", anchor="middle", opacity=0.96))

    total_label, total_value = headline_total_metric(summary)
    daily_label, daily_value, _daily_weighted = headline_daily_metric(summary)
    stats = [
        (total_label, human_tokens(total_value)),
        (daily_label, human_tokens(daily_value)),
        ("连续天数", str(summary.current_streak_days)),
    ]
    x0, y0 = 120, 1044
    box_w, box_h, gap = 268, 92, 18
    for index, (label, value) in enumerate(stats):
        x = x0 + index * (box_w + gap)
        y = y0
        parts.append(f'<rect x="{x}" y="{y}" width="{box_w}" height="{box_h}" rx="24" fill="#FFFFFF" opacity="0.065"/>')
        parts.append(svg_text(x + 30, y + 32, label, 21, 500, "#CBD5E1", opacity=0.94))
        parts.append(svg_text(x + 30, y + 69, value, 32, 850, fg))

    for line_index, line in enumerate(top_metadata_lines(summary)[:2]):
        parts.append(svg_text(540, 1194 + line_index * 24, line, 16, 520, "#CBD5E1", anchor="middle", opacity=0.72))

    parts.append(svg_text(540, 1310, "本地只读生成 · Token 等级仅供娱乐展示", 20, 430, "#94A3B8", anchor="middle", opacity=0.78))
    parts.append("</svg>\n")
    return "\n".join(parts)


def image_generation_prompts(
    nickname: str,
    summary: UsageSummary,
    level_result: LevelResult,
    visual_style: str = DEFAULT_VISUAL_STYLE,
    platform: str = "generic",
    display_unit: str = "compact",
    public_safe: bool = False,
    variation_seed: str = "",
) -> Dict[str, str]:
    source = dominant_source(summary)
    creature = pick_creature(nickname, level_result.level, source, summary.weighted_tokens, visual_style, variation_seed)
    seed = stable_seed(nickname, creature, level_result.level, summary.weighted_tokens, variation_seed)
    primary, secondary, accent, _bg, _fg = palette_for(source, seed)
    source_label = SOURCE_LABELS.get(source, source)
    style = style_profile(visual_style)
    quote = elegant_metric_copy(level_result.level, creature, summary)
    creature_variation = creature_variation_lines(
        nickname,
        level_result.level,
        source,
        summary.weighted_tokens,
        visual_style,
        variation_seed,
    )
    badge_rows = prompt_badge_rows(level_result.level)
    badge_text = "\n".join(f"- badge row {index + 1} icons: {row}" for index, row in enumerate(badge_rows))
    total_label, total_value = headline_total_metric(summary)
    daily_label, daily_value, _daily_weighted = headline_daily_metric(summary)
    stats = {
        "total_label": total_label,
        "window_total": format_tokens(total_value, display_unit, public_safe),
        "daily_label": daily_label,
        "daily": format_tokens(daily_value, display_unit, public_safe),
    }
    canvas_hint = (
        f"{XHS_CANVAS}; keep the main title/subject inside the central 1:1 preview-safe area; "
        "designed for a Xiaohongshu/Rednote carousel post."
        if platform == "xhs"
        else "Vertical portrait share card, 4:5 ratio, designed as a polished shareable rank artifact."
    )
    metadata_chips = top_metadata_prompt_text(summary)

    style_palette = style.get("palette", f"{primary}, {secondary}, {accent}, deep navy/black, off-white highlights")
    style_layout = style.get("layout", style["card"])

    avatar_prompt = f"""Use case: stylized-concept
Asset type: square Token Rank avatar generated entirely by image_gen.
Primary request: create one finished 1:1 style-led fantasy animal avatar. Do not leave blank text areas and do not rely on later SVG/text composition.

Subject: a fictional mythic animal, not a human and not a real person. Base species seed: {creature}, influenced by {source_label}. The character should quietly imply this usage profile: Lv.{level_result.level}, top-tier wordless medal rank, {total_label} {stats["window_total"]}, {daily_label} {stats["daily"]}, current streak {summary.current_streak_days} days.
Creative variation seed: {variation_seed or "stable"}. Use it only to diversify the creature design; do not render this seed as visible text.

Character variation:
{creature_variation}

Style/medium: use the selected visual style as the primary art direction; do not force pixel art unless the selected style asks for it. Keep the avatar readable at small size with a clean silhouette, centered enough to recognize, polished but not overdecorated.
Visual style preset: {style["name"]} / {style["zh"]}.
Style direction: {style["avatar"]}.
Scene/backdrop: match the selected style direction; include only subtle token/rank hints that do not become text.
Color palette: {style_palette}.
Constraints: no text, no numbers, no letters, no real people, no logos, no watermark, no UI frame. Use an original design; do not copy anime, manga, game, or film characters, symbols, emblems, logos, or distinctive franchise layouts. Avoid photorealism, painterly blur, anime human features, cluttered scenery, and unreadable micro-detail."""

    if style.get("template") == "wanted":
        card_prompt = f"""Use case: infographic-diagram
Asset type: one-shot vertical wanted-poster share card generated entirely by image_gen.
Primary request: create the final complete Token Rank wanted poster as one polished bitmap image. The output should read first as a classic printed manga-adventure bounty poster, not as a modern UI dashboard or ornate collectible card.

Canvas and poster layout:
- {canvas_hint}
- Aged tan newsprint parchment with darker worn edges.
- Top band: huge bold black serif word "WANTED", spanning almost the full width.
- Middle: one large rectangular portrait-photo panel with the fictional mythic animal centered, like a printed bounty-photo snapshot.
- Under the portrait: a compact "DEAD OR ALIVE" line, then the large nickname "{nickname}", then a large bounty/value line based on the token rank.
- Bottom area: small official-looking seals/stamps for Lv.{level_result.level}, badge icons, recent daily average, streak days, and local-only note.
- Keep the composition simple and poster-like: one main photo, one big name, one big bounty number. Do not create a luxury card frame, dashboard grid, terminal screenshot, or multi-panel achievement-card UI.
- Use stable safe margins; no symbols cropped at the right edge. If badges are many, wrap them as small stamp icons or seal marks. Do not use multiplication notation such as x2, times signs, or grouped counts.

Exact visible text to include:
- WANTED
- DEAD OR ALIVE
- {nickname}
- TOKEN BOUNTY {stats["window_total"]}
- Lv.{level_result.level}
- {total_label}: {stats["window_total"]}
- {daily_label}: {stats["daily"]}
- 连续天数: {summary.current_streak_days}
- 本地只读生成 · Token 等级仅供娱乐展示

QQ-style badge icons to draw, not text labels. Show only the highest two non-zero badge tiers for clarity; do not draw lower-tier leftovers. Repeat visible icons one-by-one and wrap:
{badge_text}

Low-emphasis metadata chips, names only and no token values:
- {metadata_chips}
- Place these in a visually weak position such as a lower side seal, footer rail, side stamp, or tiny paper-label strip. They must not compete with the nickname, level, bounty, badge row, or three core metrics.

Elegant line to include as a small handwritten-style motto:
「{quote}」

Portrait subject:
- Fictional mythic animal seed: {creature}
- Dominant source influence: {source_label}
- Creative variation seed: {variation_seed or "stable"}. Use it only to diversify the portrait; do not render it as text.
- Make it a lively hand-drawn manga-adventure animal portrait with a clear expression, clean silhouette, and printed halftone texture. It must not be a real person or a human character.
{creature_variation}

Visual style:
- Visual style preset: {style["name"]} / {style["zh"]}.
- Style direction: {style["card"]}.
- Old adventure manga wanted poster mood: flat warm parchment, black ink typography, slightly faded color portrait, rough paper fibers, stamp marks, simple frame lines, small sea-map doodles.
- Palette: {style_palette}.
- Strong recent token total, daily rhythm, level, and streak should quietly appear as a more imposing bounty value, stronger printed seals, richer paper texture, and more confident portrait presence, without explaining the mapping literally.
- Typography should be bold and poster-like. Prioritize large readable WANTED, nickname, TOKEN BOUNTY, Lv, and the three metrics.

Badge design rules:
- The first high-tier medal icon must contain no letters, no words, no visible "T", and no small label underneath.
- The first high-tier medal icon must look clearly above a crown: larger or more luminous than crowns, faceted octagonal/prismatic relic, double halo, star-core, crown-ray accents, ceremonial glow.
- Crowns, moons, and stars may be familiar icons, but the high-tier medal must be a wordless prestige emblem, not a text badge.
- Display only the highest two non-zero badge tiers. Do not add lower-tier sun/moon/star leftovers when a higher two-tier pair is already shown.

Constraints:
- Generate the entire poster in one image; do not create placeholder boxes for later composition.
- Use raw total tokens for visible usage metrics. Do not display weighted tokens, cache-adjusted tokens, or any "more valuable" token count.
- The headline total metric must be {total_label}: {stats["window_total"]}.
- The headline daily metric must be {daily_label}: {stats["daily"]}.
- Do not display historical total, active days, latest streak, longest streak, full exact comma-separated token numbers, date range, rank score, weighted tokens, or source token values.
- No real people, no brand logos, no screenshots, no watermarks, no QR code.
- Use an original design. Do not copy or imitate any existing anime, manga, game, or film franchise. No existing characters, no straw-hat character, no named pirate crew, no skull-and-crossbones emblem, no Marine word or crest, no franchise flags, no named treasure symbols, no copied ship designs, and no exact proprietary bounty-poster template.
- Do not invent extra metrics or extra badge tiers that conflict with the values above.
- Avoid ornate fantasy card styling. This should look like a simple printed wanted poster from a fictional seafaring adventure world."""
        return {"avatar": avatar_prompt, "card": card_prompt}

    card_prompt = f"""Use case: infographic-diagram
Asset type: one-shot share card generated entirely by image_gen.
Primary request: create the final complete Token Rank as one polished bitmap image. Include the animal avatar, refined card layout, wordless rank badges, three core metrics, nickname, elegant line, and footer inside the generated image itself. No later SVG or typography pass will be used. Minor small-text imperfections are acceptable, but keep the nickname, level, recent total token, recent daily average, and streak large and clear.

Canvas and layout:
- {canvas_hint}
- It must not feel like a dense dashboard.
- The selected visual style is the primary design language. Do not default to dark fantasy, ornate trading-card borders, neon sci-fi, or centered creature card composition unless this specific style asks for it.
- Style layout direction: {style_layout}.
- Composition should still include: small title, nickname, animal/avatar treatment, large Lv.{level_result.level}, wordless badge area, three core metrics, one elegant line, minimal footer.
- Avoid table-like grids, stacked mini-stat rows, terminal screenshots, dense source panels, excessive borders, and decorative clutter.
- Use stable safe margins; no symbols cropped at the right edge. If badges are many, wrap them gracefully to multiple centered rows. Do not use multiplication notation such as x2 or ×2.

Identity and rank data to show:
- Title: Token Rank
- Do not add or render any second subtitle line under the title.
- Nickname: {nickname}
- Rank: Lv.{level_result.level}
- Rank title: {rank_title(level_result.level)}
- QQ-style badge icons to draw, not text labels. Show only the highest two non-zero badge tiers for clarity; do not draw lower-tier leftovers. Repeat visible icons one-by-one and wrap:
{badge_text}

Metrics to show prominently:
- {total_label}: {stats["window_total"]}
- {daily_label}: {stats["daily"]}
- 连续天数: {summary.current_streak_days}

Low-emphasis metadata chips, names only and no token values:
- {metadata_chips}
- Place these in a visually weak position such as a bottom metadata rail, lower corner, side caption, or faint label strip. They must not compete with the nickname, level, animal portrait, badge row, or three core metrics.

Elegant line to include:
「{quote}」

Animal avatar direction:
- Fictional mythic animal seed: {creature}
- Dominant source influence: {source_label}
- Creative variation seed: {variation_seed or "stable"}. Use it only to diversify the animal/avatar treatment; do not render it as text.
- Style-led fantasy creature, arcane, calm, intelligent, companion-like; no human face and no real person.
{creature_variation}

Visual style:
- Visual style preset: {style["name"]} / {style["zh"]}.
- Style direction: {style["card"]}.
- Palette: {style_palette}.
- Make the card feel high-rank in a way native to the selected style. The stronger recent token total, recent daily rhythm, level, and streak should be reflected through more confident composition, stronger presence, richer material detail, or more deliberate whitespace, without explaining that relationship literally.
- Typography should feel premium and spacious: large display text, short labels, no crowded paragraphs, no tiny exact-number footnotes.

Badge design rules:
- The first high-tier medal icon must contain no letters, no words, no visible "T", and no small label underneath.
- The first high-tier medal icon must look clearly above a crown: larger or more luminous than crowns, faceted octagonal/prismatic relic, double halo, star-core, crown-ray accents, ceremonial glow.
- Crowns, moons, and stars may be familiar icons, but the high-tier medal must be a wordless prestige emblem, not a text badge.
- Display only the highest two non-zero badge tiers. Do not add lower-tier sun/moon/star leftovers when a higher two-tier pair is already shown.

Footer text:
- 本地只读生成 · Token 等级仅供娱乐展示

Constraints:
- Generate the entire card in one image; do not create placeholder boxes for later composition.
- Use raw total tokens for visible usage metrics. Do not display weighted tokens, cache-adjusted tokens, or any "more valuable" token count.
- The headline total metric must be {total_label}: {stats["window_total"]}.
- The headline daily metric must be {daily_label}: {stats["daily"]}.
- Do not display historical total, active days, latest streak, longest streak, full exact comma-separated token numbers, date range, rank score, weighted tokens, or source token values.
- No real people, no brand logos, no screenshots, no watermarks, no QR code.
- Use an original design. Do not copy anime, manga, game, film, sports-league, fashion-brand, magazine, trading-card, membership-card, or social-template IP; no logos, skull marks, team marks, brand marks, flags, named symbols, or distinctive proprietary layouts.
- Do not invent extra metrics or extra badge tiers that conflict with the values above.
- Avoid tiny unreadable tables; prioritize three large metric values, a visually striking wrapped badge area, and a calmer high-end layout."""
    return {"avatar": avatar_prompt, "card": card_prompt}


def selected_image_prompt(
    nickname: str,
    summary: UsageSummary,
    level_result: LevelResult,
    mode: str,
    visual_style: str = DEFAULT_VISUAL_STYLE,
    platform: str = "generic",
    display_unit: str = "compact",
    public_safe: bool = False,
    variation_seed: str = "",
) -> str:
    prompts = image_generation_prompts(
        nickname,
        summary,
        level_result,
        visual_style,
        platform,
        display_unit,
        public_safe,
        variation_seed,
    )
    return prompts["avatar" if mode == "avatar" else "card"]


def xhs_style_notes(style: Dict[str, str]) -> str:
    return (
        f"Use visual style {style['name']} / {style['zh']}: {style['summary']}. "
        "Stay original and open-source-safe; do not copy any brand, anime, manga, game, platform template, "
        "social UI, magazine, card game, team mark, logo, flag, skull mark, or proprietary layout."
    )


def xhs_main_hook(level_result: LevelResult, total_value: str) -> str:
    if level_result.level >= 256:
        return f"我的 AI 编程等级到 Lv.{level_result.level}"
    if level_result.level >= 64:
        return "AI 编程也有段位了"
    if total_value:
        return f"近30天用了{total_value}Token"
    return "生成你的 Token 等级卡"


def xhs_share_pack_prompts(
    nickname: str,
    summary: UsageSummary,
    level_result: LevelResult,
    visual_style: str,
    display_unit: str,
    public_safe: bool,
    variation_seed: str,
) -> List[Dict[str, str]]:
    style = style_profile(visual_style)
    source = dominant_source(summary)
    creature = pick_creature(nickname, level_result.level, source, summary.weighted_tokens, visual_style, variation_seed)
    source_label = SOURCE_LABELS.get(source, source)
    creature_variation = creature_variation_lines(
        nickname,
        level_result.level,
        source,
        summary.weighted_tokens,
        visual_style,
        variation_seed,
    )
    quote = elegant_metric_copy(level_result.level, creature, summary)
    total_label, total_value_raw = headline_total_metric(summary)
    daily_label, daily_value_raw, _daily_weighted = headline_daily_metric(summary)
    total_value = format_tokens(total_value_raw, display_unit, public_safe)
    daily_value = format_tokens(daily_value_raw, display_unit, public_safe)
    hook = xhs_main_hook(level_result, total_value)
    style_notes = xhs_style_notes(style)
    badge_rows = "\n".join(f"- {row}" for row in prompt_badge_rows(level_result.level, max_per_row=6))
    metadata_line = top_metadata_prompt_text(summary)

    common = f"""Common constraints for every page:
- Canvas: {XHS_CANVAS}.
- Keep the most important text and subject inside the central square preview-safe area, because feeds may crop previews.
- One page, one message. Use large Chinese type, short lines, clear hierarchy, and generous safe margins.
- Use only the exact metrics provided here; do not invent extra numbers.
- Use raw visible-window tokens, not weighted/cache-adjusted tokens.
- No QR code, no watermark, no screenshots, no real people, no brand logos.
- The high-tier medal is a wordless prestige emblem: no letter T, no Chinese/English text, no label underneath; it must look above crowns through scale, halo, facets, or ceremonial light.
- {style_notes}
"""

    prompts = [
        {
            "slug": "01-cover",
            "title": "小红书封面",
            "prompt": f"""Use case: ads-marketing
Asset type: Xiaohongshu/Rednote carousel cover image.
Primary request: create a high-click but elegant cover for a Token Rank post.
{common}

Large cover text:
「{hook}」

Secondary text:
「{nickname} · {rank_title(level_result.level)}」
「{total_label} {total_value}」

Visual: a fictional mythic animal avatar ({creature}, influenced by {source_label}) as the anchor. Make it instantly readable in feed preview, and let its silhouette vary strongly instead of repeating a standard dragon/qilin/fox mascot. Creative variation seed: {variation_seed}; use it only to diversify the character and do not render it as text.
Creature variation:
{creature_variation}
The cover should feel intriguing and shareable, not noisy.
Layout: large hook at top or center, creature as strong visual anchor, one compact stat ribbon, tiny footer "本地只读 · 娱乐等级".
Weak-position metadata: add tiny low-emphasis chips in a lower corner or footer strip, names only and no token values: {metadata_line}
Avoid: dense data panels, long paragraphs, tiny labels, fake UI, platform chrome, clickbait symbols, real app screenshots.""",
        },
        {
            "slug": "02-rank-card",
            "title": "等级卡正文页",
            "prompt": selected_image_prompt(
                nickname,
                summary,
                level_result,
                "card",
                visual_style,
                "xhs",
                display_unit,
                public_safe,
                variation_seed,
            ),
        },
        {
            "slug": "03-badge-guide",
            "title": "等级符号说明页",
            "prompt": f"""Use case: infographic-diagram
Asset type: Xiaohongshu/Rednote carousel explainer page.
Primary request: explain the Token Rank badge ladder in a clean, collectible visual.
{common}

Main title:
「等级怎么换算」

Required ladder text, keep readable:
- 1 星星 = 1级
- 1 月亮 = 4星星
- 1 太阳 = 4月亮
- 1 皇冠 = 4太阳
- 1 神徽 = 4皇冠

Current visible badge row for {nickname}, repeated one-by-one and wrapped, no multiplication notation. Show only the highest two non-zero tiers:
{badge_rows}

Tiny metadata strip, names only and no token values:
{metadata_line}

Visual: show a beautiful progression from star to moon to sun to crown to one wordless prismatic prestige medal. The prestige medal must contain no T and no text. Use the selected style, but keep this page calmer and more instructional than the cover.""",
        },
        {
            "slug": "04-how-to",
            "title": "复刻教程页",
            "prompt": f"""Use case: infographic-diagram
Asset type: Xiaohongshu/Rednote carousel how-to page.
Primary request: show how another Codex user can generate their own token rank card.
{common}

Main title:
「你也能生成」

Required steps, keep short and readable:
1. 安装这个 Codex Skill
2. 说：生成卡片，昵称=你的名字
3. 本机只读统计 token
4. 交给 image_gen 一次出图

Small trust note:
「不上传日志 · 不展示会话 · 仅供娱乐」

Visual: simple four-step flow with tiny terminal/card/avatar icons, not a screenshot. Keep enough whitespace for readability on mobile.""",
        },
        {
            "slug": "05-style-picker",
            "title": "风格选择页",
            "prompt": f"""Use case: infographic-diagram
Asset type: Xiaohongshu/Rednote carousel style-picker page.
Primary request: present the 12 available visual styles as a save-worthy picker page.
{common}

Main title:
「12 种风格任选」

Show 12 small original swatches in a neat 3x4 grid. Each swatch should feel visually distinct and use only the numbered names below. Keep labels short and readable:
01 印刷悬赏令
02 哥特黑塔罗
03 Riso 小报
04 植物炼金
05 黑白终端
06 彩窗圣像
07 符石图腾
08 留白 Story
09 杂志封面
10 时装拟人
11 极简通行证
12 跑者号码布

Bottom CTA:
「评论区告诉我你想用哪一款」

Visual: do not reuse screenshots. Draw abstract mini cards/avatars as style swatches. Keep the page bright enough and easy to scan.""",
        },
    ]
    return prompts


def xhs_caption_markdown(
    nickname: str,
    summary: UsageSummary,
    level_result: LevelResult,
    visual_style: str,
    display_unit: str,
    public_safe: bool,
) -> str:
    total_label, total_value_raw = headline_total_metric(summary)
    daily_label, daily_value_raw, _daily_weighted = headline_daily_metric(summary)
    total_value = format_tokens(total_value_raw, display_unit, public_safe)
    daily_value = format_tokens(daily_value_raw, display_unit, public_safe)
    style = style_profile(visual_style)
    titles = [
        f"我让 Codex 算了下我的 AI 编程等级：Lv.{level_result.level}",
        "Vibe Coding 也有等级系统了",
        f"近30天 Token 修行卡：{total_value}",
        "程序员的 AI 使用量，终于有分享卡了",
        "把本机 coding-agent 用量做成了一张等级卡",
    ]
    body = f"""# 小红书发布文案

## 标题备选

{chr(10).join(f'{index + 1}. {title}' for index, title in enumerate(titles))}

## 正文

我做了一个 Codex Skill，可以把本机 coding-agent 的 token 使用记录生成一张「Token Rank」等级卡。

这次用我的本机数据生成了一组 demo：昵称 `{nickname}`，等级 `Lv.{level_result.level}`，{total_label} `{total_value}`，{daily_label} `{daily_value}`，连续天数 `{summary.current_streak_days}`。

它不是账单，也不是能力证明，只是把每天和 AI 一起写代码的痕迹做成一张可以分享的卡。数据默认本机只读，卡片上也只放适合公开展示的简化指标。

这组图用的是 `{style['zh']}` 风格。你更想用哪一款？我后面准备把这个 skill 开源。

## 标签

#Codex #AI编程 #VibeCoding #程序员日常 #AI工具 #小红书封面 #生图Prompt #开源项目 #Token等级卡 #效率工具

## 评论区引导

评论你的昵称和想要的风格编号，我看看哪种风格最适合上线。
"""
    return body


def write_xhs_share_pack(
    output: str,
    nickname: str,
    summary: UsageSummary,
    level_result: LevelResult,
    warnings: List[str],
    visual_style: str,
    display_unit: str,
    public_safe: bool,
    variation_seed: str,
) -> Dict[str, Any]:
    out_dir = Path(output)
    if out_dir.suffix:
        out_dir = out_dir.with_suffix("")
    out_dir.mkdir(parents=True, exist_ok=True)
    prompts = xhs_share_pack_prompts(
        nickname,
        summary,
        level_result,
        visual_style,
        display_unit,
        public_safe,
        variation_seed,
    )
    files: List[Dict[str, str]] = []
    for page in prompts:
        prompt_path = out_dir / f"{page['slug']}.image-prompt.txt"
        prompt_path.write_text(page["prompt"], encoding="utf-8")
        files.append({"slug": page["slug"], "title": page["title"], "prompt": str(prompt_path)})

    caption_path = out_dir / "xhs-caption.zh-CN.md"
    caption_path.write_text(
        xhs_caption_markdown(nickname, summary, level_result, visual_style, display_unit, public_safe),
        encoding="utf-8",
    )
    summary_path = out_dir / "summary.json"
    write_summary_json(
        summary_path,
        nickname,
        summary,
        level_result,
        warnings,
        visual_style,
        platform="xhs",
        display_unit=display_unit,
        public_safe=public_safe,
        variation_seed=variation_seed,
    )
    manifest = {
        "type": "xhs-share-pack",
        "platform": "xhs",
        "canvas": XHS_CANVAS,
        "nickname": nickname,
        "visualStyle": visual_style,
        "visualStyleName": style_profile(visual_style)["name"],
        "displayUnit": display_unit,
        "publicSafe": public_safe,
        "variationSeed": variation_seed,
        "level": level_result.level,
        "rankTitle": rank_title(level_result.level),
        "symbols": level_symbols(level_result.level),
        "fullSymbols": full_level_symbols(level_result.level),
        "headlineTotal": {
            "label": headline_total_metric(summary)[0],
            "value": format_tokens(headline_total_metric(summary)[1], display_unit, public_safe),
        },
        "headlineDaily": {
            "label": headline_daily_metric(summary)[0],
            "value": format_tokens(headline_daily_metric(summary)[1], display_unit, public_safe),
        },
        "currentStreakDays": summary.current_streak_days,
        "topAgents": top_agents(summary, 2),
        "topModels": top_models(summary, 2),
        "files": files + [
            {"slug": "caption", "title": "小红书发布文案", "prompt": str(caption_path)},
            {"slug": "summary", "title": "统计摘要", "prompt": str(summary_path)},
        ],
        "warnings": warnings,
    }
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "xhsSharePack": str(out_dir),
        "manifest": str(manifest_path),
        "caption": str(caption_path),
        "summaryJson": str(summary_path),
        "prompts": files,
    }


def maybe_convert_png(svg_path: Path, png_path: Path) -> Optional[str]:
    if shutil.which("rsvg-convert"):
        proc = subprocess.run(
            ["rsvg-convert", "-o", str(png_path), str(svg_path)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return None if proc.returncode == 0 else proc.stderr.strip()
    if shutil.which("magick"):
        proc = subprocess.run(
            ["magick", str(svg_path), str(png_path)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return None if proc.returncode == 0 else proc.stderr.strip()
    if shutil.which("sips"):
        proc = subprocess.run(
            ["sips", "-s", "format", "png", str(svg_path), "--out", str(png_path)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return None if proc.returncode == 0 else proc.stderr.strip()
    try:
        import cairosvg  # type: ignore

        cairosvg.svg2png(url=str(svg_path), write_to=str(png_path))
        return None
    except Exception as ex:  # noqa: BLE001
        return f"未转换 PNG：缺少 rsvg-convert/ImageMagick/sips/cairosvg，或转换失败：{ex}"


def write_summary_json(
    path: Path,
    nickname: str,
    summary: UsageSummary,
    level_result: LevelResult,
    warnings: List[str],
    visual_style: str = DEFAULT_VISUAL_STYLE,
    platform: str = "generic",
    display_unit: str = "compact",
    public_safe: bool = False,
    variation_seed: str = "",
) -> None:
    total_label, total_value = headline_total_metric(summary)
    daily_label, daily_value, daily_weighted = headline_daily_metric(summary)
    style = style_profile(visual_style)
    payload = {
        "nickname": nickname,
        "visualStyle": visual_style,
        "visualStyleName": style["name"],
        "visualStyleZh": style["zh"],
        "visualStyleSummary": style["summary"],
        "platform": platform,
        "displayUnit": display_unit,
        "publicSafe": public_safe,
        "variationSeed": variation_seed,
        "level": level_result.level,
        "rankTitle": rank_title(level_result.level),
        "symbols": level_symbols(level_result.level),
        "fullSymbols": full_level_symbols(level_result.level),
        "levelProfile": level_result.profile,
        "rankScore": level_result.level_float,
        "totalLevelComponent": level_result.total_level,
        "dailyLevelComponent": level_result.daily_level,
        "linearScoreTokens": level_result.linear_score_tokens,
        "totalBenchmarkTokens": level_result.total_benchmark,
        "dailyBenchmarkTokens": level_result.daily_benchmark,
        "advancedLevel": level_result.advanced_level,
        "totalTokens": summary.total_tokens,
        "weightedTokens": summary.weighted_tokens,
        "headlineTotalLabel": total_label,
        "headlineTotalTokens": total_value,
        "headlineDailyLabel": daily_label,
        "headlineDailyTokens": daily_value,
        "headlineDailyWeightedTokens": daily_weighted,
        "avgCalendarTokens": summary.avg_calendar_tokens,
        "avgCalendarWeightedTokens": summary.avg_calendar_weighted_tokens,
        "avgActiveTokens": summary.avg_active_tokens,
        "avgActiveWeightedTokens": summary.avg_active_weighted_tokens,
        "currentStreakTokens": summary.current_streak_tokens,
        "currentStreakWeightedTokens": summary.current_streak_weighted_tokens,
        "avgCurrentStreakTokens": summary.avg_current_streak_tokens,
        "avgCurrentStreakWeightedTokens": summary.avg_current_streak_weighted_tokens,
        "windowTokens": summary.window_tokens,
        "windowWeightedTokens": summary.window_weighted_tokens,
        "effectiveWindowDays": summary.effective_window_days,
        "avgWindowTokens": summary.avg_window_tokens,
        "avgWindowWeightedTokens": summary.avg_window_weighted_tokens,
        "windowTokensExcludingToday": summary.window_tokens_excluding_today,
        "windowWeightedTokensExcludingToday": summary.window_weighted_tokens_excluding_today,
        "effectiveWindowDaysExcludingToday": summary.effective_window_days_excluding_today,
        "avgWindowTokensIncludingToday": summary.avg_window_tokens_including_today,
        "avgWindowWeightedTokensIncludingToday": summary.avg_window_weighted_tokens_including_today,
        "avgWindowTokensExcludingToday": summary.avg_window_tokens_excluding_today,
        "avgWindowWeightedTokensExcludingToday": summary.avg_window_weighted_tokens_excluding_today,
        "windowDays": summary.window_days,
        "activeDays": summary.active_days,
        "currentStreakDays": summary.current_streak_days,
        "latestActiveStreakDays": summary.latest_active_streak_days,
        "longestStreakDays": summary.longest_streak_days,
        "firstDate": summary.first_date.isoformat() if summary.first_date else None,
        "lastDate": summary.last_date.isoformat() if summary.last_date else None,
        "sourceTotals": summary.source_totals,
        "sourceWeightedTotals": summary.source_weighted_totals,
        "sourceWindowTotals": summary.source_window_totals,
        "sourceWindowWeightedTotals": summary.source_window_weighted_totals,
        "modelTotals": summary.model_totals,
        "modelWeightedTotals": summary.model_weighted_totals,
        "modelWindowTotals": summary.model_window_totals,
        "modelWindowWeightedTotals": summary.model_window_weighted_totals,
        "topAgents": top_agents(summary, 2),
        "topModels": top_models(summary, 2),
        "dominantSource": dominant_source(summary),
        "privacyNote": "本地只读生成 · Token 等级仅供娱乐展示",
        "warnings": warnings,
        "imageGenerationPrompts": image_generation_prompts(
            nickname,
            summary,
            level_result,
            visual_style,
            platform,
            display_unit,
            public_safe,
            variation_seed,
        ),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def output_paths(output: str) -> Tuple[Path, Path]:
    requested = Path(output)
    if requested.suffix.lower() == ".png":
        svg_path = requested.with_suffix(".svg")
    elif requested.suffix.lower() == ".svg":
        svg_path = requested
    elif requested.suffix:
        svg_path = requested.with_suffix(requested.suffix + ".svg")
    else:
        svg_path = requested.with_suffix(".svg")
    return svg_path, svg_path.with_suffix(".summary.json")


def image_prompt_path(output: str) -> Path:
    svg_path, _summary_path = output_paths(output)
    return svg_path.with_suffix(".image-prompt.txt")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a Token Rank avatar/card from local token usage.")
    parser.add_argument(
        "--mode",
        choices=["avatar", "card", "xhs-pack"],
        required=True,
        help="avatar=头像；card=完整等级卡；xhs-pack=小红书轮播分享包 prompt",
    )
    parser.add_argument("--nickname", default=os.environ.get("USER") or os.environ.get("USERNAME") or "Vibe Coder")
    parser.add_argument("--output", default="token-rank", help="Output path. Extension is optional.")
    parser.add_argument("--avg-days", type=int, default=DEFAULT_AVG_DAYS, help="Daily average window, default 30.")
    parser.add_argument("--since", help="Start date passed to ccusage, e.g. 2026-06-01.")
    parser.add_argument("--until", help="End date passed to ccusage, e.g. 2026-06-26.")
    parser.add_argument("--sources", default="auto", help="Comma-separated ccusage sources, or auto.")
    parser.add_argument("--skip-source-breakdown", action="store_true", help="Skip source-focused ccusage commands.")
    parser.add_argument("--extra-command", action="append", default=[], help="Read-only adapter: source:command")
    parser.add_argument("--allow-download-runner", action="store_true", help="Allow bunx/npx/pnpm to run ccusage if absent.")
    parser.add_argument("--no-ccusage", action="store_true", help="Only use --extra-command data.")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--png", action="store_true", help="Also export PNG if a local converter is available.")
    parser.add_argument("--emit-image-prompt", action="store_true", help="Write a complete image_gen prompt next to the output.")
    parser.add_argument("--prompt-only", action="store_true", help="Only collect data and write the image_gen prompt/summary; skip SVG fallback rendering.")
    parser.add_argument(
        "--visual-style",
        choices=sorted(STYLE_PROFILES),
        default=DEFAULT_VISUAL_STYLE,
        help="Image prompt style preset.",
    )
    parser.add_argument(
        "--platform",
        choices=["generic", "xhs"],
        default="generic",
        help="Prompt platform. xhs uses 1080x1440 3:4 Rednote/Xiaohongshu constraints.",
    )
    parser.add_argument(
        "--display-unit",
        choices=["auto", "compact", "zh"],
        default="auto",
        help="Visible token unit style. auto uses zh for xhs-pack/--platform xhs, compact otherwise.",
    )
    parser.add_argument("--public-safe", action="store_true", help="Round visible values and omit source details for public sharing.")
    parser.add_argument(
        "--variation-seed",
        help="Creative seed for image_gen creature variation. Default is random each run; use 'stable' or any custom string to reproduce a look.",
    )
    parser.add_argument("--avatar-image", help="SVG fallback only: embed a pre-generated local image as avatar art.")
    parser.add_argument("--background-image", help="SVG fallback only: embed a pre-generated local image as card background art.")
    parser.add_argument("--level-profile", choices=["sqrt", "benchmark", "linear"], default=DEFAULT_LEVEL_PROFILE)
    parser.add_argument("--unit", type=int, default=DEFAULT_LINEAR_UNIT, help="Linear profile tokens per level.")
    parser.add_argument("--total-benchmark", type=int, default=DEFAULT_TOTAL_BENCHMARK)
    parser.add_argument("--daily-benchmark", type=int, default=DEFAULT_DAILY_BENCHMARK)
    parser.add_argument("--advanced-level", type=int, default=DEFAULT_ADVANCED_LEVEL)
    parser.add_argument("--cache-read-weight", type=float, default=DEFAULT_CACHE_READ_WEIGHT)
    return parser


def resolve_window_end(until: Optional[str]) -> dt.date:
    parsed = parse_date(until)
    return parsed or dt.date.today()


def resolve_variation_seed(
    raw: Optional[str],
    nickname: str,
    summary: UsageSummary,
    level_result: LevelResult,
    visual_style: str,
) -> str:
    if raw and raw.strip():
        value = raw.strip()
        if value.lower() == "stable":
            seed = stable_seed("variation-stable-v1", nickname, level_result.level, summary.weighted_tokens, visual_style)
            return f"stable-{seed % 1_000_000:06d}"
        return value
    return secrets.token_hex(4)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    warnings: List[str] = []
    records: List[UsageRecord] = []

    if not args.no_ccusage:
        cc_records, cc_warnings = collect_from_ccusage(args)
        records.extend(cc_records)
        warnings.extend(cc_warnings)

    extra_records, extra_warnings = collect_from_extra_commands(args)
    records.extend(extra_records)
    warnings.extend(extra_warnings)

    summary = summarize(records, max(1, args.avg_days), resolve_window_end(args.until))
    if summary.total_tokens <= 0 and summary.weighted_tokens <= 0:
        warnings.append("没有检测到本机 ccusage-compatible token 数据。")
    if args.avatar_image and file_data_uri(args.avatar_image) is None:
        warnings.append(f"头像图片不可读，已降级为 SVG 像素头像：{args.avatar_image}")
    if args.background_image and file_data_uri(args.background_image) is None:
        warnings.append(f"背景图片不可读，已降级为 SVG 背景：{args.background_image}")

    level_result = compute_level(summary, args)
    display_unit = resolve_display_unit(args.display_unit, args.mode, args.platform)
    variation_seed = resolve_variation_seed(args.variation_seed, args.nickname, summary, level_result, args.visual_style)

    if args.mode == "xhs-pack":
        pack_result = write_xhs_share_pack(
            args.output,
            args.nickname,
            summary,
            level_result,
            warnings,
            args.visual_style,
            display_unit,
            args.public_safe,
            variation_seed,
        )
        total_label, total_value = headline_total_metric(summary)
        daily_label, daily_value, _daily_weighted = headline_daily_metric(summary)
        result = {
            **pack_result,
            "visualStyle": args.visual_style,
            "visualStyleName": style_profile(args.visual_style)["name"],
            "platform": "xhs",
            "displayUnit": display_unit,
            "publicSafe": args.public_safe,
            "variationSeed": variation_seed,
            "level": level_result.level,
            "symbols": level_symbols(level_result.level),
            "fullSymbols": full_level_symbols(level_result.level),
            "rankTitle": rank_title(level_result.level),
            "headlineTotalLabel": total_label,
            "headlineTotalTokens": total_value,
            "headlineTotalDisplay": format_tokens(total_value, display_unit, args.public_safe),
            "headlineDailyLabel": daily_label,
            "headlineDailyTokens": daily_value,
            "headlineDailyDisplay": format_tokens(daily_value, display_unit, args.public_safe),
            "currentStreakDays": summary.current_streak_days,
            "topAgents": top_agents(summary, 2),
            "topModels": top_models(summary, 2),
            "warnings": warnings,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    svg_path, summary_path = output_paths(args.output)
    svg_path.parent.mkdir(parents=True, exist_ok=True)

    prompt_path: Optional[Path] = None
    if args.emit_image_prompt or args.prompt_only:
        prompt_path = image_prompt_path(args.output)
        prompt_path.write_text(
            selected_image_prompt(
                args.nickname,
                summary,
                level_result,
                args.mode,
                args.visual_style,
                args.platform,
                display_unit,
                args.public_safe,
                variation_seed,
            ),
            encoding="utf-8",
        )

    svg_written = False
    if not args.prompt_only:
        if args.mode == "avatar":
            svg = avatar_svg(args.nickname, summary, level_result, size=512, standalone=True, avatar_image=args.avatar_image)
        else:
            svg = render_card_svg(args.nickname, summary, level_result, args.avatar_image, args.background_image)
        svg_path.write_text(svg, encoding="utf-8")
        svg_written = True

    png_path: Optional[Path] = None
    if (args.png or Path(args.output).suffix.lower() == ".png") and svg_written:
        png_path = Path(args.output) if Path(args.output).suffix.lower() == ".png" else svg_path.with_suffix(".png")
        png_warning = maybe_convert_png(svg_path, png_path)
        if png_warning:
            warnings.append(png_warning)
    elif args.png and args.prompt_only:
        warnings.append("--prompt-only 已跳过 SVG 渲染，因此未导出 PNG。")

    write_summary_json(
        summary_path,
        args.nickname,
        summary,
        level_result,
        warnings,
        args.visual_style,
        args.platform,
        display_unit,
        args.public_safe,
        variation_seed,
    )
    total_label, total_value = headline_total_metric(summary)
    daily_label, daily_value, _daily_weighted = headline_daily_metric(summary)
    style = style_profile(args.visual_style)

    result = {
        "svg": str(svg_path) if svg_written else None,
        "png": str(png_path) if png_path and png_path.exists() else None,
        "summaryJson": str(summary_path),
        "imagePrompt": str(prompt_path) if prompt_path else None,
        "visualStyle": args.visual_style,
        "visualStyleName": style["name"],
        "platform": args.platform,
        "displayUnit": display_unit,
        "publicSafe": args.public_safe,
        "variationSeed": variation_seed,
        "level": level_result.level,
        "symbols": level_symbols(level_result.level),
        "fullSymbols": full_level_symbols(level_result.level),
        "rankTitle": rank_title(level_result.level),
        "rankScore": level_result.level_float,
        "totalTokens": summary.total_tokens,
        "headlineTotalLabel": total_label,
        "headlineTotalTokens": total_value,
        "headlineDailyLabel": daily_label,
        "headlineDailyTokens": daily_value,
        "windowTokens": summary.window_tokens,
        "effectiveWindowDays": summary.effective_window_days,
        "avgWindowTokens": summary.avg_window_tokens,
        "windowTokensExcludingToday": summary.window_tokens_excluding_today,
        "effectiveWindowDaysExcludingToday": summary.effective_window_days_excluding_today,
        "avgWindowTokensIncludingToday": summary.avg_window_tokens_including_today,
        "avgWindowTokensExcludingToday": summary.avg_window_tokens_excluding_today,
        "avgActiveTokens": summary.avg_active_tokens,
        "avgCalendarTokens": summary.avg_calendar_tokens,
        "avgCurrentStreakTokens": summary.avg_current_streak_tokens,
        "currentStreakTokens": summary.current_streak_tokens,
        "weightedTokens": summary.weighted_tokens,
        "avgWindowWeightedTokens": summary.avg_window_weighted_tokens,
        "windowWeightedTokensExcludingToday": summary.window_weighted_tokens_excluding_today,
        "avgWindowWeightedTokensIncludingToday": summary.avg_window_weighted_tokens_including_today,
        "avgWindowWeightedTokensExcludingToday": summary.avg_window_weighted_tokens_excluding_today,
        "activeDays": summary.active_days,
        "currentStreakDays": summary.current_streak_days,
        "latestActiveStreakDays": summary.latest_active_streak_days,
        "longestStreakDays": summary.longest_streak_days,
        "sourceTotals": summary.source_totals,
        "sourceWindowTotals": summary.source_window_totals,
        "modelTotals": summary.model_totals,
        "modelWindowTotals": summary.model_window_totals,
        "topAgents": top_agents(summary, 2),
        "topModels": top_models(summary, 2),
        "warnings": warnings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
