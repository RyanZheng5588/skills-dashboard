#!/usr/bin/env python3
"""Build and optionally serve a local dashboard for installed Codex skills."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import socket
import subprocess
import sys
import time
import webbrowser
from dataclasses import dataclass
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote


SKILL_DIR = Path(__file__).resolve().parents[1]
ASSETS_DIR = SKILL_DIR / "assets"
DEFAULT_OUT = SKILL_DIR / ".dashboard"
DEFAULT_REPO_URL = "https://github.com/RyanZheng5588/skills-dashboard.git"
GIT_INFO_CACHE: dict[str, dict[str, object]] = {}


CATEGORY_RULES: dict[str, list[str]] = {
    "文案": [
        "copy",
        "copywriting",
        "writing",
        "writer",
        "article",
        "draft",
        "prose",
        "title",
        "translate",
        "humanizer",
        "story",
        "script",
        "blog",
        "newsletter",
        "wechat",
        "xhs",
        "social",
        "content",
        "文案",
        "写作",
        "文章",
        "标题",
        "翻译",
        "小红书",
        "公众号",
    ],
    "图片": [
        "image",
        "img",
        "photo",
        "picture",
        "poster",
        "cover",
        "wallpaper",
        "visual",
        "illustration",
        "infographic",
        "art",
        "comic",
        "doodle",
        "screenshot",
        "raster",
        "图",
        "图片",
        "插画",
        "海报",
        "封面",
    ],
    "视频": [
        "video",
        "film",
        "filmmaking",
        "storyboard",
        "remotion",
        "hyperframes",
        "youtube",
        "transcript",
        "reel",
        "shorts",
        "movie",
        "视频",
        "短片",
        "分镜",
    ],
    "PPT": [
        "ppt",
        "slide",
        "slides",
        "powerpoint",
        "presentation",
        "deck",
        "keynote",
        "课件",
        "幻灯片",
    ],
    "排版": [
        "layout",
        "format",
        "markdown",
        "richtext",
        "html",
        "print",
        "typography",
        "wechat",
        "article-layout",
        "排版",
        "格式",
        "打印",
    ],
    "数据": [
        "data",
        "analytics",
        "dashboard",
        "chart",
        "spreadsheet",
        "sheets",
        "report",
        "kpi",
        "metric",
        "analysis",
        "market",
        "quality",
        "数据",
        "报表",
        "仪表盘",
    ],
    "代码": [
        "code",
        "coding",
        "repo",
        "git",
        "github",
        "branch",
        "debug",
        "test",
        "refactor",
        "codex",
        "api",
        "plugin",
        "codebase",
        "代码",
        "开发",
    ],
    "知识库": [
        "kb",
        "wiki",
        "knowledge",
        "obsidian",
        "note",
        "memory",
        "search",
        "docs",
        "ingest",
        "query",
        "知识库",
        "笔记",
        "检索",
    ],
    "自动化": [
        "automation",
        "workflow",
        "cron",
        "sync",
        "publish",
        "post",
        "archive",
        "agent",
        "ops",
        "batch",
        "自动化",
        "发布",
        "同步",
    ],
    "设计": [
        "design",
        "ui",
        "ux",
        "figma",
        "frontend",
        "web",
        "polish",
        "product-design",
        "设计",
        "界面",
        "前端",
    ],
    "文档": [
        "document",
        "documents",
        "docx",
        "pdf",
        "contract",
        "template",
        "manual",
        "paper",
        "文档",
        "合同",
        "模板",
    ],
    "音频": [
        "audio",
        "speech",
        "tts",
        "voice",
        "podcast",
        "music",
        "transcript",
        "音频",
        "语音",
        "播客",
        "音乐",
    ],
    "研究": [
        "research",
        "audit",
        "review",
        "investigate",
        "explore",
        "analysis",
        "validate",
        "triage",
        "研究",
        "调研",
        "审计",
        "评审",
    ],
}

CATEGORY_ORDER = [
    "文案",
    "图片",
    "视频",
    "PPT",
    "排版",
    "数据",
    "代码",
    "知识库",
    "自动化",
    "设计",
    "文档",
    "音频",
    "研究",
    "其他",
]

PLATFORM_ORDER = ["System", "Codex", "Claude", "Hermes", "Other"]

PLATFORM_LABELS = {
    "System": {"zh": "系统", "en": "System"},
    "Codex": {"zh": "Codex", "en": "Codex"},
    "Claude": {"zh": "Claude", "en": "Claude"},
    "Hermes": {"zh": "Hermes", "en": "Hermes"},
    "Other": {"zh": "其他", "en": "Other"},
}

SKIP_HEADINGS = {
    "overview",
    "resources",
    "scripts/",
    "references/",
    "assets/",
    "structuring this skill",
    "not every skill requires all three types of resources.",
}


@dataclass(frozen=True)
class Root:
    path: Path
    label: str


def read_text(path: Path, limit: int | None = None) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    if limit and len(text) > limit:
        return text[:limit]
    return text


def strip_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.S)
    if not match:
        return {}, text
    meta: dict[str, str] = {}
    for raw_line in match.group(1).splitlines():
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key:
            meta[key] = value
    return meta, text[match.end() :]


def parse_openai_yaml(skill_dir: Path) -> dict[str, str]:
    text = read_text(skill_dir / "agents" / "openai.yaml", limit=12000)
    fields: dict[str, str] = {}
    for key in ("display_name", "short_description", "default_prompt", "brand_color"):
        pattern = rf"^\s*{re.escape(key)}:\s*[\"']?(.*?)[\"']?\s*$"
        match = re.search(pattern, text, re.M)
        if match:
            fields[key] = match.group(1).strip()
    return fields


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def markdown_to_plain(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.M)
    text = re.sub(r"^[>\-*+\d.)\s]+", "", text, flags=re.M)
    text = text.replace("|", " ")
    return normalize_spaces(text)


def extract_headings(body: str) -> list[dict[str, str]]:
    matches = list(re.finditer(r"^(#{2,4})\s+(.+?)\s*$", body, flags=re.M))
    sections: list[dict[str, str]] = []
    for index, match in enumerate(matches):
        title = normalize_spaces(re.sub(r"\s*#+\s*$", "", match.group(2)))
        key = title.lower()
        if key in SKIP_HEADINGS or title.startswith("[TODO"):
            continue
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        plain = markdown_to_plain(body[start:end])
        if not plain:
            continue
        sections.append(
            {
                "title": title[:90],
                "body": plain[:620],
                "level": str(len(match.group(1))),
            }
        )
        if len(sections) >= 8:
            break
    return sections


def first_sentence(text: str, fallback: str) -> str:
    clean = normalize_spaces(markdown_to_plain(text))
    for sep in ("。", ".", "!", "?", "\n"):
        if sep in clean:
            part = clean.split(sep, 1)[0].strip()
            if len(part) >= 12:
                return part[:220]
    return (clean or fallback)[:220]


def is_system_skill(path: Path) -> bool:
    text = str(path)
    home = str(Path.home())
    return text.startswith(f"{home}/.codex/skills/.system")


def infer_platforms(path: Path, name: str, description: str, body: str) -> list[str]:
    if is_system_skill(path):
        return ["System"]
    haystack = f"{path} {name} {description} {body[:3000]}".lower()
    platforms: list[str] = []
    if any(token in haystack for token in ("claude", "anthropic", ".claude")):
        platforms.append("Claude")
    if any(token in haystack for token in ("hermes", ".hermes")):
        platforms.append("Hermes")
    if any(token in haystack for token in ("codex", "openai", ".codex")):
        platforms.append("Codex")
    if not platforms:
        platforms.append("Other")
    return [platform for platform in PLATFORM_ORDER if platform in platforms]


def infer_categories(name: str, description: str, body: str) -> list[str]:
    name_text = name.lower()
    description_text = description.lower()
    body_text = body[:5000].lower()
    scores: dict[str, int] = {}
    for category, keywords in CATEGORY_RULES.items():
        score = 0
        for keyword in keywords:
            token = keyword.lower()
            if token in name_text:
                score += 7
            if token in description_text:
                score += 4
            if token in body_text:
                score += 1
        if score >= 4:
            scores[category] = score
    ranked = [key for key, _ in sorted(scores.items(), key=lambda item: (-item[1], CATEGORY_ORDER.index(item[0])))]
    if not ranked:
        ranked = ["其他"]
    return ranked[:4]


def infer_example_kind(categories: list[str]) -> str:
    for preferred in ("图片", "视频", "PPT", "排版", "数据", "代码", "音频", "文档", "文案"):
        if preferred in categories:
            return preferred
    return categories[0] if categories else "其他"


def source_label(path: Path) -> str:
    text = str(path)
    home = str(Path.home())
    if "/.codex/plugins/cache/" in text:
        match = re.search(r"/\.codex/plugins/cache/([^/]+)", text)
        plugin = match.group(1) if match else "plugin-cache"
        return f"Plugin: {plugin}"
    if text.startswith(f"{home}/.codex/skills/.system"):
        return "Codex system"
    if text.startswith(f"{home}/.codex/skills"):
        return "Codex user"
    if text.startswith(f"{home}/.agents/skills"):
        return "Agents"
    if text.startswith(f"{home}/.claude"):
        return "Claude"
    if text.startswith(f"{home}/.hermes"):
        return "Hermes"
    return "Local"


def capability_labels(name: str, description: str, sections: list[dict[str, str]], categories: list[str]) -> list[str]:
    labels: list[str] = []
    for category in categories:
        if category != "其他":
            labels.append(category)
    for section in sections:
        title = section["title"]
        if 2 <= len(title) <= 28 and not title.lower().startswith(("step ", "quick start")):
            labels.append(title)
    desc = markdown_to_plain(description)
    for token in re.split(r"[;；,，。.!?]", desc):
        token = token.strip()
        if 4 <= len(token) <= 24:
            labels.append(token)
    deduped: list[str] = []
    seen: set[str] = set()
    for label in labels:
        key = label.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(label[:34])
        if len(deduped) >= 6:
            break
    if not deduped:
        deduped = [name]
    return deduped


def localized_category_list(categories: list[str], lang: str) -> str:
    if not categories:
        return "general workflow" if lang == "en" else "通用流程"
    if lang == "en":
        mapping = {
            "文案": "copywriting",
            "图片": "image work",
            "视频": "video work",
            "PPT": "slide decks",
            "排版": "layout",
            "数据": "data analysis",
            "代码": "code work",
            "知识库": "knowledge work",
            "自动化": "automation",
            "设计": "design",
            "文档": "documents",
            "音频": "audio",
            "研究": "research",
            "其他": "general workflow",
        }
        return ", ".join(mapping.get(item, item) for item in categories[:3])
    return "、".join(categories[:3])


def make_intro(display_name: str, platforms: list[str], categories: list[str], capabilities: list[str], source: str) -> dict[str, str]:
    zh_categories = localized_category_list(categories, "zh")
    en_categories = localized_category_list(categories, "en")
    zh_caps = "、".join(capabilities[:3]) if capabilities else zh_categories
    en_caps = ", ".join(capabilities[:3]) if capabilities else en_categories
    zh_platform = " / ".join(PLATFORM_LABELS.get(item, {"zh": item})["zh"] for item in platforms)
    en_platform = " / ".join(PLATFORM_LABELS.get(item, {"en": item})["en"] for item in platforms)
    return {
        "zh": f"{display_name} 是一个偏向「{zh_categories}」的本机 skill，适合在 {zh_platform} 场景下快速处理 {zh_caps} 等任务。它来自 {source}，可在详情页复制调用提示、查看变体入口，或在 localhost 模式下尝试真实生成示例。",
        "en": f"{display_name} is a local skill focused on {en_categories}. Use it in {en_platform} workflows for tasks such as {en_caps}. It is sourced from {source}; the detail panel lets you copy invocation prompts, inspect variants, or try a real example in localhost mode.",
    }


def make_usage_cards(display_name: str, name: str, categories: list[str], capabilities: list[str]) -> list[dict[str, str]]:
    zh_categories = localized_category_list(categories, "zh")
    en_categories = localized_category_list(categories, "en")
    zh_caps = "、".join(capabilities[:4]) if capabilities else zh_categories
    en_caps = ", ".join(capabilities[:4]) if capabilities else en_categories
    return [
        {
            "titleZh": "什么时候用",
            "bodyZh": f"当任务需要 {zh_categories}，并且希望复用已经沉淀好的流程、提示或本地工具时，优先考虑 {display_name}。",
            "titleEn": "When to use",
            "bodyEn": f"Choose {display_name} when the task needs {en_categories} and you want a reusable local workflow instead of starting from scratch.",
        },
        {
            "titleZh": "准备什么",
            "bodyZh": f"先准备目标、输入材料和期望产出风格；如果任务涉及真实生成，请确认 token 额度、模型配置或本地软件可用。",
            "titleEn": "What to prepare",
            "bodyEn": "Prepare the goal, source material, and expected output style. For real generation, confirm token budget, model/provider setup, or local app availability first.",
        },
        {
            "titleZh": "怎么调用",
            "bodyZh": f"复制 `Use ${name}` 开头的提示，补充你要完成的具体任务；也可以直接复制下方变体提示，一键进入对应分支。",
            "titleEn": "How to invoke",
            "bodyEn": f"Copy a prompt starting with `Use ${name}`, add the concrete task, or use one of the variant prompts below for a specific branch.",
        },
        {
            "titleZh": "产出预期",
            "bodyZh": f"常见产出会围绕 {zh_caps} 展开。Dashboard 的真实案例按钮会尝试把结果写入本地示例目录。",
            "titleEn": "Expected output",
            "bodyEn": f"Expected output usually centers on {en_caps}. The real example action attempts to write artifacts into a local example folder.",
        },
    ]


def variant_candidates(name: str, categories: list[str], capabilities: list[str], body: str) -> list[dict[str, str]]:
    candidates: list[tuple[str, str, str]] = []
    for category in categories[:4]:
        candidates.append((category, category, f"Use ${name} to create a {category} example."))
    for cap in capabilities[:5]:
        if cap not in {item[0] for item in candidates}:
            candidates.append((cap, cap, f"Use ${name} with the {cap} branch for a realistic task."))
    style_keywords = [
        ("科技感", "Tech style"),
        ("国风", "Chinese style"),
        ("极简", "Minimal style"),
        ("复古", "Retro style"),
        ("手绘", "Hand-drawn style"),
        ("商业", "Business style"),
        ("社媒", "Social style"),
        ("小红书", "Xiaohongshu style"),
        ("公众号", "WeChat article style"),
        ("暗色", "Dark tone"),
        ("亮色", "Bright tone"),
    ]
    lower_body = body.lower()
    for zh, en in style_keywords:
        if zh.lower() in lower_body and zh not in {item[0] for item in candidates}:
            candidates.append((zh, en, f"Use ${name} with the {zh} variant for a realistic task."))
    variants: list[dict[str, str]] = []
    for index, (zh, en, prompt) in enumerate(candidates[:6], start=1):
        variants.append(
            {
                "id": f"v{index}",
                "labelZh": zh[:28],
                "labelEn": en[:40],
                "prompt": prompt,
            }
        )
    if not variants:
        variants.append(
            {
                "id": "v1",
                "labelZh": "默认流程",
                "labelEn": "Default workflow",
                "prompt": f"Use ${name} to complete a realistic task.",
            }
        )
    return variants


def safe_relative(path: Path) -> str:
    try:
        return str(path.relative_to(Path.home()))
    except ValueError:
        return str(path)


def path_uri(path: Path) -> str:
    try:
        return path.resolve().as_uri()
    except (OSError, ValueError):
        return ""


def run_git(args: list[str], cwd: Path, timeout: int = 4) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def find_git_root(path: Path) -> Path | None:
    try:
        current = path.resolve()
    except OSError:
        current = path
    if current.is_file():
        current = current.parent
    for candidate in [current, *current.parents]:
        if (candidate / ".git").exists():
            try:
                result = run_git(["rev-parse", "--show-toplevel"], candidate)
            except (OSError, subprocess.TimeoutExpired):
                return candidate
            if result.returncode == 0 and result.stdout.strip():
                return Path(result.stdout.strip())
            return candidate
    return None


def git_update_info(path: Path) -> dict[str, object]:
    root = find_git_root(path)
    if not root:
        return {
            "type": "local",
            "available": False,
            "label": "Local",
            "note": "No git repository was detected for this skill.",
            "command": "",
        }
    key = str(root)
    if key in GIT_INFO_CACHE:
        return dict(GIT_INFO_CACHE[key])
    info: dict[str, object] = {
        "type": "git",
        "available": False,
        "label": "Git",
        "repoRoot": key,
        "repoRootUri": path_uri(root),
        "branch": "",
        "upstream": "",
        "remote": "",
        "dirty": False,
        "command": f"git -C {shlex.quote(key)} pull --ff-only",
    }
    try:
        branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"], root)
        upstream = run_git(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], root)
        remote = run_git(["remote", "get-url", "origin"], root)
        status = run_git(["status", "--porcelain"], root)
    except (OSError, subprocess.TimeoutExpired):
        info["note"] = "Git metadata could not be read."
        GIT_INFO_CACHE[key] = info
        return dict(info)
    if branch.returncode == 0:
        info["branch"] = branch.stdout.strip()
    if upstream.returncode == 0:
        info["upstream"] = upstream.stdout.strip()
        info["available"] = True
    if remote.returncode == 0:
        info["remote"] = remote.stdout.strip()
    if status.returncode == 0:
        info["dirty"] = bool(status.stdout.strip())
    info["note"] = "Pull with --ff-only from the configured upstream." if info["available"] else "Git repo found, but no upstream branch is configured."
    GIT_INFO_CACHE[key] = info
    return dict(info)


def scan_skill(skill_md: Path) -> dict[str, object] | None:
    raw = read_text(skill_md)
    if not raw:
        return None
    meta, body = strip_frontmatter(raw)
    folder = skill_md.parent
    openai = parse_openai_yaml(folder)
    name = meta.get("name") or folder.name
    description = meta.get("description") or openai.get("short_description") or first_sentence(body, name)
    display_name = openai.get("display_name") or name.replace("-", " ").title()
    sections = extract_headings(body)
    plain_body = markdown_to_plain(body)
    categories = infer_categories(name, description, plain_body)
    platforms = infer_platforms(folder, name, description, plain_body)
    stat = skill_md.stat()
    identifier = hashlib.sha1(str(folder.resolve()).encode("utf-8")).hexdigest()[:12]
    summary = first_sentence(description, first_sentence(body, display_name))
    update_info = git_update_info(folder)
    capabilities = capability_labels(name, description, sections, categories)
    source = source_label(folder)
    intro = make_intro(display_name, platforms, categories, capabilities, source)
    return {
        "id": identifier,
        "name": name,
        "displayName": display_name,
        "description": description,
        "summary": summary,
        "intro": intro,
        "platforms": platforms,
        "categories": categories,
        "exampleKind": infer_example_kind(categories),
        "capabilities": capabilities,
        "usageCards": make_usage_cards(display_name, name, categories, capabilities),
        "variants": variant_candidates(name, categories, capabilities, plain_body),
        "sections": sections,
        "path": str(folder),
        "pathLabel": safe_relative(folder),
        "pathUri": path_uri(folder),
        "sourceFile": str(skill_md),
        "sourceFileUri": path_uri(skill_md),
        "source": source,
        "update": update_info,
        "defaultPrompt": openai.get("default_prompt") or f"Use ${name} to handle this task.",
        "brandColor": openai.get("brand_color") or "",
        "bodyPreview": plain_body[:1800],
        "searchText": normalize_spaces(
            f"{name} {display_name} {description} {' '.join(categories)} {' '.join(platforms)} {update_info.get('remote', '')} {plain_body}"
        )[:7000],
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
        "size": stat.st_size,
    }


def default_roots() -> list[Root]:
    home = Path.home()
    roots: list[Root] = [
        Root(home / ".codex" / "skills", "Codex skills"),
        Root(home / ".agents" / "skills", "Agent skills"),
        Root(home / ".claude" / "skills", "Claude skills"),
        Root(home / ".claude" / "commands", "Claude commands"),
        Root(home / ".hermes" / "skills", "Hermes skills"),
    ]
    plugin_cache = home / ".codex" / "plugins" / "cache"
    if plugin_cache.exists():
        for skills_dir in sorted(plugin_cache.rglob("skills")):
            if skills_dir.is_dir():
                roots.append(Root(skills_dir, "Plugin skills"))
    return roots


def parse_root_args(root_args: list[str] | None) -> list[Root]:
    roots = default_roots()
    env_roots = os.environ.get("SKILL_DASHBOARD_ROOTS", "")
    raw_roots: list[str] = []
    if env_roots:
        raw_roots.extend(part for part in env_roots.split(os.pathsep) if part)
    for value in root_args or []:
        raw_roots.extend(part for part in re.split(r"[:,]", value) if part)
    roots.extend(Root(Path(part).expanduser(), "Custom") for part in raw_roots)
    deduped: list[Root] = []
    seen: set[str] = set()
    for root in roots:
        try:
            key = str(root.path.resolve())
        except OSError:
            key = str(root.path)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(root)
    return deduped


def discover_skill_files(roots: Iterable[Root]) -> list[Path]:
    files: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        if not root.path.exists():
            continue
        for skill_md in sorted(root.path.rglob("SKILL.md")):
            try:
                key = str(skill_md.resolve())
            except OSError:
                key = str(skill_md)
            if key in seen:
                continue
            seen.add(key)
            files.append(skill_md)
    return files


def build_dataset(root_args: list[str] | None = None) -> dict[str, object]:
    roots = parse_root_args(root_args)
    skills: list[dict[str, object]] = []
    for skill_md in discover_skill_files(roots):
        skill = scan_skill(skill_md)
        if skill:
            skills.append(skill)
    skills.sort(key=lambda item: (str(item["source"]), str(item["name"])))
    platform_counts = {platform: 0 for platform in PLATFORM_ORDER}
    category_counts = {category: 0 for category in CATEGORY_ORDER}
    for skill in skills:
        for platform in skill["platforms"]:  # type: ignore[index]
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
        for category in skill["categories"]:  # type: ignore[index]
            category_counts[category] = category_counts.get(category, 0) + 1
    return {
        "generatedAt": datetime.now().isoformat(timespec="seconds"),
        "skillCount": len(skills),
        "roots": [
            {"path": str(root.path), "pathUri": path_uri(root.path), "label": root.label, "exists": root.path.exists()} for root in roots
        ],
        "platformCounts": platform_counts,
        "categoryCounts": category_counts,
        "platformOrder": ["全部"] + PLATFORM_ORDER,
        "platformLabels": PLATFORM_LABELS,
        "categoryOrder": ["全部"] + CATEGORY_ORDER,
        "dashboardUpdate": {
            "available": (SKILL_DIR / "scripts" / "update.sh").exists(),
            "command": shlex.quote(str(SKILL_DIR / "scripts" / "update.sh")),
            "script": str(SKILL_DIR / "scripts" / "update.sh"),
            "repoUrl": DEFAULT_REPO_URL,
            "repo": git_update_info(SKILL_DIR),
        },
        "skills": skills,
        "referenceSources": [
            {
                "label": "FutureTools",
                "url": "https://futuretools.io/",
                "note": "工具目录、榜单和分类导航结构",
            },
            {
                "label": "Matt Wolfe",
                "url": "https://mattwolfe.com/",
                "note": "内容分区、项目入口和紧凑信息层级",
            },
            {
                "label": "Curious Refuge",
                "url": "https://curiousrefuge.com/",
                "note": "创意教育站点的沉浸式视觉和课程卡片",
            },
        ],
    }


def render_dashboard(dataset: dict[str, object], out_dir: Path) -> Path:
    template = read_text(ASSETS_DIR / "dashboard.html")
    if "__SKILL_DASHBOARD_DATA__" not in template:
        raise RuntimeError("dashboard.html is missing the data placeholder")
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(dataset, ensure_ascii=False)
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )
    html_text = template.replace("__SKILL_DASHBOARD_DATA__", payload)
    index_path = out_dir / "index.html"
    index_path.write_text(html_text, encoding="utf-8")
    (out_dir / "skills-data.json").write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8")
    return index_path


def find_port(preferred: int) -> int:
    port = preferred
    while port < preferred + 100:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", port))
            except OSError:
                port += 1
                continue
            return port
    raise RuntimeError(f"No free port found near {preferred}")


def trim_output(text: str | bytes, limit: int = 6000) -> str:
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="replace")
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...[truncated]"


def run_update_process(args: list[str], timeout: int = 180) -> dict[str, object]:
    command = " ".join(shlex.quote(part) for part in args)
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
    except FileNotFoundError as exc:
        return {"ok": False, "command": command, "stdout": "", "stderr": str(exc), "code": 127}
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "command": command,
            "stdout": trim_output(exc.stdout or ""),
            "stderr": trim_output(exc.stderr or "Update timed out."),
            "code": 124,
        }
    return {
        "ok": proc.returncode == 0,
        "command": command,
        "stdout": trim_output(proc.stdout),
        "stderr": trim_output(proc.stderr),
        "code": proc.returncode,
    }


def find_skill(dataset: dict[str, object], skill_id: str) -> dict[str, object] | None:
    for skill in dataset.get("skills", []):
        if isinstance(skill, dict) and skill.get("id") == skill_id:
            return skill
    return None


def update_skill(dataset: dict[str, object], skill_id: str) -> dict[str, object]:
    skill = find_skill(dataset, skill_id)
    if not skill:
        return {"ok": False, "stderr": "Skill not found in the current dashboard scan.", "code": 404}
    update = skill.get("update")
    if not isinstance(update, dict) or not update.get("available"):
        return {
            "ok": False,
            "stderr": "This skill is not connected to a git upstream, so it cannot be updated automatically.",
            "code": 400,
            "command": update.get("command", "") if isinstance(update, dict) else "",
        }
    repo_root = Path(str(update.get("repoRoot", ""))).expanduser()
    if not repo_root.exists():
        return {"ok": False, "stderr": f"Repository path does not exist: {repo_root}", "code": 404}
    return run_update_process(["git", "-C", str(repo_root), "pull", "--ff-only"])


def update_dashboard() -> dict[str, object]:
    script = SKILL_DIR / "scripts" / "update.sh"
    if not script.exists():
        return {"ok": False, "stderr": f"Update script is missing: {script}", "code": 404}
    return run_update_process(["bash", str(script)])


def allowed_paths(dataset: dict[str, object], out_dir: Path) -> list[Path]:
    paths = [out_dir, SKILL_DIR]
    for root in dataset.get("roots", []):
        if isinstance(root, dict) and root.get("path"):
            paths.append(Path(str(root["path"])).expanduser())
    for skill in dataset.get("skills", []):
        if isinstance(skill, dict):
            for key in ("path", "sourceFile"):
                if skill.get(key):
                    paths.append(Path(str(skill[key])).expanduser())
            update = skill.get("update")
            if isinstance(update, dict) and update.get("repoRoot"):
                paths.append(Path(str(update["repoRoot"])).expanduser())
    resolved: list[Path] = []
    for path in paths:
        try:
            resolved.append(path.resolve())
        except OSError:
            continue
    return resolved


def is_allowed_local_path(path: Path, dataset: dict[str, object], out_dir: Path) -> bool:
    try:
        target = path.expanduser().resolve()
    except OSError:
        return False
    for allowed in allowed_paths(dataset, out_dir):
        if target == allowed or allowed in target.parents:
            return True
    return False


def open_local_path(dataset: dict[str, object], out_dir: Path, raw_path: str) -> dict[str, object]:
    if not raw_path:
        return {"ok": False, "stderr": "Missing path.", "code": 400}
    path = Path(unquote(raw_path)).expanduser()
    if not path.exists():
        return {"ok": False, "stderr": f"Path does not exist: {path}", "code": 404}
    if not is_allowed_local_path(path, dataset, out_dir):
        return {"ok": False, "stderr": "Path is outside the scanned skill roots.", "code": 403}
    if sys.platform == "darwin":
        args = ["open", str(path)]
    elif os.name == "nt":
        args = ["cmd", "/c", "start", "", str(path)]
    else:
        args = ["xdg-open", str(path)]
    result = run_update_process(args, timeout=12)
    result["path"] = str(path)
    return result


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-")
    return slug[:72] or "skill"


def find_variant(skill: dict[str, object], variant_id: str) -> dict[str, str] | None:
    for variant in skill.get("variants", []):
        if isinstance(variant, dict) and variant.get("id") == variant_id:
            return {key: str(value) for key, value in variant.items()}
    return None


def build_real_example_prompt(skill: dict[str, object], variant: dict[str, str] | None, out_dir: Path) -> str:
    name = str(skill.get("name", "skill"))
    display_name = str(skill.get("displayName", name))
    variant_label = variant.get("labelZh") if variant else "默认流程"
    variant_prompt = variant.get("prompt") if variant else str(skill.get("defaultPrompt", f"Use ${name}."))
    return f"""Use ${name} at {skill.get('path')} to generate a realistic example for Skill Dashboard.

Skill: {display_name}
Variant: {variant_label}
Base prompt: {variant_prompt}

Create the actual best-effort output files inside this folder:
{out_dir}

If the skill requires token budget, model/provider configuration, login, or a local app that is not currently available, do not fake the result. Write a concise NEXT_STEPS.md explaining exactly what is missing and what the user should configure.

Return a short summary of what was generated and list the files created.
"""


def generate_real_example(dataset: dict[str, object], out_dir: Path, skill_id: str, variant_id: str = "") -> dict[str, object]:
    skill = find_skill(dataset, skill_id)
    if not skill:
        return {"ok": False, "stderr": "Skill not found in the current dashboard scan.", "code": 404}
    skill_path = Path(str(skill.get("path", ""))).expanduser()
    if not skill_path.exists():
        return {"ok": False, "stderr": f"Skill path does not exist: {skill_path}", "code": 404}
    codex_bin = os.environ.get("SKILL_DASHBOARD_CODEX") or shutil_which("codex")
    if not codex_bin:
        command = f"codex exec --cd <output-dir> --add-dir {shlex.quote(str(skill_path))} \"Use ${skill.get('name')} ...\""
        return {
            "ok": False,
            "needsConfig": True,
            "stderr": "Codex CLI was not found. Install or configure codex, or set SKILL_DASHBOARD_CODEX.",
            "command": command,
            "code": 127,
        }
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    example_dir = out_dir / "real-examples" / f"{timestamp}-{safe_slug(str(skill.get('name', 'skill')))}"
    example_dir.mkdir(parents=True, exist_ok=True)
    variant = find_variant(skill, variant_id)
    prompt = build_real_example_prompt(skill, variant, example_dir)
    prompt_path = example_dir / "REQUEST.md"
    prompt_path.write_text(prompt, encoding="utf-8")
    last_message = example_dir / "RESULT.md"
    args = [
        codex_bin,
        "exec",
        "--cd",
        str(example_dir),
        "--add-dir",
        str(skill_path),
        "--skip-git-repo-check",
        "--output-last-message",
        str(last_message),
        prompt,
    ]
    result = run_update_process(args, timeout=int(os.environ.get("SKILL_DASHBOARD_EXAMPLE_TIMEOUT", "900")))
    files = []
    for item in sorted(example_dir.rglob("*")):
        if item.is_file():
            files.append({"path": str(item), "name": item.name, "pathUri": path_uri(item)})
    result.update(
        {
            "outputPath": str(example_dir),
            "outputUri": path_uri(example_dir),
            "files": files[:80],
            "summary": read_text(last_message, limit=4000) if last_message.exists() else "",
        }
    )
    return result


def shutil_which(command: str) -> str | None:
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(directory) / command
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def serve_directory(out_dir: Path, preferred_port: int, open_browser: bool, dataset: dict[str, object]) -> None:
    port = find_port(preferred_port)
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args: object, **kwargs: object) -> None:
            super().__init__(*args, directory=str(out_dir), **kwargs)

        def log_message(self, fmt: str, *args: object) -> None:
            sys.stderr.write("[%s] %s\n" % (time.strftime("%H:%M:%S"), fmt % args))

        def send_json(self, status: int, payload: dict[str, object]) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def read_json(self) -> dict[str, object]:
            length = int(self.headers.get("Content-Length", "0") or 0)
            if length <= 0:
                return {}
            raw = self.rfile.read(min(length, 65536))
            try:
                value = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError:
                return {}
            return value if isinstance(value, dict) else {}

        def do_POST(self) -> None:
            if self.path == "/api/update-skill":
                payload = self.read_json()
                result = update_skill(dataset, str(payload.get("id", "")))
                self.send_json(200 if result.get("ok") else 400, result)
                return
            if self.path == "/api/update-dashboard":
                result = update_dashboard()
                self.send_json(200 if result.get("ok") else 400, result)
                return
            if self.path == "/api/open-path":
                payload = self.read_json()
                result = open_local_path(dataset, out_dir, str(payload.get("path", "")))
                self.send_json(200 if result.get("ok") else 400, result)
                return
            if self.path == "/api/generate-real-example":
                payload = self.read_json()
                result = generate_real_example(
                    dataset,
                    out_dir,
                    str(payload.get("id", "")),
                    str(payload.get("variantId", "")),
                )
                self.send_json(200 if result.get("ok") else 400, result)
                return
            self.send_json(404, {"ok": False, "stderr": "Unknown API endpoint."})

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}/index.html"
    print(f"Skill Dashboard is running: {url}")
    print("Press Ctrl+C in this terminal to stop the local server.")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped Skill Dashboard.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a local dashboard for installed skills.")
    parser.add_argument("--root", action="append", help="Additional root to scan. Repeatable; comma/colon separated.")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Output directory for the generated dashboard.")
    parser.add_argument("--json", action="store_true", help="Print the scanned dataset as JSON instead of writing HTML.")
    parser.add_argument("--serve", action="store_true", help="Serve the generated dashboard over localhost.")
    parser.add_argument("--open", action="store_true", help="Open the dashboard in the default browser.")
    parser.add_argument("--port", type=int, default=8765, help="Preferred localhost port for --serve.")
    parser.add_argument("--quiet", action="store_true", help="Only print the generated path.")
    args = parser.parse_args()

    dataset = build_dataset(args.root)
    if args.json:
        print(json.dumps(dataset, ensure_ascii=False, indent=2))
        return 0

    out_dir = Path(args.out).expanduser().resolve()
    index_path = render_dashboard(dataset, out_dir)
    if not args.quiet:
        print(f"Scanned {dataset['skillCount']} skills.")
        print(f"Dashboard: {index_path}")
    if args.open and not args.serve:
        webbrowser.open(index_path.as_uri())
    if args.serve:
        serve_directory(out_dir, args.port, args.open, dataset)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
