#!/usr/bin/env python3
"""Export the public Markdown corpus as Mintlify pages using only the stdlib."""

import argparse
import json
import re
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parent.parent
REPOSITORY = "https://github.com/uniac-ai/agent-skills/blob/main/"
REFERENCES = Path("skills/uniac/references")
GUIDES = {"agents/agents.md": "setup", "skills/uniac-quickstart/SKILL.md": "quickstart"}
FRONTMATTER = re.compile(r"\A---\r?\n.*?\r?\n---\r?\n", re.S)
HEADING = re.compile(r"\A\s*# ([^\r\n]+)\r?\n")
INLINE_CODE = re.compile(r"(`+)(.*?)(?<!`)\1(?!`)", re.S)
LINK = re.compile(r"(?<=\]\()<?([^\s)>]+)>?")
REFERENCE_LINK = re.compile(r"(^ {0,3}\[[^\]\n]+\]:[ \t]*)<?([^\s>]+)>?", re.M)


def pages(source: Path) -> dict[str, str]:
    """Every reference owns one route; setup and quickstart are the two guides."""
    result = dict(GUIDES)
    for path in sorted((source / REFERENCES).rglob("*.md")):
        relative = path.relative_to(source / REFERENCES).with_suffix("").as_posix()
        result[path.relative_to(source).as_posix()] = "index" if relative == "concepts" else relative
    if "skills/uniac/references/concepts.md" not in result:
        raise ValueError("missing canonical reference: skills/uniac/references/concepts.md")
    if len(set(result.values())) != len(result):
        raise ValueError("multiple source pages map to the same website route")
    return result


def outside_code(text: str, transform) -> str:
    """Transform prose while copying fenced and inline code byte for byte."""
    def inline(prose):
        parts, start = [], 0
        for match in INLINE_CODE.finditer(prose):
            parts.extend((transform(prose[start:match.start()]), match.group()))
            start = match.end()
        return "".join(parts) + transform(prose[start:])

    parts, prose, fence = [], [], None
    for line in text.splitlines(keepends=True):
        if fence:
            parts.append(line)
            if re.fullmatch(rf" {{0,3}}{fence[0]}{{{fence[1]},}}[ \t]*\r?\n?", line):
                fence = None
        else:
            match = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
            if match:
                parts.extend((inline("".join(prose)), line))
                prose = []
                fence = (match[1][0], len(match[1]))
            else:
                prose.append(line)
    return "".join(parts) + inline("".join(prose))


def destination(url: str, current: str, routes: dict[str, str], source: Path) -> str:
    parsed = urlsplit(url)
    if url.startswith(REPOSITORY):
        path = unquote(parsed.path[len(urlsplit(REPOSITORY).path):])
    elif parsed.scheme or parsed.netloc or not parsed.path:
        return url
    else:
        path = (Path(current).parent / unquote(parsed.path)).as_posix()
    resolved = (source / path).resolve()
    try:
        relative = resolved.relative_to(source.resolve()).as_posix()
    except ValueError:
        raise ValueError(f"{current}: link escapes the source repository: {url}") from None
    if not resolved.is_file():
        raise ValueError(f"{current}: link target does not exist: {url}")
    if relative in routes:
        route = routes[relative]
        target = "/" if route == "index" else "/" + route
    else:
        target = REPOSITORY + quote(relative, safe="/")
    target_parts = urlsplit(target)
    return urlunsplit((*target_parts[:3], parsed.query, parsed.fragment))


def render(text: str, current: str, routes: dict[str, str], source: Path) -> str:
    document = FRONTMATTER.sub("", text, count=1)
    heading = HEADING.match(document)
    if not heading:
        raise ValueError(f"{current}: expected a leading level-one heading")
    title = heading[1].rstrip(" #")
    body = document[heading.end():]

    def prose(value):
        value = LINK.sub(lambda m: destination(m[1], current, routes, source), value)
        value = REFERENCE_LINK.sub(
            lambda m: m[1] + destination(m[2], current, routes, source), value
        )
        return value.replace("<", "&lt;").replace("{", "&#123;").replace("}", "&#125;")

    # Metadata is derived from authored text; the body remains the source contract.
    paragraphs = re.split(r"\r?\n[ \t]*\r?\n", body.strip())
    description = next((p for p in paragraphs if p and not re.match(r"^(?:#{1,6} |\||`{3,}|~{3,}|> |[-*+] )", p)), title)
    description = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", description)
    description = " ".join(description.replace("`", "").replace("**", "").split())
    metadata = {"title": title, "description": description}
    if routes[current] == "index":
        metadata["sidebarTitle"] = "Concepts"
    frontmatter = "\n".join(f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in metadata.items())
    notice = f"{{/* Generated from uniac-ai/agent-skills: {current} */}}"
    return f"---\n{frontmatter}\n---\n\n{notice}\n" + outside_code(body, prose)


def export(source: Path, output: Path, check: bool = False) -> list[str]:
    routes = pages(source)
    expected = {
        route + ".mdx": render((source / path).read_bytes().decode("utf-8"), path, routes, source)
        for path, route in routes.items()
    }
    existing = {
        path.relative_to(output).as_posix(): path
        for path in output.rglob("*.mdx")
        if not any(part.startswith(".") or part == "node_modules" for part in path.relative_to(output).parts)
    }
    changes = []
    for name, content in expected.items():
        path = output / name
        if not path.is_file() or path.read_bytes() != content.encode("utf-8"):
            changes.append(name)
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content.encode("utf-8"))
    for name in sorted(existing.keys() - expected.keys()):
        changes.append(name)
        if not check:
            existing[name].unlink()
    return changes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="Mintlify repository; all MDX pages are generated")
    parser.add_argument("--check", action="store_true", help="report drift without writing files")
    args = parser.parse_args()
    if not (args.output / "docs.json").is_file():
        parser.error("--output must be a Mintlify repository containing docs.json")
    try:
        changes = export(ROOT, args.output.resolve(), args.check)
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    if args.check and changes:
        print("Documentation differs from source: " + ", ".join(changes))
        return 1
    print(f"ok: {len(pages(ROOT))} generated pages" + (" match source" if args.check else f"; {len(changes)} changed"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
