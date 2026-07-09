#!/usr/bin/env python3
"""Build and optionally serve a local dashboard for installed Codex skills."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import socket
import sys
import time
import webbrowser
from dataclasses import dataclass
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterable


SKILL_DIR = Path(__file__).resolve().parents[1]
ASSETS_DIR = SKILL_DIR / "assets"
DEFAULT_OUT = SKILL_DIR / ".dashboard"


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

PLATFORM_ORDER = ["Codex", "Claude", "Hermes", "Other"]

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


def infer_platforms(path: Path, name: str, description: str, body: str) -> list[str]:
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


def safe_relative(path: Path) -> str:
    try:
        return str(path.relative_to(Path.home()))
    except ValueError:
        return str(path)


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
    return {
        "id": identifier,
        "name": name,
        "displayName": display_name,
        "description": description,
        "summary": summary,
        "platforms": platforms,
        "categories": categories,
        "exampleKind": infer_example_kind(categories),
        "capabilities": capability_labels(name, description, sections, categories),
        "sections": sections,
        "path": str(folder),
        "pathLabel": safe_relative(folder),
        "source": source_label(folder),
        "defaultPrompt": openai.get("default_prompt") or f"Use ${name} to handle this task.",
        "brandColor": openai.get("brand_color") or "",
        "bodyPreview": plain_body[:1800],
        "searchText": normalize_spaces(f"{name} {display_name} {description} {' '.join(categories)} {' '.join(platforms)} {plain_body}")[
            :7000
        ],
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
            {"path": str(root.path), "label": root.label, "exists": root.path.exists()} for root in roots
        ],
        "platformCounts": platform_counts,
        "categoryCounts": category_counts,
        "platformOrder": ["全部"] + PLATFORM_ORDER,
        "categoryOrder": ["全部"] + CATEGORY_ORDER,
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


def serve_directory(out_dir: Path, preferred_port: int, open_browser: bool) -> None:
    port = find_port(preferred_port)
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args: object, **kwargs: object) -> None:
            super().__init__(*args, directory=str(out_dir), **kwargs)

        def log_message(self, fmt: str, *args: object) -> None:
            sys.stderr.write("[%s] %s\n" % (time.strftime("%H:%M:%S"), fmt % args))

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}/index.html"
    print(f"Skill Dashboard serving {html.escape(url)}")
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
        serve_directory(out_dir, args.port, args.open)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
