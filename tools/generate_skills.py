#!/usr/bin/env python3
"""Generate the Markdown that agents read from the documentation pages.

`docs/` holds the authored documentation and is the Mintlify project that
publishes docs.uniac.ai. Every file below is derived from it and committed,
because installers, uniac.ai and Mintlify read them from this repository;
CI fails when a committed copy differs from this generator's output.

    skills/uniac/references/<route>.md      one file per reference page,
                                            with index.mdx as overview.md
    skills/uniac-quickstart/SKILL.md        the quickstart page as a skill
    agents/agents.md                        the setup page; uniac.ai builds
                                            its /agents.md from a pinned copy
    docs/.mintlify/skills/<name>/SKILL.md   each skill's entry as Mintlify
                                            serves it at /skill.md and the
                                            skill discovery endpoints

A page's frontmatter title becomes its level-one heading, and a page that
becomes a skill supplies the skill's description. Code is copied byte for
byte; MDX entities in prose are decoded. Site links (`/route`) become
relative links inside the uniac skill and docs.uniac.ai Markdown URLs
everywhere else, so a skill installed on its own still reaches the complete
documentation. A page containing an MDX component or expression is rejected.

Usage:
    tools/generate_skills.py            # write the files
    tools/generate_skills.py --check    # exit non-zero if any differs
"""

import json
import re
import sys
from os.path import normpath
from pathlib import Path
from posixpath import relpath
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
DOCS = Path("docs")
SKILLS = Path("skills")
REFERENCES = SKILLS / "uniac/references"
HOME = "index"
GUIDES = {"setup": Path("agents/agents.md"), "quickstart": SKILLS / "uniac-quickstart/SKILL.md"}
SITE_SKILLS = DOCS / ".mintlify/skills"
SITE = "https://docs.uniac.ai/"
NAVIGATION_KEYS = ("groups", "pages", "root")
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
FIELD = re.compile(r"^(title|description):[ \t]*(.*)$", re.M)
INLINE_CODE = re.compile(r"(`+)(.*?)(?<!`)\1(?!`)", re.S)
LINK = re.compile(r"(?<=\]\()<?([^\s)>]+)>?")
REFERENCE_LINK = re.compile(r"(^ {0,3}\[[^\]\n]+\]:[ \t]*)<?([^\s>]+)>?", re.M)
MDX = re.compile(r"^[ \t]*[<{]", re.M)
ENTITIES = {"&lt;": "<", "&#123;": "{", "&#125;": "}"}


def output_path(route: str) -> Path:
    """The generated file for a page route, relative to the repository."""
    if route in GUIDES:
        return GUIDES[route]
    return (REFERENCES / ("overview" if route == HOME else route)).with_suffix(".md")


def skill_of(path: Path) -> str | None:
    return path.parts[1] if path.parts[:1] == (SKILLS.name,) and len(path.parts) > 2 else None


def routes(root: Path) -> list[str]:
    """Every page route; the pages and docs.json navigation must agree."""
    docs = root / DOCS
    found = {path.relative_to(docs).with_suffix("").as_posix() for path in docs.rglob("*.mdx")}

    def navigated(node):
        if isinstance(node, str):
            yield node
        elif isinstance(node, dict):
            for key in NAVIGATION_KEYS:
                yield from navigated(node.get(key, []))
        elif isinstance(node, list):
            for item in node:
                yield from navigated(item)

    listed = set(navigated(json.loads((docs / "docs.json").read_text(encoding="utf-8"))["navigation"]))
    if found != listed:
        raise ValueError(
            "docs.json navigation and docs/ pages differ: "
            f"unlisted {sorted(found - listed)}, missing {sorted(listed - found)}"
        )
    return sorted(found)


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


def convert(text: str, source: Path, output: Path, pages: list[str]) -> str:
    """Point links at the output's neighbours or the site, and decode entities."""
    files = {output_path(route): route for route in pages}

    def destination(url):
        parsed = urlsplit(url)
        if parsed.scheme or parsed.netloc or not parsed.path:
            return url
        if parsed.path.startswith("/"):
            route = parsed.path.strip("/") or HOME
        else:
            route = files.get(Path(normpath(source.parent / parsed.path)))
        if route not in pages:
            raise ValueError(f"{source}: link to an unknown page: {url}")
        target = output_path(route)
        if skill_of(target) is not None and skill_of(target) == skill_of(output):
            path = relpath(target.as_posix(), output.parent.as_posix())
        else:
            path = f"{SITE}{route}.md"
        return path + (f"?{parsed.query}" if parsed.query else "") + (f"#{parsed.fragment}" if parsed.fragment else "")

    def prose(value):
        component = MDX.search(value)
        if component:
            line = value[component.start():].splitlines()[0].strip()
            raise ValueError(f"{source}: MDX components and expressions are not converted: {line}")
        value = LINK.sub(lambda m: destination(m[1]), value)
        value = REFERENCE_LINK.sub(lambda m: m[1] + destination(m[2]), value)
        for entity, character in ENTITIES.items():
            value = value.replace(entity, character)
        return value

    return outside_code(text, prose)


def page(root: Path, route: str, output: Path, pages: list[str]) -> str:
    source = DOCS / f"{route}.mdx"
    text = (root / source).read_text(encoding="utf-8")
    match = FRONTMATTER.match(text)
    if not match:
        raise ValueError(f"{source}: expected frontmatter")
    fields = {key: json.loads(value) if value.strip().startswith('"') else value.strip().strip("'")
              for key, value in FIELD.findall(match[1])}
    if "title" not in fields:
        raise ValueError(f"{source}: expected a title")
    document = f"# {fields['title']}\n\n{text[match.end():].lstrip(chr(10))}"
    if output.name == "SKILL.md":
        if "description" not in fields:
            raise ValueError(f"{source}: a page that becomes a skill needs a description")
        document = f"---\nname: {output.parent.name}\ndescription: {fields['description']}\n---\n\n{document}"
    return convert(document, source, output, pages)


def expected(root: Path) -> dict[Path, str]:
    """Every generated file and its content, computed before anything is written."""
    pages = routes(root)
    files = {output_path(route): page(root, route, output_path(route), pages) for route in pages}
    generated = {path: route for route, path in GUIDES.items()}
    names = {path.name for path in (root / SKILLS).iterdir() if path.is_dir()}
    names |= {path.parent.name for path in GUIDES.values() if path.name == "SKILL.md"}
    for name in sorted(names):
        entry, output = SKILLS / name / "SKILL.md", SITE_SKILLS / name / "SKILL.md"
        if entry in generated:
            files[output] = page(root, generated[entry], output, pages)
        else:
            files[output] = convert((root / entry).read_text(encoding="utf-8"), entry, output, pages)
    return files


def generate(root: Path, check: bool = False) -> list[str]:
    files = expected(root)
    owned = set(files) | {
        path.relative_to(root)
        for directory in (REFERENCES, SITE_SKILLS)
        for path in (root / directory).rglob("*")
        if path.is_file()
    }
    changes = []
    for path in sorted(owned):
        actual, content = root / path, files.get(path)
        if content is None:
            changes.append(path.as_posix())
            if not check:
                actual.unlink()
        elif not actual.is_file() or actual.read_bytes() != content.encode("utf-8"):
            changes.append(path.as_posix())
            if not check:
                actual.parent.mkdir(parents=True, exist_ok=True)
                actual.write_bytes(content.encode("utf-8"))
    return changes


def main() -> int:
    check = "--check" in sys.argv[1:]
    try:
        changes = generate(ROOT, check)
    except (OSError, ValueError) as error:
        print(f"FAIL {error}", file=sys.stderr)
        return 1
    if check and changes:
        print("Generated files differ from the pages: " + ", ".join(changes))
        return 1
    print(f"ok: {len(expected(ROOT))} generated files " + ("current" if check else f"written; {len(changes)} changed"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
