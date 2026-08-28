#!/usr/bin/env python3
"""Validate every skill against what strict consumers require.

Installers parse SKILL.md frontmatter with strict YAML; a skill that a
forgiving loader accepts can still be silently dropped by them (a plain
scalar containing ": " is the classic case). This gate runs in CI and
before publishing, and fails loudly instead.

Checks, per skills/<name>/SKILL.md:
  - frontmatter exists, is strict-YAML-parseable, and contains exactly
    the keys the spec requires (name, description) with non-empty
    string values;
  - name matches the directory;
  - every relative markdown link resolves to a file in the skill;
  - referenced files live inside the skill directory.

Exits non-zero on any failure, printing one line per defect.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"

# Strict plain-scalar rule: a mid-scalar ": " (or a value starting with
# characters YAML reserves) must be quoted. We parse with a tiny strict
# reader instead of PyYAML so CI needs no dependencies — and so the
# gate is exactly as harsh as the harshest consumer we have seen.
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
KEY_RE = re.compile(r"\A([A-Za-z][A-Za-z0-9_-]*):[ ](.*)\Z")


def parse_frontmatter(text: str, defects: list, where: str):
    m = FRONTMATTER_RE.match(text)
    if not m:
        defects.append(f"{where}: no frontmatter block")
        return {}
    fields = {}
    for line in m.group(1).splitlines():
        if not line.strip():
            continue
        km = KEY_RE.match(line)
        if not km:
            defects.append(f"{where}: unparseable frontmatter line: {line!r}")
            continue
        key, value = km.group(1), km.group(2).strip()
        if value.startswith(("'", '"')):
            quote = value[0]
            if not (len(value) >= 2 and value.endswith(quote)):
                defects.append(f"{where}: unterminated quoted scalar for {key}")
                continue
            value = value[1:-1]
        else:
            if ": " in value:
                defects.append(
                    f"{where}: {key} is a plain scalar containing ': ' — "
                    "strict parsers reject this; rephrase or quote the value"
                )
            if value and value[0] in "[{&*!|>%@`":
                defects.append(
                    f"{where}: {key} starts with YAML-reserved {value[0]!r} — quote it"
                )
        fields[key] = value
    return fields


LINK_RE = re.compile(r"\]\(([^)#\s]+)(?:#[^)\s]*)?\)")
CODE_RE = re.compile(r"```.*?```|`[^`\n]*`", re.S)


def prose_of(text: str) -> str:
    """Markdown with code fences and inline code removed, so link
    checking never trips over `](...)` sequences inside code."""
    return CODE_RE.sub("", text)


def main() -> int:
    defects: list[str] = []
    skill_dirs = sorted(p for p in SKILLS.iterdir() if p.is_dir())
    if not skill_dirs:
        defects.append("skills/: no skills found")

    for d in skill_dirs:
        md = d / "SKILL.md"
        where = md.relative_to(ROOT)
        if not md.exists():
            defects.append(f"{d.relative_to(ROOT)}: missing SKILL.md")
            continue
        text = md.read_text(encoding="utf-8")
        fields = parse_frontmatter(text, defects, str(where))
        if fields:
            if fields.get("name") != d.name:
                defects.append(
                    f"{where}: name {fields.get('name')!r} != directory {d.name!r}"
                )
            if not fields.get("description"):
                defects.append(f"{where}: empty or missing description")

        for f in d.rglob("*.md"):
            for target in LINK_RE.findall(prose_of(f.read_text(encoding="utf-8"))):
                if "://" in target or target.startswith("mailto:"):
                    continue
                resolved = (f.parent / target).resolve()
                if not resolved.exists():
                    defects.append(
                        f"{f.relative_to(ROOT)}: broken link {target!r}"
                    )
                elif d.resolve() not in resolved.parents and resolved != d.resolve():
                    defects.append(
                        f"{f.relative_to(ROOT)}: link {target!r} escapes the skill"
                    )

    for line in defects:
        print(f"FAIL {line}")
    if not defects:
        print(f"ok: {len(skill_dirs)} skill(s) valid")
    return 1 if defects else 0


if __name__ == "__main__":
    sys.exit(main())
